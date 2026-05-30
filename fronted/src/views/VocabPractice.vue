<template>
  <div
    class="min-h-screen w-full bg-white text-slate-800 outline-none"
    tabindex="0"
  >
    <div class="flex min-h-screen w-full justify-center px-4 py-5 sm:px-8 sm:py-7">
      <div class="flex w-full max-w-5xl flex-1 flex-col">
        <!-- Header -->
        <header class="mb-4 flex shrink-0 items-center gap-3">
          <button
            type="button"
            class="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 transition-colors hover:border-emerald-500 hover:text-emerald-600"
            title="Quay lại"
            @click="goBack"
          >
            <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <div class="min-w-0 flex-1">
            <h1 class="truncate text-lg font-extrabold text-slate-900">{{ topicName || 'Luyện tập' }}</h1>
            <p class="text-xs text-slate-500">Thẻ {{ cardLabel }} · SRS</p>
          </div>
          <span
            v-if="dueCount != null"
            class="shrink-0 rounded-lg bg-emerald-600 px-2.5 py-1.5 text-[11px] font-extrabold text-white"
          >
            {{ dueCount }} đến hạn
          </span>
        </header>

        <div class="mb-4 h-1 shrink-0 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-300"
            :style="{ width: `${progressPct}%` }"
          />
        </div>

        <VocabModeNav
          v-if="!loading && !completed && queue.length"
          :active-id="currentMode"
          @select="setMode"
        />

        <!-- States -->
        <div v-if="loading" class="flex flex-1 items-center justify-center text-slate-500">
          Đang tải hàng đợi SRS...
        </div>

        <div v-else-if="loadError" class="flex flex-1 flex-col items-center justify-center gap-3 text-slate-500">
          {{ loadError }}
          <button type="button" class="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-extrabold text-white" @click="loadQueue">
            Thử lại
          </button>
        </div>

        <div v-else-if="completed" class="flex flex-1 flex-col items-center justify-center gap-4 text-center">
          <div class="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-600 text-2xl font-black text-white">✓</div>
          <h2 class="text-2xl font-extrabold text-slate-900">Hoàn thành!</h2>
          <p class="text-slate-500">{{ correctCount }}/{{ doneCount }} đúng</p>
          <p v-if="sessionXpEarned != null" class="text-sm font-bold text-emerald-600">
            +{{ sessionXpEarned }} XP (10 phút = 1 XP)
          </p>
          <div class="flex gap-3">
            <button type="button" class="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-50" @click="goBack">
              Về từ vựng
            </button>
            <button type="button" class="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-extrabold text-white" @click="restartSession">
              Ôn lại
            </button>
          </div>
        </div>

        <VocabFlashcardStage
          v-else-if="currentMode === 'flashcard' && currentWord"
          :word="currentWord"
          :flipped="cardFlipped"
          :reviewing="reviewing"
          @flip="toggleFlip"
          @speak="speakWord(currentWord.word)"
          @rate="markAnswer"
        />

        <VocabTypeStage
          v-else-if="currentMode === 'typing' && currentWord"
          ref="typingStageRef"
          :word="currentWord"
          variant="typing"
          caption="Gõ từ bạn nghe được"
          :model-value="typingInput"
          :result="typingResult"
          :reviewing="reviewing"
          @update:model-value="typingInput = $event"
          @speak="speakWord(currentWord.word)"
          @check="checkTypingWord"
          @next="nextWord"
        />

        <VocabTypeStage
          v-else-if="currentMode === 'dictation' && currentWord"
          ref="dictationStageRef"
          :word="currentWord"
          variant="dictation"
          caption="Nghe chép — gõ từ còn thiếu"
          :cloze-preview="exampleWithBlank(currentWord)"
          :model-value="typingInput"
          :result="typingResult"
          :reviewing="reviewing"
          @update:model-value="typingInput = $event"
          @speak="speakExample"
          @check="checkDictation"
          @next="nextWord"
        />

        <VocabReadingStage
          v-else-if="currentMode === 'reading'"
          :loading="readingLoading"
          :error="readingError"
          :passage="readingPassage"
          :batch-size="readingBatchWordIds.length"
          :gap-answers="gapAnswers"
          :gap-status="gapStatus"
          :checked="readingChecked"
          :all-correct="readingAllCorrect"
          :reviewing="reviewing"
          :comprehension-questions="readingPassage?.comprehension_questions || []"
          :mcq-answers="readingMcqAnswers"
          :mcq-checked="readingMcqChecked"
          :mcq-all-correct="readingMcqAllCorrect"
          @retry="loadReadingPassage"
          @check="checkReadingPassage"
          @mcq-select="onMcqSelect"
          @mcq-check="checkReadingMcq"
          @next="finishReadingBatch"
          @gap-input="onGapInput"
        />

        <div v-else-if="!queue.length" class="flex flex-1 flex-col items-center justify-center gap-3 text-slate-500">
          Không có từ trong hàng đợi
          <button type="button" class="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-50" @click="goBack">
            Về từ vựng
          </button>
        </div>

        <footer v-if="showFooter" class="mt-auto shrink-0 border-t border-slate-200 pt-5">
          <p class="mb-3 text-center text-[11px] text-slate-400">
            Phím tắt: ← → chuyển thẻ · Space lật thẻ (Flashcard)
          </p>
          <div class="mx-auto flex max-w-md items-center justify-center gap-4">
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 disabled:opacity-30 hover:border-emerald-500 hover:text-emerald-600"
              :disabled="queueIndex <= 0"
              @click="goPrevCard"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6" /></svg>
            </button>
            <span class="min-w-[90px] text-center text-sm font-bold text-slate-500">Thẻ {{ cardLabel }}</span>
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 disabled:opacity-30 hover:border-emerald-500 hover:text-emerald-600"
              :disabled="queueIndex >= queue.length - 1"
              @click="goNextCard"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6" /></svg>
            </button>
          </div>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useVocabPractice } from '@/composables/useVocabPractice.js'
import { exampleWithBlank } from '@/utils/vocabAnswer.js'
import VocabModeNav from '@/components/vocabulary/practice/VocabModeNav.vue'
import VocabFlashcardStage from '@/components/vocabulary/practice/VocabFlashcardStage.vue'
import VocabTypeStage from '@/components/vocabulary/practice/VocabTypeStage.vue'
import VocabReadingStage from '@/components/vocabulary/practice/VocabReadingStage.vue'

const p = useVocabPractice()

function toggleFlip() {
  p.cardFlipped.value = !p.cardFlipped.value
}

function onGapInput({ id, value }) {
  p.gapAnswers.value = { ...p.gapAnswers.value, [id]: value }
}

const {
  currentMode, loading, loadError, topicName, dueCount, queue, queueIndex,
  correctCount, doneCount, completed, reviewing, cardFlipped, typingInput, typingResult,
  typingStageRef, dictationStageRef, readingPassage, readingLoading, readingError,
  readingBatchWordIds, gapAnswers, gapStatus, readingChecked, readingAllCorrect,
  readingMcqAnswers, readingMcqChecked, readingMcqAllCorrect,
  currentWord, cardLabel, progressPct, showFooter, sessionXpEarned,
  setMode, goBack, loadQueue, restartSession, loadReadingPassage, checkReadingPassage,
  onMcqSelect, checkReadingMcq, finishReadingBatch, speakWord, speakExample, markAnswer, checkTypingWord, checkDictation,
  nextWord, goPrevCard, goNextCard,
} = p
</script>
