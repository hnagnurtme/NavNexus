import React, { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { motion } from "framer-motion";
import {
	FileText,
	BrainCircuit,
	Lightbulb,
	FlaskConical,
	GitMerge,
	HelpCircle,
} from "lucide-react";
import { EvidenceQuestionTooltip } from "../common/EvidenceQuestionTooltip";

export interface MindmapNodeData {
	id: string;
	name: string;
	type: string;
	level?: number;
	isGap?: boolean;
	hasChildren?: boolean;
	children?: MindmapNodeData[];
	evidence?: { sourceTitle: string; questionsRaised?: string[] }[];
	isPulsing?: boolean;
	isOnJourneyPath?: boolean;
	isCurrentJourneyNode?: boolean;
	isExpanded?: boolean;
	isSelected?: boolean;
	isHighlighted?: boolean;
	isLoading?: boolean;
	isDimmed?: boolean; // For dimming non-related nodes
	view?: "galaxy" | "query";
	onToggle?: (nodeId: string) => void;
	onSelect?: (nodeId: string) => void;
	onClearSelection?: () => void;
	childCount?: number; // Number of children for decision point visualization
	questionsRaised?: string[]; // Evidence questions for this node
}

const CustomNode: React.FC<NodeProps<MindmapNodeData>> = ({
	id,
	data,
	selected,
}) => {
	const [isHovered, setIsHovered] = useState(false);
	const [showEvidenceTooltip, setShowEvidenceTooltip] = useState(false);
	const [ripples, setRipples] = useState<Array<{ id: number; x: number; y: number }>>([]);
	
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
		isDimmed,
		onToggle,
		onSelect,
		onClearSelection,
		childCount = 0,
		questionsRaised,
	} = data;

	const isLeafNode = !children || children.length === 0;
	const isDecisionPoint = hasChildren && childCount > 1; // Decision point has multiple children

	const isMergedNode =
		evidence &&
		evidence.length > 1 &&
		new Set(evidence.map((e) => e.sourceTitle)).size > 1;
	
	// Collect all evidence questions
	const evidenceQuestions = evidence?.flatMap(e => e.questionsRaised || []) || [];
	const allQuestions = [...evidenceQuestions, ...(questionsRaised || [])];

	// Determine handle positions based on view
	// const isQueryView = view === "query";
	const targetPosition = Position.Left;
	const sourcePosition = Position.Right;

	const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
		// Create ripple effect
		const rect = e.currentTarget.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;
		const newRipple = { id: Date.now(), x, y };
		setRipples(prev => [...prev, newRipple]);
		
		// Remove ripple after animation
		setTimeout(() => {
			setRipples(prev => prev.filter(r => r.id !== newRipple.id));
		}, 600);
		
		if (onSelect) {
			onSelect(id);
		}

		if (view === "galaxy" && onToggle) {
			onToggle(id);
		}
	};

	const handleKeyDown: React.KeyboardEventHandler<HTMLButtonElement> = (
		event
	) => {
		if (event.key === "Enter") {
			event.preventDefault();
			onSelect?.(id);
			if (view === "galaxy") {
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
		<motion.div
			data-node-id={id}
			initial={false}
			animate={{
				scale: selected || isCurrentJourneyNode || isSelected ? 1.08 : 1,
				opacity: isDimmed ? 0.3 : 1,
				filter: isDimmed ? 'blur(2px)' : 'blur(0px)',
			}}
			whileHover={{ scale: isDimmed ? 1 : 1.02 }}
			transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
			onMouseEnter={() => !isDimmed && setIsHovered(true)}
			onMouseLeave={() => {
				setIsHovered(false);
				setShowEvidenceTooltip(false);
			}}
			className={`
        w-64 rounded-xl shadow-lg transition-all duration-300 ease-out relative overflow-hidden
        ${
			selected || isCurrentJourneyNode || isSelected
				? "border-2 border-green-400 shadow-[0_0_20px_rgba(74,222,128,0.6)]"
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
			<motion.div 
				className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none"
				initial={{ x: '-100%' }}
				animate={{ x: isHovered ? '100%' : '-100%' }}
				transition={{ duration: 0.7, ease: 'easeInOut' }}
			/>
			
			{/* Ripple effects */}
			{ripples.map(ripple => (
				<motion.span
					key={ripple.id}
					className="absolute rounded-full bg-white/30 pointer-events-none"
					style={{
						left: ripple.x,
						top: ripple.y,
						width: 0,
						height: 0,
					}}
					initial={{ width: 0, height: 0, opacity: 0.6 }}
					animate={{ width: 100, height: 100, opacity: 0 }}
					transition={{ duration: 0.6, ease: 'easeOut' }}
				/>
			))}

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
				<motion.div 
					className="absolute -top-2 -left-2 z-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full p-1.5 shadow-lg border-2 border-gray-900"
					animate={{ scale: [1, 1.1, 1] }}
					transition={{ duration: 1, repeat: Infinity, ease: 'easeInOut' }}
				>
					<span className="text-white text-xs font-bold">📍</span>
				</motion.div>
			)}
			
			{/* Evidence Question Indicator */}
			{allQuestions.length > 0 && (
				<>
					<motion.button
						type="button"
						className="absolute -top-2 -right-2 z-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full p-1.5 shadow-lg border-2 border-gray-900 cursor-pointer"
						whileHover={{ scale: 1.1 }}
						whileTap={{ scale: 0.95 }}
						onClick={(e) => {
							e.stopPropagation();
							setShowEvidenceTooltip(!showEvidenceTooltip);
						}}
						onMouseEnter={() => setShowEvidenceTooltip(true)}
						onMouseLeave={() => setShowEvidenceTooltip(false)}
					>
						<HelpCircle width={12} height={12} className="text-white" />
					</motion.button>
					
					<EvidenceQuestionTooltip
						questions={allQuestions}
						isVisible={showEvidenceTooltip}
						position="top"
					/>
				</>
			)}

			<button
				type="button"
				aria-label={`Knowledge node ${name}`}
				aria-pressed={isSelected || selected}
				aria-expanded={view === "galaxy" ? !!isExpanded : undefined}
				onClick={handleClick}
				onKeyDown={handleKeyDown}
				className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-green-400 rounded-xl relative"
			>
				<div className="flex items-center gap-3 p-3">
					<motion.div 
						whileHover={{ rotate: 12 }}
						transition={{ duration: 0.3 }}
					>
						{getNodeIcon()}
					</motion.div>
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
							<motion.span 
								className="h-2 w-2 rounded-full border-2 border-green-300 border-t-transparent"
								animate={{ rotate: 360 }}
								transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
							/>
						) : (
							<motion.span
								aria-hidden="true"
								className="text-lg leading-none inline-block"
								animate={{ rotate: isExpanded ? 180 : 0 }}
								transition={{ duration: 0.3, ease: 'easeInOut' }}
							>
								+
							</motion.span>
						)}
					</div>
				)}
			</button>

			<Handle
				type="source"
				position={sourcePosition}
				className="!bg-green-500/70 !w-3 !h-3 !border-2 !border-green-300/50 transition-all hover:!bg-green-400 hover:!scale-125"
			/>
		</motion.div>
	);
};

export default memo(CustomNode);
