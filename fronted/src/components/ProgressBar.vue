<!-- src/components/ProgressBar.vue — Reusable animated progress bar -->
<template>
  <div class="w-full">
    <div v-if="label || showPercent" class="mb-1.5 flex items-center justify-between">
      <span class="text-sm font-medium text-[var(--color-text-muted)]">{{ label }}</span>
      <span class="text-sm font-bold text-[var(--color-text)]">{{ displayValue }}%</span>
    </div>
    <div class="w-full overflow-hidden rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)]" :style="{ height }">
      <div
        class="progress-fill-shimmer h-full rounded-full transition-[width] duration-75 ease-linear"
        :style="{
          width: animatedWidth + '%',
          background: computedColor,
        }"
        role="progressbar"
        :aria-valuenow="value"
        :aria-valuemin="0"
        :aria-valuemax="100"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  value:       { type: Number, default: 0 },
  label:       { type: String, default: '' },
  color:       { type: String, default: 'primary' },
  height:      { type: String, default: '10px' },
  showPercent: { type: Boolean, default: true },
  animated:    { type: Boolean, default: true },
})

const animatedWidth = ref(0)
const displayValue  = computed(() => Math.round(props.value))

const computedColor = computed(() => {
  const map = {
    primary: 'linear-gradient(90deg,#7c6af7,#4ecdc4)',
    success: 'linear-gradient(90deg,#43e97b,#38f9d7)',
    warning: 'linear-gradient(90deg,#f7b731,#ffd32a)',
    danger:  'linear-gradient(90deg,#f64c72,#f7797d)',
  }
  return map[props.color] || props.color
})

function animate() {
  if (!props.animated) { animatedWidth.value = props.value; return }
  const target   = Math.min(Math.max(props.value, 0), 100)
  const duration = 800
  const start    = performance.now()
  const from     = animatedWidth.value

  const step = (now) => {
    const t = Math.min((now - start) / duration, 1)
    const ease = t < 0.5 ? 2*t*t : -1+(4-2*t)*t
    animatedWidth.value = from + (target - from) * ease
    if (t < 1) requestAnimationFrame(step)
    else animatedWidth.value = target
  }
  requestAnimationFrame(step)
}

onMounted(animate)
watch(() => props.value, animate)
</script>
