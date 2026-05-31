<template>
  <section class="flex w-full flex-1 flex-col items-center justify-center py-2">
    <div class="relative w-full max-w-2xl rounded-3xl border border-slate-200 bg-white px-6 py-10 text-center shadow-lg sm:px-10">
      <AppLoading
        v-if="loadingExpected"
        message="Đang tải phiên âm chuẩn..."
        :size="44"
        inline
      />

      <div v-else-if="expectedError" class="py-6 text-center text-sm text-rose-600">
        {{ expectedError }}
      </div>

      <!-- Ready -->
      <template v-else-if="phase === 'ready'">
        <VocabSpeakerButton large title="Nghe mẫu" @play="$emit('speak')" />
        <p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">Speaking — phát âm từ</p>
        <p class="mb-1 text-3xl font-extrabold text-emerald-700 sm:text-4xl">{{ word }}</p>
        <p v-if="expectedIpa" class="mb-1 text-sm text-slate-500">{{ expectedIpa }}</p>
        <p v-if="meaningVi" class="mb-6 text-lg font-semibold text-slate-700">{{ meaningVi }}</p>

        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-extrabold text-white transition-colors hover:bg-emerald-700"
          @click="startRecording"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          </svg>
          Bắt đầu ghi âm
        </button>
      </template>

      <!-- Recording -->
      <template v-else-if="phase === 'recording'">
        <p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">Đang ghi âm</p>
        <p class="text-2xl font-extrabold text-slate-900">{{ word }}</p>
        <p v-if="expectedIpa" class="mt-1 text-xs text-slate-500">{{ expectedIpa }}</p>

        <div class="relative mx-auto mt-5 max-w-md">
          <div class="absolute inset-0 rounded-2xl bg-emerald-50/80" aria-hidden="true" />
          <canvas
            ref="canvasRef"
            class="relative block h-20 w-full rounded-2xl border border-emerald-200 bg-white"
            width="400"
            height="80"
          />
        </div>

        <p class="mt-3 text-xs font-semibold text-emerald-700">
          {{ recordSeconds }}s / {{ MAX_RECORD_SECONDS }}s
        </p>

        <button
          type="button"
          class="mt-4 inline-flex items-center justify-center gap-2 rounded-xl border-2 border-slate-900 bg-white px-6 py-3 text-sm font-extrabold text-slate-900 transition-colors hover:bg-slate-900 hover:text-white"
          @click="stopRecording"
        >
          <span class="inline-block h-3 w-3 rounded-sm bg-emerald-500" />
          Dừng & kiểm tra
        </button>
      </template>

      <!-- Checking -->
      <AppLoading
        v-else-if="phase === 'checking'"
        message="Đang kiểm tra phát âm..."
        :size="48"
        inline
      />

      <!-- Result -->
      <template v-else-if="phase === 'result' && result">
        <p class="mb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">Kết quả</p>
        <p class="text-5xl font-black tabular-nums" :class="scoreColorClass">
          {{ Math.round(result.overall_score) }}
        </p>
        <p class="mt-1 text-sm font-bold text-slate-800">{{ result.verdict?.trim() }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ result.ipa_expected }}</p>

        <div class="mt-5 flex flex-wrap justify-center gap-1.5">
          <span
            v-for="(p, i) in result.phonemes"
            :key="'ph-' + i"
            class="rounded-lg border px-2.5 py-1 text-sm font-bold"
            :class="phonemeBadgeClass(p)"
            :title="p.tip || ''"
          >
            /{{ p.ipa }}/
          </span>
        </div>

        <div class="mt-4 flex flex-wrap justify-center gap-0.5">
          <span
            v-for="(letter, i) in displayLetters"
            :key="'ch-' + i"
            class="rounded-md px-1.5 py-1 text-3xl font-extrabold tracking-wide"
            :class="letterClass(letter)"
          >
            {{ letter.char }}
          </span>
        </div>

        <ul v-if="wrongTips.length" class="mt-4 space-y-1 text-left text-xs text-slate-600">
          <li v-for="(tip, i) in wrongTips" :key="i">• {{ tip }}</li>
        </ul>

        <div class="mt-6 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            class="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-bold text-slate-700 transition-colors hover:border-emerald-400 hover:bg-emerald-50 hover:text-emerald-800"
            @click="retry"
          >
            Thử lại
          </button>
          <button
            v-if="showNext"
            type="button"
            class="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-extrabold text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
            :disabled="reviewing"
            @click="$emit('next')"
          >
            Tiếp theo
          </button>
        </div>
      </template>

      <p v-if="errorMsg" class="mt-4 text-center text-xs text-rose-600">{{ errorMsg }}</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import AppLoading from '@/components/ui/AppLoading.vue'
import VocabSpeakerButton from '@/components/vocabulary/practice/VocabSpeakerButton.vue'
import { getWordExpectedPhonemes, scoreWordPronunciation } from '@/services/pronunciationService.js'

const props = defineProps({
  word: { type: String, required: true },
  meaningVi: { type: String, default: '' },
  result: { type: String, default: null },
  reviewing: Boolean,
  showNext: { type: Boolean, default: true },
})

const emit = defineEmits(['scored', 'next', 'speak', 'retry'])

const PASS_SCORE = 65
const MAX_RECORD_SECONDS = 5
const WAVE_COLOR = '#34d399' // --green-l

const phase = ref('ready')
const loadingExpected = ref(true)
const expectedError = ref('')
const expectedIpa = ref('')
const errorMsg = ref('')
const result = ref(null)
const recordSeconds = ref(0)

const canvasRef = ref(null)
let mediaRecorder = null
let mediaStream = null
let chunks = []
let recordTimer = null
let autoStopTimer = null
let analyser = null
let audioContext = null
let animationId = null

const scoreColorClass = computed(() => {
  const s = result.value?.overall_score ?? 0
  if (s >= 85) return 'text-emerald-600'
  if (s >= 70) return 'text-emerald-700'
  if (s >= 50) return 'text-slate-700'
  return 'text-slate-900'
})

const displayLetters = computed(() => {
  if (result.value?.letters?.length) return result.value.letters
  return [...props.word].map((ch) => ({ char: ch, score: 0, correct: false }))
})

const wrongTips = computed(() =>
  (result.value?.phonemes || [])
    .filter((p) => !p.correct && p.tip)
    .map((p) => p.tip)
    .slice(0, 3),
)

function phonemeBadgeClass(p) {
  if (p.correct) return 'border-emerald-400 bg-emerald-50 text-emerald-800'
  if (p.score >= 0.5) return 'border-slate-300 bg-slate-50 text-slate-700'
  return 'border-slate-800 bg-white text-slate-900'
}

function letterClass(letter) {
  if (letter.correct) return 'bg-emerald-50 text-emerald-700'
  if (letter.score >= 0.5) return 'bg-slate-100 text-slate-700'
  return 'bg-white text-slate-900 ring-1 ring-slate-300'
}

watch(() => props.word, () => {
  resetAll()
  loadExpected()
})

watch(() => props.result, (val) => {
  if (!val) {
    phase.value = 'ready'
    result.value = null
  }
})

onMounted(loadExpected)
onUnmounted(cleanupRecording)

async function loadExpected() {
  loadingExpected.value = true
  expectedError.value = ''
  expectedIpa.value = ''
  try {
    const data = await getWordExpectedPhonemes(props.word)
    expectedIpa.value = data.ipa || ''
  } catch (e) {
    expectedError.value =
      e?.response?.data?.detail ||
      `Không tra được phiên âm cho "${props.word}".`
  } finally {
    loadingExpected.value = false
  }
}

function pickMimeType() {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) || ''
}

function resetAll() {
  cleanupRecording()
  phase.value = 'ready'
  result.value = null
  errorMsg.value = ''
  recordSeconds.value = 0
}

function cleanupRecording() {
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
  if (autoStopTimer) {
    clearTimeout(autoStopTimer)
    autoStopTimer = null
  }
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    try { mediaRecorder.stop() } catch { /* ignore */ }
  }
  mediaStream?.getTracks().forEach((t) => t.stop())
  mediaStream = null
  mediaRecorder = null
  if (audioContext) {
    audioContext.close().catch(() => {})
    audioContext = null
  }
  analyser = null
  chunks = []
}

function drawWaveform() {
  const canvas = canvasRef.value
  if (!canvas || !analyser) return
  const ctx = canvas.getContext('2d')
  const buffer = new Uint8Array(analyser.frequencyBinCount)
  analyser.getByteTimeDomainData(buffer)
  const w = canvas.width
  const h = canvas.height
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, w, h)
  ctx.lineWidth = 2
  ctx.strokeStyle = WAVE_COLOR
  ctx.beginPath()
  const slice = w / buffer.length
  let x = 0
  for (let i = 0; i < buffer.length; i++) {
    const v = buffer[i] / 128.0
    const y = (v * h) / 2
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
    x += slice
  }
  ctx.lineTo(w, h / 2)
  ctx.stroke()
  animationId = requestAnimationFrame(drawWaveform)
}

async function startRecording() {
  if (expectedError.value) return
  emit('speak')
  errorMsg.value = ''
  chunks = []
  recordSeconds.value = 0

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(mediaStream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)

    const mimeType = pickMimeType()
    mediaRecorder = mimeType
      ? new MediaRecorder(mediaStream, { mimeType })
      : new MediaRecorder(mediaStream)

    mediaRecorder.ondataavailable = (e) => {
      if (e.data?.size > 0) chunks.push(e.data)
    }
    mediaRecorder.onstop = onRecordStop

    mediaRecorder.start()
    phase.value = 'recording'
    recordTimer = setInterval(() => { recordSeconds.value += 1 }, 1000)
    autoStopTimer = setTimeout(stopRecording, MAX_RECORD_SECONDS * 1000)
    requestAnimationFrame(drawWaveform)
  } catch {
    cleanupRecording()
    phase.value = 'ready'
    errorMsg.value = 'Không truy cập được micro. Cho phép quyền ghi âm trong trình duyệt.'
  }
}

function stopRecording() {
  if (autoStopTimer) {
    clearTimeout(autoStopTimer)
    autoStopTimer = null
  }
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
}

async function onRecordStop() {
  mediaStream?.getTracks().forEach((t) => t.stop())
  mediaStream = null
  if (audioContext) {
    await audioContext.close().catch(() => {})
    audioContext = null
  }
  analyser = null

  const blob = new Blob(chunks, { type: chunks[0]?.type || 'audio/webm' })
  chunks = []

  if (!blob.size) {
    phase.value = 'ready'
    errorMsg.value = 'Không thu được âm thanh. Thử lại.'
    return
  }

  phase.value = 'checking'
  try {
    const data = await scoreWordPronunciation(props.word, blob)
    result.value = data
    phase.value = 'result'
    emit('scored', {
      score: data.overall_score,
      correct: data.overall_score >= PASS_SCORE,
      result: data,
    })
  } catch (e) {
    phase.value = 'ready'
    errorMsg.value =
      e?.response?.data?.detail || e?.message || 'Kiểm tra phát âm thất bại.'
  }
}

function retry() {
  resetAll()
  emit('retry')
}
</script>
