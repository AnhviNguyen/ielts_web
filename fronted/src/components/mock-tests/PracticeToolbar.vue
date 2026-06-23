<template>
  <template v-if="practiceMode">
    <div class="fixed left-4 top-1/2 z-[150] flex -translate-y-1/2 flex-col gap-2" data-tour="quiz-toolbar">

      <div class="relative">
        <button
          type="button"
          data-tour="quiz-tool-highlight"
          class="relative flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border shadow-sm transition-all hover:-translate-x-0.5 hover:shadow-md"
          :class="activeTool === 'highlight'
            ? 'border-yellow-300 bg-yellow-100 text-yellow-800'
            : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-yellow-300 hover:bg-yellow-50'"
          title="Tô màu (T)"
          @click="setTool('highlight')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 11-6 6v3h9l3-3"/>
            <path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>
          </svg>
          <span class="absolute bottom-0.5 right-1 text-[8px] font-bold leading-none opacity-50">T</span>
        </button>

        <Transition name="slide-x">
          <div v-if="activeTool === 'highlight'" class="absolute left-14 top-0 flex gap-1.5 rounded-xl border border-[var(--border)] bg-white p-1.5 shadow-lg">
            <button
              v-for="c in COLORS"
              :key="c.value"
              type="button"
              :title="c.label"
              class="h-6 w-6 rounded-lg border-2 transition-transform hover:scale-110"
              :class="highlightColor === c.value ? 'border-[var(--ink)]' : 'border-transparent'"
              :style="{ background: c.bg }"
              @click.stop="highlightColor = c.value"
            />
          </div>
        </Transition>
      </div>

      <button
        type="button"
        data-tour="quiz-tool-note"
        class="relative flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border shadow-sm transition-all hover:-translate-x-0.5 hover:shadow-md"
        :class="activeTool === 'note'
          ? 'border-[var(--blue-l)] bg-[var(--blue-bg)] text-[var(--blue)]'
          : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-[var(--blue-l)] hover:bg-[var(--blue-bg)]'"
        title="Ghi chú (N)"
        @click="setTool('note')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <span class="absolute bottom-0.5 right-1 text-[8px] font-bold leading-none opacity-50">N</span>
      </button>

      <button
        type="button"
        data-tour="quiz-tool-vocab"
        class="relative flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border shadow-sm transition-all hover:-translate-x-0.5 hover:shadow-md"
        :class="activeTool === 'vocab'
          ? 'border-green-700 bg-green-100 text-green-700'
          : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-green-700 hover:bg-green-50'"
        title="Tra từ vựng (S)"
        @click="setTool('vocab')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span class="absolute bottom-0.5 right-1 text-[8px] font-bold leading-none opacity-50">S</span>
      </button>

      <div class="mx-auto h-px w-8 bg-[var(--border)]"></div>
      <div class="flex h-11 w-11 items-center justify-center text-center text-[9px] leading-tight text-[var(--ink3)]">
        Công<br>cụ
      </div>
    </div>

    <Teleport to="body">
      <Transition name="slide-right">
        <div
          v-if="activeTool === 'note'"
          class="fixed right-0 top-0 z-[160] flex h-full w-80 flex-col border-l border-[var(--border)] bg-white shadow-[-4px_0_24px_rgba(0,0,0,0.1)]"
        >
          <div class="flex shrink-0 items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <div class="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Ghi chú
            </div>
            <button type="button" class="cursor-pointer rounded-md p-1 text-[var(--ink3)] hover:bg-[var(--bg2)] hover:text-[var(--ink)]" @click="setTool('note')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <textarea
            v-model="noteText"
            class="flex-1 resize-none p-4 text-[13px] leading-relaxed text-[var(--ink)] outline-none"
            placeholder="Ghi chú của bạn tại đây..."
          />
          <div class="shrink-0 border-t border-[var(--border)] px-4 py-2 text-right">
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

watch(noteText, (v) => emit('update:modelNote', v))
watch(activeTool, (t) => emit('tool-changed', { tool: t, color: highlightColor.value }))
watch(highlightColor, (c) => emit('tool-changed', { tool: activeTool.value, color: c }))

defineExpose({ activeTool, highlightColor, noteText })
</script>
