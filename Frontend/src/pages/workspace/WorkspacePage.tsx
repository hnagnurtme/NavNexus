import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { WorkspaceHeader } from './components/layout/WorkspaceHeader';
import { WorkspaceToolbar } from './components/layout/WorkspaceToolbar';
import { WorkspaceSidebar } from './components/layout/WorkspaceSidebar';
import { TreeNavigator } from './components/navigation/TreeNavigator';
import { KnowledgeTree } from './components/tree/KnowledgeTree';
import { useTreeStore } from '@/store/treeStore';

export const WorkspacePage: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const { loadTreeRoot, reset } = useTreeStore();

  useEffect(() => {
    if (workspaceId) {
      loadTreeRoot(workspaceId);
    }

    return () => {
      reset();
    };
  }, [workspaceId, loadTreeRoot, reset]);

  if (!workspaceId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-600 dark:text-gray-400">Invalid workspace ID</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <WorkspaceHeader workspaceName="My Workspace" />
        <WorkspaceToolbar />
        <TreeNavigator workspaceId={workspaceId} />
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <KnowledgeTree workspaceId={workspaceId} />
          </div>
        </main>
      </div>

      {/* Sidebar */}
      <WorkspaceSidebar onClose={() => {}} />
    </div>
  );
};
