<template>
  <div v-bind="$attrs">
    <div
      ref="rootEl"
      class="shadowing-vocab-text whitespace-normal"
      :class="[large ? 'text-lg leading-relaxed' : 'text-[13px] leading-[1.65]', vocabEnabled ? 'vocab-mode flex flex-wrap justify-center gap-x-1 gap-y-0.5' : '']"
    >
      <template v-if="vocabEnabled">
        <span
          v-for="(w, i) in words"
          :key="i"
          class="inline-block max-w-full cursor-pointer rounded px-0.5 transition-colors hover:bg-[var(--green-bg)]"
          :class="{ 'underline decoration-[var(--spotify-green)] decoration-2 underline-offset-2': hovered === w }"
          @click.stop="onWordClick(w, $event)"
          @mouseenter="hovered = w"
          @mouseleave="hovered = null"
        >{{ w }}</span>
      </template>
      <template v-else>{{ text }}</template>
    </div>

    <VocabPopup
      :visible="popupVisible"
      :word="popupWord"
      :loading="popupLoading"
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { tokenizeWords } from '@/utils/segmentUtils.js'
import { useVocabPopup } from '@/composables/useVocabPopup.js'
import VocabPopup from '@/components/reading/VocabPopup.vue'
import SaveWordDialog from '@/components/vocabulary/SaveWordDialog.vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  text: { type: String, default: '' },
  vocabEnabled: { type: Boolean, default: true },
  large: { type: Boolean, default: false },
  sourceQuizId: { type: String, default: '' },
})

const vocab = useVocabPopup()
const {
  popupVisible, popupWord, popupPos, popupLoading,
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
