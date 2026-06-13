import { toRaw } from 'vue'

/** Clone speaking result payload for router history (avoids DataCloneError on Vue proxies). */
export function speakingResultState(payload) {
  if (!payload) return {}
  const raw = toRaw(payload)
  const state = {
    audioUrl: raw.audioUrl || '',
    question: raw.question || '',
  }
  if (raw.result) {
    state.result = JSON.parse(JSON.stringify(raw.result))
  }
  if (raw.summary) {
    state.summary = JSON.parse(JSON.stringify(raw.summary))
  }
  if (raw.mode) state.mode = raw.mode
  if (raw.fetchSummary) state.fetchSummary = true
  if (raw.quiz_id != null) state.quiz_id = raw.quiz_id
  return state
}
