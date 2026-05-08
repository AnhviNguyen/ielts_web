<template>
  <div class="min-h-screen bg-[var(--bg)]">
    <!-- Exit confirm dialog -->
    <Teleport to="body">
      <div v-if="showExitConfirm" class="fixed inset-0 z-[500] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="showExitConfirm = false"></div>
        <div class="relative z-10 w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
          <div class="mb-1 text-base font-bold text-[var(--ink)]">Thoát bài thi?</div>
          <p class="mb-5 text-[13px] text-[var(--ink3)]">Tiến trình làm bài sẽ không được lưu. Bạn có chắc muốn thoát?</p>
          <div class="flex justify-end gap-2">
            <button class="ct-btn" @click="showExitConfirm = false">Tiếp tục làm</button>
            <button class="ct-btn" style="border-color:#e11d48;color:#e11d48" @click="confirmExit">Thoát</button>
          </div>
        </div>
      </div>
    </Teleport>

    <PracticeToolbar :practice-mode="practiceMode" />
    <ExamHeader
      :title="quizTitle"
      :subtitle="quizSubtitle"
      :remaining-seconds="store.remainingSeconds"
      @submit="submit(false)"
    />

    <div class="container py-5">
      <div v-if="store.loading" class="card p-6 text-center text-[var(--ink2)]">Loading…</div>
      <div v-else-if="!store.quiz" class="card p-6 text-center">
        <div class="text-lg font-semibold mb-2">Quiz not found</div>
        <RouterLink to="/dashboard" class="btn btn-primary">Về trang chủ</RouterLink>
      </div>

      <template v-else>
        <!-- Speaking evaluation overlay -->
        <Teleport to="body">
          <div v-if="evaluating" class="fixed inset-0 z-[600] flex items-center justify-center bg-black/60">
            <div class="flex flex-col items-center gap-4 rounded-2xl bg-[#0f0f1a] p-8 text-white shadow-2xl">
              <div class="h-10 w-10 animate-spin rounded-full border-4 border-[#6c63ff] border-t-transparent"/>
              <p class="text-sm font-semibold">Đang phân tích bài nói…</p>
              <p class="text-[11px] text-[#a0a0c0]">Pronunciation · Transcription · AI Feedback</p>
            </div>
          </div>
        </Teleport>

        <!-- Speaking mode -->
        <div v-if="isSpeaking">
          <!-- Sub-header: progress (practice) or nav grid (exam) + "Need help" button -->
          <div class="mb-4 flex items-center justify-between gap-3">
            <!-- Practice: pill progress indicator -->
            <div v-if="practiceMode" class="flex items-center gap-3">
              <button class="ct-btn px-3 py-1.5 text-[12px]" @click="showExitConfirm = true">
                <svg class="mr-1" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                Thoát
              </button>
              <div class="flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-white px-4 py-1.5 text-[12px]">
                <span class="font-bold text-[var(--ink)]">Question {{ currentSpeakingIdx + 1 }}</span>
                <span class="text-[var(--ink3)]">/ {{ speakingFlat.length }}</span>
              </div>
              <!-- dot progress -->
              <div class="flex gap-1">
                <div
                  v-for="(_, i) in speakingFlat" :key="i"
                  class="h-2 w-2 rounded-full transition-colors"
                  :class="i < currentSpeakingIdx ? 'bg-[#34d399]' : i === currentSpeakingIdx ? 'bg-[#111]' : 'bg-[var(--border2)]'"
                />
              </div>
            </div>
            <!-- Exam: full nav grid -->
            <QuestionNavGrid
              v-else
              :questions="navQuestions"
              :nav-parts="navParts"
              :current-order="store.currentOrder"
              :answered-map="store.answers"
              @go="goToOrder"
              class="flex-1"
            />

            <!-- "Need help" button (both modes) -->
            <button
              @click="chatOpen = !chatOpen"
              class="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-colors"
              :class="chatOpen
                ? 'border-[#34d399] bg-[#34d39911] text-[#34d399]'
                : 'border-[var(--border2)] bg-white text-[var(--ink2)] hover:border-[#34d399] hover:text-[#34d399]'"
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>
              Need help? Click here.
            </button>
          </div>

          <!-- Two-column when chat open, single-column otherwise -->
          <div
            class="flex gap-0 overflow-hidden rounded-2xl border border-[var(--border)] bg-white"
            :class="chatOpen ? 'mx-auto max-w-7xl' : 'mx-auto max-w-[96rem]'"
          >
            <!-- Questions panel -->
            <div class="flex-1 min-w-0 p-5" :class="chatOpen ? 'border-r border-[var(--border)]' : ''">

              <!-- ── PRACTICE: one question at a time ── -->
              <template v-if="practiceMode">
                <div v-if="currentSpeakingItem">
                  <!-- Part label -->
                  <div class="mb-3 text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">
                    {{ currentSpeakingItem.partTitle || `Part ${currentSpeakingIdx + 1}` }}
                  </div>
                  <QuestionRenderer
                    :item="currentSpeakingItem"
                    :answer="store.answers[currentSpeakingItem.question.id]"
                    :is-current="true"
                    @update:answer="(v) => store.setAnswer(currentSpeakingItem.question.id, v)"
                    @evaluate-speaking="onEvaluateSpeaking"
                  />
                </div>

                <!-- Prev / Next navigation -->
                <div class="mt-6 flex items-center justify-between gap-3">
                  <button
                    class="ct-btn flex items-center gap-1.5 px-4 py-2 text-[13px]"
                    :class="currentSpeakingIdx === 0 ? 'opacity-30 cursor-not-allowed' : ''"
                    :disabled="currentSpeakingIdx === 0"
                    @click="prevSpeaking"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                    Previous
                  </button>
                  <button
                    class="ct-btn flex items-center gap-1.5 px-4 py-2 text-[13px]"
                    :class="currentSpeakingIdx >= speakingFlat.length - 1 ? 'opacity-30 cursor-not-allowed' : ''"
                    :disabled="currentSpeakingIdx >= speakingFlat.length - 1"
                    @click="nextSpeaking"
                  >
                    Next
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                  </button>
                </div>

                <!-- Full speaking-result style feedback of current question -->
                <div v-if="currentSpeakingEval?.result" class="mt-5 space-y-5">
                  <div class="flex items-center justify-between">
                    <div class="text-[14px] font-semibold text-[var(--ink)]">Detailed feedback for this question</div>
                    <button
                      class="ct-btn px-3 py-1.5 text-[12px]"
                      @click="router.push({ path: '/speaking/result', state: currentSpeakingEval })"
                    >
                      Open full result page
                    </button>
                  </div>

                  <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
                    <div class="card p-6">
                      <div class="mb-4 flex items-center gap-2 text-[var(--ink2)]">
                        <span class="text-xs font-bold uppercase tracking-wider">Band Score</span>
                      </div>
                      <div class="flex items-center gap-6">
                        <BandScoreRing :band="currentSpeakingEval.result.band_estimate || 0" />
                        <div class="flex-1 space-y-2 text-sm text-[var(--ink2)]">
                          <div class="flex justify-between">
                            <span>Grammar</span>
                            <span class="font-semibold text-[var(--ink)]">{{ Number(currentSpeakingEval.result.grammar?.score || 0).toFixed(1) }}/9</span>
                          </div>
                          <div class="flex justify-between">
                            <span>Vocabulary</span>
                            <span class="font-semibold text-[var(--ink)]">{{ Number(currentSpeakingEval.result.vocabulary?.score || 0).toFixed(1) }}/9</span>
                          </div>
                          <div class="flex justify-between">
                            <span>Pronunciation</span>
                            <span class="font-semibold text-[var(--ink)]">{{ Number(currentSpeakingEval.result.pronunciation?.total || 0).toFixed(1) }}/10</span>
                          </div>
                        </div>
                      </div>
                      <div class="mt-5">
                        <AudioPlayer :audio-url="currentSpeakingEval.audioUrl" />
                      </div>
                    </div>

                    <div class="card p-6">
                      <div class="mb-4 flex items-center gap-2 text-[var(--ink2)]">
                        <span class="text-xs font-bold uppercase tracking-wider">Pronunciation</span>
                      </div>
                      <div class="grid grid-cols-2 gap-y-5 gap-x-4">
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.accuracy || 0" label="Accuracy" />
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.fluency || 0" label="Fluency" />
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.prosodic || 0" label="Prosodic" />
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.total || 0" label="Total" :size="96" />
                      </div>
                    </div>
                  </div>

                  <TranscriptHighlight
                    :transcript="currentSpeakingEval.result.transcript || ''"
                    :word-timestamps="currentSpeakingEval.result.word_timestamps || []"
                  />

                  <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
                    <GrammarCard
                      :score="Number(currentSpeakingEval.result.grammar?.score || 0)"
                      :errors="currentSpeakingEval.result.grammar?.errors || []"
                    />
                    <VocabCard
                      :score="Number(currentSpeakingEval.result.vocabulary?.score || 0)"
                      :feedback="currentSpeakingEval.result.vocabulary?.feedback || []"
                    />
                  </div>

                  <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
                    <div class="card p-5">
                      <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[#34d399]">Strengths</div>
                      <ul class="space-y-1.5">
                        <li
                          v-for="(s, i) in currentSpeakingEval.result.strengths || []"
                          :key="`st_${i}`"
                          class="flex items-start gap-2 text-sm text-[var(--ink)]"
                        >
                          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#34d399]"/>
                          {{ s }}
                        </li>
                        <li v-if="!(currentSpeakingEval.result.strengths || []).length" class="text-sm text-[var(--ink3)]">—</li>
                      </ul>
                    </div>
                    <div class="card p-5">
                      <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[#f59e0b]">Improvements</div>
                      <ul class="space-y-1.5">
                        <li
                          v-for="(imp, i) in currentSpeakingEval.result.improvements || []"
                          :key="`im_${i}`"
                          class="flex items-start gap-2 text-sm text-[var(--ink)]"
                        >
                          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f59e0b]"/>
                          {{ imp }}
                        </li>
                        <li v-if="!(currentSpeakingEval.result.improvements || []).length" class="text-sm text-[var(--ink3)]">—</li>
                      </ul>
                    </div>
                  </div>

                  <div v-if="currentSpeakingEval.result.overall_comment" class="card border-l-4 border-l-[#34d399] p-5">
                    <div class="mb-2 text-xs font-bold uppercase tracking-wider text-[#34d399]">Overall comment</div>
                    <p class="text-sm leading-relaxed text-[var(--ink)]">{{ currentSpeakingEval.result.overall_comment }}</p>
                  </div>
                </div>
              </template>

              <!-- ── EXAM: all questions at once ── -->
              <template v-else>
                <div v-for="sec in sections" :key="sec.key" class="mb-6">
                  <div class="mb-2 text-xs font-semibold text-[var(--ink2)]">{{ sec.title }}</div>
                  <div class="mb-3 text-sm text-[var(--ink2)]" v-if="sec.description" v-html="sec.description"></div>
                  <div class="grid gap-3">
                    <div
                      v-for="it in sec.items"
                      :key="it.question.id"
                      :ref="(el) => registerQuestionEl(it.question.order, el)"
                      @click="setCurrent(it.question.order)"
                    >
                      <QuestionRenderer
                        :item="it"
                        :answer="store.answers[it.question.id]"
                        :is-current="store.currentOrder === it.question.order"
                        @update:answer="(v) => store.setAnswer(it.question.id, v)"
                        @evaluate-speaking="onEvaluateSpeaking"
                      />
                    </div>
                  </div>
                </div>
                <div class="mt-6 flex items-center justify-between gap-2">
                  <button class="btn btn-secondary" @click="showExitConfirm = true">Thoát</button>
                  <button class="btn btn-primary" @click="submit(false)">Nộp bài</button>
                </div>
              </template>

              <!-- Error banner (both modes) -->
              <div v-if="evalError" class="mt-3 rounded-lg border border-[#f43f5e44] bg-[#f43f5e11] px-4 py-2 text-xs text-[#f43f5e]">
                {{ evalError }}
              </div>
            </div>

            <!-- Chatbot side panel -->
            <Transition name="slide">
              <SpeakingChatbot
                v-if="chatOpen"
                :question-text="speakingCurrentQuestion"
                @close="chatOpen = false"
              />
            </Transition>
          </div>
        </div>

        <!-- Resizable two-panel layout (Reading / Listening) -->
        <div v-else class="flex gap-4" ref="layoutEl">
          <!-- Left panel -->
          <div class="flex flex-col gap-4 min-w-0" :style="{ flex: `0 0 ${leftWidth}px`, width: leftWidth + 'px' }">
            <template v-if="isListening">
              <ExamAudioPlayer
                ref="playerRef"
                :src="audioSrc"
                :title="activePart?.title || 'Listening'"
                :subtitle="`File: ${activePart?.file_id || '—'}`"
                :seek-to="seekTo"
                @time="(t) => (currentAudioTime.value = t)"
              />
              <TranscriptPanel
                :paragraphs="activeParagraphs"
                :current-time="currentAudioTime"
                :highlighted-ids="transcript.highlightedIds.value"
                @seek="(t) => { seekTo.value = t; transcript.clearForced() }"
              />
            </template>

            <template v-else>
              <div class="card p-4">
                <div class="text-xs font-semibold text-[var(--ink2)] mb-2">{{ activePart?.title }}</div>
                <div class="reading-passage">
                  <div
                    v-for="p in activeParagraphs"
                    :key="p.paragraph"
                    class="reading-paragraph"
                    :class="isHighlightedParagraph(p.paragraph) ? 'is-highlight' : ''"
                  >
                    <span class="para-tag">{{ p.paragraph }}</span>
                    <span>{{ p.text }}</span>
                  </div>
                </div>
              </div>
            </template>

            <QuestionNavGrid
              :questions="navQuestions"
              :nav-parts="navParts"
              :current-order="store.currentOrder"
              :answered-map="store.answers"
              @go="goToOrder"
            />
          </div>

          <!-- Drag divider -->
          <div
            class="flex w-2 cursor-col-resize items-center justify-center group"
            @mousedown.prevent="startResize"
          >
            <div class="h-12 w-0.5 rounded-full bg-[var(--border2)] group-hover:bg-[#34d399] transition-colors"></div>
          </div>

          <!-- Right: question list -->
          <div class="card flex-1 overflow-auto p-4" style="max-height: calc(100vh - 140px)" ref="rightCol">
            <div v-for="sec in sections" :key="sec.key" class="mb-6">
              <div class="text-xs font-semibold text-[var(--ink2)] mb-2">{{ sec.title }}</div>
              <div class="text-sm text-[var(--ink2)] mb-3" v-if="sec.description" v-html="sec.description"></div>

              <GapFillingSet
                v-if="sec.kind === 'gap'"
                :title="sec.title"
                :description="sec.description"
                :html="sec.content"
                :questions="sec.questions"
                :answers="store.answers"
                :is-current="isAnyOrderCurrent(sec.questions)"
                @answer="({questionId, value}) => store.setAnswer(questionId, value)"
              />

              <div v-else class="grid gap-3">
                <div
                  v-for="it in sec.items"
                  :key="it.question.id"
                  :ref="(el) => registerQuestionEl(it.question.order, el)"
                  @click="setCurrent(it.question.order)"
                >
                  <QuestionRenderer
                    :item="it"
                    :answer="store.answers[it.question.id]"
                    :is-current="store.currentOrder === it.question.order"
                    @update:answer="(v) => store.setAnswer(it.question.id, v)"
                    @jump-audio="onJumpAudio"
                  />
                </div>
              </div>
            </div>

            <div class="mt-6 flex items-center justify-between gap-2">
              <button class="btn btn-secondary" @click="showExitConfirm = true">Thoát</button>
              <button class="btn btn-primary" @click="submit(false)">Nộp bài</button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ExamHeader from '@/components/mock-tests/ExamHeader.vue'
import ExamAudioPlayer from '@/components/mock-tests/ExamAudioPlayer.vue'
import TranscriptPanel from '@/components/mock-tests/TranscriptPanel.vue'
import QuestionNavGrid from '@/components/mock-tests/QuestionNavGrid.vue'
import QuestionRenderer from '@/components/mock-tests/QuestionRenderer.vue'
import GapFillingSet from '@/components/mock-tests/GapFillingSet.vue'
import PracticeToolbar from '@/components/mock-tests/PracticeToolbar.vue'
import SpeakingChatbot from '@/components/speaking/SpeakingChatbot.vue'
import BandScoreRing from '@/components/speaking/BandScoreRing.vue'
import CircularScore from '@/components/speaking/CircularScore.vue'
import TranscriptHighlight from '@/components/speaking/TranscriptHighlight.vue'
import GrammarCard from '@/components/speaking/GrammarCard.vue'
import VocabCard from '@/components/speaking/VocabCard.vue'
import AudioPlayer from '@/components/speaking/AudioPlayer.vue'
import { useMockQuizStore } from '@/stores/mockQuiz.js'
import { usePracticeStore } from '@/stores/practice.js'
import { buildAudioSrc } from '@/utils/audio.js'
import { buildParagraphsFromVocabs, extractParagraphSpans, isListeningQuiz } from '@/utils/mockQuiz.js'
import { scoreQuiz } from '@/utils/scoring.js'
import { useTranscript } from '@/composables/useTranscript.js'

const route = useRoute()
const router = useRouter()
const store = useMockQuizStore()
const practiceStore = usePracticeStore()
const practiceMode = computed(() => route.query.mode === 'practice')

// ─── Speaking evaluation + chatbot ───
const evaluating = ref(false)
const evalError  = ref(null)
const chatOpen   = ref(false)
const lastSpeakingEval = ref(null)
const speakingEvalByQuestion = ref({})

async function onEvaluateSpeaking({ blob, questionText }) {
  evaluating.value = true
  evalError.value  = null
  try {
    const formData = new FormData()
    formData.append('file', blob, 'recording.webm')
    formData.append('question_text', questionText)

    const res = await fetch('/api/speaking/evaluate', { method: 'POST', body: formData })
    if (!res.ok) throw new Error(`Server error ${res.status}`)
    const result = await res.json()

    const audioUrl = URL.createObjectURL(blob)

    // Practice flow: stay on QuizRunner, save result, move to next question.
    if (practiceMode.value) {
      const qid = String(currentSpeakingItem.value?.question?.id ?? '')
      const payload = { result, audioUrl, question: questionText, questionId: qid }
      lastSpeakingEval.value = payload
      if (qid) speakingEvalByQuestion.value[qid] = payload
      if (currentSpeakingIdx.value < speakingFlat.value.length - 1) nextSpeaking()
      return
    }

    // Exam flow: keep existing behavior (navigate to result page)
    router.push({
      path: '/speaking/result',
      state: { result, audioUrl, question: questionText },
    })
  } catch (err) {
    evalError.value = err.message || 'Evaluation failed. Please try again.'
  } finally {
    evaluating.value = false
  }
}

const questionEls = new Map()
const rightCol = ref(null)
const layoutEl  = ref(null)
const playerRef = ref(null)   // template ref to ExamAudioPlayer

const currentAudioTime = ref(0)
const seekTo = ref(null)

// ─── Exit confirmation ───
const showExitConfirm = ref(false)
function confirmExit() { showExitConfirm.value = false; router.push('/dashboard') }

const handleBeforeUnload = (e) => { e.preventDefault(); e.returnValue = '' }

// ─── Resizable layout ───
const leftWidth = ref(580)
let isResizing = false
let resizeStartX = 0
let resizeStartW = 0

function startResize(e) {
  isResizing = true
  resizeStartX = e.clientX
  resizeStartW = leftWidth.value
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
}
function onMouseMove(e) {
  if (!isResizing) return
  const delta = e.clientX - resizeStartX
  const containerW = layoutEl.value?.clientWidth || 1200
  leftWidth.value = Math.max(280, Math.min(containerW - 340, resizeStartW + delta))
}
function onMouseUp() {
  if (!isResizing) return
  isResizing = false
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}

const isListening = computed(() => isListeningQuiz(store.quiz))
const isSpeaking  = computed(() => store.flat.some(x => String(x.questionSetType || '').toLowerCase() === 'speaking'))

// ── Speaking practice: one question at a time ─────────────────────────────
const speakingFlat = computed(() =>
  store.flat.filter((x) => {
    const q = x.question || {}
    const t1 = String(x.questionSetType || '').toLowerCase()
    const t2 = String(q.question_type || '').toLowerCase()
    const t3 = String(q.type || '').toLowerCase()
    return t1 === 'speaking' || t2 === 'speaking' || t3 === 'speaking'
  })
)
const speakingPracticeIndex = ref(0)
const currentSpeakingIdx = computed(() => {
  const max = Math.max(0, speakingFlat.value.length - 1)
  return Math.min(Math.max(0, speakingPracticeIndex.value), max)
})
const currentSpeakingItem = computed(() => speakingFlat.value[currentSpeakingIdx.value] ?? null)
const currentSpeakingEval = computed(() => {
  const qid = String(currentSpeakingItem.value?.question?.id ?? '')
  return qid ? speakingEvalByQuestion.value[qid] : null
})

function prevSpeaking() {
  const idx = currentSpeakingIdx.value - 1
  if (idx < 0) return
  speakingPracticeIndex.value = idx
  const prev = speakingFlat.value[idx]
  if (prev?.question?.order != null) goToOrder(prev.question.order)
}
function nextSpeaking() {
  const idx = currentSpeakingIdx.value + 1
  if (idx >= speakingFlat.value.length) return
  speakingPracticeIndex.value = idx
  const next = speakingFlat.value[idx]
  if (next?.question?.order != null) goToOrder(next.question.order)
}

// The text of the currently-active speaking question (fed to chatbot)
const speakingCurrentQuestion = computed(() => {
  const item = practiceMode.value ? currentSpeakingItem.value : store.currentItem
  if (!item) return ''
  const q = item.question || {}
  return q.text || q.title || q.content || ''
})

const quizTitle = computed(() => store.quiz?.title || `Quiz #${route.params.quizId}`)
const quizSubtitle = computed(() => {
  const skill = isListening.value ? 'Listening' : isSpeaking.value ? 'Speaking' : 'Reading'
  return `${skill} · ${store.totalQuestions} câu`
})

const navQuestions = computed(() => store.flat.map((x) => ({ order: x.question.order, id: x.question.id })))

const navParts = computed(() => {
  const parts = store.quiz?.parts || []
  return parts.map((p, i) => {
    const qs = store.flat.filter(x => x.partId === p.id).map(x => ({ order: x.question.order, id: x.question.id }))
    const label = `Part ${p.passage || (i + 1)}`
    return { id: p.id, label, questions: qs }
  })
})

const activePart = computed(() => {
  const pid = store.currentItem?.partId
  return store.quiz?.parts?.find((p) => p.id === pid) || store.quiz?.parts?.[0] || null
})

const activeParagraphs = computed(() => buildParagraphsFromVocabs(activePart.value?.vocabs || []))

const audioSrc = computed(() => buildAudioSrc(activePart.value?.file_id))

// ── transcript composable ────────────────────────────────────────────────
const transcript = useTranscript(activeParagraphs, currentAudioTime)

const currentLocateInfo = computed(() => store.currentItem?.question?.locate_info)
const highlightSpans = computed(() => extractParagraphSpans(currentLocateInfo.value))

function isHighlightedParagraph(paragraph) {
  if (!highlightSpans.value.length) return false
  return highlightSpans.value.some((r) => paragraph >= r.startParagraph && paragraph <= r.endParagraph)
}

function registerQuestionEl(order, el) {
  if (!order || !el) return
  const dom = el?.$el ?? el
  questionEls.set(order, dom)
}

function scrollToOrder(order) {
  const el = questionEls.get(order)
  if (!el) return
  if (typeof el.scrollIntoView === 'function') el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function setCurrent(order) {
  store.gotoOrder(order)
}

async function goToOrder(order) {
  store.gotoOrder(order)
  await nextTick()
  scrollToOrder(order)
}

function isAnyOrderCurrent(questions) {
  const orders = new Set((questions || []).map((q) => q.order))
  return orders.has(store.currentOrder)
}

/**
 * Called when the user clicks the green play button on a question.
 * @param {{ time: number, locateInfo: object }} payload
 */
function onJumpAudio({ time, locateInfo } = {}) {
  if (Number.isFinite(time)) {
    playerRef.value?.seekAndPlay(time)
  }
  if (locateInfo) {
    transcript.activateLocateInfo(locateInfo)
  }
}

const sections = computed(() => {
  const parts = store.quiz?.parts || []
  const out = []
  for (const part of parts) {
    for (const qs of part.question_sets || []) {
      const key = `${part.id}_${qs.id}`
      if (qs.question_type === 'GAP_FILLING') {
        out.push({
          key,
          kind: 'gap',
          title: qs.title || `Part ${part.passage}`,
          description: qs.description || '',
          content: qs.content || '',
          questions: (qs.questions || []).map((q) => ({ id: q.id, sort: q.sort, order: q.order })),
        })
        continue
      }
      const items = store.flat.filter((x) => x.partId === part.id && x.questionSetId === qs.id)
      out.push({
        key,
        kind: 'items',
        title: qs.title || `Part ${part.passage}`,
        description: qs.description || '',
        items,
      })
    }
  }
  return out
})

async function submit(auto) {
  store.submit({ auto })
  const currentSession = practiceStore.currentSession
  const sessionQuizId = currentSession?.quiz?.id
  const routeQuizId = Number(route.params.quizId)
  const subject = isListening.value ? 'listening' : 'reading'

  // Real backend flow when this quiz was started via /practice/*/session.
  if (currentSession?.session_id && Number(sessionQuizId) === routeQuizId) {
    const normalizedAnswers = Object.entries(store.answers || {}).reduce((acc, [k, v]) => {
      acc[String(k)] = v
      return acc
    }, {})
    const submitted = await practiceStore.submitSession(
      subject,
      currentSession.session_id,
      normalizedAnswers
    )
    if (submitted) {
      router.push(`/results/${currentSession.session_id}`)
      return
    }
  }

  // Fallback for legacy mock-test flow.
  const scored = scoreQuiz({ quiz: store.quiz, flat: store.flat, answers: store.answers })
  store.result = {
    quizId: routeQuizId,
    title: store.quiz?.title,
    correct: scored.correct,
    total: scored.total,
    estimatedBand: scored.estimatedBand,
    detailed: scored.detailed,
    answers: store.answers,
  }
  router.push(`/quiz/${route.params.quizId}/result`)
}

watch(
  () => store.remainingSeconds,
  (s) => {
    if (s === 0 && store.quiz && !store.result) submit(true)
  }
)

watch(
  [() => speakingFlat.value, () => store.currentOrder, () => practiceMode.value],
  () => {
    if (!practiceMode.value || !speakingFlat.value.length) return
    const idx = speakingFlat.value.findIndex(
      (x) => String(x.question?.order) === String(store.currentOrder)
    )
    if (idx >= 0) speakingPracticeIndex.value = idx
  },
  { immediate: true, deep: false }
)

onMounted(async () => {
  await store.loadQuiz(route.params.quizId)
  await nextTick()
  scrollToOrder(store.currentOrder)
  window.addEventListener('beforeunload', handleBeforeUnload)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onUnmounted(() => {
  store.stopTimer()
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateX(20px); }

.reading-passage {
  max-height: 420px;
  overflow: auto;
  padding-right: 8px;
}
.reading-paragraph {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  margin-bottom: 10px;
  background: var(--surface);
}
.reading-paragraph.is-highlight {
  border-color: rgba(124, 106, 247, 0.35);
  background: rgba(124, 106, 247, 0.08);
}
.para-tag {
  min-width: 28px;
  height: 22px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--ink2);
  border: 1px solid var(--border2);
  background: var(--bg);
}
</style>

