import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, X, ChevronDown, ChevronUp } from 'lucide-react';
import type { KnowledgeNodeUI } from '@/types';

interface FloatingAISynthesisProps {
  node: KnowledgeNodeUI | null;
  onClose: () => void;
}

export const FloatingAISynthesis: React.FC<FloatingAISynthesisProps> = ({ node, onClose }) => {
  const [isMinimized, setIsMinimized] = useState(false);

  if (!node) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: -30, y: 0 }}
        animate={{ opacity: 1, x: 0, y: 0 }}
        exit={{ opacity: 0, x: -30, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="pointer-events-auto absolute left-6 top-24 z-20 w-96 max-w-md rounded-2xl border border-emerald-500/30 bg-slate-950/95 text-white shadow-2xl backdrop-blur-lg"
      >
        <div className="flex items-center justify-between border-b border-white/10 p-4">
          <div className="flex items-center gap-3 text-emerald-300">
            <BrainCircuit width={20} height={20} />
            <h3 className="text-base font-bold">AI Synthesis</h3>
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
              aria-label="Close AI Synthesis"
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
            {/* Node name for context */}
            <h4 className="text-base font-semibold text-white">{node.nodeName}</h4>
            
            {/* AI-generated description only */}
            <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-3">
              <p className="leading-relaxed text-sm text-white/90">
                {node.description || 'No AI synthesis available for this node yet.'}
              </p>
            </div>
            
            {/* Source information */}
            {node.sourceCount > 0 && (
              <p className="text-xs text-white/60">
                Synthesized from {node.sourceCount} {node.sourceCount === 1 ? 'source' : 'sources'}
              </p>
            )}
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};
