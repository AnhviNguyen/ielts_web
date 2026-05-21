<template>
  <div
    class="cursor-pointer rounded-[var(--r)] border p-[18px] transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow)]"
    :class="overall
      ? 'border-transparent bg-[var(--ink)] text-white'
      : 'border-[var(--border)] bg-[var(--surface)]'"
  >
    <div
      class="text-[11px] font-semibold uppercase tracking-wider"
      :class="overall ? 'text-white/60' : 'text-[var(--ink3)] opacity-55'"
    >{{ label }}</div>
    <div
      class="font-display my-1.5 text-[32px] font-bold leading-none"
      :style="{ color: overall ? 'var(--green-l)' : colorHex }"
    >{{ score ?? '—' }}</div>
    <div :class="overall ? 'text-xs text-white/45' : 'text-xs text-[var(--ink3)]'">Mục tiêu: {{ target }}</div>
    <div v-if="overall" class="mt-2.5 h-1.5 overflow-hidden rounded-full bg-white/15">
      <div
        class="h-full rounded-full bg-[var(--green-l)] transition-[width] duration-500 ease-out"
        :style="{ width: progressPct + '%' }"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:    { type: String, required: true },
  score:    { type: Number, default: null },
  target:   { type: Number, required: true },
  colorHex: { type: String, default: 'var(--ink)' },
  overall:  { type: Boolean, default: false },
})

const progressPct = computed(() =>
  props.target > 0 ? Math.min(100, (props.score / props.target) * 100) : 0
)
</script>
