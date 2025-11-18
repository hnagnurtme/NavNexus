

```
Frontend/
│
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       ├── images/
│       │   ├── logo.svg
│       │   ├── empty-state.svg
│       │   └── icons/
│       │       ├── node-topic.svg
│       │       ├── node-gap.svg
│       │       └── node-crossroads.svg
│       └── fonts/
│
├── src/
│   │
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component + Router
│   ├── vite-env.d.ts              # Vite type definitions
│   │
│   ├── config/
│   │   ├── api.config.ts          # API base URLs, endpoints
│   │   ├── constants.ts           # App constants (max file size, etc.)
│   │   └── routes.ts              # Route paths constants
│   │
│   ├── types/
│   │   ├── index.ts               # Export all types
│   │   ├── auth.types.ts          # User, LoginRequest, RegisterRequest
│   │   ├── workspace.types.ts     # Workspace, WorkspaceCreate, WorkspaceMember
│   │   ├── tree.types.ts          # TreeNodeShallow, TreeRootResponse, NodeChildrenResponse
│   │   ├── evidence.types.ts      # Evidence, NodeDetailsResponse, AiSuggestion
│   │   └── api.types.ts           # ApiResponse<T>, ApiError, PaginatedResponse<T>
│   │
│   ├── services/
│   │   ├── api.service.ts         # Base axios instance, interceptors
│   │   ├── auth.service.ts        # login(), register(), logout(), getCurrentUser()
│   │   ├── workspace.service.ts   # getWorkspaces(), createWorkspace(), deleteWorkspace()
│   │   ├── tree.service.ts        # getTreeRoot(), getNodeChildren(), getNodeDetails()
│   │   └── document.service.ts    # uploadDocument(), deleteDocument(), getDocuments()
│   │
│   ├── hooks/
│   │   ├── useAuth.ts             # Custom hook: login state, logout function
│   │   ├── useWorkspaces.ts       # Fetch & manage workspaces list
│   │   ├── useTree.ts             # Tree state management (expand/collapse/load)
│   │   ├── useNodeDetails.ts      # Sidebar details loading
│   │   ├── useTreeNavigation.ts   # Du hành trên cây (breadcrumb, history, jump)
│   │   └── useDebounce.ts         # Utility hook
│   │
│   ├── store/                     # State management (Zustand recommended)
│   │   ├── index.ts               # Store setup
│   │   ├── authStore.ts           # Auth state (user, token, isAuthenticated)
│   │   ├── workspaceStore.ts      # Current workspace, workspaces list
│   │   ├── treeStore.ts           # Tree state (nodes, expanded IDs, selected node)
│   │   ├── navigationStore.ts     # Navigation history, bookmarks, search
│   │   └── uiStore.ts             # UI state (sidebar open/close, theme, etc.)
│   │
│   ├── pages/
│   │   │
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── ForgotPasswordPage.tsx (optional)
│   │   │
│   │   ├── home/
│   │   │   ├── HomePage.tsx              # Main homepage (workspace list)
│   │   │   └── components/
│   │   │       ├── WorkspaceCard.tsx     # Single workspace card
│   │   │       ├── WorkspaceGrid.tsx     # Grid layout
│   │   │       ├── CreateWorkspaceModal.tsx
│   │   │       └── EmptyState.tsx        # No workspaces yet
│   │   │
│   │   └── workspace/
│   │       ├── WorkspacePage.tsx         # Main workspace page (Trang 3)
│   │       │
│   │       └── components/
│   │           │
│   │           ├── layout/
│   │           │   ├── WorkspaceHeader.tsx    # Top bar (workspace name, actions)
│   │           │   ├── WorkspaceToolbar.tsx   # Tools (upload, export, settings)
│   │           │   └── WorkspaceSidebar.tsx   # Right sidebar (node details)
│   │           │
│   │           ├── tree/
│   │           │   ├── KnowledgeTree.tsx          # Main tree component
│   │           │   ├── TreeNode.tsx               # Single node (recursive)
│   │           │   ├── TreeNodeIcon.tsx           # Icon based on type/flags
│   │           │   ├── TreeNodeContent.tsx        # Node text + badges
│   │           │   ├── TreeExpandButton.tsx       # [+]/[-] button
│   │           │   ├── TreeLoadingState.tsx       # Skeleton loader
│   │           │   └── TreeEmptyState.tsx         # No documents uploaded
│   │           │
│   │           ├── navigation/
│   │           │   ├── TreeNavigator.tsx          # Du hành component container
│   │           │   ├── NavigationBreadcrumb.tsx   # Path từ root → current
│   │           │   ├── NavigationHistory.tsx      # History stack (back/forward)
│   │           │   ├── NavigationJumpList.tsx     # Quick jump menu
│   │           │   ├── NavigationSearch.tsx       # Search nodes trong tree
│   │           │   └── NavigationMiniMap.tsx      # Tree overview (optional)
│   │           │
│   │           ├── details/
│   │           │   ├── NodeDetailsSidebar.tsx     # Main sidebar
│   │           │   ├── NodeSynthesis.tsx          # Synthesis section
│   │           │   ├── NodeEvidence.tsx           # Evidence list
│   │           │   ├── EvidenceItem.tsx           # Single evidence card
│   │           │   ├── NodeAiSuggestion.tsx       # AI insight banner
│   │           │   ├── SuggestedDocuments.tsx     # GAP - suggested docs list
│   │           │   └── NodeMetadata.tsx           # Type, level, flags info
│   │           │
│   │           ├── documents/
│   │           │   ├── DocumentUploader.tsx       # Upload file component
│   │           │   ├── DocumentList.tsx           # List uploaded docs
│   │           │   ├── DocumentItem.tsx           # Single doc card
│   │           │   └── DocumentDeleteModal.tsx    # Confirm delete
│   │           │
│   │           └── shared/
│   │               ├── NodeBadge.tsx              # Gap/Crossroads badges
│   │               ├── LevelIndicator.tsx         # Level depth indicator
│   │               └── LoadingSpinner.tsx         # Spinner for async ops
│   │
│   ├── components/                # Shared components (dùng chung nhiều pages)
│   │   │
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx              # Main layout wrapper
│   │   │   ├── Header.tsx                 # Global header (logo, user menu)
│   │   │   ├── Footer.tsx                 # Global footer
│   │   │   └── Sidebar.tsx                # Global sidebar (nếu có)
│   │   │
│   │   ├── ui/                            # UI primitives (shadcn/ui style)
│   │   │   ├── Button.tsx                 # Variants: primary, secondary, ghost, outline
│   │   │   ├── Input.tsx                  # Base input với Tailwind
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── Avatar.tsx
│   │   │   ├── ScrollArea.tsx
│   │   │   └── Separator.tsx
│   │   │
│   │   ├── form/
│   │   │   ├── FormField.tsx              # Wrapper with label + error
│   │   │   ├── TextInput.tsx
│   │   │   ├── EmailInput.tsx
│   │   │   ├── PasswordInput.tsx
│   │   │   ├── FileInput.tsx
│   │   │   └── FormError.tsx
│   │   │
│   │   └── feedback/
│   │       ├── LoadingScreen.tsx          # Full screen loader
│   │       ├── ErrorBoundary.tsx          # React error boundary
│   │       ├── EmptyState.tsx             # Generic empty state
│   │       └── NotFound.tsx               # 404 component
│   │
│   ├── utils/
│   │   ├── api.utils.ts               # API helpers (buildUrl, handleError)
│   │   ├── tree.utils.ts              # Tree operations (findNode, updateNode, calculateLevel)
│   │   ├── navigation.utils.ts        # Breadcrumb generation, path calculation
│   │   ├── format.utils.ts            # Date, number formatting
│   │   ├── validation.utils.ts        # Form validation helpers
│   │   ├── storage.utils.ts           # LocalStorage wrapper
│   │   ├── string.utils.ts            # String operations (truncate, slugify)
│   │   └── cn.ts                      # classnames utility (clsx + tailwind-merge)
│   │
│   ├── styles/
│   │   ├── index.css                  # Main CSS entry (Tailwind directives)
│   │   └── animations.css             # Custom @keyframes animations
│   │
│   ├── lib/                           # Third-party library configs
│   │   ├── axios.ts                   # Axios instance setup
│   │   └── react-query.ts             # React Query client config (optional)
│   │
│   ├── routes/
│   │   ├── index.tsx                  # Route configuration
│   │   ├── ProtectedRoute.tsx         # Auth guard wrapper
│   │   └── PublicRoute.tsx            # Redirect if authenticated
│   │
│   └── contexts/                      # React Contexts (nếu cần bổ sung Zustand)
│       ├── ThemeContext.tsx           # Dark/Light mode toggle
│       └── ToastContext.tsx           # Global toast notifications
│
├── .env.development                   # Dev environment variables
├── .env.production                    # Prod environment variables
├── .eslintrc.json                     # ESLint config
├── .prettierrc                        # Prettier config
├── tsconfig.json                      # TypeScript config
├── vite.config.ts                     # Vite config
├── tailwind.config.js                 # Tailwind CSS config ⭐
├── postcss.config.js                  # PostCSS config (autoprefixer)
├── package.json
└── README.md
```

## Chatbot API Readiness

- Frontend types: `src/types/chatbot.types.ts` defines the payload/response shapes.
- Service: `src/services/chatbot.service.ts` posts to `/chatbot/query` (or the mock when `VITE_USE_CHATBOT_MOCK` is not `"false"`).
- Mock data: `src/services/mocks/chatbot.mock.ts` mirrors the expected backend output for local development.
- Full contract + sample payloads: see [`docs/chatbot-api.md`](docs/chatbot-api.md) before wiring the backend so both sides agree on the shape.
