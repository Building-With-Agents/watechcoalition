"use client";
import React, {
  createContext,
  ReactNode,
  useState,
  useContext,
  useCallback,
} from "react";

export interface Message {
  id: number;
  text: string;
  sender: "user" | "bot";
}

export interface ChatContextType {
  isOpen: boolean;
  messages: Message[];
  isLoading: boolean;
  resumeText: string | null;
  setResumeText: (text: string | null) => void;
  openChat: () => void;
  closeChat: () => void;
  sendMessage: (message: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
  children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [resumeText, setResumeText] = useState<string | null>(null);

  const openChat = useCallback(() => setIsOpen(true), []);
  const closeChat = useCallback(() => setIsOpen(false), []);

  const sendMessage = useCallback(
    async (message: string) => {
      const userMessage: Message = {
        id: Date.now(),
        text: message,
        sender: "user",
      };

      const newMessages = [...messages, userMessage];
      setMessages(newMessages);
      setIsLoading(true);

      try {
        const response = await fetch("/api/chatbot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: message, resumeText }),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        const botMessage: Message = {
          id: Date.now() + 1,
          text: data.reply,
          sender: "bot",
        };

        setMessages((prev) => [...prev, botMessage]);
      } catch (error) {
        console.error("Fetch error:", error);
        const errorMessage: Message = {
          id: Date.now() + 1,
          text: "Sorry, I'm having trouble connecting. Please try again later.",
          sender: "bot",
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, resumeText],
  );

  const value: ChatContextType = {
    isOpen,
    messages,
    isLoading,
    resumeText,
    setResumeText,
    openChat,
    closeChat,
    sendMessage,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextType {
  const ctx = useContext(ChatContext);
  if (!ctx) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return ctx;
}
