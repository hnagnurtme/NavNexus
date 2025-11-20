export type ContextType = "file" | "node";

export const DEFAULT_NODE_CONTEXT_ID = "chatbot-default-node";

export interface ContextItem {
	id: string;
	type: ContextType;
	label: string;
	entityId?: string;
}

export interface ContextSuggestion {
	id: string;
	label: string;
	entityId?: string;
}

export const buildDefaultContexts = (
	nodeName?: string | null,
	evidenceSources?: string[],
	nodeId?: string | null
): ContextItem[] => {
	const baseContexts: ContextItem[] = [];
	if (nodeName) {
		baseContexts.push({
			id: DEFAULT_NODE_CONTEXT_ID,
			type: "node",
			label: nodeName,
			entityId: nodeId ?? undefined,
		});
	}
	(evidenceSources ?? []).forEach((label, idx) => {
		const safeLabel = label?.trim();
		if (!safeLabel) return;
		baseContexts.push({
			id: `file-${idx}-${safeLabel}`,
			type: "file",
			label: safeLabel,
		});
	});
	return baseContexts;
};
