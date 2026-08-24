import { useEffect, useState, useCallback, type ReactNode } from 'react'
import { ThemeContext, type ThemeMode, type Resolved, resolveMode } from './useTheme'

const STORAGE_KEY = 'skilleval-theme'

export default function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
    return saved ?? 'system'
  })
  const [resolved, setResolved] = useState<Resolved>(() => resolveMode('system'))

  useEffect(() => {
    const r = resolveMode(mode)
    setResolved(r)
    document.documentElement.classList.toggle('dark', r === 'dark')
  }, [mode])

  useEffect(() => {
    if (mode !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      const r = resolveMode('system')
      setResolved(r)
      document.documentElement.classList.toggle('dark', r === 'dark')
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [mode])

  const setMode = useCallback((m: ThemeMode) => {
    localStorage.setItem(STORAGE_KEY, m)
    setModeState(m)
  }, [])

  return <ThemeContext.Provider value={{ mode, setMode, resolved }}>{children}</ThemeContext.Provider>
}
