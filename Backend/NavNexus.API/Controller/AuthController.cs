using AutoMapper;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using ErrorOr;
using Swashbuckle.AspNetCore.Annotations;
using NavNexus.API.Common;
using NavNexus.API.Contract.Authentication;
using NavNexus.Application.Authentication;

namespace NavNexus.API.Controller;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IMapper _mapper;

    public AuthController(IMediator mediator, IMapper mapper)
    {
        _mediator = mediator;
        _mapper = mapper;
    }

    [HttpPost("register")]
    [SwaggerOperation(Summary = "Register account", Description = "Create a new user account with the provided registration information.")]
    [ProducesResponseType(typeof(ApiResponse<AuthenticationResponse>), StatusCodes.Status201Created)]
    public async Task<IActionResult> Register([FromBody] RegisterRequest request)
    {
        var command = _mapper.Map<RegisterCommand>(request);
        var result = await _mediator.Send(command);
        var response = result.MapTo<AuthenticationResult, AuthenticationResponse>(_mapper);
        return OK.HandleResult(response, "Register success");
    }

    [HttpPost("login")]
    [SwaggerOperation(Summary = "Login", Description = "Authenticate user and return a JWT token.")]
    [ProducesResponseType(typeof(ApiResponse<AuthenticationResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> Login([FromBody] LoginRequest request)
    {
        var query = _mapper.Map<LoginQuery>(request);
        var result = await _mediator.Send(query);
        var response = result.MapTo<AuthenticationResult, AuthenticationResponse>(_mapper);
        return OK.HandleResult(response, "Login success");
    }

    [HttpPost("refresh-token")]
    [SwaggerOperation(Summary = "Generate refresh token", Description = "Generate a new refresh token for the authenticated user.")]
    [ProducesResponseType(typeof(ApiResponse<RefreshTokenResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> RefreshToken([FromBody] RefreshTokenRequest request)
    {
        var command = _mapper.Map<ValidateRefreshTokenCommand>(request);
        var result = await _mediator.Send(command);
        var response = result.MapTo<AuthenticationResult, AuthenticationResponse>(_mapper);
        return OK.HandleResult(response, "Refresh token success");
    }

    [HttpGet("verify-email")]
    [SwaggerOperation(Summary = "Verify email", Description = "Verify user's email using the provided token.")]
    [ProducesResponseType(typeof(ApiResponse<AuthenticationResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> VerifyEmail([FromQuery] VerifyEmailParam request)
    {
        var query = _mapper.Map<VerifyEmailQuery>(request);
        var result = await _mediator.Send(query);
        var response = result.MapTo<AuthenticationResult, AuthenticationResponse>(_mapper);
        return OK.HandleResult(response, "Email verified successfully");
    }
}
