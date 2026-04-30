/**
 * SmartShop AI - API Client
 * Centralized API calls to backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface SentimentResult {
  label: "positive" | "negative" | "neutral";
  score: number;
}

export interface ChatResponse {
  response: string;
  agent_used: "sales_agent" | "support_agent" | "manager_agent";
  sentiment: SentimentResult;
  session_id: string;
  processing_time_ms: number | null;
}

export interface StreamMetaEvent {
  type: "meta";
  agent_used: string;
  sentiment: SentimentResult;
  session_id: string;
}

export interface StreamChunkEvent {
  type: "chunk";
  content: string;
}

export interface StreamDoneEvent {
  type: "done";
}

export interface StreamErrorEvent {
  type: "error";
  content: string;
}

export type StreamEvent =
  | StreamMetaEvent
  | StreamChunkEvent
  | StreamDoneEvent
  | StreamErrorEvent;

/**
 * Gửi tin nhắn chat (non-streaming)
 */
export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, stream: false }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Gửi tin nhắn với SSE streaming
 */
export async function* sendMessageStream(
  message: string,
  sessionId?: string
): AsyncGenerator<StreamEvent> {
  const url = new URL(`${API_BASE}/chat/stream`);
  url.searchParams.set("message", message);
  if (sessionId) url.searchParams.set("session_id", sessionId);

  const res = await fetch(url.toString());
  if (!res.ok || !res.body) {
    throw new Error(`HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6).trim();
        if (data) {
          try {
            yield JSON.parse(data) as StreamEvent;
          } catch {
            console.error("Failed to parse SSE event:", data);
          }
        }
      }
    }
  }
}

/**
 * Health check
 */
export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Backend không khả dụng");
  return res.json();
}
