<template>
  <div class="min-h-screen bg-[var(--bg)] py-8">
    <div class="mx-auto w-full max-w-2xl px-4">

      <!-- Back nav -->
      <RouterLink to="/dashboard" class="mb-5 inline-flex items-center gap-1.5 text-[12px] text-[var(--ink3)] hover:text-[var(--ink)] transition-colors">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        Về trang chủ
      </RouterLink>

      <div v-if="!result" class="ct-card p-8 text-center">
        <div class="mb-2 text-base font-semibold text-[var(--ink)]">Không tìm thấy kết quả</div>
        <RouterLink to="/dashboard" class="ct-btn mt-4 inline-flex">Về Dashboard</RouterLink>
      </div>

      <template v-else>

        <!-- Hero score card -->
        <div class="ct-card mb-5 overflow-hidden">
          <div class="h-1 w-full" style="background:#34d399"></div>
          <div class="p-6">

            <div class="mb-6 flex items-start justify-between gap-4">
              <div>
                <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Kết quả luyện tập</div>
                <div class="mt-1 text-base font-bold text-[var(--ink)]">{{ display.subject }}</div>
              </div>
              <div class="shrink-0 rounded-xl border border-[var(--border)] bg-[var(--bg)] px-4 py-2 text-center">
                <div class="text-[10px] text-[var(--ink3)]">Điểm</div>
                <div class="text-xl font-extrabold text-[var(--ink)]">{{ display.score }}/{{ display.total }}</div>
              </div>
            </div>

            <!-- Ring + stats -->
            <div class="flex flex-wrap items-center gap-8">
              <div class="relative shrink-0">
                <svg viewBox="0 0 120 120" width="120" height="120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#f3f4f6" stroke-width="10"/>
                  <circle
                    cx="60" cy="60" r="50"
                    fill="none"
                    stroke="#34d399"
                    stroke-width="10"
                    stroke-linecap="round"
                    :stroke-dasharray="`${display.percentage * 3.14} 314`"
                    transform="rotate(-90 60 60)"
                    style="transition:stroke-dasharray 1.2s ease"
                  />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span class="text-2xl font-extrabold text-[var(--ink)]">{{ display.percentage }}%</span>
                  <span class="text-[10px] text-[var(--ink3)]">Score</span>
                </div>
              </div>

              <div class="flex flex-1 flex-wrap gap-3">
                <div class="flex-1 rounded-xl border border-[var(--border)] bg-[#f0fdf4] px-4 py-3 text-center">
                  <div class="text-[10px] font-semibold uppercase tracking-wide text-[#059669]">Đúng</div>
                  <div class="mt-1 text-2xl font-extrabold text-[#059669]">{{ display.score }}</div>
                </div>
                <div class="flex-1 rounded-xl border border-[var(--border)] bg-[var(--rose-bg)] px-4 py-3 text-center">
                  <div class="text-[10px] font-semibold uppercase tracking-wide text-[var(--rose)]">Sai</div>
                  <div class="mt-1 text-2xl font-extrabold text-[var(--rose)]">{{ display.total - display.score }}</div>
                </div>
                <div class="flex-1 rounded-xl border border-[var(--border)] bg-[var(--bg2)] px-4 py-3 text-center">
                  <div class="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink3)]">Tổng</div>
                  <div class="mt-1 text-2xl font-extrabold text-[var(--ink)]">{{ display.total }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ Answer Key section ══ -->
        <div v-if="display.detailedAnswers.length" class="ct-card mb-5 overflow-hidden">
          <div class="border-b border-[var(--border)] px-5 py-3.5">
            <span class="text-[14px] font-bold text-[var(--ink)]">Answer Key</span>
          </div>

          <!-- Grouped by part -->
          <div v-for="(part, pi) in answerKeyParts" :key="pi" class="border-b border-[var(--border)] last:border-0 px-5 py-4">
            <!-- Part header -->
            <div class="mb-3 flex items-center justify-between">
              <span class="text-[12px] font-bold text-[var(--ink2)]">{{ part.label }}</span>
              <span
                class="rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                :style="part.correct === part.total ? 'background:#d1fae5;color:#065f46' : 'background:#ffe4e6;color:#be123c'"
              >
                {{ part.correct }}/{{ part.total }} đúng
              </span>
            </div>

            <!-- Two-column grid -->
            <div class="grid grid-cols-2 gap-x-6 gap-y-2">
              <div
                v-for="ans in part.answers"
                :key="ans.questionId"
                class="flex items-center gap-2 text-[12px]"
              >
                <!-- Question number bubble -->
                <div
                  class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                  :style="ans.isCorrect
                    ? 'background:#d1fae5;color:#065f46'
                    : 'background:#ffe4e6;color:#be123c'"
                >
                  {{ ans.order }}
                </div>
                <!-- Correct answer -->
                <span class="truncate font-medium text-[var(--ink)]">{{ ans.correctAnswer ?? '—' }}</span>
                <!-- Separator -->
                <span class="text-[var(--ink3)]"> : </span>
                <!-- User answer -->
                <span
                  class="font-mono font-semibold"
                  :style="ans.isCorrect ? 'color:#059669' : 'color:#e11d48'"
                >{{ ans.userAnswer ?? '—' }}</span>
                <!-- Icon -->
                <svg v-if="ans.isCorrect" class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                <svg v-else class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="!display.detailedAnswers.length" class="ct-card mb-5 p-6 text-center text-[var(--ink3)]">
          Chưa có thông tin chi tiết đáp án.
        </div>

        <!-- Actions -->
        <div class="profile-page mt-6 flex flex-wrap justify-center gap-3">
          <RouterLink
            v-if="reviewLink"
            :to="reviewLink"
            class="btn btn-primary inline-flex items-center"
          >
            <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            Giải thích
          </RouterLink>
          <RouterLink to="/dashboard" class="ct-btn">
            <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Dashboard
          </RouterLink>
          <RouterLink :to="`/${String(display.subject).toLowerCase()}`" class="ct-btn" @click="quizStore.clearResult?.()">
            <svg class="mr-1.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
            Thử lại
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
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePracticeStore } from '@/stores/practice.js'
import { useMockQuizStore } from '@/stores/mockQuiz.js'

const practiceStore  = usePracticeStore()
const quizStore      = useMockQuizStore()
const route          = useRoute()
const result         = computed(() => practiceStore.lastResult)

const display = computed(() => {
  const r   = result.value || {}
  const score      = Number(r.score ?? 0)
  const total      = Number(r.total_questions ?? r.total ?? 0)
  const percentage = Number(r.percentage ?? (total ? Math.round((score / total) * 100) : 0))
  const detailedAnswers = Array.isArray(r.details)
    ? r.details.map((x) => ({
        questionId:    x.question_id,
        order:         x.order || 0,
        question:      x.question,
        userAnswer:    x.user_answer,
        correctAnswer: x.correct_answer ?? (Array.isArray(x.correct_answers) ? x.correct_answers.join(' / ') : null),
        isCorrect:     Boolean(x.is_correct),
        partIndex:     x.part_index ?? null,
        partTitle:     x.part_title ?? null,
      }))
    : Array.isArray(r.detailedAnswers) ? r.detailedAnswers : []

  return { score, total, percentage, subject: r.subject || 'Listening', detailedAnswers }
})

/**
 * Group answers by part for the Answer Key.
 * Uses part_index from backend if available, else groups by chunks of 10.
 */
const answerKeyParts = computed(() => {
  const answers = display.value.detailedAnswers
  if (!answers.length) return []

  // Check if backend provides part info
  const hasPartInfo = answers.some(a => a.partIndex !== null && a.partIndex !== undefined)

  if (hasPartInfo) {
    // Group by part_index
    const partsMap = new Map()
    for (const ans of answers) {
      const key = ans.partIndex ?? 0
      if (!partsMap.has(key)) {
        partsMap.set(key, {
          label: ans.partTitle || `Part ${key + 1}`,
          answers: [],
          correct: 0,
          total: 0,
        })
      }
      const p = partsMap.get(key)
      p.answers.push(ans)
      p.total++
      if (ans.isCorrect) p.correct++
    }
    return Array.from(partsMap.values()).sort((a, b) => {
      const ai = parseInt(a.label.match(/\d+/)?.[0] || 0)
      const bi = parseInt(b.label.match(/\d+/)?.[0] || 0)
      return ai - bi
    })
  }

  // Fallback: chunk by 10 (IELTS standard)
  const chunkSize = 10
  const parts = []
  for (let i = 0; i < answers.length; i += chunkSize) {
    const chunk = answers.slice(i, i + chunkSize)
    const partNum = Math.floor(i / chunkSize) + 1
    parts.push({
      label: `Part ${partNum}`,
      answers: chunk,
      correct: chunk.filter(a => a.isCorrect).length,
      total: chunk.length,
    })
  }
  return parts
})

const reviewLink = computed(() => {
  const sessionId = route.params.sessionId
  const annotationSession = route.query.annotationSession
  if (sessionId) {
    const q = annotationSession ? `?annotationSession=${annotationSession}` : ''
    return `/review/${sessionId}${q}`
  }
  const quizId = result.value?.quizId
  if (quizId) return `/review/quiz/${quizId}`
  return null
})

onMounted(async () => {
  const sessionId = route.params.sessionId
  if (sessionId) await practiceStore.fetchResult(sessionId)
})
</script>
