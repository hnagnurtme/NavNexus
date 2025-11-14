import clsx from "clsx";
import { ArrowLeft, ArrowRight, GitBranch, MapPin, X } from "lucide-react";
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
		<>
			<div className="pointer-events-auto fixed bottom-6 left-1/2 z-20 w-full max-w-3xl -translate-x-1/2 px-4">
				<div className="rounded-3xl border border-emerald-500/30 bg-slate-900/90 p-5 text-white shadow-2xl backdrop-blur">
					<header className="mb-4 flex items-center justify-between gap-4">
						<div>
							<p className="text-xs uppercase tracking-[0.4em] text-emerald-300">
								Journey Mode
							</p>
							<h3 className="text-2xl font-semibold">
								{currentNode ? currentNode.name : "Exploration"}
							</h3>
							<p className="text-xs uppercase tracking-[0.4em] text-white/50">
								{currentNode?.type}
							</p>
						</div>
						<button
							type="button"
							onClick={onCancel}
							className="rounded-full border border-white/10 p-2 text-white/60 transition hover:text-white"
						>
							<X width={18} height={18} />
						</button>
					</header>

					<div className="mb-4">
						<div className="flex items-center justify-between text-xs text-white/60">
							<span className="flex items-center gap-2">
								<MapPin width={12} height={12} />
								Step {journey.pathIds.length}
							</span>
							<span>{progress}% complete</span>
						</div>
						<div className="mt-2 h-2 w-full rounded-full bg-white/10">
							<div
								className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all"
								style={{ width: `${progress}%` }}
							/>
						</div>
					</div>

					<div className="flex flex-wrap gap-2 text-xs">
						{pathNodes.map((node) => (
							<span
								key={node.id}
								className={clsx(
									"rounded-full border px-3 py-1",
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
						<button
							type="button"
							onClick={onBack}
							className="flex items-center gap-2 rounded-2xl border border-white/10 px-4 py-2 text-sm font-semibold text-white/70 transition hover:border-white/40"
						>
							<ArrowLeft width={16} height={16} />
							Back
						</button>
						{!journey.completed ? (
							<button
								type="button"
								onClick={onNext}
								className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-6 py-2 text-sm font-semibold text-white shadow-lg transition hover:brightness-110"
							>
								Next Step
								<ArrowRight width={16} height={16} />
							</button>
						) : (
							<button
								type="button"
								onClick={onRestart}
								className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-emerald-500/40 px-6 py-2 text-sm font-semibold text-emerald-200 hover:border-emerald-400"
							>
								Restart
							</button>
						)}
					</div>
				</div>
			</div>

			{journey.awaitingBranch && (
				<div className="fixed inset-0 z-30 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
					<div className="w-full max-w-3xl rounded-3xl border border-white/10 bg-slate-900/90 p-6 text-white shadow-2xl">
						<div className="mb-4 flex items-center gap-2 text-cyan-300">
							<GitBranch width={20} height={20} />
							<h4 className="text-xl font-semibold">
								Choose your branch
							</h4>
						</div>
						<p className="text-sm text-white/70">
							This node fans out into multiple perspectives.
							Select a branch to continue the journey.
						</p>
						<div className="mt-6 grid gap-3 md:grid-cols-2">
							{journey.branchOptions.map((option) => (
								<button
									type="button"
									key={option.id}
									onClick={() => onSelectBranch(option.id)}
									className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-emerald-400/60 hover:bg-white/10"
								>
									<p className="text-xs uppercase tracking-[0.4em] text-white/50">
										{option.type}
									</p>
									<h5 className="mt-1 text-lg font-semibold">
										{option.name}
									</h5>
									<p className="mt-2 text-xs text-white/60">
										{option.childrenLoaded
											? `${
													option.children?.length ?? 0
											  } further leads`
											: "Select to expand this branch"}
									</p>
								</button>
							))}
						</div>
					</div>
				</div>
			)}
		</>
	);
};
