import apiClient from '@/api/client.js'

export async function getPlacementStatus() {
  const { data } = await apiClient.get('/placement/status')
  return data
}

export async function submitManualPlacement(body) {
  const { data } = await apiClient.post('/placement/manual', body)
  return data
}

export async function finalizeFullExamPlacement(body) {
  const { data } = await apiClient.post('/placement/full-exam/finalize', body)
  return data
}

export async function createPlacementSession() {
  const { data } = await apiClient.post('/placement/sessions')
  return data
}

export async function getCurrentPlacementSession() {
  const { data } = await apiClient.get('/placement/sessions/current')
  return data
}

export async function getPlacementStage(sessionId, stage) {
  const { data } = await apiClient.get(`/placement/sessions/${sessionId}/stage/${stage}`)
  return data
}

export async function submitPlacementStage(sessionId, stage, body) {
  const { data } = await apiClient.post(`/placement/sessions/${sessionId}/stage/${stage}/submit`, body)
  return data
}

export async function finalizePlacement(sessionId) {
  const { data } = await apiClient.post(`/placement/sessions/${sessionId}/finalize`)
  return data
}
