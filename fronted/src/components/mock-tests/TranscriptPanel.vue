<template>
  <div class="card overflow-hidden">
    <!-- Header: toggle collapse + controls -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
      <button
        class="flex items-center gap-2 text-left"
        @click="open = !open"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="text-[12px] font-semibold text-[var(--ink)]">Transcript</span>
        <span class="rounded-full bg-[var(--bg2)] px-2 py-0.5 text-[10px] text-[var(--ink3)]">
          {{ filteredSegments.length }}<template v-if="searchQuery"> / {{ segments.length }}</template>
        </span>
      </button>

      <div class="flex items-center gap-2">
        <span class="font-mono text-[10px] text-[var(--ink3)]">{{ fmtTime(currentTime) }}</span>

        <!-- Search toggle -->
        <button
          class="flex h-6 w-6 items-center justify-center rounded transition-colors"
          :class="showSearch ? 'bg-[#34d399] text-white' : 'text-[var(--ink3)] hover:bg-[var(--bg2)]'"
          title="Tìm kiếm trong transcript"
          @click="toggleSearch"
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </button>

        <!-- Expand/collapse height -->
        <button
          class="flex h-6 w-6 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)] transition-colors"
          :title="expanded ? 'Thu nhỏ transcript' : 'Mở rộng transcript'"
          @click="expanded = !expanded"
        >
          <svg v-if="!expanded" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
          <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 14h6m0 0v6m0-6l-7 7m17-11h-6m0 0V4m0 6l7-7"/></svg>
        </button>

        <!-- Collapse chevron -->
        <button @click="open = !open" class="flex h-6 w-6 items-center justify-center rounded text-[var(--ink3)] hover:bg-[var(--bg2)]">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            class="transition-transform" :class="open ? 'rotate-180' : ''">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Search bar -->
    <div v-show="showSearch && open" class="border-b border-[var(--border)] px-3 py-2">
      <div class="relative">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--ink3)]" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          class="w-full rounded-lg border border-[var(--border2)] bg-[var(--bg)] py-1.5 pl-7 pr-3 text-[12px] outline-none focus:border-[#34d399]"
          placeholder="Tìm từ trong transcript..."
          @keydown.escape="clearSearch"
        />
        <button v-if="searchQuery" @click="clearSearch" class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--ink3)] hover:text-[var(--ink)]">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>

    <!-- Content (collapsible) -->
    <div
      v-show="open"
      class="overflow-y-auto border-t border-[var(--border)] px-3 py-2 transition-all"
      :style="{ height: expanded ? 'calc(100vh - 380px)' : '13rem', maxHeight: expanded ? 'none' : '13rem' }"
      ref="listEl"
    >
      <div v-if="!filteredSegments.length && searchQuery" class="py-6 text-center text-[12px] text-[var(--ink3)]">
        Không tìm thấy "{{ searchQuery }}" trong transcript.
      </div>

      <div
        v-for="seg in filteredSegments"
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

        <!-- Text: bold when highlighted, with search highlight -->
        <span
          class="text-[12px] leading-relaxed transition-all"
          :class="isHighlighted(seg) ? 'font-semibold text-[var(--ink)]' : 'text-[var(--ink2)]'"
          v-html="sanitizeQuizHtml(highlightSearch(seg.text))"
        ></span>

        <!-- Save-to-vocab button (visible on hover) -->
        <button
          v-if="$attrs.onSaveWord"
          class="ml-auto shrink-0 opacity-0 group-hover:opacity-100 flex h-5 w-5 items-center justify-center rounded text-[var(--ink3)] hover:bg-[#34d399] hover:text-white transition-all"
          title="Lưu từ vựng"
          @click.stop="$emit('save-word', seg.text)"
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { sanitizeQuizHtml } from '@/utils/sanitizeHtml.js'

const props = defineProps({
  paragraphs:     { type: Array,  default: () => [] },
  currentTime:    { type: Number, default: 0 },
  highlightedIds: { type: Object, default: () => new Set() },
})
defineEmits(['seek', 'save-word'])

const open     = ref(true)
const expanded = ref(false)
const listEl   = ref(null)
const segEls   = new Map()

// ── Search ────────────────────────────────────────────────────────────────
const showSearch   = ref(false)
const searchQuery  = ref('')
const searchInputRef = ref(null)

function toggleSearch() {
  showSearch.value = !showSearch.value
  if (showSearch.value) {
    nextTick(() => searchInputRef.value?.focus())
  } else {
    clearSearch()
  }
}

function clearSearch() {
  searchQuery.value = ''
  showSearch.value  = false
}

function highlightSearch(text) {
  if (!searchQuery.value) return text
  const escaped = searchQuery.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const re = new RegExp(`(${escaped})`, 'gi')
  return text.replace(re, '<mark style="background:#fef08a;border-radius:2px;padding:0 1px">$1</mark>')
}

// ── Segments ──────────────────────────────────────────────────────────────
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

const filteredSegments = computed(() => {
  if (!searchQuery.value) return segments.value
  const q = searchQuery.value.toLowerCase()
  return segments.value.filter(s => s.text.toLowerCase().includes(q))
})

// ── Highlight logic ───────────────────────────────────────────────────────
const activeId = computed(() => {
  const t = props.currentTime || 0
  return segments.value.find(s => t >= s.from && t <= s.to)?.id ?? null
})

function isHighlighted(seg) {
  if (props.highlightedIds.size > 0) return props.highlightedIds.has(seg.id)
  return seg.id === activeId.value
}

// ── Auto-scroll ───────────────────────────────────────────────────────────
async function scrollToSeg(id) {
  if (!id || !open.value) return
  await nextTick()
  const el = segEls.get(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

watch(() => props.highlightedIds, async (ids) => {
  if (ids.size > 0) {
    const firstId = [...ids][0]
    await scrollToSeg(firstId)
  }
})

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
