<template>
  <div class="min-h-screen bg-[var(--bg)] pb-16">
    <!-- Header -->
    <div class="sticky top-0 z-50 border-b border-[var(--border)] bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1400px] items-center gap-4 px-6 py-3">
        <button class="review-back-btn" @click="router.back()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          Quay lại
        </button>
        <div class="flex-1">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Xem lại bài làm</div>
          <div class="text-sm font-bold text-[var(--ink)]">{{ quizTitle }}</div>
        </div>
        <!-- Score badge -->
        <div v-if="result" class="review-score-badge">
          <span class="text-[10px] text-[var(--ink3)]">Điểm</span>
          <span class="text-lg font-extrabold text-[var(--ink)]">{{ result.score ?? result.correct }}/{{ result.total ?? result.total_questions }}</span>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center pt-24 gap-4 text-[var(--ink3)]">
      <svg class="animate-spin" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M22 12a10 10 0 0 1-10 10"/></svg>
      Đang tải...
    </div>

    <template v-else>
      <!-- Score summary bar -->
      <div v-if="result" class="mx-auto max-w-[1400px] px-4 pt-4">
        <div class="score-summary">
          <!-- Overall ring -->
          <div class="score-ring-wrap">
            <svg viewBox="0 0 80 80" width="80" height="80">
              <circle cx="40" cy="40" r="32" fill="none" stroke="#f1f5f9" stroke-width="7"/>
              <circle cx="40" cy="40" r="32" fill="none" stroke="#34d399" stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="`${overallPct * 2.01} 201`"
                transform="rotate(-90 40 40)"
                style="transition:stroke-dasharray 1s ease"
              />
            </svg>
            <div class="score-ring-label">
              <div class="text-xl font-extrabold text-[var(--ink)]">{{ overallPct }}%</div>
              <div class="text-[9px] text-[var(--ink3)]">Tổng</div>
            </div>
          </div>

          <!-- Correct / Wrong / Total -->
          <div class="score-stats">
            <div class="score-stat score-stat--correct">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <span class="score-stat-num">{{ correctCount }}</span>
              <span class="score-stat-lbl">Đúng</span>
            </div>
            <div class="score-stat score-stat--wrong">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              <span class="score-stat-num">{{ wrongCount }}</span>
              <span class="score-stat-lbl">Sai</span>
            </div>
            <div class="score-stat">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span class="score-stat-num">{{ totalCount }}</span>
              <span class="score-stat-lbl">Tổng</span>
            </div>
          </div>

          <!-- Per-part bars -->
          <div v-if="partScores.length > 1" class="part-bars">
            <div v-for="ps in partScores" :key="ps.idx" class="part-bar-item">
              <div class="part-bar-label">Passage {{ ps.idx + 1 }}</div>
              <div class="part-bar-track">
                <div class="part-bar-fill" :style="{ width: ps.pct + '%', background: ps.pct >= 70 ? '#34d399' : ps.pct >= 40 ? '#fbbf24' : '#f43f5e' }"></div>
              </div>
              <div class="part-bar-pct">{{ ps.correct }}/{{ ps.total }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Two-panel layout (same as QuizRunner) -->
      <div class="mx-auto max-w-[1400px] px-4 pt-4">
        <div class="flex gap-4">
          <div class="review-tools-rail">
            <ReadingToolbar
              vertical
              icon-only
              v-model:model-note="reviewNote"
              @tool-changed="onReviewToolbarChanged"
            />
          </div>

          <!-- Left: passage / audio -->
          <div class="flex flex-col gap-4 min-w-0" :style="{ flex: `0 0 ${leftWidth}px`, width: leftWidth + 'px' }">

            <!-- Listening: audio player -->
            <div v-if="isListeningQuiz" class="card p-4">
              <div class="mb-3 text-[12px] font-semibold text-[var(--ink2)]">
                {{ activePart?.title || 'Audio' }}
              </div>
              <audio
                ref="reviewAudioRef"
                :src="reviewAudioSrc"
                controls
                class="w-full rounded-lg"
                style="height: 40px; accent-color: #34d399"
              ></audio>
              <div v-if="!reviewAudioSrc" class="mt-2 text-[11px] text-[var(--ink3)]">
                Audio không khả dụng cho bài này.
              </div>
            </div>

            <div class="card overflow-hidden">
              <div class="flex flex-wrap items-center justify-between gap-2 px-4 pt-3 pb-2">
                <div class="text-xs font-semibold text-[var(--ink2)]">{{ activePart?.title }}</div>
                <div v-if="parts.length > 1" class="flex flex-wrap gap-1">
                  <button
                    v-for="(p, i) in parts"
                    :key="p.id"
                    class="rounded-lg px-3 py-1 text-[11px] font-semibold transition-colors"
                    :class="activePartIdx === i ? 'bg-[#15803d] text-white' : 'bg-[var(--bg2)] text-[var(--ink2)] hover:bg-[var(--border)]'"
                    @click="activePartIdx = i"
                  >{{ isListeningQuiz ? 'Part' : 'Passage' }} {{ i + 1 }}</button>
                </div>
              </div>

              <div class="overflow-y-auto px-4 pb-4" style="max-height: calc(100vh - 260px)">
                <ReadingPassage
                  :key="`review-${activePartIdx}-${reviewAudioSrc || 'r'}`"
                  ref="reviewPassageRef"
                  :paragraphs="activeParagraphs"
                  :active-tool="reviewActiveTool"
                  :highlight-color="reviewHighlightColor"
                  :review-mode="!isListeningQuiz"
                  :answer-highlights="isListeningQuiz ? [] : activeAnswerHighlights"
                  :session-highlights="reviewHighlights"
                  :source-type="isListeningQuiz ? 'listening' : 'reading'"
                  :source-quiz-id="String(quiz?.id || route.params.quizId || '')"
                  @highlights-changed="onReviewHighlightsChanged"
                />
              </div>
            </div>
          </div>

          <!-- Drag divider -->
          <div class="flex w-2 cursor-col-resize items-center justify-center group" @mousedown.prevent="startResize" ref="dividerEl">
            <div class="h-12 w-0.5 rounded-full bg-[var(--border2)] group-hover:bg-[#34d399] transition-colors"></div>
          </div>

          <!-- Right: Q&A with explanations -->
          <div class="card flex-1 overflow-auto p-5" style="max-height: calc(100vh - 100px)">
            <div v-for="(sec, si) in sections" :key="si" class="mb-6">
              <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">{{ sec.title }}</div>

              <!-- Listening gap-fill: hiển thị đề + chỗ trống để đối chiếu -->
              <template v-if="sec.kind === 'gap'">
                <div v-if="sec.description" class="mb-3 text-[13px] text-[var(--ink2)]" v-html="sec.description"></div>
                <div class="mb-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
                  <GapFillingHtml :html="sec.content" :gaps="sec.gapMap" :disabled="true" />
                </div>
                <div class="flex flex-col gap-3">
                  <div
                    v-for="q in sec.questions"
                    :key="q.id"
                    class="review-question-card"
                    :class="q.isCorrect ? 'review-question-card--correct' : 'review-question-card--wrong'"
                  >
                    <div class="review-q-header">
                      <span class="review-q-num">Câu {{ q.order }}</span>
                      <span class="review-q-badge" :class="q.isCorrect ? 'badge-correct' : 'badge-wrong'">
                        {{ q.isCorrect ? '✓ Đúng' : '✗ Sai' }}
                      </span>
                      <button
                        v-if="q.canExplain"
                        class="review-explain-btn"
                        :class="{ active: activeExplainId === q.id }"
                        type="button"
                        title="Xem giải thích"
                        @click="toggleExplain(q)"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                      </button>
                    </div>
                    <div class="review-answers">
                      <div class="review-answer-row">
                        <span class="review-answer-label">Đáp án của bạn</span>
                        <span class="review-answer-val" :class="q.isCorrect ? 'val-correct' : 'val-wrong'">
                          {{ getAnswerDisplay(q) || '—' }}
                        </span>
                      </div>
                      <div v-if="!q.isCorrect" class="review-answer-row review-answer-row--border">
                        <span class="review-answer-label">Đáp án đúng</span>
                        <span class="review-answer-val val-correct">{{ q.correctAnswers?.join(', ') || q.correctAnswer || '—' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <template v-else>
                <div v-if="sec.description" class="mb-3 text-[13px] text-[var(--ink2)]" v-html="sec.description"></div>
                <div class="flex flex-col gap-3">
                  <div
                    v-for="q in sec.questions"
                    :key="q.id"
                    class="review-question-card"
                    :class="q.isCorrect ? 'review-question-card--correct' : 'review-question-card--wrong'"
                  >
                    <div class="review-q-header">
                      <span class="review-q-num">Câu {{ q.order }}</span>
                      <span class="review-q-badge" :class="q.isCorrect ? 'badge-correct' : 'badge-wrong'">
                        {{ q.isCorrect ? '✓ Đúng' : '✗ Sai' }}
                      </span>
                      <button
                        v-if="q.canExplain"
                        class="review-explain-btn"
                        :class="{ active: activeExplainId === q.id }"
                        type="button"
                        title="Xem giải thích"
                        @click="toggleExplain(q)"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                      </button>
                    </div>
                    <p v-if="q.stemText" class="review-q-text review-q-stem">{{ q.stemText }}</p>
                    <p v-else-if="q.text || q.title" class="review-q-text">{{ q.text || q.title }}</p>
                    <div class="review-answers">
                      <div class="review-answer-row">
                        <span class="review-answer-label">Đáp án của bạn</span>
                        <span class="review-answer-val" :class="q.isCorrect ? 'val-correct' : 'val-wrong'">
                          {{ getAnswerDisplay(q) || '—' }}
                        </span>
                      </div>
                      <div v-if="!q.isCorrect" class="review-answer-row review-answer-row--border">
                        <span class="review-answer-label">Đáp án đúng</span>
                        <span class="review-answer-val val-correct">{{ q.correctAnswers?.join(', ') || q.correctAnswer || '—' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Explanation popup -->
    <Teleport to="body">
      <Transition name="popup-fade">
        <div v-if="explainPopup.visible" class="explain-overlay" @click.self="explainPopup.visible = false">
          <div class="explain-box">
            <div class="explain-header">
              <span class="explain-title">Giải thích – Câu {{ explainPopup.questionOrder }}</span>
              <div class="flex items-center gap-2">
                <button
                  v-if="explainPopup.listenFrom != null && isListeningQuiz"
                  type="button"
                  class="explain-goto-btn"
                  @click="goToExplainAudio()"
                >
                  Go to {{ formatSeconds(explainPopup.listenFrom) }}
                </button>
                <button class="explain-close" @click="explainPopup.visible = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>
            <div class="explain-body" v-html="explainPopup.html"></div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePracticeStore } from '@/stores/practice.js'
import { useMockQuizStore } from '@/stores/mockQuiz.js'
import { getAnnotation, saveAnnotation } from '@/services/vocabularyService.js'
import { buildParagraphsFromVocabs, isListeningQuiz as checkIsListening } from '@/utils/mockQuiz.js'
import { buildAudioSrc } from '@/utils/audio.js'
import { isCorrectAnswer } from '@/utils/scoring.js'
import {
  buildListeningExplainHtml,
  hasListeningExplain,
  resolveListenTimestamp,
  stripHtml,
} from '@/utils/listeningExplain.js'
import ReadingPassage from '@/components/reading/ReadingPassage.vue'
import ReadingToolbar from '@/components/reading/ReadingToolbar.vue'
import GapFillingHtml from '@/components/mock-tests/GapFillingHtml.vue'

const route  = useRoute()
const router = useRouter()
const practiceStore = usePracticeStore()
const quizStore     = useMockQuizStore()

const loading     = ref(true)
const quiz        = ref(null)
const result      = ref(null)
const reviewHighlights = ref([])
const reviewNote  = ref('')
const persistKey  = ref('')
const activePartIdx     = ref(0)
const activeExplainId   = ref(null)

const reviewActiveTool       = ref(null)
const reviewHighlightColor   = ref('yellow')
const reviewPassageRef       = ref(null)

const explainPopup = ref({ visible: false, html: '', questionOrder: 0, listenFrom: null })

// ── Listening audio (review mode) ─────────────────────────────────────────────
const reviewAudioRef   = ref(null)

const isListeningQuiz = computed(() => {
  if (!quiz.value) return false
  return checkIsListening(quiz.value)
})

const reviewAudioSrc = computed(() => {
  const part = parts.value[activePartIdx.value]
  if (!part?.file_id) return ''
  return buildAudioSrc(part.file_id)
})

// ── Layout ────────────────────────────────────────────────────────────────────
const leftWidth   = ref(580)
let isResizing = false, resizeStartX = 0, resizeStartW = 0
const dividerEl = ref(null)

function startResize(e) {
  isResizing = true; resizeStartX = e.clientX; resizeStartW = leftWidth.value
  document.body.style.userSelect = 'none'; document.body.style.cursor = 'col-resize'
}
function onMouseMove(e) {
  if (!isResizing) return
  leftWidth.value = Math.max(280, Math.min(900, resizeStartW + (e.clientX - resizeStartX)))
}
function onMouseUp() {
  if (!isResizing) return
  isResizing = false; document.body.style.userSelect = ''; document.body.style.cursor = ''
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  loadData()
})
onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  clearTimeout(persistTimer)
})

let persistTimer = null
const annotationHydrating = ref(false)

function schedulePersistReview() {
  if (annotationHydrating.value) return
  clearTimeout(persistTimer)
  persistTimer = setTimeout(async () => {
    if (!persistKey.value) return
    try {
      await saveAnnotation(persistKey.value, {
        session_id: persistKey.value,
        quiz_id: String(quiz.value?.id || route.params.quizId || ''),
        highlights: reviewHighlights.value,
        note: reviewNote.value,
      })
    } catch (e) {
      console.warn('Review annotation save failed', e)
    }
  }, 800)
}

watch([reviewNote, reviewHighlights], schedulePersistReview, { deep: true })

function onReviewToolbarChanged({ tool, color }) {
  reviewActiveTool.value = tool
  reviewHighlightColor.value = color || 'yellow'
}

function onReviewHighlightsChanged(hs) {
  reviewHighlights.value = hs
}

function questionStemPlain(q) {
  const raw = q.text || q.title || q.content || ''
  if (!raw) return ''
  if (typeof raw === 'string' && raw.includes('<')) {
    const d = document.createElement('div')
    d.innerHTML = raw
    return (d.textContent || '').trim()
  }
  return String(raw).trim()
}

// ── Data loading ──────────────────────────────────────────────────────────────
const quizTitle = computed(() => quiz.value?.title || result.value?.subject || 'Xem lại bài làm')

async function loadData() {
  loading.value = true
  try {
    const sessionId = route.params.sessionId
    const quizIdParam = route.params.quizId

    if (sessionId) {
      await practiceStore.fetchResult(sessionId)
      result.value = practiceStore.lastResult
    } else if (quizIdParam) {
      await practiceStore.fetchResultByQuiz(Number(quizIdParam))
      result.value = practiceStore.lastResult
    } else {
      result.value = practiceStore.lastResult || quizStore.result
    }

    const quizId = quizIdParam || result.value?.quiz_id
    if (quizId) {
      await quizStore.loadQuiz(Number(quizId))
    }
    quiz.value = quizStore.quiz

    const sid = String(sessionId || '')
    const qidPersist = String(quiz.value?.id || quizId || route.params.quizId || '')
    const hid = String(result.value?.id || sid || qidPersist)
    persistKey.value = String(route.query.annotationSession || `review_${qidPersist}_${hid}`)

    annotationHydrating.value = true
    try {
      try {
        const ann = await getAnnotation(persistKey.value)
        reviewHighlights.value = ann.highlights || []
        reviewNote.value = ann.note || ''
      } catch {
        reviewHighlights.value = []
        reviewNote.value = ''
      }
    } finally {
      await nextTick()
      annotationHydrating.value = false
    }
  } finally {
    loading.value = false
  }
}

// ── Score stats ───────────────────────────────────────────────────────────────
const correctCount = computed(() => Number(result.value?.score ?? result.value?.correct ?? 0))
const totalCount   = computed(() => Number(result.value?.total_questions ?? result.value?.total ?? 0))
const wrongCount   = computed(() => totalCount.value - correctCount.value)
const overallPct   = computed(() => totalCount.value ? Math.round((correctCount.value / totalCount.value) * 100) : 0)

const partScores = computed(() => {
  if (!quiz.value?.parts?.length) return []
  return quiz.value.parts.map((part, idx) => {
    const allQs = (part.question_sets || []).flatMap(qs => qs.questions || [])
    const total = allQs.length
    const correct = allQs.filter(q => {
      const ua = userAnswers.value[String(q.id)]
      return ua?.isCorrect
    }).length
    return { idx, total, correct, pct: total ? Math.round((correct / total) * 100) : 0 }
  })
})

// ── Parts & paragraphs ────────────────────────────────────────────────────────
const parts = computed(() => quiz.value?.parts || [])
const activePart = computed(() => parts.value[activePartIdx.value] || null)

const activeParagraphs = computed(() => {
  if (!activePart.value) return []
  return buildParagraphsFromVocabs(activePart.value.vocabs || [])
})

// ── Answer highlights in passage ──────────────────────────────────────────────
const activeAnswerHighlights = computed(() => {
  if (!activePart.value) return []
  const out = []
  for (const qs of activePart.value.question_sets || []) {
    for (const q of qs.questions || []) {
      const loc = q.locate_info?.paragraph_ranges?.[0]
      if (!loc) continue
      const answers = q.correct_answers || (q.correct_answer ? [q.correct_answer] : [])
      answers.forEach((ans) => {
        if (ans) out.push({ questionOrder: q.order, text: ans, paragraphIdx: loc.start?.paragraph ?? 0 })
      })
    }
  }
  return out
})

// ── Sections with Q&A ─────────────────────────────────────────────────────────
const userAnswers = computed(() => {
  if (!result.value) return {}
  const details = result.value.details || result.value.detailed || []
  const map = {}
  if (details.length) {
    details.forEach((d) => {
      map[String(d.question_id || d.questionId)] = {
        userAnswer: d.user_answer ?? d.userAnswer,
        isCorrect: Boolean(d.is_correct ?? d.isCorrect),
      }
    })
    return map
  }

  const answers = result.value.answers || {}
  for (const part of quiz.value?.parts || []) {
    for (const qs of part.question_sets || []) {
      for (const q of qs.questions || []) {
        const qid = String(q.id)
        const ua = answers[qid]
        const hasAnswer = ua !== undefined && ua !== null && ua !== ''
        map[qid] = {
          userAnswer: ua,
          isCorrect: hasAnswer ? isCorrectAnswer({ question: q, userAnswer: ua }) : false,
        }
      }
    }
  }
  return map
})

const sections = computed(() => {
  if (!activePart.value) return []
  const listening = isListeningQuiz.value

  const mapOne = (q) => {
    const ua = userAnswers.value[String(q.id)] || {}
    const explainHtml = listening
      ? buildListeningExplainHtml(q, activePart.value.vocabs || [])
      : (q.explain || q.explanation || '')
    const canExplain = listening
      ? hasListeningExplain(q, activePart.value.vocabs || [])
      : Boolean(stripHtml(explainHtml))
    return {
      id: q.id,
      order: q.order,
      text: q.text || q.title || q.content || '',
      stemText: questionStemPlain(q),
      correctAnswers: q.correct_answers || (q.correct_answer ? [q.correct_answer] : []),
      correctAnswer: q.correct_answer,
      userAnswer: ua.userAnswer,
      isCorrect: ua.isCorrect ?? false,
      explain: explainHtml,
      canExplain,
      locateInfo: q.locate_info || null,
    }
  }

  return (activePart.value.question_sets || []).map((qs) => {
    const isGap = String(qs.question_type || '').toUpperCase() === 'GAP_FILLING'
    if (isGap) {
      const sorted = [...(qs.questions || [])].sort((a, b) => (a.sort ?? 0) - (b.sort ?? 0))
      const gapMap = {}
      sorted.forEach((qq, idx) => {
        gapMap[`gf_${idx + 1}`] = {
          questionId: qq.id,
          value: String(userAnswers.value[String(qq.id)]?.userAnswer ?? ''),
        }
      })
      return {
        kind: 'gap',
        title: qs.title || '',
        description: qs.description || '',
        content: qs.content || '',
        gapMap,
        questions: sorted.map(mapOne),
      }
    }
    return {
      kind: 'items',
      title: qs.title || '',
      description: qs.description || '',
      questions: (qs.questions || []).map(mapOne),
    }
  })
})

function getAnswerDisplay(q) {
  return q.userAnswer ?? null
}

// ── Explanation popup ─────────────────────────────────────────────────────────
function toggleExplain(q) {
  if (activeExplainId.value === q.id) {
    explainPopup.value.visible = false
    activeExplainId.value = null
    return
  }
  activeExplainId.value = q.id
  explainPopup.value = {
    visible: true,
    html: q.explain,
    questionOrder: q.order,
    listenFrom: resolveListenTimestamp(q, activeParagraphs.value),
  }
  scrollToAnswer(q)
}

function goToExplainAudio() {
  const t = Number(explainPopup.value.listenFrom)
  if (!Number.isFinite(t) || !reviewAudioRef.value) return
  reviewAudioRef.value.currentTime = t
  reviewAudioRef.value.play?.().catch(() => {})
}

function formatSeconds(sec) {
  if (!Number.isFinite(sec) || sec < 0) return '00:00'
  const total = Math.floor(sec)
  const mm = String(Math.floor(total / 60)).padStart(2, '0')
  const ss = String(total % 60).padStart(2, '0')
  return `${mm}:${ss}`
}

function scrollToAnswer(q) {
  const loc = q.locateInfo?.paragraph_ranges?.[0]
  if (!loc) return
  const paraIdx = loc.start?.paragraph
  if (paraIdx == null) return
  const el = document.querySelector(`[data-para="${paraIdx}"]`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<style scoped>
/* ── Score summary ─────────────────────────────────────────────────── */
.score-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.score-ring-wrap {
  position: relative;
  flex-shrink: 0;
  width: 80px; height: 80px;
}
.score-ring-label {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.score-stats {
  display: flex; gap: 12px; flex-shrink: 0;
}
.score-stat {
  display: flex; flex-direction: column; align-items: center;
  gap: 2px; padding: 8px 14px;
  border: 1.5px solid #e2e8f0; border-radius: 10px;
  background: #f8fafc; min-width: 60px;
}
.score-stat--correct { border-color: #34d399; background: #f0fdf4; }
.score-stat--wrong   { border-color: #f43f5e; background: #fff1f2; }
.score-stat svg { color: #94a3b8; }
.score-stat--correct svg { color: #15803d; }
.score-stat--wrong svg   { color: #e11d48; }
.score-stat-num { font-size: 20px; font-weight: 800; color: #0f172a; }
.score-stat-lbl { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }
.score-stat--correct .score-stat-num { color: #15803d; }
.score-stat--wrong   .score-stat-num { color: #e11d48; }

.part-bars { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 160px; }
.part-bar-item { display: flex; align-items: center; gap: 10px; }
.part-bar-label { font-size: 11px; font-weight: 600; color: #64748b; white-space: nowrap; min-width: 70px; }
.part-bar-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.part-bar-fill  { height: 100%; border-radius: 99px; transition: width 1s ease; }
.part-bar-pct   { font-size: 11px; font-weight: 700; color: #374151; min-width: 36px; text-align: right; }

/* ── Header ────────────────────────────────────────────────────────── */
.review-back-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--ink3); background: none; border: none; cursor: pointer;
  padding: 6px 10px; border-radius: 8px; transition: all .15s;
}
.review-back-btn:hover { background: var(--bg2); color: var(--ink); }

.review-score-badge {
  display: flex; flex-direction: column; align-items: center;
  border: 1px solid var(--border); border-radius: 12px;
  padding: 6px 16px; background: var(--bg);
}
.review-tools-rail {
  position: sticky;
  top: 120px;
  align-self: flex-start;
}

/* ── Question cards ──────────────────────────────────────────────── */
.review-question-card {
  border: 1.5px solid var(--border);
  border-radius: 12px; overflow: hidden; background: #fff;
  transition: border-color .15s;
}
.review-question-card--correct { border-left: 4px solid #34d399; }
.review-question-card--wrong   { border-left: 4px solid #f43f5e; }

.review-q-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-bottom: 1px solid var(--border);
}
.review-q-num { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ink3); letter-spacing: .06em; }
.review-q-badge {
  margin-left: auto;
  border-radius: 99px; padding: 2px 10px;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
}
.badge-correct { background: #d1fae5; color: #065f46; }
.badge-wrong   { background: #ffe4e6; color: #be123c; }

.review-explain-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 8px; border: 1px solid #15803d;
  background: #f0fdf4; color: #15803d; font-size: 11px; font-weight: 600; cursor: pointer;
  transition: all .15s;
}
.review-explain-btn:hover, .review-explain-btn.active { background: #15803d; color: #fff; }

.review-q-text {
  padding: 10px 14px; font-size: 13px; color: var(--ink); line-height: 1.6;
  border-bottom: 1px solid var(--border);
}
.review-q-stem {
  white-space: pre-wrap;
}

.review-answers { padding: 10px 14px; }
.review-answer-row {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 4px 0; font-size: 12px;
}
.review-answer-row--border { border-top: 1px solid var(--border); padding-top: 8px; margin-top: 4px; }
.review-answer-label { color: var(--ink3); }
.review-answer-val { font-weight: 700; font-family: monospace; }
.val-correct { color: #059669; }
.val-wrong   { color: #e11d48; }

/* ── Explanation popup ────────────────────────────────────────────── */
.explain-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,.35);
  display: flex; align-items: flex-start; justify-content: flex-end;
  padding: 80px 16px 16px;
}
.explain-box {
  width: 460px; max-height: calc(100vh - 100px);
  background: #fff; border-radius: 20px;
  box-shadow: 0 24px 80px rgba(0,0,0,.18);
  display: flex; flex-direction: column; overflow: hidden;
}
.explain-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.explain-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.explain-goto-btn {
  border: 1px solid #34d399;
  background: #ecfdf5;
  color: #047857;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
}
.explain-close {
  background: none; border: none; cursor: pointer;
  color: var(--ink3); padding: 4px; border-radius: 6px;
}
.explain-close:hover { background: var(--bg2); }
.explain-body {
  flex: 1; overflow-y: auto; padding: 16px 18px;
  font-size: 13px; line-height: 1.7; color: var(--ink);
}
.explain-body :deep(u strong) { color: #15803d; }
.explain-body :deep(.list-bullet1) { padding-left: 18px; }

/* ── Transitions ─────────────────────────────────────────────────── */
.popup-fade-enter-active, .popup-fade-leave-active { transition: opacity .2s, transform .2s; }
.popup-fade-enter-from, .popup-fade-leave-to { opacity: 0; transform: translateX(20px); }
</style>
