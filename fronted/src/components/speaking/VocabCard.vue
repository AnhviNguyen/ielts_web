<template>
  <div class="card p-5">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="text-[var(--ink2)]"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        <span class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Vocabulary</span>
        <span v-if="llmGenerated" class="rounded-full bg-[#ecfdf5] px-2 py-0.5 text-[9px] font-bold text-[#047857]">AI</span>
      </div>
      <span
        class="rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
        :style="{ borderColor: scoreColor + '55', color: scoreColor, background: scoreColor + '11' }"
      >
        {{ displayScore.toFixed(1) }}/9
      </span>
    </div>

    <div class="mb-3 flex flex-wrap gap-3 text-[10px] text-[var(--ink3)]">
      <span class="inline-flex items-center gap-1"><span class="inline-block h-2.5 w-2.5 rounded-sm bg-yellow-200"></span> Từ yếu / lặp</span>
      <span class="inline-flex items-center gap-1"><span class="inline-block h-2.5 w-2.5 rounded-sm bg-green-200"></span> Từ tốt / collocation</span>
    </div>

    <div v-if="loading" class="py-6 text-center text-sm text-[var(--ink3)]">Đang phân tích từ vựng (LLM)…</div>
    <div v-else-if="error" class="rounded-lg border border-[#fecaca] bg-[#fef2f2] px-3 py-2 text-xs text-[#b91c1c]">{{ error }}</div>

    <template v-else>
      <div v-if="transcript" class="mb-4 rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
        <div class="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--ink3)]">Transcript</div>
        <p class="transcript-html text-[13px] leading-relaxed text-[var(--ink)]" v-html="highlightedHtml"></p>
      </div>

      <div v-if="displayReplacements.length" class="space-y-3">
        <div
          v-for="(item, i) in displayReplacements"
          :key="i"
          class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3"
        >
          <div class="flex flex-wrap items-center gap-2 text-sm">
            <span class="rounded bg-[#fef9c3] px-2 py-0.5 font-medium text-[#854d0e]">{{ item.weak }}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            <span class="rounded-full border border-[#34d39955] bg-[#34d39911] px-2 py-0.5 text-[11px] font-semibold text-[#34d399]">
              {{ item.better }}
            </span>
          </div>
          <p v-if="item.reason" class="mt-1.5 text-[11px] text-[var(--ink3)]">{{ item.reason }}</p>
        </div>
      </div>

      <div v-else-if="displayStrong.length" class="text-sm text-[#34d399]">
        Strong vocabulary detected. See highlighted phrases above.
      </div>
      <div v-else class="text-sm text-[var(--ink3)]">No vocabulary suggestions from LLM for this transcript.</div>
    </template>
  </div>
</template>

<script setup>
import { computed, watch, toRef } from 'vue'
import { useVocabCheck } from '@/composables/useVocabCheck.js'

const props = defineProps({
  transcript: { type: String, default: '' },
  questionText: { type: String, default: '' },
  score: { type: Number, default: 0 },
  feedback: { type: Array, default: () => [] },
  evaluateResult: { type: Object, default: null },
})

const transcriptRef = toRef(props, 'transcript')
const questionRef = toRef(props, 'questionText')

const {
  loading,
  error,
  score: llmScore,
  replacements: llmReplacements,
  strongWords,
  highlightedHtml,
  llmGenerated,
  hydrateFromEvaluate,
  analyze,
} = useVocabCheck({ transcript: transcriptRef, questionText: questionRef, auto: false })

const displayScore = computed(() => (llmGenerated.value ? llmScore.value : props.score))

const displayReplacements = computed(() => {
  if (llmGenerated.value && llmReplacements.value.length) {
    return llmReplacements.value.map((r) => ({
      weak: r.weak,
      better: r.better,
      reason: r.reason,
    }))
  }
  return (props.feedback || []).map((f) => ({
    weak: f.word_used || f.weak || '',
    better: f.better_alternative || f.better || '',
    reason: f.reason || '',
  }))
})

const displayStrong = computed(() => strongWords.value || [])

const scoreColor = computed(() => {
  const s = displayScore.value
  if (s >= 7) return '#34d399'
  if (s >= 5) return '#f59e0b'
  return '#f43f5e'
})

watch(
  () => props.evaluateResult,
  (r) => {
    if (r) hydrateFromEvaluate(r)
  },
  { immediate: true, deep: true },
)

watch(
  () => [props.transcript, props.evaluateResult],
  ([t, r]) => {
    if (r?.llm_generated && (r.vocabulary_analysis || r.vocabulary)) return
    if (t && t.trim().length > 8) analyze(t, props.questionText)
  },
  { immediate: true },
)
</script>
