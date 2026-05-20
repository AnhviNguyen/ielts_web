<!-- ReadingPassage.vue
  Renders a reading passage with highlight/vocab/review tool support.
  SRP: Only responsible for passage rendering + tool interaction.
-->
<template>
  <div
    ref="passageEl"
    class="reading-passage"
    :class="[
      activeTool === 'highlight' ? 'cursor-text select-text' : '',
      activeTool === 'vocab'     ? 'vocab-mode' : '',
    ]"
    @mouseup="onMouseUp"
  >
    <!-- Review-mode: answer highlight banner -->
    <div v-if="reviewMode && answerHighlights.length" class="answer-legend">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Đáp án được đánh dấu màu vàng trong đoạn văn
    </div>

    <div
      v-for="p in paragraphs"
      :key="p.paragraph"
      :data-para="p.paragraph"
      class="reading-paragraph"
      :class="isAnswerParagraph(p.paragraph) ? 'para-answer-glow' : ''"
    >
      <span class="para-tag">{{ p.paragraph }}</span>
      <span v-html="renderParagraph(p)" />
    </div>
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
    v-if="showSaveDialog"
    :visible="showSaveDialog"
    :word="wordToSave"
    @close="showSaveDialog = false"
    @saved="onWordSaved"
  />
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import VocabPopup    from './VocabPopup.vue'
import SaveWordDialog from './SaveWordDialog.vue'
import { useTextHighlighter } from '@/composables/useTextHighlighter.js'
import { useVocabPopup }      from '@/composables/useVocabPopup.js'
import { saveWord }           from '@/services/vocabularyService.js'

const props = defineProps({
  paragraphs:       { type: Array,   default: () => [] },
  activeTool:       { type: String,  default: null },
  highlightColor:   { type: String,  default: 'yellow' },
  reviewMode:       { type: Boolean, default: false },
  answerHighlights: { type: Array,   default: () => [] }, // [{questionOrder, text, paragraphIdx}]
  sessionHighlights:{ type: Array,   default: () => [] }, // saved user highlights to restore
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
  if (!props.reviewMode || !props.answerHighlights.length) return p.text

  let html = p.text
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

async function onWordSaved({ topicId, word }) {
  try {
    await saveWord(topicId, {
      word:       word.word,
      phonetic:   word.phonetic,
      word_type:  word.word_type,
      meaning_vi: word.meaning_vi || '',
      example:    word.example || '',
    })
  } catch (e) {
    console.error('Failed to save word', e)
  }
}

// ── Expose highlights for parent to persist ───────────────────────────────────
defineExpose({ highlights, clearHighlights })
</script>

<style scoped>
.reading-passage { font-size: 14px; line-height: 1.8; color: var(--ink); }

.reading-paragraph {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  padding: 6px 4px;
  border-radius: 6px;
  transition: background .2s;
}
.reading-paragraph.para-answer-glow { background: rgba(250, 204, 21, 0.08); }

.para-tag {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  color: var(--ink3);
  width: 20px;
  padding-top: 3px;
}

.vocab-mode :deep(.vocab-word) { cursor: pointer; }
.vocab-mode :deep(.vocab-underline) {
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: #15803d;
  color: #15803d;
}

:deep(.answer-mark) {
  background: #fef08a;
  border-radius: 3px;
  padding: 1px 2px;
  font-weight: 600;
}

.answer-legend {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: #854d0e;
  background: #fefce8; border: 1px solid #fde047;
  border-radius: 8px; padding: 6px 10px; margin-bottom: 12px;
}
</style>
