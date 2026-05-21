/**
 * Streaming vocabulary lookup via backend OpenRouter proxy.
 */

function _parseSseChunk(buffer) {
  const events = []
  const parts = buffer.split('\n\n')
  const remainder = parts.pop() || ''
  for (const block of parts) {
    const line = block.split('\n').find((l) => l.startsWith('data: '))
    if (!line) continue
    try {
      events.push(JSON.parse(line.slice(6)))
    } catch {
      /* ignore */
    }
  }
  return { events, remainder }
}

/**
 * @param {string} word
 * @param {{ onPatch?: (partial: object) => void, onDone?: (result: object) => void, onError?: (msg: string) => void }} handlers
 */
export async function streamLookupWord(word, { onPatch, onDone, onError } = {}) {
  const token = localStorage.getItem('token')
  const url = `/api/vocabulary/lookup/stream?word=${encodeURIComponent(word)}`

  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg = err.detail || err.error || `HTTP ${res.status}`
    onError?.(typeof msg === 'string' ? msg : 'Tra từ thất bại')
    throw new Error(msg)
  }

  const reader = res.body?.getReader()
  if (!reader) {
    onError?.('Streaming không được hỗ trợ')
    throw new Error('no stream')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const { events, remainder } = _parseSseChunk(buffer)
    buffer = remainder
    for (const ev of events) {
      if (ev.error) {
        onError?.(ev.error)
        throw new Error(ev.error)
      }
      if (ev.patch) onPatch?.(ev.patch)
      if (ev.done && ev.result) onDone?.(ev.result)
    }
  }

  if (buffer.trim()) {
    const { events } = _parseSseChunk(buffer + '\n\n')
    for (const ev of events) {
      if (ev.patch) onPatch?.(ev.patch)
      if (ev.done && ev.result) onDone?.(ev.result)
    }
  }
}
