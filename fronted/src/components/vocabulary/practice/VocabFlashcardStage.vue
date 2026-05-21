<template>
  <section class="flex w-full flex-1 flex-col items-center justify-center gap-4 py-2">
    <div
      class="flashcard-container relative w-full max-w-2xl min-h-[min(460px,52vh)] cursor-pointer rounded-3xl border border-slate-200 bg-white shadow-lg"
      @click="$emit('flip')"
    >
      <VocabSpeakerButton @play="$emit('speak')" />
      <div class="flashcard-inner h-full min-h-[inherit]" :class="{ flipped }">
        <div class="card-face flex flex-col items-center justify-center gap-2 bg-white p-8 text-center">
          <p class="text-4xl font-black tracking-tight text-slate-900 sm:text-5xl">{{ word.word }}</p>
          <p v-if="word.phonetic" class="text-sm italic text-emerald-600">
            {{ word.word_type }} · {{ word.phonetic }}
          </p>
          <p class="mt-4 text-[11px] text-slate-400">Space / Enter để lật thẻ</p>
        </div>
        <div class="card-face card-back-face flex flex-col items-center justify-center gap-2 bg-emerald-50 p-8 text-center">
          <p v-if="word.meaning_en" class="text-sm italic text-slate-500">{{ word.meaning_en }}</p>
          <p class="text-2xl font-extrabold text-emerald-700">{{ word.meaning_vi }}</p>
          <p v-if="word.example" class="text-sm italic text-slate-500">{{ word.example }}</p>
        </div>
      </div>
    </div>

    <div v-if="flipped" class="flex w-full max-w-2xl gap-3">
      <button
        type="button"
        class="flex-1 rounded-2xl border-2 border-rose-200 bg-rose-50 py-3.5 text-sm font-bold text-rose-600 disabled:opacity-50"
        :disabled="reviewing"
        @click="$emit('rate', false)"
      >
        Chưa nhớ
      </button>
      <button
        type="button"
        class="flex-1 rounded-2xl border-2 border-emerald-500 bg-emerald-50 py-3.5 text-sm font-bold text-emerald-700 disabled:opacity-50"
        :disabled="reviewing"
        @click="$emit('rate', true)"
      >
        Đã nhớ
      </button>
    </div>
  </section>
</template>

<script setup>
import VocabSpeakerButton from './VocabSpeakerButton.vue'

defineProps({
  word: { type: Object, required: true },
  flipped: Boolean,
  reviewing: Boolean,
})
defineEmits(['flip', 'speak', 'rate'])
</script>
