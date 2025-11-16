import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, ExternalLink, Lightbulb, Search } from "lucide-react";
import type { GapSuggestion } from "@/types";

interface GapAssistantProps {
	suggestions: GapSuggestion[];
	topicName: string;
}

const GAP_PAGE_SIZE = 2;

export const GapAssistant: React.FC<GapAssistantProps> = ({
	suggestions,
	topicName,
}) => {
	const [page, setPage] = useState(0);
	const keywords = [
		`"${topicName}" reinforcement learning gap`,
		`"${topicName}" 네트워크 최적화`,
		`"${topicName}" tối ưu hoá nghiên cứu`,
	];

	useEffect(() => {
		setPage(0);
	}, [topicName, suggestions.length]);

	const totalPages = useMemo(() => {
		return Math.max(
			1,
			Math.ceil((suggestions?.length ?? 0) / GAP_PAGE_SIZE)
		);
	}, [suggestions?.length]);

	useEffect(() => {
		if (page > totalPages - 1) {
			setPage(totalPages - 1);
		}
	}, [page, totalPages]);

	const paginatedSuggestions = useMemo(() => {
		const start = page * GAP_PAGE_SIZE;
		return suggestions.slice(start, start + GAP_PAGE_SIZE);
	}, [page, suggestions]);

	return (
		<section className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
			<div className="mb-3 flex items-center gap-2 text-amber-200">
				<Lightbulb width={18} height={18} />
				<h4 className="font-semibold uppercase tracking-widest text-xs">
					Gap Assistant
				</h4>
			</div>

			<div className="space-y-3 mb-3">
				{paginatedSuggestions.map((suggestion, idx) => (
					<div
						key={suggestion.id || idx}
						className="rounded-xl border border-amber-500/20 bg-black/10 p-3"
					>
						<p className="text-amber-50/80">
							{suggestion.suggestionText || "Gap detected"}
						</p>
						{suggestion.similarityScore !== undefined && (
							<p className="mt-1 text-xs text-amber-200/70">
								Confidence:{" "}
								{(suggestion.similarityScore * 100).toFixed(0)}%
							</p>
						)}
					</div>
				))}
				{suggestions.length > GAP_PAGE_SIZE && (
          <div className="flex items-center justify-between px-2 py-1 text-xs text-amber-200/80">
            <button
              type="button"
              onClick={() => setPage((prev) => Math.max(0, prev - 1))}
              disabled={page === 0}
              className="px-2 py-1 transition hover:text-amber-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft width={16} height={16} />
            </button>
            <span>
              {page + 1} / {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((prev) => Math.min(totalPages - 1, prev + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-1 transition hover:text-amber-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight width={16} height={16} />
            </button>
          </div>
        )}
			</div>

			<div className="space-y-2">
				{keywords.map((keyword) => (
					<button
						key={keyword}
						type="button"
						className="flex w-full items-center justify-between rounded-xl border border-amber-500/30 bg-black/10 px-3 py-2 text-left text-xs text-amber-50/80 hover:border-amber-400"
						onClick={() => navigator.clipboard.writeText(keyword)}
					>
						<span className="line-clamp-1 font-mono">
							{keyword}
						</span>
						<Search width={14} height={14} />
					</button>
				))}
			</div>
			<div className="mt-3 flex gap-2 text-xs text-amber-200">
				<a
					className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-3 py-1"
					target="_blank"
					rel="noreferrer"
					href={`https://scholar.google.com/scholar?q=${encodeURIComponent(
						keywords[0]
					)}`}
				>
					Scholar
					<ExternalLink width={12} height={12} />
				</a>
				<a
					className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-3 py-1"
					target="_blank"
					rel="noreferrer"
					href={`https://www.dbpia.co.kr/search/topSearch?searchOption=all&query=${encodeURIComponent(
						keywords[1]
					)}`}
				>
					DBpia
					<ExternalLink width={12} height={12} />
				</a>
			</div>
		</section>
	);
};
