<template>
  <div class="card p-5">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="text-[var(--ink2)]"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        <span class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Vocabulary</span>
      </div>
      <span
        class="rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
        :style="{ borderColor: scoreColor + '55', color: scoreColor, background: scoreColor + '11' }"
      >
        {{ score.toFixed(1) }}/9
      </span>
    </div>

    <div v-if="!feedback || !feedback.length" class="flex items-center gap-2 text-sm text-[#34d399]">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      Great vocabulary usage!
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="(item, i) in feedback"
        :key="i"
        class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3"
      >
        <div class="flex flex-wrap items-center gap-2 text-sm">
          <span class="text-[var(--ink2)]">{{ item.word_used }}</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
          <span class="rounded-full border border-[#34d39955] bg-[#34d39911] px-2 py-0.5 text-[11px] font-semibold text-[#34d399]">
            {{ item.better_alternative }}
          </span>
        </div>
        <p class="mt-1.5 text-[11px] text-[var(--ink3)]">{{ item.reason }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  score:    { type: Number, default: 0 },
  feedback: { type: Array,  default: () => [] },
})

const scoreColor = computed(() => {
  if (props.score >= 7) return '#34d399'
  if (props.score >= 5) return '#f59e0b'
  return '#f43f5e'
})
</script>
