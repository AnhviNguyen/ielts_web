<template>
  <div
    class="flex cursor-pointer items-center gap-3.5 border-b border-[var(--border)] px-[18px] py-3.5 transition-colors last:border-b-0 hover:bg-[var(--bg)]"
    @click="$emit('click')"
  >
    <div
      class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px]"
      :style="{ background: skill.colorBg }"
    >
      <span v-html="skill.icon" :style="{ color: skill.colorHex }"></span>
    </div>
    <div class="min-w-0 flex-1">
      <div class="truncate text-[13.5px] font-semibold text-[var(--ink)]">{{ title }}</div>
      <div class="mt-0.5 text-xs text-[var(--ink3)]">{{ date }} · {{ duration }} · {{ modeLabel }}</div>
    </div>
    <div class="shrink-0 font-display text-lg font-bold" :style="{ color: skill.colorHex }">{{ score }}</div>
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
  mode:     { type: String, default: 'practice' },
})

defineEmits(['click'])

const skill     = computed(() => getSkill(props.skillId))
const modeLabel = computed(() => ({
  practice:  'Luyện tập',
  exam:      'Thi thật',
  flashcard: 'Flashcard',
}[props.mode] ?? props.mode))
</script>
