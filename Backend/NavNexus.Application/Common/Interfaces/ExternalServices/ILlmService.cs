using NavNexus.Application.Chatbox.Result;

namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface ILlmService
{
    Task<ChatbotQueryResult> GetChatbotResponseAsync(string prompt , CancellationToken cancellationToken = default);
}
