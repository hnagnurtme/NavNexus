export type ChatRole = "user" | "ai";

export interface ChatMessage {
	id: string;
	role: ChatRole;
	content: string;
	source?: string;
	timestamp: number;
	nodeSnapshot?: string | null;
	sourceSnapshot?: string | null;
}

export const buildInitialMessage = (
	topicName?: string | null,
	summary?: string | null
): ChatMessage => ({
	id: "ai-initial",
	role: "ai",
	content:
		summary && summary.trim().length > 0
			? `Here is the latest synthesis for ${
					topicName ?? "this selection"
			  }: ${summary}`
			: `Hi! I can help you reason about ${
					topicName ?? "this part of the graph"
			  }. What should we explore?`,
	source: summary ? "Node synthesis" : "Workspace knowledge graph",
	timestamp: Date.now(),
	nodeSnapshot: topicName ?? null,
	sourceSnapshot: summary
		? "Node synthesis"
		: topicName
		? `${topicName} dossier`
		: "Workspace knowledge base",
});
