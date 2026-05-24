/**
 * Navigation helpers for full mock exam flow.
 */
export const FULL_EXAM_STAGES = ['reading', 'listening', 'writing', 'speaking']

export function fullExamQuery(sessionId) {
  return { fullExam: '1', session: sessionId }
}

export function nextStage(current) {
  const i = FULL_EXAM_STAGES.indexOf(current)
  return i >= 0 && i < FULL_EXAM_STAGES.length - 1 ? FULL_EXAM_STAGES[i + 1] : null
}

/** Route to optional break screen before the next section. */
export function breakRoute(session, afterStage) {
  return {
    path: '/full-exam/break',
    query: { session: session.sessionId, after: afterStage },
  }
}

export function stageRoute(router, session, stage) {
  const set = session.set
  const q = fullExamQuery(session.sessionId)

  if (stage === 'reading') {
    return { path: `/quiz/${set.reading_quiz_id}`, query: { ...q, stage: 'reading' } }
  }
  if (stage === 'listening') {
    return { path: `/quiz/${set.listening_quiz_id}`, query: { ...q, stage: 'listening' } }
  }
  if (stage === 'writing') {
    return { path: `/full-exam/writing`, query: q }
  }
  if (stage === 'speaking') {
    return { path: `/quiz/${set.speaking_quiz_id}`, query: { ...q, stage: 'speaking' } }
  }
  if (stage === 'done') {
    return { path: '/full-exam/result', query: q }
  }
  return { path: '/full-exam' }
}
