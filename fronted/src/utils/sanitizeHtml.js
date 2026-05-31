/**
 * Sanitize HTML before v-html.
 *
 * Two levels:
 *  - sanitizeHtml()      → strict, for user-generated content (chat, profile, writing feedback)
 *  - sanitizeQuizHtml()  → allows style/border on table elements, for trusted admin quiz JSON data
 */
import DOMPurify from 'dompurify'

// Safe CSS properties allowed in quiz content (IELTS table/heading formatting)
const _SAFE_STYLE_PROPS = new Set([
  'text-align', 'font-weight', 'font-style', 'color', 'background-color',
  'border', 'border-color', 'border-collapse', 'border-style', 'border-width',
  'padding', 'padding-left', 'padding-right', 'padding-top', 'padding-bottom',
  'margin', 'margin-left', 'margin-right', 'margin-top', 'margin-bottom',
  'width', 'max-width', 'height', 'vertical-align',
])

// Strip dangerous CSS values (javascript: protocol, expression(), etc.)
function _sanitizeStyleValue(value) {
  if (!value) return ''
  if (/javascript\s*:/i.test(value)) return ''
  if (/expression\s*\(/i.test(value)) return ''
  return value
}

// DOMPurify hook: strips unsafe CSS properties from style attributes
function _addStyleHook() {
  DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
    if (data.attrName !== 'style') return
    const declarations = data.attrValue
      .split(';')
      .map((d) => d.trim())
      .filter(Boolean)
      .filter((d) => {
        const [prop] = d.split(':')
        return _SAFE_STYLE_PROPS.has((prop || '').trim().toLowerCase())
      })
      .map((d) => {
        const idx = d.indexOf(':')
        const prop = d.slice(0, idx).trim()
        const val = _sanitizeStyleValue(d.slice(idx + 1).trim())
        return val ? `${prop}: ${val}` : null
      })
      .filter(Boolean)
    data.attrValue = declarations.join('; ')
    if (!data.attrValue) data.keepAttr = false
  })
}

_addStyleHook()

const _COMMON_TAGS = [
  'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'ol', 'ul', 'li',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div',
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
  'img', 'sub', 'sup', 'blockquote', 'mark', 'code', 'pre',
]

// ── Strict config: user content, chat messages, writing feedback ──────────────
const _STRICT_CONFIG = {
  ALLOWED_TAGS: _COMMON_TAGS,
  ALLOWED_ATTR: ['class', 'alt', 'colspan', 'rowspan', 'title', 'data-question-id'],
  FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick', 'onmouseover'],
  ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):|\/(?:images|audio|media|uploads)\/|[^a-z]|[a-z+.-]+(?:[^a-z+.-:]|$))/i,
}

// ── Quiz config: trusted admin JSON data (IELTS tables, headings, GAP_FILLING, images) ─
const _QUIZ_CONFIG = {
  ALLOWED_TAGS: _COMMON_TAGS,
  ALLOWED_ATTR: [
    'class', 'style', 'src', 'alt', 'colspan', 'rowspan', 'title',
    'data-question-id', 'border', 'width', 'height', 'cellpadding', 'cellspacing',
    'align', 'valign', 'loading',
  ],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'href'],
  // Allow https:// external images (cms.youpass.vn) and local data-assets paths
  ALLOWED_URI_REGEXP: /^(?:(?:https?):|\/(?:images|audio|media|uploads|data-assets)\/|[^a-z]|[a-z+.-]+(?:[^a-z+.-:]|$))/i,
}

/**
 * Strict sanitizer — use for user-generated content (chat, profile, writing feedback).
 * Strips all inline styles.
 */
export function sanitizeHtml(dirty) {
  if (dirty == null || dirty === '') return ''
  return DOMPurify.sanitize(String(dirty), _STRICT_CONFIG)
}

/**
 * Quiz-safe sanitizer — use for IELTS question content, GAP_FILLING tables,
 * passage titles, and instruction HTML from trusted admin JSON data.
 * Allows safe inline styles (text-align, border-color, etc.) but strips JS.
 */
export function sanitizeQuizHtml(dirty) {
  if (dirty == null || dirty === '') return ''
  return DOMPurify.sanitize(String(dirty), _QUIZ_CONFIG)
}
