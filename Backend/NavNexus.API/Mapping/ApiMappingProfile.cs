using AutoMapper;
using NavNexus.API.Contracts.Responses;
using NavNexus.Domain.Entities;

namespace NavNexus.API.Mapping;

public class ApiMappingProfile : Profile
{
    public ApiMappingProfile()
    {
        CreateMap<Document, DocumentResponse>()
            .ForMember(dest => dest.Status, opt => opt.MapFrom(src => src.Status.ToString()));

        CreateMap<Node, NodeResponse>();
    }
}
