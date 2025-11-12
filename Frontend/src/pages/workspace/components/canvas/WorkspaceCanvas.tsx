import { Loader2 } from 'lucide-react';
import { WorkspaceNode } from '../../utils/treeUtils';
import { OnboardingPanel } from './OnboardingPanel';
import { GalaxyMapView } from './GalaxyMapView';
import { QueryTreeView } from './QueryTreeView';

type CanvasView = 'onboarding' | 'active';
type ViewMode = 'galaxy' | 'query';

type NodeSelectHandler = (nodeId: string) => void | Promise<void>;

interface WorkspaceCanvasProps {
  view: CanvasView;
  viewMode: ViewMode;
  tree: WorkspaceNode | null;
  isBuilding: boolean;
  isNodeLoading: boolean;
  selectedNodeId: string | null;
  highlightedNodeIds: string[];
  journeyPathIds: string[];
  onSelectNode: NodeSelectHandler;
  onBuildGraph: () => void;
}

export const WorkspaceCanvas: React.FC<WorkspaceCanvasProps> = ({
  view,
  viewMode,
  tree,
  isBuilding,
  isNodeLoading,
  selectedNodeId,
  highlightedNodeIds,
  journeyPathIds,
  onSelectNode,
  onBuildGraph,
}) => {
  if (view === 'onboarding') {
    return (
      <div className="relative h-full w-full rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-900 to-black p-10 text-white shadow-[0_0_120px_rgba(3,199,90,0.35)]">
        <OnboardingPanel onStart={onBuildGraph} isBuilding={isBuilding} />
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="flex h-full items-center justify-center rounded-3xl border border-white/10 bg-black/60 text-white/70">
        {isBuilding ? 'Synthesizing workspace...' : 'Upload documents to initialize this workspace.'}
      </div>
    );
  }

  return (
    <div className="relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-black p-6 text-white shadow-[0_0_80px_rgba(0,0,0,0.5)]">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(16,185,129,0.25),transparent_45%),radial-gradient(circle_at_80%_0%,rgba(59,130,246,0.2),transparent_40%)]" />
      <div className="h-full overflow-y-auto pr-2">
        {viewMode === 'galaxy' ? (
          <GalaxyMapView
            root={tree}
            selectedNodeId={selectedNodeId}
            highlightedNodeIds={highlightedNodeIds}
            journeyPathIds={journeyPathIds}
            onSelectNode={onSelectNode}
          />
        ) : (
          <QueryTreeView
            root={tree}
            selectedNodeId={selectedNodeId}
            highlightedNodeIds={highlightedNodeIds}
            journeyPathIds={journeyPathIds}
            onSelectNode={onSelectNode}
          />
        )}
      </div>

      {isNodeLoading && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="flex items-center gap-3 rounded-full border border-white/10 bg-black/60 px-5 py-2 text-sm font-medium text-white/80">
            <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
            Loading insights…
          </div>
        </div>
      )}
    </div>
  );
};
