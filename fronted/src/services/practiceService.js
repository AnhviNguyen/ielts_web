import apiClient from '@/api/client.js'

export class PracticeService {
  async createReadingSession(quizId = null) {
    const params = {}
    if (quizId) params.quiz_id = quizId
    const { data } = await apiClient.get('/practice/reading/session', { params, timeout: 45000 })
    return data
  }

  async createListeningSession(quizId = null) {
    const params = {}
    if (quizId) params.quiz_id = quizId
    const { data } = await apiClient.get('/practice/listening/session', { params, timeout: 45000 })
    return data
  }

  async submitReading(payload) {
    const { data } = await apiClient.post('/practice/reading/submit', payload, { timeout: 60000 })
    return data
  }

  async submitListening(payload) {
    const { data } = await apiClient.post('/practice/listening/submit', payload, { timeout: 60000 })
    return data
  }

  async getHistory(params = {}) {
    const { data } = await apiClient.get('/history', { params })
    return data
  }

  async getResultBySession(sessionId) {
    const { data } = await apiClient.get(`/history/sessions/${sessionId}`)
    return data
  }

  async getResultByQuiz(quizId) {
    const { data } = await apiClient.get(`/history/quiz/${quizId}`)
    return data
  }
}

export const practiceService = new PracticeService()
