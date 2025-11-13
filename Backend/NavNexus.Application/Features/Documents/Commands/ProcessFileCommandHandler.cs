using System.Diagnostics;
using MediatR;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Application.Common.Models;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Features.Documents.Commands;

/// <summary>
/// Handler for file processing - implements the full async flow from flow.md
/// STEP 1-7: Cache check → Upload → Translate → LLM → Dual Storage → Update cache
/// </summary>
public class ProcessFileCommandHandler : IRequestHandler<ProcessFileCommand, Result<string>>
{
    private readonly IFirestoreService _firestoreService;
    private readonly IFileStorageService _fileStorageService;
    private readonly ITranslationService _translationService;
    private readonly IQdrantService _qdrantService;
    private readonly ILlmService _llmService;
    private readonly INeo4jService _neo4jService;
    private readonly ILogger<ProcessFileCommandHandler> _logger;

    public ProcessFileCommandHandler(
        IFirestoreService firestoreService,
        IFileStorageService fileStorageService,
        ITranslationService translationService,
        IQdrantService qdrantService,
        ILlmService llmService,
        INeo4jService neo4jService,
        ILogger<ProcessFileCommandHandler> logger)
    {
        _firestoreService = firestoreService;
        _fileStorageService = fileStorageService;
        _translationService = translationService;
        _qdrantService = qdrantService;
        _llmService = llmService;
        _neo4jService = neo4jService;
        _logger = logger;
    }

    public async Task<Result<string>> Handle(ProcessFileCommand request, CancellationToken cancellationToken)
    {
        var stopwatch = Stopwatch.StartNew();
        
        try
        {
            _logger.LogInformation("Starting file processing for file {FileId} in workspace {WorkspaceId}", 
                request.FileId, request.WorkspaceId);

            // STEP 1: Check Firestore cache (deduplication)
            var existingFile = await _firestoreService.GetFileByHashAsync(request.WorkspaceId, request.FileHash, cancellationToken);
            if (existingFile != null && existingFile.Status == ProcessingStatus.Completed)
            {
                _logger.LogInformation("File {FileId} already processed (cache hit)", request.FileId);
                return Result<string>.Success($"File already processed: {existingFile.FileId}");
            }

            // Create initial metadata
            var fileMetadata = new FileMetadata
            {
                FileId = request.FileId,
                FileHash = request.FileHash,
                FileName = request.FileName,
                FileSize = request.FileSize,
                MimeType = request.MimeType,
                WorkspaceId = request.WorkspaceId,
                UploadDate = DateTime.UtcNow,
                NosUrl = request.FileUrl,
                Status = ProcessingStatus.Processing
            };
            
            await _firestoreService.SaveFileMetadataAsync(fileMetadata, cancellationToken);

            // STEP 2: Download file (already uploaded, URL provided)
            _logger.LogInformation("Downloading file from {FileUrl}", request.FileUrl);
            var fileStream = await _fileStorageService.DownloadFileAsync(request.FileUrl, cancellationToken);
            
            // Extract text from file (simplified - assumes text extraction is done)
            var extractedText = "Sample extracted text from document"; // TODO: Implement PDF/DOC extraction

            // STEP 3: Language Detection & Translation
            _logger.LogInformation("Detecting language for file {FileId}", request.FileId);
            var detectedLanguage = await _translationService.DetectLanguageAsync(extractedText, cancellationToken);
            fileMetadata.LanguageDetected = detectedLanguage;
            
            string translatedText = extractedText;
            if (detectedLanguage != "en")
            {
                _logger.LogInformation("Translating file {FileId} from {SourceLang} to en", 
                    request.FileId, detectedLanguage);
                translatedText = await _translationService.TranslateAsync(extractedText, detectedLanguage, "en", cancellationToken);
                fileMetadata.TranslationTarget = "en";
            }

            // STEP 4: Qdrant Context Retrieval
            _logger.LogInformation("Retrieving context from Qdrant for file {FileId}", request.FileId);
            var collectionName = $"workspace_{request.WorkspaceId}";
            await _qdrantService.EnsureCollectionExistsAsync(collectionName, cancellationToken);
            
            var queryVector = await _qdrantService.GenerateEmbeddingAsync(translatedText, cancellationToken);
            var contextChunks = await _qdrantService.SearchSimilarChunksAsync(collectionName, queryVector, 5, cancellationToken);

            // STEP 5: LLM Processing (HyperCLOVA X)
            _logger.LogInformation("Extracting knowledge using LLM for file {FileId}", request.FileId);
            var extractionResult = await _llmService.ExtractKnowledgeAsync(translatedText, contextChunks, cancellationToken);

            // STEP 6: Dual Storage (Parallel) - Qdrant + Neo4j
            _logger.LogInformation("Storing knowledge in dual storage for file {FileId}", request.FileId);
            
            // 6A: Store in Qdrant
            var vectors = new List<float[]>();
            foreach (var (_, text) in extractionResult.Chunks)
            {
                var vector = await _qdrantService.GenerateEmbeddingAsync(text, cancellationToken);
                vectors.Add(vector);
            }
            
            var chunkPayloads = extractionResult.Chunks.Select(c => c.Payload).ToList();
            foreach (var payload in chunkPayloads)
            {
                payload.PaperId = request.FileId;
                payload.WorkspaceId = request.WorkspaceId;
                payload.Language = "en";
                payload.SourceLanguage = detectedLanguage;
            }
            
            var qdrantPointIds = await _qdrantService.UpsertChunksAsync(collectionName, chunkPayloads, vectors, cancellationToken);

            // 6B: Store in Neo4j
            foreach (var node in extractionResult.KnowledgeNodes)
            {
                node.WorkspaceId = request.WorkspaceId;
            }
            
            foreach (var evidence in extractionResult.Evidences)
            {
                evidence.WorkspaceId = request.WorkspaceId;
                evidence.SourceUrl = request.FileUrl;
            }
            
            var neo4jNodeIds = await _neo4jService.UpsertKnowledgeNodesAsync(extractionResult.KnowledgeNodes, cancellationToken);
            await _neo4jService.CreateEvidenceNodesAsync(extractionResult.Evidences, neo4jNodeIds, cancellationToken);
            await _neo4jService.CreateRelationshipsAsync(extractionResult.Relationships, cancellationToken);

            // STEP 7: Update Firestore Cache
            stopwatch.Stop();
            fileMetadata.Status = ProcessingStatus.Completed;
            fileMetadata.Neo4jNodeIds = neo4jNodeIds;
            fileMetadata.QdrantPointIds = qdrantPointIds;
            fileMetadata.ProcessingTimeMs = stopwatch.ElapsedMilliseconds;
            
            await _firestoreService.SaveFileMetadataAsync(fileMetadata, cancellationToken);
            await _firestoreService.UpdateWorkspaceStatsAsync(request.WorkspaceId, 1, request.FileSize, cancellationToken);

            _logger.LogInformation("File processing completed for {FileId} in {ElapsedMs}ms", 
                request.FileId, stopwatch.ElapsedMilliseconds);

            return Result<string>.Success(request.FileId);
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Error processing file {FileId}", request.FileId);
            
            // Update file metadata with error
            try
            {
                var fileMetadata = await _firestoreService.GetFileByIdAsync(request.WorkspaceId, request.FileId, cancellationToken);
                if (fileMetadata != null)
                {
                    fileMetadata.Status = ProcessingStatus.Failed;
                    fileMetadata.ErrorMessage = ex.Message;
                    fileMetadata.ProcessingTimeMs = stopwatch.ElapsedMilliseconds;
                    await _firestoreService.SaveFileMetadataAsync(fileMetadata, cancellationToken);
                }
            }
            catch (Exception saveEx)
            {
                _logger.LogError(saveEx, "Failed to save error state for file {FileId}", request.FileId);
            }

            return Result<string>.Failure($"File processing failed: {ex.Message}", "PROCESSING_FAILED");
        }
    }
}
