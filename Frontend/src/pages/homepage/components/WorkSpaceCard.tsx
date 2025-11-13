import { ArrowRight, Briefcase } from "lucide-react";
import { useNavigate } from "react-router-dom";
export const WorkSpaceCard = ({ workspace }:{workspace: any}) => {
  const navigate = useNavigate();
  return (
    <div
      key={workspace.id}
      className="group relative overflow-hidden rounded-[1.75rem] border border-[#2a2a2a] bg-[#121212] p-6 shadow-[0_20px_40px_rgba(0,0,0,0.4)] transition hover:border-[#03C75A]/40 hover:shadow-[0_30px_70px_rgba(3,199,90,0.15)]"
    >
      <div
        className={`absolute inset-0 bg-linear-to-br ${workspace.color} opacity-25`}
      />
      <div className="relative flex flex-col h-full gap-5">
        <div className="inline-flex w-fit items-center gap-2 rounded-full border border-[#2a2a2a] bg-[#1a1a1a] px-3 py-1 text-[11px] font-medium uppercase tracking-[0.3em] text-[#b3b3b3]">
          <Briefcase className="w-3 h-3 text-[#03C75A]" />
          Workspace
        </div>

        <div>
          <h4 className="text-lg font-semibold text-[#f5f5f5]">
            {workspace.name}
          </h4>
          <p className="mt-2 text-sm text-[#b3b3b3]">{workspace.description}</p>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#b3b3b3]">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#03C75A]/20 text-[11px] font-semibold text-[#03C75A]">
            {workspace.documentCount}
          </span>
          documents
        </div>

        <ul className="space-y-2 text-xs text-[#b3b3b3]">
          {workspace.documents.map((doc:any) => (
            <li key={doc} className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#03C75A]" />
              {doc}
            </li>
          ))}
        </ul>

        <button
          onClick={() => navigate(`/workspace/${workspace.id}`)}
          className="mt-auto inline-flex items-center gap-2 self-start rounded-full border border-transparent bg-[#03C75A]/20 px-4 py-2 text-sm font-semibold text-[#03C75A] transition hover:bg-[#03C75A]/30"
        >
          Open Workspace
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
