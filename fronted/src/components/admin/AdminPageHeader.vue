<template>
  <section
    class="admin-hero relative overflow-hidden rounded-2xl border p-5 shadow-sm"
    :style="moduleStyle(moduleKey)"
  >
    <div class="admin-hero-glow pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full blur-2xl" />
    <div class="relative flex flex-wrap items-start justify-between gap-3">
      <div>
        <div
          class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide shadow-sm"
          :style="{ background: 'var(--admin-accent-soft)', color: 'var(--admin-accent)', border: '1px solid var(--admin-accent-border)' }"
        >
          <span class="h-1.5 w-1.5 rounded-full" :style="{ background: 'var(--admin-accent)' }" />
          {{ mod.label }}
        </div>
        <h1 class="mt-2 text-xl font-bold text-[var(--ink)]">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1 max-w-2xl text-sm text-[var(--ink3)]">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { ADMIN_MODULES, moduleStyle } from '@/components/admin/adminModules.js'

const props = defineProps({
  module: { type: String, default: 'dashboard' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})

const moduleKey = computed(() => props.module)
const mod = computed(() => ADMIN_MODULES[props.module] || ADMIN_MODULES.dashboard)
</script>
