import clsx from 'clsx';
import { ChevronRight, GitBranch } from 'lucide-react';
import type { WorkspaceNode } from '../../utils/treeUtils';

interface QueryTreeViewProps {
  root: WorkspaceNode;
  selectedNodeId: string | null;
  highlightedNodeIds: string[];
  journeyPathIds: string[];
  onSelectNode: (nodeId: string) => void | Promise<void>;
}

export const QueryTreeView: React.FC<QueryTreeViewProps> = ({
  root,
  selectedNodeId,
  highlightedNodeIds,
  journeyPathIds,
  onSelectNode,
}) => (
  <div className="rounded-3xl border border-white/10 bg-black/40 p-6">
    <TreeNodeItem
      node={root}
      level={0}
      selectedNodeId={selectedNodeId}
      highlightedNodeIds={highlightedNodeIds}
      journeyPathIds={journeyPathIds}
      onSelectNode={onSelectNode}
    />
  </div>
);

interface TreeNodeItemProps {
  node: WorkspaceNode;
  level: number;
  selectedNodeId: string | null;
  highlightedNodeIds: string[];
  journeyPathIds: string[];
  onSelectNode: (nodeId: string) => void | Promise<void>;
}

const TreeNodeItem: React.FC<TreeNodeItemProps> = ({
  node,
  level,
  selectedNodeId,
  highlightedNodeIds,
  journeyPathIds,
  onSelectNode,
}) => {
  const isSelected = selectedNodeId === node.id;
  const isHighlighted = highlightedNodeIds.includes(node.id);
  const isOnJourney = journeyPathIds.includes(node.id);

  return (
    <div className={clsx('relative', level > 0 && 'pl-8')}>
      {level > 0 && (
        <span className="absolute left-0 top-4 h-full w-px bg-white/10" aria-hidden="true" />
      )}

      <button
        type="button"
        onClick={() => onSelectNode(node.id)}
        className={clsx(
          'mb-3 flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition',
          'bg-white/5 backdrop-blur',
          isSelected ? 'border-emerald-400/80 shadow-lg shadow-emerald-500/30' : 'border-white/10',
          isHighlighted && 'ring-2 ring-cyan-400/70',
          isOnJourney && 'bg-emerald-400/10',
        )}
      >
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">{node.type}</p>
          <h4 className="text-base font-semibold text-white">{node.name}</h4>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/60">
          {node.isGap && (
            <span className="rounded-full bg-amber-500/10 px-3 py-1 text-amber-200">Gap</span>
          )}
          {node.isCrossroads && (
            <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-cyan-200">Crossroad</span>
          )}
          <ChevronRight className="h-4 w-4" />
        </div>
      </button>

      {node.children && node.children.length > 0 && (
        <div className="ml-4 border-l border-white/5 pl-4">
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              selectedNodeId={selectedNodeId}
              highlightedNodeIds={highlightedNodeIds}
              journeyPathIds={journeyPathIds}
              onSelectNode={onSelectNode}
            />
          ))}
        </div>
      )}

      {!node.childrenLoaded && node.hasChildren && (
        <div className="ml-6 flex items-center gap-2 rounded-2xl border border-dashed border-white/10 bg-white/5 px-4 py-3 text-xs text-white/50">
          <GitBranch size={12} />
          Select this node to fetch detailed branches
        </div>
      )}
    </div>
  );
};
