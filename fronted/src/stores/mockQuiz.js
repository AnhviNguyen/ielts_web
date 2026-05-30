import { defineStore } from 'pinia'
import { getQuiz } from '@/services/mockTestService.js'
import { flattenQuizQuestions } from '@/utils/mockQuiz.js'

export const useMockQuizStore = defineStore('mockQuiz', {
  state: () => ({
    loading: false,
    quiz: null,
    flat: [],
    answers: {}, // questionId -> string | string[]
    currentOrder: null, // question.order
    remainingSeconds: 0,
    _timer: null,
    result: null,
  }),

  getters: {
    totalQuestions: (s) => s.flat.length,
    answeredCount: (s) => Object.keys(s.answers || {}).length,
    currentIndex: (s) => {
      if (!s.flat.length) return -1
      const idx = s.flat.findIndex((x) => x.question?.order === s.currentOrder)
      return idx >= 0 ? idx : 0
    },
    currentItem: (s) => (s.flat.length ? s.flat[Math.max(0, s.flat.findIndex((x) => x.question?.order === s.currentOrder))] : null),
  },

  actions: {
    // Quiz from practice session response (avoids extra GET /quizzes).
    hydrateQuiz(quizData, { resetAnswers = true } = {}) {
      if (!quizData) return false
      this.quiz = quizData
      this.flat = flattenQuizQuestions(this.quiz)
      if (resetAnswers) {
        this.answers = {}
        this.currentOrder = this.flat[0]?.question?.order ?? null
        this.result = null
      }
      this.startTimer((this.quiz?.time ?? 0) * 60)
      return true
    },

    async loadQuiz(quizId, { force = false } = {}) {
      const id = Number(quizId)
      if (!force && this.quiz && Number(this.quiz.id) === id) {
        return
      }
      this.loading = true
      try {
        this.quiz = await getQuiz(quizId)
        this.flat = flattenQuizQuestions(this.quiz)
        this.answers = {}
        this.currentOrder = this.flat[0]?.question?.order ?? null
        this.result = null
        this.startTimer((this.quiz?.time ?? 0) * 60)
      } finally {
        this.loading = false
      }
    },

    setAnswer(questionId, value) {
      if (!questionId) return
      if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
        const { [questionId]: _, ...rest } = this.answers
        this.answers = rest
        return
      }
      this.answers = { ...this.answers, [questionId]: value }
    },

    gotoOrder(order) {
      this.currentOrder = order
    },

    startTimer(seconds) {
      this.stopTimer()
      this.remainingSeconds = Math.max(0, Number(seconds) || 0)
      this._timer = setInterval(() => {
        if (this.remainingSeconds <= 0) {
          this.remainingSeconds = 0
          this.stopTimer()
          return
        }
        this.remainingSeconds -= 1
      }, 1000)
    },

    stopTimer() {
      if (this._timer) clearInterval(this._timer)
      this._timer = null
    },

    submit() {
      // Compute in view; we keep only navigation state here.
      this.stopTimer()
      return true
    },

    reset() {
      this.stopTimer()
      this.loading = false
      this.quiz = null
      this.flat = []
      this.answers = {}
      this.currentOrder = null
      this.remainingSeconds = 0
      this.result = null
    },
  },
})

