import type { ChunkingStrategy } from "../types/api";

interface ChunkStrategySelectorProps {
  value: ChunkingStrategy;
  onChange: (value: ChunkingStrategy) => void;
}

export default function ChunkStrategySelector({ value, onChange }: ChunkStrategySelectorProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Chunking Strategy</p>
      <select
        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        value={value}
        onChange={(event) => onChange(event.target.value as ChunkingStrategy)}
      >
        <option value="parent_child">parent_child</option>
        <option value="sentence_window">sentence_window</option>
      </select>
    </div>
  );
}