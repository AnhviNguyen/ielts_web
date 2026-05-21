<template>
  <div
    class="p-4"
    :class="[
      speakingCompact ? 'rounded-none border-0 bg-transparent p-4 shadow-none' : 'card',
      isCurrent && !speakingCompact ? 'ring-2 ring-[rgba(124,106,247,0.35)]' : '',
    ]"
  >
    <div class="flex items-start gap-2">
      <!-- Question number + audio play button (listening) -->
      <div class="flex shrink-0 items-center gap-1.5">
        <button
          v-if="canJumpToAudio"
          class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#34d399] text-white transition-colors hover:bg-[#059669]"
          :title="`Play from ${Math.floor(question.listen_from)}s`"
          @click.stop="$emit('jump-audio', { time: question.listen_from, locateInfo: question.locate_info })"
        >
          <svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        </button>
        <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--bg2)] text-[11px] font-bold text-[var(--ink2)]">
          {{ question.order }}
        </div>
      </div>
      <div class="flex-1" :class="speakingCompact ? '[&_.text-sm.font-semibold]:text-lg [&_.text-sm.font-semibold]:font-semibold [&_.text-sm.font-semibold]:leading-normal [&_.text-sm.font-semibold]:text-[var(--ink)]' : ''">
        <div class="text-sm font-semibold" v-if="question.text || question.title">{{ question.text || question.title }}</div>
        <div class="text-sm" v-else-if="question.content" v-html="question.content"></div>
      </div>
    </div>

    <div class="mt-3" v-if="mode === 'single'">
      <div class="grid gap-2">
        <label
          v-for="opt in singleOptions"
          :key="opt.option"
          class="flex items-center gap-2 rounded-xl border border-[var(--border2)] bg-[var(--surface)] px-3 py-2 cursor-pointer hover:border-[var(--ink3)]"
        >
          <input type="radio" :name="`q_${question.id}`" :value="opt.option" v-model="singleValue" />
          <div class="text-sm">
            <span class="font-semibold mr-2">{{ opt.option }}</span>
            <span>{{ opt.text }}</span>
          </div>
        </label>
      </div>
    </div>

    <div class="mt-3" v-else-if="mode === 'multi'">
      <div class="text-xs text-[var(--ink2)] mb-2">Choose {{ maxSelections }} answers</div>
      <div class="grid gap-2">
        <label
          v-for="opt in multiOptions"
          :key="opt.option"
          class="flex items-center gap-2 rounded-xl border border-[var(--border2)] bg-[var(--surface)] px-3 py-2 cursor-pointer hover:border-[var(--ink3)]"
        >
          <input type="checkbox" :value="opt.option" v-model="multiValue" :disabled="isMultiDisabled(opt.option)" />
          <div class="text-sm">
            <span class="font-semibold mr-2">{{ opt.option }}</span>
            <span>{{ opt.text }}</span>
          </div>
        </label>
      </div>
    </div>

    <div class="mt-3" v-else-if="mode === 'select'">
      <div class="text-xs text-[var(--ink2)] mb-2">Select answer</div>
      <select class="w-full rounded-xl border border-[var(--border2)] bg-[var(--surface)] px-3 py-2" v-model="singleValue">
        <option value="">—</option>
        <option v-for="opt in selectOptions" :key="opt.option" :value="opt.option">{{ opt.option }}</option>
      </select>
    </div>

    <!-- Speaking question: record button -->
    <div class="mt-5" v-else-if="mode === 'speaking'">
      <div
        class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-5"
        :class="speakingCompact ? 'flex flex-col items-center gap-4 text-center' : 'flex items-center justify-between gap-4'"
      >
        <div :class="speakingCompact ? 'w-full' : ''">
          <div class="text-[11px] font-semibold uppercase tracking-wider text-[var(--ink3)]">
            No time limit
          </div>
          <div class="mt-1 text-[13px] text-[var(--ink2)]">
            {{ isRecording ? `Đang ghi âm... ${elapsed}s` : recordedBlob ? 'Đã ghi xong' : 'Nhấn micro để bắt đầu ghi âm' }}
          </div>
        </div>
        <div class="flex flex-col items-center gap-1.5">
          <button
            type="button"
            @click="toggleRecord"
            class="flex items-center justify-center rounded-full border-2 transition-all"
            :class="[
              speakingCompact ? 'h-16 w-16' : 'h-12 w-12',
              isRecording
                ? 'border-[#e11d48] bg-[#e11d48] text-white animate-pulse'
                : 'border-[#34d399] bg-[#f0fdf4] text-[#34d399] hover:bg-[#34d399] hover:text-white',
            ]"
          >
            <svg v-if="!isRecording" :width="speakingCompact ? 22 : 18" :height="speakingCompact ? 22 : 18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
          </button>
          <div v-if="recordedBlob" class="text-[10px] font-medium text-[#059669]">✓ Đã ghi</div>
        </div>
      </div>

      <!-- Playback -->
      <audio v-if="recordedUrl" :src="recordedUrl" controls class="mt-2 w-full" style="height:32px"></audio>

      <!-- Min-duration hint -->
      <div
        v-if="recordedBlob && !isRecording && recordedElapsed < MIN_RECORD_SECONDS"
        class="mt-2 rounded-lg border border-[#f59e0b33] bg-[#fef9ee] px-3 py-2 text-[11px] text-[#b45309]"
      >
        Bài ghi quá ngắn ({{ recordedElapsed }}s). Ghi lại ít nhất {{ MIN_RECORD_SECONDS }} giây để đánh giá chính xác.
      </div>

      <!-- Evaluate button — only active when recording is long enough -->
            <button
              v-if="recordedBlob && !isRecording"
              :disabled="recordedElapsed < MIN_RECORD_SECONDS"
              class="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border-none py-2.5 text-sm font-semibold text-white transition-all"
              :class="evalReady
                ? 'cursor-pointer bg-emerald-400 hover:bg-emerald-600'
                : 'cursor-not-allowed bg-emerald-200 opacity-60'"
              @click="onEvalBtnClick"
            >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
        {{ recordedElapsed < MIN_RECORD_SECONDS ? `Ghi thêm ${MIN_RECORD_SECONDS - recordedElapsed}s...` : 'Đánh giá bài nói' }}
      </button>
    </div>

    <div class="mt-3" v-else>
      <div class="text-xs text-[var(--ink2)]">Unsupported question type: {{ question.question_type }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  item: { type: Object, required: true }, // from flattenQuizQuestions()
  answer: { type: [String, Array], default: undefined },
  isCurrent: { type: Boolean, default: false },
  /** Practice speaking: centered stack layout without outer card chrome */
  speakingCompact: { type: Boolean, default: false },
})

const emit = defineEmits(['update:answer', 'jump-audio', 'evaluate-speaking'])

const question = computed(() => props.item.question || {})
const questionSetType = computed(() => props.item.questionSetType || '')
const questionSetOptions = computed(() => props.item.questionSetOptions || [])
const maxSelections = computed(() => props.item.questionSetMaxSelections || 0)

const mode = computed(() => {
  const t = String(questionSetType.value || question.value.question_type || '').toUpperCase()
  if (t === 'SPEAKING' || t === 'speaking' || String(question.value.type || '').toLowerCase() === 'speaking') return 'speaking'
  if (t === 'MULTIPLE_CHOICE_MANY') return 'multi'
  if (
    t === 'TABLE_SELECTION' ||
    t === 'MATCHING' ||
    t === 'MATCHING_FEATURES' ||
    t === 'MATCHING_INFO' ||
    t === 'MATCHING_HEADING' ||
    t === 'MATCHING_HEADINGS' ||
    t === 'MATCHING_ENDINGS'
  ) return 'select'
  if (t === 'SINGLE_SELECTION' || t === 'SINGLE_CHOICE') return 'single'
  if (t === 'MULTIPLE_CHOICE_ONE') return 'single'
  return 'unknown'
})

// ── Speaking recorder ────────────────────────────────────────────────
const MIN_RECORD_SECONDS = 2

const isRecording    = ref(false)
const recordedUrl    = ref(null)
const recordedBlob   = ref(null)
const elapsed        = ref(0)   // live counter while recording
const recordedElapsed = ref(0)  // duration of the completed recording
let mediaRecorder    = null
let chunks           = []
let elapsedTimer     = null

async function toggleRecord() {
  if (isRecording.value) {
    recordedElapsed.value = elapsed.value
    mediaRecorder?.stop()
    isRecording.value = false
    clearInterval(elapsedTimer)
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    chunks = []
    elapsed.value = 0
    recordedElapsed.value = 0
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data)
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'audio/webm' })
      recordedBlob.value = blob
      recordedUrl.value  = URL.createObjectURL(blob)
      stream.getTracks().forEach(t => t.stop())
      emit('update:answer', 'recorded')
    }
    mediaRecorder.start()
    isRecording.value = true
    elapsedTimer = setInterval(() => elapsed.value++, 1000)
  } catch (err) {
    console.warn('Microphone access denied:', err)
  }
}

onUnmounted(() => {
  if (isRecording.value) mediaRecorder?.stop()
  clearInterval(elapsedTimer)
})

// ── Evaluate button helpers ───────────────────────────────────────────
const evalReady = computed(() => recordedElapsed.value >= MIN_RECORD_SECONDS)

function onEvalBtnClick() {
  if (!evalReady.value) return
  emit('evaluate-speaking', {
    blob: recordedBlob.value,
    questionText: question.value.text || question.value.title || '',
    questionId: question.value.id,
  })
}

const canJumpToAudio = computed(() => Number.isFinite(question.value.listen_from))

const singleOptions = computed(() => {
  // Some sets have global options (TRUE/FALSE/NG); others store options per question.
  const perQ = Array.isArray(question.value.options) ? question.value.options : []
  const setOpts = Array.isArray(questionSetOptions.value) ? questionSetOptions.value : []
  const opts = perQ.length ? perQ : setOpts
  return opts.map((o) => ({ option: o.option, text: o.text }))
})

const multiOptions = computed(() => {
  const perQ = Array.isArray(question.value.options) ? question.value.options : []
  return perQ.map((o) => ({ option: o.option, text: o.text }))
})

const selectOptions = computed(() => {
  const perQ = Array.isArray(question.value.options) ? question.value.options : []
  const setOpts = Array.isArray(questionSetOptions.value) ? questionSetOptions.value : []
  const opts = perQ.length ? perQ : setOpts
  return opts.map((o) => ({ option: o.option, text: o.text }))
})

const singleValue = ref('')
const multiValue = ref([])

watch(
  () => props.answer,
  (v) => {
    if (Array.isArray(v)) {
      multiValue.value = v
      singleValue.value = ''
    } else if (typeof v === 'string') {
      singleValue.value = v
      multiValue.value = []
    } else {
      singleValue.value = ''
      multiValue.value = []
    }
  },
  { immediate: true }
)

watch(singleValue, (v) => {
  if (mode.value === 'single' || mode.value === 'select') emit('update:answer', v)
})
watch(multiValue, (v) => {
  if (mode.value === 'multi') emit('update:answer', v)
}, { deep: true })

function isMultiDisabled(opt) {
  if (!maxSelections.value) return false
  if (multiValue.value.includes(opt)) return false
  return multiValue.value.length >= maxSelections.value
}

</script>

