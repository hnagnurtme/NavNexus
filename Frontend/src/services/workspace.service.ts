import { apiClient } from './api.service';
import type {
  CreateWorkspaceRequest,
  WorkspaceDetailResponseApiResponse,
} from '@/types/workspace.types';

export const workspaceService = {
  /**
   * Get all workspaces for the current user
   */
  async getUserWorkspaces(): Promise<WorkspaceDetailResponseApiResponse> {
    const response = await apiClient.get<WorkspaceDetailResponseApiResponse>('/workspace');
    return response.data;
  },

  /**
   * Create a new workspace
   */
  async createWorkspace(data: CreateWorkspaceRequest): Promise<WorkspaceDetailResponseApiResponse> {
    const response = await apiClient.post<WorkspaceDetailResponseApiResponse>(
      '/workspace',
      data
    );
    return response.data;
  },

  /**
   * Get workspace details by workspace ID
   */
  async getWorkspaceDetails(userId: string, workspaceId: string): Promise<WorkspaceDetailResponseApiResponse> {
    const response = await apiClient.get<WorkspaceDetailResponseApiResponse>(
      `/workspace/${userId}`,
      {
        params: { workspaceId },
      }
    );
    return response.data;
  },
};
