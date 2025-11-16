import { useState } from "react";
import clsx from "clsx";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import type { Evidence } from "@/types";

interface EvidenceCardProps {
	evidence: Evidence;
	selected: boolean;
	disabled: boolean;
	onToggle: () => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
	evidence,
	selected,
	disabled,
	onToggle,
}) => {
	const [isExpanded, setIsExpanded] = useState(false);

	return (
		<article
			className={clsx(
				"group relative rounded-xl border transition-all duration-200",
				selected
					? "border-cyan-400/60 bg-gradient-to-br from-cyan-500/15 to-cyan-600/5 shadow-lg shadow-cyan-500/20"
					: "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/[0.07]",
				disabled && !selected && "opacity-40 cursor-not-allowed",
				!disabled && "cursor-pointer"
			)}
			onClick={() => !disabled && onToggle()}
		>
			{/* Selection Indicator */}
			{selected && (
				<div className="absolute top-3 right-3 flex h-6 w-6 items-center justify-center rounded-full bg-cyan-400/90 shadow-lg">
					<svg
						width="14"
						height="14"
						viewBox="0 0 14 14"
						fill="none"
						className="text-cyan-950"
					>
						<path
							d="M11.5 3.5L5.5 9.5L2.5 6.5"
							stroke="currentColor"
							strokeWidth="2"
							strokeLinecap="round"
							strokeLinejoin="round"
						/>
					</svg>
				</div>
			)}

			<div className="p-4">
				{/* Source Name - Most Important */}
				{evidence.sourceName && (
					<div className="mb-3 flex items-start justify-between gap-3">
						<div className="flex items-center gap-2 flex-1 min-w-0">
							<FileText
								width={16}
								height={16}
								className="text-white/40 flex-shrink-0"
							/>
							<h3 className="font-semibold text-white text-sm truncate">
								{evidence.sourceName}
							</h3>
						</div>
						{evidence.page && (
							<span className="text-xs font-medium text-white/40 flex-shrink-0">
								p.{evidence.page}
							</span>
						)}
					</div>
				)}

				{/* Expand Toggle */}
				{(evidence.text?.length ?? 0) > 200 && (
					<button
						type="button"
						onClick={(e) => {
							e.stopPropagation();
							setIsExpanded(!isExpanded);
						}}
						className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-cyan-300/80 hover:text-cyan-300 transition-colors"
					>
						{isExpanded ? (
							<>
								<ChevronUp width={14} height={14} />
								Less
							</>
						) : (
							<>
								<ChevronDown width={14} height={14} />
								More
							</>
						)}
					</button>
				)}

				{/* Additional Metadata - Only When Expanded */}
				{isExpanded && (
					<div className="mt-4 pt-3 border-t border-white/10 space-y-3">
						{/* Key Claims */}
						{evidence.keyClaims &&
							evidence.keyClaims.length > 0 && (
								<div>
									<p className="text-xs font-semibold uppercase tracking-wider text-emerald-300/80 mb-2">
										Key Claims
									</p>
									<ul className="space-y-1.5">
										{evidence.keyClaims.map(
											(claim, idx) => (
												<li
													key={idx}
													className="flex gap-2 text-xs text-white/60"
												>
													<span className="text-emerald-400 mt-1">
														•
													</span>
													<span className="flex-1">
														{claim}
													</span>
												</li>
											)
										)}
									</ul>
								</div>
							)}

						{/* Questions Raised */}
						{evidence.questionsRaised &&
							evidence.questionsRaised.length > 0 && (
								<div>
									<p className="text-xs font-semibold uppercase tracking-wider text-amber-300/80 mb-2">
										Questions
									</p>
									<ul className="space-y-1.5">
										{evidence.questionsRaised.map(
											(question, idx) => (
												<li
													key={idx}
													className="flex gap-2 text-xs text-amber-200/60"
												>
													<span className="text-amber-400 mt-1">
														?
													</span>
													<span className="flex-1">
														{question}
													</span>
												</li>
											)
										)}
									</ul>
								</div>
							)}

						{/* Secondary Metadata */}
						<div className="pt-2 space-y-1">
							{evidence.hierarchyPath && (
								<p
									className="text-[10px] font-mono text-white/30 truncate"
									title={evidence.hierarchyPath}
								>
									{evidence.hierarchyPath}
								</p>
							)}
							{evidence.sourceLanguage && (
								<p className="text-[10px] text-white/30">
									Lang: {evidence.sourceLanguage}
								</p>
							)}
						</div>
					</div>
				)}
			</div>

			{/* Hover Effect Border */}
			{!selected && !disabled && (
				<div className="absolute inset-0 rounded-xl border border-cyan-400/0 group-hover:border-cyan-400/20 transition-colors pointer-events-none" />
			)}
		</article>
	);
};
