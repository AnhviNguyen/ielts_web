<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[1000] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="close"
      >
        <div
          class="modal-box relative w-[480px] max-w-[calc(100vw-40px)] rounded-[var(--r-lg)] bg-[var(--surface)] p-7 shadow-[var(--shadow-lg)]"
          role="dialog"
          :aria-labelledby="titleId"
        >
          <button
            class="absolute right-3.5 top-3.5 flex h-[30px] w-[30px] cursor-pointer items-center justify-center rounded-full border-0 bg-[var(--bg2)] text-base text-[var(--ink2)] transition-colors hover:bg-[var(--border)]"
            aria-label="Đóng"
            @click="close"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
          <div :id="titleId" class="font-display mb-1.5 text-xl font-bold text-[var(--ink)]">{{ title }}</div>
          <div v-if="subtitle" class="mb-5 text-[13px] text-[var(--ink3)]">{{ subtitle }}</div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String, default: '' },
  subtitle:   { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const titleId = computed(() => `modal-title-${Math.random().toString(36).slice(2)}`)

function close() {
  emit('update:modelValue', false)
}
</script>
