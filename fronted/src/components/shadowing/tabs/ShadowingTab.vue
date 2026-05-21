<template>
  <div class="flex flex-1 flex-col items-center justify-center p-6">
    <div class="sh-card w-full max-w-2xl p-8">
      <div class="mb-6 flex flex-wrap justify-center gap-2">
        <span v-for="(w, i) in words" :key="i" class="sh-word-chip text-lg">{{ w }}</span>
      </div>
      <p
        v-if="showTranslation && segment?.translation"
        class="border-t border-gray-100 pt-4 text-center text-[15px] italic text-gray-600"
      >
        {{ segment.translation }}
      </p>
      <p v-else-if="!segment" class="text-center text-sm text-gray-400">Chọn một câu trong bản chép</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { tokenizeWords } from '@/utils/segmentUtils.js'

const props = defineProps({
  segment: { type: Object, default: null },
  showTranslation: { type: Boolean, default: true },
})

const words = computed(() => tokenizeWords(props.segment?.text || ''))
</script>
