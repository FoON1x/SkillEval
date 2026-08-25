import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import ThemeProvider from './ThemeProvider'
import ThemeToggle from './ThemeToggle'
import { useTheme } from './useTheme'
import indexHtml from '../../index.html?raw'

function stubMatchMedia(matches = false) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }))
}

function firstResolvedProbe() {
  let captured = false
  let value: 'light' | 'dark' | null = null
  function CapturingProbe() {
    const { resolved } = useTheme()
    if (!captured) {
      captured = true
      value = resolved
    }
    return null
  }
  return {
    CapturingProbe,
    get: () => value,
  }
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    stubMatchMedia()
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

  it('first-frame resolved matches saved mode, not system', () => {
    stubMatchMedia(false)
    localStorage.setItem('skilleval-theme', 'dark')
    const probe = firstResolvedProbe()
    render(
      <ThemeProvider>
        <probe.CapturingProbe />
      </ThemeProvider>,
    )
    expect(probe.get()).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})

describe('index.html FOUC guard', () => {
  it('contains a pre-hydration script that reads skilleval-theme and prefers-color-scheme', () => {
    expect(indexHtml).toContain('skilleval-theme')
    expect(indexHtml).toContain('prefers-color-scheme: dark')
    expect(indexHtml).toContain('classList.add(')
  })
})
