import dagre from 'dagre';
import type { Edge, Node } from 'reactflow';

const NODE_WIDTH = 260;
const NODE_HEIGHT = 96;

const createGraph = (direction: 'LR' | 'TB') => {
  const graph = new dagre.graphlib.Graph();
  graph.setGraph({
    rankdir: direction,
    align: 'UL',
    ranksep: direction === 'LR' ? 180 : 120,
    nodesep: 40,
    marginx: 40,
    marginy: 40,
  });
  graph.setDefaultEdgeLabel(() => ({}));
  return graph;
};

export const applyDagreLayout = (
  nodes: Node[],
  edges: Edge[],
  direction: 'LR' | 'TB' = 'LR',
): { nodes: Node[]; edges: Edge[] } => {
  const graph = createGraph(direction);

  nodes.forEach((node) => {
    graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  edges.forEach((edge) => {
    graph.setEdge(edge.source, edge.target);
  });

  dagre.layout(graph);

  const positionedNodes = nodes.map((node) => {
    const position = graph.node(node.id);
    return {
      ...node,
      position: {
        x: position.x - NODE_WIDTH / 2,
        y: position.y - NODE_HEIGHT / 2,
      },
      data: {
        ...node.data,
        layoutDirection: direction,
      },
    };
  });

  return { nodes: positionedNodes, edges };
};
