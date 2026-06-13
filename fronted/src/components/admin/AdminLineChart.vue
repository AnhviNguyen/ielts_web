<template>
  <svg :viewBox="`0 0 ${width} ${height}`" class="h-auto w-full" preserveAspectRatio="xMidYMid meet">
    <g v-for="tick in yTicks" :key="`y-${tick}`">
      <line :x1="padL" :y1="yScale(tick)" :x2="width - padR" :y2="yScale(tick)" stroke="var(--border)" stroke-dasharray="3 3" />
      <text :x="padL - 6" :y="yScale(tick) + 4" text-anchor="end" class="fill-[var(--ink3)]" style="font-size:9px">{{ tick }}</text>
    </g>
    <template v-for="(series, si) in normalizedSeries" :key="si">
      <path v-if="series.areaPath" :d="series.areaPath" :fill="series.color" fill-opacity="0.12" />
      <polyline :points="series.line" fill="none" :stroke="series.color" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
      <circle
        v-for="(pt, i) in series.points"
        :key="`${si}-${i}`"
        :cx="xScale(i)"
        :cy="yScale(pt)"
        r="3.5"
        :fill="series.color"
        stroke="white"
        stroke-width="1.5"
      />
    </template>
    <text
      v-for="(lbl, i) in xLabels"
      :key="`x-${i}`"
      :x="xScale(i)"
      :y="height - 4"
      text-anchor="middle"
      class="fill-[var(--ink3)]"
      style="font-size:9px"
    >{{ lbl }}</text>
    <g v-if="legend.length" :transform="`translate(${padL}, ${padT - 4})`">
      <g v-for="(item, i) in legend" :key="item.label" :transform="`translate(${i * 110}, 0)`">
        <line x1="0" y1="0" x2="14" y2="0" :stroke="item.color" stroke-width="2.5" />
        <text x="18" y="4" class="fill-[var(--ink2)]" style="font-size:10px;font-weight:600">{{ item.label }}</text>
      </g>
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  height: { type: Number, default: 200 },
})

const width = 520
const padL = 36
const padR = 12
const padT = 22
const padB = 28
const innerW = width - padL - padR
const innerH = props.height - padT - padB

const allValues = computed(() =>
  props.series.flatMap((s) => s.data.map((v) => Number(v) || 0))
)
const maxY = computed(() => Math.max(1, ...allValues.value))
const yTicks = computed(() => {
  const m = maxY.value
  const step = m <= 5 ? 1 : m <= 20 ? 5 : Math.ceil(m / 4 / 5) * 5
  const ticks = []
  for (let v = 0; v <= m; v += step) ticks.push(v)
  if (ticks[ticks.length - 1] < m) ticks.push(m)
  return ticks.slice(0, 5)
})

function xScale(i) {
  const n = Math.max(1, props.labels.length - 1)
  return padL + (i / n) * innerW
}
function yScale(v) {
  return padT + innerH - (Number(v) / maxY.value) * innerH
}

const xLabels = computed(() =>
  props.labels.map((d) => {
    const s = String(d)
    return s.length > 6 ? s.slice(5) : s
  })
)

const legend = computed(() =>
  props.series.map((s) => ({ label: s.label, color: s.color }))
)

const normalizedSeries = computed(() =>
  props.series.map((s) => {
    const pts = s.data.map((v) => Number(v) || 0)
    const line = pts.map((v, i) => `${xScale(i)},${yScale(v)}`).join(' ')
    const baseY = padT + innerH
    const areaPath = pts.length
      ? `M ${xScale(0)},${baseY} ` +
        pts.map((v, i) => `L ${xScale(i)},${yScale(v)}`).join(' ') +
        ` L ${xScale(pts.length - 1)},${baseY} Z`
      : ''
    return { ...s, points: pts, line, areaPath }
  })
)
</script>
