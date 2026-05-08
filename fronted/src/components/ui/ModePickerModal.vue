<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="fixed inset-0 z-[200] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="$emit('update:modelValue', false)"></div>

        <div class="relative z-10 w-full max-w-sm rounded-xl bg-white shadow-xl">
          <!-- Header -->
          <div class="flex items-start justify-between border-b border-[var(--border)] px-5 py-4">
            <div>
              <div class="text-[11px] font-semibold uppercase tracking-wider text-[var(--ink3)]">Chọn chế độ luyện tập</div>
              <div class="mt-0.5 text-[14px] font-bold text-[var(--ink)] leading-snug line-clamp-2">{{ testTitle }}</div>
            </div>
            <button class="ml-3 flex h-7 w-7 shrink-0 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)]" @click="$emit('update:modelValue', false)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <!-- Options -->
          <div class="grid grid-cols-2 gap-3 p-4">
            <button
              class="flex flex-col items-start gap-2 rounded-lg border-2 p-4 text-left transition-colors"
              :class="selected === 'practice' ? 'border-[var(--ink)] bg-[var(--bg)]' : 'border-[var(--border)] hover:border-[var(--ink2)]'"
              @click="selected = 'practice'"
            >
              <div class="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-white">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
              </div>
              <div class="text-[13px] font-bold text-[var(--ink)]">Luyện tập</div>
              <div class="text-[11px] leading-relaxed text-[var(--ink3)]">Xem đáp án, highlight, ghi chú, tra từ</div>
            </button>

            <button
              class="flex flex-col items-start gap-2 rounded-lg border-2 p-4 text-left transition-colors"
              :class="selected === 'exam' ? 'border-[var(--ink)] bg-[var(--bg)]' : 'border-[var(--border)] hover:border-[var(--ink2)]'"
              @click="selected = 'exam'"
            >
              <div class="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-white">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
              </div>
              <div class="text-[13px] font-bold text-[var(--ink)]">Thi thật</div>
              <div class="text-[11px] leading-relaxed text-[var(--ink3)]">Đếm ngược, không xem đáp án</div>
            </button>
          </div>

          <!-- Confirm -->
          <div class="border-t border-[var(--border)] px-4 pb-4 pt-3">
            <button
              :disabled="!selected"
              class="ct-btn ct-btn-primary w-full disabled:cursor-not-allowed disabled:opacity-40"
              @click="confirm"
            >
              {{ selected === 'practice' ? 'Bắt đầu luyện tập' : selected === 'exam' ? 'Vào phòng thi' : 'Chọn chế độ' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ modelValue: Boolean, testTitle: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue', 'confirm'])
const selected = ref(null)
watch(() => props.modelValue, v => { if (v) selected.value = null })
function confirm() { if (!selected.value) return; emit('confirm', selected.value); emit('update:modelValue', false) }
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.15s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
