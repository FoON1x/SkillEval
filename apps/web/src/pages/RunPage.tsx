import { FormEvent, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, postStream } from '../api/client'
import { Button, Card, Field, Input, Modal, Select, Spinner, Textarea } from '../components/ui'
import { Model, groupByProvider, buildModelId } from '../utils/models'

interface FsEntry {
  name: string
  type: 'dir' | 'file'
  path: string
}

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
  const [models, setModels] = useState<Model[]>([])
  const [provider, setProvider] = useState('')
  const [modelId, setModelId] = useState('')
  const [cwd, setCwd] = useState('')
  const [auto, setAuto] = useState(true)
  const [prompt, setPrompt] = useState('')
  const [events, setEvents] = useState<StreamEvent['node'][]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [browseOpen, setBrowseOpen] = useState(false)
  const [browsePath, setBrowsePath] = useState('')
  const [entries, setEntries] = useState<FsEntry[]>([])
  const [browseLoading, setBrowseLoading] = useState(false)
  const [browseError, setBrowseError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    api
      .get<{ skills: Skill[] }>('/api/runner/skills')
      .then((b) => setSkills(b.skills))
      .catch(() => setSkills([]))
    api
      .get<{ models: Model[] }>('/api/runner/models')
      .then((b) => setModels(b.models))
      .catch(() => setModels([]))
    return () => {
      abortRef.current?.abort()
    }
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
    const model = provider && modelId ? buildModelId(provider, modelId) : null

    const ctrl = new AbortController()
    abortRef.current = ctrl

    try {
      await postStream(
        '/api/runner/run/stream',
        {
          agent: 'opencode',
          task,
          skill_name: skillName && skillName !== '__none__' ? skillName : null,
          cwd: cwd || null,
          auto,
          agent_name: agentName,
          model,
        },
        {
          onEvent: (n) => setEvents((prev) => [...prev, n as StreamEvent['node']]),
          onDone: (id) => {
            setRunning(false)
            navigate(`/traces/${id}`)
          },
          onError: (m) => {
            setError(m)
            setRunning(false)
          },
          signal: ctrl.signal,
        },
      )
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      setError(err instanceof Error ? err.message : '请求失败')
    } finally {
      setRunning(false)
      abortRef.current = null
    }
  }

  async function loadDir(path: string | null) {
    setBrowseLoading(true)
    setBrowseError(null)
    try {
      const b = await api.get<{ path: string; entries: FsEntry[] }>(
        '/api/fs/browse' + (path ? `?path=${encodeURIComponent(path)}` : ''),
      )
      setBrowsePath(b.path)
      setEntries(b.entries)
    } catch {
      setBrowseError('无法读取该目录')
    } finally {
      setBrowseLoading(false)
    }
  }

  function openBrowse() {
    setBrowseOpen(true)
    loadDir(cwd || null)
  }

  function enterDir(path: string) {
    loadDir(path)
  }

  function crumbTo(path: string) {
    loadDir(path)
  }

  function confirmBrowse() {
    setCwd(browsePath)
    setBrowseOpen(false)
  }

  function closeBrowse() {
    setBrowseOpen(false)
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
          <p className="text-sm text-muted">通过 opencode CLI 运行并实时抓取 Trace</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="submit"
            form="run-form"
            loading={running}
            disabled={!prompt.trim()}
          >
            {running ? '运行中…' : '运行'}
          </Button>
          {running && (
            <Button variant="ghost" onClick={() => abortRef.current?.abort()}>停止</Button>
          )}
        </div>
      </div>

      <Card className="mb-6">
        <form id="run-form" onSubmit={submit} className="grid grid-cols-2 gap-3">
          <Field label="Skill" optional htmlFor="run-skill">
            <Select
              id="run-skill"
              value={skillName}
              onChange={(e) => setSkillName(e.target.value)}
              className="w-full"
            >
              <option value="__none__">（无 / 普通 Prompt）</option>
              {skills.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Agent" htmlFor="run-agent">
            <Select
              id="run-agent"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full"
            >
              {AGENTS.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="提供商" htmlFor="run-provider">
            <Select
              id="run-provider"
              value={provider}
              onChange={(e) => {
                setProvider(e.target.value)
                setModelId('')
              }}
              className="w-full"
            >
              <option value="">默认（由 opencode 决定）</option>
              {Object.keys(groupByProvider(models)).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="模型" htmlFor="run-model">
            <Select
              id="run-model"
              value={modelId}
              disabled={!provider || !groupByProvider(models)[provider]?.length}
              onChange={(e) => setModelId(e.target.value)}
              className="w-full"
            >
              {!provider || !groupByProvider(models)[provider]?.length ? (
                <option value="">选择提供商</option>
              ) : (
                <option value="">默认（由 opencode 决定）</option>
              )}
              {(groupByProvider(models)[provider] ?? []).map((m) => (
                <option key={m.id} value={m.model}>
                  {m.model}
                </option>
              ))}
            </Select>
          </Field>
          <div className="col-span-2">
            <Field label="工作目录" htmlFor="run-cwd">
              <div className="flex items-center gap-2">
                <Input
                  id="run-cwd"
                  placeholder="E:\playground\my-project（留空则用后端 cwd）"
                  value={cwd}
                  onChange={(e) => setCwd(e.target.value)}
                />
                <Button variant="ghost" onClick={openBrowse}>浏览</Button>
              </div>
            </Field>
          </div>
          <div className="col-span-2">
            <Field label="自动批准工具执行（--auto）" htmlFor="run-auto">
              <div className="flex items-center gap-2">
                <input
                  id="run-auto"
                  type="checkbox"
                  checked={auto}
                  onChange={(e) => setAuto(e.target.checked)}
                  className="h-4 w-4"
                />
                {auto && <span className="text-xs text-bad">⚠ 将自动执行所有工具，请确认工作目录安全</span>}
              </div>
            </Field>
          </div>
          <div className="col-span-2">
            <Textarea
              required
              placeholder="输入要执行的 Prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              className="font-mono"
            />
          </div>
        </form>
      </Card>

      {skillName && skillName !== '__none__' && (
        <p className="mb-4 text-xs text-muted">
          提示：opencode skill 由模型按需自动触发，无法强制。所选 skill 的引导语会注入 Prompt 以提高命中。
        </p>
      )}

      {error && (
        <div className="mb-4 rounded-md border border-bad bg-bad/5 px-3 py-2 text-sm text-bad">{error}</div>
      )}

      {(events.length > 0 || running) && (
        <Card>
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
        </Card>
      )}

      <Modal
        open={browseOpen}
        onClose={closeBrowse}
        title="选择工作目录"
        footer={
          <>
            <Button variant="ghost" onClick={closeBrowse}>取消</Button>
            <Button variant="primary" disabled={!browsePath} onClick={confirmBrowse}>选择此目录</Button>
          </>
        }
      >
        {browseLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : browseError ? (
          <div className="flex flex-col items-center gap-3 px-4 py-8">
            <p className="text-sm text-bad">{browseError}</p>
            <Button variant="ghost" onClick={() => loadDir(browsePath || null)}>重试</Button>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-1 border-b border-line px-4 py-2 text-sm">
              {(() => {
                const sep = browsePath.includes('\\') ? '\\' : '/'
                const posix = browsePath.startsWith('/')
                const parts = browsePath.split(/[\\/]/).filter((s) => s.length > 0)
                const crumbs: { label: string; path: string }[] = []
                if (posix) crumbs.push({ label: '/', path: '/' })
                let acc = ''
                parts.forEach((part, i) => {
                  acc = i === 0 ? (posix ? `/${part}` : part) : `${acc}${sep}${part}`
                  crumbs.push({ label: part, path: acc })
                })
                return crumbs.map((c, i) => (
                  <span key={i} className="flex items-center gap-1">
                    {i > 0 && crumbs[i - 1].label !== '/' && <span className="text-faint">{sep}</span>}
                    {i === crumbs.length - 1 ? (
                      <span className="font-semibold text-ink">{c.label}</span>
                    ) : (
                      <button type="button" className="text-muted hover:text-ink" onClick={() => crumbTo(c.path)}>
                        {c.label}
                      </button>
                    )}
                  </span>
                ))
              })()}
            </div>
            {entries.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted">空目录</p>
            ) : (
              <ul>
                {entries.map((e) => (
                  <li key={e.path}>
                    {e.type === 'dir' ? (
                      <button
                        type="button"
                        onClick={() => enterDir(e.path)}
                        className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-ink hover:bg-line/40"
                      >
                        <span aria-hidden="true">📁</span>
                        <span className="truncate">{e.name}</span>
                      </button>
                    ) : (
                      <span className="flex items-center gap-2 px-4 py-2 text-sm text-faint">
                        <span aria-hidden="true">📄</span>
                        <span className="truncate">{e.name}</span>
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </Modal>
    </div>
  )
}
