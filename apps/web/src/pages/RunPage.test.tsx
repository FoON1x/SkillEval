import { render, screen, waitFor, act, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import RunPage from './RunPage'

function lastPath() {
  let path = '/run'
  function Tracker() {
    const loc = useLocation()
    path = loc.pathname
    return null
  }
  return { Tracker, get: () => path }
}

function mockFetch(
  sseFrames: string[],
  skills = [{ name: 'xlsx', description: 'spreadsheet', source: 'a' }],
  models: { provider: string; model: string; id: string }[] = [],
  browseByPath: Record<string, { path: string; entries: { name: string; type: string; path: string }[] }> = {},
  pending = false,
  options: { modelsFail?: boolean; modelsStatus?: number } = {},
) {
  const bodies: { url: string; body: unknown }[] = []
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (String(url).includes('/api/runner/skills') && (!init || init.method === undefined)) {
      return new Response(JSON.stringify({ skills }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    if (String(url).includes('/api/runner/models') && (!init || init.method === undefined)) {
      if (options.modelsFail) {
        throw new Error('network error')
      }
      if (options.modelsStatus) {
        return new Response(JSON.stringify({ detail: 'upstream down' }), {
          status: options.modelsStatus,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ models }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    if (String(url).includes('/api/fs/browse')) {
      const parsed = new URL(String(url), 'http://x')
      const p = parsed.searchParams.get('path') ?? ''
      const found = browseByPath[p]
      if (found) {
        return new Response(JSON.stringify(found), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response('not found', { status: 404 })
    }
    if (String(url).includes('/api/runner/run/stream')) {
      if (init?.body) {
        bodies.push({ url: String(url), body: JSON.parse(String(init.body)) })
      }
      const encoder = new TextEncoder()
      let rejectRead: ((reason: unknown) => void) | null = null
      const stream = new ReadableStream({
        start(controller) {
          if (!pending) {
            for (const frame of sseFrames) {
              controller.enqueue(encoder.encode(frame))
            }
            controller.close()
          }
        },
        pull() {
          if (!pending) return
          return new Promise((_, reject) => {
            rejectRead = reject
          })
        },
      })
      init?.signal?.addEventListener('abort', () => {
        rejectRead?.(new DOMException('Aborted', 'AbortError'))
      })
      return new Response(stream, {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      })
    }
    return new Response('not found', { status: 404 })
  })
  ;(fetchMock as unknown as { bodies: { url: string; body: unknown }[] }).bodies = bodies
  return fetchMock
}

const SSE_EVENT_STEP =
  'data: {"type": "event", "node": {"node_type": "agent_step", "status": "running"}}\n\n'
const SSE_EVENT_TOOL =
  'data: {"type": "event", "node": {"node_type": "tool_call", "status": "completed", "name": "bash"}}\n\n'
const SSE_DONE = 'data: {"type": "done", "trace_id": "tr-xyz"}\n\n'
const SSE_ERROR = 'data: {"type": "error", "message": "opencode CLI not available"}\n\n'

describe('RunPage', () => {
  let originalFetch: typeof globalThis.fetch
  beforeEach(() => {
    originalFetch = globalThis.fetch
  })
  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('renders the form and loads skills into the dropdown', async () => {
    globalThis.fetch = mockFetch([]) as unknown as typeof globalThis.fetch
    const { Tracker, get } = lastPath()
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
          <Route path="*" element={<Tracker />} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText(/运行 Skill/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'xlsx' })).toBeInTheDocument()
    })
    expect(get()).toBe('/run')
  })

  it('renders provider→model cascade selects', async () => {
    const models = [
      { provider: 'opencode-go', model: 'glm-5.2', id: 'opencode-go/glm-5.2' },
      { provider: 'anthropic', model: 'claude-opus-4-6', id: 'anthropic/claude-opus-4-6' },
    ]
    globalThis.fetch = mockFetch([], [{ name: 'xlsx', description: 'spreadsheet', source: 'a' }], models) as unknown as typeof globalThis.fetch
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'opencode-go' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'anthropic' })).toBeInTheDocument()
    })
    const modelSelect = screen.getByLabelText('模型') as HTMLSelectElement
    expect(modelSelect).toBeDisabled()
    fireEvent.change(screen.getByLabelText('提供商'), { target: { value: 'opencode-go' } })
    expect(screen.getByRole('option', { name: 'glm-5.2' })).toBeInTheDocument()
    expect(modelSelect).not.toBeDisabled()
  })

  it('renders live events in the stream', async () => {
    globalThis.fetch = mockFetch([SSE_EVENT_STEP, SSE_EVENT_TOOL]) as unknown as typeof globalThis.fetch
    const { Tracker, get } = lastPath()
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
          <Route path="*" element={<Tracker />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: 'xlsx' })).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText(/输入要执行的 Prompt/i), { target: { value: 'list files' } })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /运行/i }))
    })

    await waitFor(() => expect(screen.getByText('bash')).toBeInTheDocument())
    expect(screen.getByText('tool_call')).toBeInTheDocument()
    expect(get()).toBe('/run')
  })

  it('navigates to the trace detail page on done', async () => {
    globalThis.fetch = mockFetch([SSE_EVENT_STEP, SSE_EVENT_TOOL, SSE_DONE]) as unknown as typeof globalThis.fetch
    const { Tracker, get } = lastPath()
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
          <Route path="/traces/:id" element={<Tracker />} />
          <Route path="*" element={<Tracker />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: 'xlsx' })).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText(/输入要执行的 Prompt/i), { target: { value: 'list files' } })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /运行/i }))
    })

    await waitFor(() => expect(get()).toBe('/traces/tr-xyz'))
  })

  it('shows an error message on an error frame', async () => {
    globalThis.fetch = mockFetch([SSE_ERROR]) as unknown as typeof globalThis.fetch
    const { Tracker, get } = lastPath()
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
          <Route path="*" element={<Tracker />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: 'xlsx' })).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText(/输入要执行的 Prompt/i), { target: { value: 'hi' } })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /运行/i }))
    })

    await waitFor(() => expect(screen.getByText(/opencode CLI not available/i)).toBeInTheDocument())
    expect(get()).toBe('/run')
  })

  it('opens the browse modal and fills cwd on select', async () => {
    const browseByPath = {
      '': {
        path: 'C:/demo',
        entries: [
          { name: 'src', type: 'dir', path: 'C:/demo/src' },
          { name: 'a.txt', type: 'file', path: 'C:/demo/a.txt' },
        ],
      },
      'C:/demo/src': {
        path: 'C:/demo/src',
        entries: [{ name: 'b.txt', type: 'file', path: 'C:/demo/src/b.txt' }],
      },
    }
    globalThis.fetch = mockFetch([], [{ name: 'xlsx', description: 'spreadsheet', source: 'a' }], [], browseByPath) as unknown as typeof globalThis.fetch
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: 'xlsx' })).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: '浏览' }))
    await waitFor(() => expect(screen.getByText('src')).toBeInTheDocument())
    expect(screen.getByText('a.txt')).toBeInTheDocument()

    fireEvent.click(screen.getByText('src'))
    await waitFor(() => expect(screen.getByText('b.txt')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: '选择此目录' }))
    expect((screen.getByLabelText('工作目录') as HTMLInputElement).value).toBe('C:/demo/src')
  })

  it('submits the selected provider/model in the request body', async () => {
    const models = [{ provider: 'opencode-go', model: 'glm-5.2', id: 'opencode-go/glm-5.2' }]
    const fetchMock = mockFetch([SSE_DONE], [{ name: 'xlsx', description: 'spreadsheet', source: 'a' }], models)
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
          <Route path="/traces/:id" element={<div />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: 'opencode-go' })).toBeInTheDocument())

    fireEvent.change(screen.getByLabelText('提供商'), { target: { value: 'opencode-go' } })
    fireEvent.change(screen.getByLabelText('模型'), { target: { value: 'glm-5.2' } })
    fireEvent.change(screen.getByPlaceholderText(/输入要执行的 Prompt/i), { target: { value: 'list files' } })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /运行/i }))
    })

    const captured = (fetchMock as unknown as { bodies: { url: string; body: unknown }[] }).bodies
    expect(captured.length).toBe(1)
    expect(captured[0].url).toContain('/api/runner/run/stream')
    expect(captured[0].body).toMatchObject({ model: 'opencode-go/glm-5.2' })
  })

  it('stops a running stream and reverts the button', async () => {
    globalThis.fetch = mockFetch([], undefined, undefined, undefined, true) as unknown as typeof globalThis.fetch
    const { Tracker, get } = lastPath()
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
          <Route path="*" element={<Tracker />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: 'xlsx' })).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText(/输入要执行的 Prompt/i), { target: { value: 'list files' } })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /运行/i }))
    })

    await waitFor(() => expect(screen.getByRole('button', { name: '停止' })).toBeInTheDocument())
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: '停止' }))
    })

    await waitFor(() => expect(screen.getByRole('button', { name: '运行' })).toBeInTheDocument())
    expect(screen.queryByRole('button', { name: '停止' })).not.toBeInTheDocument()
    expect(get()).toBe('/run')
  })

  it('shows a hint when the model list fetch fails', async () => {
    globalThis.fetch = mockFetch(
      [],
      [{ name: 'xlsx', description: 'spreadsheet', source: 'a' }],
      [],
      {},
      false,
      { modelsFail: true },
    ) as unknown as typeof globalThis.fetch
    render(
      <MemoryRouter initialEntries={['/run']}>
        <Routes>
          <Route path="/run" element={<RunPage />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText(/模型列表获取失败/i)).toBeInTheDocument())
  })
})
