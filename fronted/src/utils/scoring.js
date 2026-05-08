import { isListeningQuiz } from '@/utils/mockQuiz.js'

function normalizeText(s) {
  return String(s ?? '').trim().toLowerCase()
}

export function isCorrectAnswer({ question, userAnswer }) {
  const q = question || {}

  // Multi-answers (gap filling, multiple-choice-many)
  if (Array.isArray(q.correct_answers) && q.correct_answers.length) {
    if (Array.isArray(userAnswer)) {
      const ua = userAnswer.map(normalizeText).sort().join('|')
      const ca = q.correct_answers.map(normalizeText).sort().join('|')
      return ua === ca
    }
    const ua = normalizeText(userAnswer)
    return q.correct_answers.some((a) => normalizeText(a) === ua)
  }

  if (q.correct_answer !== undefined && q.correct_answer !== null && q.correct_answer !== '') {
    return normalizeText(userAnswer) === normalizeText(q.correct_answer)
  }

  return false
}

export function scoreQuiz({ quiz, flat, answers }) {
  const detailed = []
  let correct = 0
  for (const item of flat) {
    const q = item.question
    const userAnswer = answers?.[q?.id]
    const ok = isCorrectAnswer({ question: q, userAnswer })
    if (ok) correct += 1
    detailed.push({
      order: q?.order,
      questionId: q?.id,
      text: q?.text,
      userAnswer,
      correct_answer: q?.correct_answer,
      correct_answers: q?.correct_answers,
      isCorrect: ok,
      explain: q?.explain || '',
    })
  }

  return {
    correct,
    total: flat.length,
    estimatedBand: estimateBand({ quiz, raw: correct }),
    detailed,
  }
}

export function estimateBand({ quiz, raw }) {
  const listening = isListeningQuiz(quiz)
  const score = Number(raw) || 0

  // Approximate IELTS conversion (common Cambridge ranges). Works for both Reading/Listening.
  const table = listening
    ? [
      [39, 9], [37, 8.5], [35, 8], [32, 7.5], [30, 7], [26, 6.5], [23, 6], [18, 5.5],
      [16, 5], [13, 4.5], [11, 4], [8, 3.5], [6, 3], [4, 2.5], [0, 2],
    ]
    : [
      [39, 9], [37, 8.5], [35, 8], [33, 7.5], [30, 7], [27, 6.5], [23, 6], [19, 5.5],
      [15, 5], [13, 4.5], [10, 4], [8, 3.5], [6, 3], [4, 2.5], [0, 2],
    ]

  for (const [min, band] of table) {
    if (score >= min) return band
  }
  return 0
}

