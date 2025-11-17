import { useEffect, useMemo, useRef, useState } from "react";
import { FileText, GitBranch, Loader2, Plus, Send, X } from "lucide-react";
import {
	type ContextItem,
	type ContextType,
	buildDefaultContexts,
} from "./contextUtils";
import { type ChatMessage, buildInitialMessage } from "./chatTypes";

interface ChatbotPanelProps {
	topicName?: string | null;
	summary?: string | null;
	evidenceSources?: string[];
}

export const ChatbotPanel: React.FC<ChatbotPanelProps> = ({
	topicName,
	summary,
	evidenceSources,
}) => {
	const [messages, setMessages] = useState<ChatMessage[]>(() => [
		buildInitialMessage(topicName, summary),
	]);
	const [inputValue, setInputValue] = useState("");
	const [isThinking, setIsThinking] = useState(false);
	const [contextItems, setContextItems] = useState<ContextItem[]>(() =>
		buildDefaultContexts(topicName, evidenceSources)
	);
	const scrollAnchorRef = useRef<HTMLDivElement | null>(null);
	const [isContextMenuOpen, setIsContextMenuOpen] = useState(false);

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
			const nodeSnapshot = topicName ?? null;
			const sourceSnapshot = nodeSnapshot
				? `${nodeSnapshot} dossier`
				: "Workspace knowledge base";
			setMessages((prev) => [
				...prev,
				{
					id: `ai-${Date.now()}`,
					role: "ai",
					content: `Here is how this connects back to ${
						topicName ?? "the workspace"
					}:\n${prompt} — I will outline supporting evidence and next steps as data sources come online.`,
					source: sourceSnapshot,
					nodeSnapshot,
					sourceSnapshot,
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

	const handleAddContext = (type: ContextType) => {
		if (typeof window === "undefined") return;
		const promptLabel =
			type === "node"
				? "Enter a node or concept to prioritize"
				: "Enter a document or evidence source";
		const defaultValue =
			type === "node" ? topicName ?? "Untitled node" : "Untitled file";
		const value = window.prompt(promptLabel, defaultValue);
		if (!value) return;
		const trimmed = value.trim();
		if (!trimmed) return;
		setContextItems((prev) => [
			...prev,
			{
				id: `${type}-${Date.now()}`,
				type,
				label: trimmed,
			},
		]);
	};

	const handleRemoveContext = (contextId: string) => {
		setContextItems((prev) =>
			prev.filter((context) => context.id !== contextId)
		);
	};

	const handleContextMenuSelect = (type: ContextType) => {
		setIsContextMenuOpen(false);
		handleAddContext(type);
	};

	useEffect(() => {
		setContextItems((prev) => {
			if (!topicName) {
				const hasNode = prev.some((item) => item.type === "node");
				return hasNode
					? prev.filter((item) => item.type !== "node")
					: prev;
			}
			const nodeItem: ContextItem = {
				id: `node-${topicName}`,
				type: "node",
				label: topicName,
			};
			const nodeIndex = prev.findIndex((item) => item.type === "node");
			if (nodeIndex === -1) {
				return [nodeItem, ...prev];
			}
			const existing = prev[nodeIndex];
			if (existing.label === topicName) {
				return prev;
			}
			const next = [...prev];
			next[nodeIndex] = nodeItem;
			return next;
		});
	}, [topicName]);

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
								<div className="mt-2 flex flex-wrap items-center gap-1.5">
									{message.nodeSnapshot && (
										<div className="flex items-center gap-1.5 rounded-lg border border-emerald-400/30 bg-emerald-500/5 px-2 py-1 text-[10px] text-emerald-100/80 shadow-inner shadow-black/20">
											<GitBranch className="h-3 w-3 flex-shrink-0 text-emerald-200" />
											<span className="max-w-[120px] truncate font-semibold text-emerald-50">
												{message.nodeSnapshot}
											</span>
										</div>
									)}
									{(message.sourceSnapshot ??
										message.source) && (
										<div className="flex items-center gap-1.5 rounded-lg border border-cyan-400/30 bg-cyan-500/5 px-2 py-1 text-[10px] text-cyan-100/80 shadow-inner shadow-black/20">
											<FileText className="h-3 w-3 flex-shrink-0 text-cyan-200" />
											<span className="max-w-[140px] truncate font-semibold text-white/80">
												{message.sourceSnapshot ??
													message.source}
											</span>
										</div>
									)}
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

			<div className="mt-4 rounded-xl border border-white/10 bg-slate-900/80 p-2.5 shadow-inner shadow-black/30">
				<div className="mb-2 flex flex-wrap items-center gap-1.5 text-[11px] text-white/60">
					<div className="relative">
						<button
							type="button"
							onClick={() =>
								setIsContextMenuOpen((prev) => !prev)
							}
							className="inline-flex h-6 w-6 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white transition hover:border-white/30 hover:bg-white/10"
							aria-label="Add context"
						>
							<Plus className="h-3.5 w-3.5" />
						</button>
						{isContextMenuOpen && (
							<div className="absolute bottom-8 left-0 z-10 mb-2 w-32 rounded-xl border border-white/10 bg-slate-900/95 p-1 text-[11px] text-white shadow-xl">
								<button
									type="button"
									onClick={() =>
										handleContextMenuSelect("node")
									}
									className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-white/5"
								>
									<GitBranch className="h-3.5 w-3.5 text-white/70" />
									Node
								</button>
								<button
									type="button"
									onClick={() =>
										handleContextMenuSelect("file")
									}
									className="mt-1 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-white/5"
								>
									<FileText className="h-3.5 w-3.5 text-white/70" />
									File
								</button>
							</div>
						)}
					</div>

					{contextItems.length === 0 ? (
						<p className="text-xs text-white/40">
							No context selected. Add nodes or documents to guide
							the copilot.
						</p>
					) : (
						contextItems.map((context) => {
							const isFile = context.type === "file";
							const IconComponent = isFile ? FileText : GitBranch;
							const cardAccent = isFile
								? "border-cyan-400/30 bg-cyan-500/5 text-cyan-100/80"
								: "border-emerald-400/30 bg-emerald-500/5 text-emerald-100/80";
							return (
								<div
									key={context.id}
									className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[10px] shadow-inner shadow-black/30 ${cardAccent}`}
								>
									<IconComponent className="h-3 w-3 flex-shrink-0 text-white/80" />
									<span className="max-w-[130px] truncate font-medium text-white/80">
										{context.label}
									</span>
									<button
										type="button"
										onClick={() =>
											handleRemoveContext(context.id)
										}
										className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full text-white/70 transition hover:text-white"
										aria-label={`Remove ${context.label}`}
									>
										<X className="h-3.5 w-3.5" />
									</button>
								</div>
							);
						})
					)}
				</div>

				<div className="relative">
					<textarea
						value={inputValue}
						onChange={(event) => setInputValue(event.target.value)}
						onKeyDown={handleKeyDown}
						placeholder={placeholder}
						rows={2}
						className="scrollbar w-full resize-none rounded-xl bg-transparent p-2.5 pr-12 text-sm text-white placeholder:text-white/30 focus:outline-none scrollbar-thin scrollbar-track-slate-900/60 scrollbar-thumb-cyan-500/40 hover:scrollbar-thumb-cyan-400/60"
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
