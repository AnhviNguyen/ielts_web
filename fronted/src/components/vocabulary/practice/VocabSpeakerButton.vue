<template>
  <button
    type="button"
    :class="[
      'z-10 flex items-center justify-center rounded-full border-[1.5px] border-emerald-500',
      'bg-white text-emerald-600 transition-colors hover:bg-emerald-600 hover:text-white',
      large ? 'relative mx-auto mb-4 h-14 w-14' : 'absolute right-3.5 top-3.5 h-11 w-11',
    ]"
    :title="title"
    @click.stop="$emit('play')"
  >
    <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
    </svg>
  </button>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'Phát âm' },
  large: { type: Boolean, default: false },
})
defineEmits(['play'])
</script>
