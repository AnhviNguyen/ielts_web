<template>
  <!-- 3D flip flashcard -->
  <div class="flashcard-container" style="height: 240px;" @click="emit('flip')">
    <div class="flashcard-inner" :class="{ flipped: isFlipped }">
      <!-- Front: word -->
      <div class="card-face card-front">
        <div class="card-word font-display">{{ word }}</div>
        <div class="card-ipa font-mono">{{ ipa }}</div>
        <button class="card-audio-btn" @click.stop="$emit('audio')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        </button>
        <div class="card-hint">Bấm để xem nghĩa</div>
      </div>

      <!-- Back: meaning & example -->
      <div class="card-face card-back-face card-back">
        <div class="card-type-badge">{{ type }}</div>
        <div class="card-meaning">{{ meaning }}</div>
        <div class="card-example">{{ example }}</div>
        <div v-if="exampleVi" class="card-example-vi">{{ exampleVi }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  word:      { type: String, required: true },
  ipa:       { type: String, default: '' },
  type:      { type: String, default: 'noun' },
  meaning:   { type: String, required: true },
  example:   { type: String, default: '' },
  exampleVi: { type: String, default: '' },
  isFlipped: { type: Boolean, default: false },
})

const emit = defineEmits(['flip', 'audio'])
</script>

<style scoped>
.card-front {
  background: var(--ink);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
}

.card-word {
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.card-ipa {
  font-size: 14px;
  color: var(--green-l);
  margin-bottom: 12px;
}

.card-audio-btn {
  width: 40px; height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.12);
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.card-audio-btn:hover { background: rgba(255,255,255,0.25); }

.card-hint {
  position: absolute;
  bottom: 12px;
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.05em;
}

.card-back {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-type-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  background: var(--violet-bg);
  color: var(--violet);
  margin-bottom: 10px;
  align-self: flex-start;
}

.card-meaning {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 10px;
  line-height: 1.4;
}

.card-example {
  font-size: 13px;
  color: var(--ink3);
  line-height: 1.6;
  font-style: italic;
  border-left: 3px solid var(--green-l);
  padding-left: 10px;
}

.card-example-vi {
  font-size: 12px;
  color: var(--ink3);
  margin-top: 6px;
  padding-left: 13px;
}
</style>
