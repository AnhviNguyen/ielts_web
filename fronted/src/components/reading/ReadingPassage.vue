<!-- ReadingPassage.vue
  Renders a reading passage with highlight/vocab/review tool support.
  SRP: Only responsible for passage rendering + tool interaction.
-->
<template>
  <div
    ref="passageEl"
    class="text-sm leading-[1.8] text-[var(--ink)]"
    :class="[
      activeTool === 'highlight' ? 'cursor-text select-text' : '',
      activeTool === 'vocab' ? 'vocab-mode' : '',
    ]"
    @mouseup="onMouseUp"
  >
    <!-- Review-mode: answer highlight banner -->
    <div
      v-if="reviewMode && answerHighlights.length"
      class="mb-3 flex items-center gap-1.5 rounded-lg border border-yellow-300 bg-yellow-50 px-2.5 py-1.5 text-[11px] text-yellow-800"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Đáp án được đánh dấu màu vàng trong đoạn văn
    </div>

    <template v-for="p in paragraphs" :key="p.paragraph">
      <!-- Empty separator block (blank line between paragraphs in Orange 16+ format) -->
      <div v-if="p.isEmpty" :data-para="p.paragraph" class="h-3" />
      <!-- Normal paragraph block -->
      <div
        v-else
        :data-para="p.paragraph"
        class="mb-3 flex gap-2 rounded-md px-1 py-1.5 transition-colors"
        :class="isAnswerParagraph(p.paragraph) ? 'bg-yellow-400/10' : ''"
      >
        <span class="w-5 shrink-0 pt-0.5 text-[11px] font-bold text-[var(--ink3)]">{{ p.paragraph }}</span>
        <span v-html="renderParagraph(p)" />
      </div>
    </template>
  </div>

  <!-- VocabPopup -->
  <VocabPopup
    :visible="vocabPopupVisible"
    :word="vocabPopupWord"
    :loading="vocabPopupLoading"
    :position="vocabPopupPos"
    @close="vocabPopup.closePopup()"
    @save="onSaveWord"
  />

  <!-- Save to vocab dialog -->
  <SaveWordDialog
    :visible="showSaveDialog"
    :word="wordToSave"
    :source-type="sourceType"
    :source-quiz-id="sourceQuizId"
    @close="showSaveDialog = false"
    @saved="onWordSaved"
  />
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import VocabPopup    from './VocabPopup.vue'
import SaveWordDialog from '@/components/vocabulary/SaveWordDialog.vue'
import { useTextHighlighter } from '@/composables/useTextHighlighter.js'
import { useVocabPopup }      from '@/composables/useVocabPopup.js'
import { getTopics }          from '@/services/vocabularyService.js'
import { sanitizeHtml }       from '@/utils/sanitizeHtml.js'

const props = defineProps({
  paragraphs:       { type: Array,   default: () => [] },
  activeTool:       { type: String,  default: null },
  highlightColor:   { type: String,  default: 'yellow' },
  reviewMode:       { type: Boolean, default: false },
  answerHighlights: { type: Array,   default: () => [] },
  sessionHighlights:{ type: Array,   default: () => [] },
  sourceType:       { type: String,  default: 'reading' },
  sourceQuizId:     { type: String,  default: null },
})

const emit = defineEmits(['highlights-changed'])

// ── Refs ──────────────────────────────────────────────────────────────────────
const passageEl = ref(null)

// ── Highlight composable ─────────────────────────────────────────────────────
const highlighter = useTextHighlighter(passageEl)
const { highlights, applyHighlight, clearHighlights } = highlighter

watch(highlights, (v) => emit('highlights-changed', v), { deep: true })

// ── Vocab composable ──────────────────────────────────────────────────────────
const vocabPopup = useVocabPopup()
const {
  popupVisible: vocabPopupVisible,
  popupWord:    vocabPopupWord,
  popupLoading: vocabPopupLoading,
  popupPos:     vocabPopupPos,
  bindContainer, unbindContainer,
} = vocabPopup

// ── Save word state ───────────────────────────────────────────────────────────
const showSaveDialog = ref(false)
const wordToSave     = ref(null)

// ── Tool change watcher ───────────────────────────────────────────────────────
watch(() => props.activeTool, async (tool, prev) => {
  if (prev === 'vocab') unbindContainer(passageEl.value)
  if (tool === 'vocab') {
    await nextTick()
    bindContainer(passageEl.value)
  }
})

// ── Mouse-up: apply highlight ────────────────────────────────────────────────
function onMouseUp() {
  if (props.activeTool === 'highlight') {
    applyHighlight(props.highlightColor)
  }
}

// ── Review mode: render paragraph with answer highlights ─────────────────────
function renderParagraph(p) {
  if (!props.reviewMode || !props.answerHighlights.length) return sanitizeHtml(p.text)

  let html = sanitizeHtml(p.text)
  props.answerHighlights
    .filter((ah) => ah.paragraphIdx === p.paragraph)
    .forEach((ah) => {
      const escaped = ah.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      html = html.replace(
        new RegExp(escaped, 'gi'),
        `<mark class="answer-mark" data-q="${ah.questionOrder}">$&</mark>`,
      )
    })
  return html
}

function isAnswerParagraph(paragraphIdx) {
  return props.reviewMode && props.answerHighlights.some((ah) => ah.paragraphIdx === paragraphIdx)
}

// ── Session restore (rehydrate highlights on mount) ──────────────────────────
onMounted(async () => {
  getTopics().catch(() => {})
  if (props.sessionHighlights?.length) {
    await nextTick()
    highlights.value = [...props.sessionHighlights]
    highlighter.rehydrateHighlights()
  }
})

// ── Save word ─────────────────────────────────────────────────────────────────
function onSaveWord(word) {
  wordToSave.value = word
  showSaveDialog.value = true
  vocabPopup.closePopup()
}

function onWordSaved() {
  showSaveDialog.value = false
  wordToSave.value = null
}

// ── Expose highlights for parent to persist ───────────────────────────────────
defineExpose({ highlights, clearHighlights })
</script>
