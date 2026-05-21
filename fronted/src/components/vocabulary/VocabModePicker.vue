<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="$emit('update:modelValue', false)">
        <div class="picker-box">
          <div class="picker-header">
            <div>
              <div class="picker-title">Chọn chế độ học</div>
              <div class="picker-sub">{{ topicName }} · {{ wordCount }} từ</div>
            </div>
            <button type="button" class="picker-close" @click="$emit('update:modelValue', false)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div v-if="loading" class="picker-loading">Đang tải...</div>
          <div v-else class="mode-grid">
            <button
              v-for="m in modes"
              :key="m.id"
              type="button"
              class="mode-card"
              :class="{ active: selected === m.id }"
              @click="selected = m.id"
            >
              <div class="mode-card__label">{{ m.label }}</div>
              <div class="mode-card__desc">{{ m.description }}</div>
            </button>
          </div>

          <div class="picker-footer">
            <button type="button" class="btn-cancel" @click="$emit('update:modelValue', false)">Hủy</button>
            <button
              type="button"
              class="btn-green"
              :disabled="!selected"
              @click="confirm"
            >
              Bắt đầu
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { getStudyModes } from '@/services/vocabularyService.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  topicName:  { type: String, default: '' },
  wordCount:  { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const modes   = ref([])
const loading = ref(false)
const selected = ref('flashcard')

watch(() => props.modelValue, (v) => {
  if (v) selected.value = 'flashcard'
})

onMounted(async () => {
  loading.value = true
  try {
    const data = await getStudyModes()
    modes.value = data.modes || []
  } catch {
    modes.value = [
      { id: 'flashcard', label: 'Flashcard', description: 'Lật thẻ EN ↔ VI' },
      { id: 'multiple', label: 'Trắc nghiệm', description: 'Chọn nghĩa đúng' },
      { id: 'reading', label: 'Đọc hiểu', description: 'Điền từ vào câu ví dụ' },
      { id: 'dictation', label: 'Nghe chép', description: 'Nghe và gõ từ' },
    ]
  } finally {
    loading.value = false
  }
})

function confirm() {
  if (!selected.value) return
  emit('confirm', selected.value)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; padding: 16px;
}
.picker-box {
  background: #fff; border-radius: 20px; width: 100%; max-width: 480px;
  box-shadow: 0 24px 80px rgba(0,0,0,.18); overflow: hidden;
}
.picker-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 18px 20px; border-bottom: 1px solid #f1f5f9;
}
.picker-title { font-size: 16px; font-weight: 800; color: #0f172a; }
.picker-sub { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.picker-close { background: none; border: none; cursor: pointer; color: #94a3b8; padding: 4px; }
.picker-loading { padding: 32px; text-align: center; font-size: 13px; color: #94a3b8; }

.mode-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  padding: 16px 20px;
}
.mode-card {
  text-align: left; padding: 14px;
  border: 2px solid #e2e8f0; border-radius: 12px;
  background: #f8fafc; cursor: pointer; transition: all .15s;
}
.mode-card:hover { border-color: #86efac; }
.mode-card.active { border-color: #15803d; background: #f0fdf4; }
.mode-card__label { font-size: 13px; font-weight: 700; color: #0f172a; }
.mode-card__desc { font-size: 11px; color: #64748b; margin-top: 4px; line-height: 1.4; }

.picker-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px; border-top: 1px solid #f1f5f9;
}
.btn-cancel { padding: 8px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; font-size: 13px; cursor: pointer; }
.btn-green { padding: 8px 20px; background: #15803d; color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; }
.btn-green:disabled { opacity: .4; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity .2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
