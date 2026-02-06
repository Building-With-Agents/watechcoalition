"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { Avatar } from "@mui/material";
interface Props {
  id: string;
  fileTypeText: string;
  accept: string;
  maxSizeMB: number;
  userId: string;
  onImageUpload: (url: string) => void;
  initialImageUrl: string; // new prop to accept session image URL
  disabled?: boolean;
  apiPath: string;
}

export default function AvatarUpload({
  id,
  fileTypeText,
  accept,
  maxSizeMB,
  userId,
  onImageUpload,
  initialImageUrl,
  disabled,
  apiPath,
}: Props) {
  const [filesizeExceeded, setFilesizeExceeded] = useState(false);
  const [fileSelected, setFileSelected] = useState("");
  const [filePath, setFilePath] = useState("");

  useEffect(() => {
    setFilePath(initialImageUrl); // Update filePath when initialImageUrl changes
  }, [initialImageUrl]);

  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files != null) {
      const file = event.target.files[0];
      if (file.name !== "") {
        setFileSelected(file.name);
      }

      if (filePath) URL.revokeObjectURL(filePath);
      setFilePath(URL.createObjectURL(file));

      const maxSize = 1048576 * maxSizeMB;
      if (file.size > maxSize) {
        // file is too large
        setFilesizeExceeded(true);
        console.error("File size exceeded. Please use file less than 5MB.");
        return;
      } else setFilesizeExceeded(false); // file juuuust right

      try {
        // Convert file to buffer
        const fileBuffer = await file.arrayBuffer();
        const fileBufferView = Array.from(new Uint8Array(fileBuffer)); // Convert to array for JSON serialization

        // Prepare the payload
        const payload = {
          file: fileBufferView,
          fileName: file.name,
          id: userId,
        };

        // Make a POST request to the API route
        const response = await fetch(apiPath, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        // Check if the upload was successful
        if (response.ok) {
          const result = await response.json();
          setFilePath(result.imageUrl); // Update filePath with the uploaded image URL
          onImageUpload(result.imageUrl); // Return the image URL to the parent component
        } else {
          const errorData = await response.json();
          console.error(errorData.error || "Failed to upload image");
        }
      } catch (error) {
        console.error("Error uploading image:", error);
      }
    } else {
      setFileSelected(""); // no file selected
      if (filePath !== "") URL.revokeObjectURL(filePath);
    }
  };

  let validFiletype = true;
  if (fileSelected != "") {
    const fileType = fileSelected.substring(
      fileSelected.lastIndexOf("."),
      fileSelected.length,
    );
    validFiletype = accept.split(",").includes(fileType.toLowerCase());
  }

  const fileTypeTextPlusSizeLimit =
    fileTypeText + " (max. " + maxSizeMB + " MB)";

  return (
    <div>
      <label className="flex cursor-pointer rounded-full p-4 hover:bg-slate-50">
        <Avatar
          src={filePath || initialImageUrl || undefined}
          alt="Uploaded Avatar"
          sx={{
            width: "5rem",
            height: "5rem",
            flexShrink: 0,
            borderRadius: "50%",
          }}
          data-testid="avatar-image"
        />
        <input
          type="file"
          id={id}
          name={id}
          className="sr-only"
          accept={accept}
          onChange={handleChange}
          disabled={disabled}
        />
        <div className="px-6">
          {fileSelected == "" && (
            <p className="font-medium uppercase text-sky-400">Upload Image</p>
          )}
          {fileSelected != "" && !filesizeExceeded && validFiletype && (
            <p className="font-medium uppercase text-gray-400">
              {fileSelected}
            </p>
          )}
          {fileSelected != "" && !filesizeExceeded && !validFiletype && (
            <p className="font-medium text-red-500">
              Unsupported file type: {fileSelected}
            </p>
          )}
          {fileSelected != "" && filesizeExceeded && (
            <p className="font-medium text-red-500">
              File is too large: {fileSelected}
            </p>
          )}
          <p className="text-sm">{fileTypeTextPlusSizeLimit}</p>
        </div>
      </label>
    </div>
  );
}
