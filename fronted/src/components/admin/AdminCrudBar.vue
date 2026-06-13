<template>
  <div
    class="admin-crud-bar flex flex-wrap items-center gap-2 rounded-xl border px-3 py-2 shadow-sm"
    :style="accentStyle"
  >
    <span class="admin-crud-tag rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">CRUD</span>
    <button type="button" class="ct-btn btn-sm" @click="$emit('create')">
      <span class="inline-flex items-center gap-1.5" v-html="iconPlus" /> Tạo mới
    </button>
    <button
      v-if="showSave"
      type="button"
      class="ct-btn btn-sm admin-save-btn shadow-sm"
      :disabled="!canSave || saving"
      @click="$emit('save')"
    >
      {{ saving ? 'Đang lưu...' : 'Lưu' }}
    </button>
    <button v-if="canArchive" type="button" class="ct-btn btn-sm" :disabled="saving" @click="$emit('archive')">
      {{ isArchived ? 'Hiện đề' : archiveLabel }}
    </button>
    <button type="button" class="ct-btn btn-sm" :disabled="saving" @click="$emit('refresh')">
      Tải lại
    </button>
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { moduleStyle } from '@/components/admin/adminModules.js'

const props = defineProps({
  canSave: { type: Boolean, default: true },
  canArchive: { type: Boolean, default: false },
  archiveLabel: { type: String, default: 'Lưu trữ' },
  saving: { type: Boolean, default: false },
  showSave: { type: Boolean, default: true },
  module: { type: String, default: 'dashboard' },
  isArchived: { type: Boolean, default: false },
})

defineEmits(['create', 'save', 'archive', 'refresh'])

const accentStyle = computed(() => moduleStyle(props.module))

const iconPlus = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`
</script>
