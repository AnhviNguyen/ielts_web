<template>
  <section class="flex w-full flex-1 flex-col items-center justify-center py-2">
    <div class="relative w-full max-w-2xl rounded-3xl border border-[var(--border)] bg-[var(--bg-surface)] px-6 py-10 text-center shadow-[var(--shadow-medium)] sm:px-10">
      <AppLoading
        v-if="loadingExpected"
        message="Đang tải phiên âm chuẩn..."
        :size="44"
        inline
      />

      <div v-else-if="expectedError" class="py-6 text-center text-sm text-[var(--rose)]">
        {{ expectedError }}
      </div>

      <!-- Ready -->
      <template v-else-if="phase === 'ready'">
        <VocabSpeakerButton large title="Nghe mẫu" @play="$emit('speak')" />
        <p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-[var(--text-subdued)]">Speaking — phát âm từ</p>
        <p class="mb-1 text-3xl font-extrabold text-[var(--spotify-green)] sm:text-4xl">{{ word }}</p>
        <p v-if="expectedIpa" class="mb-1 text-sm text-[var(--text-subdued)]">{{ expectedIpa }}</p>
        <p v-if="meaningVi" class="mb-6 text-lg font-semibold text-[var(--text-base)]">{{ meaningVi }}</p>

        <button
          type="button"
          class="btn btn-primary inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-extrabold"
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
        <p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-[var(--text-subdued)]">Đang ghi âm</p>
        <p class="text-2xl font-extrabold text-[var(--text-base)]">{{ word }}</p>
        <p v-if="expectedIpa" class="mt-1 text-xs text-[var(--text-subdued)]">{{ expectedIpa }}</p>

        <div class="relative mx-auto mt-5 max-w-md">
          <div class="absolute inset-0 rounded-2xl bg-[var(--green-bg)]" aria-hidden="true" />
          <canvas
            ref="canvasRef"
            class="relative block h-20 w-full rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)]"
            width="400"
            height="80"
          />
        </div>

        <p class="mt-3 text-xs font-semibold text-[var(--spotify-green)]">
          {{ recordSeconds }}s / {{ MAX_RECORD_SECONDS }}s
        </p>

        <button
          type="button"
          class="ct-btn mt-4 inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-extrabold"
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
        <p class="mb-1 text-[11px] font-bold uppercase tracking-wider text-[var(--text-subdued)]">Kết quả</p>
        <p class="text-5xl font-black tabular-nums" :class="scoreColorClass">
          {{ Math.round(result.overall_score) }}
        </p>
        <p class="mt-1 text-sm font-bold text-[var(--text-base)]">{{ result.verdict?.trim() }}</p>
        <p class="mt-1 text-xs text-[var(--text-subdued)]">{{ result.ipa_expected }}</p>

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

        <ul v-if="wrongTips.length" class="mt-4 space-y-1 text-left text-xs text-[var(--text-subdued)]">
          <li v-for="(tip, i) in wrongTips" :key="i">• {{ tip }}</li>
        </ul>

        <div class="mt-6 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            class="ct-btn px-5 py-2.5 text-sm font-bold"
            @click="retry"
          >
            Thử lại
          </button>
          <button
            v-if="showNext"
            type="button"
            class="btn btn-primary px-5 py-2.5 text-sm font-extrabold disabled:opacity-50"
            :disabled="reviewing"
            @click="$emit('next')"
          >
            Tiếp theo
          </button>
        </div>
      </template>

      <p v-if="errorMsg" class="mt-4 text-center text-xs text-[var(--rose)]">{{ errorMsg }}</p>
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
  if (s >= 85) return 'text-[var(--spotify-green)]'
  if (s >= 70) return 'text-[var(--spotify-green-dark)]'
  if (s >= 50) return 'text-[var(--amber)]'
  return 'text-[var(--rose)]'
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
  if (p.correct) return 'border-[var(--spotify-green)] bg-[var(--green-bg)] text-[var(--spotify-green)]'
  if (p.score >= 0.5) return 'border-[var(--border)] bg-[var(--bg-interactive)] text-[var(--text-base)]'
  return 'border-[var(--rose)] bg-[var(--rose-bg)] text-[var(--rose)]'
}

function letterClass(letter) {
  if (letter.correct) return 'bg-[var(--green-bg)] text-[var(--spotify-green)]'
  if (letter.score >= 0.5) return 'bg-[var(--bg-interactive)] text-[var(--text-base)]'
  return 'bg-[var(--rose-bg)] text-[var(--rose)] ring-1 ring-[var(--rose)]'
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
    const status = e?.response?.status
    if (status === 401) {
      expectedError.value = 'Vui lòng đăng nhập để dùng kiểm tra phát âm.'
    } else {
      expectedError.value =
        e?.response?.data?.detail ||
        `Không tra được phiên âm cho "${props.word}".`
    }
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
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg-surface').trim() || '#121212'
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
