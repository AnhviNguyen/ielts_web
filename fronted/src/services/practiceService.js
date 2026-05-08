import apiClient from '@/api/client.js'

export class PracticeService {
  async createReadingSession(quizId = null) {
    const params = {}
    if (quizId) params.quiz_id = quizId
    const { data } = await apiClient.get('/practice/reading/session', { params })
    return data
  }

  async createListeningSession(quizId = null) {
    const params = {}
    if (quizId) params.quiz_id = quizId
    const { data } = await apiClient.get('/practice/listening/session', { params })
    return data
  }

  async submitReading(payload) {
    const { data } = await apiClient.post('/practice/reading/submit', payload)
    return data
  }

  async submitListening(payload) {
    const { data } = await apiClient.post('/practice/listening/submit', payload)
    return data
  }

  async getHistory(params = {}) {
    const { data } = await apiClient.get('/practice/history', { params })
    return data
  }

  async getResultBySession(sessionId) {
    const { data } = await apiClient.get(`/practice/history/${sessionId}`)
    return data
  }
}

export const practiceService = new PracticeService()
