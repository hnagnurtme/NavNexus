import { useState } from 'react';
import {
  ArrowRight,
  LogIn,
  LogOut,
  Plus,
  Loader2,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspaces } from '@/hooks/useWorkspaces';
import AddWorkSpaceForm from './components/AddWorkSpaceForm';
import { WorkSpaceCard } from './components/WorkSpaceCard';
import type { CreateWorkspaceRequest } from '@/types/workspace.types';

export const Homepage = () => {
  const { user, isAuthenticated, signOutUser, isActionLoading } = useAuth();
  const { workspaces, isLoading: isLoadingWorkspaces, createWorkspace } = useWorkspaces();
  const [openWorkSpace, setOpenWorkSpace] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const handleCreateWorkspace = () => {
    setOpenWorkSpace(true);
    setCreateError(null);
  };

  const handleWorkspaceCreate = async (payload: {
    name: string;
    description?: string;
    visibility: 'private' | 'team' | 'public';
    color: string;
    documents: File[];
  }) => {
    try {
      setCreateError(null);
      
      // Map the form payload to API request
      const workspaceData: CreateWorkspaceRequest = {
        name: payload.name,
        description: payload.description,
        // For now, we'll leave fileIds empty as file upload is not implemented yet
        fileIds: [],
      };

      await createWorkspace(workspaceData);
      setOpenWorkSpace(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create workspace';
      setCreateError(errorMessage);
      throw err;
    }
  };

  const handleLogout = async () => {
    await signOutUser();
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] text-[#f5f5f5]">
      {openWorkSpace && (
        <div className='fixed inset-0 z-50 flex items-center justify-center w-full h-screen bg-black bg-opacity-50'>
          <div className="max-w-4xl">
            {createError && (
              <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                {createError}
              </div>
            )}
            <AddWorkSpaceForm
              onCreate={handleWorkspaceCreate}
              onCancel={() => {
                setOpenWorkSpace(false);
                setCreateError(null);
              }}
            />
          </div>
        </div>
      )}
      
      <div className="w-full px-6 py-12 mx-auto max-w-7xl">
        {/* Header */}
        <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-4">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-[#2a2a2a] bg-[#1a1a1a] px-4 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-[#b3b3b3]">
              NavNexus
            </span>
            <h1 className="text-[clamp(2.5rem,5vw,3.5rem)] font-bold leading-tight text-[#03C75A]">
              Knowledge Graph Synthesizer
            </h1>
            <p className="max-w-2xl text-sm text-[#b3b3b3]">
              Upload research artefacts, orchestrate AI-assisted knowledge graphs, and move from raw
              evidence to defensible insight faster than ever.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {isAuthenticated && (
              <button
                onClick={handleCreateWorkspace}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#03C75A] px-6 py-3 text-sm font-semibold text-black shadow-lg shadow-[#03C75A]/25 transition hover:scale-[1.03]"
              >
                <Plus className="w-4 h-4" />
                Create Workspace
              </button>
            )}
            {isAuthenticated && user ? (
              <button
                onClick={handleLogout}
                disabled={isActionLoading}
                className="inline-flex items-center justify-center gap-2 rounded-full border border-[#2a2a2a] bg-[#1a1a1a] px-4 py-3 text-sm font-semibold text-[#f5f5f5] transition hover:border-[#03C75A] hover:bg-[#1f1f1f] disabled:opacity-50"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 rounded-full border border-[#2a2a2a] bg-[#1a1a1a] px-4 py-3 text-sm font-semibold text-[#f5f5f5] transition hover:border-[#03C75A] hover:bg-[#1f1f1f]"
              >
                <LogIn className="w-4 h-4" />
                Login
              </Link>
            )}
          </div>
        </header>

        {/* Workspaces */}
        <section className="mt-12">
          <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-xl font-semibold text-[#f5f5f5]">
                {isAuthenticated ? 'Your Workspaces' : 'Featured Workspaces'}
              </h3>
              <p className="text-sm text-[#b3b3b3]">
                {isAuthenticated 
                  ? 'Manage your knowledge graphs and research workspaces.'
                  : 'Login to create and manage your own workspaces.'}
              </p>
            </div>
            {isAuthenticated && workspaces.length > 0 && (
              <button
                onClick={handleCreateWorkspace}
                className="inline-flex items-center gap-2 rounded-full border border-[#03C75A]/60 px-4 py-2 text-sm font-semibold text-[#03C75A] transition hover:bg-[#03C75A]/10"
              >
                Add New
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>

          {isLoadingWorkspaces ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-[#03C75A]" />
            </div>
          ) : workspaces.length > 0 ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {workspaces.map((workspace) => (
                <WorkSpaceCard key={workspace.workspaceId} workspace={workspace} />
              ))}
            </div>
          ) : isAuthenticated ? (
            <div className="col-span-full rounded-[1.75rem] border border-dashed border-[#2a2a2a] bg-[#121212] p-10 text-center">
              <p className="text-sm text-[#b3b3b3] mb-4">
                You don't have any workspaces yet. Create your first one to get started!
              </p>
              <button
                onClick={handleCreateWorkspace}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#03C75A] px-6 py-3 text-sm font-semibold text-black shadow-lg shadow-[#03C75A]/25 transition hover:scale-[1.03]"
              >
                <Plus className="w-4 h-4" />
                Create Your First Workspace
              </button>
            </div>
          ) : (
            <div className="col-span-full rounded-[1.75rem] border border-dashed border-[#2a2a2a] bg-[#121212] p-10 text-center">
              <p className="text-sm text-[#b3b3b3] mb-4">
                Please login to view and manage your workspaces.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#03C75A] px-6 py-3 text-sm font-semibold text-black shadow-lg shadow-[#03C75A]/25 transition hover:scale-[1.03]"
              >
                <LogIn className="w-4 h-4" />
                Login to Continue
              </Link>
            </div>
          )}
        </section>

        {/* Footer */}
        <footer className="mt-12 flex flex-col gap-3 border-t border-[#2a2a2a] pt-6 text-xs text-[#777] sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} NavNexus. All rights reserved.</p>
          <div className="flex gap-4">
            <a className="transition hover:text-[#03C75A]" href="#">
              Privacy
            </a>
            <a className="transition hover:text-[#03C75A]" href="#">
              Terms
            </a>
            <a className="transition hover:text-[#03C75A]" href="#">
              Support
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
};
