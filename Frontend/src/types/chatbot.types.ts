import type { ApiResponse } from './auth.types';

/**
 * Chatbot context categories currently exposed in the mock UI.
 * Mirrors the chips rendered in ChatbotPanel.
 */
export type ChatbotContextType = 'node' | 'file';

export type ChatbotContextItemPayload = {
  id?: string;
  type: ChatbotContextType;
  label: string;
};

export type ChatbotMessageRole = 'user' | 'ai';

/**
 * Minimal history shape shared between the UI and the API payload.
 * Additional metadata (node/source snapshots) lets the UI render the chips.
 */
export type ChatbotMessageHistoryItem = {
  role: ChatbotMessageRole;
  content: string;
  timestamp?: number;
  nodeSnapshot?: string | null;
  sourceSnapshot?: string | null;
  source?: string | null;
};

export type ChatbotQueryRequest = {
  prompt: string;
  workspaceId?: string;
  topicId?: string;
  contexts: ChatbotContextItemPayload[];
  history: ChatbotMessageHistoryItem[];
};

export type ChatbotCitation = {
  id?: string;
  label: string;
  type: ChatbotContextType;
  snippet?: string;
  url?: string;
  confidence?: 'high' | 'medium' | 'low';
};

export type ChatbotFollowUpSuggestion = {
  id: string;
  prompt: string;
};

export type ChatbotAnswerMessage = {
  id: string;
  role: 'ai';
  content: string;
  source?: string | null;
  nodeSnapshot?: string | null;
  sourceSnapshot?: string | null;
  citations?: ChatbotCitation[];
  suggestions?: ChatbotFollowUpSuggestion[];
};

export type ChatbotQueryResponse = {
  message: ChatbotAnswerMessage;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
};

export type ChatbotQueryResponseApiResponse = ApiResponse<ChatbotQueryResponse>;
