import { useEffect, useMemo } from "react";
import ReactFlow, {
	Background,
	Controls,
	Edge,
	MiniMap,
	Node,
	ReactFlowProvider,
	useReactFlow,
	NodeTypes,
	Panel,
} from "reactflow";
import "reactflow/dist/style.css";
import { GraphToolbar } from "./GraphToolbar";
import CustomNode from "./mindmap/CustomNode";

interface GalaxyGraphInnerProps {
	nodes: Node[];
	edges: Edge[];
	isLoading: boolean;
	error: string | null;
	onNodeSelect: (nodeId: string) => void;
	onToggleNode: (nodeId: string) => void;
	selectedNodeId: string | null;
	onClearSelection: () => void;
	viewportKey: number;
	focusedNodeId?: string | null;
}

const nodeTypes: NodeTypes = {
	workspaceNode: CustomNode,
};

const GraphContent: React.FC<GalaxyGraphInnerProps> = ({
	nodes,
	edges,
	isLoading,
	error,
	onNodeSelect,
	onToggleNode,
	selectedNodeId,
	onClearSelection,
	viewportKey,
	focusedNodeId,
}) => {
	const { fitView, getNodes, setCenter } = useReactFlow();

	// Fit view whenever nodes or edges change
	useEffect(() => {
		if (nodes.length === 0 || focusedNodeId) return; // Ignore if no nodes or focused node is set

		// Use a small timeout to ensure the layout has been applied
		const timer = setTimeout(() => {
			fitView({
				padding: 0.2,
				duration: 400,
				maxZoom: 1.5, // Prevent zooming in too much
				minZoom: 0.5, // Prevent zooming out too much
			});
			console.log("Fitting view to", nodes.length, "nodes");
		}, 50); // Small delay to let React Flow update the DOM

		return () => clearTimeout(timer);
	}, [fitView, nodes.length, edges.length, viewportKey]);

	useEffect(() => {
		if (!focusedNodeId) return;
		const node = getNodes().find((n) => n.id === focusedNodeId);
		if (!node) return;
		const targetX = node.position.x + (node.width ?? 0) / 2;
		const targetY = node.position.y + (node.height ?? 0) / 2;
		setCenter(targetX, targetY, {
			zoom: 1.3, // Increased zoom for better focus
			duration: 800, // Smoother animation
		});
	}, [focusedNodeId, getNodes, setCenter]);

	const enrichedNodes = useMemo(
		() =>
			nodes.map((node) => ({
				...node,
				data: {
					...node.data,
					view: "galaxy" as const,
					onSelect: onNodeSelect,
					onToggle: onToggleNode,
					onClearSelection,
					isSelected: node.id === selectedNodeId,
				},
			})),
		[nodes, onNodeSelect, onToggleNode, onClearSelection, selectedNodeId]
	);

	return (
		<div className="relative h-full rounded-3xl border border-white/10 bg-slate-950/90 p-4">
			<ReactFlow
				nodes={enrichedNodes}
				edges={edges}
				nodeTypes={nodeTypes}
				fitView // Initial fitView on mount
				panOnDrag
				nodesDraggable={false} // Set back to false since you don't want dragging
				nodesConnectable={false} // Set back to false
				elementsSelectable={true}
				onPaneClick={onClearSelection}
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

			{isLoading && (
				<div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-3xl bg-slate-950/80 text-sm text-white/70">
					Expanding nodes…
				</div>
			)}

			{error && (
				<div className="pointer-events-none absolute inset-x-0 bottom-4 mx-auto w-max rounded-full border border-rose-500/50 bg-rose-500/10 px-4 py-1 text-xs text-rose-200">
					{error}
				</div>
			)}
		</div>
	);
};

export const GalaxyGraph: React.FC<GalaxyGraphInnerProps> = (props) => (
	<ReactFlowProvider>
		<GraphContent {...props} />
	</ReactFlowProvider>
);
