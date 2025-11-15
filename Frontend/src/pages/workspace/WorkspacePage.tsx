import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { ControlPanel } from './components/control/ControlPanel';
import { WorkspaceCanvas } from './components/canvas/WorkspaceCanvas';
import { ForensicPanel } from './components/forensic/ForensicPanel';
import { ViewToggle } from './components/common/ViewToggle';
import { JourneyOverlay } from './components/journey/JourneyOverlay';
import { useWorkspaceExperience } from './hooks/useWorkspaceExperience';
import { findWorkspaceNode } from './utils/treeUtils';

export const WorkspacePage: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const experience = useWorkspaceExperience(workspaceId);

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
        return { id: nodeId, name: node?.name ?? nodeId };
      }),
    [journey.pathIds, tree],
  );

  const loadingNodeName = useMemo(() => {
    if (!tree || !loadingNodeId) return null;
    const node = findWorkspaceNode(tree, loadingNodeId);
    return node?.name ?? null;
  }, [loadingNodeId, tree]);

  if (!workspaceId) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-white/70">
        Workspace not found
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-slate-950 text-white">
      {error && (
        <div className="absolute left-1/2 top-4 z-30 -translate-x-1/2 rounded-full border border-rose-500/60 bg-rose-500/10 px-6 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}
      <div className="flex h-full gap-4 p-4">
        {isControlPanelVisible ? (
          <ControlPanel
            isBusy={isBuilding}
            onSynthesize={actions.buildGraph}
            onReset={actions.resetWorkspace}
            onToggleVisibility={actions.toggleControlPanel}
          />
        ) : (
          <button
            type="button"
            onClick={actions.toggleControlPanel}
            className="flex h-full w-12 items-center justify-center rounded-3xl border border-white/10 bg-white/5 text-white/60 transition hover:text-white"
            aria-label="Show control panel"
          >
            <Menu size={20} />
          </button>
        )}

        <main className="relative flex flex-1 flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.5em] text-white/50">Workspace</p>
              <h1 className="text-3xl font-semibold text-white">NavNexus Knowledge Journey</h1>
            </div>
            {view === 'active' && (
              <ViewToggle active={viewMode} onChange={actions.setMode} disabled={isBuilding} />
            )}
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
            focusedJourneyNodeId={journey.isActive ? journey.currentNodeId : null}
          />
        </main>

        <ForensicPanel
          details={details}
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
