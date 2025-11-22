using System.Text;
using ErrorOr;
using MediatR;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Chatbox.Result;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Chatbox.Queries;

public class ChatbotQueryHandler : IRequestHandler<ChatbotQuery, ErrorOr<ChatbotQueryResult>>
{
    private readonly IKnowledgetreeRepository _knowledgeTreeRepository;
    private readonly ILlmService _llmService;
    private readonly ILogger<ChatbotQueryHandler> _logger;

    // Configuration constants
    private const int MaxHistoryItems = 20;
    private const int MaxContextItems = 10;
    private const int MaxChildNodesToInclude = 5;
    private const int MaxSuggestionsFromWorkspace = 5;

    public ChatbotQueryHandler(
        IKnowledgetreeRepository knowledgeTreeRepository,
        ILlmService llmService,
        ILogger<ChatbotQueryHandler> logger)
    {
        _knowledgeTreeRepository = knowledgeTreeRepository ?? throw new ArgumentNullException(nameof(knowledgeTreeRepository));
        _llmService = llmService ?? throw new ArgumentNullException(nameof(llmService));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task<ErrorOr<ChatbotQueryResult>> Handle(ChatbotQuery request, CancellationToken cancellationToken)
    {
        // Validate request
        if (request == null)
        {
            return Error.Validation("ChatbotQuery.NullRequest", "Request cannot be null");
        }

        if (string.IsNullOrWhiteSpace(request.Prompt))
        {
            return Error.Validation("ChatbotQuery.EmptyPrompt", "Prompt cannot be empty or whitespace");
        }

        try
        {
            _logger.LogInformation(
                "Processing chatbot query. Workspace: {WorkspaceId}, Topic: {TopicId}, Prompt length: {PromptLength}",
                request.WorkspaceId ?? "None",
                request.TopicId ?? "None",
                request.Prompt.Length);

            // Safely handle null collections
            var contexts = request.Contexts ?? new List<ChatContext>();
            var history = request.History ?? new List<ChatHistory>();

            // Get node data for enrichment
            KnowledgeNode? currentNode = null;
            if (!string.IsNullOrEmpty(request.TopicId))
            {
                currentNode = await _knowledgeTreeRepository.GetNodeByIdAsync(request.TopicId, cancellationToken);
            }

            // Build context components
            string nodeDataContextString = await BuildNodeDataContextString(request.TopicId, request.WorkspaceId);
            string contextString = BuildChatContextString(contexts);
            string historyString = BuildChatHistoryString(history);

            // Build final prompt
            string finalPrompt = BuildFinalPrompt(request.Prompt, contextString, historyString, nodeDataContextString);

            _logger.LogDebug("Final prompt built. Length: {PromptLength}", finalPrompt.Length);

            // Get response from LLM service
            var response = await _llmService.GetChatbotResponseAsync(finalPrompt, cancellationToken);

            _logger.LogInformation("Successfully received response from LLM service");

            // Enrich response with citations and suggestions
            if (currentNode != null)
            {
                response.Message.Citations = BuildCitations(currentNode);
                response.Message.Suggestions = BuildSuggestions(currentNode);
                response.Message.Source = currentNode.Name;
                response.Message.NodeSnapshot = $"{currentNode.Name} ({currentNode.Type})";
                response.Message.SourceSnapshot = $"{currentNode.SourceCount} sources, Confidence: {currentNode.TotalConfidence:F2}";

                _logger.LogInformation(
                    "Enriched response with {CitationCount} citations and {SuggestionCount} suggestions for node {NodeId}",
                    response.Message.Citations?.Count ?? 0,
                    response.Message.Suggestions?.Count ?? 0,
                    currentNode.Id);
            }
            else
            {
                _logger.LogInformation("No topicId provided - will populate suggestions from workspace");

                // Try to get suggestions from workspace root nodes
                if (!string.IsNullOrEmpty(request.WorkspaceId))
                {
                    try
                    {
                        var rootNodes = await _knowledgeTreeRepository.GetAllRootNodesByWorkspaceIdAsync(request.WorkspaceId, cancellationToken);

                        if (rootNodes.Count > 0)
                        {
                            response.Message.Suggestions = BuildSuggestionsFromRootNodes(rootNodes);
                            response.Message.Source = "General Knowledge Base";
                            response.Message.SourceSnapshot = $"{rootNodes.Count} topics available";

                            _logger.LogInformation(
                                "Added {SuggestionCount} suggestions from {RootNodeCount} workspace topics",
                                response.Message.Suggestions?.Count ?? 0,
                                rootNodes.Count);
                        }
                        else
                        {
                            _logger.LogWarning("Workspace {WorkspaceId} has no root nodes", request.WorkspaceId);
                            response.Message.SourceSnapshot = "No topics available in workspace";
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Failed to retrieve workspace root nodes for workspace {WorkspaceId}", request.WorkspaceId);
                        response.Message.SourceSnapshot = "Unable to retrieve workspace topics";
                    }
                }
                else
                {
                    _logger.LogWarning(
                        "Neither topicId nor workspaceId provided - response will have no context. " +
                        "Please provide at least workspaceId for better suggestions.");
                    response.Message.SourceSnapshot = "No context provided (missing topicId and workspaceId)";
                }
            }

            return response;
        }
        catch (OperationCanceledException)
        {
            _logger.LogWarning("Chatbot query was cancelled");
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing chatbot query for workspace {WorkspaceId}", request.WorkspaceId);
            return Error.Failure("ChatbotQueryHandler.ExecutionFailed", $"Failed to process chatbot query: {ex.Message}");
        }
    }

    private async Task<string> BuildNodeDataContextString(string? nodeId, string? workspaceId)
    {
        if (string.IsNullOrEmpty(nodeId))
        {
            return string.Empty;
        }

        try
        {
            var node = await _knowledgeTreeRepository.GetNodeByIdAsync(nodeId);
            if (node == null)
            {
                _logger.LogWarning("Node with ID {NodeId} not found", nodeId);
                return string.Empty;
            }

            var sb = new StringBuilder();

            // Add main node information
            sb.AppendLine($"Topic: {node.Name}");
            sb.AppendLine($"Type: {node.Type}");

            if (!string.IsNullOrWhiteSpace(node.Synthesis))
            {
                sb.AppendLine();
                sb.AppendLine("Summary:");
                sb.AppendLine(node.Synthesis.Trim());
            }

            // Add evidences with source information
            if (node.Evidences?.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine($"Supporting Evidence ({node.Evidences.Count} sources):");

                foreach (var evidence in node.Evidences.Take(MaxContextItems))
                {
                    if (!string.IsNullOrWhiteSpace(evidence.Text))
                    {
                        sb.AppendLine();
                        sb.AppendLine($"[Source: {evidence.SourceName} | Page: {evidence.Page} | Confidence: {evidence.Confidence:F2}]");
                        sb.AppendLine(evidence.Text.Trim());

                        if (evidence.KeyClaims?.Count > 0)
                        {
                            sb.AppendLine("Key Claims:");
                            foreach (var claim in evidence.KeyClaims.Take(3))
                            {
                                sb.AppendLine($"  • {claim}");
                            }
                        }
                    }
                }
                sb.AppendLine();
            }
            // Add children information (limited to prevent overly long prompts)
            if (node.Children?.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine($"Related Subtopics ({node.Children.Count} available):");

                foreach (var child in node.Children.Take(MaxChildNodesToInclude))
                {
                    sb.AppendLine();
                    sb.AppendLine($"→ {child.Name}");

                    if (!string.IsNullOrWhiteSpace(child.Synthesis))
                    {
                        sb.AppendLine($"  {child.Synthesis}");
                    }

                    // Add a couple of key evidences from child nodes
                    if (child.Evidences?.Count > 0)
                    {
                        var keyEvidences = child.Evidences
                            .Where(e => !string.IsNullOrWhiteSpace(e.Text))
                            .OrderByDescending(e => e.Confidence)
                            .Take(2); // Top 2 by confidence

                        if (keyEvidences.Any())
                        {
                            foreach (var evidence in keyEvidences)
                            {
                                sb.AppendLine($"  • {evidence.Text.Trim()}");
                            }
                        }
                    }
                }
            }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error building node data context for node {NodeId}", nodeId);
            return string.Empty;
        }
    }

    private string BuildChatContextString(List<ChatContext> contexts)
    {
        if (contexts.Count == 0)
        {
            return string.Empty;
        }

        var limitedContexts = contexts.Take(MaxContextItems);
        var contextStrings = limitedContexts.Select(c => $"{c.Type}: {c.Label} (ID: {c.Id})");
        
        var sb = new StringBuilder();
        sb.AppendLine("=== CONTEXT ===");
        sb.AppendLine(string.Join("\n", contextStrings));
        sb.AppendLine();
        
        return sb.ToString();
    }

    private string BuildChatHistoryString(List<ChatHistory> history)
    {
        if (history.Count == 0)
        {
            return string.Empty;
        }

        var limitedHistory = history
            .Where(h => !string.IsNullOrWhiteSpace(h.Content))
            .TakeLast(MaxHistoryItems); // Take most recent items

        if (!limitedHistory.Any())
        {
            return string.Empty;
        }

        var sb = new StringBuilder();
        sb.AppendLine("=== CHAT HISTORY ===");
        
        foreach (var item in limitedHistory)
        {
            sb.AppendLine($"{item.Role.ToUpperInvariant()}: {item.Content.Trim()}");
        }
        
        sb.AppendLine();
        return sb.ToString();
    }

    private static List<ChatCitationResult> BuildCitations(KnowledgeNode node)
    {
        var citations = new List<ChatCitationResult>();

        if (node.Evidences == null || node.Evidences.Count == 0)
        {
            return citations;
        }

        // Get top evidences by confidence
        var topEvidences = node.Evidences
            .Where(e => !string.IsNullOrWhiteSpace(e.Text))
            .OrderByDescending(e => e.Confidence)
            .Take(MaxContextItems);

        foreach (var evidence in topEvidences)
        {
            citations.Add(new ChatCitationResult
            {
                Id = evidence.Id,
                Label = evidence.SourceName,
                Type = "evidence",
                Snippet = evidence.Text.Length > 200
                    ? evidence.Text[..197] + "..."
                    : evidence.Text,
                Confidence = evidence.Confidence.ToString("F2")
            });
        }

        return citations;
    }

    private static List<ChatSuggestionResult> BuildSuggestions(KnowledgeNode node)
    {
        var suggestions = new List<ChatSuggestionResult>();

        // Add suggestions from related topics (children)
        if (node.Children?.Count > 0)
        {
            foreach (var child in node.Children.Take(3))
            {
                suggestions.Add(new ChatSuggestionResult
                {
                    Id = child.Id,
                    Prompt = $"Tell me more about {child.Name}"
                });
            }
        }

        // Add suggestions from gap suggestions
        if (node.GapSuggestions?.Count > 0)
        {
            foreach (var gap in node.GapSuggestions.Take(2))
            {
                if (!string.IsNullOrWhiteSpace(gap.SuggestionText))
                {
                    suggestions.Add(new ChatSuggestionResult
                    {
                        Id = gap.Id,
                        Prompt = gap.SuggestionText
                    });
                }
            }
        }

        // Add general exploration suggestions if we don't have enough
        if (suggestions.Count < 3 && node.Evidences?.Count > 0)
        {
            var questionsFromEvidences = node.Evidences
                .SelectMany(e => e.QuestionsRaised ?? [])
                .Where(q => !string.IsNullOrWhiteSpace(q))
                .Take(3 - suggestions.Count);

            foreach (var question in questionsFromEvidences)
            {
                suggestions.Add(new ChatSuggestionResult
                {
                    Id = Guid.NewGuid().ToString(),
                    Prompt = question
                });
            }
        }

        return suggestions;
    }

    private static List<ChatSuggestionResult> BuildSuggestionsFromRootNodes(List<KnowledgeNode> rootNodes)
    {
        var suggestions = new List<ChatSuggestionResult>();

        // Get top nodes by confidence or source count
        var topNodes = rootNodes
            .OrderByDescending(n => n.TotalConfidence)
            .ThenByDescending(n => n.SourceCount)
            .Take(MaxSuggestionsFromWorkspace);

        foreach (var node in topNodes)
        {
            suggestions.Add(new ChatSuggestionResult
            {
                Id = node.Id,
                Prompt = $"Tell me about {node.Name}"
            });
        }

        return suggestions;
    }

    private string BuildFinalPrompt(string userPrompt, string contextString, string historyString, string nodeDataContextString)
    {
        var sb = new StringBuilder();

        // Add system instructions
        sb.AppendLine("=== SYSTEM INSTRUCTIONS ===");
        sb.AppendLine("You are a knowledgeable assistant with access to a structured knowledge base.");
        sb.AppendLine();
        sb.AppendLine("Response Guidelines:");
        sb.AppendLine("- Provide concise, direct answers (aim for 2-4 paragraphs maximum)");
        sb.AppendLine("- Focus on the most important points from the evidence");
        sb.AppendLine("- Reference sources when making claims");
        sb.AppendLine("- If information is unavailable, state it clearly and briefly");
        sb.AppendLine("- Maintain conversation context");
        sb.AppendLine("- Be clear and professional");
        sb.AppendLine();
        sb.AppendLine("IMPORTANT FORMATTING RULES:");
        sb.AppendLine("- DO NOT use markdown formatting (no **, __, *, #, etc.)");
        sb.AppendLine("- Write in plain text only");
        sb.AppendLine("- Use simple paragraphs separated by line breaks");
        sb.AppendLine("- For lists, use simple dash (-) or numbers without special formatting");
        sb.AppendLine();

        // Add knowledge base context
        if (!string.IsNullOrWhiteSpace(nodeDataContextString))
        {
            sb.AppendLine("=== KNOWLEDGE BASE CONTEXT ===");
            sb.AppendLine(nodeDataContextString);
        }

        // Add conversation context
        if (!string.IsNullOrWhiteSpace(contextString))
        {
            sb.AppendLine(contextString);
        }

        // Add chat history
        if (!string.IsNullOrWhiteSpace(historyString))
        {
            sb.AppendLine(historyString);
        }

        // Add the current user question
        sb.AppendLine("=== USER QUESTION ===");
        sb.AppendLine(userPrompt.Trim());
        sb.AppendLine();
        sb.AppendLine("Provide a concise, well-structured answer focusing on key points.");

        return sb.ToString();
    }
}