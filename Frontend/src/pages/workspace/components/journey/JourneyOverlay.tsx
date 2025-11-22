import clsx from "clsx";
import { ArrowLeft, ArrowRight, GitBranch, MapPin, X, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { JourneyState } from "../../hooks/useWorkspaceExperience";
import type { WorkspaceNode } from "../../utils/treeUtils";

interface JourneyOverlayProps {
	journey: JourneyState;
	currentNode: WorkspaceNode | null;
	pathNodes: { id: string; name: string }[];
	onNext: () => void;
	onBack: () => void;
	onRestart: () => void;
	onCancel: () => void;
	onSelectBranch: (nodeId: string) => void;
}

export const JourneyOverlay: React.FC<JourneyOverlayProps> = ({
	journey,
	currentNode,
	pathNodes,
	onNext,
	onBack,
	onRestart,
	onCancel,
	onSelectBranch,
}) => {
	if (!journey.isActive) {
		return null;
	}

	const progress =
		journey.pathIds.length > 0
			? Math.round(
					((journey.pathIds.length - (journey.completed ? 0 : 1)) /
						(journey.pathIds.length || 1)) *
						100
			  )
			: 0;

	return (
		<AnimatePresence>
			{journey.isActive && (
				<motion.div 
					className="pointer-events-auto fixed bottom-6 left-1/2 z-20 w-full max-w-3xl -translate-x-1/2 px-4"
					initial={{ y: 100, opacity: 0, scale: 0.95 }}
					animate={{ y: 0, opacity: 1, scale: 1 }}
					exit={{ y: 100, opacity: 0, scale: 0.95 }}
					transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
				>
					<motion.div 
						className="rounded-3xl border border-emerald-500/30 bg-slate-900/90 p-5 text-white shadow-2xl backdrop-blur"
						initial={{ boxShadow: '0 0 0 rgba(16, 185, 129, 0)' }}
						animate={{ boxShadow: '0 20px 40px rgba(16, 185, 129, 0.15)' }}
						transition={{ duration: 0.5 }}
					>
					{/* Branch Selection View */}
					{journey.awaitingBranch ? (
						<motion.div
							key="branch-selection"
							initial={{ opacity: 0, y: 20 }}
							animate={{ opacity: 1, y: 0 }}
							exit={{ opacity: 0, y: -20 }}
							transition={{ duration: 0.3 }}
						>
							<header className="mb-4 flex items-center justify-between gap-4">
								<motion.div 
									className="flex items-center gap-3"
									initial={{ x: -20, opacity: 0 }}
									animate={{ x: 0, opacity: 1 }}
									transition={{ delay: 0.1 }}
								>
									<motion.div
										animate={{ rotate: [0, 15, -15, 0] }}
										transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
									>
										<GitBranch
											size={24}
											className="text-cyan-300"
										/>
									</motion.div>
									<div>
										<p className="text-xs uppercase tracking-[0.4em] text-cyan-300">
											Branch Selection
										</p>
										<h3 className="text-xl font-semibold">
											Choose your path
										</h3>
									</div>
								</motion.div>
								<motion.button
									type="button"
									onClick={onCancel}
									className="rounded-full border border-white/10 p-2 text-white/60 transition hover:text-white"
									aria-label="Exit journey mode"
									whileHover={{ scale: 1.1, rotate: 90 }}
									whileTap={{ scale: 0.9 }}
								>
									<X size={18} />
								</motion.button>
							</header>

							<p className="text-sm text-white/70 mb-4">
								Select a branch to continue your journey:
							</p>

							<div className="flex w-full flex-nowrap gap-3 overflow-x-auto p-2 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10 hover:scrollbar-thumb-white/20">
								{journey.branchOptions.map((option, index) => (
									<motion.button
										type="button"
										key={option.nodeId}
										onClick={() =>
											onSelectBranch(option.nodeId)
										}
										className="
                rounded-2xl border border-white/10 bg-white/5 p-3 text-left 
                transition hover:border-emerald-400/60 hover:bg-emerald-500/10 
                flex-shrink-0 
                min-w-[200px] max-w-[200px]
                break-words
              "
										initial={{ opacity: 0, y: 20 }}
										animate={{ opacity: 1, y: 0 }}
										transition={{ delay: index * 0.1 }}
										whileHover={{ scale: 1.05, y: -5 }}
										whileTap={{ scale: 0.98 }}
									>
										<h5 className="mt-1 text-base font-semibold">
											{option.nodeName}
										</h5>
									</motion.button>
								))}
							</div>
						</motion.div>
					) : (
						<motion.div
							key="journey-progress"
							initial={{ opacity: 0, y: 20 }}
							animate={{ opacity: 1, y: 0 }}
							exit={{ opacity: 0, y: -20 }}
							transition={{ duration: 0.3 }}
						>
							{/* Normal Journey View */}
							<header className="mb-4 flex items-center justify-between gap-4">
								<motion.div
									initial={{ x: -20, opacity: 0 }}
									animate={{ x: 0, opacity: 1 }}
									transition={{ delay: 0.1 }}
								>
									<div className="flex items-center gap-2">
										<p className="text-xs uppercase tracking-[0.4em] text-emerald-300">
											Journey Mode
										</p>
										<motion.div
											animate={{ scale: [1, 1.2, 1], opacity: [0.7, 1, 0.7] }}
											transition={{ duration: 2, repeat: Infinity }}
										>
											<Sparkles size={12} className="text-emerald-300" />
										</motion.div>
									</div>
									<h3 className="text-2xl font-semibold">
										{currentNode
											? currentNode.nodeName
											: "Exploration"}
									</h3>
									{currentNode?.tags &&
										currentNode.tags.length > 0 && (
											<motion.div 
												className="mt-1 flex flex-wrap gap-1"
												initial={{ opacity: 0 }}
												animate={{ opacity: 1 }}
												transition={{ delay: 0.2 }}
											>
												{currentNode.tags.map(
													(tag, idx) => (
														<motion.span
															key={idx}
															className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/70"
															initial={{ scale: 0 }}
															animate={{ scale: 1 }}
															transition={{ delay: 0.3 + idx * 0.05 }}
														>
															{tag}
														</motion.span>
													)
												)}
											</motion.div>
										)}
								</motion.div>
								<motion.button
									type="button"
									onClick={onCancel}
									className="rounded-full border border-white/10 p-2 text-white/60 transition hover:text-white"
									aria-label="Exit journey mode"
									whileHover={{ scale: 1.1, rotate: 90 }}
									whileTap={{ scale: 0.9 }}
								>
									<X size={18} />
								</motion.button>
							</header>

							<div className="mb-4">
								<div className="flex items-center justify-between text-xs text-white/60">
									<span className="flex items-center gap-2">
										<MapPin size={12} />
										Step {journey.pathIds.length}
									</span>
									<span>{progress}% complete</span>
								</div>
								<div className="mt-2 h-2 w-full rounded-full bg-white/10 overflow-hidden">
									<motion.div
										className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500"
										initial={{ width: 0 }}
										animate={{ width: `${progress}%` }}
										transition={{ duration: 0.5, ease: 'easeOut' }}
									/>
								</div>
							</div>

							<div className="flex w-full gap-2 overflow-x-auto text-xs whitespace-nowrap scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10 hover:scrollbar-thumb-white/20">
								{pathNodes.map((node) => (
									<span
										key={node.id}
										className={clsx(
											"rounded-full border px-3 py-1 truncate max-w-[200px] overflow-hidden whitespace-nowrap",
											node.id === journey.currentNodeId
												? "border-emerald-400 bg-emerald-500/20 text-white"
												: "border-white/10 text-white/70"
										)}
									>
										{node.name}
									</span>
								))}
							</div>

							<div className="mt-5 flex flex-wrap gap-3">
								<motion.button
									type="button"
									onClick={onBack}
									className="flex items-center gap-2 rounded-2xl border border-white/10 px-4 py-2 text-sm font-semibold text-white/70 transition hover:border-white/40"
									whileHover={{ scale: 1.05, x: -5 }}
									whileTap={{ scale: 0.95 }}
								>
									<ArrowLeft size={16} />
									Back
								</motion.button>
								{!journey.completed ? (
									<motion.button
										type="button"
										onClick={onNext}
										className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-6 py-2 text-sm font-semibold text-white shadow-lg transition hover:brightness-110"
										whileHover={{ scale: 1.05 }}
										whileTap={{ scale: 0.95 }}
										animate={{ boxShadow: ['0 4px 14px 0 rgba(16, 185, 129, 0.4)', '0 4px 20px 0 rgba(16, 185, 129, 0.6)', '0 4px 14px 0 rgba(16, 185, 129, 0.4)'] }}
										transition={{ duration: 2, repeat: Infinity }}
									>
										Next Step
										<ArrowRight size={16} />
									</motion.button>
								) : (
									<motion.button
										type="button"
										onClick={onRestart}
										className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-emerald-500/40 px-6 py-2 text-sm font-semibold text-emerald-200 hover:border-emerald-400"
										whileHover={{ scale: 1.05 }}
										whileTap={{ scale: 0.95 }}
									>
										Restart
									</motion.button>
								)}
							</div>
						</motion.div>
					)}
				</motion.div>

				<style>{`
				@media (prefers-reduced-motion: reduce) {
					* {
						animation-duration: 0.01ms !important;
						animation-iteration-count: 1 !important;
						transition-duration: 0.01ms !important;
					}
				}
			`}</style>
			</motion.div>
		)}
	</AnimatePresence>
	);
};
