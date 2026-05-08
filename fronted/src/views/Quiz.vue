<!-- src/views/Quiz.vue -->
<template>
  <div class="page-wrapper">
    <div class="container" style="max-width:760px">

      <!-- Not found -->
      <div v-if="!validSubject" class="card text-center" style="padding:3rem">
        <h2>Subject not found</h2>
        <RouterLink to="/dashboard" class="btn btn-primary mt-md">Back to Dashboard</RouterLink>
      </div>

      <template v-else>
        <!-- Header -->
        <div class="quiz-header">
          <RouterLink to="/dashboard" class="back-link">← Dashboard</RouterLink>
          <div class="quiz-subject">
            <span class="subject-emoji">{{ subjectEmoji }}</span>
            <h1>{{ subject }}</h1>
          </div>
          <p class="text-muted">Answer all {{ quizStore.totalQuestions }} questions</p>
        </div>

        <!-- Top progress bar -->
        <div class="quiz-progress-top">
          <ProgressBar
            :value="quizStore.progressPercent"
            color="primary" height="6px"
            :show-percent="false"
          />
          <span class="progress-text text-muted">
            {{ quizStore.answeredCount }} / {{ quizStore.totalQuestions }} answered
          </span>
        </div>

        <!-- Question card -->
        <Transition name="slide" mode="out-in">
          <div :key="quizStore.currentIndex" class="card question-card">
            <div class="question-num">
              Question {{ quizStore.currentIndex + 1 }} of {{ quizStore.totalQuestions }}
            </div>
            <h2 class="question-text">{{ quizStore.currentQuestion?.question }}</h2>

            <div class="options-list">
              <button
                v-for="(opt, idx) in quizStore.currentQuestion?.options"
                :key="idx"
                class="option-btn"
                :class="{
                  selected: quizStore.userAnswers[quizStore.currentQuestion?.id] === idx,
                }"
                @click="quizStore.selectAnswer(quizStore.currentQuestion?.id, idx)"
                :id="`option-${idx}`"
              >
                <span class="option-letter">{{ letters[idx] }}</span>
                <span class="option-text">{{ opt }}</span>
                <span
                  v-if="quizStore.userAnswers[quizStore.currentQuestion?.id] === idx"
                  class="option-check"
                >✓</span>
              </button>
            </div>
          </div>
        </Transition>

        <!-- Navigation -->
        <div class="quiz-nav">
          <button class="btn btn-secondary" :disabled="quizStore.currentIndex === 0"
            @click="quizStore.prevQuestion()" id="prev-question-btn">← Previous</button>

          <div class="dot-indicators">
            <button
              v-for="(_, i) in quizStore.questions"
              :key="i"
              class="dot"
              :class="{
                active:    i === quizStore.currentIndex,
                answered:  quizStore.userAnswers[quizStore.questions[i]?.id] !== undefined,
              }"
              @click="quizStore.currentIndex = i"
            />
          </div>

          <button v-if="!quizStore.isLastQuestion" class="btn btn-primary"
            @click="quizStore.nextQuestion()" id="next-question-btn">Next →</button>
          <button v-else class="btn btn-primary" id="submit-quiz-btn"
            :disabled="quizStore.answeredCount < quizStore.totalQuestions || quizStore.loading"
            @click="handleSubmit">
            <span v-if="quizStore.loading" class="spinner"></span>
            <span v-else>Submit Quiz 🚀</span>
          </button>
        </div>

        <!-- Submit warning -->
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

<style scoped>
.quiz-header { margin-bottom: 1.5rem; }
.back-link { font-size: 0.9rem; color: var(--color-text-muted); text-decoration: none; display:inline-block; margin-bottom: 1rem; }
.back-link:hover { color: var(--color-primary); }
.quiz-subject { display:flex; align-items:center; gap:0.75rem; margin-bottom: 0.5rem; }
.subject-emoji { font-size: 2rem; }
.quiz-subject h1 { margin: 0; }

.quiz-progress-top { margin-bottom: 1.5rem; }
.progress-text { font-size: 0.82rem; display:block; margin-top: 6px; text-align:right; }

.question-card { padding: 2rem; }
.question-num { font-size: 0.8rem; font-weight: 600; color: var(--color-primary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom: 1rem; }
.question-text { font-size: 1.2rem; font-weight: 700; line-height: 1.5; margin-bottom: 1.75rem; }

.options-list { display:flex; flex-direction:column; gap: 0.75rem; }
.option-btn {
  display: flex; align-items: center; gap: 1rem;
  padding: 1rem 1.25rem; width: 100%;
  background: var(--color-surface-2); border: 2px solid var(--color-border);
  border-radius: var(--radius-md); cursor: pointer;
  text-align: left; color: var(--color-text);
  font-family: inherit; font-size: 0.95rem;
  transition: all var(--transition-fast);
}
.option-btn:hover { border-color: var(--color-primary); background: rgba(124,106,247,0.08); }
.option-btn.selected { border-color: var(--color-primary); background: rgba(124,106,247,0.15); }
.option-letter {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--color-surface); border: 2px solid var(--color-border);
  display:flex; align-items:center; justify-content:center;
  font-weight: 700; font-size: 0.85rem; flex-shrink: 0;
  transition: all var(--transition-fast);
}
.option-btn.selected .option-letter { background: var(--color-primary); border-color: var(--color-primary); color: #fff; }
.option-text { flex: 1; }
.option-check { color: var(--color-primary); font-weight: 700; }

.quiz-nav { display:flex; align-items:center; justify-content:space-between; gap: 1rem; margin-top: 1.5rem; }
.dot-indicators { display:flex; gap: 6px; }
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--color-surface-2); border: 2px solid var(--color-border);
  cursor: pointer; transition: all 0.2s; padding: 0;
}
.dot.answered { background: rgba(124,106,247,0.4); border-color: var(--color-primary); }
.dot.active   { background: var(--color-primary); border-color: var(--color-primary); transform: scale(1.3); }

/* Slide transition */
.slide-enter-active, .slide-leave-active { transition: all 0.25s ease; }
.slide-enter-from { opacity:0; transform: translateX(30px); }
.slide-leave-to   { opacity:0; transform: translateX(-30px); }
</style>
