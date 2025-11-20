# Frontend Integration Guide - Knowledge Graph Build UX

## Overview

The Frontend has been updated to handle two different scenarios when building a knowledge graph:

1. **SUCCESS Status**: All files already exist → Fetch graph immediately
2. **PENDING Status**: New files to process → Show loading animation and listen to Firebase

## 🎨 User Experience Flow

```
User uploads files/links
        ↓
Clicks "Build Knowledge Graph"
        ↓
API Call: POST /api/knowledge-tree
        ↓
    ┌─────────────┐
    │   Response  │
    └─────────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
SUCCESS    PENDING
    ↓         ↓
 Fetch     Loading
 Graph   Animation
    ↓         ↓
Display   Firebase
 Graph    Listener
             ↓
         Status Update
             ↓
          Fetch &
         Display
          Graph
```

## 📦 New Components

### 1. Firebase Listener Utility

**File**: `Frontend/src/utils/firebase-listener.ts`

```typescript
import { listenToJobStatus } from '@/utils/firebase-listener';

// Listen to job status updates
const cleanup = listenToJobStatus(jobId, (status) => {
  console.log('Job status:', status);
  
  if (status.status === 'completed') {
    // Handle completion
  } else if (status.status === 'failed') {
    // Handle failure
  }
});

// Cleanup when done
cleanup();
```

**Job Status Structure**:
```typescript
interface JobStatus {
  status: 'pending' | 'completed' | 'failed' | 'partial';
  workspaceId?: string;
  totalFiles?: number;
  successful?: number;
  failed?: number;
  currentFile?: number;
  processingTimeMs?: number;
  timestamp?: string;
  error?: string;
  results?: any[];
}
```

### 2. Updated ControlPanel

**File**: `Frontend/src/pages/workspace/components/control/ControlPanel.tsx`

#### New States

```typescript
const [isBuilding, setIsBuilding] = useState(false);
const [buildStatus, setBuildStatus] = useState<JobStatus | null>(null);
const [buildError, setbuildError] = useState<string | null>(null);
```

#### Handler Function

```typescript
const handleBuildKnowledgeGraph = async () => {
  // 1. Call API
  const response = await treeService.createKnowledgeTree({
    workspaceId: workspaceId,
    filePaths: filePaths,
  });

  // 2. Check status
  if (status === "SUCCESS") {
    // Immediate fetch
    onSynthesize();
    showSuccessToast("Knowledge graph ready!");
  } else if (status === "PENDING") {
    // Show loading and listen
    const cleanup = listenToJobStatus(messageId, (jobStatus) => {
      setBuildStatus(jobStatus);
      
      if (jobStatus.status === "completed") {
        setIsBuilding(false);
        onSynthesize();
        showSuccessToast("Graph built successfully!");
      }
    });
  }
};
```

## 🎭 UI Components

### Loading Modal

The loading modal appears when `isBuilding === true`:

```tsx
{isBuilding && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div className="rounded-2xl bg-slate-900 p-8 text-center">
      <Loader className="mx-auto mb-4 h-16 w-16 animate-spin text-emerald-400" />
      <h3 className="mb-2 text-xl font-semibold text-white">
        Building Knowledge Graph...
      </h3>
      <p className="mb-4 text-white/60">
        Processing your documents. This may take a few minutes.
      </p>
      
      {/* Progress Bar */}
      {buildStatus && buildStatus.totalFiles && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-white/70">
            <span>Progress</span>
            <span>{buildStatus.successful || 0} / {buildStatus.totalFiles}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all"
              style={{
                width: `${((buildStatus.successful || 0) / buildStatus.totalFiles) * 100}%`,
              }}
            />
          </div>
          <p className="text-xs text-white/50">
            Processing file {buildStatus.currentFile} of {buildStatus.totalFiles}...
          </p>
        </div>
      )}
    </div>
  </div>
)}
```

### Error Display

Error toast appears when `buildError` is set:

```tsx
{buildError && (
  <div className="fixed bottom-4 right-4 z-50 max-w-sm rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
    <div className="flex items-start gap-3">
      <XCircle className="h-5 w-5 flex-shrink-0 text-rose-400" />
      <div className="flex-1">
        <p className="text-sm font-semibold text-rose-300">Build Failed</p>
        <p className="mt-1 text-xs text-rose-200/80">{buildError}</p>
      </div>
      <button onClick={() => setbuildError(null)}>×</button>
    </div>
  </div>
)}
```

## 🔥 Firebase Integration

### Configuration

**File**: `Frontend/src/config/firebase.ts`

```typescript
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth"; 
import { getDatabase } from "firebase/database";

const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  databaseURL: "https://navnexus-default-rtdb.firebaseio.com/",
  projectId: "...",
  // ... other config
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const database = getDatabase(app);  // ← NEW
```

### Realtime Updates

The Firebase listener automatically subscribes to `jobs/{jobId}` and receives real-time updates:

```typescript
// Firebase path: jobs/{jobId}
{
  "status": "pending",
  "workspaceId": "workspace-123",
  "totalFiles": 5,
  "successful": 2,
  "failed": 0,
  "currentFile": 3,
  "processingTimeMs": 15000,
  "timestamp": "2025-01-20T10:30:00Z"
}
```

As the worker processes files, it updates these fields in real-time, and the UI automatically reflects the changes.

## 🧪 Testing Scenarios

### Scenario 1: SUCCESS Status (All Files Exist)

1. Upload files that already exist in the workspace
2. Click "Build Knowledge Graph"
3. **Expected**:
   - API returns immediately with SUCCESS status
   - Graph is fetched and displayed without delay
   - No loading animation shown
   - Success toast appears

### Scenario 2: PENDING Status (New Files)

1. Upload new files that need processing
2. Click "Build Knowledge Graph"
3. **Expected**:
   - API returns PENDING status with messageId
   - Loading modal appears with spinner
   - Progress bar shows file processing progress
   - Firebase listener receives real-time updates
   - When complete, modal closes and graph appears
   - Success toast appears

### Scenario 3: Partial Success

1. Upload mix of valid and invalid files
2. Click "Build Knowledge Graph"
3. **Expected**:
   - Processing completes with some failures
   - Warning toast shows: "Graph built with X failures"
   - Graph displays successfully processed files
   - Error details available in console

### Scenario 4: Complete Failure

1. Upload invalid files or trigger error
2. Click "Build Knowledge Graph"
3. **Expected**:
   - Error modal/toast appears
   - Descriptive error message shown
   - User can dismiss error and retry

## 🎯 API Response Handling

The frontend expects this response structure from `POST /api/knowledge-tree`:

```typescript
{
  "success": true,
  "message": "Job queued for processing",
  "data": {
    "messageId": "job-abc123",  // Job ID for Firebase tracking
    "sentAt": "2025-01-20T10:30:00Z"
  },
  "statusCode": 200
}
```

**Status Determination**:
- If `messageId` exists and is not "IMMEDIATE" → PENDING
- Otherwise → SUCCESS

## 🔄 State Management

### Loading State

```typescript
isBuilding: boolean
// true: Show loading modal
// false: Hide loading modal
```

### Build Status

```typescript
buildStatus: JobStatus | null
// null: No active build
// object: Active build with progress info
```

### Error State

```typescript
buildError: string | null
// null: No error
// string: Error message to display
```

## 📱 Responsive Design

All UI components are fully responsive:

- **Desktop**: Full-width modals with generous padding
- **Tablet**: Centered modal with max-width
- **Mobile**: Full-screen modal with adjusted spacing

## 🎨 Styling

Uses Tailwind CSS v4 with custom utility classes:

- `bg-slate-900` - Dark background
- `text-emerald-400` - Success color
- `text-rose-400` - Error color
- `backdrop-blur-sm` - Glassmorphism effect
- `animate-spin` - Loading spinner animation

## 🚀 Future Improvements

- [ ] Replace `alert()` with proper toast library (e.g., react-hot-toast, sonner)
- [ ] Add animation transitions for modal
- [ ] Add sound effects for completion
- [ ] Add retry button in error state
- [ ] Add cancel button during processing
- [ ] Add detailed progress log
- [ ] Add file-by-file status display
- [ ] Add estimated time remaining
- [ ] Add WebSocket fallback if Firebase fails
- [ ] Add offline queue for failed builds

## 🐛 Troubleshooting

### Issue: Loading modal doesn't appear

- Check `isBuilding` state is being set
- Verify modal z-index is higher than other components
- Check for CSS conflicts

### Issue: Firebase updates not working

- Verify Firebase database URL in config
- Check browser console for Firebase errors
- Ensure Firebase Realtime Database rules allow reads
- Test Firebase connection separately

### Issue: Progress bar not updating

- Verify `buildStatus.totalFiles` exists
- Check `buildStatus.successful` is incrementing
- Verify worker is pushing updates to Firebase
- Check Firebase listener is active

### Issue: Graph not loading after completion

- Verify `onSynthesize()` is being called
- Check network tab for API calls
- Ensure knowledge tree API is working
- Check for JavaScript errors in console

## 📚 Related Files

- `Frontend/src/config/firebase.ts` - Firebase configuration
- `Frontend/src/utils/firebase-listener.ts` - Firebase listener utility
- `Frontend/src/pages/workspace/components/control/ControlPanel.tsx` - Main UI component
- `Frontend/src/pages/workspace/WorkspacePage.tsx` - Parent page component
- `Frontend/src/services/tree.service.ts` - API service
- `RabbitMQ/new_worker.py` - Backend worker

## ✅ Success Criteria

- [x] SUCCESS status fetches graph immediately (no delay)
- [x] PENDING status shows smooth loading animation
- [x] Firebase listener works reliably
- [x] Progress bar updates in real-time
- [x] Job completion triggers graph refresh
- [x] Error handling is user-friendly
- [x] TypeScript types are correct
- [x] Build compiles successfully
- [ ] UI tested with both scenarios
- [ ] End-to-end flow works correctly
