import { create } from 'zustand';
import { treeService } from '@/services/tree.service';
import type { KnowledgeNodeUI } from '@/types';
import { transformToKnowledgeNodeUI, updateNodeInTree } from '@/utils/treeTransform';

interface TreeState {
  // State
  tree: KnowledgeNodeUI | null;
  expandedNodeIds: Set<string>;
  selectedNodeId: string | null;
  nodeDetails: KnowledgeNodeUI | null;
  loading: boolean;
  error: string | null;

  // Actions
  loadTreeRoot: (workspaceId: string) => Promise<void>;
  expandNode: (nodeId: string) => Promise<void>;
  collapseNode: (nodeId: string) => void;
  selectNode: (nodeId: string) => Promise<void>;
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
      const response = await treeService.getKnowledgeTree(workspaceId);
      
      if (!response.data) {
        throw new Error('No data in response');
      }

      const rootNode = transformToKnowledgeNodeUI(response.data, {
        isExpanded: true,
        childrenLoaded: true,
      });

      set({ 
        tree: rootNode, 
        expandedNodeIds: new Set([rootNode.nodeId]),
        loading: false 
      });
    } catch (error) {
      console.error('Failed to load tree root:', error);
      set({ error: 'Failed to load tree', loading: false });
    }
  },

  expandNode: async (nodeId: string) => {
    set({ loading: true });
    try {
      const response = await treeService.getKnowledgeNodeById(nodeId);

      if (!response.data) {
        throw new Error('No data in response');
      }

      const updatedNode = transformToKnowledgeNodeUI(response.data, {
        isExpanded: true,
        childrenLoaded: true,
      });

      set(state => ({
        tree: updateNodeInTree(state.tree, nodeId, () => updatedNode),
        expandedNodeIds: new Set([...state.expandedNodeIds, nodeId]),
        selectedNodeId: nodeId,
        nodeDetails: updatedNode,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to expand node:', error);
      set({ error: 'Failed to expand node', loading: false });
    }
  },

  collapseNode: (nodeId: string) => {
    set(state => ({
      tree: updateNodeInTree(state.tree, nodeId, (node) => ({
        ...node,
        isExpanded: false
      })),
      expandedNodeIds: new Set(
        [...state.expandedNodeIds].filter(id => id !== nodeId)
      )
    }));
  },

  selectNode: async (nodeId: string) => {
    set({ loading: true });
    try {
      const response = await treeService.getKnowledgeNodeById(nodeId);

      if (!response.data) {
        throw new Error('No data in response');
      }

      const nodeDetails = transformToKnowledgeNodeUI(response.data, {
        isExpanded: true,
        childrenLoaded: true,
      });

      set({ 
        selectedNodeId: nodeId, 
        nodeDetails, 
        loading: false 
      });
    } catch (error) {
      console.error('Failed to load node details:', error);
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
