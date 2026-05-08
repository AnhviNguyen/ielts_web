/**
 * src/stores/quiz.js
 * Pinia store for quiz state: questions, answers, scoring, submission.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client.js'

export const SUBJECTS = ['Mathematics','Physics','Chemistry','Biology','Computer Science']

const QUESTION_BANK = {
  Mathematics: [
    { id:1, question:'What is the derivative of x²?', options:['x','2x','2','x²'], answer:1 },
    { id:2, question:'Solve: 3x + 6 = 21', options:['x=3','x=4','x=5','x=7'], answer:2 },
    { id:3, question:'What is π to 2 decimal places?', options:['3.12','3.14','3.16','3.18'], answer:1 },
    { id:4, question:'Integral of cos(x)?', options:['-sin(x)+C','sin(x)+C','cos(x)+C','tan(x)+C'], answer:1 },
    { id:5, question:'Sum of angles in a triangle?', options:['90°','180°','270°','360°'], answer:1 },
  ],
  Physics: [
    { id:1, question:"Newton's 2nd law: F = ?", options:['mv','ma','mv²','m/a'], answer:1 },
    { id:2, question:'Speed of light in vacuum?', options:['3×10⁶ m/s','3×10⁸ m/s','3×10¹⁰ m/s','3×10⁴ m/s'], answer:1 },
    { id:3, question:'Conservation of energy is which law?', options:['1st Law of Thermodynamics','2nd Law','Newton 3rd','Ohm\'s Law'], answer:0 },
    { id:4, question:'SI unit of electric current?', options:['Volt','Watt','Ampere','Ohm'], answer:2 },
    { id:5, question:'Gravitational acceleration on Earth?', options:['8.9 m/s²','9.8 m/s²','10.8 m/s²','11 m/s²'], answer:1 },
  ],
  Chemistry: [
    { id:1, question:'Atomic number of Carbon?', options:['4','6','8','12'], answer:1 },
    { id:2, question:'Water is composed of?', options:['H₂O₂','HO','H₂O','H₃O'], answer:2 },
    { id:3, question:'Symbol "Au" is for?', options:['Silver','Aluminum','Gold','Argon'], answer:2 },
    { id:4, question:'pH of pure water?', options:['5','6','7','8'], answer:2 },
    { id:5, question:'Periodic table developed by?', options:['Newton','Mendeleev','Einstein','Bohr'], answer:1 },
  ],
  Biology: [
    { id:1, question:'Powerhouse of the cell?', options:['Nucleus','Ribosome','Mitochondria','Lysosome'], answer:2 },
    { id:2, question:'DNA stands for?', options:['Deoxyribonucleic Acid','Diribonucleic Acid','Deoxyribose Nucleic Acid','Dioxynucleic Acid'], answer:0 },
    { id:3, question:'Chromosomes in human cell?', options:['23','44','46','48'], answer:2 },
    { id:4, question:'Plants make food via?', options:['Respiration','Photosynthesis','Digestion','Fermentation'], answer:1 },
    { id:5, question:'Universal blood donor type?', options:['A','B','AB','O'], answer:3 },
  ],
  'Computer Science': [
    { id:1, question:'CPU stands for?', options:['Central Processing Unit','Computer Processing Unit','Central Program Unit','Control Processing Unit'], answer:0 },
    { id:2, question:'FIFO data structure?', options:['Stack','Queue','Tree','Graph'], answer:1 },
    { id:3, question:'Binary search complexity?', options:['O(n)','O(n²)','O(log n)','O(1)'], answer:2 },
    { id:4, question:'"Mother of all languages"?', options:['Python','Java','C','Assembly'], answer:2 },
    { id:5, question:'HTTP stands for?', options:['HyperText Transfer Protocol','High Transfer Text Protocol','HyperText Transmission Protocol','Hybrid Text Transfer Protocol'], answer:0 },
  ],
}

export const useQuizStore = defineStore('quiz', () => {
  const currentSubject = ref(null)
  const questions      = ref([])
  const userAnswers    = ref({})
  const currentIndex   = ref(0)
  const result         = ref(null)
  const loading        = ref(false)
  const error          = ref(null)

  const currentQuestion = computed(() => questions.value[currentIndex.value])
  const totalQuestions  = computed(() => questions.value.length)
  const isLastQuestion  = computed(() => currentIndex.value === totalQuestions.value - 1)
  const answeredCount   = computed(() => Object.keys(userAnswers.value).length)
  const progressPercent = computed(() =>
    totalQuestions.value ? Math.round((answeredCount.value / totalQuestions.value) * 100) : 0
  )

  function startQuiz(subject) {
    currentSubject.value = subject
    questions.value      = QUESTION_BANK[subject] || []
    userAnswers.value    = {}
    currentIndex.value   = 0
    result.value         = null
    error.value          = null
  }

  function selectAnswer(questionId, optionIndex) {
    userAnswers.value[questionId] = optionIndex
  }

  function nextQuestion() { if (!isLastQuestion.value) currentIndex.value++ }
  function prevQuestion() { if (currentIndex.value > 0) currentIndex.value-- }

  async function submitQuiz() {
    loading.value = true
    error.value   = null
    let score = 0
    const detailedAnswers = questions.value.map((q) => {
      const selected = userAnswers.value[q.id] ?? -1
      const isCorrect = q.answer === selected
      if (isCorrect) score++
      return { questionId: q.id, question: q.question, selected, correct: q.answer, isCorrect }
    })
    const total      = questions.value.length
    const percentage = Math.round((score / total) * 100)
    try {
      const { data } = await apiClient.post('/history/save', {
        quiz_id: `${currentSubject.value}-${Date.now()}`,
        subject: currentSubject.value,
        score, total_questions: total, percentage, answers: detailedAnswers,
      })
      result.value = { ...data, score, total, percentage, detailedAnswers, subject: currentSubject.value }
      return result.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to submit quiz'
      return null
    } finally {
      loading.value = false
    }
  }

  function clearResult() { result.value = null }

  return {
    currentSubject, questions, userAnswers, currentIndex, result, loading, error,
    currentQuestion, totalQuestions, isLastQuestion, answeredCount, progressPercent,
    startQuiz, selectAnswer, nextQuestion, prevQuestion, submitQuiz, clearResult,
  }
})
