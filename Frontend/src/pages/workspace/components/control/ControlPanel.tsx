import { useId, useRef, useState, useEffect, type ChangeEvent } from "react";
import {
	Bot,
	ChevronLeft,
	FileText,
	RotateCcw,
	Trash2,
	Upload,
	Link as LinkIcon,
	Plus,
	Loader,
	XCircle,
} from "lucide-react";
import { treeService } from "@/services/tree.service";
import { listenToJobStatus, type JobStatus } from "@/utils/firebase-listener";

interface ControlPanelProps {
	isBusy: boolean;
	onSynthesize: () => void;
	onReset: () => void;
	onToggleVisibility: () => void;
	workspaceId?: string; // Add workspaceId prop
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
	workspaceId,
}) => {
	const [uploadedItems, setUploadedItems] = useState<UploadedItem[]>([]);
	const [linkInput, setLinkInput] = useState("");
	const [showLinkInput, setShowLinkInput] = useState(false);
	const [activeTab, setActiveTab] = useState<"file" | "link">("file");
	const [isBuilding, setIsBuilding] = useState(false);
	const [buildStatus, setBuildStatus] = useState<JobStatus | null>(null);
	const [buildError, setbuildError] = useState<string | null>(null);
	
	const inputId = useId();
	const inputRef = useRef<HTMLInputElement | null>(null);
	const cleanupRef = useRef<(() => void) | null>(null);
	const hasItems = uploadedItems.length > 0;
	
	// Cleanup Firebase listener on unmount
	useEffect(() => {
		return () => {
			if (cleanupRef.current) {
				cleanupRef.current();
			}
		};
	}, []);

	/**
	 * Handle Build Knowledge Graph button click
	 * Implements the flow described in the issue:
	 * - Call POST /api/knowledge-tree
	 * - If status === "SUCCESS": fetch graph immediately
	 * - If status === "PENDING": show loading and listen to Firebase
	 */
	const handleBuildKnowledgeGraph = async () => {
		if (!workspaceId) {
			setbuildError("No workspace ID provided");
			return;
		}

		if (uploadedItems.length === 0) {
			setbuildError("No files or links uploaded");
			return;
		}

		try {
			setIsBuilding(true);
			setbuildError(null);
			setBuildStatus(null);

			// Prepare file paths from uploaded items
			const filePaths = uploadedItems.map((item) => {
				if (item.type === "file") {
					// For files, we'll need to upload them first
					// For now, using mock URLs
					return `https://storage.example.com/${item.name}`;
				} else {
					return item.url;
				}
			});

			// Call API to create knowledge tree
			console.log("🚀 Calling createKnowledgeTree API...");
			const response = await treeService.createKnowledgeTree({
				workspaceId: workspaceId,
				filePaths: filePaths,
			});

			console.log("📥 API Response:", response);

			// Extract status and messageId from response
			// Response structure: { success, message, data: { messageId, sentAt }, statusCode }
			const responseData = response.data;
			if (!responseData) {
				throw new Error("No data in API response");
			}
			
			const messageId = responseData.messageId;
			
			// Determine status based on response structure
			// Backend returns SUCCESS status when all files already exist
			// Backend returns PENDING status when files need processing
			// For now, we'll check if messageId exists to determine PENDING vs SUCCESS
			const isPending = !!messageId && messageId !== "IMMEDIATE";
			const status = isPending ? "PENDING" : "SUCCESS";

			if (status === "SUCCESS") {
				// ✅ Case 1: All files already exist
				// Fetch graph data immediately
				console.log("✅ SUCCESS status - fetching graph immediately");
				
				setIsBuilding(false);
				showSuccessToast("Knowledge graph ready!");
				
				// Trigger parent component to fetch and display graph
				onSynthesize();
				
			} else if (status === "PENDING") {
				// ⏳ Case 2: Processing new files
				// Show loading animation and register Firebase listener
				console.log("⏳ PENDING status - listening to Firebase for job:", messageId);
				
				if (!messageId) {
					throw new Error("No messageId returned from API");
				}

				// Register Firebase Realtime Database listener
				const cleanup = listenToJobStatus(messageId, (jobStatus) => {
					console.log("🔥 Firebase job status update:", jobStatus);
					
					setBuildStatus(jobStatus);

					if (jobStatus.status === "completed") {
						// Job completed successfully
						setIsBuilding(false);
						showSuccessToast("Knowledge graph built successfully!");
						
						// Trigger parent component to fetch and display graph
						onSynthesize();
						
					} else if (jobStatus.status === "failed") {
						// Job failed
						setIsBuilding(false);
						setbuildError(
							jobStatus.error || "Failed to build knowledge graph"
						);
						showErrorToast("Failed to build knowledge graph");
						
					} else if (jobStatus.status === "partial") {
						// Job partially completed
						setIsBuilding(false);
						showWarningToast(
							`Graph built with ${jobStatus.failed || 0} failures`
						);
						
						// Still trigger refresh to show partial results
						onSynthesize();
					}
				});

				// Store cleanup function
				cleanupRef.current = cleanup;
				
			} else {
				// Unknown status
				throw new Error(`Unknown status from API: ${status}`);
			}

		} catch (error) {
			console.error("❌ Error building knowledge graph:", error);
			setIsBuilding(false);
			setbuildError(
				error instanceof Error
					? error.message
					: "Unknown error occurred"
			);
			showErrorToast("Error building knowledge graph");
		}
	};

	// Toast notification helpers
	const showSuccessToast = (message: string) => {
		// TODO: Replace with actual toast library (e.g., react-hot-toast, sonner)
		console.log("✅ SUCCESS:", message);
		alert(message); // Temporary - replace with proper toast
	};

	const showErrorToast = (message: string) => {
		console.error("❌ ERROR:", message);
		alert(message); // Temporary - replace with proper toast
	};

	const showWarningToast = (message: string) => {
		console.warn("⚠️ WARNING:", message);
		alert(message); // Temporary - replace with proper toast
	};

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
		<aside className="relative flex  overflow-y-scroll w-96 flex-col rounded-3xl border border-white/10 bg-slate-900/70 p-6 text-white shadow-2xl backdrop-blur-xl">
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
					onClick={handleBuildKnowledgeGraph}
					disabled={isBuilding || isBusy || uploadedItems.length === 0}
					className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 py-3 text-sm font-semibold text-white shadow-lg transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
				>
					<Bot className={isBuilding || isBusy ? "animate-pulse" : ""} size={18} />
					{isBuilding ? "Building..." : isBusy ? "Synthesizing..." : "Build Knowledge Graph"}
				</button>
				<button
					type="button"
					onClick={onReset}
					disabled={isBuilding}
					className="flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 py-3 text-sm font-semibold text-white/70 transition enabled:hover:border-white/50 enabled:hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
				>
					<RotateCcw size={16} />
					Reset Workspace
				</button>
			</footer>

			{/* Loading Modal - Show when building knowledge graph */}
			{isBuilding && (
				<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
					<div className="mx-4 max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 text-center shadow-2xl">
						<Loader className="mx-auto mb-4 h-16 w-16 animate-spin text-emerald-400" />
						<h3 className="mb-2 text-xl font-semibold text-white">
							Building Knowledge Graph...
						</h3>
						<p className="mb-4 text-white/60">
							Processing your documents. This may take a few minutes.
						</p>
						
						{/* Show progress if available */}
						{buildStatus && buildStatus.totalFiles && (
							<div className="space-y-2">
								<div className="flex justify-between text-sm text-white/70">
									<span>Progress</span>
									<span>
										{buildStatus.successful || 0} / {buildStatus.totalFiles}
									</span>
								</div>
								<div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
									<div
										className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
										style={{
											width: `${((buildStatus.successful || 0) / buildStatus.totalFiles) * 100}%`,
										}}
									/>
								</div>
								{buildStatus.currentFile && (
									<p className="text-xs text-white/50">
										Processing file {buildStatus.currentFile} of{" "}
										{buildStatus.totalFiles}...
									</p>
								)}
							</div>
						)}
					</div>
				</div>
			)}

			{/* Error Display */}
			{buildError && (
				<div className="fixed bottom-4 right-4 z-50 max-w-sm rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 shadow-xl">
					<div className="flex items-start gap-3">
						<XCircle className="h-5 w-5 flex-shrink-0 text-rose-400" />
						<div className="flex-1">
							<p className="text-sm font-semibold text-rose-300">
								Build Failed
							</p>
							<p className="mt-1 text-xs text-rose-200/80">
								{buildError}
							</p>
						</div>
						<button
							onClick={() => setbuildError(null)}
							className="text-rose-300 hover:text-rose-100"
						>
							×
						</button>
					</div>
				</div>
			)}
		</aside>
	);
};
