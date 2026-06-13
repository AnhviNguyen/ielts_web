function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function escapeRegex(text) {
  return String(text || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Build HTML for essay with inline grammar (rose) and vocabulary (amber) marks.
 */
export function buildAnnotatedEssayHtml(essay, grammarErrors = [], weakWords = []) {
  const source = String(essay || '')
  if (!source) return ''

  const marks = []

  const pushMarks = (phrase, type, meta, priority) => {
    const trimmed = String(phrase || '').trim()
    if (trimmed.length < 2) return
    const escaped = escapeRegex(trimmed)
    const re = /\s/.test(trimmed)
      ? new RegExp(escaped, 'gi')
      : new RegExp(`\\b${escaped}\\b`, 'gi')
    let match
    while ((match = re.exec(source)) !== null) {
      marks.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
        type,
        meta,
        priority,
      })
    }
  }

  for (const err of grammarErrors) {
    pushMarks(err?.original, 'grammar', err, 2)
  }
  for (const w of weakWords) {
    pushMarks(w?.word, 'vocab', w, 1)
  }

  if (!marks.length) {
    return escapeHtml(source).replace(/\n/g, '<br>')
  }

  marks.sort((a, b) => a.start - b.start || b.priority - a.priority || (b.end - b.start) - (a.end - a.start))

  const merged = []
  let cursor = 0
  for (const m of marks) {
    if (m.start < cursor) continue
    merged.push(m)
    cursor = m.end
  }

  let html = ''
  let pos = 0
  for (const m of merged) {
    html += escapeHtml(source.slice(pos, m.start))
    const title =
      m.type === 'grammar'
        ? `Sửa: ${m.meta?.correction || ''}${m.meta?.rule ? ` — ${m.meta.rule}` : ''}`
        : `Gợi ý: ${m.meta?.better || ''}${m.meta?.reason ? ` — ${m.meta.reason}` : ''}`
    const cls =
      m.type === 'grammar'
        ? 'writing-mark writing-mark--grammar'
        : 'writing-mark writing-mark--vocab'
    html += `<mark class="${cls}" title="${escapeHtml(title)}">${escapeHtml(m.text)}</mark>`
    pos = m.end
  }
  html += escapeHtml(source.slice(pos))
  return html.replace(/\n/g, '<br>')
}
