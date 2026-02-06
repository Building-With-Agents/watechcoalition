"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { FormLabel, SxProps } from "@mui/material";
import { BlobPrefix } from "@/app/lib/services/azureBlobService";

interface Props {
  id: string;
  fileTypeText: string;
  blobPrefix: BlobPrefix;
  accept: string;
  maxSizeMB: number;
  userId: string;
  onDocUpload: (url: string) => void;
  autoloadedUrl?: string;
}

export default function InputFileDropzone({
  id,
  fileTypeText,
  blobPrefix,
  accept,
  maxSizeMB,
  userId,
  onDocUpload,
  autoloadedUrl,
}: Props) {
  const [filesizeExceeded, setFilesizeExceeded] = useState(false);
  const [fileSelected, setFileSelected] = useState(autoloadedUrl ?? "");

  useEffect(() => {
    if (autoloadedUrl) {
      setFileSelected(autoloadedUrl);
    }
  }, [autoloadedUrl]);

  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files != null) {
      const file = event.target.files[0];
      setFileSelected(file.name);
      const maxSize = 1048576 * maxSizeMB;
      if (file.size > maxSize) {
        // file is too large
        setFilesizeExceeded(true);
      } else setFilesizeExceeded(false); // file juuuust right

      try {
        // Convert file to buffer
        const fileBuffer = await file.arrayBuffer();
        const fileBufferView = Array.from(new Uint8Array(fileBuffer)); // Convert to array for JSON serialization

        // Prepare the payload
        const payload = {
          file: fileBufferView,
          fileName: file.name,
          userId: userId,
        };

        // Make a POST request to the API route
        const response = await fetch(`/api/jobseekers/${blobPrefix}/upload`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        // Check if the upload was successful
        if (response.ok) {
          const result = await response.json();
          onDocUpload(result.imageUrl); // Return the image URL to the parent component
        } else {
          const errorData = await response.json();
          console.error(errorData.error || "Failed to upload image");
        }
      } catch (error) {
        console.error("Error uploading image:", error);
      }
    } else setFileSelected(""); // no file selected
  };

  let validFiletype = true;
  if (fileSelected != "") {
    const fileType = fileSelected.substring(
      fileSelected.lastIndexOf("."),
      fileSelected.length,
    );
    validFiletype = accept.split(",").includes(fileType);
  }

  const fileTypeTextPlusSizeLimit =
    fileTypeText + " (max. " + maxSizeMB + " MB)";

  let backgroundCSS: SxProps = {
    borderColor: "rgb(209, 213, 219)",
    backgroundColor: "rgb(249, 250, 251)",
    "&:hover": {
      backgroundColor: "rgb(243, 244, 246)",
    },
  };
  let svgCSS = "text-sky-500 dark:text-sky-400";

  if (
    (!validFiletype || filesizeExceeded) &&
    !fileSelected.startsWith("http")
  ) {
    backgroundCSS = {
      borderColor: "rgb(252, 165, 165)",
      backgroundColor: "rgb(254, 242, 242)",
      "&:hover": {
        backgroundColor: "rgb(254, 226, 226)",
      },
    };

    svgCSS = "text-red-500";
  } else if (fileSelected != "") {
    svgCSS = "text-gray-500";
  }

  backgroundCSS = {
    ...backgroundCSS,
    display: "flex",
    width: "100%",
    cursor: "pointer",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "0.5rem",
    border: "2px dashed",
  };
  svgCSS = svgCSS.concat("h-8 w-8 mr-2");

  return (
    <div className="relative flex w-full items-center justify-center">
      <FormLabel htmlFor={id} sx={backgroundCSS}>
        <div className="flex flex-col items-center justify-center pb-6 pt-5">
          <div className="flex flex-row items-center">
            <svg
              className={svgCSS}
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 20 16"
            >
              <path
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
              />
            </svg>
            {fileSelected == "" && (
              <p className="mb-2 text-sm text-gray-500">
                <span className="text-sky-400 underline">Click to upload</span>{" "}
                or drag and drop
              </p>
            )}
            {fileSelected != "" && !filesizeExceeded && validFiletype && (
              <p className="mb-2 text-sm text-gray-500">{fileSelected}</p>
            )}
            {fileSelected != "" &&
              !filesizeExceeded &&
              !validFiletype &&
              !fileSelected.startsWith("http") && (
                <p className="mb-2 text-sm text-red-500">
                  Unsupported file type: {fileSelected}
                </p>
              )}
            {fileSelected != "" &&
              !filesizeExceeded &&
              !validFiletype &&
              fileSelected.startsWith("http") && (
                <p className="mb-2 text-sm text-gray-500">
                  {(() => {
                    const filePath = fileSelected.split("?")[0];
                    const lastSlash = filePath.lastIndexOf("/");
                    return filePath.substring(lastSlash + 1);
                  })()}
                </p>
              )}
            {fileSelected != "" && filesizeExceeded && (
              <p className="mb-2 text-sm text-red-500">
                File is too large! {/*{fileSelected}*/}
              </p>
            )}
          </div>
          <p className="mt-4 text-xs text-gray-500">
            {fileTypeTextPlusSizeLimit}
          </p>
        </div>
        <input
          type="file"
          id={id}
          name={id}
          className="absolute left-0 top-0 block h-full w-full cursor-pointer opacity-0"
          accept={accept}
          onChange={handleChange}
        />
      </FormLabel>
    </div>
  );
}
