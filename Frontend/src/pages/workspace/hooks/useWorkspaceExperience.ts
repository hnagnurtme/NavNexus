import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { treeService } from "@/services/tree.service";
import type { KnowledgeNodeUI } from "@/types";
import { transformToKnowledgeNodeUI } from "@/utils/treeTransform";
import {
	WorkspaceNode,
	findWorkspaceNode,
	updateWorkspaceNode,
} from "../utils/treeUtils";

type CanvasView = "onboarding" | "active";
type ViewMode = "galaxy" | "query";

const initialJourneyState = {
	isActive: false,
	pathIds: [] as string[],
	currentNodeId: null as string | null,
	awaitingBranch: false,
	branchOptions: [] as WorkspaceNode[],
	completed: false,
	pendingBranchNodeId: null as string | null,
};

export type JourneyState = typeof initialJourneyState;

export const useWorkspaceExperience = (workspaceId?: string) => {
	const [view, setView] = useState<CanvasView>("onboarding");
	const [viewMode, setViewMode] = useState<ViewMode>("galaxy");
	const [tree, setTree] = useState<WorkspaceNode | null>(null);
	const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
	const [details, setDetails] = useState<KnowledgeNodeUI | null>(null);
	const [isBuilding, setIsBuilding] = useState(false);
	const [isNodeLoading, setIsNodeLoading] = useState(false);
	const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [isControlPanelVisible, setIsControlPanelVisible] = useState(false); // Auto-hide sidebar
	const [highlightedNodeIds, setHighlightedNodeIds] = useState<string[]>([]);
	const [journey, setJourney] = useState<JourneyState>(initialJourneyState);
	const highlightTimer = useRef<number | null>(null);
	const journeyRef = useRef<JourneyState>(journey);
	const hasAutoLoaded = useRef(false);

	useEffect(() => {
		journeyRef.current = journey;
	}, [journey]);

	useEffect(() => {
		return () => {
			if (highlightTimer.current) {
				window.clearTimeout(highlightTimer.current);
			}
		};
	}, []);

	// Auto-load MindMap when workspace is available
	useEffect(() => {
		if (workspaceId && !hasAutoLoaded.current && !tree && !isBuilding) {
			hasAutoLoaded.current = true;
			buildGraph();
		}
	}, [workspaceId]); // eslint-disable-line react-hooks/exhaustive-deps

	const focusNode = useCallback(
		async (nodeId: string) => {
			if (!workspaceId) return;

			// Skip API call for virtual root - use tree data instead
			if (nodeId === 'virtual-root') {
				const virtualNode = tree;
				if (virtualNode) {
					setDetails(virtualNode);
					setSelectedNodeId(nodeId);
					setError(null);
				}
				return;
			}

			setIsNodeLoading(true);
			setLoadingNodeId(nodeId);
			try {
				// Fetch node details using the API
				const response = await treeService.getKnowledgeNodeById(nodeId);
				if (response.data) {
					const nodeUI = transformToKnowledgeNodeUI(response.data, {
						isExpanded: true,
					});
					setDetails(nodeUI);
					setSelectedNodeId(nodeId);
					setError(null);
				}
			} catch (err) {
				console.error(err);
				setError("Unable to load insights for this topic.");
			} finally {
				setIsNodeLoading(false);
				setLoadingNodeId(null);
			}
		},
		[workspaceId, tree]
	);

	const highlightNodes = useCallback((nodeIds: string[], duration = 3200) => {
		setHighlightedNodeIds(nodeIds);
		if (highlightTimer.current) {
			window.clearTimeout(highlightTimer.current);
		}
		highlightTimer.current = window.setTimeout(() => {
			setHighlightedNodeIds([]);
		}, duration);
	}, []);

	const ensureChildrenLoaded = useCallback(
		async (nodeId: string): Promise<WorkspaceNode | null> => {
			if (!workspaceId) return null;
			const currentNode = findWorkspaceNode(tree, nodeId);
			if (!currentNode) return null;
			if (
				currentNode.childrenLoaded &&
				(currentNode.children?.length ?? 0) > 0
			) {
				return currentNode;
			}

			try {
				// Fetch node with children from API
				const response = await treeService.getKnowledgeNodeById(nodeId);
				if (response.data) {
					const updatedNodeUI = transformToKnowledgeNodeUI(
						response.data,
						{
							isExpanded: true,
							childrenLoaded: true,
						}
					);

					setTree((prev) => {
						if (!prev) return prev;
						return updateWorkspaceNode(
							prev,
							nodeId,
							() => updatedNodeUI
						);
					});
					return updatedNodeUI;
				}
				return null;
			} catch (err) {
				console.error(err);
				setError("Unable to load related nodes.");
				return null;
			}
		},
		[tree, workspaceId]
	);

	const handleNodeSelect = useCallback(
		async (nodeId: string) => {
			await ensureChildrenLoaded(nodeId);
			await focusNode(nodeId);
		},
		[ensureChildrenLoaded, focusNode]
	);

	const buildGraph = useCallback(async () => {
		if (!workspaceId) {
			setError("Missing workspace context.");
			return;
		}
		setIsBuilding(true);
		setError(null);

		try {
			// Fetch the root nodes with all children from API
			const response = await treeService.getKnowledgeTree(workspaceId);
			if (response.data?.rootNode && response.data.rootNode.length > 0) {
				const rootNodes = response.data.rootNode;

				// If multiple root nodes, create a virtual root to contain them
				let displayRoot: KnowledgeNodeUI;

				if (rootNodes.length === 1) {
					// Single root: use it directly
					displayRoot = transformToKnowledgeNodeUI(rootNodes[0], {
						isExpanded: true,
						childrenLoaded: true,
					});
				} else {
					// Multiple roots: create virtual root
					const transformedRoots = rootNodes.map(node =>
						transformToKnowledgeNodeUI(node, {
							isExpanded: false,
							childrenLoaded: true,
						})
					);

					displayRoot = {
						nodeId: 'virtual-root',
						nodeName: 'Knowledge Domains',
						description: `Workspace contains ${rootNodes.length} knowledge domains`,
						tags: ['workspace'],
						level: -1,
						sourceCount: rootNodes.reduce((sum, n) => sum + n.sourceCount, 0),
						evidences: [],
						gapSuggestions: [],
						createdAt: new Date().toISOString(),
						updatedAt: new Date().toISOString(),
						hasChildren: true,
						children: transformedRoots,
						isExpanded: true,
						childrenLoaded: true,
					};
				}

				setTree(displayRoot);
				setView("active");
				await focusNode(displayRoot.nodeId);
			}
		} catch (err) {
			console.error(err);
			setError("Unable to synthesize this workspace right now.");
		} finally {
			setIsBuilding(false);
		}
	}, [workspaceId, focusNode]);

	const resetWorkspace = useCallback(() => {
		setView("onboarding");
		setTree(null);
		setSelectedNodeId(null);
		setDetails(null);
		setJourney(initialJourneyState);
		setHighlightedNodeIds([]);
		setError(null);
	}, []);

	const toggleControlPanel = useCallback(() => {
		setIsControlPanelVisible((prev) => !prev);
	}, []);

	const setMode = useCallback((mode: ViewMode) => {
		setViewMode(mode);
	}, []);

	const startJourney = useCallback(
		async (nodeId: string) => {
			const resolvedNode = await ensureChildrenLoaded(nodeId);
			if (!resolvedNode) return;
			await focusNode(nodeId);
			setJourney({
				isActive: true,
				pathIds: [nodeId],
				currentNodeId: nodeId,
				branchOptions: resolvedNode.children ?? [],
				awaitingBranch: false,
				completed: (resolvedNode.children?.length ?? 0) === 0,
				pendingBranchNodeId: null,
			});
			highlightNodes([nodeId]);
		},
		[ensureChildrenLoaded, focusNode, highlightNodes]
	);

	const travelToNode = useCallback(
		async (nodeId: string) => {
			const resolvedNode = await ensureChildrenLoaded(nodeId);
			if (!resolvedNode) return;
			await focusNode(nodeId);
			setJourney((prev) => {
				if (!prev.isActive) return prev;
				const existingIndex = prev.pathIds.indexOf(nodeId);
				const pathIds =
					existingIndex >= 0
						? prev.pathIds.slice(0, existingIndex + 1)
						: [...prev.pathIds, nodeId];
				const children = resolvedNode.children ?? [];
				return {
					...prev,
					pathIds,
					currentNodeId: nodeId,
					branchOptions: children,
					awaitingBranch: false,
					completed: children.length === 0,
					pendingBranchNodeId: null,
				};
			});
			highlightNodes([nodeId]);
		},
		[ensureChildrenLoaded, focusNode, highlightNodes]
	);

	const nextJourneyStep = useCallback(async () => {
		const current = journeyRef.current;
		if (!current.isActive || !current.currentNodeId) return;
		const resolvedNode = await ensureChildrenLoaded(current.currentNodeId);
		const children = resolvedNode?.children ?? [];

		if (children.length === 0) {
			setJourney((prev) => ({ ...prev, completed: true }));
			return;
		}

		if (children.length === 1) {
			await travelToNode(children[0].nodeId);
			return;
		}

		setJourney((prev) => ({
			...prev,
			awaitingBranch: true,
			branchOptions: children,
		}));
	}, [ensureChildrenLoaded, travelToNode]);

	const selectJourneyBranch = useCallback(
		async (nodeId: string) => {
			await travelToNode(nodeId);
			setJourney((prev) => {
				if (!prev.isActive) return prev;
				return {
					...prev,
					pendingBranchNodeId: nodeId,
				};
			});
		},
		[travelToNode]
	);

	const previousJourneyStep = useCallback(async () => {
		const current = journeyRef.current;
		if (!current.isActive || current.pathIds.length <= 1) return;
		const previousId = current.pathIds[current.pathIds.length - 2];
		await travelToNode(previousId);
	}, [travelToNode]);

	const cancelJourney = useCallback(() => {
		setJourney(initialJourneyState);
	}, []);

	const clearPendingBranchNode = useCallback(() => {
		setJourney((prev) => {
			if (!prev.pendingBranchNodeId) return prev;
			return { ...prev, pendingBranchNodeId: null };
		});
	}, []);

	const restartJourney = useCallback(async () => {
		const current = journeyRef.current;
		if (!current.isActive || current.pathIds.length === 0) return;
		await startJourney(current.pathIds[0]);
	}, [startJourney]);

	const selectedNode = useMemo(
		() => findWorkspaceNode(tree, selectedNodeId),
		[tree, selectedNodeId]
	);

	const currentJourneyNode = useMemo(
		() => findWorkspaceNode(tree, journey.currentNodeId),
		[tree, journey.currentNodeId]
	);

	return {
		view,
		viewMode,
		tree,
		selectedNode,
		selectedNodeId,
		details,
		isBuilding,
		isNodeLoading,
		loadingNodeId,
		error,
		highlightedNodeIds,
		isControlPanelVisible,
		journey,
		currentJourneyNode,
		actions: {
			buildGraph,
			resetWorkspace,
			toggleControlPanel,
			setMode,
			selectNode: handleNodeSelect,
			startJourney,
			nextJourneyStep,
			previousJourneyStep,
			selectJourneyBranch,
			cancelJourney,
			restartJourney,
			highlightNodes,
			clearPendingBranchNode,
		},
	};
};
