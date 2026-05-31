<template>
  <div class="flex h-screen flex-col overflow-hidden bg-white">

    <!-- ─── Top bar (Cathoven style) ─── -->
    <header class="flex h-12 shrink-0 items-center justify-between border-b border-[var(--border)] px-5">
      <div class="flex items-center gap-3">
        <button @click="confirmBack" class="flex h-7 w-7 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)]">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <span class="h-4 w-px bg-[var(--border)]"></span>
        <span class="text-[12px] text-[var(--ink3)]">Back</span>
        <span class="text-[var(--border)]">|</span>
        <span class="text-[13px] font-semibold text-[var(--ink)]">
          Task {{ effectiveTaskType }}: {{ taskLabel }}
        </span>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-1.5 rounded border border-[var(--border)] px-2.5 py-1 text-[12px] font-mono font-medium text-[var(--ink)]">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          {{ fmtTimer }}
        </div>

        <button
          @click="helpOpen = !helpOpen"
          class="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[11px] font-semibold text-emerald-800 hover:bg-emerald-600 hover:text-white transition-colors"
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>
          Need help with writing? Click here.
        </button>
      </div>
    </header>

    <!-- ─── Main 3-panel area ─── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Left: Prompt panel -->
      <div class="flex w-[42%] shrink-0 flex-col overflow-hidden border-r border-[var(--border)]">
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
                  Thiếu file <code class="rounded bg-white px-1">{{ promptImageId }}</code> trong
                  <code class="rounded bg-white px-1">backend/data/assets/images/</code>
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
      <div class="flex flex-1 flex-col overflow-hidden" :class="helpOpen ? 'border-r border-[var(--border)]' : ''">
        <div class="shrink-0 border-b border-[var(--border)] px-5 py-3">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Your Answer</div>
        </div>
        <div class="flex flex-1 overflow-hidden p-4">
          <textarea
            v-model="writingText"
            class="h-full w-full resize-none rounded-lg border border-transparent p-3 text-[13px] leading-relaxed text-[var(--ink)] outline-none placeholder-[var(--ink3)] focus:border-[var(--border)] transition-colors"
            placeholder="Write your answer here..."
          />
        </div>
        <div class="flex shrink-0 items-center justify-between border-t border-[var(--border)] px-5 py-2.5">
          <span class="text-[12px] text-[var(--ink3)]">Words: <strong class="text-[var(--ink)]">{{ wordCount }}</strong></span>
          <div class="flex items-center gap-2">
            <label class="ct-btn cursor-pointer text-[12px]">
              <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              Upload File
              <input type="file" accept=".txt,.doc,.docx" class="hidden" @change="onFileUpload" />
            </label>
            <button
              class="ct-btn text-[12px] font-semibold"
              :class="wordCount >= minWords ? 'bg-[#111] text-white border-[#111]' : 'opacity-50'"
              :disabled="submitting"
              @click="submitWriting"
            >{{ submitting ? 'Đang chấm bài...' : 'Nộp bài & chấm AI' }}</button>
          </div>
        </div>
      </div>

      <!-- Right: Help chat panel -->
      <Transition name="slide">
        <div v-if="helpOpen" class="flex w-80 shrink-0 flex-col overflow-hidden">
          <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <div class="flex items-center gap-2">
              <button @click="helpOpen = false" class="flex h-6 w-6 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)]">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
              <span class="text-[12px] font-bold text-[var(--ink)]">Catbot - Personal Tutor</span>
            </div>
          </div>

          <div ref="chatScrollEl" class="flex-1 overflow-y-auto p-4 space-y-3">
            <div class="flex items-start gap-2">
              <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-[10px] font-bold text-emerald-700">AI</div>
              <div class="rounded-xl rounded-tl-none bg-[var(--bg)] p-3 text-[12px] leading-relaxed text-[var(--ink)]">
                Hey! I am your personal tutor. Need help with the task? Go ahead and ask.
              </div>
            </div>
            <div v-for="msg in chatMessages" :key="msg.id" class="flex items-start gap-2" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
              <div v-if="msg.role === 'bot'" class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--purple-bg)] text-[10px] font-bold text-[var(--purple)]">AI</div>
              <div
                class="max-w-[85%] rounded-xl p-3 text-[12px] leading-relaxed"
                :class="msg.role === 'user'
                  ? 'rounded-tr-none bg-[#111] text-white'
                  : 'rounded-tl-none bg-[var(--bg)] text-[var(--ink)]'"
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
      <div v-if="showBackConfirm" class="fixed inset-0 z-[500] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="showBackConfirm = false"></div>
        <div class="relative z-10 w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
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
import { fetchWritingTopic, postWritingChat, submitWriting as apiSubmitWriting } from '@/services/writingService.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'

const route = useRoute()
const router = useRouter()

const topic = ref(null)
const detail = ref(null)

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

onMounted(async () => {
  const state = history.state?.topic
  if (state) topic.value = state
  const id = route.params.topicId
  if (!id) { router.back(); return }
  if (!topic.value) topic.value = { id }
  await fetchDetail(id)
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

onMounted(() => {
  remaining.value = totalSecs.value
  timerInterval = setInterval(() => { if (remaining.value > 0) remaining.value-- }, 1000)
  window.addEventListener('beforeunload', onBeforeUnload)
})
onUnmounted(() => {
  clearInterval(timerInterval)
  window.removeEventListener('beforeunload', onBeforeUnload)
  if (overrideImageUrl.value) URL.revokeObjectURL(overrideImageUrl.value)
})

function onBeforeUnload(e) { e.preventDefault(); e.returnValue = '' }

const fmtTimer = computed(() => {
  const s = remaining.value
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const ss = (s % 60).toString().padStart(2, '0')
  return `${m}:${ss}`
})

const writingText = ref('')
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
  if (writingText.value.trim()) showBackConfirm.value = true
  else router.back()
}

async function submitWriting() {
  if (!writingText.value.trim()) {
    submitError.value = 'Vui lòng viết nội dung trước khi nộp.'
    return
  }
  submitting.value = true
  submitError.value = ''
  const elapsed = Math.max(0, totalSecs.value - remaining.value)
  try {
    const result = await apiSubmitWriting({
      topic_id: Number(route.params.topicId),
      task_type: effectiveTaskType.value,
      essay_text: writingText.value,
      word_count: wordCount.value,
      duration_seconds: elapsed,
      prompt_text:
        detailQuestion.value?.content_writing
        || detailQuestion.value?.title
        || topic.value?.prompt_text
        || '',
    })
    useBadgeCelebrationStore().enqueue(result?.new_badges)
    clearInterval(timerInterval)
    router.push({
      path: '/history',
      state: {
        writingResult: {
          band: result.band_score,
          evaluation: result.evaluation,
          message: result.message,
        },
      },
    })
  } catch (err) {
    submitError.value = err.response?.data?.detail || 'Nộp bài thất bại. Vui lòng thử lại.'
  } finally {
    submitting.value = false
  }
}

watch(() => route.params.topicId, (id) => { if (id) fetchDetail(id) })
</script>
