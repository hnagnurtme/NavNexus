import clsx from 'clsx';
import { Sparkles, Zap } from 'lucide-react';
import type { WorkspaceNode } from '../../utils/treeUtils';

interface GalaxyMapViewProps {
  root: WorkspaceNode;
  selectedNodeId: string | null;
  highlightedNodeIds: string[];
  journeyPathIds: string[];
  onSelectNode: (nodeId: string) => void | Promise<void>;
}

const badgeByType: Record<string, string> = {
  workspace: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40',
  'problem-domain': 'bg-amber-500/10 text-amber-200 border border-amber-500/30',
  algorithm: 'bg-cyan-500/10 text-cyan-200 border border-cyan-500/30',
  concept: 'bg-blue-500/10 text-blue-200 border border-blue-500/30',
  problem: 'bg-rose-500/10 text-rose-200 border border-rose-500/30',
};

const NodeBadge: React.FC<{ type: string }> = ({ type }) => (
  <span
    className={clsx(
      'rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
      badgeByType[type] ?? 'bg-white/10 text-white/70 border border-white/10',
    )}
  >
    {type}
  </span>
);

export const GalaxyMapView: React.FC<GalaxyMapViewProps> = ({
  root,
  selectedNodeId,
  highlightedNodeIds,
  journeyPathIds,
  onSelectNode,
}) => {
  const primaryNodes = root.children ?? [];

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/10 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/60">Workspace Root</p>
            <h2 className="mt-2 text-2xl font-semibold">{root.name}</h2>
          </div>
          <NodeBadge type={root.type} />
        </div>
        <p className="mt-4 text-sm text-white/70">
          Explore the galaxy of research threads. Nodes glow when they belong to your current journey
          or when AI detects a knowledge gap that deserves attention.
        </p>
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-white/70">
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Selected topic
          </span>
          <span className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-amber-300" />
            Gap detected
          </span>
          <span className="flex items-center gap-2">
            <Zap className="h-3.5 w-3.5 text-cyan-300" />
            Journey path
          </span>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {primaryNodes.map((node) => {
          const isSelected = selectedNodeId === node.id;
          const isHighlighted = highlightedNodeIds.includes(node.id);
          const isOnJourney = journeyPathIds.includes(node.id);

          return (
            <button
              key={node.id}
              type="button"
              onClick={() => onSelectNode(node.id)}
              className={clsx(
                'flex flex-col gap-3 rounded-3xl border p-5 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400',
                'bg-white/5 backdrop-blur-xl',
                isSelected ? 'border-emerald-400/80 shadow-lg shadow-emerald-500/30' : 'border-white/10',
                isHighlighted && 'ring-2 ring-cyan-400/60',
                isOnJourney && 'bg-emerald-500/10',
              )}
            >
              <div className="flex items-center justify-between">
                <NodeBadge type={node.type} />
                {node.isGap && (
                  <span className="flex items-center gap-1 rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-200">
                    <Sparkles size={14} />
                    Gap
                  </span>
                )}
              </div>

              <h3 className="text-lg font-semibold text-white">{node.name}</h3>

              <div className="text-xs text-white/60">
                {node.childrenLoaded
                  ? `${node.children?.length ?? 0} related insights ready`
                  : 'Tap to reveal connected ideas'}
              </div>

              <div className="flex flex-wrap gap-2">
                {(node.children ?? []).slice(0, 4).map((child) => (
                  <span
                    key={child.id}
                    className={clsx(
                      'rounded-full px-3 py-1 text-xs',
                      journeyPathIds.includes(child.id)
                        ? 'bg-cyan-500/30 text-cyan-100'
                        : 'bg-white/10 text-white/70',
                    )}
                  >
                    {child.name}
                  </span>
                ))}
                {node.children && node.children.length > 4 && (
                  <span className="rounded-full bg-white/5 px-3 py-1 text-xs text-white/60">
                    +{node.children.length - 4} more
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </section>
    </div>
  );
};
