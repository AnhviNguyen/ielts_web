<template>
  <!-- Modal overlay — teleported to body to avoid z-index issues -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <div class="modal-box" role="dialog" :aria-labelledby="titleId">
          <button class="modal-close" @click="close" aria-label="Đóng">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
          <div :id="titleId" class="modal-title font-display">{{ title }}</div>
          <div v-if="subtitle" class="modal-sub">{{ subtitle }}</div>
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

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-box {
  background: var(--surface);
  border-radius: var(--r-lg);
  padding: 28px;
  width: 480px;
  max-width: calc(100vw - 40px);
  box-shadow: var(--shadow-lg);
  position: relative;
}

.modal-close {
  position: absolute;
  top: 14px; right: 14px;
  width: 30px; height: 30px;
  border-radius: 50%;
  background: var(--bg2);
  border: none;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink2);
  transition: background 0.15s;
}

.modal-close:hover { background: var(--border); }

.modal-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--ink);
}

.modal-sub {
  font-size: 13px;
  color: var(--ink3);
  margin-bottom: 20px;
}

/* Transition */
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal-box { transition: transform 0.2s; }
.modal-enter-from .modal-box { transform: translateY(10px); }
</style>
