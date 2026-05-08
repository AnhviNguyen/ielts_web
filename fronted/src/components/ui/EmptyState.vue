<template>
  <div class="rounded-[var(--r)] border border-[var(--border)] bg-[var(--surface)] px-5 py-14 text-center">
    <div class="mb-4 text-5xl">{{ icon }}</div>
    <div class="font-display mb-2 text-xl font-semibold text-[var(--ink)]">{{ title }}</div>
    <div class="mb-5 text-[13px] text-[var(--ink3)]">{{ description }}</div>
    <router-link
      :to="actionTo"
      class="inline-flex items-center rounded-[var(--r-sm)] bg-[var(--green)] px-5 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-[#245c42]"
    >
      {{ actionLabel }}
    </router-link>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '📋' },
  title: { type: String, required: true },
  description: { type: String, required: true },
  actionLabel: { type: String, required: true },
  actionTo: { type: String, required: true },
})
</script>
