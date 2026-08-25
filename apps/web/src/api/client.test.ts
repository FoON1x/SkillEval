import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { postStream } from './client'

describe('postStream', () => {
  let originalFetch: typeof globalThis.fetch
  beforeEach(() => {
    originalFetch = globalThis.fetch
  })
  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  function streamResponse(frames: string[] = [], { immediateClose = false } = {}): Response {
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        for (const f of frames) controller.enqueue(encoder.encode(f))
        if (!immediateClose) {
          controller.close()
        } else {
          controller.close()
        }
      },
    })
    return new Response(stream, {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    })
  }

  it('calls onDone when the server sends a done frame', async () => {
    const onDone = vi.fn()
    const onError = vi.fn()
    const onEvent = vi.fn()
    globalThis.fetch = vi.fn(async () =>
      streamResponse(['data: {"type":"done","trace_id":"t1"}\n\n']),
    ) as unknown as typeof globalThis.fetch

    await postStream('/p', {}, { onEvent, onDone, onError })

    expect(onDone).toHaveBeenCalledWith('t1')
    expect(onError).not.toHaveBeenCalled()
  })

  it('calls onError when the server sends an error frame', async () => {
    const onDone = vi.fn()
    const onError = vi.fn()
    const onEvent = vi.fn()
    globalThis.fetch = vi.fn(async () =>
      streamResponse(['data: {"type":"error","message":"boom"}\n\n']),
    ) as unknown as typeof globalThis.fetch

    await postStream('/p', {}, { onEvent, onDone, onError })

    expect(onError).toHaveBeenCalledWith('boom')
    expect(onDone).not.toHaveBeenCalled()
  })

  it('calls onError when the stream ends without a terminal frame', async () => {
    const onDone = vi.fn()
    const onError = vi.fn()
    const onEvent = vi.fn()
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('data: {"type":"event","node":{"node_type":"agent_step"}}\n\n'))
        controller.close()
      },
    })
    globalThis.fetch = vi.fn(async () =>
      new Response(stream, {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      }),
    ) as unknown as typeof globalThis.fetch

    await postStream('/p', {}, { onEvent, onDone, onError })

    expect(onEvent).toHaveBeenCalledTimes(1)
    expect(onDone).not.toHaveBeenCalled()
    expect(onError).toHaveBeenCalledWith('连接中断')
  })

  it('calls onError when the reader yields done immediately with no frames', async () => {
    const onDone = vi.fn()
    const onError = vi.fn()
    const onEvent = vi.fn()
    const stream = new ReadableStream({
      start(controller) {
        controller.close()
      },
    })
    globalThis.fetch = vi.fn(async () =>
      new Response(stream, {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      }),
    ) as unknown as typeof globalThis.fetch

    await postStream('/p', {}, { onEvent, onDone, onError })

    expect(onDone).not.toHaveBeenCalled()
    expect(onError).toHaveBeenCalledWith('连接中断')
  })
})
