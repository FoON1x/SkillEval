export interface ToolRefLike {
  node_id: string
  name: string
  args?: unknown
  result?: unknown
}

export interface ProjectableNode {
  id: string
  type: string
  name: string
  status: string
  tool?: { name: string; args?: unknown; result?: unknown } | null
  children: ProjectableNode[]
}

export function projectTrace(root: ProjectableNode): ToolRefLike[] {
  const out: ToolRefLike[] = []
  const walk = (n: ProjectableNode) => {
    if (n.type === 'tool_call' && n.status !== 'skipped') {
      out.push({
        node_id: n.id,
        name: n.tool?.name ?? n.name,
        args: n.tool?.args,
        result: n.tool?.result,
      })
    }
    for (const child of n.children) walk(child)
  }
  walk(root)
  return out
}

export type DiffKind = 'added' | 'removed' | 'changed' | 'common'

export interface DiffItem {
  kind: DiffKind
  name: string
  aIndex: number | null
  bIndex: number | null
  note?: string | null
}

export function argsDiff(a: unknown, b: unknown): string | null {
  const sa = JSON.stringify(a ?? null)
  const sb = JSON.stringify(b ?? null)
  return sa === sb ? null : 'arguments differ'
}

/** LCS-based projection diff: pairwise positions, reorder detection. */
export function diffProjection(a: ToolRefLike[], b: ToolRefLike[]): DiffItem[] {
  const n = a.length
  const m = b.length
  const lcs: number[][] = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] = a[i].name === b[j].name ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }

  const items: DiffItem[] = []
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (a[i].name === b[j].name) {
      const note = argsDiff(a[i].args, b[j].args)
      items.push({ kind: note ? 'changed' : 'common', name: a[i].name, aIndex: i, bIndex: j, note })
      i++
      j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      items.push({ kind: 'removed', name: a[i].name, aIndex: i, bIndex: null })
      i++
    } else {
      items.push({ kind: 'added', name: b[j].name, aIndex: null, bIndex: j })
      j++
    }
  }
  while (i < n) items.push({ kind: 'removed', name: a[i].name, aIndex: i, bIndex: null }), i++
  while (j < m) items.push({ kind: 'added', name: b[j].name, aIndex: null, bIndex: j }), j++
  return items
}

export interface TraceDiff {
  added: string[]
  removed: string[]
  changed: string[]
  orderChanged: boolean
  items: DiffItem[]
}

export function diffProjections(a: ToolRefLike[], b: ToolRefLike[]): TraceDiff {
  const items = diffProjection(a, b)
  const added = items.filter((x) => x.kind === 'added').map((x) => x.name)
  const removed = items.filter((x) => x.kind === 'removed').map((x) => x.name)
  const changed = items.filter((x) => x.kind === 'changed').map((x) => x.name)

  const aSeq = a.map((x) => x.name).join('|')
  const bSeq = b.map((x) => x.name).join('|')
  const orderChanged = aSeq !== bSeq

  return { added, removed, changed, orderChanged, items }
}
