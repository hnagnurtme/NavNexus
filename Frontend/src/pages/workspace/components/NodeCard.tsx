import clsx from 'clsx';
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
        className="w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
      >
        <p className="text-sm font-semibold text-white truncate">{data.name}</p>
        {data.view === 'galaxy' && data.hasChildren && (
          <div className="mt-1 flex items-center justify-between text-xs text-white/60">
            <span>{data.isExpanded ? 'Collapse branch' : 'Expand branch'}</span>
            {data.isLoading ? (
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
            ) : (
              <span aria-hidden="true" className="text-lg leading-none">
                {data.isExpanded ? '−' : '+'}
              </span>
            )}
          </div>
        )}
      </button>
    </div>
  );
};
