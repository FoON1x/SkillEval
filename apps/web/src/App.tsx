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
