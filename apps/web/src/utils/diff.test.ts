import { describe, expect, it } from 'vitest'
import { argsDiff, diffProjection, diffProjections, projectTrace } from './diff'

const ref = (name: string, args?: unknown) => ({ node_id: `n-${name}`, name, args })

describe('projectTrace', () => {
  it('collects tool calls depth-first, skipping skipped', () => {
    const root = {
      id: 'r',
      type: 'skill_start',
      name: 's',
      status: 'completed',
      children: [
        {
          id: 'a',
          type: 'tool_call',
          name: 'a',
          status: 'completed',
          tool: { name: 'a' },
          children: [],
        },
        {
          id: 'b',
          type: 'tool_call',
          name: 'b',
          status: 'skipped',
          tool: { name: 'b' },
          children: [],
        },
      ],
    }
    expect(projectTrace(root).map((x) => x.name)).toEqual(['a'])
  })
})

describe('diffProjection', () => {
  it('common sequences stay common', () => {
    const items = diffProjection([ref('a'), ref('b')], [ref('a'), ref('b')])
    expect(items.map((x) => x.kind)).toEqual(['common', 'common'])
  })

  it('detects added and removed', () => {
    const items = diffProjection([ref('a'), ref('b')], [ref('a'), ref('c')])
    expect(items).toContainEqual({ kind: 'removed', name: 'b', aIndex: 1, bIndex: null })
    expect(items).toContainEqual({ kind: 'added', name: 'c', aIndex: null, bIndex: 1 })
  })

  it('marks changed args', () => {
    const items = diffProjection([ref('a', { x: 1 })], [ref('a', { x: 2 })])
    expect(items[0].kind).toBe('changed')
    expect(items[0].note).toBe('arguments differ')
  })

  it('detects reorder via LCS', () => {
    const items = diffProjection([ref('a'), ref('b'), ref('c')], [ref('b'), ref('a'), ref('c')])
    const kinds = items.map((x) => x.kind)
    expect(kinds).toContain('removed')
    expect(kinds).toContain('added')
    expect(kinds.filter((k) => k === 'common')).toHaveLength(2)
  })
})

describe('argsDiff', () => {
  it('null when equal', () => {
    expect(argsDiff({ a: 1 }, { a: 1 })).toBeNull()
  })
  it('text when different', () => {
    expect(argsDiff({ a: 1 }, { a: 2 })).toBe('arguments differ')
  })
})

describe('diffProjections summary', () => {
  it('summarizes', () => {
    const out = diffProjections([ref('a'), ref('b')], [ref('b'), ref('a')])
    expect(out.added).toEqual(['a'])
    expect(out.removed).toEqual(['a'])
    expect(out.orderChanged).toBe(true)
  })

  it('identical traces have no changes', () => {
    const out = diffProjections([ref('a'), ref('b')], [ref('a'), ref('b')])
    expect(out.added).toEqual([])
    expect(out.removed).toEqual([])
    expect(out.changed).toEqual([])
    expect(out.orderChanged).toBe(false)
  })
})
