import { apiClient } from './api.service';
import type { 
  TreeRootResponse, 
  NodeChildrenResponse, 
  NodeDetailsResponse,
  GetKnowledgeNodeResponseApiResponse,
  CreatedKnowledgetreeRequest,
  RabbitMqSendingResponseApiResponse
} from '@/types';
import { mockTreeService } from '@/mocks/mockData';

// Use mock data in development
const USE_MOCK = import.meta.env.DEV;

export const treeService = {
  /**
   * Get knowledge tree root node with children
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

  /**
   * Create knowledge tree for a workspace
   * Endpoint: POST /api/knowledge-tree
   */
  async createKnowledgeTree(request: CreatedKnowledgetreeRequest): Promise<RabbitMqSendingResponseApiResponse> {
    const { data } = await apiClient.post<RabbitMqSendingResponseApiResponse>(
      '/knowledge-tree',
      request
    );
    return data;
  },

  // Legacy methods - kept for backward compatibility with mock data
  // TODO: Remove once all components migrate to new swagger endpoints
  async getTreeRoot(workspaceId: string): Promise<TreeRootResponse> {
    if (USE_MOCK) {
      return mockTreeService.getTreeRoot(workspaceId);
    }
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/tree/root`
    );
    return data;
  },

  async getNodeChildren(
    workspaceId: string, 
    nodeId: string
  ): Promise<NodeChildrenResponse> {
    if (USE_MOCK) {
      return mockTreeService.getNodeChildren(workspaceId, nodeId);
    }
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/tree/nodes/${nodeId}/children`
    );
    return data;
  },

  async getNodeDetails(
    workspaceId: string, 
    nodeId: string
  ): Promise<NodeDetailsResponse> {
    if (USE_MOCK) {
      return mockTreeService.getNodeDetails(workspaceId, nodeId);
    }
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/tree/nodes/${nodeId}/details`
    );
    return data;
  },
};
