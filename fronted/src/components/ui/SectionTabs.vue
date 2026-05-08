<template>
  <div class="mb-5 flex border-b-2 border-[var(--border)]">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="-mb-0.5 flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-[13px] font-semibold transition-colors"
      :class="modelValue === tab.id
        ? 'border-[var(--ink)] text-[var(--ink)]'
        : 'border-transparent text-[var(--ink3)] hover:text-[var(--ink2)]'"
      @click="$emit('update:modelValue', tab.id)"
    >
      <span v-if="tab.icon" v-html="tab.icon"></span>
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, required: true },
  tabs: { type: Array, default: () => [] },
})

defineEmits(['update:modelValue'])
</script>
