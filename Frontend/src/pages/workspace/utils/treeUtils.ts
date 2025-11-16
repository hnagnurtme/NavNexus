import type { KnowledgeNodeUI } from '@/types';

/**
 * WorkspaceNode is an alias for KnowledgeNodeUI used in workspace context
 * Kept for backward compatibility during migration
 */
export type WorkspaceNode = KnowledgeNodeUI;

/**
 * Create a workspace node from API data
 * This is a simple pass-through now that transformation happens in the service layer
 */
export const createWorkspaceNode = (
  node: KnowledgeNodeUI,
  options: { expanded?: boolean; children?: WorkspaceNode[] } = {},
): WorkspaceNode => ({
  ...node,
  isExpanded: options.expanded ?? node.isExpanded,
  children: options.children ?? node.children,
  childrenLoaded: options.children ? true : node.childrenLoaded,
});

/**
 * Update a node in the workspace tree
 */
export const updateWorkspaceNode = (
  root: WorkspaceNode,
  targetId: string,
  updater: (node: WorkspaceNode) => WorkspaceNode,
): WorkspaceNode => {
  if (root.nodeId === targetId) {
    return updater(root);
  }

  if (!root.children || root.children.length === 0) {
    return root;
  }

  return {
    ...root,
    children: root.children.map((child) =>
      child.nodeId === targetId ? updater(child) : updateWorkspaceNode(child, targetId, updater),
    ),
  };
};

/**
 * Find a node by ID in the workspace tree
 */
export const findWorkspaceNode = (
  root: WorkspaceNode | null, 
  nodeId?: string | null
): WorkspaceNode | null => {
  if (!root || !nodeId) return null;
  if (root.nodeId === nodeId) return root;
  if (!root.children) return null;
  for (const child of root.children) {
    const match = findWorkspaceNode(child, nodeId);
    if (match) return match;
  }
  return null;
};
