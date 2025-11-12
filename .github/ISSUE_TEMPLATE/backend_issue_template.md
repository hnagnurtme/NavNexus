---
name: "⚙️ Backend Feature"
about: "Add or improve a backend API/service for NavNexus platform"
title: "[Backend] <feature-name>"
labels: ["backend", "feature"]
assignees: ""
---

## 🎯 Overview
Describe the backend functionality to be implemented.

---

## 📡 API Contract

### Endpoint
| Method | Endpoint | Auth Required |
|--------|----------|---------------|
| `POST` | `/api/auth/login` | ❌ No |

### Request Schema
```json
{
  "email": "string",
  "password": "string"
}
```

### Response Schema
```json
{
  "success": true,
  "data": {
    "token": "string",
    "userId": "string",
    "expiresAt": "string"
  },
  "error": null
}
```

### Error Response
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

### Constants

**Status Codes**
```
200 - Success
400 - Bad Request
401 - Unauthorized
500 - Internal Server Error
```

**Error Codes**
```csharp
public static class ErrorCodes {
    public const string INVALID_CREDENTIALS = "INVALID_CREDENTIALS";
    public const string ACCOUNT_LOCKED = "ACCOUNT_LOCKED";
    public const string SERVER_ERROR = "SERVER_ERROR";
}
```

---

## 🔗 Related Issues
**Frontend Issue:** #<issue-number>
