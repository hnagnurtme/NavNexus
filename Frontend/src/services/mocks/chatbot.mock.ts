import type {
  ChatbotContextItemPayload,
  ChatbotQueryRequest,
  ChatbotQueryResponseApiResponse,
} from '@/types';

const delay = (ms: number) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

const resolvePrimaryTopic = (
  payload: ChatbotQueryRequest
): { label: string; source: string } => {
  const matchingContext = payload.contexts.find(
    (entry) =>
      entry.type === 'node' && entry.entityId && entry.entityId === payload.topicId
  );
  const fallbackNode = payload.contexts.find((entry) => entry.type === 'node');
  const anyContext = payload.contexts[0];
  const label =
    matchingContext?.label ??
    fallbackNode?.label ??
    anyContext?.label ??
    payload.topicId ??
    'the workspace';
  const source =
    label && label !== 'the workspace'
      ? `${label} dossier`
      : 'Workspace knowledge base';
  return { label, source };
};

const buildCitations = (
  contexts: ChatbotContextItemPayload[]
) => {
  if (contexts.length === 0) return undefined;
  return contexts.slice(0, 2).map((context, index) => ({
    id: context.id ?? `${context.type}-${index}`,
    label: context.label,
    type: context.type,
    snippet: `Reference snippet about ${context.label}.`,
    confidence: 'medium' as const,
  }));
};

export const mockChatbotQuery = async (
  payload: ChatbotQueryRequest
): Promise<ChatbotQueryResponseApiResponse> => {
  await delay(450);
  const { label, source } = resolvePrimaryTopic(payload);
  const responseText = `Here is how this connects back to ${label}:\n${payload.prompt} — I will outline supporting evidence and next steps as data sources come online.`;
  const timestamp = Date.now();
  return {
    success: true,
    message: 'Mock chatbot response',
    statusCode: 200,
    errorCode: null,
    meta: null,
    data: {
      message: {
        id: `ai-${timestamp}`,
        role: 'ai',
        content: responseText,
        source,
        nodeSnapshot: label,
        sourceSnapshot: source,
        citations: buildCitations(payload.contexts),
        suggestions: [
          {
            id: 'follow-up-1',
            prompt: `What evidence connects ${label} to recent findings?`,
          },
          {
            id: 'follow-up-2',
            prompt: 'Summarize the most relevant leads from the evidence list.',
          },
        ],
      },
      usage: {
        promptTokens: payload.prompt.length,
        completionTokens: responseText.length,
        totalTokens: payload.prompt.length + responseText.length,
      },
    },
  };
};
