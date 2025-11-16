import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { treeService } from '@/services/tree.service';
import type { NodeDetailsResponse, TreeNodeShallow } from '@/types';
import {
  WorkspaceNode,
  createWorkspaceNode,
  findWorkspaceNode,
  updateWorkspaceNode,
} from '../utils/treeUtils';

type CanvasView = 'onboarding' | 'active';
type ViewMode = 'galaxy' | 'query';

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

const convertChildren = (children: TreeNodeShallow[]): WorkspaceNode[] =>
  children.map((child) => createWorkspaceNode(child));

export const useWorkspaceExperience = (workspaceId?: string) => {
  const [view, setView] = useState<CanvasView>('onboarding');
  const [viewMode, setViewMode] = useState<ViewMode>('galaxy');
  const [tree, setTree] = useState<WorkspaceNode | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [details, setDetails] = useState<NodeDetailsResponse | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isNodeLoading, setIsNodeLoading] = useState(false);
  const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isControlPanelVisible, setIsControlPanelVisible] = useState(true);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<string[]>([]);
  const [journey, setJourney] = useState<JourneyState>(initialJourneyState);
  const highlightTimer = useRef<number | null>(null);
  const journeyRef = useRef<JourneyState>(journey);

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

  const focusNode = useCallback(
    async (nodeId: string) => {
      if (!workspaceId) return;
      setIsNodeLoading(true);
      setLoadingNodeId(nodeId);
      try {
        const data = await treeService.getNodeDetails(workspaceId, nodeId);
        setDetails(data);
        setSelectedNodeId(nodeId);
        setError(null);
      } catch (err) {
        console.error(err);
        setError('Unable to load insights for this topic.');
      } finally {
        setIsNodeLoading(false);
        setLoadingNodeId(null);
      }
    },
    [workspaceId],
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
      if (currentNode.childrenLoaded) {
        return currentNode;
      }

      try {
        const childrenData = await treeService.getNodeChildren(workspaceId, nodeId);
        const childrenNodes = convertChildren(childrenData);
        const updatedNode: WorkspaceNode = {
          ...currentNode,
          children: childrenNodes,
          childrenLoaded: true,
          isExpanded: true,
        };
        setTree((prev) => {
          if (!prev) return prev;
          return updateWorkspaceNode(prev, nodeId, () => updatedNode);
        });
        return updatedNode;
      } catch (err) {
        console.error(err);
        setError('Unable to load related nodes.');
        return null;
      }
    },
    [tree, workspaceId],
  );

  const handleNodeSelect = useCallback(
    async (nodeId: string) => {
      await ensureChildrenLoaded(nodeId);
      await focusNode(nodeId);
    },
    [ensureChildrenLoaded, focusNode],
  );

  const buildGraph = useCallback(async () => {
    if (!workspaceId) {
      setError('Missing workspace context.');
      return;
    }
    setIsBuilding(true);
    setError(null);

    try {
      const data = await treeService.getTreeRoot(workspaceId);
      const rootNode = createWorkspaceNode(data.root, {
        expanded: true,
        children: convertChildren(data.children),
      });
      rootNode.childrenLoaded = true;

      setTree(rootNode);
      setView('active');
      await focusNode(rootNode.id);
    } catch (err) {
      console.error(err);
      setError('Unable to synthesize this workspace right now.');
    } finally {
      setIsBuilding(false);
    }
  }, [workspaceId, focusNode]);

  const resetWorkspace = useCallback(() => {
    setView('onboarding');
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
    [ensureChildrenLoaded, focusNode, highlightNodes],
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
          existingIndex >= 0 ? prev.pathIds.slice(0, existingIndex + 1) : [...prev.pathIds, nodeId];
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
    [ensureChildrenLoaded, focusNode, highlightNodes],
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
      await travelToNode(children[0].id);
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
    [travelToNode],
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
    [tree, selectedNodeId],
  );

  const currentJourneyNode = useMemo(
    () => findWorkspaceNode(tree, journey.currentNodeId),
    [tree, journey.currentNodeId],
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
