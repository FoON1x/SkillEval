import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Badge, Card, EmptyState } from '../components/ui'
import { resultLabel } from '../utils/labels'

interface EvalRun {
  id: string
  test_case_id: string
  trace_id: string
  rule: string
  result: string
  score: number | null
  details: Record<string, unknown>
  created_at: string
}

const resultTone: Record<string, 'ok' | 'bad' | 'wait' | 'skip'> = {
  passed: 'ok',
  failed: 'bad',
  review: 'wait',
  error: 'skip',
}

export default function EvalRunsPage() {
  const [items, setItems] = useState<EvalRun[]>([])
  const [openId, setOpenId] = useState<string | null>(null)

  useEffect(() => {
    api.get<{ items: EvalRun[] }>('/api/eval-runs?limit=100').then((b) => setItems(b.items)).catch(() => setItems([]))
  }, [])

  return (
    <div className="mx-auto max-w-5xl p-8">
      <h2 className="mb-1 text-2xl font-semibold tracking-tight">评测记录</h2>
      <p className="mb-6 text-sm text-muted">{items.length} 条评测记录（规则评测与 LLM 评测）</p>

      <div className="flex flex-col gap-3">
        {items.map((run) => (
          <Card key={run.id}>
            <button className="flex w-full items-center justify-between text-left" onClick={() => setOpenId(openId === run.id ? null : run.id)}>
              <div className="flex items-center gap-3">
                <Badge tone={resultTone[run.result] ?? 'skip'}>{resultLabel(run.result)}</Badge>
                <Badge tone="neutral">{run.rule}</Badge>
                {run.score != null && (
                  <span className="text-sm tabular-nums text-muted">score {run.score.toFixed(2)}</span>
                )}
              </div>
              <span className="text-xs text-faint">
                {new Date(run.created_at).toLocaleString()} · trace {run.trace_id.slice(0, 8)} · case {run.test_case_id.slice(0, 8)}
              </span>
            </button>
            {openId === run.id && (
              <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-canvas p-3 text-xs whitespace-pre-wrap" data-testid="run-details">
                {JSON.stringify(run.details, null, 2)}
              </pre>
            )}
          </Card>
        ))}
        {items.length === 0 && <EmptyState title="暂无评测记录。" />}
      </div>
    </div>
  )
}
