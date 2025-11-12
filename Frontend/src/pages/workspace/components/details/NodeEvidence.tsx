import React from 'react';
import type { Evidence } from '@/types';
import { EvidenceItem } from './EvidenceItem';
import { AlertTriangle } from 'lucide-react';

interface NodeEvidenceProps {
  evidence: Evidence[];
}

export const NodeEvidence: React.FC<NodeEvidenceProps> = ({ evidence }) => {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
        🔍 Evidence ({evidence.length})
      </h3>
      
      {evidence.length === 0 ? (
        <div className="flex items-center gap-2 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-md">
          <AlertTriangle className="w-5 h-5 text-orange-500" />
          <p className="text-sm text-orange-700 dark:text-orange-300">
            No evidence from documents
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {evidence.map((item) => (
            <EvidenceItem key={item.id} evidence={item} />
          ))}
        </div>
      )}
    </div>
  );
};
