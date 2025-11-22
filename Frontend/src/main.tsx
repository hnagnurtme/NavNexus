import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import './styles/index.css';
import { WorkSpaceProvider } from './contexts/WorkSpaceContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <WorkSpaceProvider>
        <App />
      </WorkSpaceProvider>
    </AuthProvider>
  </React.StrictMode>,
);
