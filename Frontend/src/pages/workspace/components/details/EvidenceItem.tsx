import React from 'react';
import type { Evidence } from '@/types';
import { Copy, ExternalLink } from 'lucide-react';
import { cn } from '@/utils/cn';

interface EvidenceItemProps {
  evidence: Evidence;
}

export const EvidenceItem: React.FC<EvidenceItemProps> = ({ evidence }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(evidence.text);
  };

  return (
    <div className={cn(
      "border rounded-lg p-4 hover:shadow-md transition-shadow",
      "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700"
    )}>
      <div className="flex items-start justify-between mb-3">
        <p className="italic text-gray-700 dark:text-gray-300 flex-1">
          "{evidence.text}"
        </p>
        <button
          onClick={handleCopy}
          className="ml-2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          title="Copy quote"
        >
          <Copy className="w-4 h-4 text-gray-500" />
        </button>
      </div>
      
      <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
        <div>📍 {evidence.location}</div>
        <div>
          👤 {evidence.sourceAuthor} ({evidence.sourceYear})
        </div>
        <div className="font-medium text-gray-600 dark:text-gray-300">
          📖 {evidence.sourceTitle}
        </div>
        {evidence.sourceUrl && (
          <a
            href={evidence.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline"
          >
            <ExternalLink className="w-3 h-3 mr-1" />
            View source
          </a>
        )}
      </div>
    </div>
  );
};
