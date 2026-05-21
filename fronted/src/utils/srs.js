/**
 * SM-2 spaced repetition (Anki-style simplified).
 * quality: 0–5 (0–2 = fail, 3+ = pass)
 */

export function sm2Next(card, quality) {
  let ease = Number(card.srs_ease ?? 2.5)
  let interval = Number(card.srs_interval_days ?? 0)
  let reps = Number(card.srs_repetitions ?? 0)

  if (quality < 3) {
    reps = 0
    interval = 1
  } else {
    if (reps === 0) interval = 1
    else if (reps === 1) interval = 6
    else interval = Math.max(1, Math.round(interval * ease))
    reps += 1
    ease += 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    if (ease < 1.3) ease = 1.3
  }

  const next = new Date()
  next.setDate(next.getDate() + interval)

  let mastery = 'learning'
  if (reps >= 2 && interval >= 21) mastery = 'mastered'
  else if (reps >= 1) mastery = 'learning'

  return {
    srs_ease: Math.round(ease * 100) / 100,
    srs_interval_days: interval,
    srs_repetitions: reps,
    srs_next_review_at: next.toISOString(),
    mastery,
  }
}

/** Map flashcard buttons to SM-2 quality */
export function qualityFromFlashcard(knew) {
  return knew ? 4 : 1
}

export function qualityFromMcq(correct) {
  return correct ? 4 : 2
}
