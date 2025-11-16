import type { components } from './api.generated';

// Use swagger-generated Evidence type
export type Evidence = components['schemas']['Evidence'];

// Use swagger-generated GapSuggestion type (renamed from old SuggestedDocument)
export type GapSuggestion = components['schemas']['GapSuggestion'];

// Keep legacy types for backward compatibility during migration
// TODO: Remove these once all components are migrated to swagger types
export interface SuggestedDocument {
  title: string;
  reason: string;
  uploadUrl: string;
  previewUrl?: string;
}

export interface AiSuggestion {
  isGap: boolean;
  isCrossroads: boolean;
  reason: string;
  suggestedDocuments?: SuggestedDocument[];
}
