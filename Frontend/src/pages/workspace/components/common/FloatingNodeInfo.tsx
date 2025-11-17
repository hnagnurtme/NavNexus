import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, Tag, Calendar, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
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
  const [isMinimized, setIsMinimized] = useState(false);

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
        className="pointer-events-auto absolute right-6 top-24 z-20 w-80 max-w-sm rounded-2xl border border-cyan-500/30 bg-slate-950/95 text-white shadow-2xl backdrop-blur-lg"
      >
        <div className="flex items-center justify-between border-b border-white/10 p-4">
          <div className="flex items-center gap-3 text-cyan-300">
            <FileText width={20} height={20} />
            <h3 className="text-base font-bold">Node Metadata</h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIsMinimized(!isMinimized)}
              className="rounded-lg p-1.5 text-white/60 transition hover:bg-white/10 hover:text-white"
              aria-label={isMinimized ? "Expand panel" : "Minimize panel"}
            >
              {isMinimized ? <ChevronDown width={16} height={16} /> : <ChevronUp width={16} height={16} />}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1.5 text-white/60 transition hover:bg-white/10 hover:text-white"
              aria-label="Close node details"
            >
              <X width={16} height={16} />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="p-4 space-y-3"
          >
            {/* Tags only - no name or description */}
            {node.tags && node.tags.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/50">Tags</p>
                <div className="flex flex-wrap gap-1.5">
                  {node.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-full bg-cyan-500/20 px-2.5 py-1 text-xs font-medium text-cyan-200"
                    >
                      <Tag width={10} height={10} />
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Stats - more compact */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-emerald-500/10 p-2.5">
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Sparkles width={14} height={14} />
                  <span className="text-xs font-semibold">Evidence</span>
                </div>
                <p className="mt-1 text-xl font-bold text-white">{evidenceCount}</p>
              </div>
              <div className="rounded-lg bg-purple-500/10 p-2.5">
                <div className="flex items-center gap-1.5 text-purple-300">
                  <FileText width={14} height={14} />
                  <span className="text-xs font-semibold">Sources</span>
                </div>
                <p className="mt-1 text-xl font-bold text-white">{node.sourceCount}</p>
              </div>
            </div>

            {/* Gap indicator */}
            {hasGaps && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5">
                <p className="text-xs font-semibold text-amber-200">
                  ⚠️ Knowledge gaps detected
                </p>
              </div>
            )}

            {/* Children info */}
            {node.hasChildren && (
              <div className="rounded-lg bg-white/5 p-2.5">
                <p className="text-xs text-white/70">
                  <span className="font-bold text-white">{node.children?.length ?? 0}</span> child node{(node.children?.length ?? 0) !== 1 ? 's' : ''}
                </p>
              </div>
            )}

            {/* Timestamps */}
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Calendar width={12} height={12} />
              <span>Updated: {new Date(node.updatedAt).toLocaleDateString()}</span>
            </div>

            {/* Action button - more compact */}
            {node.hasChildren && onStartJourney && (
              <button
                type="button"
                onClick={() => onStartJourney(node.nodeId)}
                disabled={journeyActive}
                className="w-full rounded-xl border-2 border-emerald-500/60 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 px-3 py-2 text-xs font-bold uppercase tracking-wider text-emerald-200 shadow-lg transition-all hover:border-emerald-400 hover:shadow-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-50"
              >
                🚀 Start Journey
              </button>
            )}
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};
