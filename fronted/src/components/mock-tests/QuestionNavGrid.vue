<template>
  <!-- Horizontal scrollable navigation bar like Cathoven -->
  <div class="overflow-hidden rounded-xl border border-[var(--border)] bg-white">
    <div class="flex items-center overflow-x-auto px-3 py-2.5 gap-1 scrollbar-hide">
      <template v-for="group in groups" :key="group.partId">
        <!-- Part label pill -->
        <button
          class="shrink-0 flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[12px] font-semibold transition-colors whitespace-nowrap"
          :class="group.hasCurrent
            ? 'border-[#111] bg-[#111] text-white'
            : 'border-[var(--border2)] bg-white text-[var(--ink)]'"
          @click="$emit('go', group.questions[0]?.order)"
        >
          {{ group.label }}
          <span class="text-[10px] font-normal opacity-70">{{ group.answered }}/{{ group.questions.length }}</span>
        </button>

        <!-- Question circles -->
        <button
          v-for="q in group.questions"
          :key="q.order"
          class="shrink-0 flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-semibold transition-colors border"
          :class="circleClass(q)"
          @click="$emit('go', q.order)"
        >{{ q.order }}</button>
      </template>
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-4 border-t border-[var(--border)] px-3 py-1.5 text-[10px] text-[var(--ink3)]">
      <div class="flex items-center gap-1">
        <span class="inline-block h-3 w-3 rounded-full border border-[var(--border2)] bg-white"></span> Chưa làm
      </div>
      <div class="flex items-center gap-1">
        <span class="inline-block h-3 w-3 rounded-full border border-[#34d399] bg-[#f0fdf4]"></span> Đã làm
      </div>
      <div class="flex items-center gap-1">
        <span class="inline-block h-3 w-3 rounded-full bg-[#111]"></span> Đang làm
      </div>
      <div class="ml-auto font-medium text-[var(--ink2)]">{{ totalAnswered }}/{{ totalQuestions }} câu</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  questions:    { type: Array,  default: () => [] }, // [{order, id, partId?, partLabel?}]
  navParts:     { type: Array,  default: () => [] }, // [{id, label, questions:[{order,id}]}]
  currentOrder: { type: Number, default: 0 },
  answeredMap:  { type: Object, default: () => ({}) },
})
defineEmits(['go'])

const groups = computed(() => {
  // If structured parts provided, use them
  if (props.navParts?.length) {
    return props.navParts.map(p => ({
      partId: p.id,
      label:  p.label,
      questions: p.questions,
      hasCurrent: p.questions.some(q => q.order === props.currentOrder),
      answered:   p.questions.filter(q => props.answeredMap?.[q.id] !== undefined).length,
    }))
  }
  // Fallback: single group with all questions
  return [{
    partId: 0,
    label: 'Câu hỏi',
    questions: props.questions,
    hasCurrent: props.questions.some(q => q.order === props.currentOrder),
    answered: props.questions.filter(q => props.answeredMap?.[q.id] !== undefined).length,
  }]
})

const totalQuestions = computed(() => props.questions.length || groups.value.reduce((s, g) => s + g.questions.length, 0))
const totalAnswered  = computed(() => Object.keys(props.answeredMap || {}).length)

function circleClass(q) {
  const isCurrent  = q.order === props.currentOrder
  const isAnswered = props.answeredMap?.[q.id] !== undefined
  if (isCurrent)  return 'bg-[#111] border-[#111] text-white'
  if (isAnswered) return 'bg-[#f0fdf4] border-[#34d399] text-[#065f46]'
  return 'bg-white border-[var(--border2)] text-[var(--ink3)] hover:border-[var(--ink2)]'
}
</script>

