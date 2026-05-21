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
        <button type="button" class="sh-btn sh-btn-primary gap-2" :disabled="listening || checking" @click="toggleRecord">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          </svg>
          {{ listening ? 'Đang ghi...' : checking ? 'Đang phân tích...' : 'Ghi âm & kiểm tra' }}
        </button>
        <button type="button" class="sh-btn gap-2" :disabled="!lastBlobUrl" @click="playRecording">
          Phát lại ghi âm
        </button>
      </div>

      <div class="mt-auto shrink-0 text-center">
        <p class="text-sm font-semibold text-black">
          Điểm: <span class="text-[#059669]">{{ score ?? '—' }}</span>
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

const listening = ref(false)
const checking = ref(false)
const score = ref(null)
const wordResults = ref(null)
const transcript = ref('')
const wrongWords = ref([])
const errorMsg = ref('')
const lastBlobUrl = ref(null)
let mediaRecorder = null
let mediaStream = null
const chunks = ref([])
const lastBlob = ref(null)

const displayWords = computed(() => {
  if (wordResults.value?.length) {
    return wordResults.value.map((w) => ({ word: w.word, ok: w.ok }))
  }
  return tokenizeWords(props.segment?.text || '').map((w) => ({ word: w, ok: null }))
})

const tip = computed(() => {
  if (checking.value) return 'Đang chạy Whisper + mô hình phát âm...'
  if (score.value == null) return 'Nói rõ từng âm tiết, chú ý ngữ điệu lên xuống.'
  if (score.value >= 80) return 'Rất tốt! Giữ nhịp độ và nhấn trọng âm đúng chỗ.'
  return 'Thử nói chậm hơn, bắt chước ngữ điệu trong video.'
})

watch(() => props.segmentIndex, () => {
  resetResults()
})

function resetResults() {
  score.value = null
  wordResults.value = null
  transcript.value = ''
  wrongWords.value = []
  errorMsg.value = ''
}

async function toggleRecord() {
  if (listening.value) {
    mediaRecorder?.stop()
    return
  }
  if (!props.segment?.text?.trim()) {
    errorMsg.value = 'Không có câu mục tiêu để so khớp.'
    return
  }
  resetResults()
  chunks.value = []
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(mediaStream)
    mediaRecorder.ondataavailable = (e) => chunks.value.push(e.data)
    mediaRecorder.onstop = async () => {
      listening.value = false
      const blob = new Blob(chunks.value, { type: 'audio/webm' })
      lastBlob.value = blob
      if (lastBlobUrl.value) URL.revokeObjectURL(lastBlobUrl.value)
      lastBlobUrl.value = URL.createObjectURL(blob)
      mediaStream?.getTracks().forEach((t) => t.stop())
      mediaStream = null
      await runCheck(blob)
    }
    mediaRecorder.start()
    listening.value = true
    errorMsg.value = ''
  } catch {
    errorMsg.value = 'Không truy cập được micro. Cho phép quyền ghi âm.'
    listening.value = false
  }
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
    emit('scored', { index: props.segmentIndex, score: data.score })
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Kiểm tra phát âm thất bại.'
  } finally {
    checking.value = false
  }
}

function playRecording() {
  if (lastBlobUrl.value) new Audio(lastBlobUrl.value).play()
}

onUnmounted(() => {
  mediaRecorder?.stop()
  mediaStream?.getTracks().forEach((t) => t.stop())
  if (lastBlobUrl.value) URL.revokeObjectURL(lastBlobUrl.value)
})

defineExpose({
  listening,
  score,
  tip,
  toggleRecord,
  playRecording,
  lastBlobUrl,
  checking,
})
</script>
