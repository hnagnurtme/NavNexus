import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Edge } from "reactflow";
import { OnboardingPanel } from "./OnboardingPanel";
import { GalaxyGraph } from "../../components/GalaxyGraph";
import { QueryTreeGraph } from "../../components/QueryTreeGraph";
import { useWorkspaceGraph } from "../../hooks/useWorkspaceGraph";

type CanvasView = "onboarding" | "active";
type ViewMode = "galaxy" | "query";

type NodeSelectHandler = (nodeId: string) => void | Promise<void>;

interface WorkspaceCanvasProps {
	workspaceId: string;
	view: CanvasView;
	viewMode: ViewMode;
	isBuilding: boolean;
	isNodeLoading: boolean;
	loadingNodeName?: string | null;
	selectedNodeId: string | null;
	highlightedNodeIds: string[];
	journeyPathIds: string[];
	onSelectNode: NodeSelectHandler;
	onBuildGraph: () => void;
}

const DEFAULT_EDGE_STYLE = { strokeWidth: 2, stroke: "#059669" } as const;
const HIGHLIGHTED_EDGE_STYLE = { strokeWidth: 3, stroke: "#10b981" } as const;

const applyJourneyStyling = (edges: Edge[], journeyPathIds: string[]) => {
	if (edges.length === 0) return edges;
	const indexMap = new Map<string, number>();
	journeyPathIds.forEach((id, index) => indexMap.set(id, index));
	return edges.map((edge) => {
		const sourceIndex = indexMap.get(edge.source);
		const targetIndex = indexMap.get(edge.target);
		const isOnPath =
			sourceIndex !== undefined && targetIndex === sourceIndex + 1;
		return {
			...edge,
			animated: isOnPath ? true : edge.animated ?? true,
			style: isOnPath ? HIGHLIGHTED_EDGE_STYLE : DEFAULT_EDGE_STYLE,
		};
	});
};

export const WorkspaceCanvas: React.FC<WorkspaceCanvasProps> = ({
	workspaceId,
	view,
	viewMode,
	isBuilding,
	isNodeLoading,
	loadingNodeName,
	selectedNodeId,
	highlightedNodeIds,
	journeyPathIds,
	onSelectNode,
	onBuildGraph,
}) => {
	const { galaxy, query, actions, initialized } =
		useWorkspaceGraph(workspaceId);
	const [hasRequestedInit, setHasRequestedInit] = useState(false);

	useEffect(() => {
		if (view === "active" && !initialized && !hasRequestedInit) {
			actions.initialize();
			setHasRequestedInit(true);
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [hasRequestedInit, initialized, view]);

	useEffect(() => {
		if (view !== "active") return;
		actions.selectNode(selectedNodeId ?? null);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [selectedNodeId, view]);

	useEffect(() => {
		if (view !== "active" || viewMode !== "query") return;
		if (query.nodes.length > 0 || query.loading || query.error) return;
		actions.loadQueryTree();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [query.error, query.loading, query.nodes.length, view, viewMode]);

	const galaxyNodes = useMemo(
		() =>
			galaxy.nodes.map((node) => ({
				...node,
				data: {
					...node.data,
					isHighlighted:
						highlightedNodeIds.includes(node.id) ||
						journeyPathIds.includes(node.id),
				},
			})),
		[galaxy.nodes, highlightedNodeIds, journeyPathIds]
	);

	const queryNodes = useMemo(
		() =>
			query.nodes.map((node) => ({
				...node,
				data: {
					...node.data,
					isHighlighted:
						highlightedNodeIds.includes(node.id) ||
						journeyPathIds.includes(node.id),
				},
			})),
		[query.nodes, highlightedNodeIds, journeyPathIds]
	);

	const galaxyEdges = useMemo(
		() => applyJourneyStyling(galaxy.edges, journeyPathIds),
		[galaxy.edges, journeyPathIds]
	);

	const queryEdges = useMemo(
		() => applyJourneyStyling(query.edges, journeyPathIds),
		[query.edges, journeyPathIds]
	);

	const handleNodeSelect = useCallback(
		(nodeId: string) => {
			actions.selectNode(nodeId);
			onSelectNode(nodeId);
		},
		[actions, onSelectNode]
	);

	const handleToggleNode = useCallback(
		(nodeId: string) => {
			actions.toggleNode(nodeId);
		},
		[actions]
	);

	const handleClearSelection = useCallback(() => {
		actions.selectNode(null);
	}, [actions]);

	if (view === "onboarding") {
		return (
			<div className="relative h-full w-full rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-900 to-black p-10 text-white shadow-[0_0_120px_rgba(3,199,90,0.35)]">
				<OnboardingPanel
					onStart={onBuildGraph}
					isBuilding={isBuilding}
				/>
			</div>
		);
	}

	return (
		<div className="relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-black p-6 text-white shadow-[0_0_80px_rgba(0,0,0,0.5)]">
			<div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(16,185,129,0.25),transparent_45%),radial-gradient(circle_at_80%_0%,rgba(59,130,246,0.2),transparent_40%)]" />
			<div className="h-full overflow-hidden">
				{viewMode === "galaxy" ? (
					<GalaxyGraph
						nodes={galaxy.nodes}
						edges={galaxy.edges}
						isLoading={galaxy.loading}
						error={galaxy.error}
						selectedNodeId={galaxy.selectedNodeId}
						onNodeSelect={handleNodeSelect}
						onToggleNode={handleToggleNode}
						onClearSelection={handleClearSelection}
					/>
				) : (
					<QueryTreeGraph
						nodes={queryNodes}
						edges={queryEdges}
						isLoading={query.loading}
						error={query.error}
						onSelect={handleNodeSelect}
						selectedNodeId={galaxy.selectedNodeId}
						onRetry={actions.loadQueryTree}
					/>
				)}
			</div>

			{isNodeLoading && (
				<div className="pointer-events-none absolute left-6 top-6">
					<div
						className="flex items-center gap-3 rounded-full border border-white/10 bg-black/70 px-5 py-2 text-xs font-medium text-white/80 shadow-lg"
						aria-live="polite"
					>
						<Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
						<span>
							{loadingNodeName
								? `Fetching insights for ${loadingNodeName}`
								: "Fetching insights…"}
						</span>
					</div>
				</div>
			)}
		</div>
	);
};
