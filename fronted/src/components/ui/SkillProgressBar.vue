<template>
  <div class="w-full">
    <div class="mb-1 flex justify-between text-[11px] text-[var(--ink3)]">
      <span class="font-medium">{{ label }}</span>
      <span class="font-bold text-[var(--ink2)]">{{ value }}%</span>
    </div>
    <div class="h-2 overflow-hidden rounded-full bg-[var(--bg2)]">
      <div
        class="h-full rounded-full transition-[width] duration-500 ease-out"
        :style="{ width: value + '%', background: color }"
      />
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: Number, required: true },
  color: { type: String, default: 'var(--green-l)' },
})
</script>
