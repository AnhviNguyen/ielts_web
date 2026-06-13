<template>
  <RouterLink
    v-if="show"
    to="/dashboard?tab=forecast"
    class="flex items-center gap-3 rounded-xl border px-4 py-3 transition hover:brightness-[0.98]"
    :class="bannerClass"
  >
    <span class="shrink-0" v-html="icon" />
    <div class="min-w-0 flex-1">
      <div class="text-[13px] font-semibold">{{ title }}</div>
      <p class="truncate text-[12px] opacity-90">{{ data.message }}</p>
    </div>
    <span class="shrink-0 text-[12px] font-bold">{{ fmt(data.overall.predicted) }}
      <span class="ml-0.5 text-[11px] font-medium opacity-80">({{ deltaLabel }})</span>
    </span>
    <svg class="shrink-0 opacity-60" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
  </RouterLink>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchNextWeekForecast } from '@/services/forecastService.js'

const data = ref(null)

// Home view never triggers notifications — that is owned by the Forecast tab.
const show = computed(() => !!data.value && data.value.enabled && !data.value.cold_start && !!data.value.overall)

const title = computed(() => {
  const st = data.value?.status
  if (st === 'improving') return 'Dự báo tuần tới: đang tiến bộ'
  if (st === 'declining') return 'Cảnh báo: điểm có thể giảm tuần tới'
  return 'Dự báo tuần tới: đang chững lại'
})

const deltaLabel = computed(() => {
  const d = Number(data.value?.overall?.delta || 0)
  return `${d > 0 ? '+' : ''}${d.toFixed(1)}`
})

function fmt(v) {
  return v == null ? '—' : Number(v).toFixed(1)
}

const bannerClass = computed(() => {
  const st = data.value?.status
  if (st === 'improving') return 'border-[var(--spotify-green)] bg-[var(--green-bg)] text-[var(--text-base)]'
  if (st === 'declining') return 'border-[var(--text-negative)] bg-[var(--rose-bg)] text-[var(--text-base)]'
  return 'border-[var(--text-warning)] bg-[var(--amber-bg)] text-[var(--text-base)]'
})

const icon = computed(() => {
  const st = data.value?.status
  if (st === 'improving') {
    return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>`
  }
  return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
})

onMounted(async () => {
  try {
    data.value = await fetchNextWeekForecast(false)
  } catch {
    data.value = null
  }
})
</script>
