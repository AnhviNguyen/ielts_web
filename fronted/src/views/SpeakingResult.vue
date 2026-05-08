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

      <!-- Transcript -->
      <TranscriptHighlight
        :transcript="result.transcript"
        :word-timestamps="result.word_timestamps"
      />

      <!-- Grammar + Vocabulary -->
      <div class="grid grid-cols-1 gap-5 md:grid-cols-2">
        <GrammarCard :score="result.grammar.score" :errors="result.grammar.errors" />
        <VocabCard   :score="result.vocabulary.score" :feedback="result.vocabulary.feedback" />
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
      <div v-if="result.overall_comment" class="card border-l-4 border-l-[#34d399] p-5">
        <div class="mb-2 flex items-center gap-2 text-[#34d399]">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="text-xs font-bold uppercase tracking-wider">Nhận xét chung</span>
        </div>
        <p class="text-sm leading-relaxed text-[var(--ink)]">{{ result.overall_comment }}</p>
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
import { onMounted, ref } from 'vue'

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

onMounted(() => {
  const state = window.history.state || {}
  if (state.result) {
    result.value   = state.result
    question.value = state.question || ''
    audioUrl.value = state.audioUrl || ''
    loading.value  = false
  } else {
    error.value   = 'Không tìm thấy dữ liệu kết quả. Vui lòng thử lại.'
    loading.value = false
  }
})
</script>
