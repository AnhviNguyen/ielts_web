import apiClient from '@/api/client.js'

export async function listMockTests({ skillId } = {}) {
  const params = {}
  if (skillId) params.skill_id = skillId
  const res = await apiClient.get('/mock-tests', { params, timeout: 30000 })
  return res.data?.data ?? []
}

export async function getMockTest(id) {
  const res = await apiClient.get(`/mock-tests/${id}`)
  return res.data?.data
}

export async function getQuiz(quizId) {
  const res = await apiClient.get(`/quizzes/${quizId}`, { timeout: 45000 })
  const body = res.data
  return body?.data ?? body
}

