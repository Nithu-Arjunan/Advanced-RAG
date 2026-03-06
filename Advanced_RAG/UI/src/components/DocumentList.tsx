import type { UploadedDocument } from "../types/api";

interface DocumentListProps {
  documents: UploadedDocument[];
  selected?: UploadedDocument;
  onSelect: (doc: UploadedDocument) => void;
  onRefresh: () => void;
  disabled?: boolean;
}

function logicalFileName(fileName: string): string {
  if (fileName.length > 33 && fileName[32] === "_") {
    const prefix = fileName.slice(0, 32);
    if (/^[0-9a-fA-F]{32}$/.test(prefix)) {
      return fileName.slice(33);
    }
  }
  return fileName;
}

export default function DocumentList({ documents, selected, onSelect, onRefresh, disabled }: DocumentListProps) {
  const dedupedByLogicalName = new Map<string, UploadedDocument>();
  for (const doc of documents) {
    const key = logicalFileName(doc.file_name);
    const existing = dedupedByLogicalName.get(key);
    if (!existing || doc.uploaded_at > existing.uploaded_at) {
      dedupedByLogicalName.set(key, doc);
    }
  }
  const visibleDocuments = Array.from(dedupedByLogicalName.values());
  const selectedPath = selected?.file_path ?? "";

  return (
    <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Documents</h3>
        <button
          className="rounded-lg border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          type="button"
          disabled={disabled}
          onClick={onRefresh}
        >
          Refresh
        </button>
      </div>
      <select
        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        value={selectedPath}
        disabled={disabled || visibleDocuments.length === 0}
        onChange={(event) => {
          const doc = visibleDocuments.find((d) => d.file_path === event.target.value);
          if (doc) onSelect(doc);
        }}
      >
        {visibleDocuments.length === 0 ? (
          <option value="">No documents uploaded yet</option>
        ) : (
          visibleDocuments.map((doc) => (
            <option key={doc.file_path} value={doc.file_path}>
              {logicalFileName(doc.file_name)}
            </option>
          ))
        )}
      </select>
      {selected && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
          <p className="font-medium">Preview</p>
          <p>{logicalFileName(selected.file_name)}</p>
          <p className="truncate">{selected.file_path}</p>
          <p>{new Date(selected.uploaded_at).toLocaleString()}</p>
        </div>
      )}
    </section>
  );
}
