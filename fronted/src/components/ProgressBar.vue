<!-- src/components/ProgressBar.vue — Reusable animated progress bar -->
<template>
  <div class="progress-bar-wrapper">
    <div v-if="label || showPercent" class="progress-bar-header">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-value">{{ displayValue }}%</span>
    </div>
    <div class="progress-track" :style="{ height: height }">
      <div
        class="progress-fill"
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
  value:       { type: Number, default: 0 },   // 0–100
  label:       { type: String, default: '' },
  color:       { type: String, default: 'primary' },  // primary | success | warning | danger | custom hex
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
    const ease = t < 0.5 ? 2*t*t : -1+(4-2*t)*t   // easeInOut
    animatedWidth.value = from + (target - from) * ease
    if (t < 1) requestAnimationFrame(step)
    else animatedWidth.value = target
  }
  requestAnimationFrame(step)
}

onMounted(animate)
watch(() => props.value, animate)
</script>

<style scoped>
.progress-bar-wrapper { width: 100%; }

.progress-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.progress-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-muted);
}
.progress-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-text);
}

.progress-track {
  width: 100%;
  background: var(--color-surface-2);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.05s linear;
  position: relative;
  overflow: hidden;
}
.progress-fill::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 200%; height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%);
  animation: shimmer 2s infinite;
}
@keyframes shimmer { to { left: 100%; } }
</style>
