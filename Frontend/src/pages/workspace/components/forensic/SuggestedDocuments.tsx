import { GapSuggestion } from '@/types';
import { Lightbulb } from 'lucide-react';

interface SuggestedDocumentsProps {
  suggestions: GapSuggestion[];
}

export const SuggestedDocuments: React.FC<SuggestedDocumentsProps> = ({ suggestions }) => (
  <section className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
    <div className="mb-3 flex items-center gap-2 text-white">
      <Lightbulb width={16} height={16} />
      <h4 className="text-xs font-semibold uppercase tracking-widest">Knowledge Gap Suggestions</h4>
    </div>
    <ul className="space-y-3">
      {suggestions.map((suggestion, idx) => (
        <li key={suggestion.id || idx} className="rounded-2xl border border-white/10 bg-black/30 p-3">
          <p className="text-base font-semibold text-white">{suggestion.suggestionText || 'Suggestion'}</p>
          {suggestion.similarityScore !== undefined && (
            <p className="mt-1 text-xs text-white/60">
              Similarity: {(suggestion.similarityScore * 100).toFixed(0)}%
            </p>
          )}
          {suggestion.targetNodeId && (
            <p className="mt-1 text-xs text-emerald-300">
              Related to node: {suggestion.targetNodeId}
            </p>
          )}
        </li>
      ))}
    </ul>
  </section>
);
