import { useEffect, useMemo, useRef, useState } from "react";
import {
	ChevronRight,
	FileText,
	GitBranch,
	Loader2,
	Plus,
	Send,
	X,
} from "lucide-react";
import {
	DEFAULT_NODE_CONTEXT_ID,
	type ContextItem,
	type ContextType,
	type ContextSuggestion,
	buildDefaultContexts,
} from "./contextUtils";
import { type ChatMessage, buildInitialMessage } from "./chatTypes";
import { chatbotService } from "@/services/chatbot.service";
import {
	type ChatbotContextItemPayload,
	type ChatbotMessageHistoryItem,
} from "@/types";

interface ChatbotPanelProps {
	topicId?: string | null;
	topicName?: string | null;
	summary?: string | null;
	evidenceSources?: string[];
	nodeSuggestions?: ContextSuggestion[];
	fileSuggestions?: ContextSuggestion[];
}

export const ChatbotPanel: React.FC<ChatbotPanelProps> = ({
	topicId,
	topicName,
	summary,
	evidenceSources,
	nodeSuggestions = [],
	fileSuggestions = [],
}) => {
	const [messages, setMessages] = useState<ChatMessage[]>(() => [
		buildInitialMessage(topicName, summary),
	]);
	const [inputValue, setInputValue] = useState("");
	const [isThinking, setIsThinking] = useState(false);
	const [errorMessage, setErrorMessage] = useState<string | null>(null);
	const [contextItems, setContextItems] = useState<ContextItem[]>(() =>
		buildDefaultContexts(topicName, evidenceSources, topicId)
	);
	const scrollAnchorRef = useRef<HTMLDivElement | null>(null);
	const [isContextMenuOpen, setIsContextMenuOpen] = useState(false);
	const [contextMenuType, setContextMenuType] = useState<ContextType | null>(
		null
	);

	useEffect(() => {
		scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages, isThinking]);

	useEffect(() => {
		if (!isContextMenuOpen) {
			setContextMenuType(null);
		}
	}, [isContextMenuOpen]);

	const placeholder = useMemo(
		() => `Ask about ${topicName ?? "this topic"}...`,
		[topicName]
	);

	const contextPayload = useMemo<ChatbotContextItemPayload[]>(
		() =>
			contextItems.map((item) => ({
				id: item.entityId ?? item.id,
				entityId: item.entityId,
				type: item.type,
				label: item.label,
			})),
		[contextItems]
	);

	const buildHistoryPayload = (
		history: ChatMessage[]
	): ChatbotMessageHistoryItem[] =>
		history.map((message) => ({
			role: message.role,
			content: message.content,
			timestamp: message.timestamp,
			nodeSnapshot: message.nodeSnapshot ?? null,
			sourceSnapshot: message.sourceSnapshot ?? null,
			source: message.source ?? null,
		}));

	const sendPrompt = async (prompt: string, history: ChatMessage[]) => {
		setIsThinking(true);
		setErrorMessage(null);
		try {
			const payload = {
				prompt,
				topicId: topicId ?? undefined,
				contexts: contextPayload,
				history: buildHistoryPayload(history),
			};
			const response = await chatbotService.query(payload);
			console.log("Your message payload:", payload);
			console.log("Chatbot response:", response);
			const aiMessage = response.data.message;
			const timestamp = Date.now();
			const normalizedMessage: ChatMessage = {
				id: aiMessage.id ?? `ai-${timestamp}`,
				role: "ai",
				content: aiMessage.content,
				source: aiMessage.source ?? undefined,
				timestamp,
				nodeSnapshot: aiMessage.nodeSnapshot ?? null,
				sourceSnapshot: aiMessage.sourceSnapshot ?? null,
			};
			setMessages((prev) => [...prev, normalizedMessage]);
		} catch (error) {
			console.error("Failed to query chatbot", error);
			setErrorMessage(
				"The chatbot is unavailable right now. Please try again."
			);
		} finally {
			setIsThinking(false);
		}
	};

	const handleSend = () => {
		const trimmed = inputValue.trim();
		if (!trimmed || isThinking) return;

		const now = Date.now();
		const outboundMessage: ChatMessage = {
			id: `user-${now}`,
			role: "user",
			content: trimmed,
			timestamp: now,
		};

		setMessages((prev) => [...prev, outboundMessage]);
		setInputValue("");
		void sendPrompt(trimmed, [...messages, outboundMessage]);
	};

	const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (
		event
	) => {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			handleSend();
		}
	};

	const handleAddContext = (
		type: ContextType,
		presetLabel?: string,
		presetEntityId?: string
	) => {
		if (typeof window === "undefined") return;
		let resolvedLabel = presetLabel;
		if (!resolvedLabel) {
			const promptLabel =
				type === "node"
					? "Enter a node or concept to prioritize"
					: "Enter a document or evidence source";
			const defaultValue =
				type === "node"
					? topicName ?? "Untitled node"
					: "Untitled file";
			const value = window.prompt(promptLabel, defaultValue);
			if (!value) return;
			resolvedLabel = value.trim();
		}
		if (!resolvedLabel) return;
		const exists = contextItems.some((item) => {
			if (item.type !== type) return false;
			if (presetEntityId && item.entityId) {
				return item.entityId === presetEntityId;
			}
			return (
				item.label.toLowerCase() === resolvedLabel!.toLowerCase()
			);
		});
		if (exists) return;
		setContextItems((prev) => [
			...prev,
			{
				id: `${type}-${Date.now()}`,
				type,
				label: resolvedLabel!,
				entityId: presetEntityId,
			},
		]);
	};

	const handleRemoveContext = (contextId: string) => {
		setContextItems((prev) =>
			prev.filter((context) => context.id !== contextId)
		);
	};

	const handleContextMenuSelect = (
		type: ContextType,
		option: ContextSuggestion
	) => {
		setIsContextMenuOpen(false);
		handleAddContext(
			type,
			option.label,
			option.entityId ?? option.id ?? undefined
		);
	};

	useEffect(() => {
		setContextItems((prev) => {
			const remaining = prev.filter(
				(item) => item.id !== DEFAULT_NODE_CONTEXT_ID
			);
			if (!topicName) {
				return remaining;
			}
			return [
				{
					id: DEFAULT_NODE_CONTEXT_ID,
					type: "node",
					label: topicName,
					entityId: topicId ?? undefined,
				},
				...remaining,
			];
		});
	}, [topicId, topicName]);

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
							<div className="absolute bottom-8 left-0 z-10 mb-2 rounded-xl border border-white/10 bg-slate-900/95 p-1 text-white shadow-xl">
								<div className="w-28">
									{[
										{
											type: "node" as ContextType,
											label: "Node",
											icon: GitBranch,
										},
										{
											type: "file" as ContextType,
											label: "File",
											icon: FileText,
										},
									].map((entry) => {
										const Icon = entry.icon;
										const isActive =
											contextMenuType === entry.type;
										return (
											<button
												type="button"
												key={entry.type}
												onMouseEnter={() =>
													setContextMenuType(
														entry.type
													)
												}
												className={`flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left ${
													isActive
														? "bg-white/10 text-white"
														: "hover:bg-white/5"
												}`}
											>
												<span className="flex items-center gap-2">
													<Icon className="h-3.5 w-3.5 text-white/70" />
													{entry.label}
												</span>
												<ChevronRight className="h-3 w-3 text-white/60" />
											</button>
										);
									})}
								</div>
								{contextMenuType && (
									<div
										data-submenu
										className="absolute top-0 left-full ml-2 w-40 rounded-xl border border-white/10 bg-slate-900/95 p-2 shadow-inner shadow-black/40"
									>
										<div className="scrollbar max-h-48 space-y-1 overflow-y-auto pr-1 text-[11px] text-white/80 scrollbar-thin scrollbar-track-slate-900/60 scrollbar-thumb-cyan-500/40 hover:scrollbar-thumb-cyan-400/60">
											{(contextMenuType === "node"
												? nodeSuggestions
												: fileSuggestions
											).length === 0 ? (
												<p className="text-[10px] text-white/40">
													No entries
												</p>
											) : (
												(contextMenuType === "node"
													? nodeSuggestions
													: fileSuggestions
												).map((option) => (
													<button
														type="button"
															key={`${contextMenuType}-${option.id}`}
															onClick={() =>
																handleContextMenuSelect(
																	contextMenuType,
																	option
																)
															}
														className="flex w-full items-center justify-between rounded-lg px-2 py-1 text-left hover:bg-white/5"
													>
														<span className="max-w-[150px] truncate font-medium">
															{option.label}
														</span>
														<Plus className="h-3 w-3 text-white/60" />
													</button>
												))
											)}
										</div>
									</div>
								)}
							</div>
						)}
					</div>

					{contextItems.length === 0 ? (
						<p className="text-xs text-white/20">
							Add context to guide the chatbot
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
				{errorMessage && (
					<p className="mt-2 text-xs text-red-400">{errorMessage}</p>
				)}
			</div>
		</div>
	);
};
