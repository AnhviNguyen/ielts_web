<template>
  <div class="record-card">
    <!-- Header row -->
    <div class="record-header">
      <span class="chip-green-light">{{ partLabel }}</span>
      <span class="prep-timer font-mono" v-if="prepTime">Prep: {{ formatTime(prepTime) }}</span>
    </div>

    <!-- Question -->
    <div class="record-question">
      {{ question }}
      <span v-if="hint" class="record-hint">{{ hint }}</span>
    </div>

    <!-- Record button -->
    <div class="record-btn-wrap">
      <button
        class="record-btn"
        :class="{ 'record-btn-idle': !isRecording, 'record-btn-active': isRecording }"
        @click="toggle"
        :title="isRecording ? 'Dừng ghi âm' : 'Bắt đầu ghi âm'"
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
      </button>
    </div>

    <div class="record-status">
      {{ isRecording ? 'Đang ghi âm...' : 'Nhấn để bắt đầu ghi âm' }}
    </div>
    <div class="record-timer font-mono">{{ formatTime(elapsed) }}</div>
  </div>
</template>

<script setup>
import { useRecorder } from '@/composables/useRecorder.js'

defineProps({
  partLabel: { type: String, default: 'Part 2 · Cue Card' },
  question:  { type: String, default: 'Describe a skill you would like to learn in the future.' },
  hint:      { type: String, default: '' },
  prepTime:  { type: Number, default: 60 }, // seconds
})

const emit = defineEmits(['recorded'])

const { isRecording, elapsed, toggle, reset, formatTime } = useRecorder()
</script>

<style scoped>
.record-card {
  background: var(--ink);
  color: white;
  border-radius: var(--r);
  padding: 28px;
  text-align: center;
  margin-bottom: 20px;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chip-green-light {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(82,183,136,0.2);
  color: var(--green-l);
}

.prep-timer {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}

.record-question {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.7;
  margin-bottom: 24px;
  color: rgba(255,255,255,0.88);
}

.record-hint {
  display: block;
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  margin-top: 6px;
}

.record-btn-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.record-btn {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: var(--rose-l);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
}

.record-btn:hover { transform: scale(1.05); }

.record-status {
  font-size: 12px;
  color: rgba(255,255,255,0.45);
}

.record-timer {
  font-size: 20px;
  font-weight: 600;
  color: white;
  margin-top: 6px;
}
</style>
