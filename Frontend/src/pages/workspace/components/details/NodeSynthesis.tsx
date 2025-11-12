import React from 'react';
import { Copy } from 'lucide-react';

interface NodeSynthesisProps {
  synthesis: string;
}

export const NodeSynthesis: React.FC<NodeSynthesisProps> = ({ synthesis }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(synthesis);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          📝 AI Synthesis
        </h3>
        <button
          onClick={handleCopy}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
          title="Copy synthesis"
        >
          <Copy className="w-4 h-4 text-gray-500" />
        </button>
      </div>
      
      <div className="prose dark:prose-invert max-w-none">
        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
          {synthesis}
        </p>
      </div>
    </div>
  );
};
