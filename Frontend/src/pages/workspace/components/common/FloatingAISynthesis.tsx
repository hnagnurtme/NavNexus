import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, X } from 'lucide-react';
import type { KnowledgeNodeUI } from '@/types';

interface FloatingAISynthesisProps {
  node: KnowledgeNodeUI | null;
  onClose: () => void;
}

export const FloatingAISynthesis: React.FC<FloatingAISynthesisProps> = ({ node, onClose }) => {
  if (!node) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: -30, y: 0 }}
        animate={{ opacity: 1, x: 0, y: 0 }}
        exit={{ opacity: 0, x: -30, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="pointer-events-auto absolute left-6 top-24 z-20 w-96 max-w-md rounded-2xl border border-emerald-500/30 bg-slate-950/95 p-5 text-white shadow-2xl backdrop-blur-lg"
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3 text-emerald-300">
            <BrainCircuit width={22} height={22} />
            <h3 className="text-lg font-bold">AI Synthesis</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-white/60 transition hover:bg-white/10 hover:text-white"
            aria-label="Close AI Synthesis"
          >
            <X width={18} height={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <h4 className="mb-2 text-base font-semibold text-white">{node.nodeName}</h4>
            {node.tags && node.tags.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-1.5">
                {node.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-medium text-emerald-200"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
          <p className="leading-relaxed text-sm text-white/90">
            {node.description || 'No synthesis available.'}
          </p>
          {node.sourceCount > 0 && (
            <p className="mt-3 text-xs text-white/60">
              Based on {node.sourceCount} {node.sourceCount === 1 ? 'source' : 'sources'}
            </p>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
