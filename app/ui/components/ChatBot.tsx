"use client";
import {
  Box,
  Button,
  TextField,
  IconButton,
  Paper,
  Typography,
  List,
  ListItem,
  CircularProgress,
} from "@mui/material";
import { Send, Close, Chat as ChatIcon } from "@mui/icons-material";
import { useCallback, useEffect, useState } from "react";
import { Message, useChat } from "@/app/contexts/ChatContext";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { useSession } from "next-auth/react";

const PDF_WORKER_URL = "/pdf.worker.min.mjs";

marked.setOptions({
  gfm: true,
  breaks: true,
});

const ChatBot = () => {
  const session = useSession();

  const {
    isOpen,
    messages,
    isLoading,
    openChat,
    closeChat,
    sendMessage,
    setResumeText,
    resumeText,
  } = useChat();
  const [input, setInput] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;
      } catch (e) {
        console.error("Failed to load PDF.js", e);
      }
    })();
  }, []);

  const parsePdf = useCallback(
    async (file: File) => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;
        const arrayBuffer = await file.arrayBuffer();
        const loadingTask = pdfjs.getDocument({ data: arrayBuffer });

        const pdf = await loadingTask.promise;

        let fullText = "";
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const textContent = await page.getTextContent();

          if (textContent?.items && Array.isArray(textContent.items)) {
            const pageText = textContent.items
              .filter(
                (item: any) =>
                  typeof item === "object" &&
                  item !== null &&
                  typeof (item as any).str === "string",
              )
              .map((item: any) => (item as any).str)
              .join(" ");
            fullText += pageText + "\n\n";
          }
        }

        const trimmedText = fullText.trim();
        if (!trimmedText) {
          throw new Error("No text could be extracted from the PDF.");
        }
        setResumeText(trimmedText);
      } catch (err: any) {
        console.error("Error parsing PDF:", err);
      } finally {
      }
    },
    [setResumeText],
  );

  useEffect(() => {
    async function fetchAndParseResume() {
      if (!session.data?.user.jobseekerId) {
        return;
      }
      try {
        const resp = await fetch("/api/jobseekers/resume/get");
        if (!resp.ok) {
          throw new Error(`Failed to get resume URL: ${resp.status}`);
        }
        const resumeBlobUrl = await resp.json();
        const pdfResp = await fetch(resumeBlobUrl);
        if (!pdfResp.ok) {
          throw new Error(`Failed to fetch resume PDF: ${pdfResp.status}`);
        }
        const blob = await pdfResp.blob();
        const file = new File([blob], "resume.pdf", {
          type: "application/pdf",
        });
        await parsePdf(file);
      } catch (err) {
        console.error("Error fetching/parsing resume:", err);
      }
    }
    if (!resumeText) {
      fetchAndParseResume();
    }
  }, [parsePdf, resumeText]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput("");
    }
  };

  if (!session.data?.user.jobseekerId) {
    return <></>;
  }

  if (!isOpen) {
    return (
      <Box sx={{ zIndex: 9999, position: "fixed", bottom: 50, right: 24 }}>
        <IconButton
          color="primary"
          onClick={openChat}
          size="large"
          sx={{ bgcolor: "primary.light" }}
        >
          <ChatIcon />
        </IconButton>
      </Box>
    );
  }

  const initialBotMessage: Message = {
    id: 63346346346346,
    sender: "bot" as const,
    text: "Welcome! I'm here to assist you in identifying optimal career opportunities that align with your professional skills. We can begin by analyzing positions that best match your qualifications as highlighted in your resume.",
  };
  const displayMessages = isOpen && [initialBotMessage].concat(messages);

  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        right: 0,
        width: { xs: "100%", sm: "450px" },
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        zIndex: 9999,
        boxShadow: 6,
        backgroundColor: "background.paper",
      }}
    >
      <Paper
        elevation={3}
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          borderRadius: 0,
        }}
      >
        {/* Header */}
        <Box
          sx={{
            bgcolor: "primary.main",
            color: "white",
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6">Career Assistant</Typography>
          <IconButton onClick={closeChat} color="inherit">
            <Close />
          </IconButton>
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            overflowY: "auto",
            p: 2,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <List sx={{ flex: 1, overflowY: "auto" }}>
            {displayMessages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  justifyContent:
                    message.sender === "user" ? "flex-end" : "flex-start",
                  px: 1,
                  py: 0.5,
                }}
              >
                <Paper
                  sx={{
                    p: 1.5,
                    maxWidth: "80%",
                    color: "text.primary",
                    bgcolor:
                      message.sender === "user" ? "primary.light" : "grey.100",
                    borderRadius:
                      message.sender === "user"
                        ? "18px 18px 0 18px"
                        : "18px 18px 18px 0",
                    wordBreak: "break-word",
                    "& pre": {
                      backgroundColor: "rgba(0,0,0,0.05)",
                      padding: "8px",
                      borderRadius: "4px",
                      overflowX: "auto",
                    },
                    "& code": {
                      fontFamily: "monospace",
                      backgroundColor: "rgba(0,0,0,0.05)",
                      padding: "2px 4px",
                      borderRadius: "4px",
                    },
                    "& ol": {
                      listStyleType: "decimal",
                      margin: 0,
                      paddingLeft: "20px",
                    },
                    "& ul": {
                      listStyleType: "disc",
                      margin: 0,
                      paddingLeft: "20px",
                    },
                    "& ul ul": {
                      listStyleType: "circle",
                      margin: 0,
                      paddingLeft: "20px",
                    },
                  }}
                >
                  {message.sender === "bot" ? (
                    <div
                      dangerouslySetInnerHTML={{
                        __html: DOMPurify.sanitize(
                          marked.parse(message.text) as string,
                        ),
                      }}
                    />
                  ) : (
                    <Typography variant="body1">{message.text}</Typography>
                  )}
                </Paper>
              </ListItem>
            ))}
            {isLoading && (
              <ListItem sx={{ justifyContent: "flex-start" }}>
                <CircularProgress size={20} />
              </ListItem>
            )}
          </List>
        </Box>

        {/* Input Area */}
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ p: 1.5, borderTop: 1, borderColor: "divider" }}
        >
          <Box sx={{ display: "flex", gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={isLoading}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={!input.trim()}
              loading={isLoading}
              sx={{ minWidth: "auto" }}
            >
              <Send />
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatBot;
