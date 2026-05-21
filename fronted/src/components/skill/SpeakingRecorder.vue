<template>
  <div class="mb-5 rounded-[var(--r)] bg-[var(--ink)] px-7 py-7 text-center text-white">
    <div class="mb-4 flex items-center justify-between">
      <span class="inline-block rounded-full bg-[rgba(82,183,136,0.2)] px-2.5 py-0.5 text-[11px] font-semibold text-[var(--green-l)]">{{ partLabel }}</span>
      <span v-if="prepTime" class="font-mono text-xs text-white/40">Prep: {{ formatTime(prepTime) }}</span>
    </div>

    <div class="mb-6 text-base font-medium leading-relaxed text-white/[0.88]">
      {{ question }}
      <span v-if="hint" class="mt-1.5 block text-[13px] text-white/50">{{ hint }}</span>
    </div>

    <div class="mb-5 flex justify-center">
      <button
        type="button"
        class="flex h-20 w-20 cursor-pointer items-center justify-center rounded-full border-0 bg-[var(--rose-l)] text-[28px] text-white transition-all hover:scale-105"
        :class="isRecording ? 'record-btn-active' : 'record-btn-idle'"
        @click="toggle"
        :title="isRecording ? 'Dừng ghi âm' : 'Bắt đầu ghi âm'"
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
      </button>
    </div>

    <div class="text-xs text-white/45">
      {{ isRecording ? 'Đang ghi âm...' : 'Nhấn để bắt đầu ghi âm' }}
    </div>
    <div class="mt-1.5 font-mono text-xl font-semibold">{{ formatTime(elapsed) }}</div>
  </div>
</template>

<script setup>
import { useRecorder } from '@/composables/useRecorder.js'

defineProps({
  partLabel: { type: String, default: 'Part 2 · Cue Card' },
  question:  { type: String, default: 'Describe a skill you would like to learn in the future.' },
  hint:      { type: String, default: '' },
  prepTime:  { type: Number, default: 60 },
})

defineEmits(['recorded'])

const { isRecording, elapsed, toggle, formatTime } = useRecorder()
</script>
