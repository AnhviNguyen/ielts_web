<template>
  <div class="flex min-h-screen flex-col bg-white">
    <header class="flex h-12 items-center justify-between border-b border-[var(--border)] px-5">
      <span class="text-[13px] font-semibold">Writing — Full Mock Exam</span>
      <span class="font-mono text-[12px] font-medium">{{ fmtTimer }}</span>
    </header>

    <div class="flex-1 overflow-y-auto p-5">
      <div class="mx-auto max-w-3xl">
        <div class="mb-4 flex gap-2">
          <button
            type="button"
            class="rounded-full px-3 py-1 text-[12px] font-medium"
            :class="taskStep === 1 ? 'bg-[#34d399] text-white' : 'border border-[var(--border)]'"
            @click="taskStep = 1"
          >
            Task 1 ({{ timers.writing_task1_minutes }} phút)
          </button>
          <button
            type="button"
            class="rounded-full px-3 py-1 text-[12px] font-medium"
            :class="taskStep === 2 ? 'bg-[#34d399] text-white' : 'border border-[var(--border)]'"
            :disabled="taskStep < 2 && !task1Done"
            @click="goTask2"
          >
            Task 2 ({{ timers.writing_task2_minutes }} phút)
          </button>
        </div>

        <p v-if="taskStep === 1" class="mb-2 text-[12px] text-[var(--ink3)]">
          Viết ít nhất 150 từ. Khi xong Task 1, chuyển sang Task 2.
        </p>
        <p v-else class="mb-2 text-[12px] text-[var(--ink3)]">
          Viết ít nhất 250 từ. Nộp cả hai bài để chấm AI.
        </p>

        <textarea
          v-model="currentText"
          class="ct-input min-h-[320px] w-full resize-y font-serif text-[15px] leading-relaxed"
          :placeholder="taskStep === 1 ? 'Task 1 essay...' : 'Task 2 essay...'"
        />
        <div class="mt-2 text-[12px] text-[var(--ink3)]">{{ wordCount }} từ</div>
        <div v-if="submitError" class="mt-3 text-[13px] text-[var(--rose)]">{{ submitError }}</div>
      </div>
    </div>

    <footer class="profile-page flex justify-end gap-2 border-t border-[var(--border)] p-4">
      <button v-if="taskStep === 1" type="button" class="ct-btn" @click="goTask2">Tiếp Task 2 →</button>
      <button
        v-else
        type="button"
        class="btn btn-primary"
        :disabled="submitting"
        @click="submitBoth"
      >
        {{ submitting ? 'Đang chấm...' : 'Nộp Writing & tiếp Speaking' }}
      </button>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { submitWriting } from '@/services/writingService.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'
import { useFullExamStore } from '@/stores/fullExam.js'
import { breakRoute } from '@/utils/fullExamNav.js'

const route = useRoute()
const router = useRouter()
const fullExam = useFullExamStore()

const session = computed(() => fullExam.getSession())
const timers = computed(() => session.value?.set?.timers || {})

const taskStep = ref(1)
const task1Text = ref('')
const task2Text = ref('')
const task1Done = ref(false)
const submitting = ref(false)
const submitError = ref('')

const totalSecs = computed(() => {
  const t = timers.value
  return ((t.writing_task1_minutes || 20) + (t.writing_task2_minutes || 40)) * 60
})
const remaining = ref(0)
let timerId = null

const currentText = computed({
  get: () => (taskStep.value === 1 ? task1Text.value : task2Text.value),
  set: (v) => {
    if (taskStep.value === 1) task1Text.value = v
    else task2Text.value = v
  },
})

const wordCount = computed(() =>
  currentText.value.trim().split(/\s+/).filter(Boolean).length,
)

const fmtTimer = computed(() => {
  const s = remaining.value
  const m = String(Math.floor(s / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${m}:${ss}`
})

function goTask2() {
  if (task1Text.value.trim().split(/\s+/).filter(Boolean).length < 20) {
    submitError.value = 'Task 1 cần ít nhất ~20 từ trước khi sang Task 2.'
    return
  }
  task1Done.value = true
  taskStep.value = 2
  submitError.value = ''
}

async function submitBoth() {
  if (!session.value) {
    router.push('/full-exam')
    return
  }
  const set = session.value.set
  const elapsed = Math.max(0, totalSecs.value - remaining.value)
  const half = Math.floor(elapsed / 2)
  submitting.value = true
  submitError.value = ''
  try {
    const r1 = await submitWriting({
      topic_id: set.writing_task1_topic_id,
      task_type: 1,
      essay_text: task1Text.value,
      word_count: task1Text.value.trim().split(/\s+/).filter(Boolean).length,
      duration_seconds: half,
    })
    const r2 = await submitWriting({
      topic_id: set.writing_task2_topic_id,
      task_type: 2,
      essay_text: task2Text.value,
      word_count: task2Text.value.trim().split(/\s+/).filter(Boolean).length,
      duration_seconds: elapsed - half,
    })
    const celebration = useBadgeCelebrationStore()
    celebration.enqueue(r1?.new_badges)
    celebration.enqueue(r2?.new_badges)
    fullExam.recordStageResult('writing', { task1: r1, task2: r2, band: r2.band_score })
    router.push(breakRoute(session.value, 'writing'))
  } catch (e) {
    submitError.value = e.response?.data?.detail || 'Nộp bài Writing thất bại'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (!session.value || route.query.session !== session.value.sessionId) {
    router.replace('/full-exam')
    return
  }
  remaining.value = totalSecs.value
  timerId = setInterval(() => {
    if (remaining.value > 0) remaining.value--
  }, 1000)
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>
