import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { diffProjections, projectTrace, type DiffItem, type ProjectableNode } from '../utils/diff'
import type { TraceLike } from '../utils/trace'
import { Badge, EmptyState, Select, Spinner } from '../components/ui'

const kindStyle: Record<string, string> = {
  added: 'bg-ok/10 text-ok',
  removed: 'bg-bad/10 text-bad',
  changed: 'bg-wait/10 text-wait',
  common: 'text-muted',
}

const kindLabel: Record<string, string> = {
  added: '+',
  removed: '−',
  changed: '~',
  common: ' ',
}

export default function DiffPage() {
  const [params] = useSearchParams()
  const [traces, setTraces] = useState<{ id: string; skill_name: string | null }[]>([])
  const [from, setFrom] = useState(params.get('from') ?? '')
  const [to, setTo] = useState('')
  const [a, setA] = useState<TraceLike | null>(null)
  const [b, setB] = useState<TraceLike | null>(null)

  useEffect(() => {
    api.get<{ items: { id: string; skill_name: string | null }[] }>('/api/traces?limit=100').then((r) => {
      setTraces(r.items)
      if (r.items.length > 1) setTo(r.items[0].id)
    }).catch(() => setTraces([]))
  }, [])

  useEffect(() => {
    if (!from) {
      setA(null)
      return
    }
    api.get<TraceLike>(`/api/traces/${from}`).then(setA).catch(() => setA(null))
  }, [from])

  useEffect(() => {
    if (!to) {
      setB(null)
      return
    }
    api.get<TraceLike>(`/api/traces/${to}`).then(setB).catch(() => setB(null))
  }, [to])

  const diff = useMemo(() => {
    if (!a || !b) return null
    const items = diffProjections(
      projectTrace(a.root as unknown as ProjectableNode),
      projectTrace(b.root as unknown as ProjectableNode),
    )
    return {
      ...items,
      seqA: projectTrace(a.root as unknown as ProjectableNode).map((x) => x.name),
      seqB: projectTrace(b.root as unknown as ProjectableNode).map((x) => x.name),
    }
  }, [a, b])

  return (
    <div className="mx-auto max-w-5xl p-8">
      <h2 className="mb-6 text-2xl font-semibold tracking-tight">Trace 对比</h2>

      <div className="mb-6 grid grid-cols-2 gap-4">
        <label className="flex flex-col gap-1 text-xs text-muted">
          基线 Trace
          <Select value={from} onChange={(e) => setFrom(e.target.value)}>
            <option value="">选择…</option>
            {traces.map((t) => (
              <option key={t.id} value={t.id}>
                {t.skill_name ?? t.id} ({t.id.slice(0, 8)})
              </option>
            ))}
          </Select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          对比 Trace
          <Select value={to} onChange={(e) => setTo(e.target.value)}>
            <option value="">选择…</option>
            {traces
              .filter((t) => t.id !== from)
              .map((t) => (
                <option key={t.id} value={t.id}>
                  {t.skill_name ?? t.id} ({t.id.slice(0, 8)})
                </option>
              ))}
          </Select>
        </label>
      </div>

      {diff && (
        <div data-testid="diff-view">
          <div className="mb-4 flex flex-wrap gap-2">
            <Badge tone="ok">+{diff.added.length} 新增</Badge>
            <Badge tone="bad">−{diff.removed.length} 删除</Badge>
            <Badge tone="wait">~{diff.changed.length} 参数变化</Badge>
            <Badge tone="skip">顺序{diff.orderChanged ? '有变' : '一致'}</Badge>
          </div>

          <div className="overflow-hidden rounded-xl border border-line bg-surface">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-faint">
                  <th className="w-10 px-3 py-2" />
                  <th className="px-3 py-2">工具</th>
                  <th className="px-3 py-2">基线</th>
                  <th className="px-3 py-2">对比</th>
                </tr>
              </thead>
              <tbody>
                {diff.items.map((item: DiffItem, i) => (
                  <tr key={i} className={`border-b border-line last:border-b-0 ${item.kind === 'common' ? 'text-muted' : 'font-medium'}`}>
                    <td className={`px-3 py-2 text-center ${kindStyle[item.kind]}`}>{kindLabel[item.kind]}</td>
                    <td className="px-3 py-2">{item.name}</td>
                    <td className="px-3 py-2 text-xs text-faint">{item.aIndex != null ? `#${item.aIndex + 1}` : '—'}</td>
                    <td className="px-3 py-2 text-xs text-faint">{item.bIndex != null ? `#${item.bIndex + 1}` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {!diff &&
        ((from && !a) || (to && !b) ? (
          <div className="flex items-center justify-center gap-2 py-16 text-muted">
            <Spinner size={20} />
            <span>{from && !a ? '基线加载中…' : '对比加载中…'}</span>
          </div>
        ) : (
          <EmptyState title="选择两条 Trace 进行对比。" />
        ))}
    </div>
  )
}
