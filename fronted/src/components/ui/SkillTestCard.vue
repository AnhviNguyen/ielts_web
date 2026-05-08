<template>
  <div class="ct-card flex flex-col overflow-hidden rounded-xl border border-[var(--border)] bg-white">

    <!-- ─── Header row: icon + title + badge ─── -->
    <div class="flex items-start gap-3 p-4 pb-3">
      <!-- Icon: thumbnail (48×48) or colored fallback -->
      <div class="shrink-0">
        <div class="relative h-12 w-12 overflow-hidden rounded-lg bg-[#e8f5f0]">
          <img
            v-if="thumbnail && !imgErr"
            :src="`/api/images/${thumbnail}`"
            :alt="title"
            class="h-full w-full object-cover"
            loading="lazy"
            @error="imgErr = true"
          />
          <div
            v-else
            class="flex h-full w-full items-center justify-center text-[13px] font-bold text-[#34d399]"
          >
            {{ iconText }}
          </div>
        </div>
      </div>

      <!-- Title + badge -->
      <div class="min-w-0 flex-1">
        <div class="mb-1.5 text-[14px] font-semibold leading-snug text-[var(--ink)] line-clamp-2">
          {{ title }}
        </div>
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="inline-flex items-center rounded-full bg-[#fef9c3] px-2 py-0.5 text-[11px] font-semibold text-[#92400e]">
            Full Mock Test
          </span>
          <span v-if="bookCode" class="inline-flex items-center rounded-full bg-[var(--bg2)] px-2 py-0.5 text-[11px] font-medium text-[var(--ink3)]">
            {{ bookCode }}
          </span>
        </div>
      </div>
    </div>

    <!-- ─── Attempts + Start button ─── -->
    <div class="flex items-center justify-between gap-3 border-t border-[var(--border)] px-4 py-3">
      <div class="text-[12px] text-[var(--ink3)]">
        <template v-if="questionCount">
          {{ questionCount }} câu · {{ time }} phút
        </template>
        <template v-else>Chưa có lần làm</template>
      </div>

      <button
        class="flex items-center gap-1.5 rounded-lg border border-[var(--border2)] bg-white px-3 py-1.5 text-[12px] font-semibold text-[var(--ink)] transition-colors hover:bg-[var(--bg2)]"
        @click.stop="$emit('start-full')"
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Start
      </button>
    </div>

    <!-- ─── Practice by part ─── (only if parts exist) -->
    <div v-if="parts && parts.length" class="px-4 pb-4 pt-2">
      <p class="mb-2 text-[11px] font-medium text-[var(--ink3)]">Practice by part:</p>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="p in parts"
          :key="p.key"
          class="rounded-full border border-[var(--border2)] bg-white px-3 py-1 text-[11px] font-medium text-[var(--ink)] transition-colors hover:bg-[var(--bg2)]"
          @click.stop="$emit('start-part', p)"
        >
          {{ partLabel(p.key) }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  title:         String,
  thumbnail:     String,
  bookCode:      String,
  skillLabel:    { type: String, default: 'Test' },
  questionCount: Number,
  time:          Number,
  partCount:     Number,
  parts:         Array,
})
defineEmits(['click', 'start-full', 'start-part'])

const imgErr = ref(false)

const iconText = computed(() => {
  if (props.bookCode) return props.bookCode.slice(0, 2).toUpperCase()
  if (props.title)    return props.title.slice(0, 2).toUpperCase()
  return '?'
})

function partLabel(key) {
  if (!key) return '?'
  return key.replace('part_', 'Part ').replace('_', ' ')
}
</script>
