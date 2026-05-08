import apiClient from '@/api/client.js'

export async function listMockTests({ skillId } = {}) {
  const params = {}
  if (skillId) params.skill_id = skillId
  const res = await apiClient.get('/mock-tests', { params })
  return res.data?.data ?? []
}

export async function getMockTest(id) {
  const res = await apiClient.get(`/mock-tests/${id}`)
  return res.data?.data
}

export async function getQuiz(quizId) {
  const res = await apiClient.get(`/quizzes/${quizId}`)
  return res.data?.data
}

export async function listWritingTopics({ taskType, page = 1, pageSize = 20 } = {}) {
  const params = { page, page_size: pageSize }
  if (taskType) params.task_type = taskType
  const res = await apiClient.get('/writing/topics', { params })
  return res.data?.data ?? { items: [], total: 0, page, page_size: pageSize }
}

