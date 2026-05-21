<template>
  <section class="flex w-full flex-1 flex-col items-center justify-center gap-4 py-2">
    <div class="relative w-full max-w-2xl rounded-3xl border border-slate-200 bg-white px-6 py-10 text-center shadow-lg sm:px-10">
      <VocabSpeakerButton :large="variant === 'dictation'" @play="$emit('speak')" />
      <p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">{{ caption }}</p>
      <p v-if="variant === 'typing'" class="mb-6 text-xl font-extrabold text-emerald-700 sm:text-2xl">
        {{ word.meaning_vi || '—' }}
      </p>
      <p v-else-if="clozePreview" class="mb-6 text-left text-base leading-relaxed text-slate-600">
        {{ clozePreview }}
      </p>

      <div class="mx-auto flex w-full max-w-md flex-wrap justify-center gap-2">
        <input
          ref="inputEl"
          :value="modelValue"
          class="min-w-[140px] flex-1 rounded-xl border-[1.5px] bg-white px-3.5 py-3 text-[15px] text-slate-900 outline-none focus:border-emerald-500"
          :class="inputStateClass"
          placeholder="nhập từ..."
          :disabled="!!result"
          @input="$emit('update:modelValue', $event.target.value)"
          @keydown.enter="$emit('check')"
        />
        <button
          v-if="!result"
          type="button"
          class="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-extrabold text-white disabled:opacity-40"
          :disabled="!modelValue?.trim()"
          @click="$emit('check')"
        >
          Kiểm tra
        </button>
      </div>

      <p v-if="result" class="mt-4 text-sm font-bold" :class="result === 'correct' ? 'text-emerald-600' : 'text-rose-600'">
        {{ result === 'correct' ? '✓ Chính xác!' : `✗ Đáp án: ${word.word}` }}
      </p>
      <button
        v-if="result"
        type="button"
        class="mt-4 w-full max-w-xs rounded-xl bg-emerald-600 py-3 text-sm font-extrabold text-white disabled:opacity-50"
        :disabled="reviewing"
        @click="$emit('next')"
      >
        Tiếp theo
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import VocabSpeakerButton from './VocabSpeakerButton.vue'

const props = defineProps({
  word: { type: Object, required: true },
  variant: { type: String, default: 'typing' },
  caption: { type: String, required: true },
  clozePreview: { type: String, default: '' },
  modelValue: { type: String, default: '' },
  result: { type: String, default: null },
  reviewing: Boolean,
})

defineEmits(['update:modelValue', 'speak', 'check', 'next'])

const inputEl = ref(null)
defineExpose({
  focus: () => inputEl.value?.focus(),
})

const inputStateClass = computed(() => {
  if (props.result === 'correct') return 'border-emerald-500 bg-emerald-50'
  if (props.result === 'wrong') return 'border-rose-400 bg-rose-50'
  return 'border-slate-200'
})
</script>
