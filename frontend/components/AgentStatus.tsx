"use client";

import { SentimentResult } from "@/lib/api";

interface AgentStatusProps {
  agentUsed: string | null;
  sentiment: SentimentResult | null;
  processingTime: number | null;
  isLoading: boolean;
}

const AGENT_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  sales_agent: { label: "Tư vấn viên", icon: "🛍️", color: "text-violet-400" },
  support_agent: { label: "CSKH", icon: "🎧", color: "text-cyan-400" },
  manager_agent: { label: "Điều phối viên", icon: "🎯", color: "text-amber-400" },
};

const SENTIMENT_CONFIG: Record<string, { icon: string; label: string; color: string }> = {
  positive: { icon: "😊", label: "Vui vẻ", color: "text-emerald-400" },
  neutral: { icon: "😐", label: "Bình thường", color: "text-slate-400" },
  negative: { icon: "😔", label: "Tiêu cực", color: "text-rose-400" },
};

export default function AgentStatus({
  agentUsed,
  sentiment,
  processingTime,
  isLoading,
}: AgentStatusProps) {
  const agent = agentUsed ? AGENT_LABELS[agentUsed] : null;
  const sentimentInfo = sentiment ? SENTIMENT_CONFIG[sentiment.label] : null;

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-slate-900/60 border-t border-slate-700/50 text-xs">
      {isLoading ? (
        <div className="flex items-center gap-2 text-slate-400 animate-pulse">
          <span className="inline-block w-2 h-2 rounded-full bg-violet-500 animate-bounce" />
          <span className="inline-block w-2 h-2 rounded-full bg-violet-500 animate-bounce [animation-delay:0.15s]" />
          <span className="inline-block w-2 h-2 rounded-full bg-violet-500 animate-bounce [animation-delay:0.3s]" />
          <span className="ml-1">AI đang xử lý...</span>
        </div>
      ) : (
        <>
          {agent && (
            <div className="flex items-center gap-1.5">
              <span>{agent.icon}</span>
              <span className={`font-medium ${agent.color}`}>{agent.label}</span>
            </div>
          )}

          {sentimentInfo && (
            <div className="flex items-center gap-1.5">
              <span className="text-slate-600">|</span>
              <span>{sentimentInfo.icon}</span>
              <span className={`${sentimentInfo.color}`}>{sentimentInfo.label}</span>
              {sentiment && (
                <span className="text-slate-600">
                  ({Math.round(sentiment.score * 100)}%)
                </span>
              )}
            </div>
          )}

          {processingTime !== null && (
            <div className="ml-auto flex items-center gap-1 text-slate-600">
              <span>⚡</span>
              <span>{processingTime.toFixed(0)}ms</span>
            </div>
          )}

          {!agent && !isLoading && (
            <span className="text-slate-600">SmartShop AI — Trợ lý mua sắm thông minh</span>
          )}
        </>
      )}
    </div>
  );
}
