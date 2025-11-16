import { useEffect, useMemo } from "react";
import ReactFlow, {
	Background,
	Controls,
	Edge,
	MiniMap,
	Node,
	ReactFlowProvider,
	useReactFlow,
	Panel,
} from "reactflow";
import "reactflow/dist/style.css";
import { GraphToolbar } from "./GraphToolbar";
import CustomNode from "./mindmap/CustomNode";

interface QueryTreeGraphInnerProps {
	nodes: Node[];
	edges: Edge[];
	isLoading: boolean;
	error: string | null;
	onSelect: (nodeId: string) => void;
	selectedNodeId: string | null;
	onRetry: () => void;
	viewportKey: number;
	focusedNodeId?: string | null;
}

const NODE_TYPES = { workspaceNode: CustomNode };

const GraphContent: React.FC<QueryTreeGraphInnerProps> = ({
	nodes,
	edges,
	isLoading,
	error,
	onSelect,
	selectedNodeId,
	onRetry,
	viewportKey,
	focusedNodeId,
}) => {
	const { fitView, getNodes, setCenter } = useReactFlow();

	// Fit view when nodes are loaded
	useEffect(() => {
		if (nodes.length === 0 && focusedNodeId) return; // Ignore if no nodes or focused node is set

		// Use a small timeout to ensure the layout has been applied
		const timer = setTimeout(() => {
			fitView({
				padding: 0.1, // Increased padding to show more space around nodes
				duration: 500,
				maxZoom: 1, // Limit max zoom to prevent zooming in too much
				minZoom: 0.1, // Allow zooming out very far
			});
			console.log("Fitting query tree view to", nodes.length, "nodes");
		}, 50);

		return () => clearTimeout(timer);
	}, [fitView, nodes.length, viewportKey]);

	useEffect(() => {
		if (!focusedNodeId) return;
		const node = getNodes().find((n) => n.id === focusedNodeId);
		if (!node) return;
		const targetX = node.position.x + (node.width ?? 0) / 2;
		const targetY = node.position.y + (node.height ?? 0) / 2;
		setCenter(targetX, targetY, {
			zoom: 1.1,
			duration: 500,
		});
	}, [focusedNodeId, getNodes, setCenter]);

	const enrichedNodes = useMemo(
		() =>
			nodes.map((node) => ({
				...node,
				data: {
					...node.data,
					view: "query" as const,
					onSelect,
					isSelected: node.id === selectedNodeId,
				},
			})),
		[nodes, onSelect, selectedNodeId]
	);

	if (error) {
		return (
			<div className="flex h-full flex-col items-center justify-center gap-4 rounded-3xl border border-rose-500/40 bg-rose-500/5 text-white">
				<p>{error}</p>
				<button
					type="button"
					onClick={onRetry}
					className="rounded-full border border-white/20 px-4 py-2 text-sm uppercase tracking-[0.3em] hover:bg-white/10 transition-colors"
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
					className="rounded-full border border-white/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-white/70 hover:bg-white/10 transition-colors"
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
				fitView // Initial fitView on mount
				panOnDrag
				nodesDraggable={false}
				nodesConnectable={false}
				onNodeClick={(_, node) => onSelect(node.id)}
				className="text-white"
				minZoom={0.1}
				maxZoom={2}
			>
				<MiniMap className="!bg-slate-900/80" />
				<Controls className="border border-white/10 bg-slate-900/70 text-white" />
				<Background gap={24} color="#334155" />
				<Panel
					position="top-right"
					className="bg-transparent border-none p-0"
				>
					<GraphToolbar />
				</Panel>
			</ReactFlow>
		</div>
	);
};

export const QueryTreeGraph: React.FC<QueryTreeGraphInnerProps> = (props) => (
	<ReactFlowProvider>
		<GraphContent {...props} />
	</ReactFlowProvider>
);
