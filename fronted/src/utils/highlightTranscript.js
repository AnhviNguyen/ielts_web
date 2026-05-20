/**
 * Build safe HTML from plain transcript with non-overlapping span highlights.
 * @param {string} text
 * @param {Array<{ text: string, className: string, title?: string }>} spans
 */
export function highlightTranscript(text, spans = []) {
  const raw = String(text || '')
  if (!raw) return ''

  const escape = (s) =>
    String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')

  const ranges = []
  for (const span of spans) {
    const needle = String(span.text || '').trim()
    if (!needle) continue
    let from = 0
    while (from < raw.length) {
      const idx = raw.indexOf(needle, from)
      if (idx === -1) break
      ranges.push({
        start: idx,
        end: idx + needle.length,
        className: span.className,
        title: span.title || '',
      })
      from = idx + needle.length
    }
  }

  if (!ranges.length) return escape(raw)

  ranges.sort((a, b) => a.start - b.start || b.end - a.end)
  const merged = []
  for (const r of ranges) {
    const last = merged[merged.length - 1]
    if (!last || r.start >= last.end) {
      merged.push({ ...r })
      continue
    }
    if (r.end > last.end) last.end = r.end
  }

  let html = ''
  let cursor = 0
  for (const r of merged) {
    if (r.start > cursor) html += escape(raw.slice(cursor, r.start))
    const titleAttr = r.title ? ` title="${escape(r.title)}"` : ''
    html += `<mark class="${r.className}"${titleAttr}>${escape(raw.slice(r.start, r.end))}</mark>`
    cursor = r.end
  }
  if (cursor < raw.length) html += escape(raw.slice(cursor))
  return html
}
