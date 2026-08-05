import { describe, expect, it } from 'vitest'
import { buildTimeline, flattenTree, nodeTitle, statusColor, traceStats } from './trace'

const node = (over: Record<string, unknown> = {}): any => ({
  id: 'n1',
  parent_id: null,
  type: 'tool_call',
  name: 'read_file',
  status: 'completed',
  children: [],
  ...over,
})

describe('flattenTree', () => {
  it('walks depth-first with depth', () => {
    const rows = flattenTree(
      node({
        id: 'root',
        type: 'skill_start',
        name: 's',
        children: [
          node({
            id: 'a',
            type: 'agent_step',
            name: 'step',
            children: [node({ id: 't', name: 'grep' })],
          }),
          node({ id: 'b', name: 'bash' }),
        ],
      }),
    )
    expect(rows.map((r) => r.id)).toEqual(['root', 'a', 't', 'b'])
    expect(rows.map((r) => r.depth)).toEqual([0, 1, 2, 1])
  })

  it('handles empty children', () => {
    expect(flattenTree(node())).toHaveLength(1)
  })
})

describe('buildTimeline', () => {
  it('sorts by start time and offsets from earliest', () => {
    const segments = buildTimeline(
      node({
        id: 'root',
        type: 'skill_start',
        name: 's',
        children: [
          node({ id: 't1', started_at: '2026-01-01T00:00:10Z', duration_ms: 100, name: 'later' }),
          node({ id: 't0', started_at: '2026-01-01T00:00:00Z', duration_ms: 50, name: 'earlier' }),
        ],
      }),
    )
    expect(segments.map((s) => s.name)).toEqual(['earlier', 'later'])
    expect(segments[0].startMs).toBe(0)
    expect(segments[1].startMs).toBe(10000)
  })

  it('skips nodes without timing', () => {
    const segments = buildTimeline(node({ id: 'x', name: 'no-time', duration_ms: null }))
    expect(segments).toHaveLength(0)
  })
})

describe('traceStats', () => {
  it('counts tools/steps/errors', () => {
    const stats = traceStats({
      id: 't',
      agent: 'opencode',
      status: 'completed',
      usage: { total_tokens: 100, cost_usd: 0.01, latency_ms: 5000 },
      root: node({
        type: 'skill_start',
        children: [
          node({ type: 'tool_call', name: 'a' }),
          node({ type: 'tool_call', name: 'b' }),
          node({ type: 'agent_step', name: 's', children: [node({ status: 'error', name: 'c' })] }),
        ],
      }),
    })
    expect(stats.toolCount).toBe(3)
    expect(stats.stepCount).toBe(1)
    expect(stats.errorCount).toBe(1)
    expect(stats.totalTokens).toBe(100)
    expect(stats.costUsd).toBe(0.01)
  })

  it('aggregates llm usage from nodes when trace usage is absent', () => {
    const stats = traceStats({
      id: 't',
      agent: 'opencode',
      status: 'completed',
      usage: null,
      root: node({
        type: 'skill_start',
        children: [
          node({ type: 'llm_call', name: 'x', llm: { total_tokens: 150, cost_usd: 0.001, latency_ms: 900 } }),
          node({ type: 'llm_call', name: 'y', llm: { total_tokens: 50, cost_usd: 0.0005 } }),
          node({ type: 'tool_call', name: 'a' }),
        ],
      }),
    })
    expect(stats.totalTokens).toBe(200)
    expect(stats.costUsd).toBe(0.0015)
    expect(stats.latencyMs).toBe(900)
  })

  it('returns nulls when no usage anywhere', () => {
    const stats = traceStats({
      id: 't',
      agent: 'opencode',
      status: 'completed',
      usage: null,
      root: node({ type: 'skill_start', children: [node({ type: 'tool_call', name: 'a' })] }),
    })
    expect(stats.totalTokens).toBeNull()
    expect(stats.costUsd).toBeNull()
  })
})

describe('misc', () => {
  it('nodeTitle prefers tool name', () => {
    expect(nodeTitle(node({ tool: { name: 'bash' } }))).toBe('bash')
  })
  it('statusColor maps all statuses', () => {
    expect(statusColor('completed')).toContain('--color-ok')
    expect(statusColor('error')).toContain('--color-bad')
    expect(statusColor('running')).toContain('--color-wait')
    expect(statusColor('skipped')).toContain('--color-skip')
  })
})
