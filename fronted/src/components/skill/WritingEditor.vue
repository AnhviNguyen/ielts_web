<template>
  <div class="flex h-full flex-col rounded-[var(--r)] border border-[var(--border)] bg-[var(--surface)]">
    <div class="flex shrink-0 items-center justify-between border-b border-[var(--border)] px-4 py-2.5">
      <div class="flex gap-1.5">
        <button type="button" class="flex h-[30px] w-[30px] cursor-pointer items-center justify-center rounded-md border border-[var(--border2)] bg-[var(--bg)] text-[13px] text-[var(--ink2)] transition-colors hover:bg-[var(--border)]" title="Bold" @click="execCmd('bold')"><b>B</b></button>
        <button type="button" class="flex h-[30px] w-[30px] cursor-pointer items-center justify-center rounded-md border border-[var(--border2)] bg-[var(--bg)] text-[13px] text-[var(--ink2)] transition-colors hover:bg-[var(--border)]" title="Italic" @click="execCmd('italic')"><i>I</i></button>
        <button type="button" class="flex h-[30px] w-[30px] cursor-pointer items-center justify-center rounded-md border border-[var(--border2)] bg-[var(--bg)] text-[13px] text-[var(--ink2)] transition-colors hover:bg-[var(--border)]" title="Undo" @click="execCmd('undo')">↩</button>
        <button type="button" class="flex h-[30px] w-[30px] cursor-pointer items-center justify-center rounded-md border border-[var(--border2)] bg-[var(--bg)] text-[13px] text-[var(--ink2)] transition-colors hover:bg-[var(--border)]" title="Redo" @click="execCmd('redo')">↪</button>
      </div>
      <div class="text-xs text-[var(--ink3)]">
        Số từ: <span class="font-bold" :class="wordCount >= minWords ? 'text-[var(--green)]' : wordCount > 0 ? 'text-[var(--amber)]' : 'text-[var(--ink)]'">{{ wordCount }}</span>
        / {{ minWords }}+
      </div>
    </div>

    <textarea
      class="min-h-[200px] flex-1 resize-none border-0 bg-transparent px-5 py-5 font-[var(--font-body)] text-sm leading-[1.9] text-[var(--ink)] outline-none"
      :placeholder="placeholder"
      :value="modelValue"
      @input="handleInput"
    />

    <div class="flex shrink-0 items-center justify-between border-t border-[var(--border)] px-4 py-3">
      <div class="flex gap-2">
        <button type="button" class="inline-flex cursor-pointer items-center gap-1.5 rounded-[var(--r-sm)] border-0 bg-transparent px-3 py-1.5 font-[var(--font-body)] text-xs font-semibold text-[var(--ink2)] transition-colors hover:bg-[var(--bg2)]" @click="$emit('save')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          Lưu nháp
        </button>
        <button type="button" class="inline-flex cursor-pointer items-center gap-1.5 rounded-[var(--r-sm)] border-0 bg-transparent px-3 py-1.5 font-[var(--font-body)] text-xs font-semibold text-[var(--ink2)] transition-colors hover:bg-[var(--bg2)]" @click="$emit('aiHint')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 1v2M15 1v2M9 21v2M15 21v2M1 9h2M1 15h2M21 9h2M21 15h2"/><rect x="2" y="2" width="20" height="20" rx="2"/></svg>
          AI gợi ý
        </button>
      </div>
      <button type="button" class="inline-flex cursor-pointer items-center gap-1.5 rounded-[var(--r-sm)] border-0 bg-[var(--green)] px-[18px] py-2 text-[13px] font-semibold text-white transition-all hover:-translate-y-px hover:bg-[#245c42] hover:shadow-[0_4px_12px_rgba(45,106,79,0.3)]" @click="$emit('submit')">
        Nộp bài & Chấm điểm ✓
      </button>
    </div>
  </div>
</template>

<script setup>
import { useWordCount } from '@/composables/useWordCount.js'

const props = defineProps({
  modelValue:  { type: String, default: '' },
  placeholder: { type: String, default: 'Bắt đầu viết bài...' },
  minWords:    { type: Number, default: 150 },
})

const emit = defineEmits(['update:modelValue', 'save', 'aiHint', 'submit'])

const { wordCount, updateText } = useWordCount()

function handleInput(e) {
  const val = e.target.value
  emit('update:modelValue', val)
  updateText(val)
}

function execCmd(cmd) {
  document.execCommand(cmd)
}
</script>
