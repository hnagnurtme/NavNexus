import { createContext } from "react";
export interface UploadCloudinaryContextType {
  changeRawCloudinary: (files: File[]) => Promise<string[]>;
  changeRawCloudinarySingle: (file: File) => Promise<string>;
}
export const UploadCloudinaryContext = createContext<UploadCloudinaryContextType>({
  changeRawCloudinary: async () => {
    return [];
  },
  changeRawCloudinarySingle: async () => {
    return "";
  },
});
export const UploadCloudinaryProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const PresetCloudinary = "navnexus_workspace_preset";
  const CloudinaryUrl = "https://api.cloudinary.com/v1_1/dnxjlsyp4/upload";
  const uploadToCloudinary = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("upload_preset", PresetCloudinary);

    const response = await fetch(CloudinaryUrl, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Cloudinary upload failed: ${response.status}`);
    }

    return await response.json();
  };
  const changeRawCloudinary = async (files: File[]) => {
    const uploadPromises = files.map((file) => uploadToCloudinary(file));
    const uploadResults = await Promise.all(uploadPromises);
    const urls = uploadResults.map((result) => result.url);
    return urls;
  };
  const changeRawCloudinarySingle = async (file: File) => {
    const result = await uploadToCloudinary(file);
    return result.url;
  }
  return (
    <UploadCloudinaryContext.Provider value={{ changeRawCloudinary,changeRawCloudinarySingle }}>
      {children}
    </UploadCloudinaryContext.Provider>
  );
};
