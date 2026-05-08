<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center gap-1">
    <!-- Prev -->
    <button
      class="flex h-8 w-8 items-center justify-center rounded border border-[var(--border)] bg-white text-[var(--ink3)] transition hover:bg-[var(--bg2)] disabled:pointer-events-none disabled:opacity-30"
      :disabled="modelValue === 1"
      @click="$emit('update:modelValue', modelValue - 1)"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
    </button>

    <!-- Page numbers -->
    <template v-for="p in pages" :key="p">
      <span v-if="p === '...'" class="px-1 text-[12px] text-[var(--ink3)]">…</span>
      <button
        v-else
        class="flex h-8 w-8 items-center justify-center rounded border text-[12px] font-medium transition"
        :class="p === modelValue
          ? 'border-[var(--ink)] bg-[var(--ink)] text-white'
          : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:bg-[var(--bg2)]'"
        @click="$emit('update:modelValue', p)"
      >{{ p }}</button>
    </template>

    <!-- Next -->
    <button
      class="flex h-8 w-8 items-center justify-center rounded border border-[var(--border)] bg-white text-[var(--ink3)] transition hover:bg-[var(--bg2)] disabled:pointer-events-none disabled:opacity-30"
      :disabled="modelValue === totalPages"
      @click="$emit('update:modelValue', modelValue + 1)"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 1 },
  total:      { type: Number, default: 0 },
  pageSize:   { type: Number, default: 9 },
})
defineEmits(['update:modelValue'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const pages = computed(() => {
  const t = totalPages.value
  const c = props.modelValue
  if (t <= 7) return Array.from({ length: t }, (_, i) => i + 1)
  const res = []
  res.push(1)
  if (c > 3) res.push('...')
  for (let p = Math.max(2, c - 1); p <= Math.min(t - 1, c + 1); p++) res.push(p)
  if (c < t - 2) res.push('...')
  res.push(t)
  return res
})
</script>
