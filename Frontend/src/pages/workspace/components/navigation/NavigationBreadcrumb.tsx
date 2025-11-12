import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { useTreeStore } from '@/store/treeStore';
import { getNodePath } from '@/utils/tree.utils';
import { cn } from '@/utils/cn';

interface NavigationBreadcrumbProps {
  workspaceId: string;
}

export const NavigationBreadcrumb: React.FC<NavigationBreadcrumbProps> = ({ 
  workspaceId 
}) => {
  const { tree, selectedNodeId, selectNode } = useTreeStore();
  
  if (!tree || !selectedNodeId) {
    return null;
  }

  const path = getNodePath(tree, selectedNodeId);

  const handleClick = async (nodeId: string) => {
    if (nodeId !== selectedNodeId) {
      await selectNode(workspaceId, nodeId);
    }
  };

  return (
    <nav className="flex items-center space-x-2 text-sm" aria-label="Breadcrumb">
      <button
        onClick={() => handleClick(tree.id)}
        className={cn(
          "flex items-center px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors",
          selectedNodeId === tree.id && "text-blue-600 dark:text-blue-400 font-medium"
        )}
        title="Root"
      >
        <Home className="w-4 h-4" />
      </button>
      
      {path.slice(1).map((node, index) => {
        const isLast = index === path.length - 2;
        const isClickable = !isLast;
        
        return (
          <React.Fragment key={node.id}>
            <ChevronRight className="w-4 h-4 text-gray-400" />
            <button
              onClick={() => isClickable && handleClick(node.id)}
              disabled={!isClickable}
              className={cn(
                "px-2 py-1 rounded transition-colors max-w-[200px] truncate",
                isClickable && "hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer",
                isLast && "text-blue-600 dark:text-blue-400 font-medium cursor-default",
                !isLast && "text-gray-700 dark:text-gray-300"
              )}
              title={node.name}
            >
              {node.name}
            </button>
          </React.Fragment>
        );
      })}
    </nav>
  );
};
