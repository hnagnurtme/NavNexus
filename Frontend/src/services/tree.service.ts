import { apiClient } from './api.service';
import type { 
  TreeRootResponse, 
  NodeChildrenResponse, 
  NodeDetailsResponse 
} from '@/types';
import { mockTreeService } from '@/mocks/mockData';

// Use mock data in development
const USE_MOCK = import.meta.env.DEV;

export const treeService = {
  // API 1: Load root + level 1 children
  async getTreeRoot(workspaceId: string): Promise<TreeRootResponse> {
    if (USE_MOCK) {
      return mockTreeService.getTreeRoot(workspaceId);
    }
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/tree/root`
    );
    return data;
  },

  // API 2: Load children of a node
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

  // API 3: Load node details (synthesis, evidence, suggestions)
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
