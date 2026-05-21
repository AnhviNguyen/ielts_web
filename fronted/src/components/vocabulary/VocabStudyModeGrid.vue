<template>
  <section class="border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white px-5 py-4">
    <div>
      <h3 class="m-0 text-sm font-extrabold text-slate-900">Chế độ học</h3>
      <p class="mt-1 text-xs text-slate-500">
        Chọn một chế độ để luyện {{ wordCount }} từ trong topic «{{ topicName }}»
      </p>
    </div>
    <div class="mt-3.5 grid grid-cols-2 gap-2.5 md:grid-cols-4">
      <button
        v-for="m in displayModes"
        :key="m.id"
        type="button"
        class="flex cursor-pointer flex-col items-start gap-1.5 rounded-xl border-2 border-slate-200 bg-white p-3.5 text-left transition-all hover:-translate-y-px hover:border-green-700 hover:bg-green-50 hover:shadow-[0_4px_12px_rgba(21,128,61,0.12)] disabled:cursor-not-allowed disabled:opacity-45"
        :disabled="wordCount < 2"
        @click="$emit('start', m.id)"
      >
        <span class="flex text-green-700" v-html="iconFor(m.id)"></span>
        <span class="text-[13px] font-bold text-slate-900">{{ m.label }}</span>
        <span class="text-[11px] leading-snug text-slate-500">{{ m.description }}</span>
      </button>
    </div>
    <p v-if="wordCount < 2" class="mt-2.5 text-xs text-amber-600">
      Cần ít nhất 2 từ trong topic để bắt đầu luyện tập.
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modes: { type: Array, default: () => [] },
  topicName: { type: String, default: '' },
  wordCount: { type: Number, default: 0 },
})

defineEmits(['start'])

const FALLBACK = [
  { id: 'flashcard', label: 'Flashcard', description: 'Lật thẻ EN ↔ VI' },
  { id: 'multiple', label: 'Trắc nghiệm', description: 'Chọn nghĩa đúng' },
  { id: 'reading', label: 'Đọc hiểu', description: 'Điền từ vào câu ví dụ' },
  { id: 'dictation', label: 'Nghe chép', description: 'Nghe và gõ từ' },
]

const displayModes = computed(() =>
  props.modes?.length ? props.modes : FALLBACK
)

const ICONS = {
  flashcard: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,
  multiple: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  reading: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  dictation: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>`,
}

function iconFor(id) {
  return ICONS[id] || ICONS.flashcard
}
</script>
