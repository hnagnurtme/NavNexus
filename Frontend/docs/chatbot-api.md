# Chatbot API Contract (Preview)

This doc tracks the request/response shape the React client expects when the AI chatbot endpoint becomes available. Keep it up to date with any backend changes—`src/types/chatbot.types.ts` mirrors the details below.

## Endpoint

- **Method:** `POST`
- **Path:** `/chatbot/query` (see `CHATBOT_ENDPOINT` inside `src/services/chatbot.service.ts`)
- **Headers:** `Content-Type: application/json` plus the standard `Authorization: Bearer <token>` automatically set by `apiClient`.

## Request Body (`ChatbotQueryRequest`)

```jsonc
{
  "prompt": "What evidence connects Project Helios to Sunrise Corp?",
  "workspaceId": "ws-123",
  "topicId": "Project Helios",
  "contexts": [
    {
      "id": "node-helios",
      "entityId": "node-helios",
      "type": "node",
      "label": "Project Helios"
    },
    {
      "id": "file-brief",
      "entityId": "file-brief",
      "type": "file",
      "label": "Helios briefing.pdf"
    }
  ],
  "history": [
    {
      "role": "user",
      "content": "Give me a quick status update on Project Helios",
      "timestamp": 1736532000000
    },
    {
      "role": "ai",
      "content": "Here is the latest synthesis ...",
      "timestamp": 1736532010000,
      "nodeSnapshot": "Project Helios",
      "sourceSnapshot": "Project Helios dossier",
      "source": "Workspace knowledge base"
    }
  ]
}
```

- `prompt` is required.
- `workspaceId`/`topicId` are optional but enable backend grounding. `topicId` should be the `nodeId` returned by the knowledge-tree API for the currently selected node.
- `contexts` mirrors the chips users pin in the UI. Each entry must include a `type` of `node` or `file` today; extend the union if new context types ship. When the context references a knowledge node or evidence already known to the system, populate both `id` and `entityId` with the canonical identifier (free-form contexts will omit `entityId`).
- `history` includes the full conversation so the model can stay stateful. `nodeSnapshot`, `sourceSnapshot`, and `source` should simply echo what the UI showed for previous AI responses.

## Response Body (`ChatbotQueryResponse`)

```jsonc
{
  "success": true,
  "message": "Chatbot response",
  "statusCode": 200,
  "errorCode": null,
  "meta": null,
  "data": {
    "message": {
      "id": "ai-1736532055000",
      "role": "ai",
      "content": "Here is how this connects back to Project Helios...",
      "source": "Project Helios dossier",
      "nodeSnapshot": "Project Helios",
      "sourceSnapshot": "Project Helios dossier",
      "citations": [
        {
          "id": "file-brief",
          "label": "Helios briefing.pdf",
          "type": "file",
          "snippet": "Slide 7 links Sunrise Corp to the procurement trail.",
          "confidence": "high"
        }
      ],
      "suggestions": [
        {
          "id": "suggestion-1",
          "prompt": "List outstanding data gaps for Project Helios."
        }
      ]
    },
    "usage": {
      "promptTokens": 421,
      "completionTokens": 180,
      "totalTokens": 601
    }
  }
}
```

- The top-level wrapper matches `ApiResponse<T>` used throughout the app.
- `message` is required and should always carry `id`, `role: "ai"`, and `content`.
- `nodeSnapshot`/`sourceSnapshot` populate the chips rendered under each AI bubble. If the backend omits them, the UI falls back to plain text.
- `citations` (optional) should list the most relevant nodes/files used; they enable future evidence previews.
- `suggestions` (optional) power follow-up prompt chips.
- `usage` mirrors typical LLM accounting and is optional.

## Environment Flags

- `VITE_USE_CHATBOT_MOCK`: when absent or set to anything other than `"false"`, the client uses `mockChatbotQuery` instead of the real API. Set `VITE_USE_CHATBOT_MOCK=false` in `.env.development` once the backend endpoint is live.
- Future enhancement: add `VITE_CHATBOT_ENDPOINT` to override `/chatbot/query` if the backend exposes the chatbot elsewhere.

## Error Handling

- Standard HTTP status codes apply. The client catches non-2xx responses and shows “The chatbot is unavailable right now. Please try again.”
- Include a descriptive `message` and `errorCode` in the ApiResponse payload to help with observability/logging.
