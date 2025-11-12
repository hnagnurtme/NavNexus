import React, { useState, useRef, useEffect } from 'react';
import { List, Star, Clock } from 'lucide-react';
import { useTreeStore } from '@/store/treeStore';
import { useNavigationStore } from '@/store/navigationStore';
import { findNodeById, flattenTree } from '@/utils/tree.utils';
import { cn } from '@/utils/cn';

interface NavigationJumpListProps {
  workspaceId: string;
}

export const NavigationJumpList: React.FC<NavigationJumpListProps> = ({ 
  workspaceId 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { tree, selectNode } = useTreeStore();
  const { bookmarks, history } = useNavigationStore();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleJump = async (nodeId: string) => {
    await selectNode(workspaceId, nodeId);
    setIsOpen(false);
  };

  const bookmarkedNodes = Array.from(bookmarks)
    .map(id => findNodeById(tree, id))
    .filter((node): node is NonNullable<typeof node> => node !== null);

  const recentNodes = history
    .slice(-5)
    .reverse()
    .map(id => findNodeById(tree, id))
    .filter((node): node is NonNullable<typeof node> => node !== null);

  const allNodes = flattenTree(tree);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600",
          "bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
        )}
        title="Jump to node"
      >
        <List className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      </button>

      {isOpen && (
        <div className={cn(
          "absolute right-0 top-full mt-2 w-80 max-h-96 overflow-y-auto",
          "bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600",
          "rounded-md shadow-lg z-50"
        )}>
          {/* Bookmarks Section */}
          {bookmarkedNodes.length > 0 && (
            <div>
              <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center text-sm font-medium text-gray-700 dark:text-gray-300">
                  <Star className="w-4 h-4 mr-2 text-yellow-500" />
                  Bookmarks
                </div>
              </div>
              {bookmarkedNodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => handleJump(node.id)}
                  className={cn(
                    "w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700",
                    "transition-colors border-b border-gray-200 dark:border-gray-700"
                  )}
                >
                  <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {node.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {node.type}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Recent Section */}
          {recentNodes.length > 0 && (
            <div>
              <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center text-sm font-medium text-gray-700 dark:text-gray-300">
                  <Clock className="w-4 h-4 mr-2" />
                  Recent
                </div>
              </div>
              {recentNodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => handleJump(node.id)}
                  className={cn(
                    "w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700",
                    "transition-colors border-b border-gray-200 dark:border-gray-700"
                  )}
                >
                  <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {node.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {node.type}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* All Nodes Section */}
          <div>
            <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                All Nodes ({allNodes.length})
              </div>
            </div>
            {allNodes.slice(0, 20).map((node) => (
              <button
                key={node.id}
                onClick={() => handleJump(node.id)}
                className={cn(
                  "w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700",
                  "transition-colors border-b border-gray-200 dark:border-gray-700 last:border-b-0"
                )}
              >
                <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                  {node.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Level {node.level} • {node.type}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
