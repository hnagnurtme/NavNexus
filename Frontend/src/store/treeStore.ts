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

      if (!response.data?.rootNode || response.data.rootNode.length === 0) {
        throw new Error('No root nodes in response');
      }

      // NEW: Response has { data: { totalNodes, rootNode: [] } }
      // rootNode is array of nodes with full nested children
      const rootNodes = response.data.rootNode;

      console.log(`[treeStore] Loaded ${rootNodes.length} root node(s), ${response.data.totalNodes} total nodes`);

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

      set({
        tree: displayRoot,
        expandedNodeIds: new Set([displayRoot.nodeId]),
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
