import { NavLink, Outlet } from 'react-router-dom'

const nav = [
  { to: '/traces', label: 'Traces' },
  { to: '/test-cases', label: 'Test Cases' },
  { to: '/eval-runs', label: 'Eval Runs' },
  { to: '/diff', label: 'Diff' },
]

export default function App() {
  return (
    <div className="flex h-screen">
      <aside className="w-56 shrink-0 border-r border-line bg-surface flex flex-col">
        <h1 className="px-5 pt-6 pb-4 text-lg font-semibold tracking-tight">SkillEval</h1>
        <nav className="flex flex-col gap-1 px-3">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-accent-soft text-ink font-medium'
                    : 'text-muted hover:bg-canvas hover:text-ink'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="mt-auto px-5 py-4 text-xs text-faint">AI Agent / Skill 测试与 Trace 可视化</p>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}