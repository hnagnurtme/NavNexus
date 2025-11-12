import React from 'react';
import { ChevronRight, ChevronDown, Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface TreeExpandButtonProps {
  hasChildren: boolean;
  isExpanded: boolean;
  isLoading?: boolean;
  onClick: (e: React.MouseEvent) => void;
}

export const TreeExpandButton: React.FC<TreeExpandButtonProps> = ({
  hasChildren,
  isExpanded,
  isLoading,
  onClick,
}) => {
  if (!hasChildren) {
    return <div className="w-6 h-6" />;
  }

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClick(e);
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "w-6 h-6 flex items-center justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-blue-500"
      )}
      aria-label={isExpanded ? "Collapse node" : "Expand node"}
      aria-expanded={isExpanded}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
      ) : isExpanded ? (
        <ChevronDown className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      ) : (
        <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      )}
    </button>
  );
};
