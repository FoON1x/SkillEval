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

function mockFetch(sseFrames: string[], skills = [{ name: 'xlsx', description: 'spreadsheet', source: 'a' }]) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (String(url).includes('/api/runner/skills') && (!init || init.method === undefined)) {
      return new Response(JSON.stringify({ skills }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    if (String(url).includes('/api/runner/run/stream')) {
      const stream = new ReadableStream({
        start(controller) {
          const encoder = new TextEncoder()
          for (const frame of sseFrames) {
            controller.enqueue(encoder.encode(frame))
          }
          controller.close()
        },
      })
      return new Response(stream, {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      })
    }
    return new Response('not found', { status: 404 })
  })
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
})
