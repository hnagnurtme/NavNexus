import { ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import { useReactFlow } from 'reactflow';

export const GraphToolbar: React.FC = () => {
  const { fitView, zoomIn, zoomOut } = useReactFlow();

  return (
    <div
      className="pointer-events-auto flex gap-2 rounded-full border border-white/10 bg-slate-900/80 p-2 text-white shadow-2xl backdrop-blur"
      onMouseDown={(event) => event.stopPropagation()}
    >
      <button
        type="button"
        aria-label="Fit view"
        onClick={() => fitView({ padding: 0.2 })}
        className="rounded-full p-2 text-white/70 transition hover:bg-white/10 hover:text-white"
      >
        <Maximize size={16} />
      </button>
      <button
        type="button"
        aria-label="Zoom in"
        onClick={() => zoomIn({ duration: 200 })}
        className="rounded-full p-2 text-white/70 transition hover:bg-white/10 hover:text-white"
      >
        <ZoomIn size={16} />
      </button>
      <button
        type="button"
        aria-label="Zoom out"
        onClick={() => zoomOut({ duration: 200 })}
        className="rounded-full p-2 text-white/70 transition hover:bg-white/10 hover:text-white"
      >
        <ZoomOut size={16} />
      </button>
    </div>
  );
};
