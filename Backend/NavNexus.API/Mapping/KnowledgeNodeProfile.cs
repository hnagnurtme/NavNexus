using AutoMapper;

using NavNexus.API.Contract.KnowledgeTree;
using NavNexus.Application.KnowledgeTree.Queries;
using NavNexus.Application.KnowledgeTree.Results;

namespace NavNexus.Api.Mapping.KnowledgeTree;

public class KnowledgeTreeProfile : Profile
{
    public KnowledgeTreeProfile()
    {
        CreateMap<GetKnowledgeNodeRequest, GetKnowledgeNodeQuery>();

        CreateMap<GetKnowledgeNodeResult, GetKnowledgeNodeResponse>();
    }
}