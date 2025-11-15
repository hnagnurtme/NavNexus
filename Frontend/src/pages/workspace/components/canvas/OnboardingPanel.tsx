import { Rocket } from 'lucide-react';

interface OnboardingPanelProps {
  onStart: () => void;
  isBuilding: boolean;
}

export const OnboardingPanel: React.FC<OnboardingPanelProps> = ({ onStart, isBuilding }) => (
  <div className="flex h-full flex-col items-center justify-center text-center text-white">
    <Rocket className="mb-6 text-emerald-400" width={72} height={72} />
    <h1 className="mb-4 text-4xl font-bold tracking-tight">Knowledge Graph Synthesizer</h1>
    <p className="max-w-2xl text-lg text-white/70">
      Upload your multilingual research dossiers and let NavNexus harmonize terminology, expose
      knowledge gaps, and guide you through a cinematic learning journey.
    </p>
    <button
      type="button"
      onClick={onStart}
      disabled={isBuilding}
      className="mt-10 rounded-full bg-emerald-500 px-10 py-3 text-sm font-semibold uppercase tracking-widest text-white shadow-lg transition enabled:hover:translate-y-0.5 disabled:cursor-wait"
    >
      {isBuilding ? 'Preparing...' : 'Start with AI'}
    </button>
  </div>
);
