import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
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