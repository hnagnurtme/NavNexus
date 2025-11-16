import { workspaceService } from "@/services/workspace.service";
import { WorkspaceDetailResponseApiResponse } from "@/types";
import { createContext, useEffect, useState } from "react";
import { useAuth } from "./AuthContext";
import { ToastNaver } from "@/pages/homepage/components/HomePageComponent/ToastNaver";




export interface WorkSpaceContextType {
  isClicked: boolean;
  setIsClicked: React.Dispatch<React.SetStateAction<boolean>>;
  WorkSpaceData: WorkspaceDetailResponseApiResponse[];
  setWorkSpaceData: React.Dispatch<
    React.SetStateAction<WorkspaceDetailResponseApiResponse[]>
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
    WorkspaceDetailResponseApiResponse[]
  >([]);

  useEffect(() => {
    const fetchWorkSpaces = async () => {
      if(!user) return;
      try {
        let workspacese = await workspaceService.getUserWorkspaces();
        setWorkSpaceData([workspacese]);
        ToastNaver.success("Workspaces loaded successfully.");

      }
      catch (error) {
        ToastNaver.error("Failed to fetch workspaces. Please try again.");
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
      setIsClicked(prev => !prev);
      setWorkSpaceData((prev) => [...prev, newWorkSpace]);
      ToastNaver.success("Workspace created successfully.");
    } catch (error) {
      ToastNaver.error("Failed to create workspace. Please try again.");
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
