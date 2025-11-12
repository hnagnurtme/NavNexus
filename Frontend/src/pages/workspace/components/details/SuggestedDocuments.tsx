import React from 'react';
import type { SuggestedDocument } from '@/types';
import { FileUp, ExternalLink } from 'lucide-react';
import { cn } from '@/utils/cn';

interface SuggestedDocumentsProps {
  documents: SuggestedDocument[];
}

export const SuggestedDocuments: React.FC<SuggestedDocumentsProps> = ({ 
  documents 
}) => {
  return (
    <div className="space-y-3">
      <h4 className="font-medium text-gray-900 dark:text-gray-100">
        Suggested Documents
      </h4>
      
      <div className="grid gap-3">
        {documents.map((doc, index) => (
          <div
            key={index}
            className={cn(
              "p-3 border rounded-md",
              "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700"
            )}
          >
            <div className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
              {doc.title}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {doc.reason}
            </p>
            
            <div className="flex gap-2">
              {doc.previewUrl && (
                <a
                  href={doc.previewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "inline-flex items-center gap-1 px-3 py-1.5 text-sm",
                    "border border-gray-300 dark:border-gray-600 rounded",
                    "hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  )}
                >
                  <ExternalLink className="w-3 h-3" />
                  Preview
                </a>
              )}
              <a
                href={doc.uploadUrl}
                className={cn(
                  "inline-flex items-center gap-1 px-3 py-1.5 text-sm",
                  "bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                )}
              >
                <FileUp className="w-3 h-3" />
                Upload
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
