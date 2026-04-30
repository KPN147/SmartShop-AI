"use client";

import { useState, useRef, useEffect, useCallback, FormEvent } from "react";
import { v4 as uuidv4 } from "uuid";
import { sendMessage, SentimentResult } from "@/lib/api";
import ChatWindow, { Message } from "@/components/ChatWindow";
import AgentStatus from "@/components/AgentStatus";

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const [lastAgent, setLastAgent] = useState<string | null>(null);
  const [lastSentiment, setLastSentiment] = useState<SentimentResult | null>(null);
  const [lastProcessingTime, setLastProcessingTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Handle quick suggestion clicks from ChatWindow
  useEffect(() => {
    const handler = (e: Event) => {
      const text = (e as CustomEvent<string>).detail;
      setInput(text);
      inputRef.current?.focus();
    };
    window.addEventListener("suggestion-click", handler);
    return () => window.removeEventListener("suggestion-click", handler);
  }, []);

  const handleSend = useCallback(
    async (messageText?: string) => {
      const text = (messageText || input).trim();
      if (!text || isLoading) return;

      setInput("");
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
      setError(null);
      setIsLoading(true);

      const userMessage: Message = {
        id: uuidv4(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await sendMessage(text, sessionId);

        const assistantMessage: Message = {
          id: uuidv4(),
          role: "assistant",
          content: response.response,
          agentUsed: response.agent_used,
          sentiment: response.sentiment,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setLastAgent(response.agent_used);
        setLastSentiment(response.sentiment);
        setLastProcessingTime(response.processing_time_ms);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Lỗi không xác định";
        setError(`Không thể kết nối đến server: ${errorMsg}`);
        // Remove the user message on error so they can retry
        setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      } finally {
        setIsLoading(false);
        inputRef.current?.focus();
      }
    },
    [input, isLoading, sessionId]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSend();
  };

  const clearChat = () => {
    setMessages([]);
    setLastAgent(null);
    setLastSentiment(null);
    setLastProcessingTime(null);
    setError(null);
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-xl shadow-lg shadow-violet-500/30">
              🛒
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-slate-900" />
          </div>
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-violet-300 to-indigo-300 bg-clip-text text-transparent">
              SmartShop AI
            </h1>
            <p className="text-xs text-slate-500">Trợ lý mua sắm thông minh</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-all"
              title="Xóa hội thoại"
            >
              🗑️ Xóa
            </button>
          )}
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-xs text-emerald-400 font-medium">Online</span>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <ChatWindow messages={messages} isLoading={isLoading} />

      {/* Error banner */}
      {error && (
        <div className="mx-4 mb-2 px-4 py-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-sm text-rose-400 flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button
            onClick={() => setError(null)}
            className="text-rose-400 hover:text-rose-200 ml-3"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input Area */}
      <div className="px-4 pb-4 pt-2 bg-slate-900/50 backdrop-blur-sm">
        <form
          onSubmit={handleSubmit}
          className="flex items-end gap-3 bg-slate-800/60 border border-slate-700/50 rounded-2xl px-4 py-3 focus-within:border-violet-500/60 focus-within:shadow-[0_0_0_1px_rgba(139,92,246,0.2)] transition-all"
        >
          <textarea
            ref={inputRef}
            id="chat-input"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              // Auto-resize the textarea to prevent layout shaking
              e.target.style.height = 'auto';
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={handleKeyDown}
            placeholder="Nhập tin nhắn... (Enter để gửi, Shift+Enter xuống dòng)"
            rows={1}
            disabled={isLoading}
            className="flex-1 bg-transparent text-slate-100 placeholder-slate-600 text-sm resize-none outline-none max-h-32 disabled:opacity-50 leading-relaxed py-2"
            style={{ scrollbarWidth: "none" }}
          />
          <button
            type="submit"
            id="send-button"
            disabled={isLoading || !input.trim()}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-violet-500/30 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95 flex-shrink-0"
            title="Gửi tin nhắn"
          >
            {isLoading ? (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </form>
        <p className="text-center text-xs text-slate-700 mt-2">
          SmartShop AI có thể mắc lỗi. Kiểm tra thông tin quan trọng.
        </p>
      </div>

      {/* Agent Status Bar */}
      <AgentStatus
        agentUsed={lastAgent}
        sentiment={lastSentiment}
        processingTime={lastProcessingTime}
        isLoading={isLoading}
      />
    </div>
  );
}
