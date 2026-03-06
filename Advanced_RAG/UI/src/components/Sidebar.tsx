import type { ChunkingStrategy, IngestResponse, UploadedDocument } from "../types/api";
import DocumentList from "./DocumentList";
import FileUpload from "./FileUpload";

interface SidebarProps {
  username: string;
  chunkingStrategy: ChunkingStrategy;
  onStrategyChange: (value: ChunkingStrategy) => void;
  onUpload: (file: File) => Promise<void>;
  ingestionResult: IngestResponse | null;
  documents: UploadedDocument[];
  selectedDocument?: UploadedDocument;
  onSelectDocument: (doc: UploadedDocument) => void;
  onRefreshDocuments: () => Promise<void>;
  onCacheStatus: () => Promise<void>;
  onClearCache: () => Promise<void>;
  onClearVectorSpace: () => Promise<void>;
  onClearDocuments: () => Promise<void>;
  cacheStats: unknown | null;
  processing: boolean;
}

export default function Sidebar(props: SidebarProps) {
  const {
    username,
    chunkingStrategy,
    onStrategyChange,
    onUpload,
    ingestionResult,
    documents,
    selectedDocument,
    onSelectDocument,
    onRefreshDocuments,
    onCacheStatus,
    onClearCache,
    onClearVectorSpace,
    onClearDocuments,
    cacheStats,
    processing
  } = props;

  const disabled = processing || !username.trim();

  return (
    <aside className="space-y-4">
      <FileUpload
        onUpload={onUpload}
        disabled={disabled}
        chunkingStrategy={chunkingStrategy}
        onStrategyChange={onStrategyChange}
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-900">
        {ingestionResult && (
          <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200">
            <p className="font-semibold">Message: {ingestionResult.message}</p>
            <p>Chunk Strategy: {ingestionResult.strategy}</p>
            <p>Chunks Created: {ingestionResult.chunks}</p>
            <p>Embedding Model: llama-text-embed-v2</p>
          </div>
        )}
      </section>

      <DocumentList
        documents={documents}
        selected={selectedDocument}
        onSelect={onSelectDocument}
        onRefresh={() => void onRefreshDocuments()}
        disabled={disabled}
      />

      <section className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-900">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Admin Tools</h3>
        <button type="button" onClick={() => void onCacheStatus()} disabled={disabled} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-800">Cache Status</button>
        <button type="button" onClick={() => void onClearCache()} disabled={disabled} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-800">Clear Cache</button>
        <button type="button" onClick={() => void onClearVectorSpace()} disabled={disabled} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-800">Clear Vector Space</button>
        <button type="button" onClick={() => void onClearDocuments()} disabled={disabled} className="w-full rounded-xl border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900/20">Clear Documents</button>
        {!!cacheStats && (
          <pre className="max-h-40 overflow-auto rounded-xl border border-slate-200 bg-slate-50 p-2 text-[10px] text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
            {JSON.stringify(cacheStats, null, 2) ?? ""}
          </pre>
        )}
      </section>
    </aside>
  );
}
