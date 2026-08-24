import { type ComponentPropsWithoutRef, type ReactNode } from 'react'

interface Props extends ComponentPropsWithoutRef<'div'> {
  label: string
  hint?: string
  optional?: boolean
  htmlFor?: string
  children: ReactNode
}

export default function Field({ label, hint, optional, htmlFor, children, className = '', ...rest }: Props) {
  return (
    <div {...rest} className={`flex flex-col gap-1 ${className}`}>
      <label htmlFor={htmlFor} className="flex items-center gap-1.5 text-xs font-semibold text-ink">
        {label}{optional && <span className="text-xs font-normal text-faint">可选</span>}
      </label>
      {children}
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </div>
  )
}