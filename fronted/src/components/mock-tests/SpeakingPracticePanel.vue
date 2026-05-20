<template>
  <div class="speaking-practice mx-auto w-full" :class="chatOpen ? 'max-w-6xl' : 'max-w-3xl'">
    <!-- Top bar: exit, progress, help -->
    <div class="mb-5 flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="ct-btn flex shrink-0 items-center gap-1.5 px-3 py-1.5 text-[12px]"
        @click="$emit('exit')"
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        Thoát
      </button>

      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2 sm:gap-3">
        <div class="flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-white px-4 py-1.5 text-[12px]">
          <span class="font-bold text-[var(--ink)]">Question {{ currentIndex + 1 }}</span>
          <span class="text-[var(--ink3)]">/ {{ total }}</span>
        </div>
        <div class="hidden gap-1 sm:flex">
          <div
            v-for="(_, i) in total"
            :key="i"
            class="h-2 w-2 rounded-full transition-colors"
            :class="dotClass(i)"
          />
        </div>
        <div class="h-1.5 flex-1 min-w-[80px] overflow-hidden rounded-full bg-[var(--border2)] sm:max-w-[200px]">
          <div
            class="h-full rounded-full bg-[#34d399] transition-all duration-300"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
      </div>

      <button
        type="button"
        class="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-colors"
        :class="chatOpen
          ? 'border-[#34d399] bg-[#34d39911] text-[#34d399]'
          : 'border-[var(--border2)] bg-white text-[var(--ink2)] hover:border-[#34d399] hover:text-[#34d399]'"
        @click="$emit('toggle-chat')"
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/>
        </svg>
        Need help?
      </button>
    </div>

    <!-- Main + optional chat -->
    <div
      class="flex overflow-hidden rounded-2xl border border-[var(--border)] bg-white shadow-sm"
      :class="chatOpen ? 'flex-col lg:flex-row' : 'flex-col'"
    >
      <div class="flex min-w-0 flex-1 flex-col" :class="chatOpen ? 'lg:border-r lg:border-[var(--border)]' : ''">
        <!-- Question body -->
        <div class="p-6 sm:p-8">
          <div
            v-if="partTitle"
            class="mb-4 text-[11px] font-bold uppercase tracking-wider text-[var(--ink3)]"
          >
            {{ partTitle }}
          </div>
          <slot />
        </div>

        <!-- Footer navigation -->
        <div class="flex items-center justify-between gap-3 border-t border-[var(--border)] bg-[var(--bg)] px-6 py-4 sm:px-8">
          <button
            type="button"
            class="ct-btn flex items-center gap-1.5 px-4 py-2 text-[13px]"
            :class="!canPrev ? 'pointer-events-none opacity-30' : ''"
            :disabled="!canPrev"
            @click="$emit('prev')"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Previous
          </button>
          <span class="text-[11px] text-[var(--ink3)]">{{ currentIndex + 1 }} / {{ total }}</span>
          <button
            type="button"
            class="ct-btn flex items-center gap-1.5 px-4 py-2 text-[13px]"
            :class="!canNext ? 'pointer-events-none opacity-30' : ''"
            :disabled="!canNext"
            @click="$emit('next')"
          >
            Next
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </div>

      <slot name="chat" />
    </div>

    <!-- Feedback / results below card -->
    <div v-if="$slots.feedback" class="mt-6">
      <slot name="feedback" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentIndex: { type: Number, default: 0 },
  total:        { type: Number, default: 1 },
  partTitle:    { type: String, default: '' },
  chatOpen:     { type: Boolean, default: false },
  canPrev:      { type: Boolean, default: false },
  canNext:      { type: Boolean, default: false },
})

defineEmits(['exit', 'prev', 'next', 'toggle-chat'])

const progressPercent = computed(() => {
  if (!props.total) return 0
  return Math.round(((props.currentIndex + 1) / props.total) * 100)
})

function dotClass(i) {
  if (i < props.currentIndex) return 'bg-[#34d399]'
  if (i === props.currentIndex) return 'bg-[#111]'
  return 'bg-[var(--border2)]'
}
</script>
