<template>
  <div class="card overflow-hidden">
    <!-- Header: toggle collapse -->
    <button
      class="flex w-full items-center justify-between px-4 py-3 text-left"
      @click="open = !open"
    >
      <div class="flex items-center gap-2">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="text-[12px] font-semibold text-[var(--ink)]">Transcript</span>
        <span class="rounded-full bg-[var(--bg2)] px-2 py-0.5 text-[10px] text-[var(--ink3)]">
          {{ segments.length }} đoạn
        </span>
      </div>
      <div class="flex items-center gap-2">
        <span class="font-mono text-[10px] text-[var(--ink3)]">{{ fmtTime(currentTime) }}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          class="transition-transform" :class="open ? 'rotate-180' : ''">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
    </button>

    <!-- Content (collapsible) -->
    <div v-show="open" class="max-h-52 overflow-y-auto border-t border-[var(--border)] px-3 py-2" ref="listEl">
      <div
        v-for="seg in segments"
        :key="seg.id"
        :ref="(el) => { if (el) segEls.set(seg.id, el) }"
        class="group mb-1 flex cursor-pointer gap-2 rounded-lg border px-2 py-1.5 transition-all"
        :class="isHighlighted(seg)
          ? 'border-[#34d399] bg-[#f0fdf4]'
          : 'border-transparent hover:bg-[var(--bg)]'"
        @click="$emit('seek', seg.from)"
      >
        <!-- Timestamp -->
        <span class="mt-0.5 shrink-0 font-mono text-[10px] text-[var(--ink3)]">{{ fmtTime(seg.from) }}</span>

        <!-- Text: bold when highlighted -->
        <span
          class="text-[12px] leading-relaxed transition-all"
          :class="isHighlighted(seg) ? 'font-semibold text-[var(--ink)]' : 'text-[var(--ink2)]'"
        >{{ seg.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  paragraphs:     { type: Array,  default: () => [] },
  currentTime:    { type: Number, default: 0 },
  /**
   * Set<string> of sentence IDs to highlight.
   * When non-empty this overrides the time-based single highlight.
   * Managed externally by useTranscript → passed down from QuizRunner.
   */
  highlightedIds: { type: Object, default: () => new Set() }, // Set<string>
})
defineEmits(['seek'])

const open   = ref(true)
const listEl = ref(null)
const segEls = new Map()

// ── segments ──────────────────────────────────────────────────────────────
const segments = computed(() => {
  const out = []
  for (const p of props.paragraphs) {
    for (const c of p.children || []) {
      if (!Number.isFinite(c.from) || !Number.isFinite(c.to)) continue
      out.push({ id: c.id, from: c.from, to: c.to, speaker: c.speaker, text: c.text })
    }
  }
  return out
})

// ── highlight logic ───────────────────────────────────────────────────────
/** Time-based fallback (single active sentence) */
const activeId = computed(() => {
  const t = props.currentTime || 0
  return segments.value.find(s => t >= s.from && t <= s.to)?.id ?? null
})

function isHighlighted(seg) {
  if (props.highlightedIds.size > 0) return props.highlightedIds.has(seg.id)
  return seg.id === activeId.value
}

// ── auto-scroll ───────────────────────────────────────────────────────────
async function scrollToSeg(id) {
  if (!id || !open.value) return
  await nextTick()
  const el = segEls.get(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

// Scroll to first forced ID when highlightedIds changes (question play)
watch(() => props.highlightedIds, async (ids) => {
  if (ids.size > 0) {
    const firstId = [...ids][0]
    await scrollToSeg(firstId)
  }
})

// Scroll to time-based active sentence when no forced highlight
watch(activeId, (id) => {
  if (props.highlightedIds.size === 0) scrollToSeg(id)
})

function fmtTime(sec) {
  const s = Math.max(0, Number(sec) || 0)
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const ss = Math.floor(s % 60).toString().padStart(2, '0')
  return `${m}:${ss}`
}
</script>
