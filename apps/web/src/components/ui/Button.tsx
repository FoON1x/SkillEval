import { type ButtonHTMLAttributes, type ReactNode } from 'react'
import Spinner from './Spinner'

type Variant = 'primary' | 'ghost' | 'danger'
type Size = 'sm' | 'md'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  icon?: ReactNode
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-accent text-accent-ink hover:brightness-108 disabled:opacity-50',
  ghost: 'border border-line-strong text-muted hover:text-ink hover:border-ink',
  danger: 'bg-bad text-bad-ink hover:brightness-108 disabled:opacity-50',
}
const SIZES: Record<Size, string> = { sm: 'px-3 py-1 text-xs', md: 'px-4 py-1.5 text-sm' }

export default function Button({ variant = 'primary', size = 'md', loading, icon, className = '', children, disabled, type, ...rest }: Props) {
  return (
    <button
      {...rest}
      type={type ?? 'button'}
      disabled={disabled || loading}
      className={`inline-flex items-center gap-1.5 rounded-md font-semibold transition disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
    >
      {loading ? <Spinner size={size === 'sm' ? 12 : 14} /> : icon}
      {children}
    </button>
  )
}
