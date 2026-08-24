# 前端重构 + 模型/提供商选择 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 SkillEval 前端全量重构为统一的中文界面 + slate/靛蓝主题（含深色模式三态切换）+ UI 原语层，并在运行页新增提供商→模型级联选择与路径浏览模态，后端新增两个列举端点。

**Architecture:** 地基优先——先建 `components/ui/` 原语 + `theme/` 主题 token/深色模式 + 文案中文化，再迁移 6 页 + 4 组件到原语上，最后给运行页加级联模型选择、路径模态、SSE 加固。后端新增 `GET /api/runner/models`（shell `opencode models`）与 `GET /api/fs/browse`（目录列举），不改 `RunContext`/`StreamRunRequest` schema。

**Tech Stack:** React 19 / TS / Vite / Tailwind v4（CSS-first `@theme` + `@custom-variant dark`）/ React Flow；FastAPI / Pydantic v2；vitest / pytest；OpenAPI→TS 类型同步。

## Global Constraints

- 文案统一中文；保留产品术语原文：Trace、Skill、Agent、DAG、Token(s)、Cost、Prompt、SSE、CLI。
- 主题 token 命名不变（canvas/surface/surface-2/line/line-strong/ink/muted/faint/accent/accent-ink/accent-soft/accent-border/ok/bad/wait/skip），仅换值为 slate/靛蓝。
- 深色模式用 `@custom-variant dark (&:where(.dark, .dark *));` + `.dark` 下覆盖 token；`<html>` 上 `.dark` 类。
- 不引入 i18n 库、不引入新运行时依赖（除已存在的）。
- 不改 `RunContext`/`StreamRunRequest` 字段（`model` 已存在）；提交时 `model` = `provider/model` 或 `null`。
- 后端测试在 `apps/api` 下运行（`pythonpath=["."]`）；前端测试 `npm test`、类型 `npx tsc -b`。
- OpenAPI→TS 同步手动执行（无 npm 脚本）。
- 注释：除非用户要求，不添加注释（遵循仓库约定）。
- 提交信息中文，格式 `feat(<范围>): <描述>`；提交前请求用户审查（AGENTS.md 约定）。

---

## File Structure

**前端新增**
- `apps/web/src/components/ui/Button.tsx` — 按钮（primary/ghost/danger · loading · icon）
- `apps/web/src/components/ui/Input.tsx` — 文本输入
- `apps/web/src/components/ui/Textarea.tsx` — 多行输入
- `apps/web/src/components/ui/Select.tsx` — 原生 select styled
- `apps/web/src/components/ui/Badge.tsx` — 状态徽章
- `apps/web/src/components/ui/Card.tsx` — 卡片容器
- `apps/web/src/components/ui/Field.tsx` — label+hint+控件包裹
- `apps/web/src/components/ui/Spinner.tsx` — 加载指示
- `apps/web/src/components/ui/EmptyState.tsx` — 空状态
- `apps/web/src/components/ui/Modal.tsx` — 遮罩对话框
- `apps/web/src/components/ui/Toast.tsx` — Toast 容器 + useToast
- `apps/web/src/components/ui/index.ts` — 统一导出
- `apps/web/src/theme/ThemeProvider.tsx` — 三态切换 + 持久化
- `apps/web/src/theme/ThemeToggle.tsx` — 三段开关
- `apps/web/src/theme/useTheme.ts` — hook
- `apps/web/src/utils/models.ts` — 提供商/模型级联过滤纯逻辑

**前端修改**
- `apps/web/src/index.css` — 替换 token 为 slate/靛蓝 + `@custom-variant dark` + `.dark` 覆盖
- `apps/web/src/main.tsx` — 包裹 `ThemeProvider`
- `apps/web/src/App.tsx` — 侧边栏迁移原语 + 中文化 + 挂 `ThemeToggle`
- `apps/web/src/pages/RunPage.tsx` — 迁移 + 新功能（级联/路径/SSE 加固）
- `apps/web/src/pages/TracesPage.tsx`、`TraceDetailPage.tsx`、`TestCasePage.tsx`、`EvalRunsPage.tsx`、`DiffPage.tsx` — 迁移 + 中文化
- `apps/web/src/components/{TraceDag,Timeline,DetailPanel,CostPanel}.tsx` — 迁移 + 中文化
- `apps/web/src/api/client.ts` — 新增 `api.postStream`（SSE + AbortSignal）
- `apps/web/src/pages/RunPage.test.tsx` — 更新新字段 + SSE
- `apps/web/src/components/ui/*.test.tsx` — 原语测试

**后端新增**
- `apps/api/skill_eval/runner/models.py` — `list_models()`（shell `opencode models --verbose`）
- `apps/api/skill_eval/fs.py` — `browse_directory()` + `/api/fs` 路由
- `apps/api/tests/test_fs.py` — fs 测试

**后端修改**
- `apps/api/skill_eval/runner/api.py` — 加 `GET /models` 路由
- `apps/api/skill_eval/app.py` — 挂载 fs 路由
- `apps/api/tests/test_runner.py` — `--model` argv 断言 + models 端点测试

**构建产物（重新生成）**
- `apps/web/openapi.json`、`apps/web/src/api/types.generated.ts`

---

### Task 1: 主题 token + 深色模式基础设施

**Files:**
- Modify: `apps/web/src/index.css`（全量重写 token 块）
- Create: `apps/web/src/theme/ThemeProvider.tsx`
- Create: `apps/web/src/theme/useTheme.ts`
- Create: `apps/web/src/theme/ThemeToggle.tsx`
- Modify: `apps/web/src/main.tsx`（包裹 Provider）
- Test: `apps/web/src/theme/ThemeProvider.test.tsx`

**Interfaces:**
- Produces: `ThemeProvider`（默认导出）、`useTheme()` → `{ mode: 'light'|'dark'|'system', setMode, resolved: 'light'|'dark' }`、`ThemeToggle`（默认导出，放侧边栏）

- [ ] **Step 1: 重写 `index.css` token + dark 变体**

替换 `apps/web/src/index.css` 的 `@theme {...}` 与 `:root` 段为：

```css
@import 'tailwindcss';

@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --color-canvas: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-2: #f1f5f9;
  --color-line: #e2e8f0;
  --color-line-strong: #cbd5e1;
  --color-ink: #0f172a;
  --color-muted: #64748b;
  --color-faint: #94a3b8;
  --color-accent: #6366f1;
  --color-accent-ink: #ffffff;
  --color-accent-soft: #eef2ff;
  --color-accent-border: #c7d2fe;
  --color-ok: #16a34a;
  --color-bad: #dc2626;
  --color-wait: #0ea5e9;
  --color-skip: #94a3b8;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'SF Mono', 'Cascadia Code', Consolas, monospace;
}

:root { color-scheme: light; }

.dark {
  --color-canvas: #0f172a;
  --color-surface: #1e293b;
  --color-surface-2: #0f172a;
  --color-line: #334155;
  --color-line-strong: #475569;
  --color-ink: #f1f5f9;
  --color-muted: #94a3b8;
  --color-faint: #64748b;
  --color-accent: #818cf8;
  --color-accent-ink: #0f172a;
  --color-accent-soft: #1e1b4b;
  --color-accent-border: #3730a3;
  --color-ok: #4ade80;
  --color-bad: #f87171;
  --color-wait: #38bdf8;
  --color-skip: #64748b;
  color-scheme: dark;
}

body {
  background: var(--color-canvas);
  color: var(--color-ink);
  font-family: var(--font-sans);
}
```

- [ ] **Step 2: 写 `useTheme.ts` + `ThemeProvider.tsx`**

`apps/web/src/theme/useTheme.ts`:
```ts
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
```

`apps/web/src/theme/ThemeProvider.tsx`:
```tsx
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
```

- [ ] **Step 3: 写 `ThemeToggle.tsx`**

`apps/web/src/theme/ThemeToggle.tsx`:
```tsx
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
```

- [ ] **Step 4: 写失败测试 `ThemeProvider.test.tsx`**

```tsx
import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import ThemeProvider from './ThemeProvider'
import ThemeToggle from './ThemeToggle'

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('defaults to system and applies resolved class to <html>', () => {
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    const toggle = screen.getByRole('button', { name: /深色/i })
    fireEvent.click(toggle)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('skilleval-theme')).toBe('dark')
  })

  it('persists choice across remount', () => {
    localStorage.setItem('skilleval-theme', 'light')
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('light button removes dark class', () => {
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>)
    fireEvent.click(screen.getByRole('button', { name: /浅色/i }))
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(localStorage.getItem('skilleval-theme')).toBe('light')
  })
})
```

- [ ] **Step 5: 在 `main.tsx` 包裹 Provider**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import ThemeProvider from './theme/ThemeProvider'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  </StrictMode>,
)
```

- [ ] **Step 6: 运行测试验证**

Run: `npm test -- src/theme/ThemeProvider.test.tsx`
Expected: PASS（3 例）

- [ ] **Step 7: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 8: 提交**

```bash
git add apps/web/src/index.css apps/web/src/theme/ apps/web/src/main.tsx
git commit -m "feat(web): slate/靛蓝主题 token + 深色模式三态切换"
```

---

### Task 2: UI 原语批次1（Button/Input/Textarea/Select/Badge/Card/Field/Spinner/EmptyState）

**Files:**
- Create: `apps/web/src/components/ui/{Button,Input,Textarea,Select,Badge,Card,Field,Spinner,EmptyState}.tsx`
- Create: `apps/web/src/components/ui/index.ts`
- Test: `apps/web/src/components/ui/primitives.test.tsx`

**Interfaces:**
- Produces: 见下方各组件签名；`index.ts` 统一 re-export。后续任务按需导入 `import { Button, Card, ... } from '../components/ui'`。

- [ ] **Step 1: 写各原语组件**

`Button.tsx`:
```tsx
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
  danger: 'bg-bad text-white hover:brightness-108 disabled:opacity-50',
}
const SIZES: Record<Size, string> = { sm: 'px-3 py-1 text-xs', md: 'px-4 py-1.5 text-sm' }

export default function Button({ variant = 'primary', size = 'md', loading, icon, className = '', children, disabled, ...rest }: Props) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center gap-1.5 rounded-md font-semibold transition disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
    >
      {loading ? <Spinner size={size === 'sm' ? 12 : 14} /> : icon}
      {children}
    </button>
  )
}
```

`Spinner.tsx`:
```tsx
export default function Spinner({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className="animate-spin" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="4" />
      <path d="M22 12a10 10 0 01-10 10" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}
```

`Input.tsx`:
```tsx
import { type InputHTMLAttributes } from 'react'
export default function Input({ className = '', ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...rest} className={`w-full rounded-md border border-line-strong bg-surface px-3 py-1.5 text-sm text-ink placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-soft ${className}`} />
}
```

`Textarea.tsx`:
```tsx
import { type TextareaHTMLAttributes } from 'react'
export default function Textarea({ className = '', ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...rest} className={`w-full rounded-md border border-line-strong bg-surface px-3 py-2 text-sm text-ink placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-soft ${className}`} />
}
```

`Select.tsx`:
```tsx
import { type SelectHTMLAttributes } from 'react'
export default function Select({ className = '', children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select {...rest} className={`w-full appearance-none rounded-md border border-line-strong bg-surface px-3 py-1.5 pr-8 text-sm text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-soft ${className}`} style={{ backgroundImage: "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5'><path d='M6 9l6 6 6-6'/></svg>\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}>
      {children}
    </select>
  )
}
```

`Badge.tsx`:
```tsx
import { type ReactNode } from 'react'
type Tone = 'ok' | 'bad' | 'wait' | 'skip' | 'neutral'
const TONES: Record<Tone, string> = {
  ok: 'bg-ok/10 text-ok', bad: 'bg-bad/10 text-bad', wait: 'bg-wait/10 text-wait',
  skip: 'bg-skip/10 text-skip', neutral: 'bg-surface-2 text-muted',
}
export default function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${TONES[tone]}`}>{children}</span>
}
```

`Card.tsx`:
```tsx
import { type ReactNode } from 'react'
export default function Card({ title, className = '', children }: { title?: string; className?: string; children: ReactNode }) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-4 shadow-sm ${className}`}>
      {title && <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">{title}</h3>}
      {children}
    </section>
  )
}
```

`Field.tsx`:
```tsx
import { type ReactNode } from 'react'
export default function Field({ label, hint, optional, htmlFor, children }: { label: string; hint?: string; optional?: boolean; htmlFor?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="flex items-center gap-1.5 text-xs font-semibold text-ink">
        {label}{optional && <span className="text-xs font-normal text-faint">可选</span>}
      </label>
      {children}
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </div>
  )
}
```

`EmptyState.tsx`:
```tsx
import { type ReactNode } from 'react'
export default function EmptyState({ icon, title, description, action }: { icon?: ReactNode; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-line bg-surface-2 p-10 text-center">
      {icon && <div className="text-faint">{icon}</div>}
      <p className="text-sm font-medium text-muted">{title}</p>
      {description && <p className="max-w-sm text-xs text-faint">{description}</p>}
      {action}
    </div>
  )
}
```

`index.ts`:
```ts
export { default as Button } from './Button'
export { default as Input } from './Input'
export { default as Textarea } from './Textarea'
export { default as Select } from './Select'
export { default as Badge } from './Badge'
export { default as Card } from './Card'
export { default as Field } from './Field'
export { default as Spinner } from './Spinner'
export { default as EmptyState } from './EmptyState'
export { default as Modal } from './Modal'
export { default as ToastContainer, useToast } from './Toast'
```
（Modal/Toast 在 Task 3 创建；index.ts 此步可先不含后两行，Task 3 补齐。）

- [ ] **Step 2: 写失败测试 `primitives.test.tsx`**

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Button, Badge, EmptyState } from './index'

describe('UI primitives', () => {
  it('Button renders variant and shows spinner when loading', () => {
    render(<Button loading>保存</Button>)
    expect(screen.getByText('保存')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('Badge applies tone class', () => {
    const { container } = render(<Badge tone="ok">已完成</Badge>)
    expect(container.firstChild).toHaveClass('text-ok')
    expect(screen.getByText('已完成')).toBeInTheDocument()
  })

  it('EmptyState renders title and description', () => {
    render(<EmptyState title="暂无记录" description="请先创建" />)
    expect(screen.getByText('暂无记录')).toBeInTheDocument()
    expect(screen.getByText('请先创建')).toBeInTheDocument()
  })

  it('Button ghost variant calls onClick', () => {
    const fn = vi.fn()
    render(<Button variant="ghost" onClick={fn}>取消</Button>)
    fireEvent.click(screen.getByText('取消'))
    expect(fn).toHaveBeenCalled()
  })
})
```
（顶部补 `import { vi } from 'vitest'`）

- [ ] **Step 3: 运行测试验证**

Run: `npm test -- src/components/ui/primitives.test.tsx`
Expected: PASS（4 例）

- [ ] **Step 4: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 5: 提交**

```bash
git add apps/web/src/components/ui/
git commit -m "feat(web): UI 原语层（Button/Input/Select/Badge/Card/Field/Spinner/EmptyState）"
```

---

### Task 3: Modal + Toast 原语

**Files:**
- Create: `apps/web/src/components/ui/Modal.tsx`
- Create: `apps/web/src/components/ui/Toast.tsx`
- Modify: `apps/web/src/components/ui/index.ts`（补 Modal/Toast 导出）
- Modify: `apps/web/src/App.tsx`（挂 `<ToastContainer/>`——在 Task 4 一并改，此处仅创建组件）
- Test: `apps/web/src/components/ui/overlay.test.tsx`

**Interfaces:**
- Produces: `Modal`（`{ open, onClose, title, children, footer }`）、`ToastContainer`（默认导出，挂载一次）、`useToast()` → `toast(msg: string, tone?: 'ok'|'bad'|'wait')`。`useToast` 在无 `ToastContainer` 祖先时返回 no-op（测试友好）。

- [ ] **Step 1: 写 `Modal.tsx`**

```tsx
import { type ReactNode, useEffect } from 'react'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
}

export default function Modal({ open, onClose, title, children, footer }: Props) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="flex max-h-[80vh] w-[540px] max-w-[92vw] flex-col rounded-xl border border-line bg-surface shadow-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h3 className="text-sm font-bold text-ink">{title}</h3>
          <button type="button" onClick={onClose} className="text-lg text-muted hover:text-ink">×</button>
        </div>
        <div className="flex-1 overflow-auto">{children}</div>
        {footer && <div className="border-t border-line px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 写 `Toast.tsx`**

```tsx
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
```

补齐 `index.ts` 末两行（Modal/Toast 导出）。

- [ ] **Step 3: 写失败测试 `overlay.test.tsx`**

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, afterEach } from 'vitest'
import { Modal, ToastContainer, useToast } from './index'

afterEach(() => vi.useRealTimers())

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(<Modal open={false} onClose={vi.fn()} title="标题">内容</Modal>)
    expect(screen.queryByText('内容')).not.toBeInTheDocument()
  })
  it('renders content and calls onClose on backdrop click', () => {
    const fn = vi.fn()
    render(<Modal open={true} onClose={fn} title="选目录">树内容</Modal>)
    expect(screen.getByText('树内容')).toBeInTheDocument()
    fireEvent.click(screen.getByText('树内容').parentElement!.parentElement!)
  })
  it('calls onClose on Escape', () => {
    const fn = vi.fn()
    render(<Modal open={true} onClose={fn} title="t">x</Modal>)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(fn).toHaveBeenCalled()
  })
})

describe('Toast', () => {
  it('toast() renders a message and auto-dismisses', () => {
    vi.useFakeTimers()
    function Emitter() {
      const { toast } = useToast()
      return <button onClick={() => toast('已保存', 'ok')}>发</button>
    }
    render(<ToastContainer><Emitter /></ToastContainer>)
    fireEvent.click(screen.getByText('发'))
    expect(screen.getByText('已保存')).toBeInTheDocument()
    vi.advanceTimersByTime(4100)
    expect(screen.queryByText('已保存')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 4: 运行测试验证**

Run: `npm test -- src/components/ui/overlay.test.tsx`
Expected: PASS

- [ ] **Step 5: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 6: 提交**

```bash
git add apps/web/src/components/ui/Modal.tsx apps/web/src/components/ui/Toast.tsx apps/web/src/components/ui/index.ts apps/web/src/components/ui/overlay.test.tsx
git commit -m "feat(web): Modal + Toast 原语"
```

---

### Task 4: 后端 `GET /api/runner/models`

**Files:**
- Create: `apps/api/skill_eval/runner/models.py`
- Modify: `apps/api/skill_eval/runner/api.py`（加路由）
- Test: `apps/api/tests/test_runner.py`（加 `TestModelsApi`）

**Interfaces:**
- Produces: `list_models() -> list[dict]`，元素 `{provider:str, model:str, id:str, context_window:int|None, input_cost:float|None, output_cost:float|None}`。CLI 缺失/出错 → `[]`。
- 端点：`GET /api/runner/models` → `{"models": [...]}`

- [ ] **Step 1: 写失败测试（加到 `test_runner.py` 末尾）**

```python
class TestModelsApi:
    def test_lists_models_from_cli(self, monkeypatch: pytest.MonkeyPatch):
        sample = "opencode-go/glm-5.2\nanthropic/claude-opus-4-6\n"
        import skill_eval.runner.models as m
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: _StubOut(stdout=sample))
        from skill_eval.runner.models import list_models
        out = list_models()
        assert out[0]["provider"] == "opencode-go"
        assert out[0]["model"] == "glm-5.2"
        assert out[0]["id"] == "opencode-go/glm-5.2"
        assert out[1]["provider"] == "anthropic"

    def test_models_empty_when_cli_missing(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(shutil, "which", lambda b: None)
        from skill_eval.runner.models import list_models
        assert list_models() == []

    def test_models_endpoint(self, monkeypatch: pytest.MonkeyPatch, client: TestClient):
        import skill_eval.runner.models as m
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: _StubOut(stdout="opencode-go/glm-5.2\n"))
        r = client.get("/api/runner/models")
        assert r.status_code == 200
        body = r.json()
        assert body["models"][0]["id"] == "opencode-go/glm-5.2"
```

在文件顶部辅助区加：
```python
class _StubOut:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
```
（`client` fixture 若无，在 `TestRunnerStreamApi` 已用同款——确认 `test_runner.py` 顶部有 `from fastapi.testclient import TestClient` 与 app 构造 fixture；若没有，沿用 `TestRunnerStreamApi` 的 `client` fixture 模式。）

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_runner.py::TestModelsApi -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 `runner/models.py`**

```python
"""List models available to the opencode CLI by shelling out to `opencode models`."""

import shutil
import subprocess
from typing import Any


def list_models() -> list[dict[str, Any]]:
    if shutil.which("opencode") is None:
        return []
    try:
        proc = subprocess.run(
            ["opencode", "models", "--verbose"],
            capture_output=True, text=True, timeout=30,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    out: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or "/" not in line:
            continue
        provider, _, model = line.partition("/")
        out.append({
            "provider": provider,
            "model": model,
            "id": line,
            "context_window": None,
            "input_cost": None,
            "output_cost": None,
        })
    return out
```

- [ ] **Step 4: 加路由到 `runner/api.py`**

在 `get_skills` 旁加：
```python
from skill_eval.runner.models import list_models

@router.get("/models")
def get_models() -> dict[str, object]:
    return {"models": list_models()}
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_runner.py::TestModelsApi -v`
Expected: PASS（3 例）

- [ ] **Step 6: 全量后端测试**

Run: `uv run pytest`
Expected: 全绿（156 → 159）

- [ ] **Step 7: 提交**

```bash
git add apps/api/skill_eval/runner/models.py apps/api/skill_eval/runner/api.py apps/api/tests/test_runner.py
git commit -m "feat(runner): GET /api/runner/models 列举可用模型"
```

---

### Task 5: 后端 `GET /api/fs/browse`

**Files:**
- Create: `apps/api/skill_eval/fs.py`
- Modify: `apps/api/skill_eval/app.py`（挂载路由）
- Test: `apps/api/tests/test_fs.py`

**Interfaces:**
- Produces: `browse_directory(path: str | None) -> dict` → `{"path": str, "entries": [{"name":str,"type":"dir"|"file","path":str}]}`；`router`（prefix `/api/fs`）。
- 端点：`GET /api/fs/browse?path=<可选>`，不存在/非目录 → 404。

- [ ] **Step 1: 写失败测试 `tests/test_fs.py`**

```python
"""Tests for filesystem browse endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skill_eval.app import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    (tmp_path / "sub1").mkdir()
    (tmp_path / "sub2").mkdir()
    (tmp_path / "hidden").mkdir()
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub1" / "inner.txt").write_text("y")
    return TestClient(create_app())


def test_browse_lists_dirs_and_files(client: TestClient, tmp_path: Path):
    r = client.get("/api/fs/browse", params={"path": str(tmp_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == str(tmp_path.resolve())
    names = {e["name"] for e in body["entries"]}
    assert "sub1" in names and "sub2" in names and "a.txt" in names
    types = {e["name"]: e["type"] for e in body["entries"]}
    assert types["sub1"] == "dir" and types["a.txt"] == "file"


def test_browse_skips_hidden(client: TestClient, tmp_path: Path):
    r = client.get("/api/fs/browse", params={"path": str(tmp_path)})
    names = {e["name"] for e in r.json()["entries"]}
    assert "hidden" in names  # 'hidden' 不以 . 开头，应保留
    # 真正隐藏目录测试
    (tmp_path / ".secret").mkdir()
    r2 = client.get("/api/fs/browse", params={"path": str(tmp_path)})
    assert ".secret" not in {e["name"] for e in r2.json()["entries"]}


def test_browse_missing_path_returns_404(client: TestClient, tmp_path: Path):
    r = client.get("/api/fs/browse", params={"path": str(tmp_path / "nope")})
    assert r.status_code == 404


def test_browse_empty_path_uses_home(client: TestClient):
    r = client.get("/api/fs/browse")
    assert r.status_code == 200
    from pathlib import Path as P
    assert r.json()["path"] == str(P.home().resolve())
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_fs.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 `skill_eval/fs.py`**

```python
"""Filesystem browse endpoint: list directory entries for the path picker modal."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/fs", tags=["fs"])


def browse_directory(path: str | None) -> dict[str, Any]:
    target = Path(path).expanduser().resolve() if path else Path.home().resolve()
    if not target.is_dir():
        raise HTTPException(status_code=404, detail=f"not a directory: {target}")
    entries: list[dict[str, str]] = []
    try:
        for d in sorted(target.iterdir()):
            if d.name.startswith("."):
                continue
            entries.append({
                "name": d.name,
                "type": "dir" if d.is_dir() else "file",
                "path": str(d.resolve()),
            })
    except PermissionError:
        pass
    except OSError:
        entries = []
    return {"path": str(target), "entries": entries}


@router.get("/browse")
def get_browse(path: str | None = Query(default=None)) -> dict[str, Any]:
    return browse_directory(path)
```

- [ ] **Step 4: 挂载路由到 `app.py`**

在 import 区加 `from skill_eval.fs import router as fs_router`，在 `app.include_router(...)` 序列加 `app.include_router(fs_router)`。

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_fs.py -v`
Expected: PASS（4 例）

- [ ] **Step 6: 全量后端测试**

Run: `uv run pytest`
Expected: 全绿（159 → 163）

- [ ] **Step 7: 提交**

```bash
git add apps/api/skill_eval/fs.py apps/api/skill_eval/app.py apps/api/tests/test_fs.py
git commit -m "feat(fs): GET /api/fs/browse 目录列举端点"
```

---

### Task 6: 后端补 `--model` argv 转发断言（填补测试缺口）

**Files:**
- Modify: `apps/api/tests/test_runner.py`（加捕获 argv 的 fake proc + 一条断言）

**Interfaces:**
- Consumes: `_patch_run` 模式；新增 `_CmdCaptureProc` 包装捕获 `Popen` 的首参 `cmd`。

- [ ] **Step 1: 写失败测试（加到 `TestOpencodeRunner`）**

```python
def test_run_stream_forwards_model_flag_into_cmd(self, monkeypatch: pytest.MonkeyPatch):
    captured: list[list[str]] = []

    class _CmdCaptureProc(_FakeProc):
        def __init__(self, lines: list[str]) -> None:
            super().__init__(lines)

    def _capture_popen(cmd, *a, **kw):
        captured.append(cmd)
        return _CmdCaptureProc(JSONL_LINES)

    monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
    monkeypatch.setattr("skill_eval.runner.opencode.subprocess.Popen", _capture_popen)
    monkeypatch.setattr("skill_eval.runner.opencode._run_export", lambda sid: EXPORT_JSON["info"])
    runner = OpencodeRunner()
    ctx = RunContext(task="hi", model="opencode-go/glm-5.2")
    runner.run_stream(ctx, emit=lambda _c: None)
    assert "--model" in captured[0]
    assert "opencode-go/glm-5.2" in captured[0]
```

- [ ] **Step 2: 运行测试验证**

Run: `uv run pytest tests/test_runner.py::TestOpencodeRunner::test_run_stream_forwards_model_flag_into_cmd -v`
Expected: PASS（`opencode.py:52-53` 已转发 `--model`；此测试锁住行为，防回归）。若 FAIL，则 `opencode.py` 转发有 bug，需修。

- [ ] **Step 3: 提交**

```bash
git add apps/api/tests/test_runner.py
git commit -m "test(runner): 断言 --model 转发至 cmd argv"
```

---

### Task 7: 重新生成 OpenAPI 类型

**Files:**
- Modify: `apps/web/openapi.json`、`apps/web/src/api/types.generated.ts`（构建产物）

- [ ] **Step 1: 导出 OpenAPI JSON**

Run（在 `apps/api`）:
```powershell
uv run python scripts/export_openapi.py ../web/openapi.json
```
Expected: 写入 `apps/web/openapi.json`，含 `/api/runner/models` 与 `/api/fs/browse`。

- [ ] **Step 2: 生成 TS 类型**

Run（在 `apps/web`）:
```powershell
npx openapi-typescript openapi.json -o src/api/types.generated.ts
```
Expected: 写入新类型（含 models / browse 响应）。

- [ ] **Step 3: 验证类型**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 4: 提交**

```bash
git add apps/web/openapi.json apps/web/src/api/types.generated.ts
git commit -m "chore: 重新生成 openapi 类型（models + fs/browse）"
```

---

### Task 8: App 外壳 + 导航迁移（中文化 + ThemeToggle + Toast）

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/main.tsx`（若 Task1 未包 Toast，此处包；Toast 需在 ThemeProvider 内）

**Interfaces:**
- Consumes: `ThemeToggle`、`ToastContainer`、`useToast` from ui/theme。

- [ ] **Step 1: 改写 `App.tsx`**

读取现有 `App.tsx`（侧边栏 + 5 导航 + Outlet）。替换为：导航中文标签、用原语类（沿用语义 token）、底部挂 `ThemeToggle`、最外层包 `ToastContainer`。导航标签映射：
- `Traces` → `运行记录`
- `运行` → `运行 Skill`
- `Test Cases` → `测试用例`
- `Eval Runs` → `评测记录`
- `Diff` → `Trace 对比`
- 标语 `AI Agent / Skill 测试与 Trace 可视化` → `AI Agent / Skill 测试与 Trace 可视化`（已是中文，保留）

```tsx
import { NavLink, Outlet } from 'react-router-dom'
import ThemeToggle from './theme/ThemeToggle'
import { ToastContainer } from './components/ui'

const NAV = [
  { to: '/traces', label: '运行记录' },
  { to: '/run', label: '运行 Skill' },
  { to: '/test-cases', label: '测试用例' },
  { to: '/eval-runs', label: '评测记录' },
  { to: '/diff', label: 'Trace 对比' },
]

export default function App() {
  return (
    <ToastContainer>
      <div className="flex min-h-screen">
        <aside className="sticky top-0 flex h-screen w-56 flex-col gap-1 border-r border-line bg-surface p-3">
          <div className="mb-4 flex items-center gap-2 px-2 text-base font-bold">
            <span className="h-2.5 w-2.5 rounded-sm bg-accent" /> SkillEval
          </div>
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm ${isActive ? 'bg-accent-soft font-semibold text-accent' : 'text-muted hover:bg-surface-2 hover:text-ink'}`
              }
            >
              {n.label}
            </NavLink>
          ))}
          <div className="mt-auto">
            <ThemeToggle />
          </div>
        </aside>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </ToastContainer>
  )
}
```

- [ ] **Step 2: 类型检查 + 测试**

Run: `npx tsc -b`；`npm test`
Expected: 退出 0 / 全绿

- [ ] **Step 3: 提交**

```bash
git add apps/web/src/App.tsx
git commit -m "feat(web): 侧边栏中文化 + 挂载 ThemeToggle 与 Toast"
```

---

### Task 9: RunPage 迁移到原语 + 中文化（不含新功能）

**Files:**
- Modify: `apps/web/src/pages/RunPage.tsx`
- Modify: `apps/web/src/pages/RunPage.test.tsx`（保持绿；新功能在 Task 13-15 改）

**Interfaces:**
- Consumes: `Button, Card, Field, Input, Textarea, Select` from ui。

- [ ] **Step 1: 迁移 RunPage 表单到原语，文案中文化**

将现有内联 `<select>/<input>/<textarea>/<button>` 替换为 `Select/Input/Textarea/Button`，`<label>` 结构换 `Field`，卡片换 `Card`。**此步不加新字段（provider/model 级联、路径模态、SSE 加固留给 Task 13-15）。** 文案映射（保留已有中文，翻英文）：
- `运行中…` / `运行` → 保留
- `通过 opencode CLI 运行并抓取 Trace` → `通过 opencode CLI 运行并实时抓取 Trace`
- `（无 / 普通 prompt）` → 保留
- `工作目录` → 保留；placeholder `E:\playground\my-project（留空则用后端 cwd）` → 保留
- `自动批准工具执行（--auto）` / `⚠ 将自动执行所有工具，请确认工作目录安全` → 保留
- `输入要执行的 prompt` → `输入要执行的 Prompt`（Prompt 保留原文）
- `提示：opencode skill 由模型按需自动触发，无法强制。所选 skill 的引导语会注入 prompt 以提高命中。` → `提示：opencode skill 由模型按需自动触发，无法强制。所选 skill 的引导语会注入 Prompt 以提高命中。`
- `实时事件流` / `等待事件…` → 保留
- `请求失败` / `运行失败` → 保留

保持现有请求体字段不变（agent/task/skill_name/cwd/auto/agent_name，**暂不加 model**）。

- [ ] **Step 2: 跑测试保持绿**

Run: `npm test -- src/pages/RunPage.test.tsx`
Expected: PASS（4 例，文案断言用 `/运行 Skill/i`、`/输入要执行的 prompt/i`——后者改为 Prompt 后需更新正则为 `/输入要执行的 Prompt/i`，同步改测试）

- [ ] **Step 3: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 4: 提交**

```bash
git add apps/web/src/pages/RunPage.tsx apps/web/src/pages/RunPage.test.tsx
git commit -m "refactor(web): RunPage 迁移原语 + 中文化"
```

---

### Task 10: TracesPage + TraceDetailPage 迁移 + 中文化

**Files:**
- Modify: `apps/web/src/pages/TracesPage.tsx`、`apps/web/src/pages/TraceDetailPage.tsx`

**文案映射：**
- TracesPage: `Traces`→`运行记录`；`共 {n} 条运行记录`→保留；`全部 Agent`→`全部 Agent`（Agent 保留）；`全部状态`→保留；表头 `Skill`/`Agent`/`状态`/`开始时间`/`Tokens`/`Cost`→`Skill`/`Agent`/`状态`/`开始时间`/`Tokens`/`Cost`（状态/Tokens/Cost 按约定）；空态 `暂无 Trace。可通过 POST /api/ingest/import 或 POST /api/ingest/push 导入。`→保留。
- TraceDetailPage: `Trace 不存在。`/`返回列表`→保留；`加载中…`→保留；`← Traces`→`← 运行记录`；`Diff 对比`→保留；`LLM 结果级`/`LLM 全过程`→保留；`judge failed`→`评测失败`。

- [ ] **Step 1: 迁移两页到原语（Badge 替状态色映射、Card 替卡片、Select/Input 替筛选、EmptyState 替空态、Spinner 替加载）**

- [ ] **Step 2: 类型检查 + 测试**

Run: `npx tsc -b`；`npm test`
Expected: 退出 0 / 全绿

- [ ] **Step 3: 提交**

```bash
git add apps/web/src/pages/TracesPage.tsx apps/web/src/pages/TraceDetailPage.tsx
git commit -m "refactor(web): 运行记录/Trace 详情页迁移原语 + 中文化"
```

---

### Task 11: TestCasePage + EvalRunsPage 迁移 + 中文化

**Files:**
- Modify: `apps/web/src/pages/TestCasePage.tsx`、`apps/web/src/pages/EvalRunsPage.tsx`

**文案映射：**
- TestCasePage: `Test Cases`→`测试用例`；`{n} 个用例`→保留；`取消`/`新建用例`/`名称`/`描述`/`创建`/`删除`/`运行评测`→保留；`期望工具（逗号分隔）：read_file, grep`→保留；`自定义断言（每行一个 Python 表达式，可用 projection/actual/expected/trace）`→保留；`暂无用例，点击右上角新建。`→保留；`无可用 Trace`→保留；`期望 … · N 条断言`→保留。
- EvalRunsPage: `Eval Runs`→`评测记录`；`{n} 条评测记录（规则评测与 LLM 评测）`→保留；`暂无评测记录。`→保留。

- [ ] **Step 1: 迁移两页到原语（Button 替创建/删除/运行评测、Card 替表单与记录卡、Badge 替状态、EmptyState 替空态）。删除/创建成功用 `useToast` 给反馈。**

- [ ] **Step 2: 类型检查 + 测试**

Run: `npx tsc -b`；`npm test`
Expected: 退出 0 / 全绿

- [ ] **Step 3: 提交**

```bash
git add apps/web/src/pages/TestCasePage.tsx apps/web/src/pages/EvalRunsPage.tsx
git commit -m "refactor(web): 测试用例/评测记录页迁移原语 + 中文化 + Toast 反馈"
```

---

### Task 12: DiffPage + 领域组件迁移 + 中文化

**Files:**
- Modify: `apps/web/src/pages/DiffPage.tsx`
- Modify: `apps/web/src/components/{TraceDag,Timeline,DetailPanel,CostPanel}.tsx`

**文案映射：**
- DiffPage: `Trace Diff`→`Trace 对比`；`基线 Trace`/`对比 Trace`→保留；`选择…`→保留；`新增`/`删除`/`参数变化`/`顺序有变`/`一致`→保留；`工具`/`基线`/`对比`（列头）→保留；`选择两条 Trace 进行对比。`→保留；`基线加载中…`/`对比加载中…`→保留。
- DetailPanel: `选择一个节点查看详情`→保留；`Tool`/`Args`/`Result`/`LLM`/`Error`/`Input`/`Output`→保留（产品术语）。
- Timeline: `无时间线数据`→保留。
- CostPanel: `Tokens`/`Cost`/`Latency`/`Steps`/`… steps · … errors`→保留（术语；`steps`/`errors` 可中文化为 `步骤 · N 错误`，按实现定，倾向 `N 步 · N 错误`）。

- [ ] **Step 1: DiffPage 迁移原语（Select 替两条 Trace 选择、Card 替对比表卡、Badge 替新增/删除/变化标签、EmptyState 替空态）。**

- [ ] **Step 2: 4 组件迁移（DetailPanel 内 Section/Code 私有子组件可保留；CostPanel Card 私有换 ui/Card；Timeline 空态换 EmptyState；Badge 用 ui/Badge）。**

- [ ] **Step 3: 类型检查 + 测试**

Run: `npx tsc -b`；`npm test`
Expected: 退出 0 / 全绿

- [ ] **Step 4: 提交**

```bash
git add apps/web/src/pages/DiffPage.tsx apps/web/src/components/
git commit -m "refactor(web): 对比页 + 领域组件迁移原语 + 中文化"
```

---

### Task 13: RunPage 功能——提供商→模型级联下拉

**Files:**
- Create: `apps/web/src/utils/models.ts`
- Modify: `apps/web/src/pages/RunPage.tsx`
- Test: `apps/web/src/utils/models.test.ts`

**Interfaces:**
- Produces: `groupByProvider(models)` → `Record<provider, Model[]>`；`buildModelId(provider, model)` → `provider/model`。`Model = { provider, model, id, context_window?, input_cost?, output_cost? }`。
- Consumes: `GET /api/runner/models` 响应 `{ models: Model[] }`。

- [ ] **Step 1: 写失败测试 `models.test.ts`**

```ts
import { describe, expect, it } from 'vitest'
import { groupByProvider, buildModelId } from './models'

const MODELS = [
  { provider: 'opencode-go', model: 'glm-5.2', id: 'opencode-go/glm-5.2' },
  { provider: 'opencode-go', model: 'glm-5.2-mini', id: 'opencode-go/glm-5.2-mini' },
  { provider: 'anthropic', model: 'claude-opus-4-6', id: 'anthropic/claude-opus-4-6' },
]

describe('models util', () => {
  it('groups by provider', () => {
    const g = groupByProvider(MODELS)
    expect(Object.keys(g).sort()).toEqual(['anthropic', 'opencode-go'])
    expect(g['opencode-go']).toHaveLength(2)
  })
  it('buildModelId joins provider/model', () => {
    expect(buildModelId('opencode-go', 'glm-5.2')).toBe('opencode-go/glm-5.2')
  })
})
```

- [ ] **Step 2: 写 `utils/models.ts`**

```ts
export interface Model {
  provider: string
  model: string
  id: string
  context_window?: number | null
  input_cost?: number | null
  output_cost?: number | null
}

export function groupByProvider(models: Model[]): Record<string, Model[]> {
  const g: Record<string, Model[]> = {}
  for (const m of models) (g[m.provider] ??= []).push(m)
  return g
}

export function buildModelId(provider: string, model: string): string {
  return `${provider}/${model}`
}
```

- [ ] **Step 3: RunPage 加级联下拉**

在 RunPage 增加 state：`models: Model[]`、`provider: string`('' = 默认)、`modelId: string`('' = 默认)。`useEffect` 拉 `/api/runner/models`。UI：两个 `Select`——提供商（选项含 `默认（由 opencode 决定）` + 各 provider）、模型（按所选 provider 过滤；选"默认"时禁用）。提交体加 `model: modelId ? buildModelId(provider, modelId) : null`。即：
```tsx
const model = provider && modelId ? buildModelId(provider, modelId) : null
// body: { agent:'opencode', task, skill_name, cwd: cwd||null, auto, agent_name, model }
```

- [ ] **Step 4: 测试**

Run: `npm test -- src/utils/models.test.ts src/pages/RunPage.test.tsx`
Expected: PASS。`RunPage.test.tsx` 的 `mockFetch` 需增 `/api/runner/models` 分支返回 `{ models: [] }`（避免未处理 fetch 警告）。

- [ ] **Step 5: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 6: 提交**

```bash
git add apps/web/src/utils/models.ts apps/web/src/utils/models.test.ts apps/web/src/pages/RunPage.tsx apps/web/src/pages/RunPage.test.tsx
git commit -m "feat(web): 运行页提供商→模型级联下拉"
```

---

### Task 14: RunPage 功能——路径浏览模态

**Files:**
- Modify: `apps/web/src/pages/RunPage.tsx`（加模态 + 浏览逻辑）

**Interfaces:**
- Consumes: `GET /api/fs/browse?path=` → `{ path: string, entries: {name,type,path}[] }`；`Modal` from ui。

- [ ] **Step 1: RunPage 加路径模态**

新增 state：`browseOpen: boolean`、`browsePath: string`、`entries: {name,type,path}[]`。函数 `openBrowse()`：以当前 `cwd` 或空为初值请求 `/api/fs/browse`，填 `entries`，开模态。`enterDir(path)`：请求该 path，更新 `browsePath` 与 `entries`。`confirmBrowse()`：写回 `cwd=browsePath`，关模态。UI：`Input`(cwd) + `Button`(variant ghost, "浏览", onClick=openBrowse)；模态内面包屑（按 `browsePath` split `/` 或 `\` 生成分段，可点击跳层——跳层即 `enterDir(到该层的路径)`）+ 目录树（`entries` 过滤 `type==='dir'` 可点击进入，`type==='file'` 灰显不可选）+ footer `Button`("取消" ghost / "选择此目录" primary)。加载中用 `Spinner`，失败用 `useToast` 提示 `无法读取该目录`。

- [ ] **Step 2: 测试**

Run: `npm test -- src/pages/RunPage.test.tsx`
Expected: PASS。`mockFetch` 增 `/api/fs/browse` 分支返回样例 entries。可加一例：点"浏览"后模态出现目录项。

- [ ] **Step 3: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 4: 提交**

```bash
git add apps/web/src/pages/RunPage.tsx apps/web/src/pages/RunPage.test.tsx
git commit -m "feat(web): 运行页路径浏览模态"
```

---

### Task 15: RunPage 功能——SSE 加固（api.postStream + AbortController）

**Files:**
- Modify: `apps/web/src/api/client.ts`（加 `postStream`）
- Modify: `apps/web/src/pages/RunPage.tsx`（改用 `postStream` + AbortController）
- Modify: `apps/web/src/pages/RunPage.test.tsx`

**Interfaces:**
- Produces: `api.postStream(path, body, { onEvent, onDone, onError, signal })` → `Promise<void>`；解析 `data: ...\n\n` 帧。

- [ ] **Step 1: 在 `client.ts` 加 `postStream`**

```ts
interface StreamHandlers {
  onEvent: (node: unknown) => void
  onDone: (traceId: string) => void
  onError: (message: string) => void
  signal?: AbortSignal
}

export async function postStream(path: string, body: unknown, h: StreamHandlers): Promise<void> {
  const resp = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: h.signal,
  })
  if (!resp.ok || !resp.body) { h.onError(`HTTP ${resp.status}`); return }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 2)
      if (!frame.startsWith('data: ')) continue
      let data: { type: string; node?: unknown; trace_id?: string; message?: string }
      try { data = JSON.parse(frame.slice(6)) } catch { continue }
      if (data.type === 'event' && data.node) h.onEvent(data.node)
      else if (data.type === 'done' && data.trace_id) { h.onDone(data.trace_id); return }
      else if (data.type === 'error') { h.onError(data.message ?? '运行失败'); return }
    }
  }
}
```

- [ ] **Step 2: RunPage 改用 postStream + AbortController**

新增 `abortRef = useRef<AbortController | null>(null)`。`submit` 内 `const ctrl = new AbortController(); abortRef.current = ctrl`，调 `postStream('/api/runner/run/stream', body, { onEvent: n=>setEvents(p=>[...p,n]), onDone: id=>{setRunning(false);navigate(`/traces/${id}`)}, onError: m=>{setError(m);setRunning(false)}, signal: ctrl.signal })`。`useEffect` 清理：卸载时 `abortRef.current?.abort()`。加"停止"按钮（运行中显示）：`onClick={()=>abortRef.current?.abort()}`，abort 后 `setRunning(false)`。

- [ ] **Step 3: 测试**

Run: `npm test -- src/pages/RunPage.test.tsx`
Expected: PASS。现有 4 例应仍绿（postStream 内部仍用 fetch）。可加一例：运行中点"停止"后 `running` 归 false（mock fetch 返回长流，点停止后断言按钮变回"运行"）。

- [ ] **Step 4: 类型检查**

Run: `npx tsc -b`
Expected: 退出 0

- [ ] **Step 5: 提交**

```bash
git add apps/web/src/api/client.ts apps/web/src/pages/RunPage.tsx apps/web/src/pages/RunPage.test.tsx
git commit -m "feat(web): SSE 抽离 api.postStream + AbortController 加固"
```

---

### Task 16: 全量验证 + 文档同步

**Files:**
- Verify: 全仓
- Modify: `README.md`（测试计数 / 运行页字段说明）、`docs/PROGRESS.md`（Phase 条目）

- [ ] **Step 1: 后端全量测试**

Run（`apps/api`）: `uv run pytest`
Expected: 全绿（163+）

- [ ] **Step 2: 前端全量测试 + 类型**

Run（`apps/web`）: `npm test`；`npx tsc -b`
Expected: 全绿 / 退出 0

- [ ] **Step 3: E2E（可选，若环境就绪）**

Run（`apps/web`）: `npm run test:e2e`
Expected: 5 例绿（若运行页 E2E 改动则同步）

- [ ] **Step 4: 人工对照 demo-cool.html 观感**

启动 `start-all.ps1`，打开 `http://localhost:5173`，逐页核对：中文化、深色模式切换、slate/靛蓝配色、运行页级联与路径模态、SSE 停止。

- [ ] **Step 5: 更新 README/PROGRESS**

更新 `README.md` 测试计数与运行页字段（新增提供商/模型、路径浏览）；`docs/PROGRESS.md` 加 Phase 条目（由规格2 的 CHANGELOG 机制统一记录，此处仅同步进度）。

- [ ] **Step 6: 提交**

```bash
git add README.md docs/PROGRESS.md
git commit -m "docs: 同步前端重构进度与运行页字段说明"
```

---

## Self-Review

**1. Spec coverage:** 逐条对照规格 §2 目标 G1-G8：
- G1 中文化 → Task 8-12（全页中文化）
- G2 UI 原语 → Task 2-3
- G3 深色模式 → Task 1
- G4 美化 + 状态补齐 → Task 1（token）+ Task 2-3（原语含 EmptyState/Spinner/Toast）+ Task 8-12（迁移应用）
- G5 提供商→模型级联 → Task 4（后端）+ Task 13（前端）
- G6 路径浏览模态 → Task 5（后端）+ Task 14（前端）
- G7 SSE 加固 → Task 15
- G8 后端两端点 → Task 4-5；不改 schema → 确认（Task 4-5 均不动 RunContext/StreamRunRequest）
- §7.4 可选 providerID 记入 Trace.extra → 未单列任务（标注可选，实现时定；不阻塞 DoD）

**2. Placeholder scan:** 无 TBD/TODO；每个 code step 含实代码；迁移任务含文案映射表。

**3. Type consistency:** `useTheme` → `{mode,setMode,resolved}` 在 Task1/8 一致；`Model` 接口 Task13 定义、RunPage 沿用；`postStream` 签名 Task15 定义、RunPage 调用一致；`browse_directory` Task5 与 RunPage Task14 消费的 `{path,entries}` 一致。

**4. 依赖顺序:** Task1(地基token)→2,3(原语)→4,5,6(后端)→7(regen)→8(外壳)→9-12(页面迁移)→13,14,15(运行页功能，依赖 Task4/5 端点 + Task7 类型 + Task9 RunPage 迁移)→16(验证)。链路无环。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-24-frontend-overhaul.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
