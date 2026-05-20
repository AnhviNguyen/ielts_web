import apiClient from '@/api/client.js'

export class IeltsService {
  // ── History & Progress ──────────────────────────────────────────
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

  // ── Skill Radar ─────────────────────────────────────────────────
  async getSkillRadar() {
    const { data } = await apiClient.get('/users/me/skill-radar')
    return data
  }

  // ── Study Plan ──────────────────────────────────────────────────
  async getStudyPlan() {
    const { data } = await apiClient.get('/users/me/study-plan')
    return data
  }

  async generateStudyPlan() {
    const { data } = await apiClient.post('/users/me/study-plan/generate')
    return data
  }

  async extendStudyPlan() {
    const { data } = await apiClient.post('/users/me/study-plan/extend')
    return data
  }

  async completeStudyTask(taskId) {
    const { data } = await apiClient.patch(`/users/me/study-plan/${taskId}/complete`)
    return data
  }

  // ── Dashboard Chatbot ───────────────────────────────────────────
  async askDashboardCoach({ userMessage, history = [] }) {
    const { data } = await apiClient.post('/users/me/chat', {
      user_message: userMessage,
      history,
    })
    return data
  }
}

export const ieltsService = new IeltsService()
