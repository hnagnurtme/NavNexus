import { useEffect, useMemo, useRef, useState } from "react";
import { FileText, Loader2, Send } from "lucide-react";

type ChatRole = "user" | "ai";

interface ChatMessage {
	id: string;
	role: ChatRole;
	content: string;
	source?: string;
	timestamp: number;
}

interface ChatbotPanelProps {
	topicName?: string | null;
	summary?: string | null;
}

const buildInitialMessage = (
	topicName?: string | null,
	summary?: string | null
): ChatMessage => ({
	id: "ai-initial",
	role: "ai",
	content:
		summary && summary.trim().length > 0
			? `Here is the latest synthesis for ${
					topicName ?? "this selection"
			  }: ${summary}`
			: `Hi! I can help you reason about ${
					topicName ?? "this part of the graph"
			  }. What should we explore?`,
	source: summary ? "Node synthesis" : "Workspace knowledge graph",
	timestamp: Date.now(),
});

export const ChatbotPanel: React.FC<ChatbotPanelProps> = ({
	topicName,
	summary,
}) => {
	const [messages, setMessages] = useState<ChatMessage[]>(() => [
		buildInitialMessage(topicName, summary),
	]);
	const [inputValue, setInputValue] = useState("");
	const [isThinking, setIsThinking] = useState(false);
	const scrollAnchorRef = useRef<HTMLDivElement | null>(null);

	useEffect(() => {
		setMessages([buildInitialMessage(topicName, summary)]);
		setInputValue("");
	}, [topicName, summary]);

	useEffect(() => {
		scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages, isThinking]);

	const placeholder = useMemo(
		() => `Ask about ${topicName ?? "this topic"}...`,
		[topicName]
	);

	const addAIResponse = (prompt: string) => {
		setIsThinking(true);
		setTimeout(() => {
			setMessages((prev) => [
				...prev,
				{
					id: `ai-${Date.now()}`,
					role: "ai",
					content: `Here is how this connects back to ${
						topicName ?? "the workspace"
					}:\n${prompt} — I will outline supporting evidence and next steps as data sources come online.`,
					source: topicName
						? `${topicName} dossier`
						: "Workspace knowledge base",
					timestamp: Date.now(),
				},
			]);
			setIsThinking(false);
		}, 400);
	};

	const handleSend = () => {
		const trimmed = inputValue.trim();
		if (!trimmed) return;

		const now = Date.now();
		setMessages((prev) => [
			...prev,
			{
				id: `user-${now}`,
				role: "user",
				content: trimmed,
				timestamp: now,
			},
		]);
		setInputValue("");
		addAIResponse(trimmed);
	};

	const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (
		event
	) => {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			handleSend();
		}
	};

	return (
		<div className="flex h-full min-h-0 flex-col rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-white shadow-inner shadow-black/40">
			<div className="scrollbar flex-1 min-h-0 space-y-4 overflow-y-auto pr-2 scrollbar-thin scrollbar-track-slate-900/60 scrollbar-thumb-cyan-500/40 hover:scrollbar-thumb-cyan-400/60">
				{messages.map((message) => (
					<div
						key={message.id}
						className={`flex ${
							message.role === "user"
								? "justify-end"
								: "justify-start"
						}`}
					>
						<div
							className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-lg ${
								message.role === "user"
									? "border-emerald-400/60 bg-emerald-500/10 text-emerald-50"
									: "border-cyan-400/50 bg-slate-900/70 text-white"
							}`}
						>
							<p className="whitespace-pre-line break-words">
								{message.content}
							</p>
							{message.role === "ai" && (
								<div className="mt-2 inline-flex max-w-full items-center gap-2 rounded-lg border border-cyan-400/20 bg-cyan-500/5 px-2.5 py-1 text-[10px] text-cyan-100/70">
									<FileText className="h-3.5 w-3.5 flex-shrink-0 text-cyan-200" />
									<span className="truncate text-xs font-medium tracking-wide text-white/50">
										{message.source ?? "Graph context"}
									</span>
								</div>
							)}
						</div>
					</div>
				))}
				{isThinking && (
					<div className="flex justify-start text-sm text-cyan-200">
						<div className="flex items-center gap-2 rounded-2xl border border-cyan-400/20 bg-cyan-500/5 px-3 py-2">
							<Loader2 className="h-4 w-4 animate-spin" />
							Thinking…
						</div>
					</div>
				)}
				<div ref={scrollAnchorRef} />
			</div>

			<div className="mt-4 rounded-xl border border-white/10 bg-slate-900/80 p-2 shadow-inner shadow-black/30">
				<div className="relative">
					<textarea
						value={inputValue}
						onChange={(event) => setInputValue(event.target.value)}
						onKeyDown={handleKeyDown}
						placeholder={placeholder}
						rows={2}
						className="w-full resize-none rounded-xl bg-transparent p-2.5 pr-12 text-sm text-white placeholder:text-white/30 focus:outline-none"
					/>
					<button
						type="button"
						onClick={handleSend}
						disabled={!inputValue.trim()}
						aria-label="Send message"
						className="absolute right-3 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-100 transition hover:bg-cyan-500/30 disabled:opacity-30"
					>
						<Send className="h-4 w-4" />
					</button>
				</div>
			</div>
		</div>
	);
};
