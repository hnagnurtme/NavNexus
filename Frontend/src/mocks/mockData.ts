import type { TreeRootResponse, NodeChildrenResponse, NodeDetailsResponse, TreeNodeShallow } from '@/types';

// Mock root node
const mockRoot: TreeNodeShallow = {
  id: 'root',
  name: 'Knowledge Base Root',
  type: 'topic',
  isGap: false,
  isCrossroads: false,
  hasChildren: true,
  parentId: null,
  level: 0,
};

// Mock level 1 children (documents/topics)
const mockLevel1Children: TreeNodeShallow[] = [
  {
    id: 'topic-sagsins',
    name: 'Vấn đề: Tối ưu Mạng SAGSINs',
    type: 'topic',
    isGap: false,
    isCrossroads: true,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
  {
    id: 'topic-rl-ppo',
    name: 'Lĩnh vực: Reinforcement Learning',
    type: 'topic',
    isGap: false,
    isCrossroads: true,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
  {
    id: 'topic-cv',
    name: 'Lĩnh vực: Computer Vision',
    type: 'topic',
    isGap: false,
    isCrossroads: false,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
  {
    id: 'topic-nlp',
    name: 'Lĩnh vực: Natural Language Processing',
    type: 'topic',
    isGap: true,
    isCrossroads: false,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
  {
    id: 'topic-network-infra',
    name: 'Lĩnh vực: Network Infrastructure',
    type: 'topic',
    isGap: false,
    isCrossroads: false,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
];

// Mock children data for different nodes
const mockChildrenMap: Record<string, TreeNodeShallow[]> = {
  'topic-sagsins': [
    {
      id: 'topic-latency',
      name: 'Tối ưu Độ trễ (Latency)',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: true,
      hasChildren: true,
      parentId: 'topic-sagsins',
      level: 2,
    },
    {
      id: 'topic-resource',
      name: 'Tối ưu Tài nguyên (Resource)',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'topic-sagsins',
      level: 2,
    },
  ],
  'topic-latency': [
    {
      id: 'sol-A',
      name: 'Giải pháp: Phương pháp A (Lập lịch)',
      type: 'algorithm',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'topic-latency',
      level: 3,
    },
    {
      id: 'sol-DQN',
      name: 'Giải pháp: DQN (Học Tăng Cường)',
      type: 'algorithm',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'topic-latency',
      level: 3,
    },
  ],
  'topic-rl-ppo': [
    {
      id: 'concept-ppo',
      name: 'Proximal Policy Optimization',
      type: 'concept',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'topic-rl-ppo',
      level: 2,
    },
    {
      id: 'concept-actor-critic',
      name: 'Actor-Critic Methods',
      type: 'concept',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'topic-rl-ppo',
      level: 2,
    },
  ],
};

// Mock node details
const mockDetailsMap: Record<string, NodeDetailsResponse> = {
  'topic-sagsins': {
    id: 'topic-sagsins',
    name: 'Vấn đề: Tối ưu Mạng SAGSINs',
    type: 'topic',
    synthesis: 'SAGSINs (Software-Defined Ground Segment for Satellite Networks) represents a paradigm shift in satellite network management. The optimization challenge focuses on reducing latency and improving resource allocation through intelligent scheduling and machine learning approaches.',
    evidence: [
      {
        id: 'ev-1',
        text: 'Software-defined networking enables dynamic resource allocation in satellite ground segments, reducing operational costs by up to 40%.',
        location: 'Page 12, Section 3.2',
        sourceTitle: 'Modern Satellite Network Architectures',
        sourceAuthor: 'Dr. Jane Smith',
        sourceYear: 2023,
        sourceUrl: 'https://example.com/paper1',
      },
      {
        id: 'ev-2',
        text: 'Machine learning-based scheduling algorithms can optimize satellite handover decisions, improving overall network performance.',
        location: 'Page 45, Abstract',
        sourceTitle: 'AI in Space Communications',
        sourceAuthor: 'Prof. John Doe',
        sourceYear: 2024,
        sourceUrl: 'https://example.com/paper2',
      },
    ],
    aiSuggestion: {
      isGap: false,
      isCrossroads: true,
      reason: 'Multiple approaches detected for optimizing SAGSINs: traditional scheduling methods and modern reinforcement learning techniques. Consider exploring both paths.',
      suggestedDocuments: [],
    },
  },
  'topic-nlp': {
    id: 'topic-nlp',
    name: 'Lĩnh vực: Natural Language Processing',
    type: 'topic',
    synthesis: 'Natural Language Processing is a critical area for understanding and processing human language. Current research focuses on transformer architectures and large language models.',
    evidence: [],
    aiSuggestion: {
      isGap: true,
      isCrossroads: false,
      reason: 'Limited evidence found for NLP techniques. Consider uploading more documents about transformers, BERT, or GPT architectures.',
      suggestedDocuments: [
        {
          title: 'Attention Is All You Need',
          reason: 'Foundational paper on transformer architecture',
          uploadUrl: 'https://example.com/upload/attention',
          previewUrl: 'https://arxiv.org/abs/1706.03762',
        },
        {
          title: 'BERT: Pre-training of Deep Bidirectional Transformers',
          reason: 'Key paper on bidirectional language understanding',
          uploadUrl: 'https://example.com/upload/bert',
          previewUrl: 'https://arxiv.org/abs/1810.04805',
        },
      ],
    },
  },
  'topic-latency': {
    id: 'topic-latency',
    name: 'Tối ưu Độ trễ (Latency)',
    type: 'problem-domain',
    synthesis: 'Latency optimization in satellite networks involves minimizing signal delay through intelligent routing and handover strategies.',
    evidence: [
      {
        id: 'ev-3',
        text: 'Predictive handover algorithms can reduce latency by 30% compared to reactive approaches.',
        location: 'Page 8, Results',
        sourceTitle: 'Satellite Handover Optimization',
        sourceAuthor: 'Dr. Maria Garcia',
        sourceYear: 2023,
        sourceUrl: 'https://example.com/paper3',
      },
    ],
    aiSuggestion: {
      isGap: false,
      isCrossroads: true,
      reason: 'Two distinct solution approaches identified: traditional scheduling and machine learning-based optimization.',
      suggestedDocuments: [],
    },
  },
};

// Mock API functions
export const mockTreeService = {
  getTreeRoot: async (_workspaceId: string): Promise<TreeRootResponse> => {
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
    return {
      root: mockRoot,
      children: mockLevel1Children,
    };
  },

  getNodeChildren: async (_workspaceId: string, nodeId: string): Promise<NodeChildrenResponse> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockChildrenMap[nodeId] || [];
  },

  getNodeDetails: async (_workspaceId: string, nodeId: string): Promise<NodeDetailsResponse> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    // Return mock details if available, otherwise generate basic details
    if (mockDetailsMap[nodeId]) {
      return mockDetailsMap[nodeId];
    }
    
    return {
      id: nodeId,
      name: 'Node Details',
      type: 'concept',
      synthesis: 'This is a placeholder synthesis for the selected node. In production, this would contain AI-generated summary of the node\'s content.',
      evidence: [],
      aiSuggestion: {
        isGap: false,
        isCrossroads: false,
        reason: '',
      },
    };
  },
};
