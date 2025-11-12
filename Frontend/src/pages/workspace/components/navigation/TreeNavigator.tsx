import React from 'react';
import { NavigationHistory } from './NavigationHistory';
import { NavigationBreadcrumb } from './NavigationBreadcrumb';
import { NavigationSearch } from './NavigationSearch';
import { NavigationJumpList } from './NavigationJumpList';

interface TreeNavigatorProps {
  workspaceId: string;
}

export const TreeNavigator: React.FC<TreeNavigatorProps> = ({ workspaceId }) => {
  return (
    <div className="flex items-center gap-4 px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
      <NavigationHistory workspaceId={workspaceId} />
      
      <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />
      
      <NavigationBreadcrumb workspaceId={workspaceId} />
      
      <div className="flex-1" />
      
      <NavigationSearch workspaceId={workspaceId} />
      
      <NavigationJumpList workspaceId={workspaceId} />
    </div>
  );
};
