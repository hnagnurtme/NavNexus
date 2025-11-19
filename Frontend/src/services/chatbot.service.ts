import { apiClient } from './api.service';
import type {
  ChatbotQueryRequest,
  ChatbotQueryResponseApiResponse,
} from '@/types';
import { mockChatbotQuery } from './mocks/chatbot.mock';

const CHATBOT_ENDPOINT = '/chatbot/query';
// Always use mock unless explicitly set to 'false'
const shouldUseMock =
  import.meta.env.VITE_USE_CHATBOT_MOCK !== 'false'; 

export const chatbotService = {
  async query(
    payload: ChatbotQueryRequest
  ): Promise<ChatbotQueryResponseApiResponse> {
    if (shouldUseMock) {
      return mockChatbotQuery(payload);
    }
    const response = await apiClient.post<ChatbotQueryResponseApiResponse>(
      CHATBOT_ENDPOINT,
      payload
    );
    return response.data;
  },
};
