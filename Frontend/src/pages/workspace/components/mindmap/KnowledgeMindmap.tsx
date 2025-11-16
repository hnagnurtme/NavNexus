import React, { useState, useEffect, useCallback, memo, useMemo } from 'react';
import ReactFlow, {
  Background,
  MiniMap,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Panel,
  ReactFlowProvider,
  type Node,
  type Edge,
} from 'reactflow';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit } from 'lucide-react';
import dagre from 'dagre';
import CustomNode, { type MindmapNodeData } from './CustomNode';
import type { WorkspaceNode } from '../../utils/treeUtils';

const nodeTypes = { custom: CustomNode };

/**
 * Convert WorkspaceNode (KnowledgeNodeUI) to MindmapNodeData
 */
const toMindmapNodeData = (node: WorkspaceNode): MindmapNodeData => ({
  id: node.nodeId,
  name: node.nodeName,
  type: node.tags?.[0] || 'node', // Use first tag as type or default to 'node'
  level: node.level,
  isGap: (node.gapSuggestions?.length ?? 0) > 0,
  hasChildren: node.hasChildren,
  children: node.children?.map(toMindmapNodeData),
  evidence: node.evidences?.map(e => ({ sourceTitle: e.sourceName || 'Unknown' })),
});

const OnboardingScreen = memo(() => (
  <div className="flex h-full w-full flex-col items-center justify-center rounded-2xl bg-black/20 p-8">
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: 'easeOut' }}
      className="text-center"
    >
      <h1 className="mb-4 text-4xl font-bold text-emerald-400 md:text-5xl">Knowledge Graph Synthesizer</h1>
      <p className="mx-auto max-w-2xl text-lg text-white/70 md:text-xl">
        Upload multilingual dossiers and watch NavNexus harmonize concepts into a guided knowledge journey.
      </p>
    </motion.div>
  </div>
));

interface KnowledgeMindmapProps {
  rootNode: WorkspaceNode | null;
  view: 'onboarding' | 'active';
  viewMode: 'galaxy' | 'query';
  onNodeSelect: (node: WorkspaceNode, parent?: WorkspaceNode | null) => void;
  onClearSelection?: () => void;
  isLoading: boolean;
  selectedNode: WorkspaceNode | null;
  selectedNodeId: string | null;
  travelTargetNodeId?: string | null;
  pulsingNodeIds?: string[];
  journeyPathNodeIds?: string[];
}

const defaultEdgeOptions = {
  type: 'smoothstep',
  animated: true,
  style: { strokeWidth: 2, stroke: '#059669' },
};

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: Node[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') => {
  const nodeWidth = 260;
  const nodeHeight = 96;

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 80,
    ranksep: 160,
    edgesep: 60,
    marginx: 50,
    marginy: 50,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const positionedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: positionedNodes, edges };
};

const KnowledgeMindmapContent: React.FC<Omit<KnowledgeMindmapProps, 'view'>> = ({
  rootNode,
  viewMode,
  onNodeSelect,
  onClearSelection,
  isLoading,
  selectedNode,
  selectedNodeId,
  travelTargetNodeId,
  pulsingNodeIds = [],
  journeyPathNodeIds = [],
}) => {
  const topLevelNodes = useMemo(() => rootNode?.children ?? [], [rootNode]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { fitView } = useReactFlow();
  const [nodeDataMap, setNodeDataMap] = useState<Map<string, WorkspaceNode>>(new Map());
  const [parentMap, setParentMap] = useState<Map<string, WorkspaceNode>>(new Map());

  useEffect(() => {
    const map = new Map<string, WorkspaceNode>();
    const parents = new Map<string, WorkspaceNode>();

    const traverse = (items: WorkspaceNode[], parent?: WorkspaceNode) => {
      items.forEach((item) => {
        map.set(item.nodeId, item);
        if (parent) parents.set(item.nodeId, parent);
        if (item.children?.length) traverse(item.children, item);
      });
    };

    if (rootNode) {
      map.set(rootNode.nodeId, rootNode);
      if (rootNode.children) {
        traverse(rootNode.children, rootNode);
      }
    }

    setNodeDataMap(map);
    setParentMap(parents);

    if (viewMode === 'galaxy') {
      const initialNodes = topLevelNodes.map((node, index) => ({
        id: node.nodeId,
        data: toMindmapNodeData(node),
        position: { x: 60, y: index * 140 },
        type: 'custom',
      }));
      setNodes(initialNodes);
      setEdges([]);
      setTimeout(() => fitView({ duration: 500, padding: 0.2 }), 100);
    } else if (viewMode === 'query' && rootNode) {
      const allNodes: Node[] = [];
      const allEdges: Edge[] = [];

      const buildHierarchy = (item: WorkspaceNode, parentId?: string) => {
        allNodes.push({
          id: item.nodeId,
          data: toMindmapNodeData(item),
          position: { x: 0, y: 0 },
          type: 'custom',
        });
        if (parentId) {
          allEdges.push({
            id: `${parentId}-${item.nodeId}`,
            source: parentId,
            target: item.nodeId,
          });
        }
        item.children?.forEach((child) => buildHierarchy(child, item.nodeId));
      };

      buildHierarchy(rootNode);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(allNodes, allEdges, 'LR');
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      setTimeout(() => fitView({ duration: 800, padding: 0.2 }), 150);
    } else {
      setNodes([]);
      setEdges([]);
    }
  }, [rootNode, topLevelNodes, viewMode, setNodes, setEdges, fitView]);

  useEffect(() => {
    if (travelTargetNodeId) {
      const targetNode = nodes.find((node) => node.id === travelTargetNodeId);
      if (targetNode) {
        fitView({
          padding: 0.3,
          duration: 1200,
          nodes: [targetNode],
          maxZoom: 1.2,
          minZoom: 0.3,
        });
      }
    }
  }, [travelTargetNodeId, nodes, fitView]);

  useEffect(() => {
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        data: {
          ...node.data,
          isPulsing: pulsingNodeIds.includes(node.id),
        },
      })),
    );
  }, [pulsingNodeIds, setNodes]);

  useEffect(() => {
    if (!selectedNodeId) {
      setNodes((current) =>
        current.map((node) => ({
          ...node,
          selected: false,
        })),
      );
      return;
    }
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
      })),
    );
  }, [selectedNodeId, setNodes]);

  useEffect(() => {
    if (journeyPathNodeIds.length === 0) {
      setNodes((current) =>
        current.map((node) => ({
          ...node,
          data: {
            ...node.data,
            isOnJourneyPath: false,
            isCurrentJourneyNode: false,
          },
        })),
      );
      setEdges((current) =>
        current.map((edge) => ({
          ...edge,
          animated: true,
          style: { strokeWidth: 2, stroke: '#059669' },
        })),
      );
      return;
    }

    const currentJourneyNodeId = journeyPathNodeIds[journeyPathNodeIds.length - 1];
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        data: {
          ...node.data,
          isOnJourneyPath: journeyPathNodeIds.includes(node.id),
          isCurrentJourneyNode: node.id === currentJourneyNodeId,
        },
      })),
    );

    setEdges((current) =>
      current.map((edge) => {
        const isOnPath =
          journeyPathNodeIds.includes(edge.source) &&
          journeyPathNodeIds.includes(edge.target) &&
          journeyPathNodeIds.indexOf(edge.target) === journeyPathNodeIds.indexOf(edge.source) + 1;
        return {
          ...edge,
          animated: isOnPath,
          style: isOnPath ? { strokeWidth: 3, stroke: '#10b981' } : { strokeWidth: 2, stroke: '#059669' },
        };
      }),
    );
  }, [journeyPathNodeIds, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, clickedNode: Node<MindmapNodeData>) => {
      const fullNodeData = nodeDataMap.get(clickedNode.id);
      const parentNodeData = parentMap.get(clickedNode.id) ?? null;
      if (!fullNodeData) return;

      onNodeSelect(fullNodeData, parentNodeData);

      const isLeafNode = !fullNodeData?.children || fullNodeData.children.length === 0;
      if (isLeafNode) {
        fitView({
          padding: 0.5,
          duration: 800,
          nodes: [clickedNode],
          maxZoom: 1.5,
          minZoom: 0.5,
        });
        return;
      }

      if (viewMode !== 'galaxy') return;
      if (!fullNodeData?.children?.length) return;

      const alreadyExpanded = edges.some((edge) => edge.source === clickedNode.id);

      if (alreadyExpanded) {
        const toRemove = new Set<string>();
        const collect = (nodeId: string) => {
          edges
            .filter((edge) => edge.source === nodeId)
            .forEach((edge) => {
              toRemove.add(edge.target);
              collect(edge.target);
            });
        };
        collect(clickedNode.id);

        setNodes((current) => current.filter((node) => !toRemove.has(node.id)));
        setEdges((current) =>
          current.filter((edge) => edge.source !== clickedNode.id && !toRemove.has(edge.source)),
        );
      } else {
        const childNodes: Node[] = fullNodeData.children.map((child) => ({
          id: child.nodeId,
          data: toMindmapNodeData(child),
          position: { x: 0, y: 0 },
          type: 'custom',
        }));
        const childEdges: Edge[] = fullNodeData.children.map((child) => ({
          id: `${clickedNode.id}-${child.nodeId}`,
          source: clickedNode.id,
          target: child.nodeId,
        }));

        const mergedNodes = [...nodes, ...childNodes];
        const mergedEdges = [...edges, ...childEdges];
        const { nodes: layoutedNodes } = getLayoutedElements(mergedNodes, mergedEdges, 'LR');
        setNodes(layoutedNodes);
        setEdges(mergedEdges);
      }
      setTimeout(() => fitView({ duration: 600, padding: 0.2 }), 300);
    },
    [nodeDataMap, parentMap, onNodeSelect, viewMode, edges, nodes, setNodes, setEdges, fitView],
  );

  const onPaneClick = useCallback(() => {
    onClearSelection?.();
  }, [onClearSelection]);

  const flowNodes = useMemo(() => nodes, [nodes]);
  const flowEdges = useMemo(() => edges, [edges]);

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodeTypes={nodeTypes}
      defaultEdgeOptions={defaultEdgeOptions}
      fitView
      className="bg-transparent"
      minZoom={0.25}
    >
      <Controls className="fill-white stroke-white text-white [&>button]:bg-slate-900/80 [&>button]:border-white/20 [&>button:hover]:bg-slate-800" />
      <MiniMap className="!bg-slate-950/80 border-white/20" nodeColor="#22c55e" maskColor="rgba(40,40,40,0.8)" />
      <Background color="#334155" gap={24} size={1} />

      <AnimatePresence>
        {selectedNode && (
          <Panel position="top-left">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className="mt-16 ml-4 w-80 max-w-sm rounded-2xl border border-emerald-500/30 bg-slate-950/80 p-4 text-white shadow-2xl backdrop-blur"
            >
              <div className="mb-3 flex items-center gap-3 text-emerald-300">
                <BrainCircuit width={20} height={20} />
                <h3 className="text-lg font-bold">AI Synthesis</h3>
              </div>
              <p className="text-sm text-white/80 leading-relaxed">
                {selectedNode.description || selectedNode.nodeName}
              </p>
            </motion.div>
          </Panel>
        )}
      </AnimatePresence>

      {isLoading && (
        <Panel position="bottom-center">
          <div className="mb-4 rounded-full border border-emerald-400/40 bg-emerald-500/10 px-6 py-2 text-sm text-emerald-200 animate-pulse">
            Synthesizing Knowledge…
          </div>
        </Panel>
      )}
    </ReactFlow>
  );
};

const KnowledgeMindmap: React.FC<KnowledgeMindmapProps> = ({ view, ...props }) => {
  if (view === 'onboarding') {
    return <OnboardingScreen />;
  }

  if (!props.rootNode) {
    return (
      <div className="flex h-full items-center justify-center rounded-2xl border border-white/10 bg-slate-900/80 text-white/70">
        Upload documents to initialize this workspace.
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <KnowledgeMindmapContent {...props} />
    </ReactFlowProvider>
  );
};

export default KnowledgeMindmap;
