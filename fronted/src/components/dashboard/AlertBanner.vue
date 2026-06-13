<template>
  <div v-if="alerts.length" class="space-y-2">
    <div
      v-for="(alert, idx) in alerts"
      :key="`${alert.code}-${alert.skill}-${idx}`"
      class="flex items-start gap-2.5 rounded-xl border px-4 py-3 text-[13px]"
      :class="alertClass(alert.severity)"
    >
      <span class="mt-0.5 shrink-0" v-html="iconFor(alert.severity)" />
      <div>
        <div class="font-semibold capitalize">{{ skillLabel(alert.skill) }}</div>
        <p class="mt-0.5 leading-snug opacity-90">{{ alert.message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  alerts: { type: Array, default: () => [] },
})

function alertClass(severity) {
  if (severity === 'warning') {
    return 'border-amber-200 bg-amber-50 text-amber-900'
  }
  if (severity === 'critical') {
    return 'border-rose-200 bg-rose-50 text-rose-900'
  }
  return 'border-sky-200 bg-sky-50 text-sky-900'
}

function iconFor(severity) {
  if (severity === 'warning') {
    return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
  }
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`
}

function skillLabel(skill) {
  const map = {
    overall: 'Overall',
    reading: 'Reading',
    listening: 'Listening',
    writing: 'Writing',
    speaking: 'Speaking',
  }
  return map[skill] || skill
}
</script>
