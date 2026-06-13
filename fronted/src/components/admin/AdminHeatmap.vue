<template>
  <div class="w-full">
    <div class="flex w-full flex-col gap-2">
      <div class="flex w-full gap-2 pl-9 text-[10px] text-[var(--ink3)]">
        <span
          v-for="m in monthLabels"
          :key="m.key"
          class="shrink-0 text-center"
          :style="{ flex: `${m.cols} 1 0` }"
        >{{ m.label }}</span>
      </div>
      <div class="flex w-full gap-2">
        <div class="flex w-7 shrink-0 flex-col justify-around text-[10px] leading-none text-[var(--ink3)]">
          <span>T2</span><span></span><span>T4</span><span></span><span>T6</span><span></span><span>CN</span>
        </div>
        <div class="grid min-w-0 flex-1 grid-flow-col grid-rows-7 gap-1.5" style="grid-auto-columns: minmax(0, 1fr)">
          <div
            v-for="cell in cells"
            :key="cell.key"
            :title="cell.title"
            class="aspect-square w-full min-h-[14px] rounded-sm transition-transform hover:scale-110"
            :class="cell.empty ? 'opacity-0 pointer-events-none' : levelClass(cell.value)"
          />
        </div>
      </div>
      <div class="mt-1 flex items-center justify-end gap-1.5 text-[10px] text-[var(--ink3)]">
        <span>Ít</span>
        <span v-for="l in 4" :key="l" class="h-3.5 w-3.5 rounded-sm" :class="levelClass(l - 1)" />
        <span>Nhiều</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  days: { type: Array, default: () => [] },
})

const valueByDate = computed(() => {
  const map = {}
  for (const d of props.days) {
    const key = typeof d.date === 'string' ? d.date.slice(0, 10) : String(d.date)
    map[key] = Number(d.attempts ?? d.value ?? 0)
  }
  return map
})

const maxVal = computed(() => Math.max(1, ...Object.values(valueByDate.value)))

function levelClass(v) {
  if (!v && v !== 0) return ''
  const ratio = v / maxVal.value
  if (ratio <= 0) return 'bg-[var(--bg2)]'
  if (ratio < 0.25) return 'bg-emerald-100 dark:bg-emerald-900/40'
  if (ratio < 0.5) return 'bg-emerald-300 dark:bg-emerald-700/70'
  if (ratio < 0.75) return 'bg-emerald-500'
  return 'bg-emerald-700'
}

const cells = computed(() => {
  const dates = props.days.length
    ? props.days.map((d) => {
        const s = typeof d.date === 'string' ? d.date.slice(0, 10) : String(d.date)
        return new Date(s + 'T12:00:00')
      })
    : []

  const end = dates.length ? new Date(Math.max(...dates)) : new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - 7 * 12 + 1)
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7))

  const out = []
  const cur = new Date(start)
  const rangeEnd = new Date(end)
  while (cur <= rangeEnd || out.length % 7 !== 0) {
    const key = cur.toISOString().slice(0, 10)
    const value = valueByDate.value[key] ?? 0
    const inRange = cur >= start && cur <= rangeEnd
    out.push({
      key,
      empty: !inRange,
      value: inRange ? value : null,
      title: inRange ? `${key}: ${value} bài làm` : '',
    })
    cur.setDate(cur.getDate() + 1)
    if (out.length > 140) break
  }
  return out
})

const monthLabels = computed(() => {
  const labels = []
  let lastMonth = -1
  let cols = 0
  for (let w = 0; w < cells.value.length; w += 7) {
    const d = cells.value[w]
    if (!d || d.empty) continue
    const dt = new Date(d.key + 'T12:00:00')
    const m = dt.getMonth()
    if (m !== lastMonth) {
      if (cols) labels.push({ key: lastMonth, cols, label: monthName(lastMonth) })
      lastMonth = m
      cols = 1
    } else {
      cols += 1
    }
  }
  if (cols) labels.push({ key: lastMonth, cols, label: monthName(lastMonth) })
  return labels
})

function monthName(m) {
  return ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'][m] || ''
}
</script>
