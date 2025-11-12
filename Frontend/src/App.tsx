import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { WorkspacePage } from './pages/workspace/WorkspacePage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/workspace/demo" replace />} />
        <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        <Route path="*" element={
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">404</h1>
              <p className="text-gray-600 dark:text-gray-400">Page not found</p>
            </div>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
