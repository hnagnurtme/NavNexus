import { useMemo, useState } from 'react';
import { BrainCircuit, FileText, Loader2, Sparkles } from 'lucide-react';
import type { NodeDetailsResponse } from '@/types';
import type { WorkspaceNode } from '../../utils/treeUtils';
import { EvidenceCard } from './EvidenceCard';
import { GapAssistant } from './GapAssistant';
import { SuggestedDocuments } from './SuggestedDocuments';

interface ForensicPanelProps {
  details: NodeDetailsResponse | null;
  selectedNode: WorkspaceNode | null;
  isLoading: boolean;
  journeyActive: boolean;
  onStartJourney: (nodeId: string) => void;
  onHighlightRelated: (nodeIds: string[]) => void;
}

export const ForensicPanel: React.FC<ForensicPanelProps> = ({
  details,
  selectedNode,
  isLoading,
  journeyActive,
  onStartJourney,
  onHighlightRelated,
}) => {
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const comparisonReady = selectedEvidenceIds.length === 2;

  const selectedEvidenceText = useMemo(() => {
    if (!details) return null;
    return details.evidence.filter((ev) => selectedEvidenceIds.includes(ev.id));
  }, [details, selectedEvidenceIds]);

  if (!details) {
    return (
      <aside className="flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-center text-white/70 shadow-2xl backdrop-blur-xl">
        <div className="flex flex-1 flex-col items-center justify-center gap-4">
          <FileText size={42} className="text-white/40" />
          <p>Select a node on the canvas to inspect AI synthesis, evidence, and travel options.</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-white shadow-2xl backdrop-blur-xl">
      <header className="mb-4">
        <p className="text-xs uppercase tracking-[0.4em] text-white/50">Forensic Panel</p>
        <div className="mt-2 flex items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-white">{details.name}</h2>
            <p className="text-xs uppercase tracking-[0.4em] text-white/50">{details.type}</p>
          </div>
          <div className="flex gap-2">
            {details.aiSuggestion.isGap && (
              <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-200">
                Gap
              </span>
            )}
            {details.aiSuggestion.isCrossroads && (
              <span className="rounded-full bg-cyan-500/20 px-3 py-1 text-xs font-semibold text-cyan-200">
                Crossroad
              </span>
            )}
          </div>
        </div>
      </header>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">
        <div className="mb-3 flex items-center gap-2 text-white">
          <BrainCircuit size={18} />
          <h3 className="text-xs font-semibold uppercase tracking-widest">AI Synthesis</h3>
        </div>
        <p className="leading-relaxed text-white/80">{details.synthesis}</p>
      </section>

      <section className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="flex-1 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-emerald-200 transition hover:border-emerald-400/80"
          disabled={!selectedNode || !selectedNode.hasChildren || journeyActive}
          onClick={() => selectedNode && onStartJourney(selectedNode.id)}
        >
          Start Journey
        </button>
        <button
          type="button"
          className="flex-1 rounded-2xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cyan-200 transition hover:border-cyan-400/80"
          disabled={!selectedNode || !(selectedNode.children?.length || 0)}
          onClick={() =>
            selectedNode?.children &&
            onHighlightRelated(selectedNode.children.map((child) => child.id))
          }
        >
          Highlight Branches
        </button>
      </section>

      {details.aiSuggestion.isGap && (
        <div className="mt-4">
          <GapAssistant suggestion={details.aiSuggestion} topicName={details.name} />
        </div>
      )}

      <section className="mt-4 flex-1 space-y-3 overflow-y-auto pr-3">
        <div className="flex items-center gap-2 text-white">
          <Sparkles size={16} />
          <h3 className="text-xs font-semibold uppercase tracking-widest">Evidence</h3>
        </div>
        <div className="space-y-3">
          {details.evidence.map((evidence) => (
            <EvidenceCard
              key={evidence.id}
              evidence={evidence}
              selected={selectedEvidenceIds.includes(evidence.id)}
              disabled={selectedEvidenceIds.length >= 2 && !selectedEvidenceIds.includes(evidence.id)}
              onToggle={() =>
                setSelectedEvidenceIds((prev) =>
                  prev.includes(evidence.id)
                    ? prev.filter((id) => id !== evidence.id)
                    : prev.length >= 2
                      ? prev
                      : [...prev, evidence.id],
                )
              }
            />
          ))}
        </div>

        {comparisonReady && selectedEvidenceText && (
          <div className="rounded-2xl border border-cyan-500/40 bg-cyan-500/10 p-4 text-sm text-cyan-50">
            <p className="text-xs uppercase tracking-[0.4em] text-cyan-200">Comparison</p>
            <ul className="mt-2 list-disc space-y-1 pl-4 text-cyan-100">
              {selectedEvidenceText.map((evidence) => (
                <li key={evidence.id}>{evidence.sourceTitle}</li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-cyan-100/80">
              TODO: Missing AI comparison service endpoint. Hook here when available.
            </p>
          </div>
        )}

        {details.aiSuggestion.suggestedDocuments && details.aiSuggestion.suggestedDocuments.length > 0 && (
          <SuggestedDocuments documents={details.aiSuggestion.suggestedDocuments} />
        )}
      </section>

      {isLoading && (
        <div className="mt-4 flex items-center gap-3 text-xs uppercase tracking-[0.4em] text-white/50">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-300" />
          Loading…
        </div>
      )}
    </aside>
  );
};
