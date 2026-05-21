/** Cache kết quả tra từ (RAM + localStorage) để mở lại gần như tức thì. */

const STORAGE_KEY = 'vocab-lookup-cache-v1'
const MAX_ENTRIES = 250

let memory = loadFromStorage()

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return new Map()
    const obj = JSON.parse(raw)
    return new Map(Object.entries(obj))
  } catch {
    return new Map()
  }
}

function persist() {
  try {
    const obj = Object.fromEntries(memory.entries())
    localStorage.setItem(STORAGE_KEY, JSON.stringify(obj))
  } catch {
    /* quota */
  }
}

export function getCachedLookup(word) {
  const key = normalizeKey(word)
  if (!key) return null
  return memory.get(key) ?? null
}

export function setCachedLookup(word, data) {
  const key = normalizeKey(word)
  if (!key || !data) return
  if (memory.has(key)) memory.delete(key)
  memory.set(key, { ...data, _cachedAt: Date.now() })
  while (memory.size > MAX_ENTRIES) {
    const first = memory.keys().next().value
    memory.delete(first)
  }
  persist()
}

function normalizeKey(word) {
  return String(word || '').replace(/[^a-zA-Z'-]/g, '').toLowerCase()
}
