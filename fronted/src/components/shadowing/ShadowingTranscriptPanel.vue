<template>
  <aside class="shadowing-transcript flex h-full min-h-0 w-full flex-col border-l border-gray-200 bg-white">
    <div class="flex shrink-0 items-center justify-between gap-2 border-b border-gray-100 px-4 py-3">
      <span class="sh-panel-title">Bản chép</span>
      <label class="flex cursor-pointer items-center gap-1 text-[10px] font-semibold text-gray-500">
        <input
          type="checkbox"
          class="rounded border-gray-300 text-emerald-500"
          :checked="showTranslation"
          @change="$emit('update:showTranslation', $event.target.checked)"
        />
        Trans
      </label>
    </div>

    <div ref="listEl" class="min-h-0 flex-1 overflow-y-auto p-3">
      <div
        v-for="(seg, idx) in segments"
        :key="seg.id"
        :ref="(el) => setCardRef(el, idx)"
        class="sh-transcript-card mb-2 w-full rounded-xl border border-gray-200 bg-white px-3 py-3 text-left transition-colors"
        :class="{ 'is-active': idx === activeIndex }"
      >
        <div class="mb-2 flex items-center justify-between">
          <button
            type="button"
            class="rounded-md px-2 py-0.5 text-[10px] font-bold"
            :class="idx === activeIndex ? 'bg-[var(--green-l)] text-black' : 'bg-gray-100 text-gray-500'"
            @click="$emit('seek', idx)"
          >
            #{{ seg.id }}
          </button>
          <button
            type="button"
            class="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 hover:bg-amber-50"
            :class="flaggedIds.includes(seg.id) ? '!text-amber-600' : ''"
            title="Đánh dấu câu khó"
            @click.stop="$emit('toggle-flag', seg.id)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
              <line x1="4" y1="22" x2="4" y2="15"/>
            </svg>
          </button>
        </div>

        <div
          role="button"
          tabindex="0"
          class="sh-transcript-body w-full cursor-pointer text-left"
          @click="$emit('seek', idx)"
          @keydown.enter="$emit('seek', idx)"
        >
          <p v-if="dictationMode" class="m-0 break-words text-[13px] leading-[1.65] text-black">
            <span
              v-for="(w, wi) in wordsOf(seg)"
              :key="wi"
              class="inline align-baseline"
            >
              <button
                v-if="!isWordRevealed(seg.id, wi)"
                type="button"
                class="mr-0.5 inline-flex h-4 w-4 align-middle items-center justify-center text-gray-500 hover:text-emerald-700"
                title="Hiện từ"
                @click.stop="$emit('reveal-word', seg.id, wi)"
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </button>
              <span :class="isWordRevealed(seg.id, wi) ? '' : 'text-gray-400'">
                {{ isWordRevealed(seg.id, wi) ? w : dotsFor(w) }}
              </span>
              <span v-if="wi < wordsOf(seg).length - 1">&nbsp;</span>
            </span>
          </p>
          <template v-else>
            <ShadowingVocabText
              v-if="vocabEnabled"
              class="sh-transcript-prose"
              :text="seg.text"
              :vocab-enabled="true"
              :source-quiz-id="sourceQuizId"
            />
            <p v-else class="m-0 break-words text-[13px] leading-[1.65] text-black">{{ seg.text }}</p>
          </template>
          <p
            v-if="showTranslation && seg.translation"
            class="mt-2 break-words text-[12px] leading-[1.55] text-gray-600"
          >
            {{ seg.translation }}
          </p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { tokenizeWords } from '@/utils/segmentUtils.js'
import ShadowingVocabText from '@/components/shadowing/ShadowingVocabText.vue'

const props = defineProps({
  segments: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: 0 },
  showTranslation: { type: Boolean, default: true },
  flaggedIds: { type: Array, default: () => [] },
  dictationMode: { type: Boolean, default: false },
  /** @type {Set<string> | string[]} keys `${segId}-${wi}` */
  revealedWordKeys: { type: [Set, Array], default: () => new Set() },
  vocabEnabled: { type: Boolean, default: true },
  sourceQuizId: { type: String, default: '' },
})

defineEmits(['seek', 'toggle-flag', 'update:showTranslation', 'reveal-word'])

const listEl = ref(null)
const cardRefs = ref({})

function setCardRef(el, idx) {
  if (el) cardRefs.value[idx] = el
}

function wordsOf(seg) {
  return tokenizeWords(seg?.text || '')
}

function wordKey(segId, wi) {
  return `${segId}-${wi}`
}

function isWordRevealed(segId, wi) {
  const keys = props.revealedWordKeys
  if (keys instanceof Set) return keys.has(wordKey(segId, wi))
  return (keys || []).includes(wordKey(segId, wi))
}

function dotsFor(w) {
  return '•'.repeat(Math.max(3, Math.min(8, w.length)))
}

watch(
  () => props.activeIndex,
  async (idx) => {
    await nextTick()
    const el = cardRefs.value[idx]
    if (el && listEl.value) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  },
)
</script>
