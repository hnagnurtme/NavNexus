import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { FileText, BrainCircuit, Lightbulb, FlaskConical, GitMerge } from 'lucide-react';

export interface MindmapNodeData {
  id: string;
  name: string;
  type: string;
  isGap?: boolean;
  children?: MindmapNodeData[];
  evidence?: { sourceTitle: string }[];
  isPulsing?: boolean;
  isOnJourneyPath?: boolean;
  isCurrentJourneyNode?: boolean;
}

const CustomNode: React.FC<NodeProps<MindmapNodeData>> = ({ data, selected }) => {
  const { name, type, isGap, children, evidence, isPulsing, isOnJourneyPath, isCurrentJourneyNode } = data;

  const isLeafNode = !children || children.length === 0;

  const isMergedNode =
    evidence && evidence.length > 1 && new Set(evidence.map((e) => e.sourceTitle)).size > 1;

  const getNodeIcon = () => {
    if (isGap || isLeafNode) return <FlaskConical size={18} className="text-amber-400" />;
    if (type === 'document') return <FileText size={18} className="text-green-300" />;
    if (type === 'topic') return <BrainCircuit size={18} className="text-green-300" />;
    return <Lightbulb size={18} className="text-green-300" />;
  };

  return (
    <div
      className={`
        w-56 rounded-lg shadow-lg transition-all duration-300 relative
        ${selected || isCurrentJourneyNode ? 'border-2 border-green-400 scale-105' : isLeafNode ? 'border-2 border-amber-400' : 'border border-white/20'}
        ${isOnJourneyPath ? 'ring-2 ring-green-500/50' : ''}
        ${isGap || isLeafNode ? 'bg-gradient-to-br from-amber-800/50 to-black/70' : 'bg-gradient-to-br from-gray-800/50 to-black/70'}
        ${isPulsing ? 'animate-pulse ring-4 ring-cyan-400/50 scale-110' : ''}
        ${isCurrentJourneyNode ? 'shadow-2xl shadow-green-500/50 ring-4 ring-green-400/70' : ''}
        backdrop-blur-md
      `}
    >
      <Handle type="target" position={Position.Left} className="!bg-green-500/50 !w-2.5 !h-2.5" />

      {isMergedNode && (
        <div className="absolute -top-2 -right-2 z-10 bg-cyan-500 rounded-full p-1.5 shadow-lg border-2 border-gray-900">
          <GitMerge size={12} className="text-white" />
        </div>
      )}

      {isCurrentJourneyNode && (
        <div className="absolute -top-2 -left-2 z-10 bg-green-500 rounded-full p-1.5 shadow-lg border-2 border-gray-900 animate-pulse">
          <span className="text-white text-xs font-bold">📍</span>
        </div>
      )}

      <div className="flex items-center gap-3 p-3">
        {getNodeIcon()}
        <h3 className="font-semibold text-sm text-white/95 truncate">{name}</h3>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-green-500/50 !w-2.5 !h-2.5" />
    </div>
  );
};

export default memo(CustomNode);
