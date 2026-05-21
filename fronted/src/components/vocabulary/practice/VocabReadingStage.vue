<template>
  <section class="flex w-full flex-1 flex-col gap-3 py-2">
    <div v-if="loading" class="flex flex-1 items-center justify-center text-slate-500">
      AI đang tạo đoạn văn...
    </div>
    <div v-else-if="error" class="flex flex-1 flex-col items-center justify-center gap-3 text-slate-500">
      {{ error }}
      <button type="button" class="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-extrabold text-white" @click="$emit('retry')">
        Thử lại
      </button>
    </div>
    <template v-else-if="passage">
      <p class="text-[11px] text-slate-400">
        {{ passage.source === 'ai' ? 'Đoạn văn AI' : 'Đoạn văn mẫu' }} · {{ batchSize }} từ
      </p>
      <article
        v-for="(para, pi) in passage.paragraphs"
        :key="pi"
        class="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-6 shadow-sm sm:px-8"
      >
        <p class="m-0 text-[15px] leading-[2] text-slate-700 underline decoration-slate-200 underline-offset-4 sm:text-[17px]">
          <template v-for="(part, idx) in para.parts" :key="idx">
            <span v-if="part.type === 'text'">{{ part.content }}</span>
            <span v-else-if="part.type === 'gap'" class="mx-1 inline-flex flex-col align-middle">
              <input
                :value="gapAnswers[part.id]"
                class="min-w-[100px] rounded-lg border bg-white px-2.5 py-1.5 text-sm text-slate-900 outline-none focus:border-emerald-500"
                :class="gapInputClass(part.id)"
                placeholder="nhập từ"
                :disabled="checked"
                @input="$emit('gap-input', { id: part.id, value: $event.target.value })"
              />
              <span v-if="part.hint_vi" class="mt-0.5 text-[11px] text-slate-400 no-underline">{{ part.hint_vi }}</span>
            </span>
          </template>
        </p>
      </article>
      <div class="flex flex-col items-center gap-3 pt-2">
        <button
          v-if="!checked"
          type="button"
          class="w-full max-w-md rounded-xl bg-emerald-600 py-3.5 text-sm font-extrabold text-white"
          @click="$emit('check')"
        >
          Kiểm tra đáp án
        </button>
        <template v-else>
          <p class="text-sm font-bold" :class="allCorrect ? 'text-emerald-600' : 'text-rose-600'">
            {{ allCorrect ? '✓ Tất cả đúng!' : '✗ Một số từ chưa đúng' }}
          </p>
          <button
            type="button"
            class="w-full max-w-md rounded-xl bg-emerald-600 py-3.5 text-sm font-extrabold text-white disabled:opacity-50"
            :disabled="reviewing"
            @click="$emit('next')"
          >
            Tiếp theo
          </button>
        </template>
      </div>
    </template>
  </section>
</template>

<script setup>
const props = defineProps({
  loading: Boolean,
  error: { type: String, default: '' },
  passage: { type: Object, default: null },
  batchSize: { type: Number, default: 0 },
  gapAnswers: { type: Object, default: () => ({}) },
  gapStatus: { type: Object, default: () => ({}) },
  checked: Boolean,
  allCorrect: Boolean,
  reviewing: Boolean,
})

defineEmits(['retry', 'check', 'next', 'gap-input'])

function gapInputClass(id) {
  const s = props.gapStatus[id]
  if (s === 'ok') return 'border-emerald-500 bg-emerald-50'
  if (s === 'bad') return 'border-rose-400 bg-rose-50'
  return 'border-slate-200'
}
</script>
