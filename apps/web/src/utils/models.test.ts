import { describe, expect, it } from 'vitest'
import { groupByProvider, buildModelId } from './models'

const MODELS = [
  { provider: 'opencode-go', model: 'glm-5.2', id: 'opencode-go/glm-5.2' },
  { provider: 'opencode-go', model: 'glm-5.2-mini', id: 'opencode-go/glm-5.2-mini' },
  { provider: 'anthropic', model: 'claude-opus-4-6', id: 'anthropic/claude-opus-4-6' },
]

describe('models util', () => {
  it('groups by provider', () => {
    const g = groupByProvider(MODELS)
    expect(Object.keys(g).sort()).toEqual(['anthropic', 'opencode-go'])
    expect(g['opencode-go']).toHaveLength(2)
  })
  it('buildModelId joins provider/model', () => {
    expect(buildModelId('opencode-go', 'glm-5.2')).toBe('opencode-go/glm-5.2')
  })
})
