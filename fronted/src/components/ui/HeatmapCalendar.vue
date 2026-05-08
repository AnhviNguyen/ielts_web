<template>
  <div class="heatmap-calendar">
    <div class="heatmap-header">
      <div>
        <div class="card-title font-display">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          Study days
        </div>
        <div class="card-sub">Đánh dấu ngày đã học</div>
      </div>
      <div class="legend">
        <span class="legend-dot"></span> Có nộp bài
      </div>
    </div>

    <div class="month-label">{{ monthLabel }}</div>

    <!-- Day headers Mon–Sun -->
    <div class="day-headers" :class="{ compact: props.compact }">
      <div v-for="d in ['T2','T3','T4','T5','T6','T7','CN']" :key="d" class="day-header">{{ d }}</div>
    </div>

    <!-- Calendar grid -->
    <div class="heatmap-grid" :class="{ compact: props.compact }">
      <div
        v-for="(cell, idx) in calendarData"
        :key="idx"
        class="heatmap-day"
        :class="{
          'empty':  cell.empty,
          'today':  cell.isToday,
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

<style scoped>
.heatmap-calendar { width: 100%; }

.heatmap-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-sub {
  font-size: 12px;
  color: var(--ink3);
  margin-top: 3px;
}

.legend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ink3);
}

.legend-dot {
  width: 10px; height: 10px;
  border-radius: 2px;
  background: var(--green-l);
  display: inline-block;
}

.month-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink3);
  margin-bottom: 8px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.day-headers {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 6px;
}

.day-header {
  font-size: 10px;
  text-align: center;
  color: var(--ink3);
  padding: 3px;
  font-weight: 600;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day-headers.compact .day-header {
  font-size: 9px;
  padding: 1px;
}

.heatmap-grid.compact {
  gap: 3px;
}

.heatmap-grid.compact .heatmap-day {
  min-height: 22px;
  font-size: 10px;
}
</style>
