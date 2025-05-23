import { create } from "zustand";
import { ChatMessage } from "../types/chat";

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  clearMessages: () => void;
  initializeSession: () => void;
}

// セッションIDを生成する関数
const generateSessionId = () => {
  return crypto.randomUUID();
};

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: null,
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    })),
  clearMessages: () => set({ messages: [] }),
  initializeSession: () => {
    const state = get();
    if (!state.sessionId) {
      set({ sessionId: generateSessionId() });
    }
  },
})); 