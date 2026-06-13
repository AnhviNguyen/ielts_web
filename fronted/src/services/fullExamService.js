import apiClient from '@/api/client.js'

export async function listFullExamSets(limit = 30) {
  const { data } = await apiClient.get('/mock-exams/sets', { params: { limit } })
  return data?.items ?? []
}
