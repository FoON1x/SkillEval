import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import TracesPage from './TracesPage'

describe('TracesPage', () => {
  let originalFetch: typeof globalThis.fetch
  beforeEach(() => {
    originalFetch = globalThis.fetch
  })
  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  function mockFetch(items: { id: string; agent: string; status: string; skill_name: string | null }[]) {
    globalThis.fetch = vi.fn(async (url: string) => {
      if (String(url).includes('/api/traces')) {
        return new Response(JSON.stringify({ items, total: items.length }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response('not found', { status: 404 })
    }) as unknown as typeof globalThis.fetch
  }

  it('renders the status filter options in Chinese', async () => {
    mockFetch([])
    render(
      <MemoryRouter>
        <TracesPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByRole('option', { name: '已完成' })).toBeInTheDocument())
    expect(screen.getByRole('option', { name: '运行中' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '错误' })).toBeInTheDocument()
  })

  it('renders Badge with Chinese status text for a completed trace', async () => {
    mockFetch([{ id: 't1', agent: 'opencode', status: 'completed', skill_name: 'demo' }])
    render(
      <MemoryRouter>
        <TracesPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('已完成')).toBeInTheDocument())
  })

  it('renders Badge with Chinese status text for a running trace', async () => {
    mockFetch([{ id: 't2', agent: 'opencode', status: 'running', skill_name: null }])
    render(
      <MemoryRouter>
        <TracesPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('运行中')).toBeInTheDocument())
  })
})
