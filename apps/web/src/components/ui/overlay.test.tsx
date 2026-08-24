import { render, screen, fireEvent, act } from '@testing-library/react'
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
    expect(fn).toHaveBeenCalledTimes(1)
  })
  it('does not call onClose when clicking inside the panel', () => {
    const fn = vi.fn()
    render(<Modal open={true} onClose={fn} title="选目录">树内容</Modal>)
    fireEvent.click(screen.getByText('树内容').parentElement!)
    expect(fn).not.toHaveBeenCalled()
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
    act(() => { vi.advanceTimersByTime(4100) })
    expect(screen.queryByText('已保存')).not.toBeInTheDocument()
  })
})
