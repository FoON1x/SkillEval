import { traceStats, type TraceLike } from '../utils/trace'

function Card({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2">
      <p className="text-xs text-faint">{label}</p>
      <p className="text-lg font-medium tabular-nums">{value}</p>
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  )
}

export default function CostPanel({ trace }: { trace: TraceLike }) {
  const stats = traceStats(trace)
  const hasData = stats.costUsd != null || stats.totalTokens != null || stats.latencyMs != null
  if (!hasData) return null

  return (
    <div className="grid grid-cols-2 gap-2 p-4 sm:grid-cols-4" data-testid="cost-panel">
      <Card label="Tokens" value={stats.totalTokens?.toLocaleString() ?? '—'} />
      <Card label="Cost" value={stats.costUsd != null ? `$${stats.costUsd.toFixed(4)}` : '—'} />
      <Card label="Latency" value={stats.latencyMs != null ? `${(stats.latencyMs / 1000).toFixed(1)}s` : '—'} />
      <Card
        label="Steps"
        value={`${stats.toolCount} tools`}
        hint={`${stats.stepCount} steps · ${stats.errorCount} errors`}
      />
    </div>
  )
}
