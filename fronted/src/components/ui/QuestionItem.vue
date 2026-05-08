<template>
  <!-- LSP: type prop cho phép swap fill/mcq mà không cần sửa parent -->
  <div class="q-item">
    <div class="q-num">Question {{ number }}</div>
    <div class="q-text">{{ question }}</div>

    <!-- Fill-in-the-blank -->
    <input
      v-if="type === 'fill'"
      class="q-input"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <!-- Multiple choice -->
    <div v-else-if="type === 'mcq'" class="q-options">
      <div
        v-for="(opt, idx) in options"
        :key="idx"
        class="q-option"
        :class="{ selected: modelValue === idx }"
        @click="$emit('update:modelValue', idx)"
      >
        <div class="q-option-letter">{{ letters[idx] }}</div>
        {{ opt }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type:        { type: String, default: 'fill' }, // 'fill' | 'mcq'
  number:      { type: Number, required: true },
  question:    { type: String, required: true },
  options:     { type: Array, default: () => [] },
  modelValue:  { default: null },
  placeholder: { type: String, default: 'Điền câu trả lời...' },
})

defineEmits(['update:modelValue'])

const letters = ['A', 'B', 'C', 'D', 'E']
</script>

<style scoped>
.q-item { margin-bottom: 18px; }

.q-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--ink3);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}

.q-text {
  font-size: 13.5px;
  font-weight: 500;
  margin-bottom: 10px;
  color: var(--ink);
  line-height: 1.6;
}

.q-input {
  width: 100%;
  padding: 8px 12px;
  border-radius: var(--r-sm);
  border: 1.5px solid var(--border2);
  background: var(--bg);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.18s;
  color: var(--ink);
}

.q-input:focus { border-color: var(--blue-l); }

.q-options { display: flex; flex-direction: column; gap: 7px; }

.q-option {
  padding: 9px 13px;
  border-radius: var(--r-sm);
  border: 1.5px solid var(--border);
  background: var(--bg);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--ink2);
}

.q-option:hover { border-color: var(--blue-l); background: var(--blue-bg); }

.q-option.selected { border-color: var(--blue-l); background: var(--blue-bg); }

.q-option-letter {
  width: 22px; height: 22px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

.q-option.selected .q-option-letter {
  background: var(--blue-l);
  color: white;
}
</style>
