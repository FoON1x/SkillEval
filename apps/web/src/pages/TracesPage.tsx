import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Badge, EmptyState, Select, Spinner } from '../components/ui'

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

const statusTone: Record<string, 'ok' | 'bad' | 'wait' | 'skip' | 'neutral'> = {
  completed: 'ok',
  running: 'wait',
  error: 'bad',
  skipped: 'skip',
}

export default function TracesPage() {
  const [items, setItems] = useState<TraceSummary[]>([])
  const [total, setTotal] = useState(0)
  const [agent, setAgent] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
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
      .finally(() => setLoading(false))
  }, [agent, status])

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">运行记录</h2>
          <p className="text-sm text-muted">共 {total} 条运行记录</p>
        </div>
        <div className="flex gap-3">
          <Select value={agent} onChange={(e) => setAgent(e.target.value)} className="w-36">
            <option value="">全部 Agent</option>
            <option value="opencode">opencode</option>
            <option value="codex">codex</option>
            <option value="claude-code">claude-code</option>
            <option value="pi">pi</option>
          </Select>
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-32">
            <option value="">全部状态</option>
            <option value="completed">completed</option>
            <option value="running">running</option>
            <option value="error">error</option>
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16 text-muted">
          <Spinner size={24} />
        </div>
      ) : items.length === 0 ? (
        <EmptyState title="暂无 Trace" description="可通过 POST /api/ingest/import 或 POST /api/ingest/push 导入。" />
      ) : (
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
                    <Badge tone={statusTone[t.status] ?? 'neutral'}>{t.status}</Badge>
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
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}