<template>
  <div class="flashcard-container h-60 cursor-pointer" @click="emit('flip')">
    <div class="flashcard-inner" :class="{ flipped: isFlipped }">
      <div class="card-face card-front flex flex-col items-center justify-center bg-[var(--ink)] p-8 text-center">
        <div class="font-display mb-2 text-4xl font-bold text-white">{{ word }}</div>
        <div class="font-mono mb-3 text-sm text-[var(--green-l)]">{{ ipa }}</div>
        <button
          type="button"
          class="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border-0 bg-white/10 text-lg text-white transition-colors hover:bg-white/25"
          @click.stop="$emit('audio')"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        </button>
        <div class="absolute bottom-3 text-[11px] tracking-wider text-white/30">Bấm để xem nghĩa</div>
      </div>

      <div class="card-face card-back-face card-back relative flex flex-col justify-center border border-[var(--border)] bg-[var(--surface)] p-6">
        <div class="mb-2.5 inline-flex self-start rounded-full bg-[var(--violet-bg)] px-2.5 py-0.5 text-[11px] font-semibold text-[var(--violet)]">{{ type }}</div>
        <div class="mb-2.5 text-lg font-semibold leading-snug text-[var(--ink)]">{{ meaning }}</div>
        <div class="border-l-[3px] border-[var(--green-l)] pl-2.5 text-[13px] italic leading-relaxed text-[var(--ink3)]">{{ example }}</div>
        <div v-if="exampleVi" class="mt-1.5 pl-[13px] text-xs text-[var(--ink3)]">{{ exampleVi }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  word:      { type: String, required: true },
  ipa:       { type: String, default: '' },
  type:      { type: String, default: 'noun' },
  meaning:   { type: String, required: true },
  example:   { type: String, default: '' },
  exampleVi: { type: String, default: '' },
  isFlipped: { type: Boolean, default: false },
})

const emit = defineEmits(['flip', 'audio'])
</script>
