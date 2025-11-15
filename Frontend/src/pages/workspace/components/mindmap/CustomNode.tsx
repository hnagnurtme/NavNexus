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
	} = data;

	const isLeafNode = !children || children.length === 0;

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
        w-64 rounded-lg shadow-lg transition-all duration-300 relative
        ${
			selected || isCurrentJourneyNode || isSelected
				? "border-2 border-green-400 scale-105"
				: isLeafNode
				? "border-2 border-amber-400"
				: "border border-white/20"
		}
        ${isOnJourneyPath ? "ring-2 ring-green-500/50" : ""}
        ${isHighlighted ? "ring-2 ring-cyan-400/80" : ""}
        ${
			isGap || isLeafNode
				? "bg-gradient-to-br from-amber-800/50 to-black/70"
				: "bg-gradient-to-br from-gray-800/50 to-black/70"
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
			<Handle
				type="target"
				position={targetPosition}
				className="!bg-green-500/50 !w-2.5 !h-2.5"
			/>

			{isMergedNode && (
				<div className="absolute -top-2 -right-2 z-10 bg-cyan-500 rounded-full p-1.5 shadow-lg border-2 border-gray-900">
					<GitMerge width={12} height={12} className="text-white" />
				</div>
			)}

			{isCurrentJourneyNode && (
				<div className="absolute -top-2 -left-2 z-10 bg-green-500 rounded-full p-1.5 shadow-lg border-2 border-gray-900 animate-pulse">
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
				className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-green-400 rounded-lg"
			>
				<div className="flex items-center gap-3 p-3">
					{getNodeIcon()}
					<h3 className="font-semibold text-sm text-white/95 truncate flex-1">
						{name}
					</h3>
				</div>

				{view === "galaxy" && hasChildren && (
					<div className="px-3 pb-3 pt-0 flex items-center justify-between text-xs text-white/60">
						<span>
							{isExpanded ? "Collapse branch" : "Expand branch"}
						</span>
						{isLoading ? (
							<span className="h-2 w-2 animate-pulse rounded-full bg-green-300" />
						) : (
							<span
								aria-hidden="true"
								className="text-lg leading-none"
							>
								{isExpanded ? "−" : "+"}
							</span>
						)}
					</div>
				)}
			</button>

			<Handle
				type="source"
				position={sourcePosition}
				className="!bg-green-500/50 !w-2.5 !h-2.5"
			/>
		</div>
	);
};

export default memo(CustomNode);
