import { useMemo, useState } from 'react';
import { FileText, Loader2, Sparkles } from 'lucide-react';
import type { KnowledgeNodeUI } from '@/types';
import type { WorkspaceNode } from '../../utils/treeUtils';
import { EvidenceCard } from './EvidenceCard';
import { GapAssistant } from './GapAssistant';

interface ForensicPanelProps {
  details: KnowledgeNodeUI | null;
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
    return details.evidences.filter((ev) => ev.id && selectedEvidenceIds.includes(ev.id));
  }, [details, selectedEvidenceIds]);

  const hasGapSuggestions = (details?.gapSuggestions?.length ?? 0) > 0;

  if (!details) {
    return (
      <aside className="flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-center text-white/70 shadow-2xl backdrop-blur-xl">
        <div className="flex flex-1 flex-col items-center justify-center gap-4">
          <FileText width={42} height={42} className="text-white/40" />
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
            <h2 className="text-lg font-semibold text-white">{details.nodeName}</h2>
            {details.tags && details.tags.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {details.tags.map((tag, idx) => (
                  <span 
                    key={idx} 
                    className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/70"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            {hasGapSuggestions && (
              <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-200">
                Gap
              </span>
            )}
          </div>
        </div>
        {details.sourceCount > 0 && (
          <p className="mt-2 text-xs text-white/50">
            {details.sourceCount} {details.sourceCount === 1 ? 'source' : 'sources'}
          </p>
        )}
      </header>

      <section className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="group relative flex-1 overflow-hidden rounded-2xl border-2 border-emerald-500/60 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 px-4 py-3 text-sm font-bold uppercase tracking-wider text-emerald-200 shadow-lg transition-all duration-300 hover:border-emerald-400 hover:shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={!selectedNode || !selectedNode.hasChildren || journeyActive}
          onClick={() => selectedNode && onStartJourney(selectedNode.nodeId)}
        >
          <span className="relative z-10 flex items-center justify-center gap-2">
            🚀 Start Journey
          </span>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-emerald-400/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
        </button>
        <button
          type="button"
          className="flex-1 rounded-2xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-3 text-sm font-semibold uppercase tracking-wider text-cyan-200 transition hover:border-cyan-400/80 hover:bg-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={!selectedNode || !(selectedNode.children?.length || 0)}
          onClick={() =>
            selectedNode?.children &&
            onHighlightRelated(selectedNode.children.map((child) => child.nodeId))
          }
        >
          Highlight Branches
        </button>
      </section>

      {hasGapSuggestions && details.gapSuggestions && (
        <div className="mt-4">
          <GapAssistant suggestions={details.gapSuggestions} topicName={details.nodeName} />
        </div>
      )}

      <section className="mt-4 flex-1 space-y-3 overflow-y-auto pr-3">
        <div className="flex items-center gap-2 text-white">
          <Sparkles width={16} height={16} />
          <h3 className="text-xs font-semibold uppercase tracking-widest">Evidence</h3>
        </div>
        <div className="space-y-3">
          {details.evidences && details.evidences.length > 0 ? (
            details.evidences.map((evidence, idx) => (
              <EvidenceCard
                key={evidence.id || idx}
                evidence={evidence}
                selected={evidence.id ? selectedEvidenceIds.includes(evidence.id) : false}
                disabled={selectedEvidenceIds.length >= 2 && (!evidence.id || !selectedEvidenceIds.includes(evidence.id))}
                onToggle={() => {
                  if (!evidence.id) return;
                  setSelectedEvidenceIds((prev) =>
                    prev.includes(evidence.id!)
                      ? prev.filter((id) => id !== evidence.id)
                      : prev.length >= 2
                        ? prev
                        : [...prev, evidence.id!],
                  );
                }}
              />
            ))
          ) : (
            <p className="text-sm text-white/50">No evidence available.</p>
          )}
        </div>

        {comparisonReady && selectedEvidenceText && (
          <div className="rounded-2xl border border-cyan-500/40 bg-cyan-500/10 p-4 text-sm text-cyan-50">
            <p className="text-xs uppercase tracking-[0.4em] text-cyan-200">Comparison</p>
            <ul className="mt-2 list-disc space-y-1 pl-4 text-cyan-100">
              {selectedEvidenceText.map((evidence, idx) => (
                <li key={evidence.id || idx}>{evidence.sourceName || 'Unknown Source'}</li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-cyan-100/80">
              TODO: Missing AI comparison service endpoint. Hook here when available.
            </p>
          </div>
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
