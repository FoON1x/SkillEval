import { FormEvent, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import { Badge, Button, Card, EmptyState, Input, Select, Textarea, useToast } from '../components/ui'
import { resultLabel } from '../utils/labels'

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

const resultTone: Record<string, 'ok' | 'bad' | 'skip'> = {
  passed: 'ok',
  failed: 'bad',
  error: 'skip',
}

export default function TestCasePage() {
  const { toast } = useToast()
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
      toast('已创建用例')
    } catch (err) {
      toast(`操作失败：${err instanceof ApiError ? err.message : 'create failed'}`, 'bad')
    }
  }

  async function runEval(tc: TestCase) {
    setLastRun(null)
    try {
      const list = await api.get<{ items: { id: string }[] }>('/api/traces?limit=1')
      const trace = list.items[0]
      if (!trace) {
        setLastRun({ caseId: tc.id, result: 'error', score: null, error: '无可用 Trace' })
        toast('操作失败：无可用 Trace', 'bad')
        return
      }
      const body = await api.post<{ result: string; score: number }>('/api/eval/run', {
        test_case_id: tc.id,
        trace_id: trace.id,
      })
      setLastRun({ caseId: tc.id, result: body.result, score: body.score })
      toast('评测已触发')
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'eval failed'
      setLastRun({ caseId: tc.id, result: 'error', score: null, error: msg })
      toast(`操作失败：${msg}`, 'bad')
    }
  }

  async function remove(tc: TestCase) {
    try {
      await api.del(`/api/test-cases/${tc.id}`)
      setItems(items.filter((x) => x.id !== tc.id))
      toast('已删除用例')
    } catch (err) {
      toast(`操作失败：${err instanceof ApiError ? err.message : 'delete failed'}`, 'bad')
    }
  }

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">测试用例</h2>
          <p className="text-sm text-muted">{items.length} 个用例</p>
        </div>
        <Button variant={creating ? 'ghost' : 'primary'} onClick={() => setCreating((v) => !v)}>
          {creating ? '取消' : '新建用例'}
        </Button>
      </div>

      {creating && (
        <Card className="mb-6">
          <form onSubmit={submit} className="grid grid-cols-2 gap-3" data-testid="case-form">
            <Input
              required
              placeholder="名称"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <Input
              placeholder="描述"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <Select
              value={form.agent}
              onChange={(e) => setForm({ ...form, agent: e.target.value })}
              className="w-full"
            >
              <option value="opencode">opencode</option>
              <option value="codex">codex</option>
              <option value="claude-code">claude-code</option>
              <option value="pi">pi</option>
            </Select>
            <Select
              value={form.rule}
              onChange={(e) => setForm({ ...form, rule: e.target.value })}
              className="w-full"
            >
              {RULES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </Select>
            <Input
              placeholder="期望工具（逗号分隔）：read_file, grep"
              value={form.toolsText}
              onChange={(e) => setForm({ ...form, toolsText: e.target.value })}
              className="col-span-2"
            />
            <Textarea
              placeholder="自定义断言（每行一个 Python 表达式，可用 projection/actual/expected/trace）"
              value={form.assertionsText}
              onChange={(e) => setForm({ ...form, assertionsText: e.target.value })}
              rows={3}
              className="col-span-2 font-mono"
            />
            <Button type="submit" className="col-span-2 justify-center">
              创建
            </Button>
          </form>
        </Card>
      )}

      <div className="flex flex-col gap-3">
        {items.map((tc) => (
          <Card key={tc.id} data-testid="case-item">
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
                  <Badge data-testid="eval-result" tone={resultTone[lastRun.result] ?? 'skip'}>
                    {resultLabel(lastRun.result)}
                    {lastRun.score != null ? ` · ${lastRun.score.toFixed(2)}` : ''}
                    {lastRun.error ? ` · ${lastRun.error}` : ''}
                  </Badge>
                )}
                <Button variant="ghost" size="sm" onClick={() => runEval(tc)}>
                  运行评测
                </Button>
                <Button variant="danger" size="sm" onClick={() => remove(tc)}>
                  删除
                </Button>
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
          </Card>
        ))}
        {items.length === 0 && !creating && <EmptyState title="暂无用例，点击右上角新建。" />}
      </div>
    </div>
  )
}
