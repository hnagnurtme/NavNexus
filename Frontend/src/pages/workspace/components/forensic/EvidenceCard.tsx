import clsx from 'clsx';
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
}) => (
  <article
    className={clsx(
      'rounded-2xl border p-4 text-sm transition',
      'bg-white/5',
      selected ? 'border-cyan-400/70 shadow shadow-cyan-500/30' : 'border-white/10',
      disabled && !selected && 'opacity-60',
    )}
  >
    <p className="line-clamp-3 text-white/80">{evidence.text}</p>
    <div className="mt-3 space-y-1.5 text-xs text-white/50">
      {evidence.hierarchyPath && (
        <p className="font-mono text-white/60">{evidence.hierarchyPath}</p>
      )}
      {evidence.sourceName && (
        <p className="inline-flex items-center gap-2 text-emerald-300">
          {evidence.sourceName}
          {evidence.page && ` (Page ${evidence.page})`}
        </p>
      )}
      {evidence.sourceLanguage && (
        <p className="text-white/60">
          Language: <span className="text-cyan-300">{evidence.sourceLanguage}</span>
        </p>
      )}
      {evidence.keyClaims && evidence.keyClaims.length > 0 && (
        <div className="mt-2">
          <p className="font-semibold text-white/70">Key Claims:</p>
          <ul className="ml-3 mt-1 list-disc space-y-0.5 text-white/60">
            {evidence.keyClaims.slice(0, 3).map((claim, idx) => (
              <li key={idx} className="line-clamp-2">{claim}</li>
            ))}
          </ul>
        </div>
      )}
      {evidence.questionsRaised && evidence.questionsRaised.length > 0 && (
        <div className="mt-2">
          <p className="font-semibold text-amber-300/80">Questions Raised:</p>
          <ul className="ml-3 mt-1 list-disc space-y-0.5 text-amber-200/70">
            {evidence.questionsRaised.slice(0, 2).map((question, idx) => (
              <li key={idx} className="line-clamp-2">{question}</li>
            ))}
          </ul>
        </div>
      )}
    </div>

    <button
      type="button"
      onClick={onToggle}
      disabled={disabled && !selected}
      className={clsx(
        'mt-4 w-full rounded-2xl border px-3 py-2 text-xs font-semibold uppercase tracking-wide',
        selected
          ? 'border-cyan-400/70 text-cyan-300'
          : 'border-white/20 text-white/70 hover:border-white/40',
        disabled && !selected && 'cursor-not-allowed opacity-60',
      )}
    >
      {selected ? 'Selected' : 'Compare'}
    </button>
  </article>
);
