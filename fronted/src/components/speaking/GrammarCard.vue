<template>
  <div class="card p-5">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="text-[var(--ink2)]"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        <span class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Grammar</span>
        <span v-if="llmGenerated" class="rounded-full bg-[#ecfdf5] px-2 py-0.5 text-[9px] font-bold text-[#047857]">AI</span>
      </div>
      <span
        class="rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
        :style="{ borderColor: scoreColor + '55', color: scoreColor, background: scoreColor + '11' }"
      >
        {{ displayScore.toFixed(1) }}/9
      </span>
    </div>

    <div v-if="loading" class="py-6 text-center text-sm text-[var(--ink3)]">Đang phân tích ngữ pháp (LLM)…</div>
    <div v-else-if="error" class="rounded-lg border border-[#fecaca] bg-[#fef2f2] px-3 py-2 text-xs text-[#b91c1c]">{{ error }}</div>

    <template v-else>
      <div v-if="transcript" class="mb-4 rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
        <div class="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--ink3)]">Transcript (lỗi được tô đỏ nhạt)</div>
        <p class="transcript-html text-[13px] leading-relaxed text-[var(--ink)]" v-html="highlightedHtml"></p>
      </div>

      <div v-if="!displayErrors.length" class="flex items-center gap-2 text-sm text-[#34d399]">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        No grammar errors found in transcript.
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(err, i) in displayErrors"
          :key="i"
          class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3"
        >
          <div class="mb-1 flex flex-wrap items-center gap-2">
            <span class="rounded-full bg-[#fee2e2] px-2 py-0.5 text-[10px] font-bold uppercase text-[#b91c1c]">
              {{ err.error_type || 'grammar' }}
            </span>
            <span class="text-[12px] text-[#f43f5e] line-through">{{ err.text || err.original }}</span>
          </div>
          <div class="mt-2 flex items-start gap-2 text-sm">
            <svg class="mt-0.5 shrink-0 text-[#34d399]" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span class="font-semibold text-[#34d399]">{{ err.correction }}</span>
          </div>
          <p v-if="err.explanation" class="mt-1.5 text-[11px] text-[var(--ink3)]">{{ err.explanation }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, watch, toRef } from 'vue'
import { useGrammarCheck } from '@/composables/useGrammarCheck.js'

const props = defineProps({
  transcript: { type: String, default: '' },
  questionText: { type: String, default: '' },
  score: { type: Number, default: 0 },
  errors: { type: Array, default: () => [] },
  evaluateResult: { type: Object, default: null },
})

const transcriptRef = toRef(props, 'transcript')
const questionRef = toRef(props, 'questionText')

const {
  loading,
  error,
  score: llmScore,
  errors: llmErrors,
  highlightedHtml,
  llmGenerated,
  hydrateFromEvaluate,
  analyze,
} = useGrammarCheck({ transcript: transcriptRef, questionText: questionRef, auto: false })

const displayScore = computed(() => (llmGenerated.value ? llmScore.value : props.score))
const displayErrors = computed(() => {
  if (llmGenerated.value && llmErrors.value.length) return llmErrors.value
  return (props.errors || []).map((e) => ({
    text: e.text || e.original || '',
    error_type: e.error_type || e.type || 'grammar',
    correction: e.correction || '',
    explanation: e.explanation || '',
  }))
})

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
    if (r?.llm_generated && (r.grammar_analysis || r.grammar)) return
    if (t && t.trim().length > 8) analyze(t, props.questionText)
  },
  { immediate: true },
)
</script>

<style scoped>
:deep(.hl-grammar-error) {
  background: #fecaca;
  color: #991b1b;
  border-radius: 3px;
  padding: 0 2px;
}
.transcript-html :deep(mark) {
  font-weight: 600;
}
</style>
