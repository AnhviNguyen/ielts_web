export function normalizeVocabAnswer(s) {
  return String(s || '').trim().toLowerCase().replace(/[^a-z0-9'-]/gi, '')
}

export function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function exampleWithBlank(word) {
  if (!word?.example) return ''
  const re = new RegExp(`\\b${escapeRegExp(word.word)}\\b`, 'gi')
  return word.example.replace(re, '_____')
}
