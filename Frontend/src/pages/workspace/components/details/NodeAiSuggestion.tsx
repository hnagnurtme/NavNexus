import React from 'react';
import type { AiSuggestion } from '@/types';
import { AlertTriangle, GitBranch } from 'lucide-react';
import { SuggestedDocuments } from './SuggestedDocuments';
import { cn } from '@/utils/cn';

interface NodeAiSuggestionProps {
  aiSuggestion: AiSuggestion;
}

export const NodeAiSuggestion: React.FC<NodeAiSuggestionProps> = ({ 
  aiSuggestion 
}) => {
  if (!aiSuggestion.isGap && !aiSuggestion.isCrossroads) {
    return null;
  }

  const isGap = aiSuggestion.isGap;
  const isCrossroads = aiSuggestion.isCrossroads;

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "p-4 rounded-lg border-l-4",
          isGap && "bg-orange-50 dark:bg-orange-900/20 border-orange-500",
          isCrossroads && !isGap && "bg-blue-50 dark:bg-blue-900/20 border-blue-500"
        )}
      >
        <div className="flex items-start gap-3">
          {isGap ? (
            <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
          ) : (
            <GitBranch className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          )}
          
          <div className="flex-1">
            <h3 className={cn(
              "font-semibold mb-2",
              isGap && "text-orange-700 dark:text-orange-300",
              isCrossroads && !isGap && "text-blue-700 dark:text-blue-300"
            )}>
              {isGap ? '⚠️ Knowledge Gap Detected' : '🔀 Knowledge Crossroads'}
            </h3>
            
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {aiSuggestion.reason}
            </p>
          </div>
        </div>
      </div>

      {isGap && aiSuggestion.suggestedDocuments && aiSuggestion.suggestedDocuments.length > 0 && (
        <SuggestedDocuments documents={aiSuggestion.suggestedDocuments} />
      )}
    </div>
  );
};
