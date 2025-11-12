import { useId, useState } from 'react';
import { Bot, ChevronLeft, RotateCcw, Upload } from 'lucide-react';

interface ControlPanelProps {
  isBusy: boolean;
  onSynthesize: () => void;
  onReset: () => void;
  onToggleVisibility: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  isBusy,
  onSynthesize,
  onReset,
  onToggleVisibility,
}) => {
  const [fileName, setFileName] = useState<string | null>(null);
  const inputId = useId();

  return (
    <aside className="relative flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-white shadow-2xl backdrop-blur-xl">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="text-emerald-400" size={28} />
          <div>
            <p className="text-xs uppercase tracking-widest text-white/60">AI Controls</p>
            <h2 className="text-xl font-semibold text-white">Workspace Pilot</h2>
          </div>
        </div>
        <button
          type="button"
          aria-label="Hide control panel"
          onClick={onToggleVisibility}
          className="rounded-full border border-white/10 p-2 text-white/60 transition hover:border-white/40 hover:text-white"
        >
          <ChevronLeft size={18} />
        </button>
      </header>

      <section className="flex flex-1 flex-col gap-4">
        <label
          htmlFor={inputId}
          className="group flex flex-1 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/20 bg-white/5 p-6 text-center transition hover:border-emerald-400/60 hover:bg-white/10"
        >
          <Upload size={28} className="mb-3 text-white/60 transition group-hover:text-emerald-300" />
          <p className="text-sm text-white/70">
            {fileName ?? 'Drop a research dossier or click to browse'}
          </p>
          <p className="mt-1 text-xs text-white/50">
            Supported: PDF, DOCX, TXT — max 10MB per batch
          </p>
        </label>
        <input
          id={inputId}
          type="file"
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0];
            setFileName(file ? file.name : null);
          }}
        />

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
          <p className="font-semibold text-white">How it works</p>
          <ul className="mt-3 space-y-2 text-xs leading-relaxed text-white/60">
            <li>1. Upload 1–3 sources; we auto-extract concepts + evidence.</li>
            <li>2. The AI integrity engine merges multilingual terms.</li>
            <li>3. A knowledge journey becomes available for deep dives.</li>
          </ul>
        </div>
      </section>

      <footer className="mt-6 space-y-3">
        <button
          type="button"
          onClick={onSynthesize}
          disabled={isBusy}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 py-3 text-sm font-semibold text-white shadow-lg transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Bot className="animate-pulse" size={18} />
          {isBusy ? 'Synthesizing...' : 'Build Knowledge Graph'}
        </button>
        <button
          type="button"
          onClick={onReset}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 py-3 text-sm font-semibold text-white/70 transition hover:border-white/50 hover:text-white"
        >
          <RotateCcw size={16} />
          Reset Workspace
        </button>
      </footer>
    </aside>
  );
};
