<!--
  QuizImage.vue
  ─────────────
  Displays a question-set image from either:
    - A UUID string  → served from backend /data-assets/images/{uuid}.png
    - A full https:// URL → used directly (e.g. cms.youpass.vn CDN)
-->
<template>
  <div
    v-if="resolvedSrc"
    class="mb-4 overflow-hidden rounded-xl border border-[var(--border2)] bg-[var(--bg2)]"
  >
    <img
      :src="resolvedSrc"
      :alt="alt"
      loading="lazy"
      class="h-auto max-h-80 w-full object-contain"
      @error="onError"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  /** UUID string (e.g. "3faa0b15-...") or a full https:// URL */
  uuid: { type: String, default: '' },
  alt:  { type: String, default: 'Question diagram / map' },
})

const failed = ref(false)

const resolvedSrc = computed(() => {
  if (!props.uuid || failed.value) return null
  if (props.uuid.startsWith('http')) return props.uuid
  const base = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
  return `${base}/data-assets/images/${props.uuid}.png`
})

function onError() {
  failed.value = true
}
</script>
