<template>
  <section class="study-modes">
    <div class="study-modes__head">
      <h3 class="study-modes__title">Chế độ học</h3>
      <p class="study-modes__sub">
        Chọn một chế độ để luyện {{ wordCount }} từ trong topic «{{ topicName }}»
      </p>
    </div>
    <div class="study-modes__grid">
      <button
        v-for="m in displayModes"
        :key="m.id"
        type="button"
        class="study-mode-card"
        :disabled="wordCount < 2"
        @click="$emit('start', m.id)"
      >
        <span class="study-mode-card__icon" v-html="iconFor(m.id)"></span>
        <span class="study-mode-card__label">{{ m.label }}</span>
        <span class="study-mode-card__desc">{{ m.description }}</span>
      </button>
    </div>
    <p v-if="wordCount < 2" class="study-modes__hint">
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

<style scoped>
.study-modes {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
}
.study-modes__title { font-size: 14px; font-weight: 800; color: #0f172a; margin: 0; }
.study-modes__sub { font-size: 12px; color: #64748b; margin: 4px 0 0; }
.study-modes__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 14px;
}
@media (min-width: 768px) {
  .study-modes__grid { grid-template-columns: repeat(4, 1fr); }
}
.study-mode-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 14px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.study-mode-card:hover:not(:disabled) {
  border-color: #15803d;
  background: #f0fdf4;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(21, 128, 61, 0.12);
}
.study-mode-card:disabled { opacity: 0.45; cursor: not-allowed; }
.study-mode-card__icon { color: #15803d; display: flex; }
.study-mode-card__label { font-size: 13px; font-weight: 700; color: #0f172a; }
.study-mode-card__desc { font-size: 11px; color: #64748b; line-height: 1.35; }
.study-modes__hint { font-size: 12px; color: #d97706; margin: 10px 0 0; }
</style>
