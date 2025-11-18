export type ContextType = "file" | "node";

export interface ContextItem {
	id: string;
	type: ContextType;
	label: string;
}

export interface ContextSuggestion {
	id: string;
	label: string;
}

export const buildDefaultContexts = (
	nodeName?: string | null,
	evidenceSources?: string[]
): ContextItem[] => {
	const baseContexts: ContextItem[] = [];
	if (nodeName) {
		baseContexts.push({
			id: `node-${nodeName}`,
			type: "node",
			label: nodeName,
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
