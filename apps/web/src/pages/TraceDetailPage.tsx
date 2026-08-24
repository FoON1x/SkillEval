import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import CostPanel from '../components/CostPanel'
import DetailPanel from '../components/DetailPanel'
import Timeline from '../components/Timeline'
import TraceDag from '../components/TraceDag'
import { flattenTree, type TraceLike } from '../utils/trace'
import { Badge, Button, Card, EmptyState, Spinner } from '../components/ui'

interface JudgeReport {
  score: number
  verdict: string
  summary: string
  findings: string[]
  raw?: string | null
}

const statusTone: Record<string, 'ok' | 'bad' | 'wait' | 'skip' | 'neutral'> = {
  completed: 'ok',
  running: 'wait',
  error: 'bad',
  skipped: 'skip',
}

const verdictTone: Record<string, 'ok' | 'bad' | 'skip'> = {
  pass: 'ok',
  fail: 'bad',
}

export default function TraceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [trace, setTrace] = useState<TraceLike | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [judge, setJudge] = useState<{ kind: string; report: JudgeReport } | null>(null)
  const [judgeBusy, setJudgeBusy] = useState(false)

  useEffect(() => {
    if (!id) return
    setTrace(null)
    setNotFound(false)
    api
      .get<TraceLike>(`/api/traces/${id}`)
      .then((t) => {
        setTrace(t)
        setSelectedId(t.root.id)
      })
      .catch((e: unknown) => {
        if (e instanceof ApiError && e.status === 404) setNotFound(true)
      })
  }, [id])

  const selectedRow = useMemo(
    () => (trace && selectedId ? flattenTree(trace.root).find((r) => r.id === selectedId) ?? null : null),
    [trace, selectedId],
  )

  async function runJudge(kind: 'result' | 'process') {
    setJudgeBusy(true)
    setJudge(null)
    try {
      const body = await api.post<{ report: JudgeReport }>(`/api/judge/${kind}`, { trace_id: id })
      setJudge({ kind, report: body.report })
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : '评测失败'
      setJudge({ kind, report: { score: 0, verdict: 'review', summary: msg, findings: [] } })
    } finally {
      setJudgeBusy(false)
    }
  }

  if (notFound) {
    return (
      <EmptyState
        title="Trace 不存在。"
        action={
          <Link to="/traces" className="text-sm text-accent">
            返回列表
          </Link>
        }
      />
    )
  }
  if (!trace) {
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-muted">
        <Spinner size={20} />
        <span>加载中…</span>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <Link to="/traces" className="text-xs text-muted hover:text-ink">← 运行记录</Link>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">
            {trace.skill_name ?? trace.id.slice(0, 8)}
            <span className="ml-3 rounded-full bg-accent-soft px-2 py-0.5 text-xs font-normal text-accent">
              {trace.agent}
            </span>
            <span className="ml-2">
              <Badge tone={statusTone[trace.status] ?? 'neutral'}>{trace.status}</Badge>
            </span>
          </h2>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/diff?from=${trace.id}`}
            className="inline-flex items-center gap-1.5 rounded-md border border-line-strong px-4 py-1.5 text-sm font-semibold text-muted transition hover:border-ink hover:text-ink"
          >
            Diff 对比
          </Link>
          <Button variant="ghost" onClick={() => runJudge('result')} loading={judgeBusy}>
            LLM 结果级
          </Button>
          <Button variant="ghost" onClick={() => runJudge('process')} loading={judgeBusy}>
            LLM 全过程
          </Button>
        </div>
      </div>

      {judge && (
        <div data-testid="judge-result">
          <Card className="mb-4">
            <div className="flex items-center gap-3">
              <Badge tone={verdictTone[judge.report.verdict] ?? 'skip'}>
                {judge.kind} · {judge.report.verdict} · score {judge.report.score.toFixed(2)}
              </Badge>
              <span className="text-sm text-muted">{judge.report.summary}</span>
            </div>
            {judge.report.findings.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-xs text-muted">
                {judge.report.findings.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}

      <CostPanel trace={trace} />

      <div className="mt-4 grid grid-cols-[1fr_340px] gap-4" style={{ height: 'min(560px, 60vh)' }}>
        <div className="overflow-hidden rounded-xl border border-line bg-surface">
          <TraceDag root={trace.root} onSelect={setSelectedId} />
        </div>
        <div className="overflow-auto rounded-xl border border-line bg-surface">
          <DetailPanel row={selectedRow} />
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-line bg-surface">
        <Timeline root={trace.root} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
    </div>
  )
}