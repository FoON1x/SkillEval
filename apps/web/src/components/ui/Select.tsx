import { type SelectHTMLAttributes } from 'react'
export default function Select({ className = '', children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select {...rest} className={`w-full appearance-none rounded-md border border-line-strong bg-surface px-3 py-1.5 pr-8 text-sm text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-soft ${className}`} style={{ backgroundImage: "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5'><path d='M6 9l6 6 6-6'/></svg>\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}>
      {children}
    </select>
  )
}