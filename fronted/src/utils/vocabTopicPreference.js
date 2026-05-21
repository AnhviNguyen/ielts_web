/** Lưu topic được chọn gần nhất khi lưu từ từ Reading/Listening. */

const STORAGE_KEY = 'vocab-last-save-topic-id'

export function getLastSaveTopicId() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const id = Number(raw)
    return Number.isFinite(id) && id > 0 ? id : null
  } catch {
    return null
  }
}

export function setLastSaveTopicId(topicId) {
  if (!topicId) return
  try {
    localStorage.setItem(STORAGE_KEY, String(topicId))
  } catch {
    /* ignore quota */
  }
}

/** Chọn topic mặc định: lần trước → topic đầu tiên. */
export function resolveDefaultTopicId(topics) {
  if (!topics?.length) return null
  const lastId = getLastSaveTopicId()
  if (lastId && topics.some((t) => t.id === lastId)) return lastId
  return topics[0].id
}
