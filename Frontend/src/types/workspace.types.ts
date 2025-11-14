// Workspace Types based on Swagger API specification
import type { ApiResponse } from './auth.types';

export type CreateWorkspaceRequest = {
  name: string;
  description?: string;
  fileIds?: string[];
};

export type WorkspaceDetailResponse = {
  workspaceId: string;
  name: string;
  description: string;
  ownerId: string;
  ownerName: string;
  fileIds: string[];
  createdAt: string;
  updatedAt: string;
};

export type WorkspaceDetailResponseApiResponse = ApiResponse<WorkspaceDetailResponse>;
