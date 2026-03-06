import type { SessionStatus } from "../types/api";

interface TopHeaderProps {
  username: string;
  onUsernameChange: (value: string) => void;
  status: SessionStatus;
}

export default function TopHeader({ username, onUsernameChange, status }: TopHeaderProps) {
  return (
    <header className="rounded-2xl border border-slate-200/70 bg-white/85 px-5 py-4 shadow-soft backdrop-blur dark:border-slate-700 dark:bg-slate-900/70">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <label className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
          Username / Namespace
          <input
            className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 outline-none ring-brand-500 transition focus:ring-2 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 md:w-80"
            placeholder="Enter username"
            value={username}
            onChange={(event) => onUsernameChange(event.target.value)}
          />
        </label>
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800">
          Status:{" "}
          <span className={status === "PROCESSING" ? "font-semibold text-amber-500" : "font-semibold text-emerald-500"}>
            {status}
          </span>
        </div>
      </div>
    </header>
  );
}

