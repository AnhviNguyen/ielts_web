<template>
  <div class="min-h-screen bg-[var(--bg)]">

    <!-- Top bar -->
    <div class="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--bg)]/95 px-6 py-3 backdrop-blur">
      <div class="mx-auto flex max-w-4xl items-center justify-between">
        <button
          class="flex items-center gap-1.5 text-sm text-[var(--ink2)] transition hover:text-[var(--ink)]"
          @click="$router.back()"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
          Quay lại
        </button>

        <div class="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="text-[var(--ink2)]"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
          <span class="text-sm font-semibold text-[var(--ink)]">Kết Quả Speaking</span>
        </div>

        <button class="ct-btn" @click="$router.back()">Luyện tập lại</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex h-64 items-center justify-center">
      <div class="flex flex-col items-center gap-3">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-[#34d399] border-t-transparent"/>
        <p class="text-sm text-[var(--ink2)]">Đang phân tích bài nói…</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="mx-auto mt-16 max-w-md rounded-xl border border-[#f43f5e44] bg-[#f43f5e08] p-8 text-center">
      <svg class="mx-auto mb-3 text-[#f43f5e]" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <p class="text-sm text-[#f43f5e]">{{ error }}</p>
      <button class="ct-btn mt-4" @click="$router.back()">Quay lại</button>
    </div>

    <!-- Attempt summary content -->
    <div v-else-if="summaryMode" class="mx-auto max-w-5xl space-y-5 px-4 py-6">
      <div class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <div class="text-sm font-bold uppercase tracking-wider text-[var(--ink2)]">Speaking Attempt Summary</div>
            <p class="mt-1 text-sm text-[var(--ink3)]">Danh sách tất cả câu đã đánh giá và điểm trung bình của lần làm này.</p>
          </div>
          <button class="ct-btn" @click="$router.push('/speaking')">Làm bài mới</button>
        </div>

        <div class="grid grid-cols-2 gap-3 md:grid-cols-5">
          <div class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3 md:col-span-1">
            <div class="text-[11px] uppercase tracking-wider text-[var(--ink3)]">Avg Band</div>
            <div class="mt-1 text-2xl font-bold text-[#34d399]">{{ Number(summaryAverage.band_estimate || 0).toFixed(2) }}</div>
          </div>
          <div class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
            <div class="text-[11px] uppercase tracking-wider text-[var(--ink3)]">GRA</div>
            <div class="mt-1 text-xl font-semibold text-[var(--ink)]">{{ Number(summaryAverage.grammar_range_accuracy_score || summaryAverage.grammar_score || 0).toFixed(2) }}<span class="text-[11px] text-[var(--ink3)]">/9</span></div>
          </div>
          <div class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
            <div class="text-[11px] uppercase tracking-wider text-[var(--ink3)]">LR</div>
            <div class="mt-1 text-xl font-semibold text-[var(--ink)]">{{ Number(summaryAverage.lexical_resource_score || summaryAverage.vocabulary_score || 0).toFixed(2) }}<span class="text-[11px] text-[var(--ink3)]">/9</span></div>
          </div>
          <div class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
            <div class="text-[11px] uppercase tracking-wider text-[var(--ink3)]">FC</div>
            <div class="mt-1 text-xl font-semibold text-[var(--ink)]">{{ Number(summaryAverage.fluency_coherence_score || summaryAverage.coherence_score || 0).toFixed(2) }}<span class="text-[11px] text-[var(--ink3)]">/9</span></div>
          </div>
          <div class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3">
            <div class="text-[11px] uppercase tracking-wider text-[var(--ink3)]">Pronunciation</div>
            <div class="mt-1 text-xl font-semibold text-[var(--ink)]">{{ Number(summaryAverage.pronunciation_total || 0).toFixed(2) }}<span class="text-[11px] text-[var(--ink3)]">/10</span></div>
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <div
          v-for="(item, idx) in summaryItems"
          :key="item.history_id || idx"
          class="card p-4"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div class="text-[11px] font-semibold uppercase tracking-wider text-[var(--ink3)]">Question {{ idx + 1 }}</div>
              <p class="mt-1 text-sm text-[var(--ink)]">{{ item.question_text || 'Speaking question' }}</p>
            </div>
            <div class="rounded-lg bg-[#34d39911] px-2.5 py-1 text-sm font-bold text-[#34d399]">
              Band {{ Number(item.band_estimate || 0).toFixed(1) }}
            </div>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-2 text-sm text-[var(--ink2)] md:grid-cols-4">
            <div>GRA: <strong class="text-[var(--ink)]">{{ Number(item.grammar_range_accuracy_score || item.grammar_score || 0).toFixed(1) }}/9</strong></div>
            <div>LR: <strong class="text-[var(--ink)]">{{ Number(item.lexical_resource_score || item.vocabulary_score || 0).toFixed(1) }}/9</strong></div>
            <div>FC: <strong class="text-[var(--ink)]">{{ Number(item.fluency_coherence_score || item.coherence_score || 0).toFixed(1) }}/9</strong></div>
            <div>Pronunciation: <strong class="text-[var(--ink)]">{{ Number(item.pronunciation_total || 0).toFixed(1) }}/10</strong></div>
          </div>
          <p v-if="displayOverallComment(item.overall_comment)" class="mt-2 text-sm text-[var(--ink2)]">{{ displayOverallComment(item.overall_comment) }}</p>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div v-else-if="result" class="mx-auto max-w-4xl space-y-5 px-4 py-6">

      <!-- Question -->
      <div v-if="question" class="card flex items-start gap-3 p-4">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="mt-0.5 shrink-0 text-[#34d399]"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <p class="text-sm text-[var(--ink)]">{{ question }}</p>
      </div>

      <!-- Row 1: Band + Pronunciation -->
      <div class="grid grid-cols-1 gap-5 md:grid-cols-2">

        <!-- Band Score card -->
        <div class="card p-6">
          <div class="mb-4 flex items-center gap-2 text-[var(--ink2)]">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>
            <span class="text-xs font-bold uppercase tracking-wider">Band Score</span>
          </div>
          <div class="flex items-center gap-6">
            <BandScoreRing :band="result.band_estimate || 0" />
            <div class="flex-1 space-y-2 text-sm text-[var(--ink2)]">
              <div class="flex justify-between">
                <span>Grammar</span>
                <span class="font-semibold text-[var(--ink)]">{{ result.grammar.score.toFixed(1) }}/9</span>
              </div>
              <div class="flex justify-between">
                <span>Vocabulary</span>
                <span class="font-semibold text-[var(--ink)]">{{ result.vocabulary.score.toFixed(1) }}/9</span>
              </div>
              <div class="flex justify-between">
                <span>Pronunciation</span>
                <span class="font-semibold text-[var(--ink)]">{{ result.pronunciation.total.toFixed(1) }}/10</span>
              </div>
            </div>
          </div>
          <div class="mt-5">
            <AudioPlayer :audio-url="audioUrl" />
          </div>
        </div>

        <!-- Pronunciation Scores -->
        <div class="card p-6">
          <div class="mb-4 flex items-center gap-2 text-[var(--ink2)]">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
            <span class="text-xs font-bold uppercase tracking-wider">Phát âm</span>
          </div>
          <div class="grid grid-cols-2 gap-y-5 gap-x-4">
            <CircularScore :score="result.pronunciation.accuracy" label="Accuracy" />
            <CircularScore :score="result.pronunciation.fluency"  label="Fluency"  />
            <CircularScore :score="result.pronunciation.prosodic" label="Prosodic"  />
            <CircularScore :score="result.pronunciation.total"    label="Total" :size="96" />
          </div>
        </div>
      </div>

      <!-- 4 IELTS criteria -->
      <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div
          v-for="c in criteriaCards"
          :key="c.key"
          class="card p-4"
        >
          <div class="flex items-center justify-between">
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">{{ c.label }}</div>
            <span
              class="rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
              :style="{ borderColor: scoreColor(c.score) + '55', color: scoreColor(c.score), background: scoreColor(c.score) + '11' }"
            >
              {{ Number(c.score || 0).toFixed(1) }}/9
            </span>
          </div>
          <p class="mt-2 text-sm text-[var(--ink3)]">{{ c.hint }}</p>
        </div>
      </div>

      <!-- Transcript -->
      <TranscriptHighlight
        :transcript="result.transcript"
        :word-timestamps="result.word_timestamps"
      />

      <!-- Grammar + Vocabulary -->
      <div class="grid grid-cols-1 gap-5 md:grid-cols-2">
        <GrammarCard
          :transcript="result.transcript"
          :question-text="question"
          :score="result.grammar?.score || 0"
          :errors="result.grammar?.errors || []"
          :evaluate-result="result"
        />
        <VocabCard
          :transcript="result.transcript"
          :question-text="question"
          :score="result.vocabulary?.score || 0"
          :feedback="result.vocabulary?.feedback || []"
          :evaluate-result="result"
        />
      </div>

      <!-- Band boost tips -->
      <div class="card p-5">
        <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[#0ea5e9]">Band Boost Tips</div>
        <ul class="space-y-1.5">
          <li
            v-for="(tip, i) in bandBoostTips"
            :key="`tip_${i}`"
            class="flex items-start gap-2 text-sm text-[var(--ink)]"
          >
            <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#0ea5e9]"/>
            {{ tip }}
          </li>
          <li v-if="!bandBoostTips.length" class="text-sm text-[var(--ink3)]">—</li>
        </ul>
      </div>

      <!-- Upgraded sample answer -->
      <div v-if="upgradedSampleAnswer" class="card border-l-4 border-l-[#6366f1] p-5">
        <div class="mb-2 text-xs font-bold uppercase tracking-wider text-[#6366f1]">Bài nói nâng band (sample)</div>
        <p class="whitespace-pre-line text-sm leading-relaxed text-[var(--ink)]">{{ upgradedSampleAnswer }}</p>
      </div>

      <!-- Strengths + Improvements -->
      <div class="grid grid-cols-1 gap-5 md:grid-cols-2">
        <!-- Strengths -->
        <div class="card p-5">
          <div class="mb-3 flex items-center gap-2 text-[#34d399]">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
            <span class="text-xs font-bold uppercase tracking-wider">Điểm mạnh</span>
          </div>
          <ul class="space-y-1.5">
            <li v-for="(s, i) in result.strengths" :key="i"
              class="flex items-start gap-2 text-sm text-[var(--ink)]">
              <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#34d399]"/>
              {{ s }}
            </li>
            <li v-if="!result.strengths?.length" class="text-sm text-[var(--ink3)]">—</li>
          </ul>
        </div>

        <!-- Improvements -->
        <div class="card p-5">
          <div class="mb-3 flex items-center gap-2 text-[#f59e0b]">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span class="text-xs font-bold uppercase tracking-wider">Cần cải thiện</span>
          </div>
          <ul class="space-y-1.5">
            <li v-for="(imp, i) in result.improvements" :key="i"
              class="flex items-start gap-2 text-sm text-[var(--ink)]">
              <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f59e0b]"/>
              {{ imp }}
            </li>
            <li v-if="!result.improvements?.length" class="text-sm text-[var(--ink3)]">—</li>
          </ul>
        </div>
      </div>

      <!-- Overall Comment -->
      <div v-if="displayOverallComment(result.overall_comment)" class="card border-l-4 border-l-[#34d399] p-5">
        <div class="mb-2 flex items-center gap-2 text-[#34d399]">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="text-xs font-bold uppercase tracking-wider">Nhận xét chung</span>
        </div>
        <p class="text-sm leading-relaxed text-[var(--ink)]">{{ displayOverallComment(result.overall_comment) }}</p>
      </div>

      <!-- Pipeline error notices -->
      <div v-if="result.pron_error || result.whisper_error || result.ai_error" class="space-y-2">
        <div v-if="result.pron_error"    class="rounded-xl border border-[#f43f5e33] bg-[#f43f5e08] px-4 py-2.5 text-xs text-[#f43f5e]">
          <span class="font-semibold">Pronunciation model:</span> {{ result.pron_error }}
        </div>
        <div v-if="result.whisper_error" class="rounded-xl border border-[#f43f5e33] bg-[#f43f5e08] px-4 py-2.5 text-xs text-[#f43f5e]">
          <span class="font-semibold">Transcription:</span> {{ result.whisper_error }}
        </div>
        <div v-if="result.ai_error"      class="rounded-xl border border-[#f59e0b33] bg-[#f59e0b08] px-4 py-2.5 text-xs text-[#f59e0b]">
          <span class="font-semibold">AI analysis:</span> {{ result.ai_error }}
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import apiClient from '@/api/client.js'

import BandScoreRing       from '@/components/speaking/BandScoreRing.vue'
import CircularScore       from '@/components/speaking/CircularScore.vue'
import TranscriptHighlight from '@/components/speaking/TranscriptHighlight.vue'
import GrammarCard         from '@/components/speaking/GrammarCard.vue'
import VocabCard           from '@/components/speaking/VocabCard.vue'
import AudioPlayer         from '@/components/speaking/AudioPlayer.vue'

const result   = ref(null)
const loading  = ref(true)
const error    = ref(null)
const question = ref('')
const audioUrl = ref('')
const summary  = ref(null)

const summaryMode    = computed(() => !!summary.value)
const summaryItems   = computed(() => summary.value?.items || [])
const summaryAverage = computed(() => summary.value?.average || {})
const bandBoostTips  = computed(() => result.value?.band_boost_tips || [])
const upgradedSampleAnswer = computed(() => result.value?.upgraded_sample_answer || '')
const criteriaCards = computed(() => {
  const r = result.value || {}
  return [
    {
      key: 'fc',
      label: 'Fluency & Coherence',
      score: Number(r.fluency_coherence_score ?? r.coherence_score ?? 0),
      hint: 'Độ trôi chảy, liên kết ý và mạch logic của câu trả lời.',
    },
    {
      key: 'lr',
      label: 'Lexical Resource',
      score: Number(r.lexical_resource_score ?? r.vocabulary?.score ?? 0),
      hint: 'Độ đa dạng, chính xác của từ vựng và khả năng paraphrase.',
    },
    {
      key: 'gra',
      label: 'Grammar Range & Accuracy',
      score: Number(r.grammar_range_accuracy_score ?? r.grammar?.score ?? 0),
      hint: 'Phạm vi cấu trúc câu và độ chính xác ngữ pháp.',
    },
    {
      key: 'pron',
      label: 'Pronunciation',
      score: Number((r.pronunciation?.total ?? 0) / 10 * 9),
      hint: 'Độ rõ ràng phát âm, trọng âm và ngữ điệu để người nghe hiểu dễ.',
    },
  ]
})

function scoreColor(score) {
  if (Number(score) >= 7) return '#34d399'
  if (Number(score) >= 5) return '#f59e0b'
  return '#f43f5e'
}

function displayOverallComment(comment) {
  const c = (comment || '').trim()
  if (!c || /^llm analysis unavailable\.?$/i.test(c)) return ''
  return c
}

onMounted(async () => {
  const state = window.history.state || {}

  if (state.result) {
    // Single question result — from inline evaluation
    result.value   = state.result
    question.value = state.question || ''
    audioUrl.value = state.audioUrl || ''
    loading.value  = false
    return
  }

  if (state.summary) {
    // Full attempt summary — passed directly from QuizRunner submit
    summary.value  = state.summary
    question.value = state.question || ''
    loading.value  = false
    return
  }

  if (state.fetchSummary && state.quiz_id) {
    // Triggered from History page: fetch attempt summary from API
    try {
      const { data } = await apiClient.get('/speaking/attempt-summary', {
        params: { quiz_id: state.quiz_id },
      })
      summary.value  = data
      question.value = state.question || `Speaking Quiz #${state.quiz_id}`
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Không thể tải kết quả speaking.'
    } finally {
      loading.value = false
    }
    return
  }

  error.value   = 'Không tìm thấy dữ liệu kết quả. Vui lòng thử lại.'
  loading.value = false
})
</script>
