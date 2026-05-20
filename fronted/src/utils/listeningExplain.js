import { buildParagraphsFromVocabs } from '@/utils/mockQuiz.js'

/** Strip HTML tags to detect empty explain fields in JSON. */
export function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return (tmp.textContent || tmp.innerText || '').trim()
}

/**
 * Timestamp for "Go to" — prefer listen_from, else first vocab segment in locate_info range.
 */
export function resolveListenTimestamp(question, paragraphs = []) {
  const from = Number(question?.listen_from)
  if (Number.isFinite(from) && from >= 0) return from

  const loc = question?.locate_info?.paragraph_ranges?.[0]
  if (!loc || !paragraphs.length) return undefined

  const para = paragraphs.find((p) => p.paragraph === loc.start?.paragraph)
  if (!para?.children?.length) return undefined

  const sentenceIdx = Math.max(0, (loc.start?.sentence || 1) - 1)
  const child = para.children[sentenceIdx] || para.children[0]
  const t = Number(child?.from)
  return Number.isFinite(t) ? t : undefined
}

/** Extract transcript text for a question from vocabs + locate_info. */
export function extractTranscriptSnippet(paragraphs, locateInfo) {
  const ranges = locateInfo?.paragraph_ranges || []
  if (!ranges.length || !paragraphs.length) return ''

  const chunks = []
  for (const r of ranges) {
    const startP = r.start?.paragraph
    const endP = r.end?.paragraph ?? startP
    if (!Number.isFinite(startP)) continue
    for (let p = startP; p <= (endP || startP); p++) {
      const para = paragraphs.find((x) => x.paragraph === p)
      if (para?.text) chunks.push(para.text)
    }
  }
  return chunks.join(' ').trim()
}

/**
 * Build explanation HTML: official `explain` from JSON, or fallback from đáp án + transcript.
 */
export function buildListeningExplainHtml(question, partVocabs = []) {
  const official = stripHtml(question?.explain || question?.explanation || '')
  if (official) return question.explain || question.explanation

  const paragraphs = buildParagraphsFromVocabs(partVocabs || [])
  const snippet = extractTranscriptSnippet(paragraphs, question?.locate_info)
  const correct =
    (question?.correct_answers || []).filter(Boolean).join(', ') ||
    question?.correct_answer ||
    ''

  const parts = []
  if (correct) {
    parts.push(`<p><strong>Đáp án đúng:</strong> ${escapeHtml(correct)}</p>`)
  }
  if (snippet) {
    parts.push(
      `<p><strong>Đoạn audio liên quan:</strong></p>` +
        `<blockquote style="margin:8px 0;padding:10px 12px;border-left:3px solid #34d399;background:#f0fdf4;font-size:13px;line-height:1.5">` +
        `${escapeHtml(snippet)}</blockquote>`
    )
  }
  if (!parts.length) return ''
  return parts.join('')
}

export function hasListeningExplain(question, partVocabs = []) {
  const html = buildListeningExplainHtml(question, partVocabs)
  return Boolean(stripHtml(html))
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
