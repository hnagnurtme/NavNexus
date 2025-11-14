using AutoMapper;
using NavNexus.API.Contract.Authentication;
using NavNexus.API.Contract.Workspace;
using NavNexus.Application.Authentication;
using NavNexus.Application.Workspace.Queries;
using NavNexus.Application.Workspace.Results;
namespace NavNexus.Api.Mapping.Authentication;

public class WorkspaceProfile : Profile
{
    public WorkspaceProfile()
    {
        CreateMap<GetWorkspaceDetailsParam, GetWorkspaceDetailsQuery>();
        CreateMap<GetWorkspaceDetailsResult,WorkspaceDetailResponse>();
    }
}