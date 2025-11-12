import React from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { useNavigationStore } from '@/store/navigationStore';
import { useTreeStore } from '@/store/treeStore';
import { cn } from '@/utils/cn';

interface NavigationHistoryProps {
  workspaceId: string;
}

export const NavigationHistory: React.FC<NavigationHistoryProps> = ({ workspaceId }) => {
  const { goBack, goForward, canGoBack, canGoForward } = useNavigationStore();
  const { selectNode } = useTreeStore();

  const handleBack = async () => {
    const nodeId = goBack();
    if (nodeId) {
      await selectNode(workspaceId, nodeId);
    }
  };

  const handleForward = async () => {
    const nodeId = goForward();
    if (nodeId) {
      await selectNode(workspaceId, nodeId);
    }
  };

  return (
    <div className="inline-flex rounded-md shadow-sm" role="group">
      <button
        onClick={handleBack}
        disabled={!canGoBack()}
        className={cn(
          "px-3 py-2 text-sm font-medium rounded-l-md border",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500",
          canGoBack()
            ? "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border-gray-300 dark:border-gray-600"
            : "bg-gray-100 dark:bg-gray-900 text-gray-400 dark:text-gray-600 border-gray-200 dark:border-gray-700 cursor-not-allowed"
        )}
        aria-label="Go back"
        title="Go back (Alt + ←)"
      >
        <ArrowLeft className="w-4 h-4" />
      </button>
      <button
        onClick={handleForward}
        disabled={!canGoForward()}
        className={cn(
          "px-3 py-2 text-sm font-medium rounded-r-md border-t border-r border-b border-l-0",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500",
          canGoForward()
            ? "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border-gray-300 dark:border-gray-600"
            : "bg-gray-100 dark:bg-gray-900 text-gray-400 dark:text-gray-600 border-gray-200 dark:border-gray-700 cursor-not-allowed"
        )}
        aria-label="Go forward"
        title="Go forward (Alt + →)"
      >
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};
