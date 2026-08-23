import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, BASE } from '../api/client'

interface Skill {
  name: string
  description: string
  source: string
}

interface StreamEvent {
  type: 'event' | 'done' | 'error'
  node?: { node_type: string; status?: string; name?: string; text?: string; reason?: string; tool?: string }
  trace_id?: string
  message?: string
}

const AGENTS = ['build', 'explore', 'plan', 'general']

const statusColor: Record<string, string> = {
  running: 'text-wait',
  completed: 'text-ok',
  error: 'text-bad',
  skipped: 'text-faint',
}

export default function RunPage() {
  const navigate = useNavigate()
  const [skills, setSkills] = useState<Skill[]>([])
  const [skillName, setSkillName] = useState('')
  const [agentName, setAgentName] = useState('build')
  const [cwd, setCwd] = useState('')
  const [auto, setAuto] = useState(true)
  const [prompt, setPrompt] = useState('')
  const [events, setEvents] = useState<StreamEvent['node'][]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<{ skills: Skill[] }>('/api/runner/skills')
      .then((b) => setSkills(b.skills))
      .catch(() => setSkills([]))
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!prompt.trim()) return
    setRunning(true)
    setEvents([])
    setError(null)

    const task =
      skillName && skillName !== '__none__'
        ? `Use the ${skillName} skill to complete the following task. ${prompt}`
        : prompt

    let resp: Response
    try {
      resp = await fetch(`${BASE}/api/runner/run/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: 'opencode',
          task,
          skill_name: skillName && skillName !== '__none__' ? skillName : null,
          cwd: cwd || null,
          auto,
          agent_name: agentName,
        }),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败')
      setRunning(false)
      return
    }

    if (!resp.ok || !resp.body) {
      setError(`HTTP ${resp.status}`)
      setRunning(false)
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    async function processStream() {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let idx: number
        while ((idx = buffer.indexOf('\n\n')) >= 0) {
          const frame = buffer.slice(0, idx).trim()
          buffer = buffer.slice(idx + 2)
          if (!frame.startsWith('data: ')) continue
          let data: StreamEvent
          try {
            data = JSON.parse(frame.slice(6))
          } catch {
            continue
          }
          if (data.type === 'event' && data.node) {
            setEvents((prev) => [...prev, data.node!])
          } else if (data.type === 'done' && data.trace_id) {
            setRunning(false)
            navigate(`/traces/${data.trace_id}`)
            return
          } else if (data.type === 'error') {
            setError(data.message ?? '运行失败')
            setRunning(false)
            return
          }
        }
      }
      setRunning(false)
    }

    processStream()
  }

  const eventLabel = (n: StreamEvent['node']): string => {
    if (!n) return ''
    if (n.node_type === 'tool_call') return n.name ?? n.tool ?? 'tool'
    if (n.node_type === 'message') return n.text ?? 'message'
    return n.node_type
  }

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">运行 Skill</h2>
          <p className="text-sm text-muted">通过 opencode CLI 运行并抓取 Trace</p>
        </div>
        <button
          type="submit"
          form="run-form"
          disabled={running || !prompt.trim()}
          className="rounded-md bg-accent px-3 py-1.5 text-sm text-white hover:opacity-90 disabled:opacity-50"
        >
          {running ? '运行中…' : '运行'}
        </button>
      </div>

      <form
        id="run-form"
        onSubmit={submit}
        className="mb-6 grid grid-cols-2 gap-3 rounded-xl border border-line bg-surface p-4"
      >
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">Skill</span>
          <select
            value={skillName}
            onChange={(e) => setSkillName(e.target.value)}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          >
            <option value="__none__">（无 / 普通 prompt）</option>
            {skills.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">Agent</span>
          <select
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          >
            {AGENTS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        <label className="col-span-2 flex flex-col gap-1 text-sm">
          <span className="text-muted">工作目录</span>
          <input
            placeholder="E:\playground\my-project（留空则用后端 cwd）"
            value={cwd}
            onChange={(e) => setCwd(e.target.value)}
            className="rounded-md border border-line px-3 py-1.5 text-sm"
          />
        </label>
        <label className="col-span-2 flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={auto}
            onChange={(e) => setAuto(e.target.checked)}
            className="h-4 w-4"
          />
          <span>自动批准工具执行（--auto）</span>
          {auto && <span className="text-xs text-bad">⚠ 将自动执行所有工具，请确认工作目录安全</span>}
        </label>
        <textarea
          required
          placeholder="输入要执行的 prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          className="col-span-2 rounded-md border border-line px-3 py-1.5 text-sm font-mono"
        />
      </form>

      {skillName && skillName !== '__none__' && (
        <p className="mb-4 text-xs text-muted">
          提示：opencode skill 由模型按需自动触发，无法强制。所选 skill 的引导语会注入 prompt
          以提高命中。
        </p>
      )}

      {error && (
        <div className="mb-4 rounded-md border border-bad bg-bad/5 px-3 py-2 text-sm text-bad">{error}</div>
      )}

      {(events.length > 0 || running) && (
        <div className="rounded-xl border border-line bg-surface p-4">
          <p className="mb-3 text-sm font-medium text-muted">实时事件流</p>
          <ul className="flex flex-col gap-1.5 text-sm">
            {events.map((n, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="tabular-nums text-faint">{String(i + 1).padStart(2, '0')}</span>
                <span className="font-mono text-muted">{n?.node_type}</span>
                <span className={statusColor[n?.status ?? ''] ?? 'text-ink'}>
                  {eventLabel(n)}
                </span>
              </li>
            ))}
            {running && <li className="text-wait">等待事件…</li>}
          </ul>
        </div>
      )}
    </div>
  )
}
