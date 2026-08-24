import { type ComponentPropsWithoutRef } from 'react'

interface Props extends ComponentPropsWithoutRef<'section'> {
  title?: string
  className?: string
}

export default function Card({ title, className = '', children, ...rest }: Props) {
  return (
    <section {...rest} className={`rounded-xl border border-line bg-surface p-4 shadow-sm ${className}`}>
      {title && <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">{title}</h3>}
      {children}
    </section>
  )
}