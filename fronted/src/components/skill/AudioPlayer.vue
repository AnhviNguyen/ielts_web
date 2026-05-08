<template>
  <div class="audio-player">
    <div class="audio-title font-display">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
      {{ title }}
    </div>
    <div class="audio-meta">{{ subtitle }}</div>

    <!-- Waveform visual -->
    <div class="waveform">
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
      ></div>
    </div>

    <!-- Controls -->
    <div class="audio-controls">
      <button class="ctrl-btn" @click="seek(-10)" title="-10s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
      </button>
      <button class="ctrl-btn" @click="seek(-5)" title="-5s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 19 2 12 11 5 11 19"/><polygon points="22 19 13 12 22 5 22 19"/></svg>
      </button>
      <button class="ctrl-btn play" @click="togglePlay" :title="isPlaying ? 'Dừng' : 'Phát'">
        <svg v-if="!isPlaying" width="18" height="18" viewBox="0 0 24 24" fill="white"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="white"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      </button>
      <button class="ctrl-btn" @click="seek(5)" title="+5s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 19 22 12 13 5 13 19"/><polygon points="2 19 11 12 2 5 2 19"/></svg>
      </button>
      <button class="ctrl-btn" @click="seek(10)" title="+10s">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
      </button>

      <span class="time-display font-mono">{{ formatTime(elapsed) }} / {{ formatTime(duration) }}</span>

      <!-- Speed -->
      <div class="speed-btns">
        <button
          v-for="s in speeds"
          :key="s"
          class="speed-btn"
          :class="{ active: speed === s }"
          @click="speed = s"
        >{{ s }}x</button>
      </div>
    </div>

    <!-- Part markers -->
    <div class="part-markers" v-if="parts.length">
      <button
        v-for="part in parts"
        :key="part.label"
        class="part-marker"
        :class="{ active: activePart === part.label }"
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
  duration: { type: Number, default: 468 }, // seconds
  parts:    { type: Array, default: () => [
    { label: 'Part 1 · 0:00', time: 0 },
    { label: 'Part 2 · 2:10', time: 130 },
    { label: 'Part 3 · 4:55', time: 295 },
    { label: 'Part 4 · 6:30', time: 390 },
  ]},
})

const isPlaying = ref(false)
const elapsed   = ref(134) // start mid-way for demo
const speed     = ref(1)
const activePart = ref('Part 2 · 2:10')
const speeds    = [0.75, 1, 1.25, 1.5]

let _timer = null

// Generate waveform heights (pseudo-random but stable)
const BARS = 80
const waveHeights = Array.from({ length: BARS }, (_, i) =>
  8 + Math.abs(Math.sin(i * 0.4) * 24 + Math.cos(i * 0.7) * 14)
)

const playedBars = computed(() =>
  Math.floor((elapsed.value / props.duration) * BARS)
)

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

<style scoped>
.audio-player {
  background: var(--ink);
  color: white;
  border-radius: var(--r);
  padding: 20px 24px;
  margin-bottom: 20px;
}

.audio-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.audio-meta {
  font-size: 12px;
  color: rgba(255,255,255,0.45);
  margin-bottom: 16px;
}

.waveform {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 48px;
  margin-bottom: 14px;
}

.audio-controls {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ctrl-btn {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.12);
  border: none;
  color: white;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  flex-shrink: 0;
}

.ctrl-btn:hover { background: rgba(255,255,255,0.22); }

.ctrl-btn.play {
  width: 44px; height: 44px;
  background: var(--green-l);
}

.ctrl-btn.play:hover { background: #3da771; }

.time-display {
  font-size: 13px;
  color: rgba(255,255,255,0.55);
  white-space: nowrap;
}

.speed-btns {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.speed-btn {
  padding: 4px 8px;
  border-radius: 5px;
  background: rgba(255,255,255,0.1);
  border: none;
  color: rgba(255,255,255,0.5);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-mono);
  transition: all 0.15s;
}

.speed-btn.active { background: rgba(255,255,255,0.25); color: white; }

.part-markers {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.part-marker {
  padding: 4px 10px;
  border-radius: 5px;
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.55);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  color: rgba(255,255,255,0.55);
}

.part-marker.active { background: var(--green-l); color: white; }
</style>
