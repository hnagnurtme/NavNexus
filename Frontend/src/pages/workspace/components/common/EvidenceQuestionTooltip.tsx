import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle } from 'lucide-react';

interface EvidenceQuestionTooltipProps {
  questions: string[];
  isVisible: boolean;
  position?: 'top' | 'bottom';
}

export const EvidenceQuestionTooltip: React.FC<EvidenceQuestionTooltipProps> = ({
  questions,
  isVisible,
  position = 'top',
}) => {
  if (!questions || questions.length === 0) return null;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: position === 'top' ? 10 : -10, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: position === 'top' ? 10 : -10, scale: 0.9 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={`
            absolute z-50 pointer-events-none
            ${position === 'top' ? 'bottom-full mb-3' : 'top-full mt-3'}
            left-1/2 -translate-x-1/2
            max-w-xs w-max
          `}
        >
          <div className="relative">
            {/* Tooltip Content */}
            <div className="bg-gradient-to-br from-amber-900/95 to-amber-950/95 backdrop-blur-md rounded-lg shadow-2xl border border-amber-500/30 p-3">
              <div className="flex items-start gap-2 mb-2">
                <HelpCircle size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs font-semibold text-amber-200 uppercase tracking-wide">
                  Evidence Questions
                </p>
              </div>
              
              <ul className="space-y-1.5">
                {questions.slice(0, 3).map((question, idx) => (
                  <li key={idx} className="flex gap-2 text-xs text-amber-100/90 leading-relaxed">
                    <span className="text-amber-400 flex-shrink-0">•</span>
                    <span className="flex-1">{question}</span>
                  </li>
                ))}
              </ul>
              
              {questions.length > 3 && (
                <p className="mt-2 text-[10px] text-amber-300/60 italic">
                  +{questions.length - 3} more questions
                </p>
              )}
            </div>
            
            {/* Arrow */}
            <div 
              className={`
                absolute left-1/2 -translate-x-1/2 w-0 h-0
                ${position === 'top' ? 'top-full' : 'bottom-full'}
                border-l-[6px] border-l-transparent
                border-r-[6px] border-r-transparent
                ${position === 'top' 
                  ? 'border-t-[6px] border-t-amber-900/95' 
                  : 'border-b-[6px] border-b-amber-900/95'
                }
              `}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
