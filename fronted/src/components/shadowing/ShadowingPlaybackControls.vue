<template>
  <div class="flex flex-wrap items-center gap-2" :class="compact ? 'justify-center' : ''">
    <button type="button" class="sh-btn" :class="compact ? 'px-2 py-2' : ''" title="Câu trước" @click="$emit('prev')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="19 20 9 12 19 4"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
      <span v-if="!compact">Câu trước</span>
    </button>
    <button type="button" class="sh-btn" :class="compact ? 'px-2 py-2' : ''" title="Phát lại" @click="$emit('replay')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
      <span v-if="!compact">Phát lại</span>
    </button>
    <button type="button" class="sh-btn sh-btn-primary" :class="compact ? 'px-3 py-2' : ''" title="Play/Pause" @click="$emit('toggle-play')">
      <svg v-if="playing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      <span v-if="!compact">{{ playing ? 'Tạm dừng' : 'Phát' }}</span>
    </button>
    <button type="button" class="sh-btn" :class="compact ? 'px-2 py-2' : ''" title="Câu tiếp" @click="$emit('next')">
      <span v-if="!compact">Câu tiếp</span>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 4 15 12 5 20"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
    </button>
    <div v-if="showSpeed" class="flex items-center gap-1 border-l border-gray-200 pl-2">
      <button
        v-for="r in rates"
        :key="r"
        type="button"
        class="rounded-lg border px-2 py-1 text-[11px] font-bold"
        :class="rate === r ? 'border-[#059669] bg-[var(--green-l)] text-black' : 'border-gray-200 bg-white text-gray-600'"
        @click="$emit('update:rate', r)"
      >
        {{ r }}x
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  playing: { type: Boolean, default: false },
  rate: { type: Number, default: 1 },
  compact: { type: Boolean, default: false },
  showSpeed: { type: Boolean, default: true },
})
defineEmits(['prev', 'replay', 'next', 'toggle-play', 'update:rate'])
const rates = [0.5, 0.75, 1]
</script>
