import { createContext, useContext } from 'react'

export type ThemeMode = 'light' | 'dark' | 'system'
export type Resolved = 'light' | 'dark'

export interface ThemeCtx {
  mode: ThemeMode
  setMode: (m: ThemeMode) => void
  resolved: Resolved
}

export const ThemeContext = createContext<ThemeCtx | null>(null)

export function useTheme(): ThemeCtx {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}

export function resolveMode(m: ThemeMode): Resolved {
  if (m !== 'system') return m
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}
