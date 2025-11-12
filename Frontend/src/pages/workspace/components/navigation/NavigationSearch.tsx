import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import { useTreeStore } from '@/store/treeStore';
import { useNavigationStore } from '@/store/navigationStore';
import { searchTree } from '@/utils/tree.utils';
import { cn } from '@/utils/cn';

interface NavigationSearchProps {
  workspaceId: string;
}

export const NavigationSearch: React.FC<NavigationSearchProps> = ({ workspaceId }) => {
  const { tree, selectNode } = useTreeStore();
  const { searchQuery, setSearchQuery, searchResults, setSearchResults, clearSearch } = useNavigationStore();
  const [isOpen, setIsOpen] = useState(false);
  const [localQuery, setLocalQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localQuery.trim()) {
        const results = searchTree(tree, localQuery);
        setSearchResults(results);
        setSearchQuery(localQuery);
        setIsOpen(true);
      } else {
        clearSearch();
        setIsOpen(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [localQuery, tree, setSearchQuery, setSearchResults, clearSearch]);

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

  const handleResultClick = async (nodeId: string) => {
    await selectNode(workspaceId, nodeId);
    setIsOpen(false);
    setLocalQuery('');
    clearSearch();
  };

  const handleClear = () => {
    setLocalQuery('');
    clearSearch();
    setIsOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          placeholder="Search nodes..."
          className={cn(
            "pl-10 pr-10 py-2 w-64 border rounded-md",
            "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100",
            "border-gray-300 dark:border-gray-600",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
            "placeholder:text-gray-400 dark:placeholder:text-gray-500"
          )}
        />
        {localQuery && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {isOpen && searchResults.length > 0 && (
        <div className={cn(
          "absolute top-full mt-2 w-full max-h-96 overflow-y-auto",
          "bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600",
          "rounded-md shadow-lg z-50"
        )}>
          {searchResults.map((node) => (
            <button
              key={node.id}
              onClick={() => handleResultClick(node.id)}
              className={cn(
                "w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700",
                "transition-colors border-b border-gray-200 dark:border-gray-700 last:border-b-0"
              )}
            >
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {node.name}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Level {node.level} • {node.type}
                {node.isGap && ' • GAP'}
                {node.isCrossroads && ' • CROSSROADS'}
              </div>
            </button>
          ))}
        </div>
      )}

      {isOpen && searchResults.length === 0 && searchQuery && (
        <div className={cn(
          "absolute top-full mt-2 w-full px-4 py-3",
          "bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600",
          "rounded-md shadow-lg z-50 text-center text-gray-500 dark:text-gray-400"
        )}>
          No results found for "{searchQuery}"
        </div>
      )}
    </div>
  );
};
