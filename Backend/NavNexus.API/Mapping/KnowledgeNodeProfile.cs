using AutoMapper;

using NavNexus.API.Contract.KnowledgeTree;
using NavNexus.Application.KnowledgeTree.Commands;
using NavNexus.Application.KnowledgeTree.Queries;
using NavNexus.Application.KnowledgeTree.Results;
using NavNexus.Domain.Entities;

namespace NavNexus.Api.Mapping.KnowledgeTree;

public class KnowledgeTreeProfile : Profile
{
    public KnowledgeTreeProfile()
    {
        CreateMap<GetKnowledgeNodeRequest, GetKnowledgeNodeQuery>();
        CreateMap<KnowledgeNode, GetKnowledgeNodeResponse>()
            .ForMember(dest => dest.NodeId,      opt => opt.MapFrom(src => src.Id))
            .ForMember(dest => dest.NodeName,    opt => opt.MapFrom(src => src.Name))
            .ForMember(dest => dest.Description, opt => opt.MapFrom(src => src.Synthesis))
            .ForMember(dest => dest.Tags,        opt => opt.MapFrom(src =>
                new List<string> { src.Type }))
            .ForMember(dest => dest.Level,       opt => opt.MapFrom(src => src.Level))
            .ForMember(dest => dest.SourceCount, opt => opt.MapFrom(src => src.SourceCount))
            .ForMember(dest => dest.Evidences,   opt => opt.Ignore())
            .ForMember(dest => dest.ChildNodes,  opt => opt.MapFrom(src => src.Children))
            .ForMember(dest => dest.CreatedAt,   opt => opt.MapFrom(src => src.CreatedAt))
            .ForMember(dest => dest.UpdatedAt,   opt => opt.MapFrom(src => src.UpdatedAt))
            .ForMember(dest => dest.GapSuggestions, opt => opt.Ignore());

        CreateMap<GapSuggestion, GapSuggestionResponse>();
        
        CreateMap<GetKnowledgeNodeResult, GetKnowledgeNodeResponse>()
            .ForMember(dest => dest.NodeId,      opt => opt.MapFrom(src => src.Id))
            .ForMember(dest => dest.NodeName,    opt => opt.MapFrom(src => src.Name))
            .ForMember(dest => dest.Description, opt => opt.MapFrom(src => src.Synthesis))
            .ForMember(dest => dest.Tags,        opt => opt.MapFrom(src =>
                new List<string> { src.Type }))
            .ForMember(dest => dest.Level,       opt => opt.MapFrom(src => src.Level))
            .ForMember(dest => dest.SourceCount, opt => opt.MapFrom(src => src.SourceCount))
            .ForMember(dest => dest.Evidences,   opt => opt.MapFrom(src => src.Evidences))
            .ForMember(dest => dest.CreatedAt,   opt => opt.MapFrom(src => src.CreatedAt))
            .ForMember(dest => dest.UpdatedAt,   opt => opt.MapFrom(src => src.UpdatedAt))
            .ForMember(dest => dest.ChildNodes,  opt => opt.MapFrom(src => src.ChildNodes))
            .ForMember(dest => dest.GapSuggestions, 
                opt => opt.MapFrom(src => src.GapSuggestions));
        
        CreateMap<RabbitMqSendingResult, RabbitMqSendingResponse>();

        CreateMap<CreatedKnowledgetreeRequest, CreateKnowledgeNodeCommand>();
        
        CreateMap<Evidence, EvidenceResponse>()
            .ForMember(dest => dest.EvidenceId, opt => opt.MapFrom(src => src.Id))
            .ForMember(dest => dest.Content, opt => opt.MapFrom(src => src.Text))
            .ForMember(dest => dest.SourceFileId, opt => opt.MapFrom(src => src.SourceId))
            .ForMember(dest => dest.Claims, opt => opt.MapFrom(src => src.Concepts));

        CreateMap<GapSuggestion, GapSuggestionResponse>()
            .ForMember(dest => dest.Id ,opt => opt.MapFrom(src => src.Id))
            .ForMember(dest => dest.SuggestionText, opt => opt.MapFrom(src => src.SuggestionText))
            .ForMember(dest => dest.TargetNodeId, opt => opt.MapFrom(src => src.TargetNodeId))
            .ForMember(dest => dest.TargetFileId, opt => opt.MapFrom(src => src.TargetFileId))
            .ForMember(dest => dest.SimilarityScore, opt => opt.MapFrom(src => src.SimilarityScore));

    }
}