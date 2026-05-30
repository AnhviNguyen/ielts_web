<template>
  <div class="card p-4" :class="isCurrent ? 'ring-2 ring-[rgba(124,106,247,0.35)]' : ''">
    <div class="flex items-start justify-between gap-3">
      <div class="text-xs font-semibold text-[var(--ink2)]">{{ title }}</div>
      <div class="text-xs text-[var(--ink2)]">{{ questions.length }} gaps</div>
    </div>

    <div class="mt-2 text-sm text-[var(--ink2)]" v-if="description" v-html="safeDescription"></div>

    <div class="mt-4" ref="rootEl">
      <GapFillingHtml :html="html" :gaps="gapMap" @answer="onAnswer" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import GapFillingHtml from '@/components/mock-tests/GapFillingHtml.vue'
import { sanitizeHtml } from '@/utils/sanitizeHtml.js'

const props = defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  html: { type: String, default: '' },
  questions: { type: Array, default: () => [] }, // [{id, sort, order}]
  answers: { type: Object, default: () => ({}) }, // questionId -> string
  isCurrent: { type: Boolean, default: false },
})

const safeDescription = computed(() => sanitizeHtml(props.description))

const emit = defineEmits(['answer'])

const rootEl = ref(null)

const questionsSorted = computed(() => [...props.questions].sort((a, b) => (a.sort ?? 0) - (b.sort ?? 0)))

const gapMap = computed(() => {
  const out = {}
  // Expect placeholders gf_1..gf_n in order; map by index.
  questionsSorted.value.forEach((q, idx) => {
    out[`gf_${idx + 1}`] = { questionId: q.id, value: props.answers?.[q.id] ?? '' }
  })
  return out
})

// Handle answer from GapFillingHtml component
function onAnswer({ gapKey, value }) {
  const m = String(gapKey || '').match(/^gf_(\d+)$/)
  if (!m) return
  const idx = Number(m[1]) - 1
  const q = questionsSorted.value[idx]
  if (!q?.id) return
  emit('answer', { questionId: q.id, value })
}
</script>

