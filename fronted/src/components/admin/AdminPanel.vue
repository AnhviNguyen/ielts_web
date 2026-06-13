<template>
  <section
    class="overflow-hidden rounded-xl border border-[var(--border)] bg-white shadow-sm"
    :class="accent ? 'admin-panel-accent' : ''"
    :style="accent ? accentStyle : undefined"
  >
    <div v-if="title || $slots.action" class="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] px-4 py-3">
      <div>
        <h2 v-if="title" class="text-sm font-bold text-[var(--ink)]">{{ title }}</h2>
        <p v-if="subtitle" class="mt-0.5 text-xs text-[var(--ink3)]">{{ subtitle }}</p>
      </div>
      <slot name="action" />
    </div>
    <div :class="padded ? 'p-4' : ''">
      <slot />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { moduleStyle } from '@/components/admin/adminModules.js'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  padded: { type: Boolean, default: true },
  accent: { type: Boolean, default: false },
  module: { type: String, default: 'dashboard' },
})

const accentStyle = computed(() => moduleStyle(props.module))
</script>
