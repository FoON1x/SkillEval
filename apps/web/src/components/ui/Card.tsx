import { type ReactNode } from 'react'
export default function Card({ title, className = '', children }: { title?: string; className?: string; children: ReactNode }) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-4 shadow-sm ${className}`}>
      {title && <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">{title}</h3>}
      {children}
    </section>
  )
}