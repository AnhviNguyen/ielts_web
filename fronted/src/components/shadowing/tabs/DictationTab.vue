<template>
  <div class="sh-tab-panel flex h-full min-h-0 flex-col">
    <div class="sh-card flex h-full min-h-0 flex-col overflow-y-auto p-6">
      <h2 class="sh-panel-title mb-4 shrink-0 text-center">Chép chính tả</h2>

      <p class="mb-2 shrink-0 text-[11px] font-bold uppercase tracking-wide text-gray-500">
        Gõ những gì bạn nghe được
      </p>
      <textarea
        v-model="userInput"
        class="mb-4 min-h-[120px] shrink-0 w-full resize-none rounded-xl border border-gray-200 bg-white px-4 py-3 text-[15px] text-black outline-none focus:border-[var(--green-l)] focus:ring-2 focus:ring-emerald-100"
        placeholder="Type what you hear..."
        @keydown.enter.ctrl="onNext"
      />

      <p class="mb-2 shrink-0 text-[11px] font-bold uppercase tracking-wide text-gray-500">
        Gợi ý từng từ
      </p>
      <div class="mb-4 flex shrink-0 flex-wrap justify-center gap-2">
        <button
          v-for="(w, wi) in words"
          :key="wi"
          type="button"
          class="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-[12px] font-medium text-black"
          @click="revealWord(wi)"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
          </svg>
          {{ isRevealed(wi) ? w : dotsFor(w) }}
        </button>
      </div>

      <div class="mt-auto flex shrink-0 flex-col gap-2 sm:flex-row">
        <button type="button" class="sh-btn sh-btn-block flex-1 border-amber-300 bg-amber-50" @click="revealAll">
          Hiện tất cả từ
        </button>
        <button type="button" class="sh-btn sh-btn-block flex-1 border-gray-300" @click="onReplay">
          Phát lại đoạn
        </button>
        <button type="button" class="sh-btn sh-btn-primary sh-btn-block flex-1 gap-2" @click="onNext">
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

function onNext() {
  const result = scoreAnswer(userInput.value, props.segment?.text || '')
  lastResult.value = result
  lastScore.value = result.score
  emit('scored', { index: props.segmentIndex, score: result.score })
  emit('next')
}

defineExpose({ replayCount, lastScore, lastResult, onReplay })
</script>
