<template>
  <article class="fe-card group flex flex-col overflow-hidden rounded-xl border border-[var(--border)] bg-white transition-shadow hover:shadow-md">
    <!-- Cover từ thumbnail mock test (backend/data) -->
    <div class="relative aspect-[16/9] w-full overflow-hidden bg-[#e8f5f0]">
      <img
        v-if="set.thumbnail && !imgErr"
        :src="`/api/images/${set.thumbnail}`"
        :alt="displayTitle"
        class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
        loading="lazy"
        @error="imgErr = true"
      />
      <div
        v-else
        class="flex h-full w-full flex-col items-center justify-center gap-1 text-[#34d399]"
      >
        <span class="text-2xl font-bold">{{ iconText }}</span>
        <span v-if="set.book_code" class="text-[11px] font-medium text-[var(--ink3)]">{{ set.book_code }}</span>
      </div>
      <div class="pointer-events-none absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/35 to-transparent" />
      <span class="absolute left-3 top-3 fe-badge fe-badge--gold shadow-sm">Full IELTS Mock</span>
      <span v-if="set.test_number" class="absolute right-3 top-3 fe-badge fe-badge--dark">
        Test {{ set.test_number }}
      </span>
    </div>

    <div class="flex flex-1 flex-col p-4">
      <h3 class="text-[14px] font-semibold leading-snug text-[var(--ink)] line-clamp-2">
        {{ displayTitle }}
      </h3>
      <p v-if="set.book_code" class="mt-1 text-[11px] font-medium text-[var(--ink3)]">{{ set.book_code }}</p>

      <ul class="mt-3 space-y-1.5">
        <li
          v-for="skill in skillRows"
          :key="skill.key"
          class="flex items-center gap-2 text-[12px]"
        >
          <span
            class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[#f0fdf4] text-[#059669]"
            v-html="skill.icon"
          />
          <span class="min-w-0 flex-1 truncate font-medium text-[var(--ink2)]">{{ skill.label }}</span>
          <span class="shrink-0 tabular-nums text-[var(--ink3)]">{{ skill.minutes }}′</span>
        </li>
      </ul>

      <div class="mt-4 flex items-center justify-between gap-3 border-t border-[var(--border)] pt-3">
        <div class="text-[12px] text-[var(--ink3)]">
          <span class="font-semibold text-[var(--ink)]">~{{ set.total_minutes }}</span> phút tổng
        </div>
        <div class="profile-page shrink-0">
          <button
            type="button"
            class="fe-start-btn btn btn-primary"
            @click="$emit('start', set)"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Bắt đầu
          </button>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  set: { type: Object, required: true },
})
defineEmits(['start'])

const imgErr = ref(false)
watch(() => props.set?.thumbnail, () => {
  imgErr.value = false
})

const SKILL_META = [
  {
    key: 'reading',
    label: 'Reading',
    minutesKey: 'reading_minutes',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  },
  {
    key: 'listening',
    label: 'Listening',
    minutesKey: 'listening_minutes',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/></svg>`,
  },
  {
    key: 'writing',
    label: 'Writing (T1 + T2)',
    minutesKey: 'writing_minutes',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  },
  {
    key: 'speaking',
    label: 'Speaking',
    minutesKey: 'speaking_minutes',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>`,
  },
]

const displayTitle = computed(() => {
  const raw = props.set?.title || ''
  return raw
    .replace(/\s*\([^)]*\)\s*/g, ' ')
    .replace(/[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
})

const iconText = computed(() => {
  const book = props.set?.book || ''
  const m = book.match(/Orange Test\s+(\d+)/i)
  if (m) return `T${m[1]}`
  if (book) return book.slice(0, 2).toUpperCase()
  return 'FM'
})

const skillRows = computed(() => {
  const t = props.set?.timers || {}
  const w1 = t.writing_task1_minutes ?? 20
  const w2 = t.writing_task2_minutes ?? 40
  return SKILL_META.map((s) => ({
    ...s,
    minutes:
      s.key === 'writing'
        ? w1 + w2
        : t[s.minutesKey] ?? (s.key === 'reading' ? 60 : s.key === 'listening' ? 30 : 15),
  }))
})
</script>

<style scoped>
.fe-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 600;
}
.fe-badge--gold {
  background: #fef9c3;
  color: #92400e;
}
.fe-badge--dark {
  background: rgba(15, 23, 42, 0.65);
  color: #fff;
  backdrop-filter: blur(4px);
}
.fe-start-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 12px;
}
</style>
