/**
 * Shadowing segment helpers — scoring, tokenization, YouTube ID.
 */

const YT_PATTERNS = [
  /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
  /^([a-zA-Z0-9_-]{11})$/,
]

export function extractYoutubeVideoId(url) {
  const s = (url || '').trim()
  for (const pat of YT_PATTERNS) {
    const m = s.match(pat)
    if (m) return m[1]
  }
  return null
}

/** YouTube thumbnail URL (mqdefault ≈ 320×180). */
export function youtubeThumbnail(videoId, quality = 'mqdefault') {
  if (!videoId) return ''
  return `https://i.ytimg.com/vi/${videoId}/${quality}.jpg`
}

export function tokenizeWords(text) {
  return (text || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
}

function normalizeToken(w) {
  return w.toLowerCase().replace(/[^\w']/g, '')
}

/**
 * Dictation scoring — ignore case & punctuation.
 * @returns {{ correct: string[], wrong: string[], missing: string[], score: number }}
 */
export function scoreAnswer(userInput, correct) {
  const target = tokenizeWords(correct).map(normalizeToken).filter(Boolean)
  const user = tokenizeWords(userInput).map(normalizeToken).filter(Boolean)

  const correctWords = []
  const wrong = []
  const missing = []

  const maxLen = Math.max(target.length, user.length)
  for (let i = 0; i < maxLen; i++) {
    const t = target[i]
    const u = user[i]
    if (!t && u) {
      wrong.push(user[i] ?? u)
    } else if (t && !u) {
      missing.push(correct.split(/\s+/)[i] ?? t)
    } else if (t && u) {
      if (t === u) correctWords.push(correct.split(/\s+/)[i] ?? t)
      else wrong.push(user[i] ?? u)
    }
  }

  const score = target.length
    ? Math.round((correctWords.length / target.length) * 100)
    : 0

  return { correct: correctWords, wrong, missing, score }
}

/**
 * Pronunciation scoring from Web Speech transcript vs target.
 */
export function scorePronunciation(spokenText, targetText) {
  const target = tokenizeWords(targetText).map(normalizeToken).filter(Boolean)
  const spoken = tokenizeWords(spokenText).map(normalizeToken).filter(Boolean)

  const wordResults = target.map((t, i) => {
    const s = spoken[i]
    return {
      word: tokenizeWords(targetText)[i] || t,
      ok: s === t,
      spoken: spoken[i] || null,
    }
  })

  const extra = spoken.slice(target.length)
  const correctCount = wordResults.filter((w) => w.ok).length
  const score = target.length
    ? Math.round((correctCount / target.length) * 100)
    : 0

  return { wordResults, extra, score }
}

export function formatTimestamp(seconds) {
  const s = Math.max(0, Number(seconds) || 0)
  const m = Math.floor(s / 60)
  const sec = (s % 60).toFixed(1)
  return `${m}:${sec.padStart(4, '0')}`
}
