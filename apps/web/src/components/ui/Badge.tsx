import { type ReactNode } from 'react'
type Tone = 'ok' | 'bad' | 'wait' | 'skip' | 'neutral'
const TONES: Record<Tone, string> = {
  ok: 'bg-ok/10 text-ok', bad: 'bg-bad/10 text-bad', wait: 'bg-wait/10 text-wait',
  skip: 'bg-skip/10 text-skip', neutral: 'bg-surface-2 text-muted',
}
export default function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return <span role="status" className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${TONES[tone]}`}>{children}</span>
}
