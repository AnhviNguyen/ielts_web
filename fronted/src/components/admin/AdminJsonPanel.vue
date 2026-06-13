<template>
  <div
    class="admin-json-live overflow-hidden rounded-xl border bg-white shadow-sm transition-shadow"
    :class="{ 'is-syncing': syncing }"
    :style="accentStyle"
  >
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] px-4 py-2.5">
      <div class="flex items-center gap-2">
        <h2 class="text-sm font-bold text-[var(--ink)]">{{ title }}</h2>
        <span
          v-if="autoSync"
          class="admin-json-badge rounded-full px-2 py-0.5 text-[10px] font-bold"
          :class="{ pulse: syncing }"
        >
          {{ syncing ? 'Đang sinh JSON...' : live ? '● JSON tự động' : 'Chờ nhập' }}
        </span>
      </div>
      <span class="text-[10px] text-[var(--ink3)]">{{ hint }}</span>
    </div>
    <textarea
      :value="modelValue"
      class="ct-input min-h-[320px] w-full resize-y border-0 font-mono text-xs focus:ring-0"
      :class="minHeightClass"
      spellcheck="false"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { moduleStyle } from '@/components/admin/adminModules.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  title: { type: String, default: 'Raw JSON' },
  hint: { type: String, default: 'Tự cập nhật khi bạn sửa form bên trên' },
  autoSync: { type: Boolean, default: true },
  live: { type: Boolean, default: false },
  syncing: { type: Boolean, default: false },
  module: { type: String, default: 'dashboard' },
  tall: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const accentStyle = computed(() => moduleStyle(props.module))
const minHeightClass = computed(() => (props.tall ? 'min-h-[620px]' : 'min-h-[320px]'))
</script>
