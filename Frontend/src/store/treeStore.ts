import { create } from 'zustand';
import { treeService } from '@/services/tree.service';
import type { TreeNodeUI, NodeDetailsResponse } from '@/types';

interface TreeState {
  // State
  tree: TreeNodeUI | null;
  expandedNodeIds: Set<string>;
  selectedNodeId: string | null;
  nodeDetails: NodeDetailsResponse | null;
  loading: boolean;
  error: string | null;

  // Actions
  loadTreeRoot: (workspaceId: string) => Promise<void>;
  expandNode: (workspaceId: string, nodeId: string) => Promise<void>;
  collapseNode: (nodeId: string) => void;
  selectNode: (workspaceId: string, nodeId: string) => Promise<void>;
  reset: () => void;
}

export const useTreeStore = create<TreeState>((set) => ({
  tree: null,
  expandedNodeIds: new Set(),
  selectedNodeId: null,
  nodeDetails: null,
  loading: false,
  error: null,

  loadTreeRoot: async (workspaceId: string) => {
    set({ loading: true, error: null });
    try {
      const data = await treeService.getTreeRoot(workspaceId);
      
      const rootNode: TreeNodeUI = {
        ...data.root,
        isExpanded: true,
        children: data.children.map(child => ({
          ...child,
          isExpanded: false,
          children: []
        }))
      };

      set({ 
        tree: rootNode, 
        expandedNodeIds: new Set([data.root.id]),
        loading: false 
      });
    } catch (error) {
      set({ error: 'Failed to load tree', loading: false });
    }
  },

  expandNode: async (workspaceId: string, nodeId: string) => {
    set({ loading: true });
    try {
      const [childrenData, detailsData] = await Promise.all([
        treeService.getNodeChildren(workspaceId, nodeId),
        treeService.getNodeDetails(workspaceId, nodeId)
      ]);

      set(state => ({
        tree: updateTreeNode(state.tree, nodeId, (node) => ({
          ...node,
          isExpanded: true,
          children: childrenData.map(child => ({
            ...child,
            isExpanded: false,
            children: []
          }))
        })),
        expandedNodeIds: new Set([...state.expandedNodeIds, nodeId]),
        selectedNodeId: nodeId,
        nodeDetails: detailsData,
        loading: false
      }));
    } catch (error) {
      set({ error: 'Failed to expand node', loading: false });
    }
  },

  collapseNode: (nodeId: string) => {
    set(state => ({
      tree: updateTreeNode(state.tree, nodeId, (node) => ({
        ...node,
        isExpanded: false
      })),
      expandedNodeIds: new Set(
        [...state.expandedNodeIds].filter(id => id !== nodeId)
      )
    }));
  },

  selectNode: async (workspaceId: string, nodeId: string) => {
    set({ loading: true });
    try {
      const detailsData = await treeService.getNodeDetails(workspaceId, nodeId);
      set({ 
        selectedNodeId: nodeId, 
        nodeDetails: detailsData, 
        loading: false 
      });
    } catch (error) {
      set({ error: 'Failed to load node details', loading: false });
    }
  },

  reset: () => set({ 
    tree: null, 
    expandedNodeIds: new Set(), 
    selectedNodeId: null,
    nodeDetails: null,
    loading: false,
    error: null
  })
}));

// Helper: Update node in tree (recursive)
function updateTreeNode(
  node: TreeNodeUI | null,
  targetId: string,
  updater: (node: TreeNodeUI) => TreeNodeUI
): TreeNodeUI | null {
  if (!node) return null;
  
  if (node.id === targetId) {
    return updater(node);
  }
  
  if (node.children) {
    return {
      ...node,
      children: node.children.map(child => 
        updateTreeNode(child, targetId, updater)
      ).filter(Boolean) as TreeNodeUI[]
    };
  }
  
  return node;
}
