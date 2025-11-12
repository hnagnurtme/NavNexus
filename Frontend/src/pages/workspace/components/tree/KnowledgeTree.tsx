import React from 'react';
import { TreeNode } from './TreeNode';
import { useTreeStore } from '@/store/treeStore';
import { Loader2, FileQuestion } from 'lucide-react';

interface KnowledgeTreeProps {
  workspaceId: string;
}

export const KnowledgeTree: React.FC<KnowledgeTreeProps> = ({ workspaceId }) => {
  const { tree, loading, error } = useTreeStore();

  if (loading && !tree) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading knowledge tree...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-500 mb-2">⚠️ Error</div>
          <p className="text-gray-600 dark:text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <FileQuestion className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            No Documents Yet
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Upload documents to start building your knowledge tree
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-4">
      <TreeNode node={tree} workspaceId={workspaceId} level={0} />
    </div>
  );
};
