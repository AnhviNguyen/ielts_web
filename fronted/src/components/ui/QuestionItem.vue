<template>
  <div class="mb-[18px]">
    <div class="mb-1.5 text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]">Question {{ number }}</div>
    <div class="mb-2.5 text-[13.5px] font-medium leading-relaxed text-[var(--ink)]">{{ question }}</div>

    <input
      v-if="type === 'fill'"
      class="ct-input w-full border-[1.5px]"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <div v-else-if="type === 'mcq'" class="flex flex-col gap-1.5">
      <div
        v-for="(opt, idx) in options"
        :key="idx"
        class="flex cursor-pointer items-center gap-2 rounded-[var(--r-sm)] border-[1.5px] px-3 py-2 text-[13px] transition-all"
        :class="modelValue === idx
          ? 'border-[var(--blue-l)] bg-[var(--blue-bg)] text-[var(--ink2)]'
          : 'border-[var(--border)] bg-[var(--bg)] text-[var(--ink2)] hover:border-[var(--blue-l)] hover:bg-[var(--blue-bg)]'"
        @click="$emit('update:modelValue', idx)"
      >
        <div
          class="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full text-[11px] font-bold"
          :class="modelValue === idx ? 'bg-[var(--blue-l)] text-white' : 'bg-[var(--border)]'"
        >{{ letters[idx] }}</div>
        {{ opt }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type:        { type: String, default: 'fill' },
  number:      { type: Number, required: true },
  question:    { type: String, required: true },
  options:     { type: Array, default: () => [] },
  modelValue:  { default: null },
  placeholder: { type: String, default: 'Điền câu trả lời...' },
})

defineEmits(['update:modelValue'])

const letters = ['A', 'B', 'C', 'D', 'E']
</script>
