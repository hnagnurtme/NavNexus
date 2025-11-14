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
}) => {
	const { fitView } = useReactFlow();

	useEffect(() => {
		if (nodes.length > 0) {
			fitView({ padding: 0.2, duration: 400 });
		}
	}, [fitView, nodes.length]);

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
				fitView
				panOnDrag
				nodesDraggable={true}
				nodesConnectable={true}
				elementsSelectable={true} // Allow selection
				onPaneClick={onClearSelection}
				// Remove onNodeClick since it's handled in CustomNode now
				className="text-white"
			>
				<MiniMap className="!bg-slate-900/80" />
				<Controls className="border border-white/10 bg-slate-900/70 text-white" />
				<Background gap={24} color="#334155" />
				<div className="pointer-events-none absolute right-4 top-4">
					<GraphToolbar />
				</div>
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
