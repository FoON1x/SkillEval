import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import ThemeProvider from './ThemeProvider'
import ThemeToggle from './ThemeToggle'

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
})
