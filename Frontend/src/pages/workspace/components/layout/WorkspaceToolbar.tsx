import React from 'react';
import { Upload, Download, Filter } from 'lucide-react';
import { cn } from '@/utils/cn';

export const WorkspaceToolbar: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
      <div className="flex items-center gap-3">
        <button
          className={cn(
            "px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md",
            "transition-colors font-medium text-sm",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          )}
        >
          <Upload className="w-4 h-4 inline-block mr-2" />
          Upload Document
        </button>

        <button
          className={cn(
            "px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md",
            "hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm",
            "text-gray-700 dark:text-gray-300"
          )}
        >
          <Download className="w-4 h-4 inline-block mr-2" />
          Export
        </button>

        <div className="flex-1" />

        <button
          className={cn(
            "px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md",
            "hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm",
            "text-gray-700 dark:text-gray-300"
          )}
        >
          <Filter className="w-4 h-4 inline-block mr-2" />
          Filters
        </button>
      </div>
    </div>
  );
};
