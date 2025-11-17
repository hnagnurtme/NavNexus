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
import { EvidenceCard } from "./EvidenceCard";
import { GapAssistant } from "./GapAssistant";

interface ForensicPanelProps {
	details: KnowledgeNodeUI | null;
	selectedNode: WorkspaceNode | null;
	isLoading: boolean;
	journeyActive: boolean;
	onStartJourney: (nodeId: string) => void;
	onHighlightRelated: (nodeIds: string[]) => void;
}

export const ForensicPanel: React.FC<ForensicPanelProps> = ({
	details,
	selectedNode,
	isLoading,
	journeyActive,
	onStartJourney,
}) => {
	const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>(
		[]
	);
	const [openSections, setOpenSections] = useState<Record<string, boolean>>({
		ai: true,
		node: true,
		gaps: true,
		evidence: true,
	});
	const comparisonReady = selectedEvidenceIds.length === 2;
	const hasGapSuggestions = (details?.gapSuggestions?.length ?? 0) > 0;

	useEffect(() => {
		setOpenSections({
			ai: true,
			node: true,
			gaps: hasGapSuggestions,
			evidence: true,
		});
		setSelectedEvidenceIds([]);
	}, [details?.nodeId, hasGapSuggestions]);

	const selectedEvidenceText = useMemo(() => {
		if (!details) return null;
		return (details.evidences ?? []).filter(
			(ev) => ev.id && selectedEvidenceIds.includes(ev.id)
		);
	}, [details, selectedEvidenceIds]);

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
			{/* Header */}
			<div className="border-b border-white/10 pb-4">
				<div className="flex items-start justify-between gap-3 mb-4">
					<div className="flex-1 min-w-0">
						<div className="flex items-center gap-2">
							<h2 className="text-xl font-bold text-white leading-tight">
								{details.nodeName}
							</h2>
							{hasGapSuggestions && (
								<span className="flex-shrink-0 rounded-full bg-amber-500/20 border border-amber-500/30 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-300">
									GAP
								</span>
							)}
						</div>
					</div>
				</div>

				{/* Tags and Metadata */}
				<div className="space-y-3">
					{details.tags && details.tags.length > 0 ? (
						<div className="flex flex-wrap gap-2">
							{details.tags.map((tag, idx) => (
								<span
									key={idx}
									className="rounded-full bg-blue-500/20 border border-blue-500/30 px-3 py-1 text-xs font-medium text-blue-200"
								>
									{tag}
								</span>
							))}
						</div>
					) : (
						<p className="text-xs text-white/40">
							No tags available
						</p>
					)}
					<div className="flex items-center gap-4 text-xs text-white/50">
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
				<button
					type="button"
					className="inline-flex items-center gap-1 rounded-full border border-emerald-400/70 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-100 transition hover:border-emerald-300 hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-40 mt-4"
					disabled={
						!selectedNode ||
						!selectedNode.hasChildren ||
						journeyActive
					}
					onClick={() =>
						selectedNode && onStartJourney(selectedNode.nodeId)
					}
				>
					<span aria-hidden="true">🚀</span>
					Start Journey
				</button>
			</div>

			<section className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1">
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
							hasGapSuggestions && details.gapSuggestions ? (
								<GapAssistant
									suggestions={details.gapSuggestions}
									topicName={details.nodeName}
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
									{details.evidences.map((evidence, idx) => (
										<EvidenceCard
											key={evidence.id || idx}
											evidence={evidence}
											selected={
												evidence.id
													? selectedEvidenceIds.includes(
															evidence.id
													  )
													: false
											}
											disabled={
												selectedEvidenceIds.length >=
													2 &&
												(!evidence.id ||
													!selectedEvidenceIds.includes(
														evidence.id
													))
											}
											onToggle={() => {
												const id = evidence.id;
												if (!id) return;
												setSelectedEvidenceIds((prev) =>
													prev.includes(id)
														? prev.filter(
																(selected) =>
																	selected !==
																	id
														  )
														: prev.length >= 2
														? prev
														: [...prev, id]
												);
											}}
										/>
									))}

									{comparisonReady &&
										selectedEvidenceText && (
											<div className="rounded-2xl border border-cyan-500/40 bg-cyan-500/10 p-4 text-sm text-cyan-50">
												<p className="text-xs uppercase tracking-[0.4em] text-cyan-200">
													Comparison
												</p>
												<ul className="mt-2 list-disc space-y-1 pl-4 text-cyan-100">
													{selectedEvidenceText.map(
														(evidence, idx) => (
															<li
																key={
																	evidence.id ||
																	idx
																}
															>
																{evidence.sourceName ||
																	"Unknown Source"}
															</li>
														)
													)}
												</ul>
												<p className="mt-2 text-xs text-cyan-100/80">
													TODO: Missing AI comparison
													service endpoint. Hook here
													when available.
												</p>
											</div>
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
								onClick={() => toggleSection(section.id)}
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
		</aside>
	);
};
