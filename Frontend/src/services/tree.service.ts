import { apiClient } from './api.service';
import type { 
  GetKnowledgeNodeResponseApiResponse,
  CreatedKnowledgetreeRequest,
  RabbitMqSendingResponseApiResponse
} from '@/types';

/**
 * Tree service for knowledge tree operations
 * All endpoints follow the API_REFERENCE.md specification
 */
export const treeService = {
  /**
   * Get knowledge tree root node with all its children (recursive)
   * Endpoint: GET /api/knowledge-tree/{workspaceId}
   * 
   * @param workspaceId - The workspace ID
   * @returns Root node with nested childNodes array
   */
  async getKnowledgeTree(workspaceId: string): Promise<GetKnowledgeNodeResponseApiResponse> {
    const { data } = await apiClient.get<GetKnowledgeNodeResponseApiResponse>(
      `/knowledge-tree/${workspaceId}`
    );
    // Temporary debugging to observe node payloads returned by the API
    console.log('[treeService] getKnowledgeTree response:', data);
    return data;
  },

  /**
   * Get specific knowledge node by ID with all its children (recursive)
   * Endpoint: GET /api/knowledge-tree/node/{nodeId}
   * 
   * @param nodeId - The node ID to fetch
   * @returns Node with nested childNodes array
   */
  async getKnowledgeNodeById(nodeId: string): Promise<GetKnowledgeNodeResponseApiResponse> {
    const { data } = await apiClient.get<GetKnowledgeNodeResponseApiResponse>(
      `/knowledge-tree/node/${nodeId}`
    );
    // Temporary debugging to observe node payloads returned by the API
    console.log('[treeService] getKnowledgeNodeById response:', data);
    return data;
  },

  /**
   * Create knowledge tree for a workspace (async via RabbitMQ)
   * Endpoint: POST /api/knowledge-tree
   * 
   * @param request - Workspace ID and file paths
   * @returns Message ID and timestamp for tracking
   */
  async createKnowledgeTree(
    request: CreatedKnowledgetreeRequest
  ): Promise<RabbitMqSendingResponseApiResponse> {
    const { data } = await apiClient.post<RabbitMqSendingResponseApiResponse>(
      '/knowledge-tree',
      request
    );
    return data;
  },
};
