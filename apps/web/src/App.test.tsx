import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import App from './App'
import ThemeProvider from './theme/ThemeProvider'

function stubMatchMedia() {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }))
}

describe('App', () => {
  beforeEach(() => {
    stubMatchMedia()
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('renders the product title', () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </MemoryRouter>,
    )
    expect(screen.getByText(/SkillEval/i)).toBeInTheDocument()
  })

  it('renders nav labels in Chinese', () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: '运行记录' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '运行 Skill' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '测试用例' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '评测记录' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Trace 对比' })).toBeInTheDocument()
  })
})
