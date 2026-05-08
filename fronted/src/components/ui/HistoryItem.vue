<template>
  <!-- HistoryItem — ISP: chỉ nhận props cần thiết -->
  <div class="history-item" @click="$emit('click')">
    <div class="hist-icon" :style="{ background: skill.colorBg }">
      <span v-html="skill.icon" :style="{ color: skill.colorHex }"></span>
    </div>
    <div class="hist-info">
      <div class="hist-title">{{ title }}</div>
      <div class="hist-meta">{{ date }} · {{ duration }} · {{ modeLabel }}</div>
    </div>
    <div class="hist-score" :style="{ color: skill.colorHex }">{{ score }}</div>
    <slot name="actions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getSkill } from '@/composables/useIeltsSkills.js'

const props = defineProps({
  skillId:  { type: String, required: true },
  title:    { type: String, required: true },
  date:     { type: String, required: true },
  duration: { type: String, default: '' },
  score:    { type: [Number, String], default: '—' },
  mode:     { type: String, default: 'practice' }, // 'practice' | 'exam' | 'flashcard'
})

defineEmits(['click'])

const skill     = computed(() => getSkill(props.skillId))
const modeLabel = computed(() => ({
  practice:  'Luyện tập',
  exam:      'Thi thật',
  flashcard: 'Flashcard',
}[props.mode] ?? props.mode))
</script>

<style scoped>
.history-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
  cursor: pointer;
}

.history-item:last-child { border-bottom: none; }
.history-item:hover { background: var(--bg); }

.hist-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hist-info { flex: 1; min-width: 0; }

.hist-title {
  font-size: 13.5px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--ink);
}

.hist-meta {
  font-size: 12px;
  color: var(--ink3);
  margin-top: 2px;
}

.hist-score {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}
</style>
