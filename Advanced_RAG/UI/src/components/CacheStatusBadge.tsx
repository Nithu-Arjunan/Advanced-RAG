interface CacheStatusBadgeProps {
  cacheHit: boolean;
  cacheTier: string | null;
  latencyMs: number | null;
}

const tierStyle: Record<string, string> = {
  exact: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-200",
  semantic: "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-200",
  retrieval: "bg-sky-100 text-sky-700 dark:bg-sky-900/60 dark:text-sky-200"
};

export default function CacheStatusBadge({ cacheHit, cacheTier, latencyMs }: CacheStatusBadgeProps) {
  if (!cacheHit) {
    return <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-red-700 dark:bg-red-900/50 dark:text-red-200">Cache MISS {latencyMs !== null ? `• ${latencyMs} ms` : ""}</span>;
  }

  const tier = (cacheTier ?? "exact").toLowerCase();
  const style = tierStyle[tier] ?? tierStyle.exact;
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${style}`}>Cache HIT ({tier}) {latencyMs !== null ? `• ${latencyMs} ms` : ""}</span>;
}