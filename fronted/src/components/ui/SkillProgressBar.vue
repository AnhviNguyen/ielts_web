<template>
  <div class="progress-bar">
    <div class="progress-header">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-value">{{ value }}%</span>
    </div>
    <div class="progress-track">
      <div
        class="progress-fill"
        :style="{ width: value + '%', background: color }"
      ></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: Number, required: true }, // 0–100
  color: { type: String, default: 'var(--green-l)' },
})
</script>

<style scoped>
.progress-bar { width: 100%; }

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--ink3);
  margin-bottom: 4px;
}

.progress-label { font-weight: 500; }
.progress-value { font-weight: 700; color: var(--ink2); }

.progress-track {
  height: 8px;
  background: var(--bg2);
  border-radius: 99px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.6s ease;
}
</style>
