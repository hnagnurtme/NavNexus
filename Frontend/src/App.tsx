import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useMemo, type PropsWithChildren } from "react";

import { WorkspacePage } from "./pages/workspace/WorkspacePage";
import { AuthPage } from "./pages/auth/AuthPage";
import { useAuth } from "./contexts/AuthContext";
import Homepage from "./pages/homepage/Homepage";
import { NaverToaster } from "./pages/homepage/components/HomePageComponent/ToastNaver";


const PrivateRoute = ({ children }: PropsWithChildren) => {
  const { isAuthenticated, isInitializing } = useAuth();

  const fallback = useMemo(
    () => (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-gray-50 text-gray-700 dark:bg-gray-950 dark:text-gray-300">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyber-blue border-t-transparent" />
        <p className="text-sm">Preparing your workspace...</p>
      </div>
    ),
    [],
  );

  if (isInitializing) {
    return fallback;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <>
    <NaverToaster />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/login" element={<AuthPage initialMode="login" />} />
          <Route
            path="/register"
            element={<AuthPage initialMode="register" />}
          />
          <Route
            path="/workspace/:workspaceId"
            element={
              <PrivateRoute>
                <WorkspacePage />
              </PrivateRoute>
            }
          />
          <Route
            path="*"
            element={
              <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    404
                  </h1>
                  <p className="text-gray-600 dark:text-gray-400">
                    Page not found
                  </p>
                </div>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
