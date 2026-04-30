"use client";

import { Message } from "./ChatWindow";

interface MessageBubbleProps {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

/** Simple markdown-to-HTML renderer for bold, images, links, and line breaks */
function renderContent(content: string): string {
  return content
    // Render images: ![alt](url)
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="w-full max-w-[280px] h-auto mt-2 mb-2 rounded-xl border border-slate-600/50 object-cover shadow-md" loading="lazy" />')
    // Render links: [text](url)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">$1</a>')
    // Render bold
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    // Render italic
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    // Line breaks
    .replace(/\n/g, "<br />");
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-start gap-3 animate-fade-in ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center text-sm flex-shrink-0 ${
          isUser
            ? "bg-gradient-to-br from-emerald-500 to-teal-500 text-white"
            : "bg-gradient-to-br from-violet-600 to-indigo-600 text-white"
        }`}
      >
        {isUser ? "👤" : "🤖"}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[75%] flex flex-col gap-1 ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-gradient-to-br from-violet-600 to-indigo-600 text-white rounded-tr-none shadow-lg shadow-violet-500/20"
              : "bg-slate-800/80 text-slate-100 rounded-tl-none border border-slate-700/40 shadow-md"
          } ${message.isStreaming ? "animate-pulse-subtle" : ""}`}
          dangerouslySetInnerHTML={{ __html: renderContent(message.content) }}
        />

        {/* Metadata */}
        <div
          className={`flex items-center gap-2 text-xs text-slate-600 px-1 ${
            isUser ? "flex-row-reverse" : ""
          }`}
        >
          <span>{formatTime(message.timestamp)}</span>
          {message.agentUsed && !isUser && (
            <>
              <span>·</span>
              <span>
                {message.agentUsed === "sales_agent"
                  ? "🛍️ Tư vấn viên"
                  : "🎧 CSKH"}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
