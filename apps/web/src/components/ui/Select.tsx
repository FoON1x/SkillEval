import { type SelectHTMLAttributes } from 'react'
const CHEVRON = "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5'><path d='M6 9l6 6 6-6'/></svg>\")"
export default function Select({ className = '', children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative">
      <select {...rest} className={`appearance-none rounded-md border border-line-strong bg-surface px-3 py-1.5 pr-8 text-sm text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-soft ${className}`}>
        {children}
      </select>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute right-2.5 top-1/2 h-3 w-3 -translate-y-1/2 bg-muted"
        style={{
          WebkitMaskImage: CHEVRON,
          WebkitMaskRepeat: 'no-repeat',
          WebkitMaskPosition: 'center',
          WebkitMaskSize: 'contain',
          maskImage: CHEVRON,
          maskRepeat: 'no-repeat',
          maskPosition: 'center',
          maskSize: 'contain',
        }}
      />
    </div>
  )
}
