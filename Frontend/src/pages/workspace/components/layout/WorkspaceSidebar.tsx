import React from 'react';
import { Loader2 } from 'lucide-react';
import { useTreeStore } from '@/store/treeStore';
import { NodeSynthesis } from '../details/NodeSynthesis';
import { NodeEvidence } from '../details/NodeEvidence';
import { NodeAiSuggestion } from '../details/NodeAiSuggestion';
import { cn } from '@/utils/cn';

interface WorkspaceSidebarProps {
  onClose?: () => void;
}

export const WorkspaceSidebar: React.FC<WorkspaceSidebarProps> = () => {
  const { nodeDetails, loading, selectedNodeId } = useTreeStore();

  if (!selectedNodeId) {
    return null;
  }

  return (
    <aside
      className={cn(
        "w-96 bg-white dark:bg-gray-900",
        "border-l border-gray-200 dark:border-gray-700",
        "overflow-y-auto flex-shrink-0"
      )}
    >
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4 z-10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Node Details
        </h2>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {loading && !nodeDetails ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Loading details...
              </p>
            </div>
          </div>
        ) : nodeDetails ? (
          <>
            {/* Node Title */}
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                {nodeDetails.name}
              </h3>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded">
                  {nodeDetails.type}
                </span>
              </div>
            </div>

            {/* AI Suggestion */}
            <NodeAiSuggestion aiSuggestion={nodeDetails.aiSuggestion} />

            {/* Synthesis */}
            <NodeSynthesis synthesis={nodeDetails.synthesis} />

            {/* Evidence */}
            <NodeEvidence evidence={nodeDetails.evidence} />
          </>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            Select a node to view details
          </div>
        )}
      </div>
    </aside>
  );
};
