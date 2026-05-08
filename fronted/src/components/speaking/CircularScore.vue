<template>
  <div class="flex flex-col items-center gap-2">
    <div class="relative" :style="{ width: size + 'px', height: size + 'px' }">
      <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="-rotate-90">
        <circle :cx="cx" :cy="cy" :r="r" fill="none" stroke="#e5e7eb" :stroke-width="strokeW" />
        <circle
          :cx="cx" :cy="cy" :r="r"
          fill="none"
          :stroke="trackColor"
          :stroke-width="strokeW"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          style="transition: stroke-dashoffset 1s ease"
        />
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="font-bold leading-none text-[var(--ink)]" :style="{ fontSize: size * 0.22 + 'px' }">
          {{ score.toFixed(1) }}
        </span>
      </div>
    </div>
    <div class="text-center text-[11px] font-semibold uppercase tracking-wider text-[var(--ink2)]">
      {{ label }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  label: { type: String, default: '' },
  size:  { type: Number, default: 88 },
})

const strokeW      = computed(() => Math.max(6, props.size * 0.09))
const cx           = computed(() => props.size / 2)
const cy           = computed(() => props.size / 2)
const r            = computed(() => (props.size - strokeW.value) / 2)
const circumference = computed(() => 2 * Math.PI * r.value)

const animated = ref(0)
onMounted(() => setTimeout(() => { animated.value = props.score }, 80))

const dashOffset = computed(() =>
  circumference.value * (1 - Math.min(animated.value, 10) / 10)
)

const trackColor = computed(() => {
  if (props.score >= 7.5) return '#34d399'
  if (props.score >= 5)   return '#f59e0b'
  return '#f43f5e'
})
</script>
