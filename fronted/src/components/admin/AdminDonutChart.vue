<template>
  <div class="flex flex-col items-center gap-4 sm:flex-row sm:items-center sm:justify-center sm:gap-8">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="shrink-0">
      <circle :cx="cx" :cy="cy" :r="r" fill="none" stroke="var(--bg2)" :stroke-width="stroke" />
      <path
        v-for="(seg, i) in segments"
        :key="i"
        :d="seg.path"
        :fill="seg.color"
        class="transition-opacity hover:opacity-90"
      />
      <text :x="cx" :y="cy - 4" text-anchor="middle" class="fill-[var(--ink)]" style="font-size:22px;font-weight:700">{{ total }}</text>
      <text :x="cx" :y="cy + 14" text-anchor="middle" class="fill-[var(--ink3)]" style="font-size:10px">tổng</text>
    </svg>
    <div class="grid w-full max-w-[200px] gap-2">
      <div v-for="(item, i) in items" :key="i" class="flex items-center justify-between gap-2 text-xs">
        <div class="flex min-w-0 items-center gap-2">
          <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ backgroundColor: colors[i % colors.length] }" />
          <span class="truncate font-medium text-[var(--ink2)]">{{ item.label }}</span>
        </div>
        <span class="shrink-0 font-bold tabular-nums text-[var(--ink)]">{{ item.value }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  size: { type: Number, default: 160 },
  colors: {
    type: Array,
    default: () => ['#059669', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5', '#9ca3af'],
  },
})

const stroke = 28
const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const r = computed(() => (props.size - stroke) / 2)
const total = computed(() => props.items.reduce((s, i) => s + (Number(i.value) || 0), 0))

const segments = computed(() => {
  const sum = total.value || 1
  let angle = -Math.PI / 2
  return props.items.map((item, i) => {
    const frac = (Number(item.value) || 0) / sum
    const sweep = frac * Math.PI * 2
    const x1 = cx.value + r.value * Math.cos(angle)
    const y1 = cy.value + r.value * Math.sin(angle)
    angle += sweep
    const x2 = cx.value + r.value * Math.cos(angle)
    const y2 = cy.value + r.value * Math.sin(angle)
    const large = sweep > Math.PI ? 1 : 0
    const path = frac <= 0
      ? ''
      : frac >= 0.999
        ? `M ${cx.value} ${cy.value - r.value} A ${r.value} ${r.value} 0 1 1 ${cx.value - 0.01} ${cy.value - r.value} Z`
        : `M ${cx.value} ${cy.value} L ${x1} ${y1} A ${r.value} ${r.value} 0 ${large} 1 ${x2} ${y2} Z`
    return { path, color: props.colors[i % props.colors.length] }
  }).filter((s) => s.path)
})
</script>
