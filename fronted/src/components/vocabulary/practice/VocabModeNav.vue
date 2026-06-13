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
  'border-[var(--border)] bg-[var(--bg-surface)] text-[var(--ink3)] hover:border-[var(--spotify-green)] hover:bg-[var(--green-bg)] hover:text-[var(--spotify-green)]'
const activeClass =
  'border-[var(--spotify-green)] bg-[var(--green-bg)] text-[var(--spotify-green)] shadow-sm'
</script>
