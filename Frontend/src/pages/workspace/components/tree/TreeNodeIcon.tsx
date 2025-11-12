import React from 'react';
import type { NodeType } from '@/types';
import { 
  FileText, 
  FolderOpen, 
  Code, 
  Lightbulb, 
  AlertTriangle, 
  GitBranch,
  Network,
  Target,
  Briefcase,
  CircleAlert,
  CheckCircle,
  ClipboardList,
  Bug,
  TrendingUp,
  Split
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface TreeNodeIconProps {
  type: NodeType;
  isGap?: boolean;
  isCrossroads?: boolean;
  className?: string;
}

const iconMap: Record<NodeType, React.ComponentType<{ className?: string }>> = {
  topic: FolderOpen,
  document: FileText,
  'problem-domain': Target,
  algorithm: Code,
  challenge: AlertTriangle,
  feature: Lightbulb,
  concept: Network,
  workspace: Briefcase,
  problem: CircleAlert,
  cause: AlertTriangle,
  solution: CheckCircle,
  requirement: ClipboardList,
  bug: Bug,
  improvement: TrendingUp,
  subproblem: Split,
};

export const TreeNodeIcon: React.FC<TreeNodeIconProps> = ({ 
  type, 
  isGap, 
  isCrossroads,
  className 
}) => {
  // Special icons for GAP and CROSSROADS
  if (isGap) {
    return (
      <AlertTriangle 
        className={cn(
          "w-5 h-5 text-orange-500 animate-pulse", 
          className
        )} 
      />
    );
  }
  
  if (isCrossroads) {
    return (
      <GitBranch 
        className={cn(
          "w-5 h-5 text-blue-500", 
          className
        )} 
      />
    );
  }
  
  // Default icon based on type
  const Icon = iconMap[type] || FileText;
  
  return (
    <Icon 
      className={cn(
        "w-5 h-5 text-gray-600 dark:text-gray-400", 
        className
      )} 
    />
  );
};
