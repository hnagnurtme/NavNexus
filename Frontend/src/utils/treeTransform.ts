import type { GetKnowledgeNodeResponse, KnowledgeNodeUI } from '@/types';

/**
 * Transform API GetKnowledgeNodeResponse to UI KnowledgeNodeUI
 * Recursively transforms all child nodes as well
 */
export function transformToKnowledgeNodeUI(
  apiNode: GetKnowledgeNodeResponse,
  options: {
    isExpanded?: boolean;
    childrenLoaded?: boolean;
  } = {}
): KnowledgeNodeUI {
  const hasChildren = (apiNode.childNodes?.length ?? 0) > 0;
  
  return {
    nodeId: apiNode.nodeId ?? '',
    nodeName: apiNode.nodeName ?? '',
    description: apiNode.description ?? '',
    tags: apiNode.tags ?? [],
    level: apiNode.level ?? 0,
    sourceCount: apiNode.sourceCount ?? 0,
    evidences: apiNode.evidences ?? [],
    gapSuggestions: apiNode.gapSuggestions ?? undefined,
    createdAt: apiNode.createdAt ?? '',
    updatedAt: apiNode.updatedAt ?? '',
    hasChildren,
    children: apiNode.childNodes?.map(child => 
      transformToKnowledgeNodeUI(child, { isExpanded: false, childrenLoaded: true })
    ),
    isExpanded: options.isExpanded ?? false,
    childrenLoaded: options.childrenLoaded ?? hasChildren,
  };
}

/**
 * Flatten a tree structure into a list of nodes
 * Useful for graph visualization
 */
export function flattenKnowledgeTree(node: KnowledgeNodeUI): KnowledgeNodeUI[] {
  const result: KnowledgeNodeUI[] = [node];
  
  if (node.children) {
    for (const child of node.children) {
      result.push(...flattenKnowledgeTree(child));
    }
  }
  
  return result;
}

/**
 * Find a node by ID in a tree structure
 */
export function findNodeById(
  tree: KnowledgeNodeUI | null,
  nodeId: string | null
): KnowledgeNodeUI | null {
  if (!tree || !nodeId) return null;
  if (tree.nodeId === nodeId) return tree;
  
  if (tree.children) {
    for (const child of tree.children) {
      const found = findNodeById(child, nodeId);
      if (found) return found;
    }
  }
  
  return null;
}

/**
 * Update a node in the tree structure
 */
export function updateNodeInTree(
  tree: KnowledgeNodeUI | null,
  nodeId: string,
  updater: (node: KnowledgeNodeUI) => KnowledgeNodeUI
): KnowledgeNodeUI | null {
  if (!tree) return null;
  
  if (tree.nodeId === nodeId) {
    return updater(tree);
  }
  
  if (tree.children) {
    return {
      ...tree,
      children: tree.children.map(child =>
        updateNodeInTree(child, nodeId, updater)
      ).filter(Boolean) as KnowledgeNodeUI[]
    };
  }
  
  return tree;
}

/**
 * Check if a node has gap suggestions
 */
export function hasGapSuggestions(node: KnowledgeNodeUI): boolean {
  return (node.gapSuggestions?.length ?? 0) > 0;
}

/**
 * Get all node IDs from a tree (for highlighting, journey, etc.)
 */
export function getAllNodeIds(node: KnowledgeNodeUI): string[] {
  const ids = [node.nodeId];
  
  if (node.children) {
    for (const child of node.children) {
      ids.push(...getAllNodeIds(child));
    }
  }
  
  return ids;
}
