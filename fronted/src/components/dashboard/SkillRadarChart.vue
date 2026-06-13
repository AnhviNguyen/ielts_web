<template>
  <div class="flex flex-col items-center gap-4">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="overflow-visible">
      <!-- Background grid rings -->
      <g v-for="ring in rings" :key="ring">
        <polygon
          :points="polygonPoints(ring / maxVal)"
          fill="none"
          stroke="var(--border)"
          stroke-width="1"
        />
      </g>

      <!-- Axis lines -->
      <line
        v-for="(axis, i) in axes"
        :key="i"
        :x1="cx"
        :y1="cy"
        :x2="outerPoint(i).x"
        :y2="outerPoint(i).y"
        stroke="var(--border)"
        stroke-width="1"
      />

      <!-- Min standard polygon (band 2) -->
      <polygon
        :points="dataPolygon(minData)"
        fill="rgba(209,213,219,0.15)"
        stroke="#d1d5db"
        stroke-width="1.5"
        stroke-dasharray="4 3"
      />

      <!-- Target polygon -->
      <polygon
        :points="dataPolygon(targetData)"
        fill="rgba(52,211,153,0.08)"
        stroke="var(--spotify-green)"
        stroke-width="1.5"
        stroke-dasharray="5 3"
      />

      <!-- Actual data polygon -->
      <polygon
        :points="dataPolygon(actualData)"
        fill="rgba(5,150,105,0.15)"
        stroke="var(--spotify-green-dark)"
        stroke-width="2"
      />

      <!-- Data point dots -->
      <circle
        v-for="(pt, i) in actualPoints"
        :key="`dot-${i}`"
        :cx="pt.x"
        :cy="pt.y"
        r="4"
        fill="var(--spotify-green-dark)"
        stroke="white"
        stroke-width="1.5"
      />

      <!-- Axis labels -->
      <text
        v-for="(axis, i) in axes"
        :key="`lbl-${i}`"
        :x="labelPoint(i).x"
        :y="labelPoint(i).y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="text-[11px] font-semibold"
        :style="{ fontSize: '11px', fontWeight: '600', fill: 'var(--ink2)' }"
      >
        {{ axis.label }}
      </text>

      <!-- Score labels on dots -->
      <text
        v-for="(pt, i) in actualPoints"
        :key="`score-${i}`"
        :x="pt.x + scoreLabelOffset(i).x"
        :y="pt.y + scoreLabelOffset(i).y"
        text-anchor="middle"
        dominant-baseline="middle"
        :style="{ fontSize: '10px', fontWeight: '700', fill: 'var(--spotify-green-dark)' }"
      >
        {{ formatScore(actualData[i]) }}
      </text>

      <!-- Ring value labels (rightmost axis) -->
      <text
        v-for="ring in rings"
        :key="`rv-${ring}`"
        :x="cx + radius * (ring / maxVal) + 4"
        :y="cy"
        dominant-baseline="middle"
        :style="{ fontSize: '9px', fill: 'var(--ink3)' }"
      >
        {{ ring }}
      </text>
    </svg>

    <!-- Legend -->
    <div class="flex flex-wrap items-center justify-center gap-4 text-[11px]">
      <div class="flex items-center gap-1.5">
        <span class="inline-block h-2.5 w-5 rounded-sm border border-dashed border-[#d1d5db] bg-[#d1d5db]/20"></span>
        <span class="text-[var(--ink3)]">Min (2.0)</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="inline-block h-2.5 w-5 rounded-sm border border-dashed border-[var(--spotify-green)] bg-[var(--green-bg)]"></span>
        <span class="text-[var(--ink3)]">Target ({{ targetVal }})</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="inline-block h-2.5 w-5 rounded-sm border border-[var(--spotify-green-dark)] bg-[var(--green-bg)]"></span>
        <span class="text-[var(--ink3)]">Actual</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** { reading, listening, writing, speaking } — values 0–9 */
  scores: {
    type: Object,
    default: () => ({ reading: 0, listening: 0, writing: 0, speaking: 0 }),
  },
  /** User's target band score */
  target: { type: Number, default: 6.5 },
  /** SVG canvas size in px */
  size: { type: Number, default: 280 },
})

const maxVal = 9
const rings  = [2, 4, 6, 8, 9]

const axes = [
  { key: 'listening', label: 'Listening' },
  { key: 'reading',   label: 'Reading'   },
  { key: 'writing',   label: 'Writing'   },
  { key: 'speaking',  label: 'Speaking'  },
]

const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const radius = computed(() => props.size * 0.36)

/** Angle for axis i (start at top, clockwise) */
function axisAngle(i) {
  return (Math.PI * 2 * i) / axes.length - Math.PI / 2
}

/** Point on the outer edge for axis i */
function outerPoint(i) {
  const angle = axisAngle(i)
  return {
    x: cx.value + radius.value * Math.cos(angle),
    y: cy.value + radius.value * Math.sin(angle),
  }
}

/** Label position (slightly beyond outer edge) */
function labelPoint(i) {
  const angle = axisAngle(i)
  const r = radius.value + 22
  return {
    x: cx.value + r * Math.cos(angle),
    y: cy.value + r * Math.sin(angle),
  }
}

/** Generate polygon points string for a normalised fraction (0–1 per axis) */
function polygonPoints(fraction) {
  return axes
    .map((_, i) => {
      const angle = axisAngle(i)
      const r = radius.value * fraction
      return `${cx.value + r * Math.cos(angle)},${cy.value + r * Math.sin(angle)}`
    })
    .join(' ')
}

/** Generate polygon points from raw data array (values 0–9) */
function dataPolygon(data) {
  return axes
    .map((_, i) => {
      const angle = axisAngle(i)
      const r = radius.value * (Math.min(data[i], maxVal) / maxVal)
      return `${cx.value + r * Math.cos(angle)},${cy.value + r * Math.sin(angle)}`
    })
    .join(' ')
}

const actualData = computed(() =>
  axes.map(a => Number(props.scores[a.key] || 0))
)
const targetVal  = computed(() => Number(props.target || 6.5))
const targetData = computed(() => axes.map(() => targetVal.value))
const minData    = [2, 2, 2, 2]

const actualPoints = computed(() =>
  axes.map((_, i) => {
    const angle = axisAngle(i)
    const r = radius.value * (Math.min(actualData.value[i], maxVal) / maxVal)
    return {
      x: cx.value + r * Math.cos(angle),
      y: cy.value + r * Math.sin(angle),
    }
  })
)

/** Small offset so score label doesn't overlap the dot */
function scoreLabelOffset(i) {
  const angle = axisAngle(i)
  return { x: Math.cos(angle) * 14, y: Math.sin(angle) * 14 }
}

function formatScore(val) {
  if (!val) return '—'
  return Number(val).toFixed(1)
}
</script>
