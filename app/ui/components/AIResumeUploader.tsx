"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { Box, Button, CircularProgress, Alert } from "@mui/material";
import * as pdfjsLib from "pdfjs-dist";
import { UploadFileRounded } from "@mui/icons-material";

const PDF_WORKER_URL = "/pdf.worker.min.mjs";

interface ResumeUploaderProps {
  onExtractionCompleteAction?: (jsonData: any) => void;
  onErrorAction?: (errorMessage: string) => void;
  onProcessingStartAction?: () => void;
}

export function ResumeUploader({
  onExtractionCompleteAction,
  onErrorAction,
  onProcessingStartAction,
}: ResumeUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [isProcessingAI, setIsProcessingAI] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;
    } catch {
      const errMsg =
        "Failed to configure PDF processing library. Please refresh the page.";
      setError(errMsg);
      if (onErrorAction) onErrorAction(errMsg);
    }
  }, [onErrorAction]);

  const parsePdf = useCallback(
    async (file: File) => {
      setIsParsing(true);
      setError(null);
      onProcessingStartAction?.();

      try {
        const arrayBuffer = await file.arrayBuffer();
        const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });

        const pdf = await loadingTask.promise;

        let fullText = "";
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const textContent = await page.getTextContent();

          if (textContent?.items && Array.isArray(textContent.items)) {
            const pageText = textContent.items
              .filter(
                (item) =>
                  typeof item === "object" &&
                  item !== null &&
                  typeof (item as any).str === "string",
              )
              .map((item) => (item as any).str)
              .join(" ");
            fullText += pageText + "\n\n";
          }
        }

        const trimmedText = fullText.trim();
        if (!trimmedText) {
          throw new Error("No text could be extracted from the PDF.");
        }
        return trimmedText;
      } catch (err: any) {
        console.error("Error parsing PDF:", err);
        const errMsg = `Error reading PDF: ${err.message || "Unknown error"}`;
        setError(errMsg);
        if (onErrorAction) onErrorAction(errMsg);
        return null;
      } finally {
        setIsParsing(false);
      }
    },
    [onErrorAction, onProcessingStartAction],
  );

  const sendTextToApi = useCallback(
    async (text: string, resume: File) => {
      setIsProcessingAI(true);
      setError(null);
      if (!isParsing) onProcessingStartAction?.();
      const formData = new FormData();
      formData.append("extractedText", text);
      formData.append("file", resume);
      try {
        const response = await fetch("/api/jobseekers/resume/parse", {
          method: "POST",
          body: formData,
        });

        const responseData = await response.json();

        if (!response.ok) {
          const errorMsg =
            responseData?.message ||
            response.statusText ||
            `API Error (${response.status})`;
          console.error("API Error Response:", responseData);
          throw new Error(errorMsg);
        }
        if (onExtractionCompleteAction)
          onExtractionCompleteAction(responseData);
      } catch (err: any) {
        console.error("Error processing with AI:", err);
        const errMsg = `AI Processing Failed: ${err.message}`;
        setError(errMsg);
        if (onErrorAction) onErrorAction(errMsg);
      } finally {
        setIsProcessingAI(false);
      }
    },
    [
      onExtractionCompleteAction,
      onErrorAction,
      onProcessingStartAction,
      isParsing,
    ],
  );

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (event.target) event.target.value = "";

      if (file && file.type === "application/pdf") {
        setSelectedFile(file);
        setError(null);

        const extractedText = await parsePdf(file);
        if (extractedText) {
          await sendTextToApi(extractedText, file);
        }
      } else if (file) {
        setSelectedFile(null);
        const errMsg = "Please select a valid PDF file.";
        setError(errMsg);
        if (onErrorAction) onErrorAction(errMsg);
      } else {
        setSelectedFile(null);
        setError(null);
      }
    },
    [parsePdf, sendTextToApi, onErrorAction],
  );

  const handleUploadClick = () => {
    setError(null);
    setSelectedFile(null);
    fileInputRef.current?.click();
  };

  const isLoading = isParsing || isProcessingAI;

  return (
    <Box>
      <input
        type="file"
        accept="application/pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        id="resume-upload-input"
        disabled={isLoading}
      />
      <label>
        <Button
          variant="outlined"
          component="span"
          startIcon={
            isLoading ? (
              <CircularProgress color="inherit" />
            ) : (
              <UploadFileRounded />
            )
          }
          onClick={handleUploadClick}
          loading={isLoading}
        >
          {isLoading ? "Processing..." : "Upload Resume (pdf)"}
        </Button>
      </label>
      {isLoading && !error && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          Processing, Please Wait
        </Alert>
      )}

      {selectedFile && !isLoading && !error && (
        <Alert sx={{ mt: 1 }}>Processed Successfully</Alert>
      )}

      {error && !isLoading && (
        <Alert severity="error" sx={{ mt: 1 }}>
          Failed to Parse Resume
        </Alert>
      )}
    </Box>
  );
}
