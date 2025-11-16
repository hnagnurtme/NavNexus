import { apiClient } from './api.service';
import type { 
  TreeRootResponse, 
  NodeChildrenResponse, 
  NodeDetailsResponse,
  GetKnowledgeNodeResponseApiResponse,
  CreatedKnowledgetreeRequest,
  RabbitMqSendingResponseApiResponse
} from '@/types';


export const treeService = {
  /**
   * Get knowledge tree root nodes with their children
   * Endpoint: GET /api/knowledge-tree/{workspaceId}
   */
  async getKnowledgeTree(workspaceId: string): Promise<GetKnowledgeNodeResponseApiResponse> {
    const { data } = await apiClient.get<GetKnowledgeNodeResponseApiResponse>(
      `/knowledge-tree/${workspaceId}`
    );
    return data;
  },

  /**
   * Get knowledge node by ID
   * Endpoint: GET /api/knowledge-tree/node/{nodeId}
   */
  async getKnowledgeNodeById(nodeId: string): Promise<GetKnowledgeNodeResponseApiResponse> {
    const { data } = await apiClient.get<GetKnowledgeNodeResponseApiResponse>(
      `/knowledge-tree/node/${nodeId}`
    );
    return data;
  },
};
