<template>
  <div class="flex gap-1.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
    <RouterLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="admin-quick-link group flex shrink-0 items-center gap-2 rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-xs font-semibold text-[var(--ink2)] shadow-sm transition-all"
      :style="{ '--link-accent': link.color || '#059669' }"
      :title="link.label"
    >
      <span
        class="admin-quick-icon flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--bg)] text-[var(--ink3)] transition-colors"
        v-html="link.icon"
      />
      <span class="whitespace-nowrap">{{ link.label }}</span>
      <span
        v-if="link.count != null"
        class="rounded-full px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-white"
        :style="{ background: link.color || '#059669' }"
      >{{ link.count }}</span>
    </RouterLink>
  </div>
</template>

<script setup>
defineProps({
  links: { type: Array, default: () => [] },
})
</script>
