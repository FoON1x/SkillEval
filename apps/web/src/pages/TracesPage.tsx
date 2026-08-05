import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export interface TraceSummary {
  id: string
  agent: string
  skill_name: string | null
  session_id: string | null
  status: string
  started_at: string | null
  ended_at: string | null
  cost_usd: number | null
  total_tokens: number | null
  latency_ms: number | null
  created_at: string
}

const statusBadge: Record<string, string> = {
  completed: 'bg-ok/10 text-ok',
  running: 'bg-wait/10 text-wait',
  error: 'bg-bad/10 text-bad',
  cancelled: 'bg-skip/10 text-faint',
}

export default function TracesPage() {
  const [items, setItems] = useState<TraceSummary[]>([])
  const [total, setTotal] = useState(0)
  const [agent, setAgent] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    const params = new URLSearchParams()
    if (agent) params.set('agent', agent)
    if (status) params.set('status', status)
    api
      .get<{ items: TraceSummary[]; total: number }>(`/api/traces?${params.toString()}`)
      .then((body) => {
        setItems(body.items)
        setTotal(body.total)
      })
      .catch(() => setItems([]))
  }, [agent, status])

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Traces</h2>
          <p className="text-sm text-muted">共 {total} 条运行记录</p>
        </div>
        <div className="flex gap-3">
          <select
            value={agent}
            onChange={(e) => setAgent(e.target.value)}
            className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm"
          >
            <option value="">全部 Agent</option>
            <option value="opencode">opencode</option>
            <option value="codex">codex</option>
            <option value="claude-code">claude-code</option>
            <option value="pi">pi</option>
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm"
          >
            <option value="">全部状态</option>
            <option value="completed">completed</option>
            <option value="running">running</option>
            <option value="error">error</option>
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-line bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-faint">
              <th className="px-4 py-3">Skill</th>
              <th className="px-4 py-3">Agent</th>
              <th className="px-4 py-3">状态</th>
              <th className="px-4 py-3">开始时间</th>
              <th className="px-4 py-3 text-right">Cost</th>
              <th className="px-4 py-3 text-right">Tokens</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id} className="border-b border-line last:border-b-0 hover:bg-canvas">
                <td className="px-4 py-3">
                  <Link to={`/traces/${t.id}`} className="font-medium hover:text-accent">
                    {t.skill_name ?? t.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-muted">{t.agent}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${statusBadge[t.status] ?? 'bg-skip/10 text-faint'}`}>
                    {t.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-muted">
                  {t.started_at ? new Date(t.started_at).toLocaleString() : '—'}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {t.cost_usd != null ? `$${t.cost_usd.toFixed(4)}` : '—'}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {t.total_tokens?.toLocaleString() ?? '—'}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-muted">
                  暂无 Trace。可通过 <code className="rounded bg-canvas px-1">POST /api/ingest/import</code> 或{' '}
                  <code className="rounded bg-canvas px-1">POST /api/ingest/push</code> 导入。
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
