<template>
  <!-- Thanh công cụ cố định bên trái, giữa màn hình (Reading / Listening practice) -->
  <div
    v-if="floating"
    class="fixed left-3 top-1/2 z-[150] flex -translate-y-1/2 flex-col items-center gap-2 sm:left-4"
  >
    <div class="relative">
      <button
        type="button"
        class="relative flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border shadow-sm transition-all hover:-translate-x-0.5 hover:shadow-md"
        :class="activeTool === 'highlight'
          ? 'border-amber-400 bg-amber-100 text-amber-800'
          : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-amber-300 hover:bg-amber-50'"
        title="Tô màu (T)"
        @click="setTool('highlight')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 19l7-7 3 3-7 7-3-3z"/>
          <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
          <path d="M2 2l7.586 7.586"/>
          <circle cx="11" cy="11" r="2"/>
        </svg>
        <span class="absolute bottom-0.5 right-1 text-[8px] font-bold leading-none opacity-50">T</span>
      </button>
      <Transition name="fade-colors">
        <div
          v-if="activeTool === 'highlight'"
          class="absolute left-[calc(100%+8px)] top-1/2 z-10 flex -translate-y-1/2 flex-col gap-1.5 rounded-xl border border-[var(--border)] bg-white p-1.5 shadow-lg"
        >
          <button
            v-for="c in COLORS"
            :key="c.value"
            type="button"
            :title="c.label"
            class="h-6 w-6 cursor-pointer rounded-lg border-2 transition-transform hover:scale-110"
            :class="highlightColor === c.value ? 'border-gray-700' : 'border-transparent'"
            :style="{ background: c.bg }"
            @click.stop="highlightColor = c.value"
          />
        </div>
      </Transition>
    </div>

    <button
      type="button"
      class="relative flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border shadow-sm transition-all hover:-translate-x-0.5 hover:shadow-md"
      :class="activeTool === 'note'
        ? 'border-blue-400 bg-blue-100 text-blue-800'
        : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-blue-300 hover:bg-blue-50'"
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
      class="relative flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl border shadow-sm transition-all hover:-translate-x-0.5 hover:shadow-md"
      :class="activeTool === 'vocab'
        ? 'border-emerald-600 bg-green-100 text-green-800'
        : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-emerald-500 hover:bg-green-50'"
      title="Tra từ (S)"
      @click="setTool('vocab')"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <span class="absolute bottom-0.5 right-1 text-[8px] font-bold leading-none opacity-50">S</span>
    </button>

    <div class="mx-auto my-0.5 h-px w-8 bg-[var(--border)]" />

    <div
      v-if="activeTool"
      class="max-w-[4.5rem] text-center text-[9px] leading-tight text-[var(--ink3)]"
    >
      {{ activeToolLabel }}
    </div>
  </div>

  <!-- Inline toolbar (review / legacy) -->
  <div
    v-else
    class="flex gap-2.5"
    :class="vertical
      ? 'flex-col items-start border-b-0 bg-transparent p-0'
      : 'flex-wrap items-center border-b border-[var(--border)] bg-[var(--surface)] px-3 py-1.5'"
  >
    <div class="flex gap-1" :class="vertical ? 'flex-col gap-2.5' : 'items-center'">
      <button
        type="button"
        :class="toolBtnClass('highlight')"
        title="Tô màu (T)"
        @click="setTool('highlight')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 19l7-7 3 3-7 7-3-3z"/>
          <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
          <path d="M2 2l7.586 7.586"/>
          <circle cx="11" cy="11" r="2"/>
        </svg>
        <span v-if="!iconOnly">Tô màu</span>
        <kbd v-if="!iconOnly" class="inline-flex h-4 w-4 items-center justify-center rounded border border-gray-300 bg-gray-100 text-[10px] text-gray-500">T</kbd>
      </button>

      <Transition name="fade-colors">
        <div
          v-if="activeTool === 'highlight'"
          class="flex gap-1"
          :class="vertical
            ? 'flex-col rounded-[10px] border border-[var(--border)] bg-white px-1 py-1.5 shadow-md'
            : 'items-center'"
        >
          <button
            v-for="c in COLORS"
            :key="c.value"
            type="button"
            :title="c.label"
            class="h-[18px] w-[18px] cursor-pointer rounded-full border-2 border-transparent transition-transform hover:scale-110"
            :class="highlightColor === c.value ? 'scale-110 border-gray-700' : ''"
            :style="{ background: c.bg }"
            @click.stop="highlightColor = c.value"
          />
        </div>
      </Transition>

      <div
        class="bg-[var(--border)]"
        :class="vertical ? 'mx-auto h-px w-6' : 'mx-1 h-5 w-px'"
      />

      <button
        type="button"
        :class="toolBtnClass('note')"
        title="Ghi chú (N)"
        @click="setTool('note')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <span v-if="!iconOnly">Ghi chú</span>
        <kbd v-if="!iconOnly" class="inline-flex h-4 w-4 items-center justify-center rounded border border-gray-300 bg-gray-100 text-[10px] text-gray-500">N</kbd>
      </button>

      <div
        class="bg-[var(--border)]"
        :class="vertical ? 'mx-auto h-px w-6' : 'mx-1 h-5 w-px'"
      />

      <button
        type="button"
        :class="toolBtnClass('vocab')"
        title="Tra từ (S)"
        @click="setTool('vocab')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span v-if="!iconOnly">Tra từ</span>
        <kbd v-if="!iconOnly" class="inline-flex h-4 w-4 items-center justify-center rounded border border-gray-300 bg-gray-100 text-[10px] text-gray-500">S</kbd>
      </button>
    </div>

    <div v-if="activeTool && !vertical && !floating" class="ml-auto flex items-center gap-1.5 text-[11px] text-[var(--ink3)]">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      {{ activeToolLabel }} đang bật · nhấn Esc hoặc click lại để tắt
    </div>
  </div>

  <Teleport to="body">
    <Transition name="slide-right">
      <div
        v-if="activeTool === 'note'"
        class="fixed right-0 top-0 z-[200] flex h-screen w-80 flex-col border-l border-[var(--border)] bg-[var(--surface)] shadow-[-4px_0_20px_rgba(0,0,0,0.08)]"
      >
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3.5">
          <div class="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Ghi chú
          </div>
          <button
            type="button"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-md border-0 bg-transparent text-[var(--ink3)] hover:bg-[var(--surface2)]"
            @click="setTool('note')"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <textarea
          :value="modelNote"
          class="flex-1 resize-none border-0 bg-transparent px-4 py-3.5 text-[13px] leading-relaxed text-[var(--ink)] outline-none"
          placeholder="Ghi chú của bạn tại đây..."
          @input="$emit('update:modelNote', $event.target.value)"
        />
        <div class="border-t border-[var(--border)] px-4 py-2">
          <span class="text-[10px] text-[var(--ink3)]">{{ modelNote.length }} ký tự</span>
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
  floating: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelNote', 'tool-changed'])

const { activeTool, setTool } = useReadingTools()
const highlightColor = ref('yellow')

const COLORS = [
  { value: 'yellow', label: 'Vàng',     bg: '#fef08a' },
  { value: 'green',  label: 'Xanh lá',  bg: '#bbf7d0' },
  { value: 'rose',   label: 'Hồng',     bg: '#fecdd3' },
  { value: 'blue',   label: 'Xanh lam', bg: '#bfdbfe' },
]

const TOOL_LABELS = {
  highlight: 'Tô màu',
  note: 'Ghi chú',
  vocab: 'Tra từ',
}

const activeToolLabel = computed(() => TOOL_LABELS[activeTool.value] || '')

const TOOL_ACTIVE = {
  highlight: 'border-amber-400 bg-amber-100 text-amber-800',
  note: 'border-blue-400 bg-blue-100 text-blue-800',
  vocab: 'border-emerald-400 bg-green-100 text-green-800',
}

function toolBtnClass(tool) {
  const base = props.vertical
    ? 'flex h-12 w-12 cursor-pointer items-center justify-center rounded-xl border border-[var(--border)] bg-white p-0 shadow-md transition-all hover:bg-[var(--surface2)]'
    : 'inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-transparent bg-transparent px-2.5 py-1 text-xs text-[var(--ink2)] transition-all hover:bg-[var(--surface2)]'
  if (activeTool.value !== tool) return base
  return `${base} ${TOOL_ACTIVE[tool] || ''}`
}

watch(activeTool, (t) => {
  emit('tool-changed', { tool: t, color: highlightColor.value })
})

watch(highlightColor, (c) => {
  emit('tool-changed', { tool: activeTool.value, color: c })
})

defineExpose({ activeTool, highlightColor })
</script>
