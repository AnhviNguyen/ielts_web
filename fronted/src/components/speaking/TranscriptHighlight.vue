<template>
  <div class="card p-5">
    <div class="mb-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="text-[var(--ink2)]"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Transcript</span>
      </div>
      <button
        class="flex items-center gap-1 rounded px-2 py-1 text-[11px] text-[#34d399] transition hover:bg-[#34d39911]"
        @click="copyText"
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
    </div>

    <p v-if="!transcript" class="text-sm italic text-[var(--ink3)]">No transcript available.</p>

    <!-- Word-level highlights when timestamps available -->
    <div v-else-if="wordTimestamps && wordTimestamps.length" class="flex flex-wrap gap-x-1 gap-y-1 leading-relaxed">
      <span
        v-for="(w, i) in wordTimestamps"
        :key="i"
        class="cursor-default rounded px-0.5 text-sm transition-colors"
        :class="wordClass(w)"
        :title="wordTitle(w)"
      >{{ w.word }}</span>
    </div>

    <!-- Plain text fallback -->
    <p v-else class="text-sm leading-relaxed text-[var(--ink)]">{{ transcript }}</p>

    <!-- Legend -->
    <div v-if="wordTimestamps && wordTimestamps.length" class="mt-3 flex flex-wrap items-center gap-3 border-t border-[var(--border)] pt-3">
      <span class="text-[10px] font-semibold uppercase text-[var(--ink3)]">Pronunciation:</span>
      <span class="flex items-center gap-1 text-[10px] text-[var(--ink2)]"><span class="inline-block h-2 w-2 rounded-full bg-[#34d399]"></span> Good</span>
      <span class="flex items-center gap-1 text-[10px] text-[var(--ink2)]"><span class="inline-block h-2 w-2 rounded-full bg-[#f59e0b]"></span> Improve</span>
      <span class="flex items-center gap-1 text-[10px] text-[var(--ink2)]"><span class="inline-block h-2 w-2 rounded-full bg-[#f43f5e]"></span> Poor</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  transcript:     { type: String, default: '' },
  wordTimestamps: { type: Array,  default: () => [] },
})

const copied = ref(false)

function wordClass(w) {
  const s = w.score ?? 1
  if (s >= 0.8) return 'text-[var(--ink)]'
  if (s >= 0.6) return 'rounded bg-[#fef3c7] text-[#92400e] font-medium'
  return 'rounded bg-[#fee2e2] text-[#991b1b] font-medium'
}

function wordTitle(w) {
  const s = w.score ?? 1
  if (s >= 0.8) return ''
  if (s >= 0.6) return 'Pronunciation needs improvement'
  return 'Poor pronunciation – review this word'
}

async function copyText() {
  try {
    await navigator.clipboard.writeText(props.transcript)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1500)
  } catch {}
}
</script>
