<template>
  <div class="sh-card sh-focus-card flex h-full min-h-0 w-full flex-col p-6">
    <p class="sh-panel-title mb-3">Câu đang luyện</p>
    <div v-if="segment" class="flex flex-1 flex-col justify-center">
      <ShadowingVocabText
        :text="segment.text"
        :vocab-enabled="true"
        :large="true"
        :source-quiz-id="sourceQuizId"
        class="sh-focus-text"
      />
      <p
        v-if="showTranslation && segment.translation"
        class="mt-4 border-t border-gray-100 pt-4 text-center text-[15px] italic text-gray-600"
      >
        {{ segment.translation }}
      </p>
    </div>
    <p v-else class="flex flex-1 items-center justify-center text-sm text-gray-400">
      Chọn một câu trong bản chép bên phải
    </p>
  </div>
</template>

<script setup>
import ShadowingVocabText from '@/components/shadowing/ShadowingVocabText.vue'

defineProps({
  segment: { type: Object, default: null },
  showTranslation: { type: Boolean, default: true },
  sourceQuizId: { type: String, default: '' },
})
</script>
