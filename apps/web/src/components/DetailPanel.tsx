import type { Row } from '../utils/trace'
import { statusLabel } from '../utils/labels'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-line py-3 first:border-t-0">
      <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-faint">{title}</h4>
      {children}
    </div>
  )
}

function Code({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="text-faint">—</span>
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  return (
    <pre className="max-h-64 overflow-auto rounded-md bg-canvas p-2 text-xs text-ink whitespace-pre-wrap">
      {text}
    </pre>
  )
}

export default function DetailPanel({ row }: { row: Row | null }) {
  if (!row) {
    return (
      <div className="p-4 text-sm text-faint">
        选择一个节点查看详情
      </div>
    )
  }
  const dur = row.duration_ms != null ? `${(row.duration_ms / 1000).toFixed(2)}s` : '—'
  return (
    <div className="p-4 text-sm" data-testid="detail-panel">
      <div className="flex items-center gap-2">
        <span
          className="h-2 w-2 rounded-full"
          style={{ background: row.status === 'completed' ? 'var(--color-ok)' : row.status === 'error' ? 'var(--color-bad)' : 'var(--color-faint)' }}
        />
        <span className="font-medium">{row.name}</span>
      </div>
      <p className="mt-1 text-xs text-muted">
        {row.type} · {statusLabel(row.status)} · {dur}
        {row.error ? ` · ${row.error.message}` : ''}
      </p>

      {row.tool && (
        <>
          <Section title="Tool">
            <p className="mb-1 text-xs text-muted">{row.tool.name}</p>
          </Section>
          <Section title="Args">
            <Code value={row.tool.args} />
          </Section>
          <Section title="Result">
            <Code value={row.tool.result} />
          </Section>
        </>
      )}
      {row.llm && (
        <Section title="LLM">
          <p className="text-xs text-muted">
            {row.llm.model ?? '—'} · in {row.llm.input_tokens ?? '—'} · out{' '}
            {row.llm.output_tokens ?? '—'} · ${row.llm.cost_usd?.toFixed(4) ?? '—'}
          </p>
        </Section>
      )}
      {row.error && (
        <Section title="Error">
          <p className="text-xs text-bad">{row.error.message}</p>
        </Section>
      )}
      {row.input !== null && row.input !== undefined && (
        <Section title="Input">
          <Code value={row.input} />
        </Section>
      )}
      {row.output !== null && row.output !== undefined && (
        <Section title="Output">
          <Code value={row.output} />
        </Section>
      )}
    </div>
  )
}
