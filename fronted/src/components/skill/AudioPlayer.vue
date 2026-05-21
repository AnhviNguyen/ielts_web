<template>
  <div class="mb-5 rounded-[var(--r)] bg-[var(--ink)] px-6 py-5 text-white">
    <div class="font-display mb-1 flex items-center gap-2 text-base font-semibold">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
      {{ title }}
    </div>
    <div class="mb-4 text-xs text-white/45">{{ subtitle }}</div>

    <div class="mb-3.5 flex h-12 items-center gap-0.5">
      <div
        v-for="(h, i) in waveHeights"
        :key="i"
        class="waveform-bar"
        :class="{
          played:  i < playedBars,
          current: i === playedBars,
          playing: isPlaying && i === playedBars,
        }"
        :style="{ height: h + 'px' }"
      />
    </div>

    <div class="flex items-center gap-3.5">
      <button type="button" class="ctrl-btn" @click="seek(-10)" title="-10s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
      </button>
      <button type="button" class="ctrl-btn" @click="seek(-5)" title="-5s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 19 2 12 11 5 11 19"/><polygon points="22 19 13 12 22 5 22 19"/></svg>
      </button>
      <button type="button" class="ctrl-btn play" @click="togglePlay" :title="isPlaying ? 'Dừng' : 'Phát'">
        <svg v-if="!isPlaying" width="18" height="18" viewBox="0 0 24 24" fill="white"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="white"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      </button>
      <button type="button" class="ctrl-btn" @click="seek(5)" title="+5s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 19 22 12 13 5 13 19"/><polygon points="2 19 11 12 2 5 2 19"/></svg>
      </button>
      <button type="button" class="ctrl-btn" @click="seek(10)" title="+10s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
      </button>

      <span class="whitespace-nowrap font-mono text-[13px] text-white/55">{{ formatTime(elapsed) }} / {{ formatTime(duration) }}</span>

      <div class="ml-auto flex gap-1">
        <button
          v-for="s in speeds"
          :key="s"
          type="button"
          class="cursor-pointer rounded-[5px] border-0 bg-white/10 px-2 py-1 font-mono text-[11px] font-semibold text-white/50 transition-all"
          :class="{ 'bg-white/25 text-white': speed === s }"
          @click="speed = s"
        >{{ s }}x</button>
      </div>
    </div>

    <div v-if="parts.length" class="mt-3 flex flex-wrap gap-1.5">
      <button
        v-for="part in parts"
        :key="part.label"
        type="button"
        class="cursor-pointer rounded-[5px] border-0 px-2.5 py-1 text-[11px] font-semibold transition-all"
        :class="activePart === part.label ? 'bg-[var(--green-l)] text-white' : 'bg-white/[0.08] text-white/55'"
        @click="jumpTo(part)"
      >{{ part.label }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'

const props = defineProps({
  title:    { type: String, default: 'IELTS Listening Test' },
  subtitle: { type: String, default: '' },
  duration: { type: Number, default: 468 },
  parts:    { type: Array, default: () => [
    { label: 'Part 1 · 0:00', time: 0 },
    { label: 'Part 2 · 2:10', time: 130 },
    { label: 'Part 3 · 4:55', time: 295 },
    { label: 'Part 4 · 7:48', time: 468 },
  ]},
})

const isPlaying  = ref(false)
const elapsed    = ref(0)
const speed      = ref(1)
const activePart = ref(props.parts[0]?.label ?? '')
const speeds     = [0.75, 1, 1.25, 1.5]

const waveHeights = Array.from({ length: 60 }, () => 8 + Math.floor(Math.random() * 32))
const playedBars  = computed(() => Math.floor((elapsed.value / props.duration) * waveHeights.length))

let _timer = null

function togglePlay() {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    _timer = setInterval(() => {
      if (elapsed.value < props.duration) elapsed.value++
      else { isPlaying.value = false; clearInterval(_timer) }
    }, 1000 / speed.value)
  } else {
    clearInterval(_timer)
  }
}

function seek(delta) {
  elapsed.value = Math.max(0, Math.min(props.duration, elapsed.value + delta))
}

function jumpTo(part) {
  elapsed.value = part.time
  activePart.value = part.label
}

function formatTime(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0')
  const s = (sec % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

onUnmounted(() => clearInterval(_timer))
</script>
