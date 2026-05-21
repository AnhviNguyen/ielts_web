<template>
  <div
    class="relative w-full overflow-hidden rounded-xl bg-black"
    :class="visible ? 'aspect-video' : 'h-0 overflow-hidden opacity-0 pointer-events-none'"
  >
    <div ref="hostEl" class="h-full w-full" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  videoId: { type: String, required: true },
  visible: { type: Boolean, default: true },
})

const emit = defineEmits(['ready'])

const hostEl = ref(null)

let playerApi = null

onMounted(() => {
  emit('ready', hostEl.value)
})

watch(() => props.videoId, () => {
  /* parent remounts player via session */
})

onUnmounted(() => {
  playerApi = null
})

defineExpose({ hostEl })
</script>
