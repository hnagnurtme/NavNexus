import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Edge, Node } from "reactflow";
import { treeService } from "@/services/tree.service";
import type { KnowledgeNodeUI } from "@/types";
import { transformToKnowledgeNodeUI } from "@/utils/treeTransform";
import { applyDagreLayout } from "../utils/layout";

interface GraphState {
	nodes: Node[];
	edges: Edge[];
	loading: boolean;
	error: string | null;
	viewportKey: number;
}

interface UseWorkspaceGraphReturn {
	galaxy: GraphState & {
		selectedNodeId: string | null;
	};
	query: GraphState;
	actions: {
		initialize: () => void;
		toggleNode: (nodeId: string) => void;
		selectNode: (nodeId: string | null) => void;
		loadQueryTree: () => void;
		expandNode: (nodeId: string) => Promise<void>;
	};
}

const toFlowNode = (
	treeNode: KnowledgeNodeUI,
	options: Partial<Node["data"]> = {}
): Node => ({
	id: treeNode.nodeId,
	type: "workspaceNode",
	position: { x: 0, y: 0 },
	data: {
		id: treeNode.nodeId,
		name: treeNode.nodeName,
		type: "node", // Default type since we don't have specific types in API
		level: treeNode.level,
		isGap: (treeNode.gapSuggestions?.length ?? 0) > 0,
		hasChildren: treeNode.hasChildren,
		childCount: treeNode.children?.length ?? 0,
		view: "galaxy" as const,
		...options,
	},
});

const DEFAULT_EDGE_STYLE = { strokeWidth: 2, stroke: "#059669" } as const;

const toEdge = (source: string, target: string): Edge => ({
	id: `${source}-${target}`,
	source,
	target,
	type: "smoothstep",
	animated: true,
	style: DEFAULT_EDGE_STYLE,
});

export const useWorkspaceGraph = (
	workspaceId?: string
): UseWorkspaceGraphReturn & { initialized: boolean } => {
	const [galaxyState, setGalaxyState] = useState<GraphState>({
		nodes: [],
		edges: [],
		loading: true,
		error: null,
		viewportKey: 0,
	});
	const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
	const [queryState, setQueryState] = useState<GraphState>({
		nodes: [],
		edges: [],
		loading: false,
		error: null,
		viewportKey: 0,
	});
	const [initialized, setInitialized] = useState(false);

	const nodeRegistry = useRef<Map<string, KnowledgeNodeUI>>(new Map());
	const visibleNodeIds = useRef<Set<string>>(new Set());
	const expandedNodeIds = useRef<Set<string>>(new Set());
	const adjacencyMap = useRef<Map<string, string[]>>(new Map());
	const childrenCache = useRef<Map<string, KnowledgeNodeUI[]>>(new Map());
	const pendingNodeIds = useRef<Set<string>>(new Set());
	const lastAddedIds = useRef<string[] | null>(null);

	const rebuildGalaxy = useCallback(() => {
		const nodes = Array.from(visibleNodeIds.current).map((id) => {
			const treeNode = nodeRegistry.current.get(id);
			if (!treeNode) {
				throw new Error(`Missing node data for ${id}`);
			}
			return toFlowNode(treeNode, {
				isExpanded: expandedNodeIds.current.has(id),
				isLoading: pendingNodeIds.current.has(id),
				isHighlighted: selectedNodeId === id,
			});
		});

		const edges: Edge[] = [];
		adjacencyMap.current.forEach((children, parentId) => {
			if (!visibleNodeIds.current.has(parentId)) return;

			children.forEach((childId) => {
				if (!visibleNodeIds.current.has(childId)) return;
				edges.push(toEdge(parentId, childId));
			});
		});

		const { nodes: layoutNodes, edges: layoutEdges } = applyDagreLayout(
			nodes,
			edges
		);
		setGalaxyState((prev) => ({
			...prev,
			nodes: layoutNodes,
			edges: layoutEdges,
			loading: false,
		}));
	}, [selectedNodeId]);

	useEffect(() => {
		nodeRegistry.current.clear();
		visibleNodeIds.current = new Set();
		expandedNodeIds.current = new Set();
		adjacencyMap.current = new Map();
		childrenCache.current = new Map();
		pendingNodeIds.current = new Set();
		lastAddedIds.current = null;
		setGalaxyState({
			nodes: [],
			edges: [],
			loading: false,
			error: null,
			viewportKey: 0,
		});
		setQueryState({
			nodes: [],
			edges: [],
			loading: false,
			error: null,
			viewportKey: 0,
		});
		setSelectedNodeId(null);
		setInitialized(false);
	}, [workspaceId]);

	const loadRoot = useCallback(async () => {
		if (!workspaceId) {
			setGalaxyState((prev) => ({
				...prev,
				loading: false,
				error: "Missing workspace id",
			}));
			return;
		}
		if (initialized) return;

		setGalaxyState((prev) => ({ ...prev, loading: true, error: null }));
		try {
			// Fetch the root node with all its children from API
			const response = await treeService.getKnowledgeTree(workspaceId);
			if (!response.data) {
				throw new Error("No data in response");
			}

			const rootNode = transformToKnowledgeNodeUI(response.data, {
				isExpanded: true,
				childrenLoaded: true,
			});

			// Recursively register all descendants in the node registry
			const registerDescendants = (node: KnowledgeNodeUI) => {
				nodeRegistry.current.set(node.nodeId, node);
				if (node.children) {
					node.children.forEach((child) => registerDescendants(child));
				}
			};
			
			// Register root and all its descendants
			registerDescendants(rootNode);
			
			// Set up visible nodes (root + immediate children)
			const childIds = rootNode.children?.map(c => c.nodeId) ?? [];
			visibleNodeIds.current = new Set([rootNode.nodeId, ...childIds]);
			
			// Set up adjacency
			adjacencyMap.current.set(rootNode.nodeId, childIds);
			
			// Cache children
			childrenCache.current.set(rootNode.nodeId, rootNode.children ?? []);
			
			expandedNodeIds.current.add(rootNode.nodeId);
			lastAddedIds.current = childIds;
			
			rebuildGalaxy();
			setGalaxyState((prev) => ({
				...prev,
				viewportKey: prev.viewportKey + 1,
			}));
			setInitialized(true);
		} catch (error) {
			console.error("Failed to load root tree:", error);
			setGalaxyState((prev) => ({
				...prev,
				loading: false,
				error: "Unable to load root tree. Please retry.",
			}));
			setInitialized(false);
		}
	}, [initialized, rebuildGalaxy, workspaceId]);

	const ensureChildren = useCallback(
		async (nodeId: string): Promise<KnowledgeNodeUI[]> => {
			if (childrenCache.current.has(nodeId)) {
				return childrenCache.current.get(nodeId)!;
			}
			if (!workspaceId) {
				throw new Error("Missing workspace id");
			}
			pendingNodeIds.current.add(nodeId);
			rebuildGalaxy();
			
			// Fetch node with its children from API
			const response = await treeService.getKnowledgeNodeById(nodeId);
			if (!response.data) {
				throw new Error("No data in response");
			}

			const nodeUI = transformToKnowledgeNodeUI(response.data, {
				isExpanded: true,
				childrenLoaded: true,
			});

			const children = nodeUI.children ?? [];
			childrenCache.current.set(nodeId, children);
			
			// Recursively register all descendants in the node registry
			const registerDescendants = (node: KnowledgeNodeUI) => {
				nodeRegistry.current.set(node.nodeId, node);
				if (node.children) {
					node.children.forEach((child) => registerDescendants(child));
				}
			};
			
			children.forEach((child) => registerDescendants(child));
			
			pendingNodeIds.current.delete(nodeId);
			return children;
		},
		[rebuildGalaxy, workspaceId]
	);

	const collapseDescendants = useCallback((nodeId: string) => {
		const queue = [...(adjacencyMap.current.get(nodeId) ?? [])];
		while (queue.length > 0) {
			const childId = queue.shift()!;
			if (visibleNodeIds.current.has(childId)) {
				visibleNodeIds.current.delete(childId);
			}
			expandedNodeIds.current.delete(childId);
			const grandchildren = adjacencyMap.current.get(childId);
			if (grandchildren && grandchildren.length > 0) {
				queue.push(...grandchildren);
			}
		}
	}, []);

	const toggleNode = useCallback(
		async (nodeId: string) => {
			const treeNode = nodeRegistry.current.get(nodeId);
			if (!treeNode || !treeNode.hasChildren) {
				setSelectedNodeId(nodeId);
				rebuildGalaxy();
				return;
			}

			if (expandedNodeIds.current.has(nodeId)) {
				expandedNodeIds.current.delete(nodeId);
				collapseDescendants(nodeId);
				rebuildGalaxy();
				return;
			}

			expandedNodeIds.current.add(nodeId);
			const children = await ensureChildren(nodeId);
			adjacencyMap.current.set(
				nodeId,
				children.map((child) => child.nodeId)
			);
			children.forEach((child) => {
				visibleNodeIds.current.add(child.nodeId);
			});
			lastAddedIds.current = children.map((child) => child.nodeId);
			rebuildGalaxy();
			setGalaxyState((prev) => ({
				...prev,
				viewportKey: prev.viewportKey + 1,
			}));
		},
		[ensureChildren, rebuildGalaxy, collapseDescendants]
	);

	const expandNode = useCallback(
		async (nodeId: string) => {
			const treeNode = nodeRegistry.current.get(nodeId);
			if (!treeNode || !treeNode.hasChildren) {
				return;
			}
			if (expandedNodeIds.current.has(nodeId)) {
				if (!visibleNodeIds.current.has(nodeId)) {
					visibleNodeIds.current.add(nodeId);
					rebuildGalaxy();
				}
				return;
			}
			expandedNodeIds.current.add(nodeId);
			const children = await ensureChildren(nodeId);
			adjacencyMap.current.set(
				nodeId,
				children.map((child) => child.nodeId)
			);
			children.forEach((child) => {
				visibleNodeIds.current.add(child.nodeId);
			});
			lastAddedIds.current = children.map((child) => child.nodeId);
			rebuildGalaxy();
		},
		[ensureChildren, rebuildGalaxy]
	);

	const selectNode = useCallback((nodeId: string | null) => {
		setSelectedNodeId(nodeId);
		setGalaxyState((prev) => ({
			...prev,
			nodes: prev.nodes.map((node) => ({
				...node,
				data: {
					...node.data,
					isSelected: node.id === nodeId,
				},
			})),
		}));
	}, []);

	const loadQueryTree = useCallback(async () => {
		if (!workspaceId) {
			setQueryState((prev) => ({
				...prev,
				error: "Missing workspace id",
			}));
			return;
		}
		setQueryState((prev) => ({
			...prev,
			nodes: [],
			edges: [],
			loading: true,
			error: null,
		}));
		try {
			// Fetch the full tree from API
			const response = await treeService.getKnowledgeTree(workspaceId);
			if (!response.data) {
				throw new Error("No data in response");
			}

			const rootNode = transformToKnowledgeNodeUI(response.data, {
				isExpanded: true,
				childrenLoaded: true,
			});

			// Flatten the tree for query view
			const nodes: KnowledgeNodeUI[] = [];
			const edges: Edge[] = [];

			const collectNodesAndEdges = (node: KnowledgeNodeUI, parentId?: string) => {
				nodes.push(node);
				if (parentId) {
					edges.push(toEdge(parentId, node.nodeId));
				}
				node.children?.forEach((child) => {
					collectNodesAndEdges(child, node.nodeId);
				});
			};

			collectNodesAndEdges(rootNode);

			const flowNodes = nodes.map((node) =>
				toFlowNode(node, {
					view: "query",
				})
			);
			const { nodes: layoutNodes, edges: layoutEdges } = applyDagreLayout(
				flowNodes,
				edges,
				"LR"
			);
			setQueryState((prev) => ({
				...prev,
				nodes: layoutNodes,
				edges: layoutEdges,
				loading: false,
				error: null,
				viewportKey: prev.viewportKey + 1,
			}));
		} catch (error) {
			console.error("Failed to load query tree:", error);
			setQueryState((prev) => ({
				...prev,
				nodes: [],
				edges: [],
				loading: false,
				error: "Unable to build the query tree right now.",
			}));
		}
	}, [workspaceId]);

	useEffect(() => {
		if (!lastAddedIds.current) return;
		const [firstAdded] = lastAddedIds.current;
		if (!firstAdded) return;
		const timer = window.setTimeout(() => {
			const nodeElement = document.querySelector<HTMLElement>(
				`[data-node-id="${firstAdded}"] button`
			);
			// Keep focus management without shifting the canvas viewport
			nodeElement?.focus({ preventScroll: true });
			lastAddedIds.current = null;
		}, 100);
		return () => window.clearTimeout(timer);
	}, [galaxyState.nodes]);

	// Memoize the actions object to prevent recreation on every render
	const actions = useMemo(
		() => ({
			initialize: loadRoot,
			toggleNode,
			selectNode,
			loadQueryTree,
			expandNode,
		}),
		[loadRoot, toggleNode, selectNode, loadQueryTree, expandNode]
	);

	return {
		galaxy: {
			...galaxyState,
			selectedNodeId,
		},
		query: queryState,
		initialized,
		actions,
	};
};
