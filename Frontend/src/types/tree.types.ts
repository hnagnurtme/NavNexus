import type { components } from './api.generated';

// ========================================
// API Types (from swagger)
// ========================================

export type GetKnowledgeNodeResponse = components['schemas']['GetKnowledgeNodeResponse'];
export type GetKnowledgeNodeResponseApiResponse = components['schemas']['GetKnowledgeNodeResponseApiResponse'];
export type CreatedKnowledgetreeRequest = components['schemas']['CreatedKnowledgetreeRequest'];
export type RabbitMqSendingResponse = components['schemas']['RabbitMqSendingResponse'];
export type RabbitMqSendingResponseApiResponse = components['schemas']['RabbitMqSendingResponseApiResponse'];

// ========================================
// Root Knowledge Tree Types (New API Format)
// ========================================

/**
 * Data payload for root knowledge tree response
 * Backend returns array of root nodes with full nested children
 */
export interface RootKnowledgeTreeData {
  totalNodes: number;
  rootNode: GetKnowledgeNodeResponse[]; // Array of root nodes (from backend List<>)
}

/**
 * Complete API response for root knowledge tree
 */
export interface RootKnowledgeTreeApiResponse {
  success: boolean;
  message: string;
  data: RootKnowledgeTreeData;
  statusCode: number;
  meta?: string;
  errorCode?: string;
}

// ========================================
// UI-Specific Types
// ========================================

/**
 * UI-enhanced node for tree visualization.
 * Extends API response with UI state (expanded, visited, etc.)
 */
export interface KnowledgeNodeUI {
  // Core fields from API
  nodeId: string;
  nodeName: string;
  description: string;
  tags: string[];
  level: number;
  sourceCount: number;
  evidences: components['schemas']['Evidence'][];
  gapSuggestions?: components['schemas']['GapSuggestion'][];
  createdAt: string;
  updatedAt: string;
  
  // Computed fields
  hasChildren: boolean;
  
  // UI state
  children?: KnowledgeNodeUI[];
  isExpanded: boolean;
  childrenLoaded: boolean;
  isVisited?: boolean;
  isBookmarked?: boolean;
}
