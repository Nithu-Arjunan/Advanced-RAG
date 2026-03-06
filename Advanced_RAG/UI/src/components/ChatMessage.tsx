import type { SourceChunk } from "../types/api";
import CacheStatusBadge from "./CacheStatusBadge";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  cacheHit?: boolean;
  cacheTier?: string | null;
  latencyMs?: number | null;
  onSourceClick?: (chunk: SourceChunk) => void;
}

export default function ChatMessage({
  role,
  content,
  sources,
  cacheHit = false,
  cacheTier = null,
  latencyMs = null,
  onSourceClick
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <article className={`max-w-[90%] rounded-2xl border px-4 py-3 shadow-soft ${isUser ? "ml-auto border-brand-200 bg-brand-50 text-slate-800 dark:border-brand-800 dark:bg-slate-800" : "mr-auto border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"}`}>
      <p className="whitespace-pre-wrap text-sm leading-6">{content}</p>
      {!isUser && (
        <div className="mt-3 space-y-2">
          <CacheStatusBadge cacheHit={cacheHit} cacheTier={cacheTier} latencyMs={latencyMs} />
          {sources && sources.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-2 text-xs dark:border-slate-700 dark:bg-slate-800">
              <p className="mb-1 font-semibold">Sources</p>
              <ul className="space-y-1">
                {sources.map((source, index) => (
                  <li key={`${source.id}-${index}`}>
                    <button
                      type="button"
                      className="text-left text-brand-700 hover:underline dark:text-brand-100"
                      onClick={() => onSourceClick?.(source)}
                    >
                      {source.source || "Unknown"} (page {String(source.page ?? "N/A")})
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {latencyMs !== null && <p className="text-xs text-slate-500">Response time: {latencyMs} ms</p>}
        </div>
      )}
    </article>
  );
}