<template>
  <section class="study-launcher">
    <div class="study-launcher__intro">
      <h3>Luyện tập (lặp lại ngắt quãng)</h3>
      <p>
        Thuật toán SM-2 giống Anki: từ đến hạn ôn được ưu tiên trong hàng đợi.
        Chọn topic và chế độ, sau đó mở trang luyện tập riêng.
      </p>
    </div>

    <div class="study-launcher__form">
      <div class="field">
        <label>Topic</label>
        <select v-model="topicId" class="select">
          <option v-for="t in topics" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.word_count }} từ)
          </option>
        </select>
      </div>
      <div class="field">
        <label>Chế độ</label>
        <select v-model="mode" class="select">
          <option v-for="m in displayModes" :key="m.id" :value="m.id">{{ m.label }}</option>
        </select>
      </div>
      <button
        type="button"
        class="start-btn"
        :disabled="!topicId || wordCount < 1"
        @click="goPractice"
      >
        Bắt đầu luyện tập
      </button>
    </div>

    <p v-if="wordCount < 1" class="hint">Topic cần ít nhất 1 từ để luyện.</p>
    <p v-else-if="dueHint" class="due-hint">{{ dueHint }}</p>

    <div class="mode-preview">
      <div v-for="m in displayModes" :key="m.id" class="mode-chip">
        <strong>{{ m.label }}</strong>
        <span>{{ m.description }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

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

<style scoped>
.study-launcher {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(180deg, #f0fdf4 0%, #fff 40%);
}
.study-launcher__intro h3 { margin: 0; font-size: 15px; font-weight: 800; color: #0f172a; }
.study-launcher__intro p { margin: 6px 0 0; font-size: 13px; color: #64748b; line-height: 1.5; max-width: 560px; }
.study-launcher__form {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-top: 16px;
}
.field { display: flex; flex-direction: column; gap: 4px; min-width: 180px; flex: 1; }
.field label { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #94a3b8; }
.select {
  padding: 10px 12px; border-radius: 10px; border: 1.5px solid #e2e8f0;
  font-size: 14px; background: #fff;
}
.start-btn {
  padding: 10px 22px; border-radius: 10px; border: none;
  background: #15803d; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer;
  white-space: nowrap;
}
.start-btn:disabled { opacity: .45; cursor: not-allowed; }
.hint { font-size: 12px; color: #d97706; margin: 10px 0 0; }
.due-hint { font-size: 12px; color: #059669; margin: 10px 0 0; font-weight: 600; }
.mode-preview {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 16px;
}
@media (min-width: 768px) { .mode-preview { grid-template-columns: repeat(4, 1fr); } }
.mode-chip {
  padding: 10px 12px; border-radius: 10px; border: 1px solid #e2e8f0; background: #f8fafc;
  display: flex; flex-direction: column; gap: 2px; font-size: 11px; color: #64748b;
}
.mode-chip strong { font-size: 12px; color: #0f172a; }
</style>
