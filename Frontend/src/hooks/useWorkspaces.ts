import { useState, useEffect } from 'react';
import { workspaceService } from '@/services/workspace.service';
import type { WorkspaceDetailResponse, CreateWorkspaceRequest } from '@/types/workspace.types';

export const useWorkspaces = () => {
  const [workspaces, setWorkspaces] = useState<WorkspaceDetailResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkspaces = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await workspaceService.getUserWorkspaces();
      if (response.success && response.data) {
        // The API returns a single workspace, but we'll handle it as an array
        setWorkspaces([response.data]);
      } else {
        setWorkspaces([]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load workspaces';
      setError(errorMessage);
      setWorkspaces([]);
    } finally {
      setIsLoading(false);
    }
  };

  const createWorkspace = async (data: CreateWorkspaceRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await workspaceService.createWorkspace(data);
      if (response.success && response.data) {
        setWorkspaces((prev) => [...prev, response.data]);
        return response.data;
      } else {
        throw new Error(response.message || 'Failed to create workspace');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create workspace';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if user is authenticated
    const token = localStorage.getItem('auth_token');
    if (token) {
      fetchWorkspaces();
    }
  }, []);

  return {
    workspaces,
    isLoading,
    error,
    fetchWorkspaces,
    createWorkspace,
  };
};
