---
name: "🎨 Frontend Feature"
about: "Add or improve a UI component/page for NavNexus platform"
title: "[Frontend] <feature-name>"
labels: ["frontend", "feature"]
assignees: ""
---

## 🎯 Overview
Describe the user-facing feature to be implemented.

---

## 📡 API Integration

### Endpoint (from Backend Issue #<number>)
```
POST /api/auth/login
```

### Request Schema
```typescript
interface LoginRequest {
  email: string;
  password: string;
}
```

### Response Schema
```typescript
interface LoginResponse {
  success: boolean;
  data: {
    token: string;
    userId: string;
    expiresAt: string;
  } | null;
  error: {
    code: string;
    message: string;
  } | null;
}
```

### Constants

**Error Codes**
```typescript
export const ErrorCodes = {
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  ACCOUNT_LOCKED: 'ACCOUNT_LOCKED',
  SERVER_ERROR: 'SERVER_ERROR'
} as const;

export const ErrorMessages: Record<string, string> = {
  INVALID_CREDENTIALS: 'Email hoặc mật khẩu không đúng',
  ACCOUNT_LOCKED: 'Tài khoản đã bị khóa',
  SERVER_ERROR: 'Lỗi hệ thống, vui lòng thử lại'
};
```

**Status Codes**
```typescript
export const StatusCodes = {
  SUCCESS: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  SERVER_ERROR: 500
} as const;
```

---

## 🔗 Related Issues
**Backend Issue:** #<issue-number>
