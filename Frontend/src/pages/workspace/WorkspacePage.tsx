import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Menu } from "lucide-react";
import { ControlPanel } from "./components/control/ControlPanel";
import { WorkspaceCanvas } from "./components/canvas/WorkspaceCanvas";
import { ForensicPanel } from "./components/forensic/ForensicPanel";
import { JourneyOverlay } from "./components/journey/JourneyOverlay";
import { useWorkspaceExperience } from "./hooks/useWorkspaceExperience";
import { findWorkspaceNode } from "./utils/treeUtils";

export const WorkspacePage: React.FC = () => {
	const { workspaceId } = useParams<{ workspaceId: string }>();
	const experience = useWorkspaceExperience(workspaceId);
	const [_showAISynthesis, setShowAISynthesis] = useState(true);
	const [_showNodeInfo, setShowNodeInfo] = useState(true);

	const {
		view,
		viewMode,
		tree,
		selectedNode,
		selectedNodeId,
		details,
		isBuilding,
		isNodeLoading,
		loadingNodeId,
		error,
		highlightedNodeIds,
		isControlPanelVisible,
		journey,
		currentJourneyNode,
		actions,
	} = experience;

	const pathNodes = useMemo(
		() =>
			journey.pathIds.map((nodeId) => {
				const node = findWorkspaceNode(tree, nodeId);
				return { id: nodeId, name: node?.nodeName ?? nodeId };
			}),
		[journey.pathIds, tree]
	);

	const loadingNodeName = useMemo(() => {
		if (!tree || !loadingNodeId) return null;
		const node = findWorkspaceNode(tree, loadingNodeId);
		return node?.nodeName ?? null;
	}, [loadingNodeId, tree]);

	// Auto-show AI Synthesis when a node is selected
	useMemo(() => {
		if (details) {
			setShowAISynthesis(true);
			setShowNodeInfo(true);
		}
	}, [details]);

	if (!workspaceId) {
		return (
			<div className="flex items-center justify-center h-screen bg-slate-950 text-white/70">
				Workspace not found
			</div>
		);
	}

	return (
		<div className="w-screen h-screen text-white bg-slate-950">
			{error && (null as unknown as boolean) }
			<div className="relative flex h-full gap-4 p-4">
				{isControlPanelVisible && (
					<ControlPanel
						isBusy={isBuilding}
						onSynthesize={actions.buildGraph}
						onReset={actions.resetWorkspace}
						onToggleVisibility={actions.toggleControlPanel}
						workspaceId={workspaceId}
					/>
				)}
				{!isControlPanelVisible && (
					<button
						type="button"
						onClick={actions.toggleControlPanel}
						className="absolute z-30 flex items-center justify-center w-12 h-12 transition-all duration-200 shadow-2xl left-4 top-4 rounded-xl bg-gradient-to-br from-white/10 to-white/5 text-white/70 ring-1 ring-white/10 backdrop-blur-sm hover:scale-105 hover:from-white/15 hover:to-white/10 hover:text-white hover:shadow-white/20 active:scale-95"
						aria-label="Show control panel"
					>
						<Menu width={20} height={20} />
					</button>
				)}

				<main className="relative flex flex-col flex-1 gap-4">
					<div
						className={`flex items-center justify-between ${
							!isControlPanelVisible ? "pl-16" : ""
						}`}
					>
						<div>
							<p className="text-xs uppercase tracking-[0.5em] text-white/50">
								Workspace
							</p>
							<h1 className="text-3xl font-semibold text-white">
								NavNexus Knowledge Journey
							</h1>
						</div>
					</div>

					<WorkspaceCanvas
						workspaceId={workspaceId}
						view={view}
						viewMode={viewMode}
						isBuilding={isBuilding}
						isNodeLoading={isNodeLoading}
						loadingNodeName={loadingNodeName}
						selectedNodeId={selectedNodeId}
						highlightedNodeIds={highlightedNodeIds}
						journeyPathIds={journey.pathIds}
						onSelectNode={actions.selectNode}
						onBuildGraph={actions.buildGraph}
						pendingBranchNodeId={journey.pendingBranchNodeId}
						onPendingBranchHandled={actions.clearPendingBranchNode}
						focusedJourneyNodeId={
							journey.isActive ? journey.currentNodeId : null
						}
					/>
				</main>

				<ForensicPanel
					details={details}
					tree={tree}
					selectedNode={selectedNode}
					isLoading={isNodeLoading}
					journeyActive={journey.isActive}
					onStartJourney={actions.startJourney}
					onHighlightRelated={actions.highlightNodes}
				/>
			</div>

			<JourneyOverlay
				journey={journey}
				currentNode={currentJourneyNode}
				pathNodes={pathNodes}
				onNext={actions.nextJourneyStep}
				onBack={actions.previousJourneyStep}
				onRestart={actions.restartJourney}
				onCancel={actions.cancelJourney}
				onSelectBranch={actions.selectJourneyBranch}
			/>
		</div>
	);
};
