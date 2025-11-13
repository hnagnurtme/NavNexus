import { ExternalLink, Lightbulb, Search } from 'lucide-react';
import type { AiSuggestion } from '@/types';

interface GapAssistantProps {
  suggestion: AiSuggestion;
  topicName: string;
}

export const GapAssistant: React.FC<GapAssistantProps> = ({ suggestion, topicName }) => {
  const keywords = [
    `"${topicName}" reinforcement learning gap`,
    `"${topicName}" 네트워크 최적화`,
    `"${topicName}" tối ưu hoá nghiên cứu`,
  ];

  return (
    <section className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
      <div className="mb-3 flex items-center gap-2 text-amber-200">
        <Lightbulb size={18} />
        <h4 className="font-semibold uppercase tracking-widest text-xs">Gap Assistant</h4>
      </div>
      <p className="mb-3 text-amber-50/80">{suggestion.reason}</p>
      <div className="space-y-2">
        {keywords.map((keyword) => (
          <button
            key={keyword}
            type="button"
            className="flex w-full items-center justify-between rounded-xl border border-amber-500/30 bg-black/10 px-3 py-2 text-left text-xs text-amber-50/80 hover:border-amber-400"
            onClick={() => navigator.clipboard.writeText(keyword)}
          >
            <span className="line-clamp-1 font-mono">{keyword}</span>
            <Search size={14} />
          </button>
        ))}
      </div>
      <div className="mt-3 flex gap-2 text-xs text-amber-200">
        <a
          className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-3 py-1"
          target="_blank"
          rel="noreferrer"
          href={`https://scholar.google.com/scholar?q=${encodeURIComponent(keywords[0])}`}
        >
          Scholar
          <ExternalLink size={12} />
        </a>
        <a
          className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-3 py-1"
          target="_blank"
          rel="noreferrer"
          href={`https://www.dbpia.co.kr/search/topSearch?searchOption=all&query=${encodeURIComponent(keywords[1])}`}
        >
          DBpia
          <ExternalLink size={12} />
        </a>
      </div>
    </section>
  );
};
