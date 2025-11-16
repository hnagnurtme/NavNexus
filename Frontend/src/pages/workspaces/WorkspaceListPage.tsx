import { useContext, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { WorkSpaceContext } from '@/contexts/WorkSpaceContext';
import { WorkspaceDetailResponse } from '@/types';
import { WorkSpaceCard } from '../homepage/components/WorkSpaceCard';
import AddWorkSpaceForm from '../homepage/components/AddWorkSpaceForm';
import { Header } from '../homepage/components/HomePageComponent/Header';

function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex-1">
      <label htmlFor="workspace-search" className="sr-only">
        Search workspaces
      </label>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center">
          <Search className="h-4 w-4 text-[#9a9a9a]" aria-hidden="true" />
        </span>
        <input
          id="workspace-search"
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search workspaces, descriptions, file ids..."
          className="w-full rounded-full border border-[#1f1f1f] bg-[#0f0f0f] py-3 pl-11 pr-4 text-sm text-white placeholder:text-[#7e7e7e] focus:outline-none focus:ring-2 focus:ring-[#03C75A]/30"
        />
      </div>
    </div>
  );
}

function WorkspaceGrid({ workspaces }: { workspaces: WorkspaceDetailResponse[] }) {
  if (!workspaces || workspaces.length === 0) {
    return (
      <div className="mt-10 rounded-xl border border-[#1f1f1f] bg-[#080808] p-8 text-center text-sm text-[#bdbdbd]">
        No workspaces yet — create one to get started.
      </div>
    );
  }

  return (
    <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {workspaces?.map((workspace) => (
        <motion.div
          key={workspace.workspaceId}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.2 }}
        >
          <WorkSpaceCard workspace={workspace} />
        </motion.div>
      ))}
    </div>
  );
}

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-20 flex flex-col gap-3 border-t border-[#1c1c1c] pt-8 text-xs text-[#9a9a9a] sm:flex-row sm:items-center sm:justify-between">
      <p>© {currentYear} NavNexus. All rights reserved.</p>
      <nav className="flex gap-4" aria-label="Footer navigation">
        <a href="/privacy" className="transition-colors hover:text-[#03C75A]">
          Privacy
        </a>
        <a href="/terms" className="transition-colors hover:text-[#03C75A]">
          Terms
        </a>
        <a href="/support" className="transition-colors hover:text-[#03C75A]">
          Support
        </a>
      </nav>
    </footer>
  );
}

export default function WorkspaceListPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [openWorkSpace, setOpenWorkSpace] = useState(false);
  const { WorkSpaceData } = useContext(WorkSpaceContext);

  const filteredWorkspaces = useMemo(() => {
    if (!searchTerm.trim()) return WorkSpaceData;

    const term = searchTerm.toLowerCase();
    return WorkSpaceData.filter((workspace: WorkspaceDetailResponse) => {
      const matchesName = workspace.name?.toLowerCase().includes(term);
      const matchesDescription = workspace.description?.toLowerCase().includes(term);
      const matchesFileIds = workspace.fileIds?.some((fileId: string) =>
        fileId.toLowerCase().includes(term)
      );

      return matchesName || matchesDescription || matchesFileIds;
    });
  }, [searchTerm, WorkSpaceData]);

  const handleCreateWorkspace = (data: any) => {
    console.log('Create workspace:', data);
    setOpenWorkSpace(false);
  };

  const handleCancelWorkspace = () => {
    setOpenWorkSpace(false);
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#f5f5f5]">
      {/* Modal */}
      {openWorkSpace && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md"
          role="dialog"
          aria-modal="true"
          aria-labelledby="workspace-modal-title"
        >
          <AddWorkSpaceForm onCreate={handleCreateWorkspace} onCancel={handleCancelWorkspace} />
        </div>
      )}

      <div className="mx-auto max-w-7xl px-6 py-12">
        <Header isAuthenticated={true} onCreate={() => setOpenWorkSpace(true)} />

        <section className="mt-10">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Your Workspaces</h2>
              <p className="text-sm text-[#bdbdbd]">
                Organize documents and explore relationships.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <SearchBar value={searchTerm} onChange={setSearchTerm} />
            </div>
          </div>

          <WorkspaceGrid workspaces={filteredWorkspaces} />
        </section>

        <Footer />
      </div>
    </div>
  );
}
