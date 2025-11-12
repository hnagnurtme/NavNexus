import type { TreeRootResponse, NodeChildrenResponse, NodeDetailsResponse, TreeNodeShallow } from '@/types';

// ===========================================
// 0. ROOT NODE
// ===========================================
const mockRoot: TreeNodeShallow = {
  id: 'root',
  name: 'NAVER K-Graph: Hackathon Demo',
  type: 'workspace',
  isGap: false,
  isCrossroads: false,
  hasChildren: true,
  parentId: null,
  level: 0,
};

// ===========================================
// 1. LEVEL 1 – Sau khi upload 3 file (SAGSINs.pdf, PPO.pdf, RL2.pdf)
// ===========================================
const level1Chaos: TreeNodeShallow[] = [
  {
    id: 'domain-sagsins',
    name: 'Vấn đề: Tối ưu Mạng SAGINs (6G Satellite-Air-Ground Integrated Networks)',
    type: 'problem-domain',
    isGap: true,
    isCrossroads: false,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
  {
    id: 'tool-ppo',
    name: 'Công cụ: Proximal Policy Optimization (PPO)',
    type: 'algorithm',
    isGap: false,
    isCrossroads: false,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
  {
    id: 'overview-rl-networking',
    name: 'Tổng quan: RL trong Networking (hụt)',
    type: 'problem-domain',
    isGap: true,
    isCrossroads: false,
    hasChildren: true,
    parentId: 'root',
    level: 1,
  },
];

// ===========================================
// 2. CHILDREN MAP – CÂY SIÊU SÂU (7 tầng)
// ===========================================
const mockChildrenMap: Record<string, TreeNodeShallow[]> = {
  // === DOMAIN: SAGINs ===
  'domain-sagsins': [
    {
      id: 'problem-resource',
      name: 'Resource Allocation in SAGIN',
      type: 'problem',
      isGap: true,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'domain-sagsins',
      level: 2,
    },
    {
      id: 'problem-latency',
      name: 'Latency Optimization',
      type: 'problem',
      isGap: true,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'domain-sagsins',
      level: 2,
    },
    {
      id: 'problem-handover',
      name: 'Satellite Handover Management',
      type: 'problem',
      isGap: true,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'domain-sagsins',
      level: 2,
    },
  ],

  // --- Resource Allocation (ngõ cụt ban đầu) ---
  'problem-resource': [
    {
      id: 'sub-resource-compute',
      name: 'Computing Resource Allocation',
      type: 'sub-problem',
      isGap: true,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'problem-resource',
      level: 3,
    },
    {
      id: 'sub-resource-bandwidth',
      name: 'Bandwidth & Subcarrier Allocation',
      type: 'sub-problem',
      isGap: true,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'problem-resource',
      level: 3,
    },
  ],

  // --- Latency Optimization ---
  'problem-latency': [
    {
      id: 'cause-propagation',
      name: 'Propagation Delay (LEO/GEO)',
      type: 'cause',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'problem-latency',
      level: 3,
    },
    {
      id: 'cause-processing',
      name: 'On-board Processing Delay',
      type: 'cause',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'problem-latency',
      level: 3,
    },
  ],

  'cause-propagation': [
    {
      id: 'mitigation-predictive',
      name: 'Predictive Handover',
      type: 'problem-domain',
      isGap: true,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'cause-propagation',
      level: 4,
    },
  ],

  // === TOOL: PPO ===
  'tool-ppo': [
    {
      id: 'concept-ppo-clip',
      name: 'Clipped Surrogate Objective',
      type: 'concept',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'tool-ppo',
      level: 2,
    },
    {
      id: 'application-ppo-atari',
      name: 'PPO on Atari & Robotics',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'tool-ppo',
      level: 2,
    },
  ],

  'concept-ppo-clip': [
    {
      id: 'math-ppo-objective',
      name: 'PPO Loss Function',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'concept-ppo-clip',
      level: 3,
    },
  ],

  // === RL in Networking (hụt) ===
  'overview-rl-networking': [
    {
      id: 'rl-network-general',
      name: 'RL for General Networking',
      type: 'concept',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'overview-rl-networking',
      level: 2,
    },
    {
      id: 'rl-sagin-missing',
      name: 'RL in SAGIN (Không có giải pháp cụ thể)',
      type: 'problem-domain',
      isGap: true,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'overview-rl-networking',
      level: 2,
    },
  ],

  'rl-network-general': [
    {
      id: 'rl-routing',
      name: 'Routing Optimization',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'rl-network-general',
      level: 3,
    },
  ],

  // ========================================
  // SAU KHI UPLOAD GAP.pdf & ALT-OPT.pdf
  // → TẠO NHÁNH MỚI DƯỚI problem-resource
  // ========================================
  // NOTE: 'problem-resource' is already defined above and will be
  // dynamically updated in getNodeChildren() instead

  // Nhánh 1: GAP.pdf → AI/DRL
  'solution-ppo-sagin': [
    {
      id: 'impl-attention-ppo',
      name: 'Attention-Enabled PPO',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: true,
      hasChildren: true,
      parentId: 'solution-ppo-sagin',
      level: 4,
    },
    {
      id: 'eval-gap-results',
      name: 'Simulation Results (vs DDPG)',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'solution-ppo-sagin',
      level: 4,
    },
  ],

  'impl-attention-ppo': [
    {
      id: 'arch-attention-layer',
      name: 'Multi-Head Attention in Policy Network',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'impl-attention-ppo',
      level: 5,
    },
  ],

  'arch-attention-layer': [
    {
      id: 'code-attention-snippet',
      name: 'Code: Attention Module (PyTorch)',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'arch-attention-layer',
      level: 6,
    },
  ],

  'eval-gap-results': [
    {
      id: 'metric-convergence',
      name: 'Convergence Speed',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'eval-gap-results',
      level: 5,
    },
    {
      id: 'metric-throughput',
      name: 'System Throughput',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'eval-gap-results',
      level: 5,
    },
  ],

  // Nhánh 2: ALT-OPT.pdf → Toán học
  'solution-alt-opt': [
    {
      id: 'method-alternating',
      name: 'Alternating Optimization Framework',
      type: 'problem-domain',
      isGap: false,
      isCrossroads: false,
      hasChildren: true,
      parentId: 'solution-alt-opt',
      level: 4,
    },
  ],

  'method-alternating': [
    {
      id: 'subproblem-1',
      name: 'Subproblem 1: User Association',
      type: 'subproblem',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'method-alternating',
      level: 5,
    },
    {
      id: 'subproblem-2',
      name: 'Subproblem 2: Computation Offloading',
      type: 'subproblem',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'method-alternating',
      level: 5,
    },
    {
      id: 'subproblem-3',
      name: 'Subproblem 3: Power Control',
      type: 'subproblem',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'method-alternating',
      level: 5,
    },
    {
      id: 'subproblem-4',
      name: 'Subproblem 4: Subcarrier Allocation',
      type: 'subproblem',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'method-alternating',
      level: 5,
    },
    {
      id: 'subproblem-5',
      name: 'Subproblem 5: Computing Resource',
      type: 'subproblem',
      isGap: false,
      isCrossroads: false,
      hasChildren: false,
      parentId: 'method-alternating',
      level: 5,
    },
  ],
};

// ===========================================
// 3. DETAILS MAP – SIÊU CHI TIẾT
// ===========================================
const mockDetailsMap: Record<string, NodeDetailsResponse> = {
  // === NGÕ CỤT: Resource Allocation (trước upload) ===
  'problem-resource': {
    id: 'problem-resource',
    name: 'Resource Allocation in SAGIN',
    type: 'problem',
    synthesis:
      'Phân bổ tài nguyên trong mạng SAGIN là bài toán đa chiều với topology động, tài nguyên không đồng nhất và độ trễ cao. Hiện tại chỉ có mô tả vấn đề, chưa có giải pháp cụ thể.',
    evidence: [
      {
        id: 'ev-sagsins-1',
        text: 'Resource allocation in SAGINs is highly complex due to dynamic topology and heterogeneous resources.',
        location: 'Page 3, Section 2.1',
        sourceTitle: 'SAGSINs.pdf',
        sourceAuthor: 'Nguyen et al.',
        sourceYear: 2024,
        sourceUrl: '/files/SAGSINs.pdf',
      },
      {
        id: 'ev-rl2-1',
        text: 'AI-based methods are promising but lack specific algorithm implementation for SAGIN.',
        location: 'Page 7, Conclusion',
        sourceTitle: 'RL2.pdf',
        sourceAuthor: 'Kim et al.',
        sourceYear: 2023,
        sourceUrl: '/files/RL2.pdf',
      },
    ],
    aiSuggestion: {
      isGap: true,
      isCrossroads: false,
      reason:
        'Node này là "ngõ cụt". Thiếu tài liệu kết nối vấn đề với giải pháp. Gợi ý 2 hướng tiếp cận:',
      suggestedDocuments: [
        {
          title: 'Graphic Deep Reinforcement Learning for Resource Allocation in SAGIN',
          reason: 'Dùng Attention-enabled PPO để tối ưu động',
          uploadUrl: '/upload/GAP.pdf',
          previewUrl: 'https://arxiv.org/abs/2401.12345',
        },
        {
          title: 'Joint Computation Offloading and Resource Allocation in SAGIN',
          reason: 'Dùng Alternating Optimization (5 sub-problems)',
          uploadUrl: '/upload/ALT-OPT.pdf',
          previewUrl: 'https://ieeexplore.ieee.org/document/9876543',
        },
      ],
    },
  },

  // === NHÁNH AI/DRL: Attention-Enabled PPO ===
  'solution-ppo-sagin': {
    id: 'solution-ppo-sagin',
    name: 'Giải pháp: Attention-enabled PPO',
    type: 'algorithm',
    synthesis:
      'Kết hợp PPO với Attention để xử lý không gian trạng thái lớn trong SAGIN. Mô hình học được chính sách tối ưu theo thời gian thực.',
    evidence: [
      {
        id: 'ev-gap-1',
        text: '...an attention-enabled proximal policy optimization (PPO) method is used to jointly optimize computation offloading and resource allocation.',
        location: 'Page 5, Section IV',
        sourceTitle: 'GAP.pdf',
        sourceAuthor: 'Tran et al.',
        sourceYear: 2024,
        sourceUrl: '/files/GAP.pdf',
      },
    ],
    aiSuggestion: {
      isGap: false,
      isCrossroads: true,
      reason: 'Bước tiếp: Tìm hiểu Attention Mechanism hoặc so sánh với DDPG.',
      suggestedDocuments: [
        {
          title: 'DDPG for Continuous Control in Networking',
          reason: 'So sánh PPO vs DDPG',
          uploadUrl: '/upload/DDPG.pdf',
          previewUrl: 'https://arxiv.org/abs/2205.67890',
        },
      ],
    },
  },

  // === NHÁNH TOÁN HỌC: Alternating Optimization ===
  'solution-alt-opt': {
    id: 'solution-alt-opt',
    name: 'Giải pháp: Alternating Optimization',
    type: 'algorithm',
    synthesis:
      'Chia bài toán thành 5 sub-problem và giải tuần tự. Ổn định, dễ triển khai, phù hợp hệ thống có ràng buộc chặt.',
    evidence: [
      {
        id: 'ev-alt-1',
        text: '...we use the alternating optimization approach where we iteratively solve five sub-problems...',
        location: 'Page 4, Section III',
        sourceTitle: 'ALT-OPT.pdf',
        sourceAuthor: 'Li et al.',
        sourceYear: 2023,
        sourceUrl: '/files/ALT-OPT.pdf',
      },
    ],
    aiSuggestion: {
      isGap: false,
      isCrossroads: false,
      reason: 'Phương pháp ổn định. Có thể lai với RL để cải thiện tốc độ hội tụ.',
      suggestedDocuments: [],
    },
  },
};

// ===========================================
// 4. MOCK TREE SERVICE – SIÊU THÔNG MINH
// ===========================================
export const mockTreeService = {
  getTreeRoot: async (): Promise<TreeRootResponse> => {
    await delay(800);
    return { root: mockRoot, children: level1Chaos };
  },

  getNodeChildren: async (_w: string, nodeId: string): Promise<NodeChildrenResponse> => {
    await delay(400);

    // DYNAMIC UPDATE: Khi upload xong → thêm nhánh
    if (nodeId === 'problem-resource') {
      const hasGAP = localStorage.getItem('uploaded_GAP.pdf');
      const hasALT = localStorage.getItem('uploaded_ALT-OPT.pdf');

      if (hasGAP && hasALT) {
        return [
          {
            id: 'solution-ppo-sagin',
            name: 'Hướng AI/DRL: Attention-enabled PPO',
            type: 'solution-path',
            isGap: false,
            isCrossroads: false,
            hasChildren: true,
            parentId: 'problem-resource',
            level: 3,
          },
          {
            id: 'solution-alt-opt',
            name: 'Hướng Toán học: Alternating Optimization',
            type: 'solution-path',
            isGap: false,
            isCrossroads: false,
            hasChildren: true,
            parentId: 'problem-resource',
            level: 3,
          },
        ];
      } else {
        return mockChildrenMap['problem-resource']?.filter(n => n.level === 3) || [];
      }
    }

    return mockChildrenMap[nodeId] || [];
  },

  getNodeDetails: async (_w: string, nodeId: string): Promise<NodeDetailsResponse> => {
    await delay(700);

    // CROSSROADS DETECTION
    if (nodeId === 'problem-resource') {
      const hasGAP = localStorage.getItem('uploaded_GAP.pdf');
      const hasALT = localStorage.getItem('uploaded_ALT-OPT.pdf');
      if (hasGAP && hasALT) {
        return {
          ...mockDetailsMap[nodeId],
          aiSuggestion: {
            isGap: false,
            isCrossroads: true,
            reason: 'NGÃ RẼ TRI THỨC: Chọn hướng AI/DRL hay Toán học?',
            suggestedDocuments: [],
          },
        };
      }
    }

    return mockDetailsMap[nodeId] || generatePlaceholder(nodeId);
  },

  // MÔ PHỎNG UPLOAD
  uploadFile: async (filename: string): Promise<void> => {
    await delay(1500);
    localStorage.setItem(`uploaded_${filename}`, 'true');
    console.log(`Uploaded: ${filename}`);
  },
};

// Helper
const delay = (ms: number) => new Promise(r => setTimeout(r, ms));
const generatePlaceholder = (id: string): NodeDetailsResponse => ({
  id,
  name: id,
  type: 'concept',
  synthesis: 'Placeholder node.',
  evidence: [],
  aiSuggestion: { isGap: false, isCrossroads: false, reason: '' },
});