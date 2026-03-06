import { useState } from "react";
import type { SourceChunk } from "../types/api";
import ChatMessage from "./ChatMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  cacheHit?: boolean;
  cacheTier?: string | null;
  latencyMs?: number | null;
}

interface ChatWindowProps {
  messages: Message[];
  processing: boolean;
  onSend: (question: string) => Promise<void>;
  onSourceClick: (source: SourceChunk) => void;
}

export default function ChatWindow({ messages, processing, onSend, onSourceClick }: ChatWindowProps) {
  const [question, setQuestion] = useState("");

  const submit = async () => {
    const clean = question.trim();
    if (!clean || processing) return;
    setQuestion("");
    await onSend(clean);
  };

  return (
    <section className="flex h-[calc(100vh-10rem)] flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-3 border-b border-slate-200 pb-3 dark:border-slate-700">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">RAG Chat</h2>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pr-2">
        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}`}
            role={message.role}
            content={message.content}
            sources={message.sources}
            cacheHit={message.cacheHit}
            cacheTier={message.cacheTier}
            latencyMs={message.latencyMs}
            onSourceClick={onSourceClick}
          />
        ))}
        {processing && (
          <div className="mr-auto flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800">
            <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
            Processing request...
          </div>
        )}
      </div>

      <div className="mt-4 flex gap-2 border-t border-slate-200 pt-4 dark:border-slate-700">
        <input
          className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          placeholder="Ask a question..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void submit();
          }}
          disabled={processing}
        />
        <button
          type="button"
          className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          onClick={() => void submit()}
          disabled={processing}
        >
          Send
        </button>
      </div>
    </section>
  );
}