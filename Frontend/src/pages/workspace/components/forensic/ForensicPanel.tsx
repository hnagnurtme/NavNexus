import { useEffect, useMemo, useState } from "react";
import {
	AlertTriangle,
	ChevronDown,
	FileText,
	Loader2,
	Sparkles,
	Target,
} from "lucide-react";
import type { KnowledgeNodeUI } from "@/types";
import type { WorkspaceNode } from "../../utils/treeUtils";
import { ChatbotPanel } from "../chatbot/ChatbotPanel";
import { EvidenceCard } from "./EvidenceCard";
import { GapAssistant } from "./GapAssistant";
import type { ContextSuggestion } from "../chatbot/contextUtils";

const collectWorkspaceNodes = (
	node: WorkspaceNode | null
): ContextSuggestion[] => {
	if (!node) return [];
	const stack: WorkspaceNode[] = [node];
	const suggestions: ContextSuggestion[] = [];
	const seen = new Set<string>();
	while (stack.length) {
		const current = stack.pop();
		if (!current) continue;
		if (!seen.has(current.nodeId)) {
			seen.add(current.nodeId);
			suggestions.push({
				id: current.nodeId,
				label: current.nodeName,
				entityId: current.nodeId,
			});
		}
		if (current.children && current.children.length > 0) {
			for (const child of current.children) {
				stack.push(child);
			}
		}
	}
	return suggestions;
};

const collectWorkspaceFiles = (
	node: WorkspaceNode | null
): ContextSuggestion[] => {
	if (!node) return [];
	const suggestions: ContextSuggestion[] = [];
	const seen = new Set<string>();
	const traverse = (current: WorkspaceNode) => {
		(current.evidences ?? []).forEach((evidence, idx) => {
			const label =
				evidence.sourceName?.trim() ||
				evidence.id ||
				`Source ${idx + 1}`;
			if (!label || seen.has(label)) return;
			seen.add(label);
			suggestions.push({
				id: evidence.id ?? `${current.nodeId}-${idx}`,
				label,
				entityId: evidence.id ?? undefined,
			});
		});
		if (!current.children) return;
		current.children.forEach(traverse);
	};
	traverse(node);
	return suggestions;
};

interface ForensicPanelProps {
	details: KnowledgeNodeUI | null;
	tree: WorkspaceNode | null;
	selectedNode: WorkspaceNode | null;
	isLoading: boolean;
	journeyActive: boolean;
	onStartJourney: (nodeId: string) => void;
	onHighlightRelated: (nodeIds: string[]) => void;
}

export const ForensicPanel: React.FC<ForensicPanelProps> = ({
	details,
	tree,
	selectedNode,
	isLoading,
	journeyActive,
	onStartJourney,
}) => {
	const [openSections, setOpenSections] = useState<Record<string, boolean>>({
		ai: true,
		node: true,
		gaps: true,
		evidence: true,
	});
	const [activeTab, setActiveTab] = useState<"insights" | "chatbot">(
		"insights"
	);
	const hasGapSuggestions = (details?.gapSuggestions?.length ?? 0) > 0;

	useEffect(() => {
		setOpenSections({
			ai: true,
			node: true,
			gaps: hasGapSuggestions,
			evidence: true,
		});
	}, [details?.nodeId, hasGapSuggestions]);

	const nodeContextOptions = useMemo(
		() => collectWorkspaceNodes(tree),
		[tree]
	);

	const fileContextOptions = useMemo(
		() => collectWorkspaceFiles(tree),
		[tree]
	);

	const toggleSection = (sectionId: string) => {
		setOpenSections((prev) => ({
			...prev,
			[sectionId]: !prev[sectionId],
		}));
	};

	if (!details) {
		return (
			<aside className="flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-center text-white/70 shadow-2xl backdrop-blur-xl">
				<div className="flex flex-1 flex-col items-center justify-center gap-4">
					<FileText
						width={42}
						height={42}
						className="text-white/40"
					/>
					<p>
						Select a node on the canvas to inspect AI synthesis,
						evidence, and travel options.
					</p>
				</div>
			</aside>
		);
	}

	return (
		<aside className="flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-white shadow-2xl backdrop-blur-xl">
			<div className="mb-4 flex items-center gap-2 rounded-full bg-white/5 p-1">
				{[
					{ id: "insights" as const, label: "Insights" },
					{ id: "chatbot" as const, label: "AI Chatbot" },
				].map((tab) => (
					<button
						key={tab.id}
						type="button"
						onClick={() => setActiveTab(tab.id)}
						className={`flex-1 rounded-full px-3 py-1.5 text-center text-xs font-semibold uppercase tracking-[0.3em] transition ${
							activeTab === tab.id
								? "bg-gradient-to-r from-cyan-500/30 to-emerald-500/30 text-white shadow-lg shadow-cyan-500/20"
								: "text-white/50 hover:text-white"
						}`}
					>
						{tab.label}
					</button>
				))}
			</div>

			{activeTab === "insights" ? (
				<>
					<div className="border-b border-white/10 pb-2">
						<div className="mb-2 flex items-start justify-between gap-3">
							<div className="min-w-0 flex-1">
								<div className="flex items-center gap-2">
									<h2 className="text-xl font-bold leading-tight text-white">
										{details.nodeName}
									</h2>
									{hasGapSuggestions && (
										<span className="flex-shrink-0 rounded-full border border-amber-500/30 bg-amber-500/20 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-300">
											GAP
										</span>
									)}
								</div>
							</div>
						</div>

						<div className="space-y-2">
							<div className="mt-2 flex items-center justify-between gap-4 text-xs">
								<div className="flex flex-1 flex-wrap items-center gap-2 text-white/80">
									{details.tags && details.tags.length > 0 ? (
										<>
											{details.tags.map((tag, idx) => (
												<span
													key={idx}
													className="rounded-full border border-blue-500/30 bg-blue-500/20 px-3 py-1 text-[11px] font-medium text-blue-200"
												>
													{tag}
												</span>
											))}
										</>
									) : (
										<span className="text-white/40">
											No tags available
										</span>
									)}
								</div>
								<div className="flex items-center gap-4 whitespace-nowrap text-white/60">
									<div className="flex items-center gap-1.5">
										<FileText width={14} height={14} />
										<span>
											{details.sourceCount}{" "}
											{details.sourceCount === 1
												? "source"
												: "sources"}
										</span>
									</div>
									<div className="flex items-center gap-1.5">
										<Target width={14} height={14} />
										<span>Level {details.level}</span>
									</div>
								</div>
							</div>
						</div>
						<button
							type="button"
							className="mt-4 inline-flex items-center gap-1 rounded-full border border-emerald-400/70 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-100 transition hover:border-emerald-300 hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-40"
							disabled={
								!selectedNode ||
								!selectedNode.hasChildren ||
								journeyActive
							}
							onClick={() =>
								selectedNode &&
								onStartJourney(selectedNode.nodeId)
							}
						>
							<span aria-hidden="true">🚀</span>
							Start Journey
						</button>
					</div>

					<section className="scrollbar mt-2 flex-1 space-y-3 overflow-y-auto pr-1 scrollbar-thin scrollbar-track-slate-900/60 scrollbar-thumb-cyan-500/40 hover:scrollbar-thumb-cyan-400/60">
						{[
							{
								id: "ai",
								title: "AI Synthesis",
								icon: Sparkles,
								content: (
									<div className="space-y-3 text-sm text-white/80">
										<p>
											{details.description ||
												"No AI synthesis available for this node yet."}
										</p>
									</div>
								),
							},
							{
								id: "gaps",
								title: "Gap Suggestions",
								icon: AlertTriangle,
								content:
									hasGapSuggestions &&
									details.gapSuggestions ? (
										<GapAssistant
											suggestions={details.gapSuggestions}
										/>
									) : (
										<p className="text-sm text-amber-200/80">
											No gap suggestions detected.
										</p>
									),
							},
							{
								id: "evidence",
								title: "Evidence",
								icon: FileText,
								content:
									details.evidences &&
									details.evidences.length > 0 ? (
										<div className="space-y-3">
											{details.evidences.map(
												(evidence, idx) => (
													<EvidenceCard
														key={evidence.id || idx}
														evidence={evidence}
													/>
												)
											)}
										</div>
									) : (
										<p className="text-sm text-white/50">
											No evidence available.
										</p>
									),
							},
						].map((section) => {
							const Icon = section.icon;
							const isOpen = openSections[section.id];
							const isAISynthesis = section.id === "ai";
							const containerClass = isAISynthesis
								? "border-cyan-300/50 bg-gradient-to-br from-slate-950/80 via-teal-900/60 to-cyan-900/40 animate-gradient-flow"
								: "border-white/10 bg-white/5";
							const headerTextClass = isAISynthesis
								? "text-xs font-semibold uppercase tracking-widest text-cyan-100"
								: "text-xs font-semibold uppercase tracking-widest text-white";
							const iconClass = isAISynthesis
								? "text-cyan-200"
								: "text-white/70";
							const contentBorderClass = isAISynthesis
								? "border-cyan-400/30 text-cyan-50/90"
								: "border-white/10 text-white/80";
							return (
								<div
									key={section.id}
									className={`rounded-2xl border ${containerClass}`}
								>
									<button
										type="button"
										className="flex w-full items-center justify-between px-4 py-3 text-left"
										onClick={() =>
											toggleSection(section.id)
										}
										aria-expanded={isOpen}
									>
										<div className="flex items-center gap-3">
											<Icon
												width={16}
												height={16}
												className={iconClass}
											/>
											<span className={headerTextClass}>
												{section.title}
											</span>
										</div>
										<ChevronDown
											width={16}
											height={16}
											className={`text-white/60 transition-transform ${
												isOpen ? "rotate-180" : ""
											}`}
										/>
									</button>
									{isOpen && (
										<div
											className={`border-t p-4 text-sm ${contentBorderClass}`}
										>
											{section.content}
										</div>
									)}
								</div>
							);
						})}
					</section>

					{isLoading && (
						<div className="mt-4 flex items-center gap-3 text-xs uppercase tracking-[0.4em] text-white/50">
							<Loader2 className="h-4 w-4 animate-spin text-emerald-300" />
							Loading…
						</div>
					)}
				</>
			) : (
				<div className="flex flex-1 min-h-0 flex-col">
					<ChatbotPanel
						topicId={details.nodeId}
						topicName={details.nodeName}
						summary={details.description}
						nodeSuggestions={nodeContextOptions}
						fileSuggestions={fileContextOptions}
					/>
				</div>
			)}
		</aside>
	);
};
