import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the product title', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /SkillEval/i })).toBeInTheDocument()
  })

  it('renders the tagline', () => {
    render(<App />)
    expect(screen.getByText(/AI Agent \/ Skill 测试与 Trace 可视化平台/i)).toBeInTheDocument()
  })
})