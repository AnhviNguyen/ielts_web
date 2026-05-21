<!-- src/views/Quiz.vue -->
<template>
  <div class="page-wrapper">
    <div class="container" style="max-width:760px">

      <div v-if="!validSubject" class="card text-center" style="padding:3rem">
        <h2>Subject not found</h2>
        <RouterLink to="/dashboard" class="btn btn-primary mt-md">Back to Dashboard</RouterLink>
      </div>

      <template v-else>
        <div class="quiz-header">
          <RouterLink to="/dashboard" class="quiz-back-link">← Dashboard</RouterLink>
          <div class="quiz-subject">
            <span class="text-3xl">{{ subjectEmoji }}</span>
            <h1>{{ subject }}</h1>
          </div>
          <p class="text-muted">Answer all {{ quizStore.totalQuestions }} questions</p>
        </div>

        <div class="quiz-progress-top">
          <ProgressBar
            :value="quizStore.progressPercent"
            color="primary" height="6px"
            :show-percent="false"
          />
          <span class="quiz-progress-text text-muted">
            {{ quizStore.answeredCount }} / {{ quizStore.totalQuestions }} answered
          </span>
        </div>

        <Transition name="slide" mode="out-in">
          <div :key="quizStore.currentIndex" class="card quiz-question-card">
            <div class="quiz-question-num">
              Question {{ quizStore.currentIndex + 1 }} of {{ quizStore.totalQuestions }}
            </div>
            <h2 class="quiz-question-text">{{ quizStore.currentQuestion?.question }}</h2>

            <div class="quiz-options-list">
              <button
                v-for="(opt, idx) in quizStore.currentQuestion?.options"
                :key="idx"
                type="button"
                class="quiz-option-btn"
                :class="{ selected: quizStore.userAnswers[quizStore.currentQuestion?.id] === idx }"
                @click="quizStore.selectAnswer(quizStore.currentQuestion?.id, idx)"
                :id="`option-${idx}`"
              >
                <span class="quiz-option-letter">{{ letters[idx] }}</span>
                <span class="flex-1">{{ opt }}</span>
                <span v-if="quizStore.userAnswers[quizStore.currentQuestion?.id] === idx" class="font-bold text-[var(--color-primary)]">✓</span>
              </button>
            </div>
          </div>
        </Transition>

        <div class="quiz-nav">
          <button type="button" class="btn btn-secondary" :disabled="quizStore.currentIndex === 0"
            @click="quizStore.prevQuestion()" id="prev-question-btn">← Previous</button>

          <div class="quiz-dot-indicators">
            <button
              v-for="(_, i) in quizStore.questions"
              :key="i"
              type="button"
              class="quiz-dot"
              :class="{
                active:    i === quizStore.currentIndex,
                answered:  quizStore.userAnswers[quizStore.questions[i]?.id] !== undefined,
              }"
              @click="quizStore.currentIndex = i"
            />
          </div>

          <button v-if="!quizStore.isLastQuestion" type="button" class="btn btn-primary"
            @click="quizStore.nextQuestion()" id="next-question-btn">Next →</button>
          <button v-else type="button" class="btn btn-primary" id="submit-quiz-btn"
            :disabled="quizStore.answeredCount < quizStore.totalQuestions || quizStore.loading"
            @click="handleSubmit">
            <span v-if="quizStore.loading" class="spinner"></span>
            <span v-else>Submit Quiz 🚀</span>
          </button>
        </div>

        <Transition name="fade">
          <div v-if="showWarning" class="alert alert-error mt-md">
            Please answer all {{ quizStore.totalQuestions }} questions before submitting.
          </div>
        </Transition>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuizStore, SUBJECTS } from '@/stores/quiz.js'
import ProgressBar from '@/components/ProgressBar.vue'

const route      = useRoute()
const router     = useRouter()
const quizStore  = useQuizStore()
const subject    = computed(() => decodeURIComponent(route.params.subject))
const validSubject = computed(() => SUBJECTS.includes(subject.value))
const showWarning  = ref(false)
const letters = ['A','B','C','D']

const subjectEmoji = computed(() => {
  const m = { Mathematics:'🔢', Physics:'⚛️', Chemistry:'⚗️', Biology:'🧬', 'Computer Science':'💻' }
  return m[subject.value] || '📖'
})

async function handleSubmit() {
  if (quizStore.answeredCount < quizStore.totalQuestions) {
    showWarning.value = true
    setTimeout(() => { showWarning.value = false }, 3000)
    return
  }
  const result = await quizStore.submitQuiz()
  if (result) router.push('/result')
}

onMounted(() => {
  if (validSubject.value) quizStore.startQuiz(subject.value)
})
</script>
