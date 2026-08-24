import { traceStats, type TraceLike } from '../utils/trace'
import { Card } from './ui'

export default function CostPanel({ trace }: { trace: TraceLike }) {
  const stats = traceStats(trace)
  const hasData = stats.costUsd != null || stats.totalTokens != null || stats.latencyMs != null
  if (!hasData) return null

  return (
    <div className="grid grid-cols-2 gap-2 p-4 sm:grid-cols-4" data-testid="cost-panel">
      <Card>
        <p className="text-xs text-faint">Tokens</p>
        <p className="text-lg font-medium tabular-nums">{stats.totalTokens?.toLocaleString() ?? '—'}</p>
      </Card>
      <Card>
        <p className="text-xs text-faint">Cost</p>
        <p className="text-lg font-medium tabular-nums">{stats.costUsd != null ? `$${stats.costUsd.toFixed(4)}` : '—'}</p>
      </Card>
      <Card>
        <p className="text-xs text-faint">Latency</p>
        <p className="text-lg font-medium tabular-nums">{stats.latencyMs != null ? `${(stats.latencyMs / 1000).toFixed(1)}s` : '—'}</p>
      </Card>
      <Card>
        <p className="text-xs text-faint">Steps</p>
        <p className="text-lg font-medium tabular-nums">{stats.toolCount} 个工具</p>
        <p className="text-xs text-muted">{stats.stepCount} 步 · {stats.errorCount} 错误</p>
      </Card>
    </div>
  )
}
