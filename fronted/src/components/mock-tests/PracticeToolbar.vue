<template>
  <!-- Only render in practice mode -->
  <template v-if="practiceMode">
    <!-- ── Left-side tool buttons ─────────────────────────────────────── -->
    <div class="fixed left-4 top-1/2 z-[150] -translate-y-1/2 flex flex-col gap-2">

      <!-- Highlight (T) -->
      <div class="relative">
        <button
          class="tool-btn"
          :class="activeTool === 'highlight' ? 'tool-btn--highlight-active' : 'tool-btn--default hover:tool-btn--highlight-hover'"
          title="Tô màu (T)"
          @click="setTool('highlight')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 11-6 6v3h9l3-3"/>
            <path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>
          </svg>
          <span class="tool-key">T</span>
        </button>

        <!-- Color picker sub-panel -->
        <Transition name="slide-x">
          <div v-if="activeTool === 'highlight'" class="absolute left-14 top-0 flex gap-1.5 rounded-xl border border-[var(--border)] bg-white p-1.5 shadow-lg">
            <button
              v-for="c in COLORS" :key="c.value"
              :title="c.label"
              class="h-6 w-6 rounded-lg border-2 transition-transform hover:scale-110"
              :class="highlightColor === c.value ? 'border-[var(--ink)]' : 'border-transparent'"
              :style="{ background: c.bg }"
              @click.stop="highlightColor = c.value"
            />
          </div>
        </Transition>
      </div>

      <!-- Note (N) -->
      <button
        class="tool-btn"
        :class="activeTool === 'note' ? 'tool-btn--note-active' : 'tool-btn--default hover:tool-btn--note-hover'"
        title="Ghi chú (N)"
        @click="setTool('note')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <span class="tool-key">N</span>
      </button>

      <!-- Vocab lookup (S) -->
      <button
        class="tool-btn"
        :class="activeTool === 'vocab' ? 'tool-btn--vocab-active' : 'tool-btn--default hover:tool-btn--vocab-hover'"
        title="Tra từ vựng (S)"
        @click="setTool('vocab')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span class="tool-key">S</span>
      </button>

      <div class="mx-auto h-px w-8 bg-[var(--border)]"></div>
      <div class="flex h-11 w-11 items-center justify-center text-[9px] text-[var(--ink3)] leading-tight text-center">
        Công<br>cụ
      </div>
    </div>

    <!-- ── Note panel (right drawer) ─────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="slide-right">
        <div v-if="activeTool === 'note'" class="note-panel">
          <div class="note-panel__header">
            <div class="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Ghi chú
            </div>
            <button class="icon-close" @click="setTool('note')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <textarea
            v-model="noteText"
            class="flex-1 resize-none p-4 text-[13px] text-[var(--ink)] outline-none leading-relaxed"
            placeholder="Ghi chú của bạn tại đây..."
          />
          <div class="note-panel__footer">
            <span class="text-[10px] text-[var(--ink3)]">{{ noteText.length }} ký tự</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </template>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useReadingTools } from '@/composables/useReadingTools.js'

const props = defineProps({
  practiceMode: { type: Boolean, default: false },
  modelNote:    { type: String,  default: '' },
})

const emit = defineEmits(['update:modelNote', 'highlight-applied', 'tool-changed'])

const { activeTool, setTool } = useReadingTools()

const highlightColor = ref('yellow')
const noteText       = ref(props.modelNote)

const COLORS = [
  { value: 'yellow', label: 'Vàng',         bg: '#fef08a' },
  { value: 'green',  label: 'Xanh lá',      bg: '#bbf7d0' },
  { value: 'rose',   label: 'Hồng',         bg: '#fecdd3' },
  { value: 'blue',   label: 'Xanh dương',   bg: '#bfdbfe' },
]

// Sync note to parent
watch(noteText, (v) => emit('update:modelNote', v))
// Expose current tool info to parent (e.g., for highlight color)
watch(activeTool, (t) => emit('tool-changed', { tool: t, color: highlightColor.value }))
watch(highlightColor, (c) => emit('tool-changed', { tool: activeTool.value, color: c }))

// Expose for parent to read
defineExpose({ activeTool, highlightColor, noteText })
</script>

<style scoped>
.tool-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  width: 44px;
  border-radius: 12px;
  border: 1px solid;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  transition: all .15s;
}
.tool-btn:hover { transform: translateX(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.12); }

.tool-key {
  position: absolute;
  bottom: 2px;
  right: 4px;
  font-size: 8px;
  font-weight: 700;
  opacity: .5;
  line-height: 1;
}

.tool-btn--default { border-color: var(--border); background: #fff; color: var(--ink2); }

/* Highlight */
.tool-btn--highlight-active  { border-color: #fde047; background: #fef9c3; color: #854d0e; }
.hover\:tool-btn--highlight-hover:hover { border-color: #fde047; background: #fefce8; }

/* Note */
.tool-btn--note-active  { border-color: var(--blue-l); background: var(--blue-bg); color: var(--blue); }
.hover\:tool-btn--note-hover:hover { border-color: var(--blue-l); background: var(--blue-bg); }

/* Vocab */
.tool-btn--vocab-active  { border-color: #15803d; background: #dcfce7; color: #15803d; }
.hover\:tool-btn--vocab-hover:hover { border-color: #15803d; background: #f0fdf4; }

/* Note panel */
.note-panel {
  position: fixed; right: 0; top: 0; z-index: 160;
  height: 100%; width: 320px;
  display: flex; flex-direction: column;
  background: #fff;
  box-shadow: -4px 0 24px rgba(0,0,0,.1);
  border-left: 1px solid var(--border);
}
.note-panel__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.note-panel__footer {
  padding: 8px 16px; border-top: 1px solid var(--border); flex-shrink: 0; text-align: right;
}
.icon-close { background: none; border: none; cursor: pointer; color: var(--ink3); padding: 4px; border-radius: 6px; }
.icon-close:hover { background: var(--bg2); color: var(--ink); }

.slide-right-enter-active, .slide-right-leave-active { transition: transform .25s ease; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }

.slide-x-enter-active, .slide-x-leave-active { transition: opacity .15s, transform .15s; }
.slide-x-enter-from, .slide-x-leave-to { opacity: 0; transform: translateX(-8px); }
</style>
