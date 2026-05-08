<template>
  <div class="card p-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-sm font-semibold">{{ title }}</div>
        <div class="text-xs text-[var(--ink2)]">{{ subtitle }}</div>
      </div>
      <div class="text-xs font-mono text-[var(--ink2)]">
        {{ audio.fmt(audio.currentTime.value) }} / {{ audio.fmt(audio.duration.value) }}
      </div>
    </div>

    <!-- hidden native element – bound to composable via onMounted -->
    <audio ref="nativeAudio" :src="src" preload="metadata" class="hidden" />

    <div class="mt-3 flex items-center gap-2">
      <button class="btn btn-secondary" @click="audio.seekDelta(-5)">-5s</button>
      <button class="btn btn-primary"   @click="audio.toggle()">
        {{ audio.playing.value ? 'Pause' : 'Play' }}
      </button>
      <button class="btn btn-secondary" @click="audio.seekDelta(5)">+5s</button>

      <div class="ml-auto flex items-center gap-2">
        <div class="text-xs text-[var(--ink2)]">Speed</div>
        <select
          class="rounded-lg border border-[var(--border2)] bg-[var(--surface)] px-2 py-1 text-xs"
          v-model.number="audio.playbackRate.value"
        >
          <option :value="0.75">0.75x</option>
          <option :value="1">1.0x</option>
          <option :value="1.25">1.25x</option>
          <option :value="1.5">1.5x</option>
        </select>
      </div>
    </div>

    <input
      class="mt-3 w-full"
      type="range"
      min="0"
      :max="Math.max(0, audio.duration.value)"
      step="0.01"
      :value="audio.currentTime.value"
      @input="e => audio.seekTo(Number(e.target.value))"
    />

    <div v-if="!src" class="mt-3 text-xs text-[var(--ink2)]">
      Chưa cấu hình audio CDN. Hãy set <code>VITE_AUDIO_CDN_BASE</code> trong <code>fronted/.env</code>.
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAudioControl } from '@/composables/useAudioControl.js'

const props = defineProps({
  src:      { type: String,  default: '' },
  title:    { type: String,  default: 'Audio' },
  subtitle: { type: String,  default: '' },
  /** Legacy seek-only (no autoplay). Use seekAndPlay() for full control. */
  seekTo:   { type: Number,  default: null },
})

const emit = defineEmits(['time'])

const audio      = useAudioControl()
const nativeAudio = ref(null)

onMounted(() => audio.attach(nativeAudio.value))

// Forward time events to parent
watch(audio.currentTime, (t) => emit('time', t))

// Legacy seekTo prop support (seek without playing)
watch(() => props.seekTo, (v) => {
  if (v !== null && v !== undefined) audio.seekTo(v)
})

/** Seek to `sec` seconds and immediately start playback. */
function seekAndPlay(sec) { audio.seekAndPlay(sec) }

defineExpose({ seekAndPlay })
</script>
