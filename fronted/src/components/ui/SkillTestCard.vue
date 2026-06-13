<template>
  <div class="ct-card flex flex-col overflow-hidden rounded-[var(--radius-comfortable)]">

    <!-- ─── Header row: icon + title + badge ─── -->
    <div class="flex items-start gap-3 p-4 pb-3">
      <!-- Icon: thumbnail (48×48) or colored fallback -->
      <div class="shrink-0">
        <div class="relative h-12 w-12 overflow-hidden rounded-[var(--radius-standard)] bg-[var(--green-bg)]">
          <img
            v-if="thumbnail && !imgErr"
            :src="thumbnailSrc"
            :alt="title"
            class="h-full w-full object-cover"
            loading="lazy"
            @error="imgErr = true"
          />
          <div
            v-else
            class="flex h-full w-full items-center justify-center text-[13px] font-bold text-[var(--spotify-green)]"
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
          <span class="ct-badge inline-flex items-center bg-[var(--amber-bg)] text-[var(--text-warning)]">
            Full Mock Test
          </span>
          <span
            v-if="attempted"
            class="inline-flex items-center gap-1 rounded-full bg-[var(--green-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--spotify-green-dark)]"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Đã làm
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
        class="btn btn-primary flex items-center gap-1.5 px-3 py-1.5 text-[12px]"
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
          class="ct-btn rounded-full px-3 py-1 text-[11px] font-medium"
          :class="completedPartKeys.includes(p.key) ? 'border-[var(--spotify-green)] bg-[var(--green-bg)] text-[var(--spotify-green-dark)]' : ''"
          @click.stop="$emit('start-part', p)"
        >
          <span v-if="completedPartKeys.includes(p.key)" class="mr-1">✓</span>{{ partLabel(p.key) }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { imageUrl } from '@/utils/mediaUrl.js'

const props = defineProps({
  title:         String,
  thumbnail:     String,
  bookCode:      String,
  skillLabel:    { type: String, default: 'Test' },
  questionCount: Number,
  time:          Number,
  partCount:     Number,
  parts:         Array,
  attempted:     { type: Boolean, default: false },
  completedPartKeys: { type: Array, default: () => [] },
})
defineEmits(['click', 'start-full', 'start-part'])

const imgErr = ref(false)
const thumbnailSrc = computed(() => imageUrl(props.thumbnail))

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
