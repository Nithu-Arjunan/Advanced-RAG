interface DebugFooterProps {
  cacheTier: string;
  embeddingModel: string;
  chunksRetrieved: number;
  responseTimeMs: number | null;
}

export default function DebugFooter({ cacheTier, embeddingModel, chunksRetrieved, responseTimeMs }: DebugFooterProps) {
  return (
    <footer className="rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-xs text-slate-700 shadow-soft dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200">
      <div className="grid gap-2 md:grid-cols-4">
        <p>Cache Tier: <span className="font-semibold">{cacheTier}</span></p>
        <p>Embedding Model: <span className="font-semibold">{embeddingModel}</span></p>
        <p>Chunks Retrieved: <span className="font-semibold">{chunksRetrieved}</span></p>
        <p>Response Time: <span className="font-semibold">{responseTimeMs ?? "-"} ms</span></p>
      </div>
    </footer>
  );
}