<template>
  <div class="sticky top-0 z-20 border-b border-[var(--border2)] bg-[var(--bg)]/90 backdrop-blur" data-tour="quiz-header">
    <div class="exam-container flex items-center justify-between gap-3 py-3 sm:py-4">
      <div class="flex min-w-0 items-center gap-3">
        <button
          v-if="showBack"
          type="button"
          class="flex shrink-0 items-center gap-1 rounded-lg border border-[var(--border)] px-2.5 py-1.5 text-[12px] font-semibold text-[var(--ink2)] transition hover:border-[var(--spotify-green)] hover:text-[var(--ink)]"
          @click="$emit('back')"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          Quay lại
        </button>
        <div class="min-w-0">
          <div class="text-sm font-semibold truncate">{{ title }}</div>
          <div class="text-xs text-[var(--ink2)] truncate">{{ subtitle }}</div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div class="rounded-xl border border-[var(--border2)] bg-[var(--surface)] px-3 py-2">
          <div class="text-[11px] text-[var(--ink2)]">Time left</div>
          <div class="font-mono text-sm font-semibold">{{ mmss }}</div>
        </div>
        <button class="btn btn-primary" @click="$emit('submit')" :disabled="disabled">
          Submit
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  remainingSeconds: { type: Number, default: 0 },
  disabled: { type: Boolean, default: false },
  showBack: { type: Boolean, default: false },
})

defineEmits(['submit', 'back'])

const mmss = computed(() => {
  const s = Math.max(0, props.remainingSeconds || 0)
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const ss = Math.floor(s % 60).toString().padStart(2, '0')
  return `${m}:${ss}`
})
</script>

