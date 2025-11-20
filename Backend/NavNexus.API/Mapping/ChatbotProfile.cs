using AutoMapper;
using NavNexus.API.Contract.Chatbox;
using NavNexus.Application.Chatbox.Queries;
using NavNexus.Application.Chatbox.Result;

namespace NavNexus.Api.Mapping.Authentication;

public class ChatbotProfile : Profile
{
    public ChatbotProfile()
    {
        // Request → Query mappings
        CreateMap<ChatbotQueryRequest, ChatbotQuery>()
            .ConstructUsing(src => new ChatbotQuery(
                src.Prompt,
                src.WorkspaceId,
                src.TopicId,
                new List<ChatContext>(),
                new List<ChatHistory>()
            ))
            .ForMember(dest => dest.Contexts, opt => opt.MapFrom(src => src.Contexts))
            .ForMember(dest => dest.History, opt => opt.MapFrom(src => src.History));

        CreateMap<ChatContextItem, ChatContext>()
            .ConstructUsing(src => new ChatContext(
                src.Id,
                src.EntityId,
                src.Type,
                src.Label
            ));

        CreateMap<ChatHistoryItem, ChatHistory>()
            .ConstructUsing(src => new ChatHistory(
                src.Role,
                src.Content,
                src.Timestamp,
                src.NodeSnapshot,
                src.SourceSnapshot,
                src.Source
            ));

        // Result → Response mappings
        CreateMap<ChatbotQueryResult, ChatbotQueryResponseData>();

        CreateMap<ChatbotMessageResult, ChatbotMessageResponse>()
            .ForMember(dest => dest.Citations, opt => opt.MapFrom(src => src.Citations))
            .ForMember(dest => dest.Suggestions, opt => opt.MapFrom(src => src.Suggestions));

        CreateMap<ChatCitationResult, ChatCitationItem>();
        CreateMap<ChatSuggestionResult, ChatSuggestionItem>();
        CreateMap<ChatbotUsageResult, ChatbotUsage>();
    }
}
