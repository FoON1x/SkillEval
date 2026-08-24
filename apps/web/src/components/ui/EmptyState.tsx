import { type ComponentPropsWithoutRef, type ReactNode } from 'react'

interface Props extends ComponentPropsWithoutRef<'div'> {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export default function EmptyState({ icon, title, description, action, ...rest }: Props) {
  return (
    <div {...rest} className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-line bg-surface-2 p-10 text-center">
      {icon && <div className="text-faint">{icon}</div>}
      <p className="text-sm font-medium text-muted">{title}</p>
      {description && <p className="max-w-sm text-xs text-faint">{description}</p>}
      {action}
    </div>
  )
}