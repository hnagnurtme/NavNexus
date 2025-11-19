import { workspaceService } from "@/services/workspace.service";
import { WorkspaceDetailResponse } from "@/types";
import { createContext, useEffect, useState } from "react";
import { useAuth } from "./AuthContext";
import { ToastNaver } from "@/pages/homepage/components/HomePageComponent/ToastNaver";




export interface WorkSpaceContextType {
  isClicked: boolean;
  setIsClicked: React.Dispatch<React.SetStateAction<boolean>>;
  WorkSpaceData: WorkspaceDetailResponse[];
  setWorkSpaceData: React.Dispatch<
    React.SetStateAction<WorkspaceDetailResponse[]>
  >;
  handleCreateWorkSpace: (
    name: string,
    description: string,
    files: string[]
  ) => Promise<void>;
}
export const WorkSpaceContext = createContext<WorkSpaceContextType>({
  isClicked: false,
  setIsClicked: () => {},
  WorkSpaceData: [],
  setWorkSpaceData: () => {},
  handleCreateWorkSpace: async () => {},
});
export const WorkSpaceProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [isClicked, setIsClicked] = useState(false);
  const {user} = useAuth();
  const [WorkSpaceData, setWorkSpaceData] = useState<
    WorkspaceDetailResponse[]
  >([]);

  useEffect(() => {
    const fetchWorkSpaces = async () => {
      if(!user) return;
      try {
        let response = await workspaceService.getUserWorkspaces();
        if (response.success && response.data && response.data.workspaces) {
          setWorkSpaceData(response.data.workspaces);
        } else {
          setWorkSpaceData([]);
          console.warn('Workspace fetch returned no data:', response.message);
        }
      }
      catch (error) {
        console.error('Failed to fetch workspaces:', error);
        ToastNaver.error("Failed to fetch workspaces. Please try again.");
        setWorkSpaceData([]);
      }
    };
    fetchWorkSpaces();
  }, [user,isClicked]);
  const handleCreateWorkSpace = async (
    name: string,
    description: string,
    files: string[]
  ) => {
    try {
      const newWorkSpace = await workspaceService.createWorkspace({
        name,
        description,
        fileIds: files,
      });
      if (newWorkSpace.success && newWorkSpace.data) {
        setWorkSpaceData((prev) => [...prev, newWorkSpace.data]);
        setIsClicked(prev => !prev);
        ToastNaver.success("Workspace created successfully.");
      } else {
        throw new Error(newWorkSpace.message || "Failed to create workspace");
      }
    } catch (error) {
      ToastNaver.error("Failed to create workspace. Please try again.");
      console.error("Error creating workspace:", error);
      throw error;
    }
  };
  return (
    <WorkSpaceContext.Provider
      value={{
        isClicked,
        setIsClicked,
        WorkSpaceData,
        setWorkSpaceData,
        handleCreateWorkSpace,
      }}
    >
      {children}
    </WorkSpaceContext.Provider>
  );
};
