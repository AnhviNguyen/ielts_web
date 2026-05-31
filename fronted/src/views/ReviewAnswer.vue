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
    <AppLoading v-if="loading" class="pt-24" message="Đang tải..." />

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
            <div
              v-for="ps in partScores"
              :key="ps.idx"
              class="part-bar-item part-bar-item--clickable"
              :class="{ 'part-bar-item--active': activePartIdx === ps.idx }"
              role="button"
              tabindex="0"
              @click="switchReviewPart(ps.idx)"
              @keydown.enter="switchReviewPart(ps.idx)"
            >
              <div class="part-bar-label">{{ partLabel }} {{ ps.idx + 1 }}</div>
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

            <!-- Part / Passage tabs (Reading + Listening) -->
            <div v-if="parts.length > 1" class="card flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
              <div class="text-xs font-semibold text-[var(--ink2)]">
                {{ activePart?.title || `${partLabel} ${activePartIdx + 1}` }}
              </div>
              <div class="flex flex-wrap gap-1">
                <button
                  v-for="(p, i) in parts"
                  :key="p.id"
                  type="button"
                  class="rounded-lg px-3 py-1 text-[11px] font-semibold transition-colors"
                  :class="activePartIdx === i ? 'bg-[#15803d] text-white' : 'bg-[var(--bg2)] text-[var(--ink2)] hover:bg-[var(--border)]'"
                  @click="switchReviewPart(i)"
                >
                  {{ partLabel }} {{ i + 1 }}
                </button>
              </div>
            </div>

            <!-- Listening: audio + synced transcript -->
            <template v-if="isListeningQuiz">
              <ExamAudioPlayer
                :key="`review-audio-${activePartIdx}-${reviewAudioSrc}`"
                ref="reviewAudioRef"
                :src="reviewAudioSrc"
                :title="activePart?.title || `${partLabel} ${activePartIdx + 1}`"
                :subtitle="reviewAudioSrc ? '' : 'Audio không khả dụng'"
                :seek-to="seekTo"
                @time="onReviewAudioTime"
              />
              <TranscriptPanel
                :key="`review-transcript-${activePartIdx}`"
                class="card"
                :paragraphs="activeParagraphs"
                :current-time="currentAudioTime"
                :highlighted-ids="transcript.highlightedIds.value"
                @seek="onTranscriptSeek"
              />
            </template>

            <div v-else class="card overflow-hidden">
              <div class="overflow-y-auto px-4 py-4" style="max-height: calc(100vh - 260px)">
                <ReadingPassage
                  :key="`review-${activePartIdx}`"
                  ref="reviewPassageRef"
                  :paragraphs="activeParagraphs"
                  :active-tool="reviewActiveTool"
                  :highlight-color="reviewHighlightColor"
                  :review-mode="true"
                  :answer-highlights="activeAnswerHighlights"
                  :session-highlights="reviewHighlights"
                  source-type="reading"
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
                <div v-if="sec.description" class="mb-3 text-[13px] text-[var(--ink2)]" v-html="sanitizeHtml(sec.description)"></div>
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
                <div v-if="sec.description" class="mb-3 text-[13px] text-[var(--ink2)]" v-html="sanitizeHtml(sec.description)"></div>
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
                <button
                  v-else-if="explainPopup.hasLocate && !isListeningQuiz"
                  type="button"
                  class="explain-goto-btn"
                  @click="goToExplainPassage()"
                >
                  Go to
                </button>
                <button class="explain-close" @click="explainPopup.visible = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>
            <div class="explain-body" v-html="sanitizeHtml(explainPopup.html)"></div>
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
import ExamAudioPlayer from '@/components/mock-tests/ExamAudioPlayer.vue'
import TranscriptPanel from '@/components/mock-tests/TranscriptPanel.vue'
import AppLoading from '@/components/ui/AppLoading.vue'
import { useTranscript } from '@/composables/useTranscript.js'
import { sanitizeHtml } from '@/utils/sanitizeHtml.js'

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

const explainPopup = ref({ visible: false, html: '', questionOrder: 0, listenFrom: null, hasLocate: false })
const explainLocateRef = ref(null)

// ── Listening audio (review mode) ─────────────────────────────────────────────
const reviewAudioRef   = ref(null)
const currentAudioTime = ref(0)
const seekTo = ref(null)

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

    const resultPromise = (async () => {
      if (sessionId) {
        await practiceStore.fetchResult(sessionId)
        return practiceStore.lastResult
      }
      if (quizIdParam) {
        await practiceStore.fetchResultByQuiz(Number(quizIdParam))
        return practiceStore.lastResult
      }
      return practiceStore.lastResult || quizStore.result
    })()

    const provisional = practiceStore.lastResult || quizStore.result
    const quizIdEarly = Number(quizIdParam || provisional?.quiz_id || 0)
    const needQuiz = quizIdEarly && Number(quizStore.quiz?.id) !== quizIdEarly
    const quizPromise = needQuiz ? quizStore.loadQuiz(quizIdEarly) : Promise.resolve()

    const [res] = await Promise.all([resultPromise, quizPromise])
    result.value = res

    const quizId = Number(quizIdParam || result.value?.quiz_id || 0)
    if (quizId && Number(quizStore.quiz?.id) !== quizId) {
      await quizStore.loadQuiz(quizId)
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
const partLabel = computed(() => (isListeningQuiz.value ? 'Part' : 'Passage'))

function switchReviewPart(idx) {
  if (idx < 0 || idx >= parts.value.length) return
  if (idx === activePartIdx.value) return
  activePartIdx.value = idx
  activeExplainId.value = null
  explainPopup.value.visible = false
  currentAudioTime.value = 0
  seekTo.value = 0
  transcript.clearForced()
  nextTick(() => {
    seekTo.value = null
  })
}

watch(activePartIdx, () => {
  currentAudioTime.value = 0
  transcript.clearForced()
})

const activeParagraphs = computed(() => {
  if (!activePart.value) return []
  return buildParagraphsFromVocabs(activePart.value.vocabs || [])
})

const transcript = useTranscript(activeParagraphs, currentAudioTime)

function onReviewAudioTime(t) {
  currentAudioTime.value = t
}

function onTranscriptSeek(t) {
  seekTo.value = t
  transcript.clearForced()
}

const detailByQid = computed(() => {
  const details = result.value?.details || result.value?.detailed || []
  const map = {}
  for (const d of details) {
    map[String(d.question_id ?? d.questionId)] = d
  }
  return map
})

// ── Answer highlights in passage ──────────────────────────────────────────────
const activeAnswerHighlights = computed(() => {
  if (!activePart.value) return []
  const out = []
  for (const qs of activePart.value.question_sets || []) {
    for (const q of qs.questions || []) {
      const det = detailByQid.value[String(q.id)] || {}
      const loc = det.locate_info?.paragraph_ranges?.[0] || q.locate_info?.paragraph_ranges?.[0]
      if (!loc) continue
      const answers = det.correct_answers?.length
        ? det.correct_answers
        : (det.correct_answer ? [det.correct_answer] : (q.correct_answers || (q.correct_answer ? [q.correct_answer] : [])))
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
    const det = detailByQid.value[String(q.id)] || {}
    const qReview = {
      ...q,
      correct_answer: det.correct_answer ?? q.correct_answer,
      correct_answers: det.correct_answers ?? q.correct_answers,
      explain: det.explanation || det.explain || q.explain,
      explanation: det.explanation || det.explain || q.explanation,
      listen_from: det.listen_from ?? q.listen_from,
      locate_info: det.locate_info || q.locate_info,
    }
    const explainHtml = listening
      ? buildListeningExplainHtml(qReview, activePart.value.vocabs || [])
      : (det.explanation || det.explain || q.explain || q.explanation || '')
    const canExplain = listening
      ? hasListeningExplain(qReview, activePart.value.vocabs || [])
      : Boolean(stripHtml(explainHtml))
    const correctAnswers = det.correct_answers?.length
      ? det.correct_answers
      : (det.correct_answer ? [det.correct_answer] : (q.correct_answers || (q.correct_answer ? [q.correct_answer] : [])))
    return {
      id: q.id,
      order: q.order,
      text: q.text || q.title || q.content || '',
      stemText: questionStemPlain(q),
      correctAnswers,
      correctAnswer: det.correct_answer ?? q.correct_answer,
      userAnswer: ua.userAnswer,
      isCorrect: ua.isCorrect ?? false,
      explain: explainHtml,
      canExplain,
      locateInfo: det.locate_info || q.locate_info || null,
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
  explainLocateRef.value = q
  const listenFrom = resolveListenTimestamp(q, activeParagraphs.value)
  explainPopup.value = {
    visible: true,
    html: q.explain,
    questionOrder: q.order,
    listenFrom,
    hasLocate: Boolean(q.locateInfo?.paragraph_ranges?.length || Object.keys(q.locateInfo || {}).length),
  }
  if (isListeningQuiz.value && q.locateInfo) {
    transcript.activateLocateInfo(q.locateInfo)
    if (listenFrom != null) goToExplainAudio()
  } else {
    scrollToAnswer(q)
  }
}

function goToExplainAudio() {
  const t = Number(explainPopup.value.listenFrom)
  if (!Number.isFinite(t)) return
  seekTo.value = t
  transcript.clearForced()
  if (explainLocateRef.value?.locateInfo) {
    transcript.activateLocateInfo(explainLocateRef.value.locateInfo)
  }
}

function goToExplainPassage() {
  const q = explainLocateRef.value
  if (!q) return
  scrollToAnswer(q)
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
