import type { SourceChunk } from "../types/api";

interface RetrievalPanelProps {
  chunks: SourceChunk[];
}

export default function RetrievalPanel({ chunks }: RetrievalPanelProps) {
  return (
    <aside className="h-[calc(100vh-10rem)] rounded-2xl border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-3 text-lg font-semibold text-slate-800 dark:text-slate-100">Retrieved Chunks</h2>
      <div className="max-h-[calc(100%-2.5rem)] space-y-3 overflow-y-auto pr-2">
        {chunks.map((chunk, index) => (
          <article key={`${chunk.id}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-slate-700 dark:bg-slate-800">
            <p><span className="font-semibold">Document:</span> {chunk.source || "Unknown"}</p>
            <p><span className="font-semibold">Chunk:</span> {chunk.id || `chunk_${index + 1}`}</p>
            <p><span className="font-semibold">Score:</span> {Number(chunk.score || 0).toFixed(3)}</p>
            <p className="mt-2 line-clamp-6 text-slate-600 dark:text-slate-300">{chunk.chunk_text}</p>
          </article>
        ))}
        {chunks.length === 0 && <p className="text-sm text-slate-500">No chunks retrieved yet.</p>}
      </div>
    </aside>
  );
}