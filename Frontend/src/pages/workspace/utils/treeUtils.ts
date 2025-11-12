import type { TreeNodeShallow, TreeNodeUI } from '@/types';

export interface WorkspaceNode extends TreeNodeUI {
  children?: WorkspaceNode[];
  childrenLoaded?: boolean;
}

export const createWorkspaceNode = (
  node: TreeNodeShallow,
  options: { expanded?: boolean; children?: WorkspaceNode[] } = {},
): WorkspaceNode => ({
  ...node,
  isExpanded: options.expanded ?? false,
  children: options.children ?? [],
  childrenLoaded: Boolean(options.children && options.children.length > 0),
});

export const updateWorkspaceNode = (
  root: WorkspaceNode,
  targetId: string,
  updater: (node: WorkspaceNode) => WorkspaceNode,
): WorkspaceNode => {
  if (root.id === targetId) {
    return updater(root);
  }

  if (!root.children || root.children.length === 0) {
    return root;
  }

  return {
    ...root,
    children: root.children.map((child) =>
      child.id === targetId ? updater(child) : updateWorkspaceNode(child, targetId, updater),
    ),
  };
};

export const findWorkspaceNode = (root: WorkspaceNode | null, nodeId?: string | null): WorkspaceNode | null => {
  if (!root || !nodeId) return null;
  if (root.id === nodeId) return root;
  if (!root.children) return null;
  for (const child of root.children) {
    const match = findWorkspaceNode(child, nodeId);
    if (match) return match;
  }
  return null;
};
