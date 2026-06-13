<template>
  <div
    class="group relative overflow-hidden rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    :class="accent ? 'border-emerald-100' : ''"
  >
    <div
      v-if="accent"
      class="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-emerald-50 opacity-80"
    />
    <div class="relative flex items-start justify-between gap-3">
      <div class="min-w-0">
        <div class="text-[11px] font-bold uppercase tracking-wide text-[var(--ink3)]">{{ label }}</div>
        <div class="mt-1.5 text-2xl font-bold tabular-nums text-[var(--ink)]">{{ value }}</div>
        <div v-if="hint" class="mt-1 text-xs text-[var(--ink3)]">{{ hint }}</div>
      </div>
      <div
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
        :style="{ backgroundColor: `${color}18`, color }"
        v-html="icon"
      />
    </div>
    <div v-if="trend != null" class="relative mt-3 flex items-center gap-1 text-xs font-semibold" :class="trend >= 0 ? 'text-emerald-600' : 'text-rose-600'">
      <span>{{ trend >= 0 ? '↑' : '↓' }} {{ Math.abs(trend) }}%</span>
      <span class="font-normal text-[var(--ink3)]">so với hôm qua</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: '' },
  icon: { type: String, default: '' },
  color: { type: String, default: '#059669' },
  accent: { type: Boolean, default: false },
  trend: { type: Number, default: null },
})
</script>
