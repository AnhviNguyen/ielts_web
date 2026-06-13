<template>
  <div class="flex h-screen flex-col overflow-hidden bg-[var(--bg-base)]">

    <!-- ─── Top bar (Cathoven style) ─── -->
    <header class="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-[var(--border)] px-3 sm:px-5">
      <div class="flex min-w-0 items-center gap-2 sm:gap-3">
        <button @click="confirmBack" class="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)]">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <span class="hidden h-4 w-px bg-[var(--border)] sm:block"></span>
        <span class="hidden text-[12px] text-[var(--ink3)] sm:inline">Back</span>
        <span class="hidden text-[var(--border)] sm:inline">|</span>
        <span v-if="writingSet" class="flex shrink-0 items-center gap-2">
          <button
            type="button"
            class="rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors"
            :class="taskStep === 1 ? 'bg-[#34d399] text-white' : 'border border-[var(--border)] text-[var(--ink3)] hover:border-[#34d399]'"
            @click="switchToTask(1)"
          >Task 1</button>
          <button
            type="button"
            class="rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors"
            :class="taskStep === 2 ? 'bg-[#34d399] text-white' : 'border border-[var(--border)] text-[var(--ink3)] hover:border-[#34d399]'"
            @click="switchToTask(2)"
          >Task 2</button>
        </span>
        <span class="truncate text-[13px] font-semibold text-[var(--ink)]">
          {{ writingSet ? (writingSet.title || 'Bộ đề Writing') : `Task ${effectiveTaskType}` }}: {{ taskLabel }}
        </span>
      </div>

      <div class="flex shrink-0 items-center gap-2 sm:gap-3">
        <div class="flex items-center gap-1.5 rounded border border-[var(--border)] px-2.5 py-1 text-[12px] font-mono font-medium text-[var(--ink)]">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          {{ fmtTimer }}
        </div>

        <button
          @click="helpOpen = !helpOpen"
          class="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1.5 text-[11px] font-semibold text-emerald-800 transition-colors hover:bg-emerald-600 hover:text-white sm:px-3"
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>
          <span class="hidden sm:inline">Need help with writing? Click here.</span>
          <span class="sm:hidden">Help</span>
        </button>
      </div>
    </header>

    <!-- ─── Main 3-panel area ─── -->
    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">

      <!-- Left: Prompt panel -->
      <div class="flex w-full shrink-0 flex-col overflow-hidden border-b border-[var(--border)] max-lg:max-h-[42vh] lg:w-[42%] lg:border-b-0 lg:border-r lg:max-h-none">
        <div class="shrink-0 border-b border-[var(--border)] px-5 py-3">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Writing Task</div>
        </div>
        <div class="flex-1 overflow-y-auto px-5 py-4">
          <template v-if="detail">
            <div
              class="writing-prompt-html"
              v-html="promptHtml"
            />

            <!-- Task 1: chart (writing_graph_image) · Task 2: thumbnail — backend/data/assets/images -->
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
              <div
                v-else-if="isTask1"
                class="rounded-lg border border-dashed border-amber-300 bg-amber-50 px-4 py-6 text-center text-[12px] text-amber-800"
              >
                <p class="font-semibold">Không tải được hình biểu đồ.</p>
                <p v-if="promptImageId" class="mt-1 text-[11px] opacity-80">
                  Không tìm thấy ảnh <code class="rounded bg-white px-1">{{ promptImageId }}</code> trên Cloudinary.
                  Chạy <code class="rounded bg-white px-1">python upload_assets.py</code> nếu chưa upload.
                </p>
                <p v-else class="mt-1 text-[11px]">Đề này không có <code>writing_graph_image</code> trong dữ liệu.</p>
              </div>
            </section>

            <details v-if="detailQuestion?.instruction" class="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg)]">
              <summary class="cursor-pointer px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-[#34d399]">
                Hướng dẫn viết bài
              </summary>
              <div class="px-4 pb-4 pt-2 text-[12px] leading-relaxed text-[var(--ink)]" v-html="instructionHtml" />
            </details>
          </template>
          <div v-else class="text-[13px] leading-relaxed text-[var(--ink)]" v-html="fallbackPromptHtml" />

          <label
            v-if="isTask1"
            class="mt-4 flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-[var(--border2)] bg-[var(--bg)] px-4 py-3 text-[12px] text-[var(--ink2)] hover:border-[#34d399] hover:bg-[#f0fdf4] transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            Tải hình thay thế (tùy chọn)
            <input type="file" accept="image/*" class="hidden" @change="onImageUpload" />
          </label>
        </div>
      </div>

      <!-- Center: Answer editor -->
      <div class="flex min-h-0 flex-1 flex-col overflow-hidden" :class="helpOpen ? 'lg:border-r lg:border-[var(--border)]' : ''">
        <div class="shrink-0 border-b border-[var(--border)] px-5 py-3">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Your Answer</div>
        </div>
        <div class="flex flex-1 overflow-hidden p-4">
          <textarea
            v-model="writingText"
            class="h-full w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--bg-interactive)] p-3 text-[13px] leading-relaxed text-[var(--ink)] outline-none placeholder-[var(--ink3)] focus:border-[var(--spotify-green)] transition-colors"
            placeholder="Write your answer here..."
          />
        </div>
        <div class="flex shrink-0 flex-col border-t border-[var(--border)] px-5 py-2.5">
          <p v-if="task1GradedMsg" class="mb-2 text-[12px] text-[var(--spotify-green-dark)]">{{ task1GradedMsg }}</p>
          <p v-if="submitError" class="mb-2 text-[12px] text-[var(--rose)]">{{ submitError }}</p>
          <div class="flex items-center justify-between">
          <span class="text-[12px] text-[var(--ink3)]">Words: <strong class="text-[var(--ink)]">{{ wordCount }}</strong></span>
          <div class="flex items-center gap-2">
            <label class="ct-btn cursor-pointer text-[12px]">
              <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              Upload File
              <input type="file" accept=".txt,.doc,.docx" class="hidden" @change="onFileUpload" />
            </label>
            <button
              class="ct-btn text-[12px] font-semibold"
              :class="canSubmit ? 'bg-[var(--spotify-green)] text-black border-transparent hover:brightness-105' : 'opacity-50'"
              :disabled="submitting || !canSubmit"
              @click="submitWriting"
            >{{ submitButtonLabel }}</button>
          </div>
          </div>
        </div>
      </div>

      <!-- Right: Help chat panel -->
      <Transition name="slide">
        <div
          v-if="helpOpen"
          class="flex w-full shrink-0 flex-col overflow-hidden border-t border-[var(--border)] bg-[var(--bg-surface)] max-lg:absolute max-lg:inset-0 max-lg:z-40 max-lg:border-t-0 lg:relative lg:w-80 lg:border-t-0"
        >
          <div class="catbot-header flex items-center justify-between border-b px-4 py-3">
            <div class="flex items-center gap-2">
              <button @click="helpOpen = false" class="flex h-6 w-6 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)]">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
              <CatbotAvatar size="sm" />
              <span class="catbot-title text-[12px] font-bold">Catbot - Personal Tutor</span>
            </div>
          </div>

          <div ref="chatScrollEl" class="flex-1 overflow-y-auto p-4 space-y-3">
            <div class="flex items-start gap-2">
              <CatbotAvatar size="sm" />
              <div class="catbot-bubble-assistant rounded-xl rounded-tl-none p-3 text-[12px] leading-relaxed">
                Hey! I am your personal tutor. Need help with the task? Go ahead and ask.
              </div>
            </div>
            <div v-for="msg in chatMessages" :key="msg.id" class="flex items-start gap-2" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
              <CatbotAvatar v-if="msg.role === 'bot'" size="sm" />
              <div
                class="max-w-[85%] rounded-xl p-3 text-[12px] leading-relaxed"
                :class="msg.role === 'user'
                  ? 'rounded-tr-none bg-[var(--spotify-green)] text-black'
                  : 'catbot-bubble-assistant rounded-tl-none'"
              >
                <span v-if="msg.loading" class="flex items-center gap-1 text-[var(--ink3)]">
                  <span class="animate-bounce">●</span>
                  <span class="animate-bounce" style="animation-delay:0.15s">●</span>
                  <span class="animate-bounce" style="animation-delay:0.3s">●</span>
                </span>
                <span v-else style="white-space:pre-wrap">{{ msg.text }}</span>
              </div>
            </div>
          </div>

          <div class="border-t border-[var(--border)] p-3">
            <div class="mb-2 flex flex-wrap gap-1.5">
              <button v-for="p in quickPrompts" :key="p" @click="sendPrompt(p)" :disabled="chatLoading"
                class="rounded-full border border-[var(--border2)] bg-white px-2.5 py-1 text-[10px] font-medium text-[var(--ink2)] hover:border-emerald-300 hover:text-emerald-700 transition-colors disabled:opacity-40">
                {{ p }}
              </button>
            </div>
            <div class="flex gap-2">
              <input
                v-model="chatInput"
                :disabled="chatLoading"
                class="ct-input flex-1 py-1.5 text-[12px]"
                placeholder="Ask anything in your language"
                @keydown.enter="sendChat"
              />
              <button @click="sendChat" :disabled="chatLoading || !chatInput.trim()" class="ct-btn px-3 py-1.5 text-[12px] disabled:opacity-40">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/></svg>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <Teleport to="body">
      <AiKeyRequiredModal
        :open="showGate"
        @close="goBack"
        @profile="goToProfile"
      />
      <div v-if="showBackConfirm" class="fixed inset-0 z-[500] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="showBackConfirm = false"></div>
        <div class="relative z-10 w-full max-w-sm rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-6 shadow-xl">
          <div class="mb-1 text-[14px] font-bold text-[var(--ink)]">Thoát bài viết?</div>
          <p class="mb-5 text-[13px] text-[var(--ink3)]">Nội dung bài viết chưa được lưu. Bạn có chắc muốn thoát?</p>
          <div class="flex justify-end gap-2">
            <button class="ct-btn text-[12px]" @click="showBackConfirm = false">Tiếp tục</button>
            <button class="ct-btn text-[12px]" style="border-color:#e11d48;color:#e11d48" @click="router.back()">Thoát</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { imageUrl } from '@/utils/mediaUrl.js'
import { sanitizeHtml } from '@/utils/sanitizeHtml.js'
import { fetchWritingTopic, fetchWritingSetByTopic, postWritingChat, submitWriting as apiSubmitWriting } from '@/services/writingService.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'
import { useAiKeyGate } from '@/composables/useAiKeyGate.js'
import AiKeyRequiredModal from '@/components/ui/AiKeyRequiredModal.vue'
import CatbotAvatar from '@/components/ui/CatbotAvatar.vue'
import { cloneRouterState } from '@/utils/routerState.js'

const route = useRoute()
const router = useRouter()
const { showGate, hasAiKey, checkAiKey, requireAiKey, goToProfile, goBack } = useAiKeyGate()

const topic = ref(null)
const detail = ref(null)
const writingSet = ref(null)
const taskStep = ref(1)
const task1Result = ref(null)
const task1GradedMsg = ref('')
const task1Text = ref('')
const task2Text = ref('')
const allowLeave = ref(false)

const currentTopicId = computed(() => {
  if (writingSet.value) {
    return taskStep.value === 1
      ? writingSet.value.task1_topic_id
      : writingSet.value.task2_topic_id
  }
  return Number(route.params.topicId) || null
})

async function fetchDetail(id) {
  if (!id) return
  try {
    detail.value = await fetchWritingTopic(id)
    promptImageFailed.value = false
    if (overrideImageUrl.value) {
      URL.revokeObjectURL(overrideImageUrl.value)
      overrideImageUrl.value = null
    }
  } catch (e) {
    console.warn('Could not fetch writing detail:', e)
  }
}

async function initSession() {
  const state = history.state || {}
  if (state.writingSet) {
    writingSet.value = state.writingSet
    taskStep.value = state.taskStep === 2 ? 2 : 1
    if (state.task1Result) task1Result.value = state.task1Result
  } else {
    const id = Number(route.params.topicId)
    if (id) {
      try {
        const set = await fetchWritingSetByTopic(id)
        if (set) {
          writingSet.value = set
          taskStep.value = set.start_step === 2 ? 2 : 1
        }
      } catch {
        /* single-topic fallback */
      }
    }
  }

  const id = route.params.topicId
  if (!id) { router.back(); return }
  if (!topic.value) topic.value = { id: currentTopicId.value }
  await fetchDetail(currentTopicId.value)
  resetTimerForStep()
}

onMounted(async () => {
  await checkAiKey()
  const state = history.state?.topic
  if (state) topic.value = state
  await initSession()
  timerInterval = setInterval(() => { if (remaining.value > 0) remaining.value-- }, 1000)
  window.addEventListener('beforeunload', onBeforeUnload)
})

const detailQuestion = computed(() => (detail.value?.questions || [])[0] || null)

const promptHtml = computed(() =>
  sanitizeHtml(
    detailQuestion.value?.content_writing
      || detailQuestion.value?.title
      || topic.value?.prompt_html
      || topic.value?.prompt_text
      || '',
  ),
)

const instructionHtml = computed(() =>
  sanitizeHtml(detailQuestion.value?.instruction || ''),
)

const fallbackPromptHtml = computed(() =>
  sanitizeHtml(topic.value?.prompt_html || topic.value?.prompt_text || ''),
)

const effectiveTaskType = computed(() => {
  if (writingSet.value) return taskStep.value
  const t = detail.value?.writing_task_type ?? topic.value?.writing_task_type
  if (t === 1 || t === 2) return t
  return 1
})

const isTask1 = computed(() => effectiveTaskType.value === 1)
const isTask2 = computed(() => effectiveTaskType.value === 2)

const taskLabel = computed(() =>
  effectiveTaskType.value === 1
    ? '20 minutes - Write at least 150 words'
    : '40 minutes - Write at least 250 words'
)
const minWords = computed(() => effectiveTaskType.value === 1 ? 150 : 250)

/** Task 1: writing_graph_image · Task 2: thumbnail (cùng thư mục assets/images) */
const promptImageId = computed(() => {
  if (isTask1.value) return detailQuestion.value?.writing_graph_image || null
  return detail.value?.thumbnail || null
})

const showPromptImage = computed(() =>
  isTask1.value || (isTask2.value && !!promptImageId.value)
)

const promptImageLabel = computed(() =>
  isTask1.value ? 'Biểu đồ / hình minh họa' : 'Hình minh họa đề bài'
)

const promptImageAlt = computed(() =>
  isTask1.value ? 'IELTS Writing Task 1 chart' : 'IELTS Writing Task 2'
)

const overrideImageUrl = ref(null)
const promptImageFailed = ref(false)

const promptImageSrc = computed(() => {
  if (overrideImageUrl.value) return overrideImageUrl.value
  if (isTask1.value) {
    const fromApi = detailQuestion.value?.chart_image_url
    if (fromApi) return imageUrl(fromApi)
    return imageUrl(detailQuestion.value?.writing_graph_image)
  }
  const thumbUrl = detail.value?.thumbnail_url
  if (thumbUrl) return imageUrl(thumbUrl)
  return imageUrl(detail.value?.thumbnail)
})

const totalSecs = computed(() => (effectiveTaskType.value === 1 ? 20 : 40) * 60)
const remaining = ref(0)
let timerInterval = null

function resetTimerForStep() {
  remaining.value = totalSecs.value
}

const canSubmit = computed(() => hasAiKey.value && wordCount.value >= 20)

const submitButtonLabel = computed(() => {
  if (submitting.value) return 'Đang chấm bài...'
  if (writingSet.value && taskStep.value === 1) return 'Nộp Task 1 & chấm AI'
  if (writingSet.value && taskStep.value === 2) return 'Nộp Task 2 & xem kết quả'
  return 'Nộp bài & chấm AI'
})

async function switchToTask(step) {
  if (!writingSet.value || taskStep.value === step) return
  taskStep.value = step
  submitError.value = ''
  chatMessages.value = []
  resetTimerForStep()
  const topicId = step === 1 ? writingSet.value.task1_topic_id : writingSet.value.task2_topic_id
  await fetchDetail(topicId)
}

onUnmounted(() => {
  clearInterval(timerInterval)
  window.removeEventListener('beforeunload', onBeforeUnload)
  if (overrideImageUrl.value) URL.revokeObjectURL(overrideImageUrl.value)
})

function onBeforeUnload(e) {
  if (allowLeave.value) return
  const hasContent = task1Text.value.trim() || task2Text.value.trim()
  if (!hasContent) return
  e.preventDefault()
  e.returnValue = ''
}

const writingText = computed({
  get: () => (taskStep.value === 1 ? task1Text.value : task2Text.value),
  set: (v) => {
    if (taskStep.value === 1) task1Text.value = v
    else task2Text.value = v
  },
})
const fmtTimer = computed(() => {
  const s = remaining.value
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const ss = (s % 60).toString().padStart(2, '0')
  return `${m}:${ss}`
})

const wordCount = computed(() => writingText.value.trim().split(/\s+/).filter(Boolean).length)

function onImageUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (overrideImageUrl.value) URL.revokeObjectURL(overrideImageUrl.value)
  overrideImageUrl.value = URL.createObjectURL(file)
  promptImageFailed.value = false
  e.target.value = ''
}

function onFileUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => { writingText.value = ev.target.result }
  reader.readAsText(file)
}

const helpOpen = ref(false)
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
let chatMsgId = 0
const quickPrompts = ['How do I start?', 'Useful Vocabulary', 'Help with ideas', 'Answer Guide', 'Sample Answer']
const chatScrollEl = ref(null)

async function scrollChatDown() {
  await nextTick()
  if (chatScrollEl.value) chatScrollEl.value.scrollTop = chatScrollEl.value.scrollHeight
}

async function callWritingBot(userText) {
  if (!userText.trim() || chatLoading.value) return
  chatMessages.value.push({ id: chatMsgId++, role: 'user', text: userText })
  const placeholder = { id: chatMsgId++, role: 'bot', text: '', loading: true }
  chatMessages.value.push(placeholder)
  chatLoading.value = true
  await scrollChatDown()

  try {
    const promptText =
      detailQuestion.value?.content_writing ||
      detailQuestion.value?.title ||
      topic.value?.prompt_text || ''

    const history = chatMessages.value
      .filter(m => !m.loading && m.id < placeholder.id)
      .map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }))

    const data = await postWritingChat({
      prompt_text: promptText,
      user_message: userText,
      history,
    })
    placeholder.loading = false
    placeholder.text = data.reply || data.error || 'Sorry, something went wrong.'
  } catch {
    placeholder.loading = false
    placeholder.text = 'Network error. Please try again.'
  } finally {
    chatLoading.value = false
    await scrollChatDown()
  }
}

function sendPrompt(p) { callWritingBot(p) }
function sendChat() {
  const t = chatInput.value.trim()
  if (!t) return
  chatInput.value = ''
  callWritingBot(t)
}

const showBackConfirm = ref(false)
const submitting = ref(false)
const submitError = ref('')

function confirmBack() {
  const hasContent = task1Text.value.trim() || task2Text.value.trim()
  if (hasContent && !allowLeave.value) showBackConfirm.value = true
  else router.back()
}

function promptTextFor(topicId) {
  const parts = []
  const isT1 = topicId === writingSet.value?.task1_topic_id
  const setTitle = isT1 ? writingSet.value?.task1_title : writingSet.value?.task2_title
  const onMatchingTopic = currentTopicId.value === topicId
  const q = onMatchingTopic ? detailQuestion.value : null
  if (setTitle) parts.push(`Topic: ${setTitle}`)
  if (q?.title && q.title !== setTitle) parts.push(`Question: ${q.title}`)
  const body = q?.content_writing || (onMatchingTopic ? topic.value?.prompt_text : '')
  if (body) parts.push(body)
  if (q?.instruction) {
    const tmp = document.createElement('div')
    tmp.innerHTML = q.instruction
    const plain = (tmp.textContent || tmp.innerText || '').trim()
    if (plain) parts.push(`Writing guide: ${plain}`)
  }
  return parts.join('\n\n').trim() || setTitle || ''
}

async function submitTask1Grade() {
  const w1 = task1Text.value.trim().split(/\s+/).filter(Boolean).length
  if (w1 < 20) {
    submitError.value = 'Task 1 cần ít nhất ~20 từ.'
    return
  }
  submitting.value = true
  submitError.value = ''
  task1GradedMsg.value = ''
  const elapsed = Math.max(0, totalSecs.value - remaining.value)
  try {
    const result = await apiSubmitWriting({
      topic_id: writingSet.value.task1_topic_id,
      task_type: 1,
      essay_text: task1Text.value,
      word_count: w1,
      duration_seconds: elapsed,
      prompt_text: promptTextFor(writingSet.value.task1_topic_id),
    })
    useBadgeCelebrationStore().enqueue(result?.new_badges)
    task1Result.value = {
      history_id: result.history_id,
      band_score: result.band_score,
      evaluation: result.evaluation,
      essay_text: task1Text.value,
      word_count: w1,
      title: writingSet.value.task1_title || detailQuestion.value?.title || 'Task 1',
    }
    const band = Number(result.band_score || 0).toFixed(1)
    task1GradedMsg.value = `Task 1 đã chấm: Band ${band}. Bấm Task 2 để làm tiếp, hoặc xem chi tiết trong Lịch sử.`
  } catch (err) {
    submitError.value = formatApiError(err)
  } finally {
    submitting.value = false
  }
}

async function submitBothTasks() {
  const w1 = task1Text.value.trim().split(/\s+/).filter(Boolean).length
  const w2 = task2Text.value.trim().split(/\s+/).filter(Boolean).length
  if (w2 < 20) {
    submitError.value = 'Task 2 cần ít nhất ~20 từ trước khi nộp.'
    return
  }
  submitting.value = true
  submitError.value = ''
  const elapsed = Math.max(0, totalSecs.value - remaining.value)
  try {
    let t1Snapshot = task1Result.value
    if (!t1Snapshot) {
      if (w1 < 20) {
        submitError.value = 'Chưa chấm Task 1 — cần ít nhất ~20 từ ở Task 1.'
        submitting.value = false
        return
      }
      const r1 = await apiSubmitWriting({
        topic_id: writingSet.value.task1_topic_id,
        task_type: 1,
        essay_text: task1Text.value,
        word_count: w1,
        duration_seconds: elapsed,
        prompt_text: promptTextFor(writingSet.value.task1_topic_id),
      })
      t1Snapshot = {
        history_id: r1.history_id,
        band_score: r1.band_score,
        evaluation: r1.evaluation,
        essay_text: task1Text.value,
        word_count: w1,
        title: writingSet.value.task1_title || 'Task 1',
      }
    }
    const r2 = await apiSubmitWriting({
      topic_id: writingSet.value.task2_topic_id,
      task_type: 2,
      essay_text: task2Text.value,
      word_count: w2,
      duration_seconds: elapsed,
      prompt_text: promptTextFor(writingSet.value.task2_topic_id),
    })
    useBadgeCelebrationStore().enqueue(r2?.new_badges)
    allowLeave.value = true
    clearInterval(timerInterval)
    router.push({
      name: 'WritingResult',
      params: { historyId: r2.history_id },
      state: cloneRouterState({
        writingResult: {
          history_id: r2.history_id,
          band: r2.band_score,
          evaluation: r2.evaluation,
          essay_text: task2Text.value,
          task_type: 2,
          word_count: w2,
          title: writingSet.value.task2_title || writingSet.value.title || 'Task 2',
          task1Result: t1Snapshot,
          setTitle: writingSet.value.title,
        },
      }),
    })
  } catch (err) {
    submitError.value = formatApiError(err)
  } finally {
    submitting.value = false
  }
}

async function submitWriting() {
  if (!requireAiKey()) return
  if (!writingText.value.trim()) {
    submitError.value = 'Vui lòng viết nội dung trước khi nộp.'
    return
  }
  if (writingSet.value && taskStep.value === 1) {
    await submitTask1Grade()
    return
  }
  if (writingSet.value && taskStep.value === 2) {
    await submitBothTasks()
    return
  }

  submitting.value = true
  submitError.value = ''
  const elapsed = Math.max(0, totalSecs.value - remaining.value)
  try {
    const result = await apiSubmitWriting({
      topic_id: currentTopicId.value,
      task_type: effectiveTaskType.value,
      essay_text: writingText.value,
      word_count: wordCount.value,
      duration_seconds: elapsed,
      prompt_text: promptTextFor(currentTopicId.value),
    })
    useBadgeCelebrationStore().enqueue(result?.new_badges)
    allowLeave.value = true
    clearInterval(timerInterval)
    router.push({
      name: 'WritingResult',
      params: { historyId: result.history_id },
      state: cloneRouterState({
        writingResult: {
          history_id: result.history_id,
          band: result.band_score,
          evaluation: result.evaluation,
          essay_text: writingText.value,
          task_type: effectiveTaskType.value,
          word_count: wordCount.value,
          title: detailQuestion.value?.title || topic.value?.title || 'IELTS Writing',
        },
      }),
    })
  } catch (err) {
    submitError.value = formatApiError(err)
  } finally {
    submitting.value = false
  }
}

function formatApiError(err) {
  const detail = err.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(' · ')
  }
  if (typeof detail === 'string') return detail
  return err.message || 'Nộp bài thất bại. Vui lòng thử lại.'
}

watch(currentTopicId, async (id) => {
  if (id) await fetchDetail(id)
})
</script>
