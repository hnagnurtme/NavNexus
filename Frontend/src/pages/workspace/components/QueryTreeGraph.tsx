import { useEffect, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Edge,
  MiniMap,
  Node,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { NodeCard } from './NodeCard';
import { GraphToolbar } from './GraphToolbar';

interface QueryTreeGraphInnerProps {
  nodes: Node[];
  edges: Edge[];
  isLoading: boolean;
  error: string | null;
  onSelect: (nodeId: string) => void;
  selectedNodeId: string | null;
  onRetry: () => void;
}

const NODE_TYPES = { workspaceNode: NodeCard };

const GraphContent: React.FC<QueryTreeGraphInnerProps> = ({
  nodes,
  edges,
  isLoading,
  error,
  onSelect,
  selectedNodeId,
  onRetry,
}) => {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (nodes.length > 0) {
      fitView({ padding: 0.15, duration: 500 });
    }
  }, [fitView, nodes.length]);

  const enrichedNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          view: 'query' as const,
          onSelect,
          isSelected: node.id === selectedNodeId,
        },
      })),
    [nodes, onSelect, selectedNodeId],
  );

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 rounded-3xl border border-rose-500/40 bg-rose-500/5 text-white">
        <p>{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full border border-white/20 px-4 py-2 text-sm uppercase tracking-[0.3em]"
        >
          Retry
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center rounded-3xl border border-white/10 bg-slate-950/80 text-white/70">
        Loading query tree…
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 rounded-3xl border border-white/10 bg-slate-950/80 text-white/60">
        <p>No nodes available.</p>
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full border border-white/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-white/70"
        >
          Reload
        </button>
      </div>
    );
  }

  return (
    <div className="relative h-full rounded-3xl border border-white/10 bg-slate-950/90 p-4">
      <ReactFlow
        nodes={enrichedNodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        panOnDrag
        nodesDraggable={false}
        nodesConnectable={false}
        onNodeClick={(_, node) => onSelect(node.id)}
        className="text-white"
      >
        <MiniMap className="!bg-slate-900/80" />
        <Controls className="border border-white/10 bg-slate-900/70 text-white" />
        <Background gap={24} color="#334155" />
        <div className="pointer-events-none absolute right-4 top-4">
          <GraphToolbar />
        </div>
      </ReactFlow>
    </div>
  );
};

export const QueryTreeGraph: React.FC<QueryTreeGraphInnerProps> = (props) => (
  <ReactFlowProvider>
    <GraphContent {...props} />
  </ReactFlowProvider>
);
