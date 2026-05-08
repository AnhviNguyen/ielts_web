<template>
  <div class="passage-card" @click="$emit('click')">
    <!-- Tags row -->
    <div class="tag-row">
      <span class="chip" :class="typeChip">{{ typeLabel }}</span>
      <span class="chip" :class="partChip">{{ partLabel }}</span>
      <span v-if="score" class="score-badge">Band {{ score }}</span>
      <span v-else class="chip" :class="diffChip">{{ diffLabel }}</span>
    </div>

    <!-- Title & excerpt -->
    <div class="passage-title">{{ title }}</div>
    <div class="passage-excerpt">{{ excerpt }}</div>

    <!-- Meta -->
    <div class="passage-meta">
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
  type:          { type: String, default: 'academic' }, // 'academic' | 'general'
  part:          { type: Number, default: 1 },           // 1 | 2 | 3
  difficulty:    { type: String, default: 'medium' },   // 'easy' | 'medium' | 'hard'
  questions:     { type: Number, default: 13 },
  minutes:       { type: Number, default: 20 },
  score:         { type: Number, default: null },
  completed:     { type: Boolean, default: false },
  completedDate: { type: String, default: '' },
})

defineEmits(['click'])

const typeLabel = computed(() => props.type === 'academic' ? 'Academic' : 'General')
const typeChip  = computed(() => props.type === 'academic' ? 'chip-blue' : 'chip-violet')

const partLabel = computed(() => `Part ${props.part}`)
const partChip  = computed(() => ['', 'chip-green', 'chip-gold', 'chip-amber'][props.part] ?? 'chip-green')

const diffLabel = computed(() => ({ easy: 'Dễ', medium: 'TB', hard: 'Khó' }[props.difficulty] ?? props.difficulty))
const diffChip  = computed(() => ({ easy: 'chip-green', medium: 'chip-gold', hard: 'chip-rose' }[props.difficulty] ?? ''))
</script>

<style scoped>
.passage-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 18px;
  cursor: pointer;
  transition: all 0.2s;
}

.passage-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.tag-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}

.chip-blue   { background: var(--blue-bg);   color: var(--blue); }
.chip-violet { background: var(--violet-bg); color: var(--violet); }
.chip-green  { background: var(--green-bg);  color: var(--green); }
.chip-gold   { background: var(--gold-bg);   color: var(--gold); }
.chip-amber  { background: var(--amber-bg);  color: var(--amber); }
.chip-rose   { background: var(--rose-bg);   color: var(--rose); }

.score-badge {
  background: var(--green-bg);
  color: var(--green);
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}

.passage-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
  line-height: 1.4;
  color: var(--ink);
}

.passage-excerpt {
  font-size: 12px;
  color: var(--ink3);
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.passage-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--ink3);
}

.passage-meta svg {
  vertical-align: middle;
  margin-right: 2px;
  opacity: 0.6;
}
</style>
