<template>
  <div
    ref="rootEl"
    class="shadowing-vocab-text break-words whitespace-normal"
    :class="[large ? 'text-lg leading-relaxed' : 'text-[13px] leading-[1.65]', vocabEnabled ? 'vocab-mode' : '']"
  >
    <template v-if="vocabEnabled">
      <span
        v-for="(w, i) in words"
        :key="i"
        class="inline cursor-pointer rounded px-0.5 transition-colors hover:bg-emerald-100"
        :class="{ 'underline decoration-emerald-500 decoration-2 underline-offset-2': hovered === w }"
        @click.stop="onWordClick(w, $event)"
        @mouseenter="hovered = w"
        @mouseleave="hovered = null"
      >{{ w }}<span v-if="i < words.length - 1">&nbsp;</span></span>
    </template>
    <template v-else>{{ text }}</template>
  </div>

  <VocabPopup
    :visible="popupVisible"
    :word="popupWord"
    :loading="popupLoading"
    :streaming="popupStreaming"
    :position="popupPos"
    @close="closePopup"
    @save="onSave"
  />
  <SaveWordDialog
    :visible="showSaveDialog"
    :word="wordToSave"
    source-type="shadowing"
    :source-quiz-id="sourceQuizId"
    @close="showSaveDialog = false"
    @saved="showSaveDialog = false"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { tokenizeWords } from '@/utils/segmentUtils.js'
import { useVocabPopup } from '@/composables/useVocabPopup.js'
import VocabPopup from '@/components/reading/VocabPopup.vue'
import SaveWordDialog from '@/components/vocabulary/SaveWordDialog.vue'

const props = defineProps({
  text: { type: String, default: '' },
  vocabEnabled: { type: Boolean, default: true },
  large: { type: Boolean, default: false },
  sourceQuizId: { type: String, default: '' },
})

const vocab = useVocabPopup()
const {
  popupVisible, popupWord, popupPos, popupLoading, popupStreaming,
  openPopup, closePopup,
} = vocab

const hovered = ref(null)
const showSaveDialog = ref(false)
const wordToSave = ref(null)
const rootEl = ref(null)

const words = computed(() => tokenizeWords(props.text || ''))

function onWordClick(word, e) {
  openPopup(word, e.clientX, e.clientY)
}

function onSave(word) {
  wordToSave.value = word
  showSaveDialog.value = true
  closePopup()
}
</script>
