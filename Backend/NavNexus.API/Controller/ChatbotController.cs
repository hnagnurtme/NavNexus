namespace NavNexus.API.Controller;

using AutoMapper;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using NavNexus.API.Common;
using NavNexus.API.Contract.Chatbox;
using NavNexus.Application.Chatbox.Queries;
using NavNexus.Application.Chatbox.Result;
using Swashbuckle.AspNetCore.Annotations;

[ApiController]
[Route("api/chatbot")]
public class ChatbotController : ControllerBase
{
    private readonly IMediator _mediator;

    private readonly IMapper _mapper;

    public ChatbotController(IMediator mediator , IMapper mapper)
    {
        _mediator = mediator;
        _mapper = mapper;
    }   
    [HttpPost("query")]
    [SwaggerOperation(Summary = "Query Chatbot", Description = "Send a query to the chatbot and receive a response.")]
    [ProducesResponseType(typeof(ApiResponse<ChatbotQueryResponseData>), StatusCodes.Status200OK)]

    public async Task<IActionResult> QueryChatbot([FromBody] ChatbotQueryRequest request)
    {
        var query = _mapper.Map<ChatbotQueryRequest, ChatbotQuery>(request);

        var result = await _mediator.Send(query);
        var response = result.MapTo<ChatbotQueryResult, ChatbotQueryResponseData>(_mapper);
        return OK.HandleResult(response, "Chatbot query processed successfully");
    }
}