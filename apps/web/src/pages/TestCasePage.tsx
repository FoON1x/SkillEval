import { FormEvent, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'

interface TestCase {
  id: string
  name: string
  description: string | null
  agent: string
  rule: string
  input_context: Record<string, unknown> | null
  expected: { tools: string[]; description?: string | null }
  assertions: { code: string; label?: string | null }[]
  created_at: string
}

const RULES = ['strict', 'unordered', 'subset', 'superset']

const emptyForm = {
  name: '',
  description: '',
  agent: 'opencode',
  rule: 'strict',
  toolsText: '',
  assertionsText: '',
}

export default function TestCasePage() {
  const [items, setItems] = useState<TestCase[]>([])
  const [form, setForm] = useState(emptyForm)
  const [creating, setCreating] = useState(false)
  const [lastRun, setLastRun] = useState<{ caseId: string; result: string; score: number | null; error?: string } | null>(null)

  useEffect(() => {
    api
      .get<{ items: TestCase[] }>('/api/test-cases')
      .then((b) => setItems(b.items))
      .catch(() => setItems([]))
  }, [creating])

  async function submit(e: FormEvent) {
    e.preventDefault()
    try {
      await api.post('/api/test-cases', {
        name: form.name,
        description: form.description || null,
        agent: form.agent,
        rule: form.rule,
        expected: { tools: form.toolsText.split(/[,，\s]+/).filter(Boolean) },
        assertions: form.assertionsText
          .split(/\n+/)
          .filter(Boolean)
          .map((code) => ({ code })),
      })
      setForm(emptyForm)
      setCreating(false)
      setItems(
        await api.get<{ items: TestCase[] }>('/api/test-cases').then((b) => b.items),
      )
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'create failed')
    }
  }

  async function runEval(tc: TestCase) {
    setLastRun(null)
    try {
      const list = await api.get<{ items: { id: string }[] }>('/api/traces?limit=1')
      const trace = list.items[0]
      if (!trace) {
        setLastRun({ caseId: tc.id, result: 'error', score: null, error: '无可用 Trace' })
        return
      }
      const body = await api.post<{ result: string; score: number }>('/api/eval/run', {
        test_case_id: tc.id,
        trace_id: trace.id,
      })
      setLastRun({ caseId: tc.id, result: body.result, score: body.score })
    } catch (err) {
      setLastRun({ caseId: tc.id, result: 'error', score: null, error: err instanceof ApiError ? err.message : 'eval failed' })
    }
  }

  async function remove(tc: TestCase) {
    await api.del(`/api/test-cases/${tc.id}`)
    setItems(items.filter((x) => x.id !== tc.id))
  }

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Test Cases</h2>
          <p className="text-sm text-muted">{items.length} 个用例</p>
        </div>
        <button
          onClick={() => setCreating((v) => !v)}
          className="rounded-md bg-accent px-3 py-1.5 text-sm text-white hover:opacity-90"
        >
          {creating ? '取消' : '新建用例'}
        </button>
      </div>

      {creating && (
        <form onSubmit={submit} className="mb-6 grid grid-cols-2 gap-3 rounded-xl border border-line bg-surface p-4" data-testid="case-form">
          <input
            required
            placeholder="名称"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          />
          <input
            placeholder="描述"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          />
          <select
            value={form.agent}
            onChange={(e) => setForm({ ...form, agent: e.target.value })}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          >
            <option value="opencode">opencode</option>
            <option value="codex">codex</option>
            <option value="claude-code">claude-code</option>
            <option value="pi">pi</option>
          </select>
          <select
            value={form.rule}
            onChange={(e) => setForm({ ...form, rule: e.target.value })}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          >
            {RULES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <input
            placeholder="期望工具（逗号分隔）：read_file, grep"
            value={form.toolsText}
            onChange={(e) => setForm({ ...form, toolsText: e.target.value })}
            className="col-span-2 rounded-md border border-line px-3 py-1.5 text-sm"
          />
          <textarea
            placeholder="自定义断言（每行一个 Python 表达式，可用 projection/actual/expected/trace）"
            value={form.assertionsText}
            onChange={(e) => setForm({ ...form, assertionsText: e.target.value })}
            rows={3}
            className="col-span-2 rounded-md border border-line px-3 py-1.5 text-sm font-mono"
          />
          <button type="submit" className="col-span-2 rounded-md bg-ink px-3 py-2 text-sm text-white hover:opacity-90">
            创建
          </button>
        </form>
      )}

      <div className="flex flex-col gap-3">
        {items.map((tc) => (
          <div key={tc.id} className="rounded-xl border border-line bg-surface p-4" data-testid="case-item">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{tc.name}</p>
                <p className="text-xs text-muted">
                  {tc.agent} · rule={tc.rule} · 期望 {tc.expected.tools.join(', ') || '（空）'} ·{' '}
                  {tc.assertions.length} 条断言
                </p>
              </div>
              <div className="flex items-center gap-2">
                {lastRun?.caseId === tc.id && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      lastRun.result === 'passed'
                        ? 'bg-ok/10 text-ok'
                        : lastRun.result === 'failed'
                          ? 'bg-bad/10 text-bad'
                          : 'bg-skip/10 text-faint'
                    }`}
                    data-testid="eval-result"
                  >
                    {lastRun.result}
                    {lastRun.score != null ? ` · ${lastRun.score.toFixed(2)}` : ''}
                    {lastRun.error ? ` · ${lastRun.error}` : ''}
                  </span>
                )}
                <button
                  onClick={() => runEval(tc)}
                  className="rounded-md border border-line px-3 py-1 text-sm hover:border-accent hover:text-accent"
                >
                  运行评测
                </button>
                <button
                  onClick={() => remove(tc)}
                  className="rounded-md border border-line px-2 py-1 text-sm text-muted hover:border-bad hover:text-bad"
                >
                  删除
                </button>
              </div>
            </div>
            {tc.assertions.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {tc.assertions.map((a, i) => (
                  <code key={i} className="rounded bg-canvas px-1.5 py-0.5 text-xs text-muted">
                    {a.code}
                  </code>
                ))}
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && !creating && (
          <p className="py-10 text-center text-muted">暂无用例，点击右上角新建。</p>
        )}
      </div>
    </div>
  )
}
