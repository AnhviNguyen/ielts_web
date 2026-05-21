<template>
  <div class="flex flex-col gap-1" :class="wrapperClass">
    <label v-if="label" :for="selectId" class="text-[11px] font-bold uppercase tracking-wider text-slate-400">
      {{ label }}
    </label>
    <select
      :id="selectId"
      :value="modelValue"
      :disabled="disabled"
      class="ct-select"
      @change="onChange"
    >
      <option v-if="placeholder" disabled value="">{{ placeholder }}</option>
      <option
        v-for="opt in options"
        :key="String(opt.value)"
        :value="opt.value"
      >{{ opt.label }}</option>
    </select>
    <p v-if="hint" class="text-[11px] text-slate-400">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  wrapperClass: { type: String, default: '' },
  id: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const selectId = computed(() => props.id || `app-select-${Math.random().toString(36).slice(2, 9)}`)

function onChange(e) {
  const raw = e.target.value
  const first = props.options[0]?.value
  const coerced = typeof first === 'number' ? Number(raw) : raw
  emit('update:modelValue', Number.isNaN(coerced) ? raw : coerced)
}
</script>
