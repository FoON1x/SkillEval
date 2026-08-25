export const BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`
    try {
      const body = await resp.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* ignore */
    }
    throw new ApiError(resp.status, detail)
  }
  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

interface StreamHandlers {
  onEvent: (node: unknown) => void
  onDone: (traceId: string) => void
  onError: (message: string) => void
  signal?: AbortSignal
}

export async function postStream(path: string, body: unknown, h: StreamHandlers): Promise<void> {
  const resp = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: h.signal,
  })
  if (!resp.ok || !resp.body) {
    h.onError(`HTTP ${resp.status}`)
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let terminated = false
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 2)
      if (!frame.startsWith('data: ')) continue
      let data: { type: string; node?: unknown; trace_id?: string; message?: string }
      try {
        data = JSON.parse(frame.slice(6))
      } catch {
        continue
      }
      if (data.type === 'event' && data.node) h.onEvent(data.node)
      else if (data.type === 'done' && data.trace_id) {
        h.onDone(data.trace_id)
        terminated = true
        return
      } else if (data.type === 'error') {
        h.onError(data.message ?? '运行失败')
        terminated = true
        return
      }
    }
  }
  if (!terminated) h.onError('连接中断')
}
