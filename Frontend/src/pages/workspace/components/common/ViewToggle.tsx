import clsx from 'clsx';

type ViewMode = 'galaxy' | 'query';

interface ViewToggleProps {
  active: ViewMode;
  onChange: (mode: ViewMode) => void;
  disabled?: boolean;
}

export const ViewToggle: React.FC<ViewToggleProps> = ({ active, onChange, disabled }) => {
  const options: { label: string; mode: ViewMode; emoji: string }[] = [
    { label: 'Galaxy Map', mode: 'galaxy', emoji: '🌌' },
    { label: 'Query Tree', mode: 'query', emoji: '🌲' },
  ];

  return (
    <div className="flex items-center gap-2 rounded-full border border-white/10 bg-black/40 p-1 text-sm shadow-lg">
      {options.map((option) => (
        <button
          key={option.mode}
          type="button"
          disabled={disabled}
          onClick={() => onChange(option.mode)}
          className={clsx(
            'flex items-center gap-2 rounded-full px-4 py-1.5 font-medium transition',
            active === option.mode
              ? 'bg-gradient-to-r from-emerald-500/90 to-cyan-500/90 text-white shadow-lg'
              : 'text-white/60 hover:text-white',
            disabled && 'cursor-not-allowed opacity-60',
          )}
        >
          <span>{option.emoji}</span>
          {option.label}
        </button>
      ))}
    </div>
  );
};
