import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

type Tone = 'ok' | 'bad' | 'wait'
interface ToastItem { id: number; msg: string; tone: Tone }
interface ToastApi { toast: (msg: string, tone?: Tone) => void }

const ToastContext = createContext<ToastApi>({ toast: () => {} })
export const useToast = () => useContext(ToastContext)

const TONE_CLASS: Record<Tone, string> = {
  ok: 'border-ok text-ok', bad: 'border-bad text-bad', wait: 'border-wait text-wait',
}

export default function ToastContainer({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const toast = useCallback((msg: string, tone: Tone = 'ok') => {
    const id = Date.now() + Math.random()
    setItems((prev) => [...prev, { id, msg, tone }])
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4000)
  }, [])
  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed right-4 top-4 z-[60] flex flex-col gap-2">
        {items.map((t) => (
          <div key={t.id} className={`rounded-md border bg-surface px-4 py-2 text-sm shadow-md ${TONE_CLASS[t.tone]}`}>
            {t.msg}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
