<template>
  <div class="ct-card p-5">
    <!-- Header -->
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-[#111] text-white">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>
          </span>
          <div class="text-sm font-bold text-[var(--ink)]">Dự đoán điểm tuần tới</div>
        </div>
        <p class="mt-1 text-[11px] text-[var(--ink3)]">
          Mô hình RandomForest · {{ data?.weeks_of_data ?? 0 }} tuần dữ liệu
        </p>
      </div>
      <button
        class="rounded-lg border border-[var(--border)] px-3 py-1.5 text-[12px] font-medium text-[var(--ink2)] transition hover:bg-[var(--bg2)] disabled:opacity-50"
        :disabled="loading"
        @click="load"
      >{{ loading ? 'Đang tính…' : 'Làm mới' }}</button>
    </div>

    <!-- Loading / error / cold-start -->
    <div v-if="loading" class="py-12 text-center text-[13px] text-[var(--ink3)]">Đang dự đoán…</div>
    <div v-else-if="error" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-800">{{ error }}</div>
    <div v-else-if="!data?.enabled" class="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-4 py-6 text-center text-[13px] text-[var(--ink3)]">
      Tính năng dự đoán tuần tới chưa được bật.
    </div>
    <div v-else-if="data?.cold_start" class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-6 text-center">
      <p class="text-[13px] font-medium text-amber-900">Chưa đủ dữ liệu để dự đoán</p>
      <p class="mt-1 text-[12px] text-amber-800">{{ data?.message }}</p>
    </div>

    <!-- Result -->
    <template v-else>
      <!-- Status banner -->
      <div class="flex items-start gap-2.5 rounded-xl border px-4 py-3" :class="bannerClass">
        <span class="mt-0.5 shrink-0" v-html="bannerIcon" />
        <p class="text-[13px] font-medium leading-snug">{{ data?.message }}</p>
      </div>

      <!-- Overall headline -->
      <div class="mt-4 flex items-center justify-between rounded-xl bg-[var(--bg)] px-4 py-3.5">
        <div>
          <div class="text-[11px] uppercase tracking-wide text-[var(--ink3)]">Overall tuần tới</div>
          <div class="mt-0.5 flex items-baseline gap-2">
            <span class="text-[28px] font-extrabold leading-none text-[var(--ink)]">{{ fmt(data.overall.predicted) }}</span>
            <span class="text-[12px] text-[var(--ink3)]">hiện tại {{ fmt(data.overall.current) }}</span>
          </div>
        </div>
        <div class="text-right">
          <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[13px] font-bold" :class="deltaPill(data.overall.delta)">
            <span v-html="deltaArrow(data.overall.delta)" />
            {{ deltaLabel(data.overall.delta) }}
          </span>
          <div class="mt-1 text-[11px] text-[var(--ink3)]">Mục tiêu {{ fmt(data.target_band) }}</div>
        </div>
      </div>

      <!-- Per-skill grid -->
      <div class="mt-3 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <div
          v-for="s in data.skills"
          :key="s.skill"
          class="rounded-xl border border-[var(--border)] px-3 py-2.5"
        >
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold capitalize text-[var(--ink2)]">{{ skillLabel(s.skill) }}</span>
            <span v-html="deltaArrow(s.delta)" />
          </div>
          <div class="mt-1.5 flex items-baseline gap-1.5">
            <span class="text-[18px] font-bold text-[var(--ink)]">{{ fmt(s.predicted) }}</span>
            <span class="text-[11px] text-[var(--ink3)]">← {{ fmt(s.current) }}</span>
          </div>
          <div class="mt-1 text-[10px] font-medium" :class="deltaText(s.delta)">{{ deltaLabel(s.delta) }} band</div>
        </div>
      </div>

      <p class="mt-3 text-[10px] leading-relaxed text-[var(--ink3)]">
        Dự đoán mang tính tham khảo (formative), dựa trên nhịp độ luyện tập của bạn — không thay thế điểm thi IELTS chính thức.
      </p>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchNextWeekForecast } from '@/services/forecastService.js'

const data = ref(null)
const loading = ref(false)
const error = ref('')

const SKILL_LABELS = {
  overall: 'Overall',
  reading: 'Reading',
  listening: 'Listening',
  writing: 'Writing',
  speaking: 'Speaking',
}

function skillLabel(skill) {
  return SKILL_LABELS[skill] || skill
}

function fmt(v) {
  return v == null ? '—' : Number(v).toFixed(1)
}

function deltaLabel(delta) {
  if (delta == null) return '—'
  const d = Number(delta)
  return `${d > 0 ? '+' : ''}${d.toFixed(1)}`
}

const ARROW_UP = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>`
const ARROW_DOWN = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2.5"><path d="M12 5v14"/><path d="M5 12l7 7 7-7"/></svg>`
const ARROW_FLAT = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2.5"><path d="M5 12h14"/></svg>`

function deltaArrow(delta) {
  const d = Number(delta || 0)
  if (d > 0.01) return ARROW_UP
  if (d < -0.01) return ARROW_DOWN
  return ARROW_FLAT
}

function deltaPill(delta) {
  const d = Number(delta || 0)
  if (d > 0.01) return 'bg-emerald-100 text-emerald-700'
  if (d < -0.01) return 'bg-rose-100 text-rose-700'
  return 'bg-gray-100 text-gray-600'
}

function deltaText(delta) {
  const d = Number(delta || 0)
  if (d > 0.01) return 'text-emerald-600'
  if (d < -0.01) return 'text-rose-600'
  return 'text-[var(--ink3)]'
}

const bannerClass = computed(() => {
  const st = data.value?.status
  if (st === 'improving') return 'border-emerald-200 bg-emerald-50 text-emerald-900'
  if (st === 'declining') return 'border-rose-200 bg-rose-50 text-rose-900'
  return 'border-amber-200 bg-amber-50 text-amber-900'
})

const bannerIcon = computed(() => {
  const st = data.value?.status
  if (st === 'improving') {
    return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`
  }
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchNextWeekForecast(true)
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Không tải được dự đoán tuần tới'
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
