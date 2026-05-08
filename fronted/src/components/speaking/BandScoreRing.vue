<template>
  <div class="flex flex-col items-center gap-3">
    <div class="relative" style="width:140px;height:140px">
      <svg width="140" height="140" viewBox="0 0 140 140" class="-rotate-90">
        <circle cx="70" cy="70" r="58" fill="none" stroke="#e5e7eb" stroke-width="12"/>
        <circle
          cx="70" cy="70" r="58"
          fill="none"
          stroke="#34d399"
          stroke-width="12"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          style="transition: stroke-dashoffset 1.2s ease"
        />
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-3xl font-extrabold leading-none text-[var(--ink)]">{{ band.toFixed(1) }}</span>
        <span class="mt-1 text-[9px] font-bold uppercase tracking-widest text-[var(--ink3)]">Band</span>
      </div>
    </div>
    <span
      class="rounded-full border px-3 py-0.5 text-[11px] font-semibold"
      :style="{ borderColor: bandColor + '66', color: bandColor, background: bandColor + '11' }"
    >
      {{ bandDescriptor }}
    </span>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({ band: { type: Number, default: 0 } })

const circumference = 2 * Math.PI * 58
const animated = ref(0)
onMounted(() => setTimeout(() => { animated.value = props.band }, 120))

const dashOffset = computed(() =>
  circumference * (1 - Math.min(animated.value, 9) / 9)
)

const bandColor = computed(() => {
  if (props.band >= 7.5) return '#34d399'
  if (props.band >= 6)   return '#f59e0b'
  return '#f43f5e'
})

const bandDescriptor = computed(() => {
  const b = props.band
  if (b >= 8.5) return 'Expert'
  if (b >= 7.5) return 'Very Good'
  if (b >= 7)   return 'Good'
  if (b >= 6.5) return 'Competent'
  if (b >= 6)   return 'Modest'
  if (b >= 5)   return 'Limited'
  return 'Developing'
})
</script>
