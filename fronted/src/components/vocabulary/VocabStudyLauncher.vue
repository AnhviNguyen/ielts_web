<template>
  <section class="border-b border-slate-100 bg-gradient-to-b from-green-50 to-white px-6 py-5">
    <div>
      <h3 class="m-0 text-[15px] font-extrabold text-slate-900">Luyện tập (lặp lại ngắt quãng)</h3>
      <p class="mt-1.5 max-w-[560px] text-[13px] leading-relaxed text-slate-500">
        Thuật toán SM-2 giống Anki: từ đến hạn ôn được ưu tiên trong hàng đợi.
        Chọn topic và chế độ, sau đó mở trang luyện tập riêng.
      </p>
    </div>

    <div class="mt-4 flex flex-wrap items-end gap-3">
      <AppSelect
        v-model="topicId"
        label="Topic"
        wrapper-class="min-w-[180px] flex-1"
        :options="topicSelectOptions"
      />
      <AppSelect
        v-model="mode"
        label="Chế độ"
        wrapper-class="min-w-[180px] flex-1"
        :options="modeSelectOptions"
      />
      <button
        type="button"
        class="whitespace-nowrap rounded-[10px] border-0 bg-green-700 px-5 py-2.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-45"
        :disabled="!topicId || wordCount < 1"
        @click="goPractice"
      >
        Bắt đầu luyện tập
      </button>
    </div>

    <p v-if="wordCount < 1" class="mt-2.5 text-xs text-amber-600">Topic cần ít nhất 1 từ để luyện.</p>
    <p v-else-if="dueHint" class="mt-2.5 text-xs font-semibold text-green-700">{{ dueHint }}</p>

    <div class="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
      <div
        v-for="m in displayModes"
        :key="m.id"
        class="flex flex-col gap-0.5 rounded-[10px] border border-slate-200 bg-slate-50 px-3 py-2.5 text-[11px] text-slate-500"
      >
        <strong class="text-xs text-slate-900">{{ m.label }}</strong>
        <span>{{ m.description }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppSelect from '@/components/ui/AppSelect.vue'

const props = defineProps({
  topics: { type: Array, default: () => [] },
  modes: { type: Array, default: () => [] },
  defaultTopicId: { type: [Number, String], default: null },
  dueCount: { type: Number, default: null },
})

const router = useRouter()
const topicId = ref(props.defaultTopicId)
const mode = ref('flashcard')

watch(() => props.defaultTopicId, (id) => {
  if (id != null) topicId.value = id
}, { immediate: true })

const FALLBACK = [
  { id: 'flashcard', label: 'Flashcard', description: 'Lật thẻ EN ↔ VI' },
  { id: 'multiple', label: 'Trắc nghiệm', description: 'Chọn nghĩa đúng' },
  { id: 'reading', label: 'Đọc hiểu', description: 'Điền từ vào câu ví dụ' },
  { id: 'dictation', label: 'Nghe chép', description: 'Nghe câu ví dụ, gõ từ thiếu' },
]

const displayModes = computed(() =>
  props.modes?.length ? props.modes : FALLBACK
)

const topicSelectOptions = computed(() =>
  props.topics.map((t) => ({
    value: t.id,
    label: `${t.name} (${t.word_count} từ)`,
  })),
)

const modeSelectOptions = computed(() =>
  displayModes.value.map((m) => ({ value: m.id, label: m.label })),
)

const selectedTopic = computed(() =>
  props.topics.find(t => t.id === Number(topicId.value))
)

const wordCount = computed(() => selectedTopic.value?.word_count ?? 0)

const dueHint = computed(() => {
  if (props.dueCount == null) return ''
  if (props.dueCount > 0) return `${props.dueCount} từ đến hạn ôn trong topic này.`
  return 'Không có từ đến hạn — vẫn có thể ôn toàn bộ topic.'
})

function goPractice() {
  if (!topicId.value) return
  router.push({
    name: 'VocabPractice',
    params: { topicId: String(topicId.value) },
    query: { mode: mode.value },
  })
}
</script>
