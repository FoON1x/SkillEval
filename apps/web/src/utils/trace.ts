export interface NodeLike {
  id: string
  parent_id: string | null
  type: string
  name: string
  summary?: string | null
  status: string
  started_at?: string | null
  ended_at?: string | null
  duration_ms?: number | null
  input?: unknown
  output?: unknown
  tool?: { name: string; args?: unknown; result?: unknown } | null
  llm?: { model?: string | null; input_tokens?: number | null; output_tokens?: number | null; total_tokens?: number | null; cost_usd?: number | null; latency_ms?: number | null } | null
  error?: { message: string; kind?: string | null } | null
  children: NodeLike[]
  extra?: Record<string, unknown>
}

export interface Row extends NodeLike {
  depth: number
}

export interface TraceLike {
  id: string
  agent: string
  skill_name?: string | null
  session_id?: string | null
  status: string
  started_at?: string | null
  ended_at?: string | null
  usage?: {
    input_tokens?: number | null
    output_tokens?: number | null
    total_tokens?: number | null
    cost_usd?: number | null
    latency_ms?: number | null
    models?: string[]
  } | null
  error?: { message: string; kind?: string | null } | null
  root: NodeLike
}

export function flattenTree(root: NodeLike): Row[] {
  const rows: Row[] = []
  const walk = (node: NodeLike, depth: number) => {
    rows.push({ ...node, depth })
    for (const child of node.children) walk(child, depth + 1)
  }
  walk(root, 0)
  return rows
}

export interface TimelineSegment {
  id: string
  name: string
  type: string
  status: string
  startMs: number
  durationMs: number
  depth: number
}

export function buildTimeline(root: NodeLike): TimelineSegment[] {
  const raw: TimelineSegment[] = []
  for (const row of flattenTree(root)) {
    if (row.started_at && row.duration_ms != null) {
      raw.push({
        id: row.id,
        name: row.tool?.name ?? row.name,
        type: row.type,
        status: row.status,
        startMs: new Date(row.started_at).getTime(),
        durationMs: row.duration_ms,
        depth: row.depth,
      })
    }
  }
  if (raw.length === 0) return []
  const base = Math.min(...raw.map((s) => s.startMs))
  return raw.map((s) => ({ ...s, startMs: s.startMs - base })).sort((a, b) => a.startMs - b.startMs)
}

export interface TraceStats {
  toolCount: number
  stepCount: number
  errorCount: number
  totalTokens: number | null
  costUsd: number | null
  latencyMs: number | null
}

export function traceStats(trace: TraceLike): TraceStats {
  const rows = flattenTree(trace.root)
  const llms = rows.flatMap((r) => (r.llm ? [r.llm] : []))
  const sum = (pick: (u: { total_tokens?: number | null; cost_usd?: number | null; latency_ms?: number | null }) => number | null | undefined): number | null => {
    const values = llms.map(pick).filter((v): v is number => typeof v === 'number')
    return values.length > 0 ? values.reduce((a, b) => a + b, 0) : null
  }
  return {
    toolCount: rows.filter((r) => r.type === 'tool_call').length,
    stepCount: rows.filter((r) => r.type === 'agent_step' || r.type === 'sub_agent').length,
    errorCount: rows.filter((r) => r.status === 'error').length,
    totalTokens: trace.usage?.total_tokens ?? sum((u) => u.total_tokens),
    costUsd: trace.usage?.cost_usd ?? sum((u) => u.cost_usd),
    latencyMs: trace.usage?.latency_ms ?? sum((u) => u.latency_ms),
  }
}

export function nodeTitle(row: Row): string {
  if (row.type === 'tool_call') return row.tool?.name ?? row.name
  if (row.type === 'llm_call') return row.llm?.model ?? row.name
  return row.name
}

export function statusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'var(--color-ok)'
    case 'error':
      return 'var(--color-bad)'
    case 'running':
      return 'var(--color-wait)'
    default:
      return 'var(--color-skip)'
  }
}
