import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the product title', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /SkillEval/i })).toBeInTheDocument()
  })

  it('renders the tagline', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByText(/AI Agent \/ Skill 测试与 Trace 可视化/i)).toBeInTheDocument()
  })
})