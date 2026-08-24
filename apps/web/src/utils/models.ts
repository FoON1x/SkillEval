export interface Model {
  provider: string
  model: string
  id: string
  context_window?: number | null
  input_cost?: number | null
  output_cost?: number | null
}

export function groupByProvider(models: Model[]): Record<string, Model[]> {
  const g: Record<string, Model[]> = {}
  for (const m of models) (g[m.provider] ??= []).push(m)
  return g
}

export function buildModelId(provider: string, model: string): string {
  return `${provider}/${model}`
}
