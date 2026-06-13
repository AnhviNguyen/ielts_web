<template>
  <button
    type="button"
    class="page-back-link group mb-4 inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--ink3)] transition-colors hover:text-[var(--ink)]"
    @click="goBack"
  >
    <svg
      class="transition-transform group-hover:-translate-x-0.5"
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
    {{ label }}
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  label: { type: String, default: 'Quay lại' },
  fallback: { type: String, default: '/dashboard' },
})

const router = useRouter()

function goBack() {
  if (window.history.state?.back) {
    router.back()
  } else {
    router.push(props.fallback)
  }
}
</script>
