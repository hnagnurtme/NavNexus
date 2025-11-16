import React, { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import {
	FileText,
	BrainCircuit,
	Lightbulb,
	FlaskConical,
	GitMerge,
} from "lucide-react";

export interface MindmapNodeData {
	id: string;
	name: string;
	type: string;
	level?: number;
	isGap?: boolean;
	hasChildren?: boolean;
	children?: MindmapNodeData[];
	evidence?: { sourceTitle: string }[];
	isPulsing?: boolean;
	isOnJourneyPath?: boolean;
	isCurrentJourneyNode?: boolean;
	isExpanded?: boolean;
	isSelected?: boolean;
	isHighlighted?: boolean;
	isLoading?: boolean;
	view?: "galaxy" | "query";
	onToggle?: (nodeId: string) => void;
	onSelect?: (nodeId: string) => void;
	onClearSelection?: () => void;
	childCount?: number; // Number of children for decision point visualization
}

const CustomNode: React.FC<NodeProps<MindmapNodeData>> = ({
	id,
	data,
	selected,
}) => {
	const {
		name,
		type,
		isGap,
		children,
		evidence,
		isPulsing,
		isOnJourneyPath,
		isCurrentJourneyNode,
		view = "galaxy",
		hasChildren,
		isExpanded,
		isLoading,
		isSelected,
		isHighlighted,
		onToggle,
		onSelect,
		onClearSelection,
		childCount = 0,
	} = data;

	const isLeafNode = !children || children.length === 0;
	const isDecisionPoint = hasChildren && childCount > 1; // Decision point has multiple children

	const isMergedNode =
		evidence &&
		evidence.length > 1 &&
		new Set(evidence.map((e) => e.sourceTitle)).size > 1;

	// Determine handle positions based on view
	// const isQueryView = view === "query";
	const targetPosition = Position.Left;
	const sourcePosition = Position.Right;

	const handleClick = () => {
		if (onSelect) {
			onSelect(id);
		}

		if (view === "galaxy" && hasChildren) {
			if (onToggle) {
				onToggle(id);
			}
		}
	};

	const handleKeyDown: React.KeyboardEventHandler<HTMLButtonElement> = (
		event
	) => {
		if (event.key === "Enter") {
			event.preventDefault();
			onSelect?.(id);
			if (view === "galaxy" && hasChildren) {
				onToggle?.(id);
			}
		}
		if (event.key === "Escape") {
			event.preventDefault();
			onClearSelection?.();
		}
	};

	const getNodeIcon = () => {
		if (isGap || isLeafNode)
			return <FlaskConical width={18} height={18} className="text-amber-400" />;
		if (type === "document")
			return <FileText width={18} height={18} className="text-green-300" />;
		if (type === "topic")
			return <BrainCircuit width={18} height={18} className="text-green-300" />;
		return <Lightbulb width={18} height={18} className="text-green-300" />;
	};

	return (
		<div
			data-node-id={id}
			className={`
        w-64 rounded-xl shadow-lg transition-all duration-300 ease-out relative overflow-hidden
        hover:shadow-2xl hover:scale-102
        ${
			selected || isCurrentJourneyNode || isSelected
				? "border-2 border-green-400 scale-105 shadow-green-500/30"
				: isLeafNode
				? "border-2 border-amber-400 shadow-amber-500/20"
				: isDecisionPoint
				? "border-2 border-purple-400 shadow-purple-500/30"
				: "border border-white/20"
		}
        ${isOnJourneyPath ? "ring-2 ring-green-500/50" : ""}
        ${isHighlighted ? "ring-2 ring-cyan-400/80 animate-pulse" : ""}
        ${
			isGap || isLeafNode
				? "bg-gradient-to-br from-amber-800/60 via-amber-900/40 to-black/80"
				: isDecisionPoint
				? "bg-gradient-to-br from-purple-800/60 via-purple-900/40 to-black/80"
				: "bg-gradient-to-br from-emerald-800/50 via-gray-800/50 to-black/80"
		}
        ${isPulsing ? "animate-pulse ring-4 ring-cyan-400/50 scale-110" : ""}
        ${
			isCurrentJourneyNode
				? "shadow-2xl shadow-green-500/50 ring-4 ring-green-400/70"
				: ""
		}
        backdrop-blur-md
      `}
		>
			{/* Animated gradient overlay on hover */}
			<div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full transition-transform duration-700 hover:translate-x-full pointer-events-none" />

			<Handle
				type="target"
				position={targetPosition}
				className="!bg-green-500/70 !w-3 !h-3 !border-2 !border-green-300/50 transition-all hover:!bg-green-400 hover:!scale-125"
			/>

			{isMergedNode && (
				<div className="absolute -top-2 -right-2 z-10 bg-gradient-to-br from-cyan-400 to-cyan-600 rounded-full p-1.5 shadow-lg border-2 border-gray-900 animate-pulse">
					<GitMerge width={12} height={12} className="text-white" />
				</div>
			)}

			{isDecisionPoint && !isCurrentJourneyNode && (
				<div className="absolute -top-2 -left-2 z-10 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full p-1.5 shadow-lg border-2 border-gray-900">
					<span className="text-white text-xs font-bold">{childCount}</span>
				</div>
			)}

			{isCurrentJourneyNode && (
				<div className="absolute -top-2 -left-2 z-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full p-1.5 shadow-lg border-2 border-gray-900 animate-pulse">
					<span className="text-white text-xs font-bold">📍</span>
				</div>
			)}

			<button
				type="button"
				aria-label={`Knowledge node ${name}`}
				aria-pressed={isSelected || selected}
				aria-expanded={view === "galaxy" ? !!isExpanded : undefined}
				onClick={handleClick}
				onKeyDown={handleKeyDown}
				className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-green-400 rounded-xl transition-transform hover:scale-[1.02] active:scale-[0.98]"
			>
				<div className="flex items-center gap-3 p-3">
					<div className="transition-transform duration-300 hover:rotate-12">
						{getNodeIcon()}
					</div>
					<h3 className="font-semibold text-sm text-white/95 truncate flex-1">
						{name}
					</h3>
				</div>

				{view === "galaxy" && hasChildren && (
					<div className="px-3 pb-3 pt-0 flex items-center justify-between text-xs text-white/60 transition-colors hover:text-white/80">
						<span>
							{isExpanded ? "Collapse branch" : "Expand branch"}
						</span>
						{isLoading ? (
							<span className="h-2 w-2 animate-spin rounded-full border-2 border-green-300 border-t-transparent" />
						) : (
							<span
								aria-hidden="true"
								className="text-lg leading-none transition-transform duration-300"
								style={{ display: 'inline-block', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
							>
								+
							</span>
						)}
					</div>
				)}
			</button>

			<Handle
				type="source"
				position={sourcePosition}
				className="!bg-green-500/70 !w-3 !h-3 !border-2 !border-green-300/50 transition-all hover:!bg-green-400 hover:!scale-125"
			/>
		</div>
	);
};

export default memo(CustomNode);
