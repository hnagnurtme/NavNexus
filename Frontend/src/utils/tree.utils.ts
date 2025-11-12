import type { TreeNodeUI } from '@/types';

/**
 * Find node by ID (recursive search through tree)
 */
export function findNodeById(
  tree: TreeNodeUI | null, 
  nodeId: string
): TreeNodeUI | null {
  if (!tree) return null;
  
  if (tree.id === nodeId) {
    return tree;
  }
  
  if (tree.children) {
    for (const child of tree.children) {
      const found = findNodeById(child, nodeId);
      if (found) return found;
    }
  }
  
  return null;
}

/**
 * Get path from root to node (for breadcrumb)
 */
export function getNodePath(
  tree: TreeNodeUI | null, 
  nodeId: string,
  path: TreeNodeUI[] = []
): TreeNodeUI[] {
  if (!tree) return [];
  
  path.push(tree);
  
  if (tree.id === nodeId) {
    return path;
  }
  
  if (tree.children) {
    for (const child of tree.children) {
      const result = getNodePath(child, nodeId, [...path]);
      if (result.length > 0 && result[result.length - 1].id === nodeId) {
        return result;
      }
    }
  }
  
  return [];
}

/**
 * Calculate level of a node in the tree
 */
export function calculateNodeLevel(
  tree: TreeNodeUI | null, 
  nodeId: string,
  currentLevel: number = 0
): number {
  if (!tree) return -1;
  
  if (tree.id === nodeId) {
    return currentLevel;
  }
  
  if (tree.children) {
    for (const child of tree.children) {
      const level = calculateNodeLevel(child, nodeId, currentLevel + 1);
      if (level !== -1) return level;
    }
  }
  
  return -1;
}

/**
 * Flatten tree to array
 */
export function flattenTree(
  tree: TreeNodeUI | null,
  result: TreeNodeUI[] = []
): TreeNodeUI[] {
  if (!tree) return result;
  
  result.push(tree);
  
  if (tree.children) {
    tree.children.forEach(child => flattenTree(child, result));
  }
  
  return result;
}

/**
 * Search tree by name (case-insensitive)
 */
export function searchTree(
  tree: TreeNodeUI | null, 
  query: string,
  results: TreeNodeUI[] = []
): TreeNodeUI[] {
  if (!tree || !query) return results;
  
  const normalizedQuery = query.toLowerCase().trim();
  
  if (tree.name.toLowerCase().includes(normalizedQuery)) {
    results.push(tree);
  }
  
  if (tree.children) {
    tree.children.forEach(child => searchTree(child, query, results));
  }
  
  return results;
}
