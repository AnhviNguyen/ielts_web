<template>
  <div class="w-full">
    <div class="mb-3.5 flex items-start justify-between">
      <div>
        <div class="font-display flex items-center gap-2 text-[15px] font-semibold text-[var(--ink)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          Study days
        </div>
        <div class="mt-0.5 text-xs text-[var(--ink3)]">Đánh dấu ngày đã học</div>
      </div>
      <div class="flex items-center gap-1.5 text-xs text-[var(--ink3)]">
        <span class="inline-block h-2.5 w-2.5 rounded-sm bg-[var(--green-l)]"></span> Có nộp bài
      </div>
    </div>

    <div class="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--ink3)]">{{ monthLabel }}</div>

    <div
      class="mb-1.5 grid grid-cols-7 gap-1"
      :class="compact ? '[&_.day-hdr]:text-[9px] [&_.day-hdr]:p-px' : ''"
    >
      <div v-for="d in ['T2','T3','T4','T5','T6','T7','CN']" :key="d" class="day-hdr py-0.5 text-center text-[10px] font-semibold text-[var(--ink3)]">{{ d }}</div>
    </div>

    <div class="grid grid-cols-7 gap-1" :class="compact ? 'gap-[3px] [&_.heatmap-day]:min-h-[22px] [&_.heatmap-day]:text-[10px]' : ''">
      <div
        v-for="(cell, idx) in calendarData"
        :key="idx"
        class="heatmap-day"
        :class="{
          empty:  cell.empty,
          today:  cell.isToday,
          'done-1': !cell.isToday && cell.level === 1,
          'done-2': !cell.isToday && cell.level === 2,
          'done-3': !cell.isToday && cell.level === 3,
        }"
        :title="cell.day ? `${cell.day}: ${cell.count ?? 0} bài` : ''"
      >
        <span v-if="!cell.empty">{{ cell.day }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useHeatmap } from '@/composables/useHeatmap.js'

const props = defineProps({
  activityMap: { type: Object, default: () => ({}) },
  compact: { type: Boolean, default: false },
})

const { calendarData, monthLabel } = useHeatmap(props.activityMap)
</script>
