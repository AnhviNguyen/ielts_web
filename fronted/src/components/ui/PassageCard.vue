<template>
  <div
    class="cursor-pointer rounded-[var(--r)] border border-[var(--border)] bg-[var(--surface)] p-[18px] transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow)]"
    @click="$emit('click')"
  >
    <div class="mb-2.5 flex flex-wrap gap-1.5">
      <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold" :class="typeChip">{{ typeLabel }}</span>
      <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold" :class="partChip">{{ partLabel }}</span>
      <span v-if="score" class="rounded-full bg-[var(--green-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--green)]">Band {{ score }}</span>
      <span v-else class="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold" :class="diffChip">{{ diffLabel }}</span>
    </div>

    <div class="mb-1.5 text-sm font-semibold leading-snug text-[var(--ink)]">{{ title }}</div>
    <div class="mb-3 line-clamp-2 text-xs leading-relaxed text-[var(--ink3)]">{{ excerpt }}</div>

    <div class="flex items-center justify-between text-[11px] text-[var(--ink3)] [&_svg]:mr-0.5 [&_svg]:inline [&_svg]:opacity-60">
      <span>
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        {{ questions }} câu · ~{{ minutes }} phút
      </span>
      <span v-if="completed">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        {{ completedDate }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title:         { type: String, required: true },
  excerpt:       { type: String, default: '' },
  type:          { type: String, default: 'academic' },
  part:          { type: Number, default: 1 },
  difficulty:    { type: String, default: 'medium' },
  questions:     { type: Number, default: 13 },
  minutes:       { type: Number, default: 20 },
  score:         { type: Number, default: null },
  completed:     { type: Boolean, default: false },
  completedDate: { type: String, default: '' },
})

defineEmits(['click'])

const typeLabel = computed(() => props.type === 'academic' ? 'Academic' : 'General')
const typeChip  = computed(() => props.type === 'academic' ? 'bg-[var(--blue-bg)] text-[var(--blue)]' : 'bg-[var(--violet-bg)] text-[var(--violet)]')

const partLabel = computed(() => `Part ${props.part}`)
const partChip  = computed(() => {
  const map = ['', 'bg-[var(--green-bg)] text-[var(--green)]', 'bg-[var(--gold-bg)] text-[var(--gold)]', 'bg-[var(--amber-bg)] text-[var(--amber)]']
  return map[props.part] ?? 'bg-[var(--green-bg)] text-[var(--green)]'
})

const diffLabel = computed(() => ({ easy: 'Dễ', medium: 'TB', hard: 'Khó' }[props.difficulty] ?? props.difficulty))
const diffChip  = computed(() => ({
  easy: 'bg-[var(--green-bg)] text-[var(--green)]',
  medium: 'bg-[var(--gold-bg)] text-[var(--gold)]',
  hard: 'bg-[var(--rose-bg)] text-[var(--rose)]',
}[props.difficulty] ?? ''))
</script>
