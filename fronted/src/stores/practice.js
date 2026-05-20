import { defineStore } from 'pinia'
import { ref } from 'vue'
import { practiceService } from '@/services/practiceService.js'

export const usePracticeStore = defineStore('practice', () => {
  const currentSession = ref(null)
  const lastResult = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function startSession(subject, quizId = null) {
    loading.value = true
    error.value = null
    try {
      currentSession.value =
        subject === 'reading'
          ? await practiceService.createReadingSession(quizId)
          : await practiceService.createListeningSession(quizId)
      return currentSession.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to start session'
      return null
    } finally {
      loading.value = false
    }
  }

  async function submitSession(subject, sessionId, answers) {
    loading.value = true
    error.value = null
    try {
      lastResult.value =
        subject === 'reading'
          ? await practiceService.submitReading({ session_id: sessionId, answers })
          : await practiceService.submitListening({ session_id: sessionId, answers })
      return lastResult.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to submit session'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchResult(sessionId) {
    loading.value = true
    error.value = null
    try {
      const payload = await practiceService.getResultBySession(sessionId)
      lastResult.value = payload?.history || null
      return lastResult.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load result'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchResultByQuiz(quizId) {
    loading.value = true
    error.value = null
    try {
      const payload = await practiceService.getResultByQuiz(quizId)
      lastResult.value = payload?.history || null
      return lastResult.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load result'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    currentSession,
    lastResult,
    loading,
    error,
    startSession,
    submitSession,
    fetchResult,
    fetchResultByQuiz,
  }
})
