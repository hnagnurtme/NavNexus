import React from 'react';
import type { TreeNodeUI } from '@/types';
import { TreeNodeIcon } from './TreeNodeIcon';
import { TreeExpandButton } from './TreeExpandButton';
import { cn } from '@/utils/cn';
import { useTreeStore } from '@/store/treeStore';
import { useNavigationStore } from '@/store/navigationStore';

interface TreeNodeProps {
  node: TreeNodeUI;
  workspaceId: string;
  level?: number;
}

export const TreeNode: React.FC<TreeNodeProps> = ({ 
  node, 
  workspaceId,
  level = 0 
}) => {
  const { expandNode, collapseNode, selectNode, selectedNodeId, loading } = useTreeStore();
  const { visitNode, bookmarks } = useNavigationStore();
  
  const isSelected = selectedNodeId === node.id;
  const isBookmarked = bookmarks.has(node.id);
  
  const handleExpand = async () => {
    if (node.isExpanded) {
      collapseNode(node.id);
    } else {
      await expandNode(workspaceId, node.id);
      visitNode(node.id);
    }
  };
  
  const handleClick = async () => {
    if (!isSelected) {
      await selectNode(workspaceId, node.id);
      visitNode(node.id);
    }
  };

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center py-2 px-3 rounded-md cursor-pointer transition-colors",
          "hover:bg-gray-100 dark:hover:bg-gray-800",
          isSelected && "bg-blue-50 dark:bg-blue-900/30 border-l-4 border-blue-500",
          !isSelected && "border-l-4 border-transparent"
        )}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-selected={isSelected}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        <TreeExpandButton
          hasChildren={node.hasChildren}
          isExpanded={node.isExpanded}
          isLoading={loading && isSelected}
          onClick={handleExpand}
        />
        
        <TreeNodeIcon
          type={node.type}
          isGap={node.isGap}
          isCrossroads={node.isCrossroads}
          className="ml-2"
        />
        
        <span className={cn(
          "ml-2 text-sm flex-1",
          isSelected && "font-medium text-blue-700 dark:text-blue-300",
          !isSelected && "text-gray-700 dark:text-gray-300"
        )}>
          {node.name}
        </span>
        
        {isBookmarked && (
          <span className="text-yellow-500 ml-2" title="Bookmarked">★</span>
        )}
        
        {node.isGap && (
          <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded">
            GAP
          </span>
        )}
        
        {node.isCrossroads && (
          <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
            CROSSROADS
          </span>
        )}
      </div>
      
      {node.isExpanded && node.children && node.children.length > 0 && (
        <div className="ml-4">
          {node.children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              workspaceId={workspaceId}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};
