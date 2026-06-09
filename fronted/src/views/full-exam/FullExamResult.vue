<template>
  <div class="fe-result">
    <RouterLink
      to="/full-exam"
      class="mb-4 inline-flex items-center gap-1.5 text-[12px] text-[var(--ink3)] transition-colors hover:text-[var(--ink)]"
      @click="fullExam.clear()"
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="15 18 9 12 15 6" />
      </svg>
      Full Mock Exam
    </RouterLink>

    <header class="fe-result__hero mb-6 overflow-hidden rounded-2xl border border-[#a7f3d0]/50 bg-gradient-to-br from-[#ecfdf5] to-white p-6 text-center">
      <div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#34d399] text-white shadow-lg shadow-[#34d399]/25">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      </div>
      <h1 class="text-xl font-bold text-[var(--ink)]">Hoàn thành Full Mock</h1>
      <p class="mt-1 text-[13px] text-[var(--ink3)]">{{ setTitle }}</p>
    </header>

    <div v-if="summaryRows.length" class="grid gap-3 sm:grid-cols-2">
      <div
        v-for="row in summaryRows"
        :key="row.label"
        class="fe-score-card rounded-xl border border-[var(--border)] bg-white p-4"
      >
        <div class="flex items-center gap-3">
          <span class="fe-score-card__icon" v-html="row.icon" />
          <div class="min-w-0 flex-1">
            <div class="text-[12px] font-medium text-[var(--ink3)]">{{ row.label }}</div>
            <div class="text-xl font-bold tabular-nums text-[var(--ink)]">{{ row.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <p v-else class="rounded-xl border border-[var(--border)] bg-white p-6 text-center text-[13px] text-[var(--ink3)]">
      Chưa có điểm chi tiết cho phiên này.
    </p>

    <div
      v-if="isPlacementMode"
      class="mt-5 rounded-xl border px-4 py-3 text-center text-[13px]"
      :class="placementError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-[#a7f3d0] bg-[#ecfdf5] text-[#047857]'"
    >
      {{ placementMessage }}
    </div>

    <div class="mt-8 flex flex-wrap justify-center gap-3">
      <router-link to="/history" class="ct-btn">Xem lịch sử</router-link>
      <div class="profile-page">
        <router-link to="/full-exam" class="btn btn-primary" @click="fullExam.clear()">
          Thi bộ đề khác
        </router-link>
      </div>
      <router-link to="/dashboard" class="ct-btn" @click="fullExam.clear()">Dashboard</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { useFullExamStore } from '@/stores/fullExam.js'
import { usePlacementStore } from '@/stores/placement.js'

const SKILL_ICONS = {
  Reading: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  Listening: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/></svg>`,
  'Writing Task 1': `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  'Writing Task 2': `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  Speaking: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>`,
}

const router = useRouter()
const auth = useAuthStore()
const fullExam = useFullExamStore()
const placement = usePlacementStore()
const placementError = ref('')
const placementSaved = ref(false)

const session = computed(() => fullExam.getSession())
const setTitle = computed(() => session.value?.set?.title || '')
const isPlacementMode = computed(() => Boolean(session.value?.placementMode))
const placementMessage = computed(() => {
  if (placementError.value) return placementError.value
  if (placementSaved.value) return 'Initial IELTS bands saved from this full placement test.'
  return 'Saving your initial IELTS bands from this full placement test...'
})

const summaryRows = computed(() => {
  const r = session.value?.results || {}
  const rows = []
  if (r.reading) {
    rows.push({
      label: 'Reading',
      value: r.reading.estimatedBand ?? r.reading.band ?? '—',
      icon: SKILL_ICONS.Reading,
    })
  }
  if (r.listening) {
    rows.push({
      label: 'Listening',
      value: r.listening.estimatedBand ?? r.listening.band ?? '—',
      icon: SKILL_ICONS.Listening,
    })
  }
  if (r.writing?.task1) {
    rows.push({
      label: 'Writing Task 1',
      value: r.writing.task1.band_score ?? '—',
      icon: SKILL_ICONS['Writing Task 1'],
    })
  }
  if (r.writing?.task2) {
    rows.push({
      label: 'Writing Task 2',
      value: r.writing.task2.band_score ?? '—',
      icon: SKILL_ICONS['Writing Task 2'],
    })
  }
  if (r.speaking) {
    rows.push({
      label: 'Speaking',
      value: r.speaking.band ?? '—',
      icon: SKILL_ICONS.Speaking,
    })
  }
  return rows
})

onMounted(async () => {
  if (!session.value) {
    router.replace('/full-exam')
    return
  }
  fullExam.setStage('done')
  if (session.value.placementMode) {
    await finalizePlacementResult()
  }
})

async function finalizePlacementResult() {
  if (placementSaved.value) return
  const bands = extractPlacementBands(session.value?.results || {})
  if (!bands) {
    placementError.value = 'Cannot save placement result because one or more skill bands are missing.'
    return
  }
  const result = await placement.finalizeFullExam({
    ...bands,
    set_id: String(session.value.setId || ''),
    session_id: session.value.sessionId,
    results: session.value.results || {},
  })
  if (!result) {
    placementError.value = placement.error || 'Cannot save placement result.'
    return
  }
  placementSaved.value = true
  await auth.fetchProfile()
}

function extractPlacementBands(results) {
  const reading = bandValue(results.reading?.estimatedBand, results.reading?.band, results.reading?.band_score)
  const listening = bandValue(results.listening?.estimatedBand, results.listening?.band, results.listening?.band_score)
  const writing = writingBand(results.writing)
  const speaking = bandValue(results.speaking?.band, results.speaking?.summary?.band_estimate, results.speaking?.band_score)
  if ([reading, listening, writing, speaking].some((value) => value == null)) return null
  return { reading, listening, writing, speaking }
}

function writingBand(result) {
  if (!result) return null
  const task1 = bandValue(result.task1?.band_score, result.task1?.overall_band)
  const task2 = bandValue(result.task2?.band_score, result.task2?.overall_band, result.band)
  const values = [task1, task2].filter((value) => value != null)
  if (!values.length) return bandValue(result.band)
  return roundBand(values.reduce((sum, value) => sum + value, 0) / values.length)
}

function bandValue(...values) {
  for (const value of values) {
    const num = Number(value)
    if (Number.isFinite(num)) return roundBand(num)
  }
  return null
}

function roundBand(value) {
  return Math.max(0, Math.min(9, Math.round(Number(value) * 2) / 2))
}
</script>

<style scoped>
.fe-result {
  max-width: 640px;
  margin: 0 auto;
}
.fe-score-card__icon {
  display: flex;
  height: 40px;
  width: 40px;
  shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #f0fdf4;
  color: #059669;
}
</style>
