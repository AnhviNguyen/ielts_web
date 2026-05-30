<template>
  <div class="min-h-screen bg-[var(--bg)] py-8">
    <div class="mx-auto w-full max-w-2xl px-4">

      <!-- Back nav -->
      <RouterLink to="/dashboard" class="mb-5 inline-flex items-center gap-1.5 text-[12px] text-[var(--ink3)] hover:text-[var(--ink)] transition-colors">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        Về trang chủ
      </RouterLink>

      <!-- No result -->
      <div v-if="!result" class="ct-card p-8 text-center">
        <div class="mb-2 text-base font-semibold text-[var(--ink)]">Chưa có kết quả</div>
        <RouterLink :to="`/quiz/${route.params.quizId}`" class="ct-btn mt-4 inline-flex">Quay lại bài</RouterLink>
      </div>

      <template v-else>

        <!-- ─── Score hero ─── -->
        <div class="ct-card mb-5 overflow-hidden">
          <!-- Top accent bar -->
          <div class="h-1 w-full" style="background:#34d399"></div>

          <div class="p-6">
            <!-- Title row -->
            <div class="mb-6 flex items-start justify-between gap-4">
              <div>
                <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Kết quả bài thi</div>
                <div class="mt-1 text-base font-bold text-[var(--ink)]">{{ result.title || 'IELTS Mock Test' }}</div>
              </div>
              <div class="shrink-0 rounded-xl border border-[var(--border)] bg-[var(--bg)] px-4 py-2 text-center">
                <div class="text-[10px] text-[var(--ink3)]">Band ước tính</div>
                <div class="text-xl font-extrabold text-[var(--ink)]">{{ result.estimatedBand ?? '—' }}</div>
              </div>
            </div>

            <!-- Score ring + stats -->
            <div class="flex flex-wrap items-center gap-8">
              <!-- SVG ring -->
              <div class="relative shrink-0">
                <svg viewBox="0 0 120 120" width="120" height="120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#f3f4f6" stroke-width="10"/>
                  <circle
                    cx="60" cy="60" r="50"
                    fill="none"
                    stroke="#34d399"
                    stroke-width="10"
                    stroke-linecap="round"
                    :stroke-dasharray="`${pct * 3.14} 314`"
                    transform="rotate(-90 60 60)"
                    style="transition: stroke-dasharray 1.2s ease"
                  />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span class="text-2xl font-extrabold text-[var(--ink)]">{{ pct }}%</span>
                  <span class="text-[10px] text-[var(--ink3)]">Score</span>
                </div>
              </div>

              <!-- Stat pills -->
              <div class="flex flex-1 flex-wrap gap-3">
                <div class="flex-1 rounded-xl border border-[var(--border)] bg-[#f0fdf4] px-4 py-3 text-center">
                  <div class="text-[10px] font-semibold uppercase tracking-wide text-[#059669]">Đúng</div>
                  <div class="mt-1 text-2xl font-extrabold text-[#059669]">{{ result.correct ?? correct }}</div>
                </div>
                <div class="flex-1 rounded-xl border border-[var(--border)] bg-[var(--rose-bg)] px-4 py-3 text-center">
                  <div class="text-[10px] font-semibold uppercase tracking-wide text-[var(--rose)]">Sai</div>
                  <div class="mt-1 text-2xl font-extrabold text-[var(--rose)]">{{ wrong }}</div>
                </div>
                <div class="flex-1 rounded-xl border border-[var(--border)] bg-[var(--bg2)] px-4 py-3 text-center">
                  <div class="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink3)]">Tổng</div>
                  <div class="mt-1 text-2xl font-extrabold text-[var(--ink)]">{{ result.total }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ─── Answer key (correct / wrong only) ─── -->
        <div v-if="rows.length" class="ct-card mb-5 overflow-hidden">
          <div class="border-b border-[var(--border)] px-5 py-3.5">
            <span class="text-[14px] font-bold text-[var(--ink)]">Answer Key</span>
          </div>
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 px-5 py-4">
            <div
              v-for="(row, i) in rows"
              :key="row.questionId || i"
              class="flex items-center gap-2 text-[12px]"
            >
              <div
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                :style="row.isCorrect ? 'background:#d1fae5;color:#065f46' : 'background:#ffe4e6;color:#be123c'"
              >
                {{ row.order || (i + 1) }}
              </div>
              <span class="truncate font-medium text-[var(--ink)]">{{ formatCorrect(row) }}</span>
              <span class="text-[var(--ink3)]">:</span>
              <span class="font-mono font-semibold" :style="row.isCorrect ? 'color:#059669' : 'color:#e11d48'">
                {{ formatUser(row.userAnswer) }}
              </span>
              <svg v-if="row.isCorrect" class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            </div>
          </div>
        </div>

        <!-- ─── Actions ─── -->
        <div class="profile-page mt-6 flex flex-wrap justify-center gap-3">
          <RouterLink
            v-if="reviewQuizLink"
            :to="reviewQuizLink"
            class="btn btn-primary inline-flex items-center"
          >
            Giải thích
          </RouterLink>
          <RouterLink to="/dashboard" class="ct-btn">
            <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Dashboard
          </RouterLink>
          <RouterLink :to="`/quiz/${route.params.quizId}`" class="ct-btn">
            <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
            Làm lại
          </RouterLink>
          <RouterLink to="/history" class="ct-btn">
            <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            Lịch sử
          </RouterLink>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useMockQuizStore } from '@/stores/mockQuiz.js'

const route = useRoute()
const store = useMockQuizStore()
const result = computed(() => store.result)

const reviewQuizLink = computed(() => {
  const qid = route.params.quizId
  if (!qid || !rows.value.length) return null
  return `/review/quiz/${qid}`
})

const correct = computed(() => {
  if (!result.value) return 0
  if (result.value.correct != null) return result.value.correct
  return (result.value.detailed || []).filter(r => r.isCorrect).length
})
const wrong   = computed(() => (result.value?.total ?? 0) - correct.value)
const pct     = computed(() => {
  const t = result.value?.total ?? 0
  if (!t) return 0
  return Math.round((correct.value / t) * 100)
})

const rows = computed(() => result.value?.detailed ?? [])

function formatUser(v) {
  if (Array.isArray(v)) return v.join(', ')
  return v != null ? String(v) : '—'
}
function formatCorrect(row) {
  if (Array.isArray(row.correct_answers) && row.correct_answers.length) return row.correct_answers.join(' / ')
  if (row.correct_answer) return String(row.correct_answer)
  return '—'
}
</script>
