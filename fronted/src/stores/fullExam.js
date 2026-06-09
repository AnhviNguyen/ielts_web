/**
 * Full IELTS mock exam session (4 skills) — persisted in sessionStorage.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'linguaielts_full_exam'

function load() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function save(session) {
  if (session) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  else sessionStorage.removeItem(STORAGE_KEY)
}

export const useFullExamStore = defineStore('fullExam', () => {
  const session = ref(load())

  function start(set, options = {}) {
    session.value = {
      sessionId: crypto.randomUUID(),
      setId: set.id,
      set,
      stage: 'reading',
      results: {},
      startedAt: Date.now(),
      placementMode: Boolean(options.placementMode),
    }
    save(session.value)
  }

  function getSession() {
    if (!session.value) session.value = load()
    return session.value
  }

  function recordStageResult(stage, payload) {
    const s = getSession()
    if (!s) return
    s.results[stage] = payload
    save(s)
  }

  function setStage(stage) {
    const s = getSession()
    if (!s) return
    s.stage = stage
    save(s)
  }

  function clear() {
    session.value = null
    save(null)
  }

  return { session, start, getSession, recordStageResult, setStage, clear }
})
