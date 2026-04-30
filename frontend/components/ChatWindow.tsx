"use client";

import { useEffect, useRef, memo } from "react";
import { SentimentResult } from "@/lib/api";
import MessageBubble from "./MessageBubble";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentUsed?: string;
  sentiment?: SentimentResult;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

const ChatWindow = memo(function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full gap-6 text-center animate-fade-in">
          <div className="relative">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-4xl shadow-2xl shadow-violet-500/30">
              🤖
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-2 border-slate-900 flex items-center justify-center text-xs">
              ✓
            </div>
          </div>
          <div>
            <h2 className="text-xl font-bold text-white mb-2">SmartShop AI sẵn sàng!</h2>
            <p className="text-slate-400 text-sm max-w-xs">
              Tôi có thể giúp bạn tư vấn sản phẩm, kiểm tra đơn hàng và giải đáp mọi thắc mắc.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 max-w-sm w-full">
            {[
              "📱 Gợi ý điện thoại tầm 10 triệu",
              "📦 Kiểm tra đơn hàng ORD-2024-001",
              "🔧 Chính sách bảo hành?",
              "💸 So sánh iPhone và Samsung",
            ].map((suggestion) => (
              <button
                key={suggestion}
                className="text-left px-3 py-2 rounded-xl bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300 hover:border-violet-500/50 hover:bg-slate-800 transition-all duration-200 hover:text-white"
                onClick={() => {
                  const event = new CustomEvent("suggestion-click", {
                    detail: suggestion.slice(3).trim(),
                  });
                  window.dispatchEvent(event);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-sm flex-shrink-0">
            🤖
          </div>
          <div className="bg-slate-800/80 rounded-2xl rounded-tl-none px-4 py-3">
            <div className="flex gap-1.5 items-center h-5">
              <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce [animation-delay:0.15s]" />
              <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce [animation-delay:0.3s]" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
});

export default ChatWindow;
