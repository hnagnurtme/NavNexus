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
    <div className="mt-3 text-xs text-white/50">
      <p className="font-mono text-white/60">{evidence.location}</p>
      <a
        href={evidence.sourceUrl}
        target="_blank"
        rel="noreferrer"
        className="mt-1 inline-flex items-center gap-2 text-emerald-300 hover:text-emerald-200"
      >
        {evidence.sourceTitle}
      </a>
      <p>
        {evidence.sourceAuthor} • {evidence.sourceYear}
      </p>
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
