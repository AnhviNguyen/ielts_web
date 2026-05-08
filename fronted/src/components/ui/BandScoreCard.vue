<template>
  <!-- ISP: nhận props tập trung, không pass props thừa -->
  <div class="score-card" :class="{ 'score-card--overall': overall }">
    <div class="score-label">{{ label }}</div>
    <div class="score-val" :style="{ color: overall ? 'var(--green-l)' : colorHex }">
      {{ score ?? '—' }}
    </div>
    <div class="score-target">Mục tiêu: {{ target }}</div>
    <!-- Progress bar for overall card -->
    <div v-if="overall" class="score-progress">
      <div
        class="score-progress-fill"
        :style="{ width: progressPct + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:    { type: String, required: true },
  score:    { type: Number, default: null },
  target:   { type: Number, required: true },
  colorHex: { type: String, default: 'var(--ink)' },
  overall:  { type: Boolean, default: false },
})

const progressPct = computed(() =>
  props.target > 0 ? Math.min(100, (props.score / props.target) * 100) : 0
)
</script>

<style scoped>
.score-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 18px;
  transition: box-shadow 0.18s, transform 0.18s;
  cursor: pointer;
}

.score-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.score-card--overall {
  background: var(--ink);
  border-color: transparent;
  color: white;
}

.score-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.55;
}

.score-card--overall .score-label {
  color: rgba(255,255,255,0.6);
  opacity: 1;
}

.score-val {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  margin: 6px 0 4px;
  color: var(--ink);
  line-height: 1;
}

.score-target {
  font-size: 12px;
  color: var(--ink3);
}

.score-card--overall .score-target {
  color: rgba(255,255,255,0.45);
}

.score-progress {
  height: 6px;
  background: rgba(255,255,255,0.15);
  border-radius: 99px;
  overflow: hidden;
  margin-top: 10px;
}

.score-progress-fill {
  height: 100%;
  border-radius: 99px;
  background: var(--green-l);
  transition: width 0.6s ease;
}
</style>
