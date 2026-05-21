<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/45 p-4"
        @click.self="$emit('update:modelValue', false)"
      >
        <div class="w-full max-w-[480px] overflow-hidden rounded-[20px] bg-white shadow-[0_24px_80px_rgba(0,0,0,0.18)]">
          <div class="flex items-start justify-between border-b border-slate-100 px-5 py-4">
            <div>
              <div class="text-base font-extrabold text-slate-900">Chọn chế độ học</div>
              <div class="mt-0.5 text-xs text-slate-400">{{ topicName }} · {{ wordCount }} từ</div>
            </div>
            <button type="button" class="cursor-pointer p-1 text-slate-400" @click="$emit('update:modelValue', false)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div v-if="loading" class="px-5 py-8 text-center text-[13px] text-slate-400">Đang tải...</div>
          <div v-else class="grid grid-cols-2 gap-2.5 px-5 py-4">
            <button
              v-for="m in modes"
              :key="m.id"
              type="button"
              class="cursor-pointer rounded-xl border-2 px-3.5 py-3 text-left transition-all"
              :class="selected === m.id
                ? 'border-green-700 bg-green-50'
                : 'border-slate-200 bg-slate-50 hover:border-green-300'"
              @click="selected = m.id"
            >
              <div class="text-[13px] font-bold text-slate-900">{{ m.label }}</div>
              <div class="mt-1 text-[11px] leading-snug text-slate-500">{{ m.description }}</div>
            </button>
          </div>

          <div class="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">
            <button type="button" class="cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-[13px]" @click="$emit('update:modelValue', false)">Hủy</button>
            <button
              type="button"
              class="cursor-pointer rounded-lg border-0 bg-green-700 px-5 py-2 text-[13px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
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
