import React from 'react';
import { ArrowLeft, Settings, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface WorkspaceHeaderProps {
  workspaceName: string;
}

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({ 
  workspaceName 
}) => {
  const navigate = useNavigate();

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            title="Back to home"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {workspaceName}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            title="Members"
          >
            <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          
          <button
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            title="Settings"
          >
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>
    </header>
  );
};
