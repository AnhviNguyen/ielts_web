/** Helpers to match hub cards with history quiz_id / topic_id. */

export function toIdSet(ids) {
  return new Set((ids || []).map((id) => String(id)))
}

export function mockTestCompletion(mt, completedIds) {
  const quizzes = mt?.quizzes || {}
  const fullId = quizzes.full?.id
  const fullCompleted = Boolean(fullId && completedIds.has(String(fullId)))
  const completedPartKeys = Object.entries(quizzes)
    .filter(([key]) => key.startsWith('part_'))
    .filter(([, meta]) => meta?.id && completedIds.has(String(meta.id)))
    .map(([key]) => key)
  const attempted = fullCompleted || completedPartKeys.length > 0
  return { fullCompleted, completedPartKeys, attempted }
}

export function writingSetCompletion(set, completedIds) {
  const task1Done = Boolean(set?.task1_topic_id && completedIds.has(String(set.task1_topic_id)))
  const task2Done = Boolean(set?.task2_topic_id && completedIds.has(String(set.task2_topic_id)))
  return {
    task1Done,
    task2Done,
    attempted: task1Done || task2Done,
    fullyDone: task1Done && task2Done,
  }
}
