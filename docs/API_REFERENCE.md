# NavNexus API Reference

This document provides a comprehensive mapping of all API endpoints from `swagger.json` to help developers understand the complete API surface.

Generated from: `docs/swagger.json`  
OpenAPI Version: 3.0.1  
API Version: v1

---

## Authentication Endpoints

### POST /api/auth/register
**Summary:** Register account  
**Description:** Create a new user account with the provided registration information.

**Request Body:**
```typescript
{
  email: string;           // User's email address
  password: string;        // User's password
  fullName: string;        // User's full name
  phoneNumber: string;     // User's phone number
}
```

**Response 201 (Created):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    refreshToken: string | null;
    accessToken: string | null;
    id: string;              // UUID format
    email: string | null;
    fullName: string | null;
    phoneNumber: string | null;
    emailVerified: boolean;
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### POST /api/auth/login
**Summary:** Login  
**Description:** Authenticate user and return a JWT token.

**Request Body:**
```typescript
{
  email: string;              // User's email address
  password: string;           // User's password
  ipAddress: string;          // The IP address of the client
  userAgent: string;          // The User-Agent string of the client
  deviceFingerprint?: string; // Optional device fingerprint
}
```

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    refreshToken: string | null;
    accessToken: string | null;
    id: string;              // UUID format
    email: string | null;
    fullName: string | null;
    phoneNumber: string | null;
    emailVerified: boolean;
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### POST /api/auth/refresh-token
**Summary:** Generate refresh token  
**Description:** Generate a new refresh token for the authenticated user.

**Request Body:**
```typescript
{
  userId: string;             // UUID format
  token: string;
  ipAddress: string;
  userAgent: string;
  deviceFingerprint?: string;
}
```

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    token: string | null;
    expiresAt: string;       // ISO 8601 date-time format
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### GET /api/auth/verify-email
**Summary:** Verify email  
**Description:** Verify user's email using the provided token.

**Query Parameters:**
- `Email` (string, optional)
- `Token` (string, optional)

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    refreshToken: string | null;
    accessToken: string | null;
    id: string;
    email: string | null;
    fullName: string | null;
    phoneNumber: string | null;
    emailVerified: boolean;
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

## Workspace Endpoints

### GET /api/workspace
**Summary:** Get workspace details by user ID  
**Description:** Retrieve details of a specific workspace by its ID.

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    workspaceId: string;
    name: string;
    description: string;
    ownerId: string;
    ownerName: string;
    fileIds: string[];
    createdAt: string;       // ISO 8601 date-time format
    updatedAt: string;       // ISO 8601 date-time format
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### POST /api/workspace
**Summary:** Create a new workspace  
**Description:** Create a new workspace with the provided details.

**Request Body:**
```typescript
{
  name: string;              // Required
  description?: string;      // Optional
  fileIds?: string[];        // Optional array of file IDs
}
```

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    workspaceId: string;
    name: string;
    description: string;
    ownerId: string;
    ownerName: string;
    fileIds: string[];
    createdAt: string;
    updatedAt: string;
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### GET /api/workspace/{userId}
**Summary:** Get workspace details  
**Description:** Retrieve details of a specific workspace by its ID.

**Path Parameters:**
- `userId` (string, required)

**Query Parameters:**
- `workspaceId` (string, optional)

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    workspaceId: string;
    name: string;
    description: string;
    ownerId: string;
    ownerName: string;
    fileIds: string[];
    createdAt: string;
    updatedAt: string;
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

## Knowledge Tree Endpoints

### GET /api/knowledge-tree/{workspaceId}
**Summary:** Get Knowledge Node  
**Description:** Retrieve a knowledge node by its ID within a specified workspace.

**Path Parameters:**
- `workspaceId` (string, required)

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    nodeId: string;
    nodeName: string;
    description: string;
    tags: string[];
    level: number;           // Integer
    sourceCount: number;     // Integer
    evidences: Evidence[];   // See Evidence schema below
    createdAt: string;       // ISO 8601 date-time
    updatedAt: string;       // ISO 8601 date-time
    childNodes: GetKnowledgeNodeResponse[];  // Recursive
    gapSuggestions?: GapSuggestion[];       // Optional
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### GET /api/knowledge-tree/node/{nodeId}
**Summary:** Get Knowledge Node by ID  
**Description:** Retrieve a knowledge node by its ID.

**Path Parameters:**
- `nodeId` (string, required)

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    nodeId: string;
    nodeName: string;
    description: string;
    tags: string[];
    level: number;
    sourceCount: number;
    evidences: Evidence[];
    createdAt: string;
    updatedAt: string;
    childNodes: GetKnowledgeNodeResponse[];
    gapSuggestions?: GapSuggestion[];
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

### POST /api/knowledge-tree
**Summary:** Create Knowledge Tree  
**Description:** Create a knowledge tree for a specified workspace using provided file paths.

**Request Body:**
```typescript
{
  workspaceId: string;       // Required
  filePaths: string[];       // Required array of file paths
}
```

**Response 200 (OK):**
```typescript
{
  success: boolean;
  message: string | null;
  data: {
    messageId: string;
    sentAt: string;          // ISO 8601 date-time
  };
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
}
```

---

## Health Check Endpoint

### GET /api/health
**Summary:** Health check  
**Description:** Check if the API is running.

**Response 200 (OK):**
- No content

---

## Schema Definitions

### Evidence
```typescript
{
  id?: string;
  sourceId?: string;
  sourceName?: string;
  chunkId?: string;
  text?: string;
  page?: number;              // Integer
  confidence?: number;        // Float (0-1)
  createdAt?: string;         // ISO 8601 date-time
  language?: string;
  sourceLanguage?: string;
  hierarchyPath?: string;
  concepts?: string[];
  keyClaims?: string[];
  questionsRaised?: string[];
  evidenceStrength?: number;  // Float (0-1)
}
```

### GapSuggestion
```typescript
{
  id?: string;
  suggestionText?: string;
  targetNodeId?: string;
  targetFileId?: string;
  similarityScore?: number;   // Float (0-1)
}
```

---

## Authentication

All endpoints except `/api/health`, `/api/auth/register`, and `/api/auth/login` require authentication.

**Security Scheme:** Bearer Token  
**Header:** `Authorization: Bearer {token}`

The access token is obtained from the login or register response and should be included in the Authorization header for all protected endpoints.

---

## Field Mapping Summary

### Login/Register Response → Frontend Usage
- `accessToken` → Store in `localStorage` as `auth_token`
- `refreshToken` → **Not stored** (access token is long-lived)
- `id` → User ID (UUID)
- `email` → User email
- `fullName` → Display name
- `phoneNumber` → User phone
- `emailVerified` → Email verification status

### Workspace Response → UI Display
- `workspaceId` → Unique identifier
- `name` → Workspace title
- `description` → Workspace description
- `ownerId` → Owner user ID
- `ownerName` → **Display in UI** (e.g., "Owner: John Doe")
- `fileIds` → **Display count** (e.g., "5 documents")
- `createdAt` → **Display formatted** (e.g., "Created: Jan 15, 2024")
- `updatedAt` → **Display formatted** (e.g., "Updated: 2 days ago")

### Knowledge Node Response → UI Display
- `nodeId` → Unique identifier
- `nodeName` → Node title
- `description` → Node description/synthesis
- `tags` → **Display as badges**
- `level` → Tree depth level
- `sourceCount` → **Display as "5 sources"**
- `evidences` → **Display in ForensicPanel**
- `createdAt` → Node creation timestamp
- `updatedAt` → Last update timestamp
- `childNodes` → Nested child nodes (recursive)
- `gapSuggestions` → **Display AI suggestions for gaps**

### Evidence Fields → UI Display
- `sourceName` → Document title
- `text` → Evidence text content
- `hierarchyPath` → Location in document (e.g., "Page 3, Section 2.1")
- `page` → Page number
- `confidence` → **Display as percentage** (e.g., "92% confidence")
- `concepts` → Key concepts extracted
- `keyClaims` → Important claims from evidence
- `questionsRaised` → Questions identified
- `evidenceStrength` → Strength score (0-1)

---

## Notes

1. **Access Token Lifetime**: Per requirements, access tokens are long-lived. No refresh token logic is needed in the frontend.

2. **Date Formats**: All dates are in ISO 8601 format (e.g., "2024-01-15T10:30:00Z")

3. **Nullable Fields**: Fields marked with `| null` may be null in responses

4. **Optional Fields**: Fields marked with `?` may be omitted from requests/responses

5. **Recursive Structures**: `GetKnowledgeNodeResponse.childNodes` is recursive, allowing infinite tree depth

6. **RabbitMQ Integration**: The `POST /api/knowledge-tree` endpoint returns a message ID and timestamp, indicating asynchronous processing via RabbitMQ
