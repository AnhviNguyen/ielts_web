<template>
  <div class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-4">
    <div class="mb-3 flex items-center gap-2 text-[var(--ink2)]">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
      <span class="text-[11px] font-semibold uppercase tracking-wider">Your Recording</span>
    </div>

    <audio ref="audioEl" :src="src" preload="metadata" class="hidden"
      @timeupdate="onTimeUpdate" @loadedmetadata="onMeta" @ended="playing = false"/>

    <!-- Progress bar -->
    <div class="relative mb-3 h-1.5 cursor-pointer overflow-hidden rounded-full bg-[var(--border)]"
      @click="seek" ref="barEl">
      <div class="absolute inset-y-0 left-0 rounded-full bg-[#34d399] transition-[width]"
        :style="{ width: progressPct + '%' }"/>
    </div>

    <div class="flex items-center gap-3">
      <!-- Play/Pause -->
      <button
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-[#34d399] text-[#34d399] transition hover:bg-[#34d399] hover:text-white"
        @click="toggle"
      >
        <svg v-if="!playing" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      </button>

      <span class="text-xs tabular-nums text-[var(--ink3)]">{{ fmt(currentTime) }} / {{ fmt(duration) }}</span>

      <!-- Speed -->
      <div class="ml-auto flex items-center gap-1">
        <button
          v-for="spd in [0.75, 1, 1.5]"
          :key="spd"
          class="rounded px-1.5 py-0.5 text-[10px] font-bold transition"
          :class="playbackRate === spd
            ? 'bg-[#34d399] text-white'
            : 'text-[var(--ink3)] hover:text-[var(--ink2)]'"
          @click="setRate(spd)"
        >{{ spd }}×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  audioUrl:  { type: String, default: '' },
  audioBlob: { type: Object, default: null },
})

const src = computed(() => {
  if (props.audioBlob) return URL.createObjectURL(props.audioBlob)
  return props.audioUrl
})

const audioEl     = ref(null)
const barEl       = ref(null)
const playing     = ref(false)
const currentTime = ref(0)
const duration    = ref(0)
const playbackRate = ref(1)
const progressPct = computed(() => duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0)

function onTimeUpdate() { currentTime.value = audioEl.value?.currentTime ?? 0 }
function onMeta()       { duration.value    = audioEl.value?.duration    ?? 0 }

function toggle() {
  if (!audioEl.value) return
  if (playing.value) { audioEl.value.pause(); playing.value = false }
  else               { audioEl.value.play();  playing.value = true  }
}

function seek(e) {
  if (!barEl.value || !audioEl.value) return
  const { left, width } = barEl.value.getBoundingClientRect()
  audioEl.value.currentTime = Math.max(0, Math.min(1, (e.clientX - left) / width)) * duration.value
}

function setRate(r) {
  playbackRate.value = r
  if (audioEl.value) audioEl.value.playbackRate = r
}

function fmt(sec) {
  if (!isFinite(sec)) return '0:00'
  return `${Math.floor(sec / 60)}:${Math.floor(sec % 60).toString().padStart(2, '0')}`
}

watch(playbackRate, (v) => { if (audioEl.value) audioEl.value.playbackRate = v })
</script>
