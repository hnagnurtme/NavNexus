using System.Text;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;

namespace NavNexus.Infrastructure.ExternalServices;

public class GapSuggestionService : IGapSuggestionService
{
    private readonly ILlmService _llmService;
    private readonly IKnowledgetreeRepository _knowledgeTreeRepository;
    private readonly ILogger<GapSuggestionService> _logger;

    public GapSuggestionService(
        ILlmService llmService,
        IKnowledgetreeRepository knowledgeTreeRepository,
        ILogger<GapSuggestionService> logger)
    {
        _llmService = llmService ?? throw new ArgumentNullException(nameof(llmService));
        _knowledgeTreeRepository = knowledgeTreeRepository ?? throw new ArgumentNullException(nameof(knowledgeTreeRepository));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task<List<GapSuggestion>> GenerateGapSuggestionsAsync(
        KnowledgeNode leafNode,
        List<KnowledgeNode> allNodesInWorkspace,
        CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation(
                "Generating gap suggestions for leaf node: {NodeId} - {NodeName}",
                leafNode.Id,
                leafNode.Name);

            // Build context from the leaf node and other nodes in workspace
            var prompt = BuildGapSuggestionPrompt(leafNode, allNodesInWorkspace);

            // Call LLM to generate suggestions
            var llmResponse = await _llmService.GetChatbotResponseAsync(prompt, cancellationToken);

            if (llmResponse?.Message == null || string.IsNullOrWhiteSpace(llmResponse.Message.Content))
            {
                _logger.LogWarning(
                    "LLM returned empty response for node: {NodeId}",
                    leafNode.Id);
                return new List<GapSuggestion>();
            }

            // Parse LLM response to extract gap suggestions
            var suggestions = ParseGapSuggestions(llmResponse.Message.Content, leafNode);

            _logger.LogInformation(
                "Successfully generated {Count} gap suggestions for node: {NodeId}",
                suggestions.Count,
                leafNode.Id);

            return suggestions;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex,
                "Error generating gap suggestions for node: {NodeId}",
                leafNode.Id);
            return new List<GapSuggestion>();
        }
    }

    public async Task<bool> HasGapSuggestionsAsync(string nodeId, CancellationToken cancellationToken = default)
    {
        try
        {
            var node = await _knowledgeTreeRepository.GetNodeByIdAsync(nodeId, cancellationToken);
            return node?.GapSuggestions?.Any() ?? false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking gap suggestions for node: {NodeId}", nodeId);
            return false;
        }
    }

    private string BuildGapSuggestionPrompt(KnowledgeNode leafNode, List<KnowledgeNode> allNodesInWorkspace)
    {
        var promptBuilder = new StringBuilder();

        promptBuilder.AppendLine("You are a knowledge graph expert. Analyze the following leaf node and suggest potential knowledge gaps or areas that need further exploration.");
        promptBuilder.AppendLine();
        promptBuilder.AppendLine("=== LEAF NODE INFORMATION ===");
        promptBuilder.AppendLine($"Name: {leafNode.Name}");
        promptBuilder.AppendLine($"Type: {leafNode.Type}");
        promptBuilder.AppendLine($"Synthesis: {leafNode.Synthesis}");
        promptBuilder.AppendLine($"Level: {leafNode.Level}");
        promptBuilder.AppendLine();

        if (leafNode.Evidences?.Any() == true)
        {
            promptBuilder.AppendLine("=== EVIDENCES ===");
            foreach (var evidence in leafNode.Evidences.Take(3))
            {
                promptBuilder.AppendLine($"- Source: {evidence.SourceName}");
                promptBuilder.AppendLine($"  Text: {evidence.Text.Substring(0, Math.Min(200, evidence.Text.Length))}...");
                promptBuilder.AppendLine();
            }
        }

        promptBuilder.AppendLine("=== OTHER NODES IN WORKSPACE (for context) ===");
        var relevantNodes = allNodesInWorkspace
            .Where(n => n.Id != leafNode.Id)
            .OrderByDescending(n => n.Level)
            .Take(10)
            .ToList();

        foreach (var node in relevantNodes)
        {
            promptBuilder.AppendLine($"- {node.Name} (Level {node.Level}, Type: {node.Type})");
        }

        promptBuilder.AppendLine();
        promptBuilder.AppendLine("=== TASK ===");
        promptBuilder.AppendLine("Based on the leaf node information and workspace context, generate ONE thought-provoking open-ended question that:");
        promptBuilder.AppendLine("- Identifies a knowledge gap or unexplored area");
        promptBuilder.AppendLine("- Encourages users to explore and develop new content");
        promptBuilder.AppendLine("- Connects the current topic to potential future research directions");
        promptBuilder.AppendLine();
        promptBuilder.AppendLine("IMPORTANT REQUIREMENTS:");
        promptBuilder.AppendLine("- Write a single question (one sentence, maximum 50 words)");
        promptBuilder.AppendLine("- DO NOT use markdown formatting (no **, __, *, #, etc.)");
        promptBuilder.AppendLine("- Write in plain text only");
        promptBuilder.AppendLine("- Make it specific to the topic but broad enough to inspire exploration");
        promptBuilder.AppendLine("- DO NOT include explanations or additional context");
        promptBuilder.AppendLine();
        promptBuilder.AppendLine("Example responses:");
        promptBuilder.AppendLine("How might real-time variations in UAV battery levels influence the dynamic selection of relay nodes in energy-constrained aerial networks?");
        promptBuilder.AppendLine();
        promptBuilder.AppendLine("What trade-offs exist between energy-aware scheduling algorithms and overall network performance in space-air-ground integrated systems?");
        promptBuilder.AppendLine();
        promptBuilder.AppendLine("Provide ONLY the question, no additional text, explanations, or formatting.");

        return promptBuilder.ToString();
    }

    private List<GapSuggestion> ParseGapSuggestions(string llmResponse, KnowledgeNode leafNode)
    {
        var suggestions = new List<GapSuggestion>();

        try
        {
            // Clean up the response - remove markdown code blocks, quotes, etc.
            var cleanedResponse = llmResponse.Trim();

            // Remove code blocks
            if (cleanedResponse.StartsWith("```"))
            {
                var firstNewline = cleanedResponse.IndexOf('\n');
                if (firstNewline > 0)
                {
                    cleanedResponse = cleanedResponse[(firstNewline + 1)..];
                }
            }
            if (cleanedResponse.EndsWith("```"))
            {
                cleanedResponse = cleanedResponse[..^3];
            }

            // Remove quotes if the entire response is wrapped in quotes
            cleanedResponse = cleanedResponse.Trim();
            if (cleanedResponse.StartsWith('"') && cleanedResponse.EndsWith('"'))
            {
                cleanedResponse = cleanedResponse[1..^1];
            }

            cleanedResponse = cleanedResponse.Trim();

            _logger.LogDebug("Parsed gap suggestion. Length: {Length}, Preview: {Preview}",
                cleanedResponse.Length,
                cleanedResponse.Length > 200 ? cleanedResponse[..200] + "..." : cleanedResponse);

            // Use the entire cleaned response as the single gap suggestion
            if (!string.IsNullOrWhiteSpace(cleanedResponse))
            {
                suggestions.Add(new GapSuggestion
                {
                    Id = Guid.NewGuid().ToString(),
                    SuggestionText = cleanedResponse,
                    TargetNodeId = leafNode.Id,
                    TargetFileId = leafNode.Evidences?.FirstOrDefault()?.SourceId ?? string.Empty,
                    SimilarityScore = 0.8f
                });

                _logger.LogInformation("Successfully created gap suggestion for node {NodeId}", leafNode.Id);
            }
            else
            {
                _logger.LogWarning("LLM returned empty response for node {NodeId}", leafNode.Id);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing LLM response for node {NodeId}. Response preview: {Response}",
                leafNode.Id,
                llmResponse.Length > 200 ? llmResponse[..200] : llmResponse);
        }

        return suggestions;
    }

}
