<template>
  <div class="sh-tab-panel flex h-full min-h-0 flex-col">
    <div class="sh-card flex h-full min-h-0 flex-col overflow-y-auto p-6">
      <h2 class="sh-panel-title mb-4 shrink-0 text-center">Phản hồi phát âm</h2>

      <div class="mb-4 flex shrink-0 flex-wrap justify-center gap-2">
        <span
          v-for="(item, i) in displayWords"
          :key="i"
          class="sh-word-chip text-lg"
          :class="item.ok === true
            ? '!border-emerald-400 !bg-emerald-50 !text-emerald-900'
            : item.ok === false
              ? '!border-rose-400 !bg-rose-50 !text-rose-800'
              : ''"
        >
          {{ item.word }}
        </span>
      </div>

      <ShadowingVocabText
        v-if="segment?.text"
        class="mb-4 shrink-0"
        :text="segment.text"
        :vocab-enabled="true"
        :large="false"
        :source-quiz-id="sourceQuizId"
      />

      <p v-if="showTranslation && segment?.translation" class="mb-4 shrink-0 text-center text-[15px] italic text-gray-600">
        {{ segment.translation }}
      </p>

      <p v-if="transcript" class="mb-3 shrink-0 text-center text-[12px] text-gray-500">
        Bạn nói: <span class="font-medium text-black">{{ transcript }}</span>
      </p>

      <p v-if="errorMsg" class="mb-3 shrink-0 text-center text-[12px] text-rose-600">{{ errorMsg }}</p>

      <div class="mb-4 flex shrink-0 flex-wrap justify-center gap-2">
        <button
          type="button"
          class="sh-btn sh-btn-primary gap-2"
          :disabled="checking"
          @click="toggleRecord"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          </svg>
          {{ recordButtonLabel }}
        </button>
        <button type="button" class="sh-btn gap-2" :disabled="!lastBlobUrl || checking" @click="playRecording">
          Phát lại ghi âm
        </button>
        <button
          v-if="lastBlobUrl && !listening && !checking"
          type="button"
          class="sh-btn gap-2 text-rose-700"
          @click="clearRecording"
        >
          Xóa ghi âm
        </button>
      </div>

      <p v-if="listening" class="mb-3 shrink-0 text-center text-[12px] font-medium text-emerald-700">
        Đang ghi âm... {{ elapsed }}s — nhấn lại để dừng và kiểm tra
      </p>

      <div class="mt-auto shrink-0 text-center">
        <p class="text-sm font-semibold text-black">
          Điểm: <span class="text-[#059669]">{{ score ?? '—' }}</span>
        </p>
        <p v-if="pronDetails" class="mt-1 text-[11px] text-gray-500">
          Mô hình: chính xác {{ pronDetails.accuracy?.toFixed?.(1) ?? '—' }} · trôi chảy {{ pronDetails.fluency?.toFixed?.(1) ?? '—' }} · ngữ điệu {{ pronDetails.prosodic?.toFixed?.(1) ?? '—' }}
        </p>
        <p v-if="wrongWords.length" class="mt-2 text-[12px] text-rose-700">
          Từ cần luyện: {{ wrongWords.join(', ') }}
        </p>
        <p class="mt-2 text-[11px] italic text-gray-600">{{ tip }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { tokenizeWords } from '@/utils/segmentUtils.js'
import { checkPronunciation } from '@/services/shadowingService.js'
import ShadowingVocabText from '@/components/shadowing/ShadowingVocabText.vue'

const props = defineProps({
  segment: { type: Object, default: null },
  showTranslation: { type: Boolean, default: true },
  segmentIndex: { type: Number, default: 0 },
  sourceQuizId: { type: String, default: '' },
})

const emit = defineEmits(['scored'])

const MIN_RECORD_SECONDS = 1

const listening = ref(false)
const checking = ref(false)
const elapsed = ref(0)
const score = ref(null)
const wordResults = ref(null)
const transcript = ref('')
const wrongWords = ref([])
const pronDetails = ref(null)
const errorMsg = ref('')
const lastBlobUrl = ref(null)
let mediaRecorder = null
let mediaStream = null
let chunks = []
let elapsedTimer = null
const lastBlob = ref(null)

const recordButtonLabel = computed(() => {
  if (checking.value) return 'Đang phân tích...'
  if (listening.value) return `Dừng ghi (${elapsed.value}s)`
  return 'Ghi âm & kiểm tra'
})

const displayWords = computed(() => {
  if (wordResults.value?.length) {
    return wordResults.value.map((w) => ({ word: w.word, ok: w.ok }))
  }
  return tokenizeWords(props.segment?.text || '').map((w) => ({ word: w, ok: null }))
})

const tip = computed(() => {
  if (checking.value) return 'Đang chạy Whisper + mô hình phát âm (pron_scorer)...'
  if (score.value == null) return 'Nói rõ từng âm tiết, chú ý ngữ điệu lên xuống.'
  if (score.value >= 80) return 'Rất tốt! Giữ nhịp độ và nhấn trọng âm đúng chỗ.'
  return 'Thử nói chậm hơn, bắt chước ngữ điệu trong video.'
})

watch(() => props.segmentIndex, () => {
  stopRecording({ discard: true })
  resetResults()
})

function pickMimeType() {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) || ''
}

function resetResults() {
  score.value = null
  wordResults.value = null
  transcript.value = ''
  wrongWords.value = []
  pronDetails.value = null
  errorMsg.value = ''
}

function stopRecording({ discard = false } = {}) {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
  if (mediaRecorder) {
    if (discard) mediaRecorder.onstop = null
    if (mediaRecorder.state !== 'inactive') {
      try { mediaRecorder.stop() } catch { /* ignore */ }
    }
  }
  mediaStream?.getTracks().forEach((t) => t.stop())
  mediaStream = null
  mediaRecorder = null
  listening.value = false
}

function clearRecording() {
  stopRecording({ discard: true })
  if (lastBlobUrl.value) URL.revokeObjectURL(lastBlobUrl.value)
  lastBlobUrl.value = null
  lastBlob.value = null
  resetResults()
}

async function toggleRecord() {
  if (checking.value) return

  if (listening.value) {
    if (elapsed.value < MIN_RECORD_SECONDS) {
      errorMsg.value = `Ghi ít nhất ${MIN_RECORD_SECONDS} giây rồi nhấn dừng để kiểm tra.`
      return
    }
    mediaRecorder?.stop()
    return
  }

  if (!props.segment?.text?.trim()) {
    errorMsg.value = 'Không có câu mục tiêu để so khớp.'
    return
  }

  clearRecording()
  chunks = []
  elapsed.value = 0

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mimeType = pickMimeType()
    mediaRecorder = mimeType
      ? new MediaRecorder(mediaStream, { mimeType })
      : new MediaRecorder(mediaStream)

    mediaRecorder.ondataavailable = (e) => {
      if (e.data?.size > 0) chunks.push(e.data)
    }

    mediaRecorder.onstop = async () => {
      listening.value = false
      if (elapsedTimer) {
        clearInterval(elapsedTimer)
        elapsedTimer = null
      }
      mediaStream?.getTracks().forEach((t) => t.stop())
      mediaStream = null

      const blobType = mimeType || 'audio/webm'
      const blob = new Blob(chunks, { type: blobType })
      chunks = []

      if (!blob.size) {
        errorMsg.value = 'Không thu được âm thanh. Kiểm tra micro và thử lại.'
        return
      }

      lastBlob.value = blob
      if (lastBlobUrl.value) URL.revokeObjectURL(lastBlobUrl.value)
      lastBlobUrl.value = URL.createObjectURL(blob)
      await runCheck(blob)
    }

    mediaRecorder.start()
    listening.value = true
    errorMsg.value = ''
    elapsedTimer = setInterval(() => { elapsed.value += 1 }, 1000)
  } catch {
    stopRecording()
    errorMsg.value = 'Không truy cập được micro. Cho phép quyền ghi âm trong trình duyệt.'
  }
}

function formatApiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg || d).join('; ')
  return err?.message || 'Kiểm tra phát âm thất bại.'
}

async function runCheck(blob) {
  checking.value = true
  errorMsg.value = ''
  try {
    const data = await checkPronunciation(blob, props.segment.text)
    score.value = data.score
    wordResults.value = data.word_results || []
    transcript.value = data.transcript || ''
    wrongWords.value = data.wrong_words || []
    pronDetails.value = data.pronunciation || null
    emit('scored', { index: props.segmentIndex, score: data.score })
  } catch (e) {
    errorMsg.value = formatApiError(e)
  } finally {
    checking.value = false
  }
}

function playRecording() {
  if (lastBlobUrl.value) new Audio(lastBlobUrl.value).play()
}

onUnmounted(() => {
  stopRecording()
  if (lastBlobUrl.value) URL.revokeObjectURL(lastBlobUrl.value)
})

defineExpose({
  listening,
  checking,
  score,
  tip,
  toggleRecord,
  playRecording,
  clearRecording,
  lastBlobUrl,
})
</script>
