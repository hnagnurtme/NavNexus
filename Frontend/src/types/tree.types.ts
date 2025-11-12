export type NodeType = 
  | 'topic' 
  | 'document' 
  | 'problem-domain' 
  | 'algorithm' 
  | 'challenge' 
  | 'feature' 
  | 'concept'
  | 'workspace'
  |  'problem'
  | 'cause'
    | 'solution'
    | 'requirement'
    | 'bug'
    | 'improvement'
    | 'subproblem'
  ;

export interface TreeNodeShallow {
  id: string;
  name: string;
  type: NodeType;
  isGap: boolean;
  isCrossroads: boolean;
  hasChildren: boolean;
  parentId: string | null;
  level: number;
}

export interface TreeNodeUI extends TreeNodeShallow {
  children?: TreeNodeUI[];
  isExpanded: boolean;
  isVisited?: boolean;
  isBookmarked?: boolean;
}

export interface TreeRootResponse {
  root: TreeNodeShallow;
  children: TreeNodeShallow[];
}

export type NodeChildrenResponse = TreeNodeShallow[];
