# Page 3 - Knowledge Tree Workspace

## Overview

The Knowledge Tree Workspace is the core feature of NavNexus, providing an interactive visualization and navigation system for exploring knowledge graphs built from uploaded documents.

## Features Implemented

### ✅ Core Functionality
- **Lazy Loading 3-Tier Architecture**: Root → Children → Details with parallel API calls
- **Hierarchical Tree Visualization**: Recursive tree rendering supporting 7+ levels deep
- **Tree Navigation System**: Breadcrumb, history (back/forward), search, and jump list
- **Node Details Sidebar**: Displays synthesis, evidence, and AI suggestions
- **Knowledge Gap Detection**: Highlights nodes with insufficient evidence
- **Crossroads Detection**: Identifies nodes with multiple solution approaches
- **Suggested Documents**: AI-powered document recommendations for gap nodes

### 🎨 UI/UX Features
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Dark Mode Support**: Full dark mode implementation
- **Loading States**: Skeleton loaders and spinners for async operations
- **Smooth Animations**: Tailwind CSS transitions for expand/collapse
- **Interactive Icons**: Type-based icons with special animations for GAP and CROSSROADS nodes
- **Badges**: Visual indicators for node types (GAP, CROSSROADS)

### 🔧 Technical Implementation
- **TypeScript**: Strict mode with full type safety
- **Zustand**: State management for tree and navigation
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first styling with custom theme
- **Lucide Icons**: Modern icon set
- **Mock Data**: Development-ready mock service

## Project Structure

```
Frontend/src/
├── types/
│   ├── tree.types.ts          # Tree node type definitions
│   ├── evidence.types.ts      # Evidence and AI suggestion types
│   └── index.ts
├── services/
│   ├── api.service.ts         # Axios instance with interceptors
│   └── tree.service.ts        # Tree API endpoints
├── store/
│   ├── treeStore.ts           # Tree state management
│   └── navigationStore.ts     # Navigation history and bookmarks
├── pages/workspace/
│   ├── WorkspacePage.tsx      # Main container
│   └── components/
│       ├── layout/
│       │   ├── WorkspaceHeader.tsx
│       │   ├── WorkspaceToolbar.tsx
│       │   └── WorkspaceSidebar.tsx
│       ├── tree/
│       │   ├── KnowledgeTree.tsx
│       │   ├── TreeNode.tsx
│       │   ├── TreeNodeIcon.tsx
│       │   └── TreeExpandButton.tsx
│       ├── navigation/
│       │   ├── TreeNavigator.tsx
│       │   ├── NavigationBreadcrumb.tsx
│       │   ├── NavigationHistory.tsx
│       │   ├── NavigationSearch.tsx
│       │   └── NavigationJumpList.tsx
│       └── details/
│           ├── NodeSynthesis.tsx
│           ├── NodeEvidence.tsx
│           ├── EvidenceItem.tsx
│           ├── NodeAiSuggestion.tsx
│           └── SuggestedDocuments.tsx
├── utils/
│   ├── cn.ts                  # Tailwind class merger
│   └── tree.utils.ts          # Tree traversal utilities
└── mocks/
    └── mockData.ts            # Mock data for development
```

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd Frontend
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Environment Variables

Create a `.env.development` file:

```
VITE_API_BASE_URL=http://localhost:5000/api
```

## API Integration

The application expects the following API endpoints:

### API 1: Load Root
```
GET /api/workspaces/{workspaceId}/tree/root
Response: { root: TreeNodeShallow, children: TreeNodeShallow[] }
```

### API 2: Load Children
```
GET /api/workspaces/{workspaceId}/tree/nodes/{nodeId}/children
Response: TreeNodeShallow[]
```

### API 3: Load Details
```
GET /api/workspaces/{workspaceId}/tree/nodes/{nodeId}/details
Response: NodeDetailsResponse
```

See `src/types/` for full type definitions.

## Usage

### Navigating the Tree

1. **Expand Nodes**: Click the `[>]` button or click on the node name
2. **Collapse Nodes**: Click the `[v]` button on expanded nodes
3. **View Details**: Click on any node to see details in the sidebar
4. **Navigate History**: Use back/forward buttons in the navigation bar
5. **Search**: Type in the search box to find nodes by name
6. **Jump to Node**: Use the jump list menu to quickly navigate to bookmarks or recent nodes

### Understanding Node Types

- **📁 Topic**: General topic or category
- **📄 Document**: Uploaded document
- **🎯 Problem Domain**: Specific problem area
- **💻 Algorithm**: Solution algorithm or approach
- **⚡ Feature**: System feature or capability
- **💡 Concept**: Conceptual knowledge
- **🌐 Network**: Network or infrastructure component

### Special Node Indicators

- **⚠️ GAP**: Node with insufficient evidence (lacks supporting documents)
- **🔀 CROSSROADS**: Node with multiple approaches or solutions

## Development Notes

### Mock Data Mode

By default, the application uses mock data in development mode. To switch to real API:

1. Set up the backend API
2. Update `VITE_API_BASE_URL` in `.env.development`
3. The app automatically switches based on `import.meta.env.DEV`

### State Management

The application uses two Zustand stores:

- **treeStore**: Manages tree data, expanded nodes, selected node, and details
- **navigationStore**: Manages history, bookmarks, and search state

### Adding New Node Types

1. Update `NodeType` in `src/types/tree.types.ts`
2. Add icon mapping in `src/pages/workspace/components/tree/TreeNodeIcon.tsx`

## Testing

The implementation includes:
- TypeScript strict mode compilation
- Mock data for development and testing
- Proper error handling and loading states

## Performance

- Lazy loading prevents loading entire tree at once
- Parallel API calls (API 2 + API 3) for faster UX
- Memoized components with React.memo (can be added)
- Debounced search (300ms)

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Known Limitations

- Maximum tree depth: 7 levels (as per requirements)
- No offline support yet
- No tree virtualization (add react-window for 1000+ nodes)

## Future Enhancements

- [ ] Graph view mode
- [ ] Export to PDF/JSON/Markdown
- [ ] Real-time collaboration
- [ ] Document upload integration
- [ ] Advanced filtering options
- [ ] Keyboard shortcuts
- [ ] Mobile gestures for tree navigation

## License

Part of the NavNexus project for Naver Vietnam AI Hackathon 2025.
