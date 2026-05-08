<template>
  <div class="relative" :class="wrapperClass">
    <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink3)]">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    </span>
    <input
      :value="modelValue"
      :placeholder="placeholder"
      :id="id"
      class="w-full rounded-[var(--r-sm)] border border-[var(--border2)] bg-[var(--surface)] px-3 py-2 pl-8 text-[13px] text-[var(--ink)] outline-none transition-colors focus:border-[var(--green-l)]"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Tìm kiếm...' },
  id: { type: String, default: undefined },
  wrapperClass: { type: String, default: '' },
})

defineEmits(['update:modelValue'])
</script>
