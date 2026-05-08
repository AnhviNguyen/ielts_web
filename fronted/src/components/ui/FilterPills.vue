<template>
  <div class="flex flex-wrap gap-1.5">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors"
      :class="modelValue === option.value
        ? 'border-[var(--ink)] bg-[var(--ink)] text-white'
        : 'border-[var(--border2)] bg-[var(--surface)] text-[var(--ink2)] hover:border-[var(--ink3)]'"
      @click="$emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
})

defineEmits(['update:modelValue'])
</script>
