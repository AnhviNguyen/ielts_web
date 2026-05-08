<template>
  <div class="card p-5">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="text-[var(--ink2)]"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        <span class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Grammar</span>
      </div>
      <span
        class="rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
        :style="{ borderColor: scoreColor + '55', color: scoreColor, background: scoreColor + '11' }"
      >
        {{ score.toFixed(1) }}/9
      </span>
    </div>

    <div v-if="!errors || !errors.length" class="flex items-center gap-2 text-sm text-[#34d399]">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      No grammar errors found!
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="(err, i) in errors"
        :key="i"
        class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3"
      >
        <div class="flex items-start gap-2 text-sm">
          <svg class="mt-0.5 shrink-0 text-[#f43f5e]" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          <span class="text-[#f43f5e] line-through">{{ err.original }}</span>
        </div>
        <div class="mt-1 flex items-start gap-2 text-sm">
          <svg class="mt-0.5 shrink-0 text-[#34d399]" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          <span class="font-semibold text-[#34d399]">{{ err.correction }}</span>
        </div>
        <p class="mt-1.5 pl-5 text-[11px] text-[var(--ink3)]">{{ err.explanation }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  score:  { type: Number, default: 0 },
  errors: { type: Array,  default: () => [] },
})

const scoreColor = computed(() => {
  if (props.score >= 7) return '#34d399'
  if (props.score >= 5) return '#f59e0b'
  return '#f43f5e'
})
</script>
