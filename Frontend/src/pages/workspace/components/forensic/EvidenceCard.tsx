import { useState } from 'react';
import clsx from 'clsx';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { Evidence } from '@/types';

interface EvidenceCardProps {
  evidence: Evidence;
  selected: boolean;
  disabled: boolean;
  onToggle: () => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  selected,
  disabled,
  onToggle,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const hasAdditionalInfo = 
    (evidence.keyClaims && evidence.keyClaims.length > 0) || 
    (evidence.questionsRaised && evidence.questionsRaised.length > 0);

  return (
    <article
      className={clsx(
        'rounded-2xl border p-4 text-sm transition',
        'bg-white/5',
        selected ? 'border-cyan-400/70 shadow shadow-cyan-500/30' : 'border-white/10',
        disabled && !selected && 'opacity-60',
      )}
    >
      {/* Main evidence text - always visible with smart truncation */}
      <p className={clsx(
        'text-white/80 leading-relaxed',
        !isExpanded && (evidence.text?.length ?? 0) > 150 && 'line-clamp-3'
      )}>
        {evidence.text || 'No evidence text available'}
      </p>

      {/* Expand/Collapse for long text */}
      {(evidence.text?.length ?? 0) > 150 && (
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 flex items-center gap-1 text-xs text-cyan-300 hover:text-cyan-200 transition"
        >
          {isExpanded ? (
            <>
              <ChevronUp width={14} height={14} />
              Show less
            </>
          ) : (
            <>
              <ChevronDown width={14} height={14} />
              Show more
            </>
          )}
        </button>
      )}

      {/* Metadata - always visible */}
      <div className="mt-3 space-y-1.5 text-xs">
        {evidence.sourceName && (
          <div className="flex items-center justify-between">
            <p className="text-emerald-300 font-medium">
              {evidence.sourceName}
            </p>
            {evidence.page && (
              <span className="text-white/50">Page {evidence.page}</span>
            )}
          </div>
        )}
        
        {evidence.hierarchyPath && (
          <p className="font-mono text-white/50 text-xs truncate" title={evidence.hierarchyPath}>
            {evidence.hierarchyPath}
          </p>
        )}
        
        {evidence.sourceLanguage && (
          <p className="text-white/50">
            Language: <span className="text-cyan-300">{evidence.sourceLanguage}</span>
          </p>
        )}
      </div>

      {/* Additional info - expandable */}
      {hasAdditionalInfo && isExpanded && (
        <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
          {evidence.keyClaims && evidence.keyClaims.length > 0 && (
            <div>
              <p className="font-semibold text-white/70 text-xs mb-1">Key Claims:</p>
              <ul className="ml-3 space-y-1 text-xs text-white/60">
                {evidence.keyClaims.map((claim, idx) => (
                  <li key={idx} className="list-disc">{claim}</li>
                ))}
              </ul>
            </div>
          )}
          
          {evidence.questionsRaised && evidence.questionsRaised.length > 0 && (
            <div>
              <p className="font-semibold text-amber-300/80 text-xs mb-1">Questions Raised:</p>
              <ul className="ml-3 space-y-1 text-xs text-amber-200/70">
                {evidence.questionsRaised.map((question, idx) => (
                  <li key={idx} className="list-disc">{question}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Compare button */}
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled && !selected}
        className={clsx(
          'mt-4 w-full rounded-2xl border px-3 py-2 text-xs font-semibold uppercase tracking-wide transition',
          selected
            ? 'border-cyan-400/70 bg-cyan-500/10 text-cyan-300'
            : 'border-white/20 text-white/70 hover:border-white/40 hover:bg-white/5',
          disabled && !selected && 'cursor-not-allowed opacity-60',
        )}
      >
        {selected ? 'Selected for Comparison' : 'Select to Compare'}
      </button>
    </article>
  );
};
