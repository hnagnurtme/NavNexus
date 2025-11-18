import { useState, useEffect } from "react";
import {
	ChevronLeft,
	ChevronRight,
	ExternalLink,
	TrendingUp,
} from "lucide-react";
import type { GapSuggestion } from "@/types";

interface GapAssistantProps {
	suggestions: GapSuggestion[];
	topicName: string;
}

const GAP_PAGE_SIZE = 1; // Show one at a time for clarity

export const GapAssistant: React.FC<GapAssistantProps> = ({
	suggestions,
	topicName,
}) => {
	const [page, setPage] = useState(0);

	useEffect(() => {
		setPage(0);
	}, [topicName, suggestions.length]);

	const totalPages = Math.max(
		1,
		Math.ceil((suggestions?.length ?? 0) / GAP_PAGE_SIZE)
	);

	useEffect(() => {
		if (page > totalPages - 1) {
			setPage(Math.max(0, totalPages - 1));
		}
	}, [page, totalPages]);

	const currentSuggestion = suggestions[page];

	// Quick search links
	const searchLinks = [
		{
			name: "Scholar",
			url: `https://scholar.google.com/scholar?q=${encodeURIComponent(
				`"${topicName}" research gap`
			)}`,
		},
		{
			name: "DBpia",
			url: `https://www.dbpia.co.kr/search/topSearch?searchOption=all&query=${encodeURIComponent(
				`"${topicName}" 연구 격차`
			)}`,
		},
	];

	if (suggestions.length === 0) {
		return (
			<div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-6 text-center">
				<p className="text-sm text-amber-200/60">
					No research gaps detected
				</p>
			</div>
		);
	}

	return (
		<div className="space-y-3">
			{/* Main Gap Card */}
			<div className="relative rounded-xl border-2 border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-amber-600/5 p-4 shadow-lg">
				{/* Confidence Badge */}
				{currentSuggestion?.similarityScore !== undefined && (
					<div className="absolute top-3 right-3 rounded-full bg-amber-500/20 px-2.5 py-1 backdrop-blur-sm">
						<div className="flex items-center gap-1.5">
							<TrendingUp
								width={12}
								height={12}
								className="text-amber-300"
							/>
							<span className="text-xs font-bold text-amber-200">
								{(
									currentSuggestion.similarityScore * 100
								).toFixed(0)}
								%
							</span>
						</div>
					</div>
				)}

				{/* Gap Text */}
				<div className="pr-16">
					<p className="text-sm leading-relaxed text-amber-50">
						{currentSuggestion?.suggestionText || "Gap detected"}
					</p>
				</div>

				{/* Pagination */}
				{suggestions.length > 1 && (
					<div className="mt-4 pt-3 border-t border-amber-500/20 flex items-center justify-between">
						<button
							type="button"
							onClick={() =>
								setPage((prev) => Math.max(0, prev - 1))
							}
							disabled={page === 0}
							className="p-1.5 rounded-lg transition-colors hover:bg-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed"
							aria-label="Previous gap"
						>
							<ChevronLeft
								width={18}
								height={18}
								className="text-amber-300"
							/>
						</button>

						<div className="flex items-center gap-2">
							{suggestions.map((_, idx) => (
								<button
									key={idx}
									onClick={() => setPage(idx)}
									className={`h-1.5 rounded-full transition-all ${
										idx === page
											? "w-6 bg-amber-400"
											: "w-1.5 bg-amber-500/30 hover:bg-amber-500/50"
									}`}
									aria-label={`Go to gap ${idx + 1}`}
								/>
							))}
						</div>

						<button
							type="button"
							onClick={() =>
								setPage((prev) =>
									Math.min(totalPages - 1, prev + 1)
								)
							}
							disabled={page >= totalPages - 1}
							className="p-1.5 rounded-lg transition-colors hover:bg-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed"
							aria-label="Next gap"
						>
							<ChevronRight
								width={18}
								height={18}
								className="text-amber-300"
							/>
						</button>
					</div>
				)}
			</div>

			{/* Quick Actions */}
			<div className="flex gap-2">
				{searchLinks.map((link) => (
					<a
						key={link.name}
						href={link.url}
						target="_blank"
						rel="noreferrer"
						className="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-200 transition-all hover:border-amber-400 hover:bg-amber-500/20 hover:shadow-lg hover:shadow-amber-500/10"
					>
						<span>{link.name}</span>
						<ExternalLink width={12} height={12} />
					</a>
				))}
			</div>
		</div>
	);
};
