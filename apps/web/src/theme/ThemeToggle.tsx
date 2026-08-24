import { useTheme, type ThemeMode } from './useTheme'

const OPTIONS: { value: ThemeMode; label: string }[] = [
  { value: 'light', label: '☀ 浅色' },
  { value: 'dark', label: '🌙 深色' },
  { value: 'system', label: '💻 系统' },
]

export default function ThemeToggle() {
  const { mode, setMode } = useTheme()
  return (
    <div className="flex gap-1 rounded-lg border border-line bg-surface-2 p-1">
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => setMode(o.value)}
          className={`flex flex-1 items-center justify-center gap-1 rounded-md px-2 py-1 text-xs ${
            mode === o.value ? 'bg-surface text-ink shadow-sm' : 'text-muted'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}
