import { useState } from "react";
import type { ChunkingStrategy } from "../types/api";
import ChunkStrategySelector from "./ChunkStrategySelector";

interface FileUploadProps {
  disabled?: boolean;
  onUpload: (file: File) => Promise<void>;
  chunkingStrategy: ChunkingStrategy;
  onStrategyChange: (value: ChunkingStrategy) => void;
}

export default function FileUpload({
  disabled,
  onUpload,
  chunkingStrategy,
  onStrategyChange
}: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  return (
    <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-900">
      <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">File Upload</h3>
      <input
        type="file"
        accept=".pdf,.txt,.md"
        disabled={disabled}
        onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        className="w-full rounded-xl border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-800"
      />
      <ChunkStrategySelector value={chunkingStrategy} onChange={onStrategyChange} />
      <button
        type="button"
        disabled={disabled || !selectedFile}
        className="w-full rounded-xl bg-brand-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-400"
        onClick={() => selectedFile && onUpload(selectedFile)}
      >
        Upload Document
      </button>
    </section>
  );
}
