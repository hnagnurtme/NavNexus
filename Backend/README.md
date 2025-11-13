# NavNexus Backend

A clean architecture ASP.NET Core backend with JWT and Firebase authentication support.

## Architecture

The backend follows Clean Architecture principles with clear separation of concerns:

```
Backend/
├── NavNexus.Domain/              # Domain Layer (Entities + Domain Logic)
│   ├── Entities/                 # Domain entities
│   │   ├── Node.cs
│   │   └── Document.cs
│   ├── ValueObjects/             # Value objects
│   ├── Interfaces/               # Domain interfaces
│   └── Exceptions/               # Domain exceptions
│       └── DomainException.cs
│
├── NavNexus.Application/         # Application Layer (Use Cases)
│   ├── Common/
│   │   ├── Behaviours/           # MediatR pipeline behaviors
│   │   │   ├── ValidationBehaviour.cs
│   │   │   └── LoggingBehaviour.cs
│   │   └── Models/
│   │       └── Result.cs         # Result pattern for error handling
│   ├── Features/                 # CQRS Commands & Queries
│   │   ├── Documents/
│   │   │   ├── Commands/
│   │   │   └── Queries/
│   │   └── Nodes/
│   ├── Exceptions/               # Application exceptions
│   │   └── BusinessException.cs
│   └── DependencyInjection.cs
│
├── NavNexus.Infrastructure/      # Infrastructure Layer
│   ├── Persistence/              # Database implementations
│   ├── Services/                 # External services
│   │   └── FirebaseService.cs
│   └── DependencyInjection.cs
│
└── NavNexus.API/                 # Presentation Layer
    ├── Controllers/              # API Controllers
    │   ├── AuthController.cs
    │   ├── NodesController.cs
    │   └── DocumentsController.cs
    ├── Contracts/                # DTOs
    │   ├── Requests/
    │   │   ├── UploadDocumentRequest.cs
    │   │   └── CreateNodeRequest.cs
    │   └── Responses/
    │       ├── ApiResponse.cs
    │       ├── DocumentResponse.cs
    │       └── NodeResponse.cs
    ├── Mapping/                  # AutoMapper profiles
    │   └── ApiMappingProfile.cs
    ├── Filters/                  # Action filters
    │   ├── ValidationFilter.cs
    │   └── AuthorizationFilter.cs
    ├── Middlewares/              # Custom middlewares
    │   ├── FirebaseAuthMiddleware.cs
    │   └── GlobalExceptionHandler.cs
    ├── Constants/                # Constants
    │   └── ErrorConstants.cs
    └── Program.cs
```

## Features

### Authentication
- **JWT Authentication**: Bearer token authentication with configurable key, issuer, and audience
- **Firebase Authentication**: Optional Firebase Auth middleware for Firebase token verification
- Secure endpoints with `[Authorize]` attribute

### Error Handling
- Global exception handler middleware
- Standardized API responses with success/error format
- Custom error codes and messages
- Validation error aggregation

### API Documentation
- Swagger/OpenAPI documentation available at `/swagger`
- Interactive API testing interface

### Security
- JWT token-based authentication
- Input sanitization for logging (prevents log forging)
- CORS configuration
- HTTPS redirection in production

## Prerequisites

- .NET 9.0 SDK or later
- (Optional) Firebase project for Firestore and Firebase Auth

## Getting Started

### 1. Clone the repository

```bash
cd Backend
```

### 2. Configure settings

Update `appsettings.json` with your configuration:

```json
{
  "Jwt": {
    "Key": "your-secret-key-at-least-32-characters-long",
    "Issuer": "NavNexus",
    "Audience": "NavNexusUsers"
  },
  "Firebase": {
    "ProjectId": "your-firebase-project-id"
  }
}
```

### 3. Build the solution

```bash
dotnet build
```

### 4. Run the API

```bash
cd NavNexus.API
dotnet run
```

The API will be available at:
- HTTP: `http://localhost:5000`
- HTTPS: `https://localhost:5001`
- Swagger UI: `http://localhost:5000/swagger`

## API Endpoints

### Authentication

#### Generate JWT Token
```http
POST /api/auth/token
Content-Type: application/json

{
  "userId": "user-123",
  "email": "user@example.com"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGci...",
    "expiresAt": "2025-11-13T15:45:37Z"
  },
  "timestamp": "2025-11-12T15:45:37Z"
}
```

#### Verify Token
```http
GET /api/auth/verify
Authorization: Bearer {token}
```

### Nodes

#### Get All Nodes
```http
GET /api/nodes
Authorization: Bearer {token}
```

#### Get Node by ID
```http
GET /api/nodes/{id}
Authorization: Bearer {token}
```

#### Create Node
```http
POST /api/nodes
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "My Node",
  "content": "Node content",
  "tags": ["tag1", "tag2"],
  "parentNodeId": null
}
```

### Documents

#### Upload Document
```http
POST /api/documents/upload
Authorization: Bearer {token}
Content-Type: application/json

{
  "fileName": "document.pdf",
  "contentType": "application/pdf",
  "fileSize": 1024,
  "storagePath": "/uploads/document.pdf"
}
```

#### Get Document
```http
GET /api/documents/{id}
Authorization: Bearer {token}
```

## Response Format

All API responses follow a standardized format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-11-12T15:45:37Z"
}
```

### Error Response
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Error message",
    "code": "ERROR_CODE",
    "validationErrors": {
      "field1": ["error1", "error2"]
    }
  },
  "timestamp": "2025-11-12T15:45:37Z"
}
```

## Testing

### Manual Testing with cURL

Generate a token:
```bash
curl -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"userId":"test-user","email":"test@example.com"}'
```

Use the token to access protected endpoints:
```bash
TOKEN="your-jwt-token"
curl http://localhost:5000/api/nodes \
  -H "Authorization: Bearer $TOKEN"
```

### Using Swagger UI

1. Navigate to `http://localhost:5000/swagger`
2. Click "Authorize" button
3. Enter token as: `Bearer {your-token}`
4. Test endpoints interactively

## Security Considerations

1. **JWT Secret Key**: Change the default JWT key in production
2. **HTTPS**: Always use HTTPS in production
3. **Firebase Credentials**: Store Firebase service account keys securely
4. **Input Validation**: All inputs are validated using FluentValidation
5. **Log Sanitization**: User inputs are sanitized before logging

## Development

### Adding a New Endpoint

1. **Define Domain Entity** (NavNexus.Domain/Entities/)
2. **Create Command/Query** (NavNexus.Application/Features/)
3. **Add Handler** (in the same file as Command/Query)
4. **Create DTOs** (NavNexus.API/Contracts/)
5. **Add Controller Action** (NavNexus.API/Controllers/)
6. **Map Entities** (NavNexus.API/Mapping/ApiMappingProfile.cs)

### Technology Stack

- **Framework**: ASP.NET Core 9.0
- **Authentication**: JWT Bearer + Firebase Auth
- **Documentation**: Swagger/OpenAPI
- **Validation**: FluentValidation
- **CQRS**: MediatR
- **Mapping**: AutoMapper
- **Database**: Firestore (Google Cloud)
- **Logging**: Microsoft.Extensions.Logging

## License

This project is part of NavNexus and follows the same license.
