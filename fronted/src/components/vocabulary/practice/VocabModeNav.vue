<template>
  <nav class="mb-4 grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 sm:gap-3">
    <button
      v-for="m in modes"
      :key="m.id"
      type="button"
      class="flex items-center justify-center gap-2 rounded-2xl border px-3 py-3 text-xs font-bold transition-all sm:flex-col sm:gap-1.5 sm:py-4 sm:text-[13px]"
      :class="activeId === m.id ? activeClass : idleClass"
      @click="$emit('select', m.id)"
    >
      <VocabModeIcon :mode="m.id" class="h-[18px] w-[18px] shrink-0" />
      <span>{{ m.label }}</span>
    </button>
  </nav>
</template>

<script setup>
import { VOCAB_PRACTICE_MODES } from '@/constants/vocabPracticeModes.js'
import VocabModeIcon from './VocabModeIcon.vue'

defineProps({
  activeId: { type: String, required: true },
})

defineEmits(['select'])

const modes = VOCAB_PRACTICE_MODES

const idleClass =
  'border-slate-200 bg-white text-slate-500 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700'
const activeClass =
  'border-emerald-500 bg-emerald-50 text-emerald-800 shadow-sm'
</script>
