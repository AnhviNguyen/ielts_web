import { defineStore } from 'pinia'
import { ref } from 'vue'
import { practiceService } from '@/services/practiceService.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'

export const usePracticeStore = defineStore('practice', () => {
  const currentSession = ref(null)
  const lastResult = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const sessionStartedAt = ref(null)

  async function startSession(subject, quizId = null) {
    loading.value = true
    error.value = null
    sessionStartedAt.value = Date.now()
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
    const duration_seconds = sessionStartedAt.value
      ? Math.floor((Date.now() - sessionStartedAt.value) / 1000)
      : 0
    try {
      const payload = { session_id: sessionId, answers, duration_seconds }
      lastResult.value =
        subject === 'reading'
          ? await practiceService.submitReading(payload)
          : await practiceService.submitListening(payload)
      useBadgeCelebrationStore().enqueue(lastResult.value?.new_badges)
      return lastResult.value
    } catch (err) {
      const detail = err.response?.data?.detail
      const already =
        err.response?.status === 400 &&
        typeof detail === 'string' &&
        detail.toLowerCase().includes('already submitted')
      if (already && sessionId) {
        try {
          lastResult.value = await practiceService.getResultBySession(sessionId)
          return lastResult.value
        } catch {
          /* fall through */
        }
      }
      error.value = detail || 'Failed to submit session'
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

  async function checkAnswer(sessionId, questionId, userAnswer) {
    try {
      return await practiceService.checkAnswer({
        session_id: sessionId,
        question_id: questionId,
        user_answer: userAnswer,
      })
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to check answer'
      return null
    }
  }

  return {
    currentSession,
    lastResult,
    loading,
    error,
    startSession,
    submitSession,
    checkAnswer,
    fetchResult,
    fetchResultByQuiz,
  }
})
