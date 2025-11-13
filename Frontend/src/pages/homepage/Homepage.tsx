import { useMemo, useState } from 'react';
import {
  ArrowRight,
  LogIn,
  LogOut,
  Plus,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import AddWorkSpaceForm from './components/AddWorkSpaceForm';
import { WorkSpaceCard } from './components/WorkSpaceCard';

type WorkspacePreview = {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  documents: string[];
  color: string;
};

export const Homepage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { user, isAuthenticated, signOutUser, isActionLoading } = useAuth();
  const [openWorkSpace, setOpenWorkSpace] = useState(false);
  const navigate = useNavigate();

  const workspacePreviews = useMemo<WorkspacePreview[]>(
    () => [
      {
        id: 'quantum',
        name: 'Quantum Computing',
        description: 'Research papers and quantum algorithms.',
        documentCount: 4,
        documents: [
          'Quantum_Bit_Operations.pdf',
          'Qubits_Entanglement_Notes.txt',
          'Quantum_Algorithms_Overview.docx',
          'Quantum_Error_Correction.md',
        ],
        color: 'from-[#03C75A]/40 to-[#03C75A]/10',
      },
      {
        id: 'bioinformatics',
        name: 'Bioinformatics Workshop',
        description: 'Genomics analysis, protein structure insights.',
        documentCount: 3,
        documents: [
          'Genome_Sequencing_Intro.pdf',
          'Protein_Folding_Models.docx',
          'DNA_Analysis_Pipeline.txt',
        ],
        color: 'from-[#03C75A]/40 to-[#00A84D]/10',
      },
      {
        id: 'robotics',
        name: 'Robotics Engineering',
        description: 'Robot control systems and automation.',
        documentCount: 5,
        documents: [
          'Robot_Kinematics_Guide.pdf',
          'PID_Controller_Theory.docx',
          'Automation_Notes.txt',
          'Vision_System_Checklist.csv',
          'Field_Test_Observations.pdf',
        ],
        color: 'from-[#00A84D]/40 to-[#03C75A]/10',
      },
    ],
    [],
  );

  const filteredWorkspaces = useMemo(() => {
    if (!searchTerm.trim()) return workspacePreviews;
    const term = searchTerm.toLowerCase();
    return workspacePreviews.filter(
      (w) =>
        w.name.toLowerCase().includes(term) ||
        w.description.toLowerCase().includes(term) ||
        w.documents.some((doc) => doc.toLowerCase().includes(term)),
    );
  }, [searchTerm, workspacePreviews]);

  const handleCreateWorkspace = () => {
    setOpenWorkSpace(true);
  };

  const handleLogout = async () => {
    await signOutUser();
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] text-[#f5f5f5]">
      {openWorkSpace && (
        <div className='fixed inset-0 z-50 flex items-center justify-center w-full h-screen bg-black bg-opacity-50'>
                  <AddWorkSpaceForm
          onCreate={async (payload) => {
            console.log('Creating workspace:', payload);
            setOpenWorkSpace(false);
          }}
          onCancel={() => setOpenWorkSpace(false)}
        />
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
            <button
              onClick={handleCreateWorkspace}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-[#03C75A] px-6 py-3 text-sm font-semibold text-black shadow-lg shadow-[#03C75A]/25 transition hover:scale-[1.03]"
            >
              <Plus className="w-4 h-4" />
              Create Workspace
            </button>
            {isAuthenticated && user ? (
              <button
                onClick={handleLogout}
                disabled={isActionLoading}
                className="inline-flex items-center justify-center gap-2 rounded-full border border-[#2a2a2a] bg-[#1a1a1a] px-4 py-3 text-sm font-semibold text-[#f5f5f5] transition hover:border-[#03C75A] hover:bg-[#1f1f1f]"
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
                Featured Workspaces
              </h3>
              <p className="text-sm text-[#b3b3b3]">
                Jump into curated demos showcasing different research domains.
              </p>
            </div>
            <button
              onClick={handleCreateWorkspace}
              className="inline-flex items-center gap-2 rounded-full border border-[#03C75A]/60 px-4 py-2 text-sm font-semibold text-[#03C75A] transition hover:bg-[#03C75A]/10"
            >
              View all
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {filteredWorkspaces.map((workspace) => (
              <WorkSpaceCard  workspace={workspace} />
            ))}
            {filteredWorkspaces.length === 0 && (
              <div className="col-span-full rounded-[1.75rem] border border-dashed border-[#2a2a2a] bg-[#121212] p-10 text-center text-sm text-[#b3b3b3]">
                No workspaces match “{searchTerm}”.
              </div>
            )}
          </div>
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
