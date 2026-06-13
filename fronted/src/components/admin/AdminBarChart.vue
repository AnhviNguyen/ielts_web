<template>
  <div class="space-y-3">
    <div v-for="(item, i) in items" :key="i" class="space-y-1">
      <div class="flex items-center justify-between gap-2 text-xs">
        <span class="truncate font-semibold text-[var(--ink)]">{{ item.label }}</span>
        <span class="shrink-0 tabular-nums text-[var(--ink2)]">
          {{ item.value }}{{ suffix }}
          <span v-if="item.extra" class="text-[var(--ink3)]"> · {{ item.extra }}</span>
        </span>
      </div>
      <div class="h-2.5 overflow-hidden rounded-full bg-[var(--bg2)]">
        <div
          class="h-full rounded-full transition-all duration-500"
          :style="{ width: `${barWidth(item.value)}%`, backgroundColor: item.color || color }"
        />
      </div>
    </div>
    <div v-if="!items.length" class="py-6 text-center text-sm text-[var(--ink3)]">{{ emptyText }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  color: { type: String, default: '#059669' },
  suffix: { type: String, default: '' },
  emptyText: { type: String, default: 'Chưa có dữ liệu.' },
})

const maxVal = computed(() => Math.max(1, ...props.items.map((i) => Number(i.value) || 0)))

function barWidth(v) {
  return Math.max(4, Math.round(((Number(v) || 0) / maxVal.value) * 100))
}
</script>
