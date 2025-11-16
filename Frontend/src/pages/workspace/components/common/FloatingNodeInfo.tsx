import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, Tag, Calendar, Sparkles } from 'lucide-react';
import type { KnowledgeNodeUI } from '@/types';

interface FloatingNodeInfoProps {
  node: KnowledgeNodeUI | null;
  onClose: () => void;
  onStartJourney?: (nodeId: string) => void;
  journeyActive?: boolean;
}

export const FloatingNodeInfo: React.FC<FloatingNodeInfoProps> = ({
  node,
  onClose,
  onStartJourney,
  journeyActive = false,
}) => {
  if (!node) return null;

  const hasGaps = (node.gapSuggestions?.length ?? 0) > 0;
  const evidenceCount = node.evidences?.length ?? 0;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="pointer-events-auto absolute right-6 top-24 z-20 w-96 max-w-md rounded-2xl border border-cyan-500/30 bg-slate-950/95 p-5 text-white shadow-2xl backdrop-blur-lg"
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3 text-cyan-300">
            <FileText width={22} height={22} />
            <h3 className="text-lg font-bold">Node Details</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-white/60 transition hover:bg-white/10 hover:text-white"
            aria-label="Close node details"
          >
            <X width={18} height={18} />
          </button>
        </div>

        <div className="space-y-4">
          {/* Node name and tags */}
          <div>
            <h4 className="mb-2 text-xl font-semibold text-white">{node.nodeName}</h4>
            {node.tags && node.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {node.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 rounded-full bg-cyan-500/20 px-2.5 py-1 text-xs font-medium text-cyan-200"
                  >
                    <Tag width={12} height={12} />
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Description */}
          {node.description && (
            <div className="rounded-lg bg-white/5 p-3">
              <p className="text-sm leading-relaxed text-white/90">{node.description}</p>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-emerald-500/10 p-3">
              <div className="flex items-center gap-2 text-emerald-300">
                <Sparkles width={16} height={16} />
                <span className="text-xs font-semibold uppercase tracking-wider">Evidence</span>
              </div>
              <p className="mt-1 text-2xl font-bold text-white">{evidenceCount}</p>
            </div>
            <div className="rounded-lg bg-purple-500/10 p-3">
              <div className="flex items-center gap-2 text-purple-300">
                <FileText width={16} height={16} />
                <span className="text-xs font-semibold uppercase tracking-wider">Sources</span>
              </div>
              <p className="mt-1 text-2xl font-bold text-white">{node.sourceCount}</p>
            </div>
          </div>

          {/* Gap indicator */}
          {hasGaps && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
              <p className="text-sm font-semibold text-amber-200">
                ⚠️ Knowledge gaps detected
              </p>
            </div>
          )}

          {/* Children info */}
          {node.hasChildren && (
            <div className="rounded-lg bg-white/5 p-3">
              <p className="text-sm text-white/70">
                This node has <span className="font-bold text-white">{node.children?.length ?? 0}</span> child node{(node.children?.length ?? 0) !== 1 ? 's' : ''}
              </p>
            </div>
          )}

          {/* Timestamps */}
          <div className="flex items-center gap-2 text-xs text-white/50">
            <Calendar width={14} height={14} />
            <span>
              Updated: {new Date(node.updatedAt).toLocaleDateString()}
            </span>
          </div>

          {/* Action buttons */}
          {node.hasChildren && onStartJourney && (
            <button
              type="button"
              onClick={() => onStartJourney(node.nodeId)}
              disabled={journeyActive}
              className="w-full rounded-2xl border-2 border-emerald-500/60 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 px-4 py-3 text-sm font-bold uppercase tracking-wider text-emerald-200 shadow-lg transition-all hover:border-emerald-400 hover:shadow-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-50"
            >
              🚀 Start Journey from Here
            </button>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
