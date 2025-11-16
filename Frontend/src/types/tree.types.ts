import type { components } from './api.generated';

// Use swagger-generated types
export type GetKnowledgeNodeResponse = components['schemas']['GetKnowledgeNodeResponse'];
export type GetKnowledgeNodeResponseApiResponse = components['schemas']['GetKnowledgeNodeResponseApiResponse'];
export type CreatedKnowledgetreeRequest = components['schemas']['CreatedKnowledgetreeRequest'];
export type RabbitMqSendingResponse = components['schemas']['RabbitMqSendingResponse'];
export type RabbitMqSendingResponseApiResponse = components['schemas']['RabbitMqSendingResponseApiResponse'];

// Keep custom UI-specific types for tree visualization
// These are not in swagger as they are frontend-specific
export type NodeType = 
  | 'topic' 
  | 'document' 
  | 'problem-domain' 
  | 'algorithm' 
  | 'challenge' 
  | 'feature' 
  | 'concept'
  | 'workspace'
  |  'problem'
  | 'cause'
    | 'solution'
    | 'requirement'
    | 'bug'
    | 'improvement'
    | 'subproblem'
  ;

export interface TreeNodeShallow {
  id: string;
  name: string;
  type: NodeType;
  isGap: boolean;
  isCrossroads: boolean;
  hasChildren: boolean;
  parentId: string | null;
  level: number;
}

export interface TreeNodeUI extends TreeNodeShallow {
  children?: TreeNodeUI[];
  isExpanded: boolean;
  isVisited?: boolean;
  isBookmarked?: boolean;
}

export interface TreeRootResponse {
  root: TreeNodeShallow;
  children: TreeNodeShallow[];
}

export type NodeChildrenResponse = TreeNodeShallow[];

// Legacy type for backward compatibility during migration
// TODO: Remove once all components use GetKnowledgeNodeResponse
export interface NodeDetailsResponse {
  id: string;
  name: string;
  type: NodeType;
  synthesis: string;
  evidence: components['schemas']['Evidence'][];
  aiSuggestion: {
    isGap: boolean;
    isCrossroads: boolean;
    reason: string;
    suggestedDocuments?: Array<{
      title: string;
      reason: string;
      uploadUrl: string;
      previewUrl?: string;
    }>;
  };
}
