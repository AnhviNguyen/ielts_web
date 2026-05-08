<template>
  <div class="sticky top-0 z-20 border-b border-[var(--border2)] bg-[var(--bg)]/90 backdrop-blur">
    <div class="container flex items-center justify-between gap-3 py-3">
      <div class="min-w-0">
        <div class="text-sm font-semibold truncate">{{ title }}</div>
        <div class="text-xs text-[var(--ink2)] truncate">{{ subtitle }}</div>
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
})

defineEmits(['submit'])

const mmss = computed(() => {
  const s = Math.max(0, props.remainingSeconds || 0)
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const ss = Math.floor(s % 60).toString().padStart(2, '0')
  return `${m}:${ss}`
})
</script>

