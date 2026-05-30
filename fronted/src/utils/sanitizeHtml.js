/**
 * Sanitize HTML before v-html to reduce XSS risk from quiz/writing content.
 */
import DOMPurify from 'dompurify'

const DEFAULT_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'ol', 'ul', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'table',
    'thead', 'tbody', 'tr', 'th', 'td', 'img', 'sub', 'sup', 'blockquote', 'mark',
  ],
  ALLOWED_ATTR: ['class', 'style', 'src', 'alt', 'colspan', 'rowspan', 'id', 'title'],
}

export function sanitizeHtml(dirty) {
  if (dirty == null || dirty === '') return ''
  return DOMPurify.sanitize(String(dirty), DEFAULT_CONFIG)
}
