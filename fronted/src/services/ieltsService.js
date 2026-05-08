import apiClient from '@/api/client.js'

export class IeltsService {
  async getHistory(params = {}) {
    const { data } = await apiClient.get('/practice/history', { params })
    return data
  }

  async getProgress() {
    const { data } = await apiClient.get('/progress')
    return data
  }

  async getUserStats() {
    const { data } = await apiClient.get('/user/stats')
    return data
  }

  async getPracticeHistory(params = {}) {
    const { data } = await apiClient.get('/practice/history', { params })
    return data
  }

  async getStreak() {
    const { data } = await apiClient.get('/users/me/streak')
    return data
  }

  async getStudyPlan() {
    const { data } = await apiClient.get('/users/me/study-plan')
    return data
  }

  async generateStudyPlan() {
    const { data } = await apiClient.post('/users/me/study-plan/generate')
    return data
  }

  async askDashboardCoach({ userMessage, history = [] }) {
    const { data } = await apiClient.post('/users/me/chat', {
      user_message: userMessage,
      history,
    })
    return data
  }
}

export const ieltsService = new IeltsService()
