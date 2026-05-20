<template>
  <div class="reading-toolbar" :class="{ 'reading-toolbar--vertical': vertical }">
    <div class="reading-toolbar__tools">

      <!-- Highlight (T) -->
      <button
        class="rt-btn"
        :class="{ 'rt-btn--active rt-btn--highlight': activeTool === 'highlight' }"
        title="To mau (T)"
        @click="setTool('highlight')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 19l7-7 3 3-7 7-3-3z"/>
          <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
          <path d="M2 2l7.586 7.586"/>
          <circle cx="11" cy="11" r="2"/>
        </svg>
        <span v-if="!iconOnly">To mau</span>
        <kbd v-if="!iconOnly">T</kbd>
      </button>

      <!-- Color picker -->
      <Transition name="fade-colors">
        <div v-if="activeTool === 'highlight'" class="rt-colors">
          <button
            v-for="c in COLORS"
            :key="c.value"
            :title="c.label"
            class="rt-color-dot"
            :class="{ 'rt-color-dot--active': highlightColor === c.value }"
            :style="{ background: c.bg }"
            @click.stop="highlightColor = c.value"
          />
        </div>
      </Transition>

      <div class="rt-divider" />

      <!-- Note (N) -->
      <button
        class="rt-btn"
        :class="{ 'rt-btn--active rt-btn--note': activeTool === 'note' }"
        title="Ghi chu (N)"
        @click="setTool('note')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <span v-if="!iconOnly">Ghi chu</span>
        <kbd v-if="!iconOnly">N</kbd>
      </button>

      <div class="rt-divider" />

      <!-- Vocab (S) -->
      <button
        class="rt-btn"
        :class="{ 'rt-btn--active rt-btn--vocab': activeTool === 'vocab' }"
        title="Tra tu (S)"
        @click="setTool('vocab')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span v-if="!iconOnly">Tra tu</span>
        <kbd v-if="!iconOnly">S</kbd>
      </button>

    </div>

    <!-- Active tool indicator -->
    <div v-if="activeTool && !vertical" class="rt-active-label">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      {{ activeToolLabel }} dang bat &middot; nhan Esc hoac click lai de tat
    </div>
  </div>

  <!-- Note drawer -->
  <Teleport to="body">
    <Transition name="slide-right">
      <div v-if="activeTool === 'note'" class="note-drawer">
        <div class="note-drawer__header">
          <div class="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Ghi chu
          </div>
          <button class="note-close-btn" @click="setTool('note')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <textarea
          :value="modelNote"
          @input="$emit('update:modelNote', $event.target.value)"
          class="note-textarea"
          placeholder="Ghi chu cua ban tai day..."
        />
        <div class="note-drawer__footer">
          <span class="text-[10px] text-[var(--ink3)]">{{ modelNote.length }} ky tu</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useReadingTools } from '@/composables/useReadingTools.js'

const props = defineProps({
  modelNote: { type: String, default: '' },
  vertical: { type: Boolean, default: false },
  iconOnly: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelNote', 'tool-changed'])

const { activeTool, setTool } = useReadingTools()
const highlightColor = ref('yellow')

const COLORS = [
  { value: 'yellow', label: 'Vang',     bg: '#fef08a' },
  { value: 'green',  label: 'Xanh la',  bg: '#bbf7d0' },
  { value: 'rose',   label: 'Hong',     bg: '#fecdd3' },
  { value: 'blue',   label: 'Xanh lam', bg: '#bfdbfe' },
]

const TOOL_LABELS = {
  highlight: 'To mau',
  note: 'Ghi chu',
  vocab: 'Tra tu',
}

const activeToolLabel = computed(() => TOOL_LABELS[activeTool.value] || '')

watch(activeTool, (t) => {
  emit('tool-changed', { tool: t, color: highlightColor.value })
})

watch(highlightColor, (c) => {
  emit('tool-changed', { tool: activeTool.value, color: c })
})

defineExpose({ activeTool, highlightColor })
</script>

<style scoped>
.reading-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: var(--surface, #f9fafb);
  border-bottom: 1px solid var(--border, #e5e7eb);
  flex-wrap: wrap;
}
.reading-toolbar--vertical {
  align-items: flex-start;
  border-bottom: none;
  padding: 0;
  background: transparent;
}

.reading-toolbar__tools {
  display: flex;
  align-items: center;
  gap: 4px;
}
.reading-toolbar--vertical .reading-toolbar__tools {
  flex-direction: column;
  gap: 10px;
}

.rt-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ink2, #374151);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.reading-toolbar--vertical .rt-btn {
  width: 48px;
  height: 48px;
  justify-content: center;
  padding: 0;
  border-radius: 12px;
  border: 1px solid var(--border, #e5e7eb);
  background: #fff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.rt-btn:hover {
  background: var(--surface2, #f3f4f6);
  border-color: var(--border, #e5e7eb);
}

.rt-btn--active {
  border-color: currentColor;
}

.rt-btn--highlight.rt-btn--active {
  background: #fef9c3;
  color: #92400e;
  border-color: #fbbf24;
}

.rt-btn--note.rt-btn--active {
  background: #dbeafe;
  color: #1e40af;
  border-color: #60a5fa;
}

.rt-btn--vocab.rt-btn--active {
  background: #dcfce7;
  color: #166534;
  border-color: #34d399;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 10px;
  background: var(--surface2, #f3f4f6);
  border: 1px solid var(--border, #d1d5db);
  border-radius: 3px;
  color: var(--ink3, #6b7280);
}

.rt-divider {
  width: 1px;
  height: 20px;
  background: var(--border, #e5e7eb);
  margin: 0 4px;
}
.reading-toolbar--vertical .rt-divider {
  width: 24px;
  height: 1px;
  margin: -2px 0;
}

.rt-colors {
  display: flex;
  gap: 4px;
  align-items: center;
}

.rt-color-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.15s;
}

.rt-color-dot:hover {
  transform: scale(1.2);
}

.rt-color-dot--active {
  border-color: #374151;
  transform: scale(1.15);
}

.rt-active-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--ink3, #6b7280);
  margin-left: auto;
}
.reading-toolbar--vertical .rt-colors {
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
  padding: 6px 4px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
}

/* Note drawer */
.note-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 320px;
  height: 100vh;
  background: var(--surface, #ffffff);
  border-left: 1px solid var(--border, #e5e7eb);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  z-index: 200;
}

.note-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border, #e5e7eb);
}

.note-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--ink3, #6b7280);
}

.note-close-btn:hover {
  background: var(--surface2, #f3f4f6);
}

.note-textarea {
  flex: 1;
  padding: 14px 16px;
  border: none;
  resize: none;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ink, #111827);
  background: transparent;
  outline: none;
}

.note-drawer__footer {
  padding: 8px 16px;
  border-top: 1px solid var(--border, #e5e7eb);
}

/* Transitions */
.fade-colors-enter-active,
.fade-colors-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-colors-enter-from,
.fade-colors-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.25s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
}
</style>
