import { NodeType } from './tree.types';

export interface Evidence {
  id: string;
  text: string;
  location: string;
  sourceTitle: string;
  sourceAuthor: string;
  sourceYear: number;
  sourceUrl: string;
}

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

export interface NodeDetailsResponse {
  id: string;
  name: string;
  type: NodeType;
  synthesis: string;
  evidence: Evidence[];
  aiSuggestion: AiSuggestion;
}
