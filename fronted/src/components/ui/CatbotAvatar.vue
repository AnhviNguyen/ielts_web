<template>
  <img
    src="/icon_profile.jpg"
    alt="Catbot"
    class="rounded-full object-cover ring-1 ring-[var(--spotify-green)]"
    :class="sizeClass"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: String, default: 'md' },
})

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'h-7 w-7'
  if (props.size === 'lg') return 'h-10 w-10 shadow-sm ring-2'
  return 'h-8 w-8'
})
</script>
