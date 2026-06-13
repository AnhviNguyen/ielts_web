<template>
  <div class="flex min-h-screen flex-col bg-[var(--bg-base)]">
    <header class="flex h-12 shrink-0 items-center justify-between border-b border-[var(--border)] px-5">
      <span class="text-[13px] font-semibold text-[var(--ink)]">Writing — Full Mock Exam</span>
      <span class="font-mono text-[12px] font-medium text-[var(--ink)]">{{ fmtTimer }}</span>
    </header>

    <div class="flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
      <!-- Prompt panel -->
      <aside class="flex w-full shrink-0 flex-col border-b border-[var(--border)] lg:w-[42%] lg:border-b-0 lg:border-r">
        <div class="shrink-0 border-b border-[var(--border)] px-5 py-3">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">
            Đề bài — Task {{ taskStep }}
          </div>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <div v-if="promptLoading" class="text-[13px] text-[var(--ink3)]">Đang tải đề Writing...</div>
          <div v-else-if="promptError" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">
            {{ promptError }}
          </div>
          <template v-else-if="currentDetail">
            <div class="writing-prompt-html text-left text-[var(--ink)]" v-html="currentPromptHtml" />

            <section v-if="showPromptImage" class="mt-4">
              <p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">
                {{ promptImageLabel }}
              </p>
              <div
                v-if="promptImageSrc && !promptImageFailed"
                class="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg)]"
              >
                <img
                  :src="promptImageSrc"
                  :alt="promptImageAlt"
                  class="max-h-[min(420px,50vh)] w-full object-contain"
                  @error="promptImageFailed = true"
                />
              </div>
            </section>

            <details v-if="currentInstructionHtml" class="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg)]">
              <summary class="cursor-pointer px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-[var(--spotify-green)]">
                Hướng dẫn viết bài
              </summary>
              <div class="px-4 pb-4 pt-2 text-left text-[12px] leading-relaxed text-[var(--ink)]" v-html="currentInstructionHtml" />
            </details>
          </template>
        </div>
      </aside>

      <!-- Answer panel -->
      <main class="flex min-h-0 flex-1 flex-col">
        <div class="shrink-0 border-b border-[var(--border)] px-5 py-3">
          <div class="mb-3 flex gap-2">
            <button
              type="button"
              class="rounded-full px-3 py-1 text-[12px] font-medium transition-colors"
              :class="taskStep === 1 ? 'bg-[var(--spotify-green)] text-black' : 'border border-[var(--border)] text-[var(--ink2)]'"
              @click="taskStep = 1"
            >
              Task 1 ({{ timers.writing_task1_minutes }} phút)
            </button>
            <button
              type="button"
              class="rounded-full px-3 py-1 text-[12px] font-medium transition-colors"
              :class="taskStep === 2 ? 'bg-[var(--spotify-green)] text-black' : 'border border-[var(--border)] text-[var(--ink2)]'"
              :disabled="taskStep < 2 && !task1Done"
              @click="goTask2"
            >
              Task 2 ({{ timers.writing_task2_minutes }} phút)
            </button>
          </div>
          <p class="text-[12px] text-[var(--ink3)]">
            {{ taskStep === 1
              ? 'Viết ít nhất 150 từ. Khi xong Task 1, chuyển sang Task 2.'
              : 'Viết ít nhất 250 từ. Nộp cả hai bài để chấm AI.' }}
          </p>
        </div>

        <div class="flex min-h-0 flex-1 flex-col p-4">
          <textarea
            ref="essayRef"
            v-model="currentText"
            class="fe-writing-editor min-h-[280px] w-full flex-1 resize-none rounded-lg border border-[var(--border)] bg-[var(--bg-interactive)] p-4 text-left font-serif text-[15px] leading-relaxed text-[var(--ink)] outline-none placeholder-[var(--ink3)] transition-colors focus:border-[var(--spotify-green)]"
            :placeholder="taskStep === 1 ? 'Viết bài Task 1 tại đây...' : 'Viết bài Task 2 tại đây...'"
            @input="growEssay"
          />
          <div class="mt-2 text-left text-[12px] text-[var(--ink3)]">{{ wordCount }} từ</div>
          <div v-if="submitError" class="mt-3 text-left text-[13px] text-[var(--rose)]">{{ submitError }}</div>
        </div>
      </main>
    </div>

    <footer class="flex shrink-0 justify-end gap-2 border-t border-[var(--border)] bg-[var(--bg-surface)] p-4">
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
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchWritingTopic, submitWriting } from '@/services/writingService.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'
import { useFullExamStore } from '@/stores/fullExam.js'
import { breakRoute } from '@/utils/fullExamNav.js'
import { imageUrl } from '@/utils/mediaUrl.js'
import { sanitizeHtml } from '@/utils/sanitizeHtml.js'
import { growTextarea } from '@/utils/adminTextareaAutoGrow.js'

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
const promptLoading = ref(true)
const promptError = ref('')
const task1Detail = ref(null)
const task2Detail = ref(null)
const promptImageFailed = ref(false)
const essayRef = ref(null)

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

const currentDetail = computed(() => (taskStep.value === 1 ? task1Detail.value : task2Detail.value))

const currentQuestion = computed(() => (currentDetail.value?.questions || [])[0] || null)

const currentPromptHtml = computed(() =>
  sanitizeHtml(
    currentQuestion.value?.content_writing
      || currentQuestion.value?.title
      || currentDetail.value?.prompt_html
      || currentDetail.value?.prompt_text
      || '',
  ),
)

const currentInstructionHtml = computed(() =>
  sanitizeHtml(currentQuestion.value?.instruction || ''),
)

const isTask1 = computed(() => taskStep.value === 1)

const promptImageId = computed(() => {
  if (isTask1.value) return currentQuestion.value?.writing_graph_image || null
  return currentDetail.value?.thumbnail || null
})

const showPromptImage = computed(() =>
  isTask1.value ? !!promptImageId.value : !!(currentDetail.value?.thumbnail || currentDetail.value?.thumbnail_url),
)

const promptImageLabel = computed(() =>
  isTask1.value ? 'Biểu đồ / hình minh họa' : 'Hình minh họa đề bài',
)

const promptImageAlt = computed(() =>
  isTask1.value ? 'IELTS Writing Task 1 chart' : 'IELTS Writing Task 2',
)

const promptImageSrc = computed(() => {
  if (isTask1.value) {
    const fromApi = currentQuestion.value?.chart_image_url
    if (fromApi) return imageUrl(fromApi)
    return imageUrl(currentQuestion.value?.writing_graph_image)
  }
  const thumbUrl = currentDetail.value?.thumbnail_url
  if (thumbUrl) return imageUrl(thumbUrl)
  return imageUrl(currentDetail.value?.thumbnail)
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

function growEssay() {
  if (essayRef.value) growTextarea(essayRef.value)
}

function promptTextFromDetail(detail) {
  const q = (detail?.questions || [])[0] || {}
  return q.content_writing || q.title || detail?.prompt_text || ''
}

function goTask2() {
  if (task1Text.value.trim().split(/\s+/).filter(Boolean).length < 20) {
    submitError.value = 'Task 1 cần ít nhất ~20 từ trước khi sang Task 2.'
    return
  }
  task1Done.value = true
  taskStep.value = 2
  submitError.value = ''
  promptImageFailed.value = false
  nextTick(growEssay)
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
      prompt_text: promptTextFromDetail(task1Detail.value),
    })
    const r2 = await submitWriting({
      topic_id: set.writing_task2_topic_id,
      task_type: 2,
      essay_text: task2Text.value,
      word_count: task2Text.value.trim().split(/\s+/).filter(Boolean).length,
      duration_seconds: elapsed - half,
      prompt_text: promptTextFromDetail(task2Detail.value),
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

async function loadPrompts(set) {
  promptLoading.value = true
  promptError.value = ''
  try {
    const ids = [set.writing_task1_topic_id, set.writing_task2_topic_id].filter(Boolean)
    if (!ids.length) {
      promptError.value = 'Bộ đề chưa gắn topic Writing Task 1/2.'
      return
    }
    const [d1, d2] = await Promise.all([
      set.writing_task1_topic_id ? fetchWritingTopic(set.writing_task1_topic_id) : null,
      set.writing_task2_topic_id ? fetchWritingTopic(set.writing_task2_topic_id) : null,
    ])
    task1Detail.value = d1
    task2Detail.value = d2
    if (!d1 && !d2) {
      promptError.value = 'Không tải được đề Writing. Thử tải lại trang.'
    }
  } catch (e) {
    promptError.value = e.response?.data?.detail || e.message || 'Không tải được đề Writing.'
  } finally {
    promptLoading.value = false
    nextTick(growEssay)
  }
}

watch(taskStep, () => {
  promptImageFailed.value = false
  nextTick(growEssay)
})

onMounted(async () => {
  if (!session.value || route.query.session !== session.value.sessionId) {
    router.replace('/full-exam')
    return
  }
  await loadPrompts(session.value.set)
  remaining.value = totalSecs.value
  timerId = setInterval(() => {
    if (remaining.value > 0) remaining.value--
  }, 1000)
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>
