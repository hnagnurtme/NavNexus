/**
 * Adapters for converting between Swagger API types and legacy UI types
 * This allows gradual migration to swagger types without breaking existing components
 */

import type { 
  GetKnowledgeNodeResponse, 
  NodeDetailsResponse,
  Evidence,
} from '@/types';

/**
 * Convert swagger GetKnowledgeNodeResponse to legacy NodeDetailsResponse
 * Use this when consuming the new swagger endpoints but need to work with legacy UI components
 */
export function adaptSwaggerNodeToLegacy(
  swaggerNode: GetKnowledgeNodeResponse
): NodeDetailsResponse {
  return {
    id: swaggerNode.nodeId || '',
    name: swaggerNode.nodeName || '',
    type: 'concept', // Default type, could be enhanced based on other fields
    synthesis: swaggerNode.description || '',
    evidence: swaggerNode.evidences || [],
    aiSuggestion: {
      isGap: (swaggerNode.gapSuggestions?.length ?? 0) > 0,
      isCrossroads: false, // Not directly available in swagger schema
      reason: swaggerNode.gapSuggestions?.[0]?.suggestionText || '',
      suggestedDocuments: (swaggerNode.gapSuggestions || []).map(gap => ({
        title: gap.suggestionText || '',
        reason: `Similarity: ${((gap.similarityScore ?? 0) * 100).toFixed(0)}%`,
        uploadUrl: '/upload',
        previewUrl: gap.targetFileId ? `/files/${gap.targetFileId}` : undefined,
      })),
    },
  };
}

/**
 * Helper to format evidence for display
 * Handles the new swagger Evidence structure
 */
export function formatEvidenceSource(evidence: Evidence): string {
  const parts: string[] = [];
  
  if (evidence.sourceName) {
    parts.push(evidence.sourceName);
  }
  
  if (evidence.page) {
    parts.push(`Page ${evidence.page}`);
  }
  
  return parts.join(' • ') || 'Unknown Source';
}

/**
 * Helper to get evidence location display text
 */
export function formatEvidenceLocation(evidence: Evidence): string {
  return evidence.hierarchyPath || (evidence.page ? `Page ${evidence.page}` : '');
}

/**
 * Helper to calculate relative time from ISO date string
 */
export function formatRelativeTime(isoDateString: string): string {
  const date = new Date(isoDateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

/**
 * Helper to format absolute date from ISO string
 */
export function formatAbsoluteDate(isoDateString: string): string {
  const date = new Date(isoDateString);
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  });
}

/**
 * Enhanced node details that combines swagger fields with computed UI properties
 */
export interface EnhancedNodeDetails extends NodeDetailsResponse {
  // Additional swagger fields (matching swagger schema with null support)
  tags?: string[] | null;
  level?: number;
  sourceCount?: number;
  createdAt?: string;
  updatedAt?: string;
  gapSuggestions?: Array<{
    id?: string | null;
    suggestionText?: string | null;
    targetNodeId?: string | null;
    targetFileId?: string | null;
    similarityScore?: number;
  }>;
}

/**
 * Convert swagger GetKnowledgeNodeResponse to EnhancedNodeDetails
 * This preserves all swagger fields while maintaining compatibility with legacy components
 */
export function adaptToEnhancedNodeDetails(
  swaggerNode: GetKnowledgeNodeResponse
): EnhancedNodeDetails {
  const legacy = adaptSwaggerNodeToLegacy(swaggerNode);
  
  return {
    ...legacy,
    tags: swaggerNode.tags || [],
    level: swaggerNode.level,
    sourceCount: swaggerNode.sourceCount,
    createdAt: swaggerNode.createdAt,
    updatedAt: swaggerNode.updatedAt,
    gapSuggestions: swaggerNode.gapSuggestions || [],
  };
}
