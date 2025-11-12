import clsx from 'clsx';
import { Sparkles } from 'lucide-react';
import type { NodeProps } from 'reactflow';

interface NodeMeta {
  id: string;
  name: string;
  type: string;
  level: number;
  hasChildren: boolean;
  isGap: boolean;
  isExpanded?: boolean;
  isSelected?: boolean;
  isHighlighted?: boolean;
  isLoading?: boolean;
  view: 'galaxy' | 'query';
  onToggle?: (nodeId: string) => void;
  onSelect?: (nodeId: string) => void;
  onClearSelection?: () => void;
}

export const NodeCard: React.FC<NodeProps<NodeMeta>> = ({ id, data }) => {
  const handleClick = () => {
    data.onSelect?.(id);
    if (data.view === 'galaxy' && data.hasChildren) {
      data.onToggle?.(id);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLButtonElement> = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      data.onSelect?.(id);
      if (data.view === 'galaxy' && data.hasChildren) {
        data.onToggle?.(id);
      }
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      data.onClearSelection?.();
    }
  };

  return (
    <div
      data-node-id={id}
      className={clsx(
        'rounded-2xl border px-4 py-3 text-left shadow-lg backdrop-blur',
        data.isSelected ? 'border-emerald-400 bg-emerald-500/10' : 'border-white/10 bg-slate-900/80',
        data.isHighlighted && 'ring-2 ring-cyan-400/80',
      )}
    >
      <button
        type="button"
        aria-label={`Knowledge node ${data.name}`}
        aria-pressed={data.isSelected}
        aria-expanded={data.view === 'galaxy' ? !!data.isExpanded : undefined}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className="flex w-full flex-col gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
      >
        <div className="flex items-center justify-between text-xs text-white/60">
          <span className="uppercase tracking-[0.3em]">{data.type}</span>
          {data.isGap && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-200">
              <Sparkles size={12} />
              Gap
            </span>
          )}
        </div>
        <p className="text-sm font-semibold text-white">{data.name}</p>
        {data.view === 'galaxy' && data.hasChildren && (
          <div className="flex items-center justify-between text-xs text-white/50">
            <span>{data.isExpanded ? 'Collapse branch' : 'Expand branch'}</span>
            {data.isLoading ? (
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
            ) : (
              <span aria-hidden="true">{data.isExpanded ? '−' : '+'}</span>
            )}
          </div>
        )}
      </button>
    </div>
  );
};
