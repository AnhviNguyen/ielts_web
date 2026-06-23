<template>
  <div class="sh-tab-panel flex h-full min-h-0 flex-col">
    <div class="sh-card flex h-full min-h-0 flex-col overflow-y-auto p-6">
      <h2 class="sh-panel-title mb-4 shrink-0 text-center">Chép chính tả</h2>

      <p class="mb-2 shrink-0 text-[11px] font-bold uppercase tracking-wide text-[var(--ink3)]">
        Gõ những gì bạn nghe được
      </p>
      <textarea
        v-model="userInput"
        class="mb-4 min-h-[120px] shrink-0 w-full resize-none rounded-xl border border-[var(--border)] bg-[var(--bg-interactive)] px-4 py-3 text-[15px] text-[var(--ink)] outline-none placeholder-[var(--ink3)] focus:border-[var(--spotify-green)] focus:ring-2 focus:ring-[var(--green-bg)]"
        placeholder="Type what you hear..."
        @keydown.enter.ctrl="onNext"
      />

      <div
        v-if="lastResult"
        class="mb-4 shrink-0 rounded-xl border px-4 py-3"
        :class="lastResult.score >= 80
          ? 'border-[var(--spotify-green)] bg-[var(--green-bg)]'
          : lastResult.score >= 50
            ? 'border-amber-300 bg-amber-50'
            : 'border-rose-300 bg-rose-50'"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="text-[12px] font-bold uppercase tracking-wide text-[var(--ink3)]">Kết quả</span>
          <span class="text-2xl font-bold" :class="lastResult.score >= 80 ? 'text-[var(--spotify-green)]' : lastResult.score >= 50 ? 'text-amber-700' : 'text-rose-600'">
            {{ lastResult.score }}%
          </span>
        </div>
        <p v-if="lastResult.wrong.length" class="mt-2 text-[13px] text-rose-700">
          Sai: {{ lastResult.wrong.join(', ') }}
        </p>
        <p v-if="lastResult.missing.length" class="mt-1 text-[13px] text-amber-800">
          Thiếu: {{ lastResult.missing.join(', ') }}
        </p>
        <p v-if="lastResult.score === 100" class="mt-2 text-[13px] font-semibold text-[var(--spotify-green)]">
          Chính xác!
        </p>
      </div>

      <p class="mb-2 shrink-0 text-[11px] font-bold uppercase tracking-wide text-[var(--ink3)]">
        Gợi ý từng từ
      </p>
      <div class="mb-4 flex shrink-0 flex-wrap justify-center gap-2">
        <button
          v-for="(w, wi) in words"
          :key="wi"
          type="button"
          class="inline-flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--bg-interactive)] px-2.5 py-1.5 text-[12px] font-medium text-[var(--ink)] hover:border-[var(--spotify-green)] hover:bg-[var(--green-bg)]"
          @click="revealWord(wi)"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
          </svg>
          {{ isRevealed(wi) ? w : dotsFor(w) }}
        </button>
      </div>

      <div class="mt-auto flex shrink-0 flex-col gap-2 sm:flex-row sm:flex-wrap">
        <button type="button" class="sh-btn sh-btn-block flex-1 border-amber-300 bg-amber-50 sm:min-w-[140px]" @click="revealAll">
          Hiện tất cả từ
        </button>
        <button type="button" class="sh-btn sh-btn-block flex-1 border-gray-300 sm:min-w-[140px]" @click="onReplay">
          Phát lại đoạn
        </button>
        <button type="button" class="sh-btn sh-btn-primary sh-btn-block flex-1 gap-2 sm:min-w-[140px]" @click="onCheck">
          Kiểm tra
        </button>
        <button type="button" class="sh-btn sh-btn-block flex-1 gap-2 border-[var(--spotify-green)] sm:min-w-[140px]" @click="onNext">
          Tiếp theo
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { tokenizeWords, scoreAnswer } from '@/utils/segmentUtils.js'

const props = defineProps({
  segment: { type: Object, default: null },
  segmentIndex: { type: Number, default: 0 },
  /** @type {Set<string>} */
  revealedWordKeys: { type: [Set, Object], default: () => new Set() },
})

const emit = defineEmits(['scored', 'next', 'replay', 'reveal-word', 'reveal-all'])

const userInput = ref('')
const replayCount = ref(0)
const lastResult = ref(null)
const lastScore = ref(null)

const words = computed(() => tokenizeWords(props.segment?.text || ''))
const segId = computed(() => props.segment?.id ?? props.segmentIndex)

function wordKey(wi) {
  return `${segId.value}-${wi}`
}

function isRevealed(wi) {
  const keys = props.revealedWordKeys
  if (keys instanceof Set) return keys.has(wordKey(wi))
  return false
}

function dotsFor(w) {
  return '•'.repeat(Math.max(3, Math.min(8, w.length)))
}

function revealWord(wi) {
  emit('reveal-word', segId.value, wi)
}

function revealAll() {
  emit('reveal-all', segId.value, words.value.length)
}

watch(() => props.segmentIndex, () => {
  userInput.value = ''
  replayCount.value = 0
  lastResult.value = null
  lastScore.value = null
})

function onReplay() {
  replayCount.value += 1
  emit('replay')
}

function runScore() {
  const result = scoreAnswer(userInput.value, props.segment?.text || '')
  lastResult.value = result
  lastScore.value = result.score
  emit('scored', { index: props.segmentIndex, score: result.score })
  return result
}

function onCheck() {
  if (!userInput.value.trim()) return
  runScore()
}

function onNext() {
  if (userInput.value.trim() && !lastResult.value) runScore()
  emit('next')
}

defineExpose({ replayCount, lastScore, lastResult, onReplay, onCheck })
</script>
