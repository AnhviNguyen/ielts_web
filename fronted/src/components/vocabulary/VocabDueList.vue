<template>
  <section class="flex-1 px-5 py-6 sm:px-9 sm:py-7">
    <div v-if="loading" class="py-14 text-center text-sm text-[var(--ink3)]">Đang tải từ đến hạn...</div>

    <div v-else-if="!topics.length" class="py-14 text-center text-sm text-[var(--ink3)]">
      Chưa có topic. Tạo topic và thêm từ để bắt đầu ôn SRS.
    </div>

    <div v-else-if="!dueRows.length" class="flex flex-col items-center py-14 text-center text-[var(--ink3)]">
      <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--green-bg)] text-xl text-[var(--spotify-green-dark)]">✓</span>
      Hôm nay không còn từ đến hạn. Bạn đã ôn xong!
    </div>

    <ul v-else class="m-0 flex list-none flex-col gap-4 p-0">
      <li
        v-for="row in dueRows"
        :key="row.topicId"
        class="flex flex-col items-stretch justify-between gap-4 rounded-2xl border-2 border-[var(--border)] bg-[var(--bg-interactive)] px-5 py-4 transition-all hover:border-[var(--spotify-green)] sm:flex-row sm:items-center"
      >
        <p class="flex-1 text-sm leading-relaxed text-[var(--ink2)]">
          Hôm nay bạn còn
          <strong class="text-lg font-extrabold text-[var(--ink)]">{{ row.dueCount }}</strong>
          từ chưa học trong topic
          <strong class="font-bold text-[var(--spotify-green-dark)]">«{{ row.topicName }}»</strong>
        </p>
        <button
          type="button"
          class="inline-flex shrink-0 items-center justify-center gap-1.5 self-end rounded-full bg-[var(--spotify-green)] px-5 py-2.5 text-sm font-extrabold text-black transition-transform hover:translate-x-0.5 sm:self-center"
          @click="goStudy(row.topicId)"
        >
          Go to
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </li>
    </ul>

    <p v-if="totalDue > 0 && !loading" class="mt-6 text-right text-xs text-[var(--ink3)]">
      Tổng cộng <strong class="text-[var(--spotify-green-dark)]">{{ totalDue }}</strong> từ đến hạn hôm nay
    </p>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getStudyQueue } from '@/services/vocabularyService.js'

const props = defineProps({
  topics: { type: Array, default: () => [] },
})

const router = useRouter()
const loading = ref(false)
const dueByTopic = ref({})

const dueRows = computed(() =>
  props.topics
    .map((t) => ({
      topicId: t.id,
      topicName: t.name,
      dueCount: dueByTopic.value[t.id] ?? 0,
    }))
    .filter((r) => r.dueCount > 0)
    .sort((a, b) => b.dueCount - a.dueCount)
)

const totalDue = computed(() => dueRows.value.reduce((s, r) => s + r.dueCount, 0))

watch(() => props.topics, (list) => { if (list?.length) loadAllDue() }, { immediate: true, deep: true })

async function loadAllDue() {
  loading.value = true
  const map = {}
  try {
    await Promise.all(
      props.topics.map(async (t) => {
        if (!t.word_count) { map[t.id] = 0; return }
        try {
          const q = await getStudyQueue(t.id)
          map[t.id] = q.due_count ?? 0
        } catch {
          map[t.id] = 0
        }
      })
    )
    dueByTopic.value = map
  } finally {
    loading.value = false
  }
}

function goStudy(topicId) {
  router.push({ name: 'VocabPractice', params: { topicId: String(topicId) }, query: { mode: 'flashcard' } })
}

defineExpose({ reload: loadAllDue })
</script>
