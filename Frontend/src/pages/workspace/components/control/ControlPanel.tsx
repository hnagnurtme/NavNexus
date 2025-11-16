import { useId, useRef, useState, type ChangeEvent } from "react";
import {
	Bot,
	ChevronLeft,
	FileText,
	RotateCcw,
	Trash2,
	Upload,
	Link as LinkIcon,
	Plus,
} from "lucide-react";

interface ControlPanelProps {
	isBusy: boolean;
	onSynthesize: () => void;
	onReset: () => void;
	onToggleVisibility: () => void;
}

interface UploadedFile {
	id: string;
	name: string;
	type: "file";
}

interface UploadedLink {
	id: string;
	url: string;
	type: "link";
}

type UploadedItem = UploadedFile | UploadedLink;

export const ControlPanel: React.FC<ControlPanelProps> = ({
	isBusy,
	onSynthesize,
	onReset,
	onToggleVisibility,
}) => {
	const [uploadedItems, setUploadedItems] = useState<UploadedItem[]>([]);
	const [linkInput, setLinkInput] = useState("");
	const [showLinkInput, setShowLinkInput] = useState(false);
	const [activeTab, setActiveTab] = useState<"file" | "link">("file");
	const inputId = useId();
	const inputRef = useRef<HTMLInputElement | null>(null);
	const hasItems = uploadedItems.length > 0;

	const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
		const files = Array.from(event.target.files ?? []);
		if (files.length === 0) return;

		setUploadedItems((prev) => [
			...prev,
			...files.map((file) => ({
				id:
					typeof crypto !== "undefined" && "randomUUID" in crypto
						? crypto.randomUUID()
						: `${Date.now()}-${file.name}`,
				name: file.name,
				type: "file" as const,
			})),
		]);

		event.target.value = "";
	};

	const handleAddLink = () => {
		const trimmedLink = linkInput.trim();
		if (!trimmedLink) return;

		// Basic URL validation
		try {
			new URL(trimmedLink);
		} catch {
			alert("Please enter a valid URL (e.g., https://example.com)");
			return;
		}

		setUploadedItems((prev) => [
			...prev,
			{
				id:
					typeof crypto !== "undefined" && "randomUUID" in crypto
						? crypto.randomUUID()
						: `${Date.now()}-${trimmedLink}`,
				url: trimmedLink,
				type: "link" as const,
			},
		]);

		setLinkInput("");
		setShowLinkInput(false);
	};

	const removeItem = (itemId: string) => {
		setUploadedItems((prev) => prev.filter((item) => item.id !== itemId));
	};

	const openFilePicker = () => {
		inputRef.current?.click();
	};

	const getDisplayName = (item: UploadedItem) => {
		if (item.type === "file") return item.name;
		try {
			const url = new URL(item.url);
			return url.hostname + url.pathname;
		} catch {
			return item.url;
		}
	};

	return (
		<aside className="relative flex h-full w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-white shadow-2xl backdrop-blur-xl">
			<header className="mb-6 flex items-center justify-between">
				<div className="flex items-center gap-3">
					<Bot className="text-emerald-400" size={28} />
					<div>
						<p className="text-xs uppercase tracking-widest text-white/60">
							AI Controls
						</p>
						<h2 className="text-xl font-semibold text-white">
							Workspace Pilot
						</h2>
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
				{!hasItems ? (
					<div className="flex flex-1 flex-col gap-4">
						{/* Tab Selector */}
						<div className="flex gap-2 rounded-2xl border border-white/10 bg-white/5 p-1">
							<button
								type="button"
								onClick={() => setActiveTab("file")}
								className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
									activeTab === "file"
										? "bg-emerald-500/20 text-emerald-300"
										: "text-white/60 hover:text-white/80"
								}`}
							>
								<Upload size={16} />
								Files
							</button>
							<button
								type="button"
								onClick={() => setActiveTab("link")}
								className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
									activeTab === "link"
										? "bg-cyan-500/20 text-cyan-300"
										: "text-white/60 hover:text-white/80"
								}`}
							>
								<LinkIcon size={16} />
								Links
							</button>
						</div>

						{/* File Upload Area */}
						{activeTab === "file" && (
							<label
								htmlFor={inputId}
								className="group flex flex-1 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/20 bg-white/5 p-6 text-center transition hover:border-emerald-400/60 hover:bg-white/10"
							>
								<Upload
									size={28}
									className="mb-3 text-white/60 transition group-hover:text-emerald-300"
								/>
								<p className="text-sm text-white/70">
									Drop a research dossier or click to browse
								</p>
								<p className="mt-1 text-xs text-white/50">
									Supported: PDF, DOCX, TXT — max 10MB per
									batch
								</p>
							</label>
						)}

						{/* Link Input Area */}
						{activeTab === "link" && (
							<div className="flex flex-1 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/20 bg-white/5 p-6">
								<LinkIcon
									size={28}
									className="mb-3 text-cyan-300"
								/>
								<p className="text-sm text-white/70 mb-4">
									Add web pages or articles
								</p>
								<div className="w-full space-y-3">
									<input
										type="url"
										value={linkInput}
										onChange={(e) =>
											setLinkInput(e.target.value)
										}
										onKeyDown={(e) => {
											if (e.key === "Enter") {
												e.preventDefault();
												handleAddLink();
											}
										}}
										placeholder="https://example.com/article"
										className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:border-cyan-400/60 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
									/>
									<button
										type="button"
										onClick={handleAddLink}
										className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 py-3 text-sm font-semibold text-white transition hover:brightness-110"
									>
										<Plus size={16} />
										Add Link
									</button>
								</div>
								<p className="mt-3 text-xs text-white/50 text-center">
									We'll extract content from the URL
									automatically
								</p>
							</div>
						)}
					</div>
				) : (
					<div className="flex flex-1 flex-col gap-4">
						<div className="space-y-3 max-h-64 overflow-y-auto">
							{uploadedItems.map((item) => (
								<div
									key={item.id}
									className="flex items-center justify-between rounded-2xl border border-white/15 bg-white/5 px-4 py-3"
								>
									<div className="flex items-center gap-3 flex-1 min-w-0">
										<div
											className={`rounded-full p-2 ${
												item.type === "file"
													? "bg-emerald-500/10 text-emerald-300"
													: "bg-cyan-500/10 text-cyan-300"
											}`}
										>
											{item.type === "file" ? (
												<FileText size={18} />
											) : (
												<LinkIcon size={18} />
											)}
										</div>
										<div className="flex-1 min-w-0">
											<p
												className="text-sm font-semibold text-white truncate"
												title={getDisplayName(item)}
											>
												{getDisplayName(item)}
											</p>
											<p className="text-xs text-white/50">
												{item.type === "file"
													? "Ready for synthesis"
													: "Web content"}
											</p>
										</div>
									</div>
									<button
										type="button"
										onClick={() => removeItem(item.id)}
										className="rounded-full border border-white/20 p-2 text-white/60 transition hover:border-rose-400/60 hover:text-rose-300 flex-shrink-0"
										aria-label={`Remove ${getDisplayName(
											item
										)}`}
									>
										<Trash2 size={16} />
									</button>
								</div>
							))}
						</div>
						<div className="flex gap-2">
							<button
								type="button"
								onClick={openFilePicker}
								className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-dashed border-white/20 px-4 py-3 text-sm font-semibold text-white/80 transition hover:border-emerald-400/60 hover:text-white"
							>
								<Upload size={16} />
								Add File
							</button>
							<button
								type="button"
								onClick={() => setShowLinkInput(!showLinkInput)}
								className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-dashed border-white/20 px-4 py-3 text-sm font-semibold text-white/80 transition hover:border-cyan-400/60 hover:text-white"
							>
								<LinkIcon size={16} />
								Add Link
							</button>
						</div>
						{showLinkInput && (
							<div className="space-y-2 rounded-2xl border border-cyan-400/30 bg-cyan-500/5 p-4">
								<input
									type="url"
									value={linkInput}
									onChange={(e) =>
										setLinkInput(e.target.value)
									}
									onKeyDown={(e) => {
										if (e.key === "Enter") {
											e.preventDefault();
											handleAddLink();
										}
									}}
									placeholder="https://example.com/article"
									autoFocus
									className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm text-white placeholder:text-white/40 focus:border-cyan-400/60 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
								/>
								<div className="flex gap-2">
									<button
										type="button"
										onClick={handleAddLink}
										className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-cyan-500 py-2 text-sm font-semibold text-white transition hover:brightness-110"
									>
										Add
									</button>
									<button
										type="button"
										onClick={() => {
											setShowLinkInput(false);
											setLinkInput("");
										}}
										className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white/70 transition hover:text-white"
									>
										Cancel
									</button>
								</div>
							</div>
						)}
					</div>
				)}
				<input
					id={inputId}
					type="file"
					className="sr-only"
					ref={inputRef}
					onChange={handleFileSelect}
					multiple
				/>

				<div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
					<p className="font-semibold text-white">How it works</p>
					<ul className="mt-3 space-y-2 text-xs leading-relaxed text-white/60">
						<li>
							1. Upload files or paste URLs; we auto-extract
							concepts + evidence.
						</li>
						<li>
							2. The AI integrity engine merges multilingual
							terms.
						</li>
						<li>
							3. A knowledge journey becomes available for deep
							dives.
						</li>
					</ul>
				</div>
			</section>

			<footer className="mt-6 space-y-3">
				<button
					type="button"
					onClick={onSynthesize}
					disabled={isBusy || uploadedItems.length === 0}
					className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 py-3 text-sm font-semibold text-white shadow-lg transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
				>
					<Bot className={isBusy ? "animate-pulse" : ""} size={18} />
					{isBusy ? "Synthesizing..." : "Build Knowledge Graph"}
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
