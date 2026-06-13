<template>
  <div class="w-full">
    <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" class="overflow-visible">
      <!-- Grid -->
      <g v-for="tick in yTicks" :key="tick">
        <line
          :x1="padL"
          :y1="yScale(tick)"
          :x2="width - padR"
          :y2="yScale(tick)"
          stroke="var(--border)"
          stroke-width="1"
          stroke-dasharray="3 3"
        />
        <text
          :x="padL - 8"
          :y="yScale(tick) + 4"
          text-anchor="end"
          class="fill-[var(--ink3)] text-[10px]"
        >{{ tick.toFixed(1) }}</text>
      </g>

      <!-- Target line -->
      <line
        v-if="target"
        :x1="padL"
        :y1="yScale(target)"
        :x2="width - padR"
        :y2="yScale(target)"
        stroke="var(--spotify-green)"
        stroke-width="1.5"
        stroke-dasharray="6 4"
      />

      <!-- Confidence band (forecast) -->
      <path
        v-if="bandPath"
        :d="bandPath"
        fill="rgba(52,211,153,0.12)"
        stroke="none"
      />

      <!-- Forecast line -->
      <polyline
        v-if="forecastLine"
        :points="forecastLine"
        fill="none"
        stroke="var(--spotify-green)"
        stroke-width="2"
        stroke-dasharray="5 3"
      />

      <!-- History line -->
      <polyline
        v-if="historyLine"
        :points="historyLine"
        fill="none"
        stroke="#111"
        stroke-width="2.5"
      />

      <!-- Observed dots -->
      <circle
        v-for="(pt, i) in historyPoints"
        :key="`h-${i}`"
        :cx="xScale(pt.idx)"
        :cy="yScale(pt.y ?? pt.yhat)"
        r="3.5"
        fill="#111"
      />

      <!-- X labels -->
      <text
        v-for="lbl in xLabels"
        :key="lbl.idx"
        :x="xScale(lbl.idx)"
        :y="height - 6"
        text-anchor="middle"
        class="fill-[var(--ink3)] text-[9px]"
      >{{ lbl.label }}</text>
    </svg>

    <div class="mt-2 flex flex-wrap items-center gap-4 text-[11px] text-[var(--ink3)]">
      <span class="flex items-center gap-1.5"><span class="inline-block h-0.5 w-5 bg-[#111]"></span> Thực tế</span>
      <span class="flex items-center gap-1.5"><span class="inline-block h-0.5 w-5 border-t-2 border-dashed border-emerald-400"></span> Dự báo</span>
      <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-5 rounded bg-emerald-100"></span> Khoảng tin cậy 90%</span>
      <span v-if="target" class="flex items-center gap-1.5"><span class="inline-block h-0.5 w-5 border-t border-dashed border-emerald-500"></span> Mục tiêu {{ target }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  history: { type: Array, default: () => [] },
  forecast: { type: Array, default: () => [] },
  target: { type: Number, default: null },
  width: { type: Number, default: 560 },
  height: { type: Number, default: 220 },
})

const padL = 36
const padR = 12
const padT = 12
const padB = 28

const allPoints = computed(() => {
  const hist = (props.history || []).map((p, idx) => ({
    ...p,
    idx,
    kind: 'history',
  }))
  const base = hist.length
  const fc = (props.forecast || []).map((p, i) => ({
    ...p,
    idx: base + i,
    kind: 'forecast',
  }))
  return [...hist, ...fc]
})

const yMin = computed(() => {
  const vals = allPoints.value.flatMap(p => [p.y, p.yhat, p.yhat_lower, p.yhat_upper].filter(v => v != null))
  const lo = vals.length ? Math.min(...vals) : 4
  return Math.max(0, Math.floor((lo - 0.3) * 2) / 2)
})

const yMax = computed(() => {
  const vals = allPoints.value.flatMap(p => [p.y, p.yhat, p.yhat_lower, p.yhat_upper].filter(v => v != null))
  const hi = vals.length ? Math.max(...vals) : 8
  return Math.min(9, Math.ceil((hi + 0.3) * 2) / 2)
})

const yTicks = computed(() => {
  const ticks = []
  for (let v = yMin.value; v <= yMax.value + 0.01; v += 0.5) ticks.push(v)
  return ticks
})

const plotW = computed(() => props.width - padL - padR)
const plotH = computed(() => props.height - padT - padB)

function yScale(v) {
  const range = yMax.value - yMin.value || 1
  return padT + plotH.value - ((v - yMin.value) / range) * plotH.value
}

function xScale(idx) {
  const n = Math.max(allPoints.value.length - 1, 1)
  return padL + (idx / n) * plotW.value
}

const historyPoints = computed(() =>
  allPoints.value.filter(p => p.kind === 'history')
)

const historyLine = computed(() =>
  historyPoints.value
    .map(p => `${xScale(p.idx)},${yScale(p.y ?? p.yhat)}`)
    .join(' ')
)

const forecastLine = computed(() => {
  const lastHist = historyPoints.value.at(-1)
  const fc = allPoints.value.filter(p => p.kind === 'forecast')
  if (!fc.length) return ''
  const pts = []
  if (lastHist) pts.push(`${xScale(lastHist.idx)},${yScale(lastHist.y ?? lastHist.yhat)}`)
  fc.forEach(p => pts.push(`${xScale(p.idx)},${yScale(p.yhat)}`))
  return pts.join(' ')
})

const bandPath = computed(() => {
  const fc = allPoints.value.filter(p => p.kind === 'forecast')
  const lastHist = historyPoints.value.at(-1)
  if (!fc.length) return ''
  const upper = []
  const lower = []
  if (lastHist) {
    upper.push([xScale(lastHist.idx), yScale(lastHist.y ?? lastHist.yhat)])
    lower.push([xScale(lastHist.idx), yScale(lastHist.y ?? lastHist.yhat)])
  }
  fc.forEach(p => {
    upper.push([xScale(p.idx), yScale(p.yhat_upper)])
    lower.unshift([xScale(p.idx), yScale(p.yhat_lower)])
  })
  const path = [...upper, ...lower]
  if (!path.length) return ''
  return `M ${path.map(([x, y]) => `${x},${y}`).join(' L ')} Z`
})

const xLabels = computed(() => {
  const pts = allPoints.value
  if (!pts.length) return []
  const picks = new Set([0, Math.floor(pts.length / 2), pts.length - 1])
  return [...picks].map(idx => ({
    idx,
    label: formatDate(pts[idx]?.ds),
  }))
})

function formatDate(ds) {
  if (!ds) return ''
  const d = new Date(ds)
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}
</script>
