<template>
  <div>
    <section class="section-white section-compact">
      <div class="app-container">
        <div class="page-header page-header--row">
          <div>
            <h1 class="font-display">Reading</h1>
            <p class="page-subtitle">{{ items.length }} bộ đề · IELTS Academic &amp; General</p>
          </div>
          <div class="ml-auto">
            <input v-model="search" class="ct-input w-full max-w-xs sm:w-64" placeholder="Tìm đề..." @input="page = 1" />
          </div>
        </div>
        <AppLoading v-if="loading" message="Đang tải danh sách đề..." />
        <div v-else-if="loadError" class="rounded-[var(--radius-comfortable)] border border-[var(--text-negative)] bg-[var(--rose-bg)] px-5 py-8 text-center text-[13px] text-[var(--text-negative)]">
          {{ loadError }}
          <button type="button" class="ct-btn mt-4" @click="loadItems">Thử lại</button>
        </div>
        <template v-else>
          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <SkillTestCard
              v-for="mt in paged" :key="mt.id"
              :title="mt.title"
              :thumbnail="mt.thumbnail"
              :book-code="mt.book_code"
              skill-label="Reading"
              :question-count="mt.quizzes?.full?.question_count"
              :time="mt.quizzes?.full?.time"
              :parts="partMetas(mt)"
              :attempted="mockCompletion(mt).attempted"
              :completed-part-keys="mockCompletion(mt).completedPartKeys"
              @start-full="openPicker(mt, mt.quizzes?.full)"
              @start-part="(p) => openPicker(mt, p)"
            />
            <p v-if="!paged.length" class="col-span-3 py-16 text-center text-[var(--text-subdued)]">Không tìm thấy đề phù hợp.</p>
          </div>
          <div class="mt-6">
            <Paginator v-model="page" :total="filtered.length" :page-size="PAGE_SIZE" />
          </div>
        </template>
      </div>
    </section>

    <ModePickerModal v-model="showPicker" :test-title="pickerTitle" @confirm="startQuiz" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listMockTests } from '@/services/mockTestService.js'
import { usePracticeStore } from '@/stores/practice.js'
import { useCompletedQuizIds } from '@/composables/useCompletedQuizIds.js'
import { mockTestCompletion } from '@/utils/testCompletion.js'
import SkillTestCard  from '@/components/ui/SkillTestCard.vue'
import ModePickerModal from '@/components/ui/ModePickerModal.vue'
import Paginator from '@/components/ui/Paginator.vue'
import AppLoading from '@/components/ui/AppLoading.vue'
const PAGE_SIZE = 9
const router = useRouter()
const practiceStore = usePracticeStore()
const { completedIds } = useCompletedQuizIds('reading')
const loading = ref(false), loadError = ref(''), search = ref(''), items = ref([]), page = ref(1)

function mockCompletion(mt) {
  return mockTestCompletion(mt, completedIds.value)
}

async function loadItems() {
  loading.value = true
  loadError.value = ''
  try {
    items.value = await listMockTests({ skillId: 1 })
  } catch (e) {
    loadError.value = e?.response?.data?.detail || 'Không tải được danh sách đề. Hãy thử lại.'
    items.value = []
  } finally {
    loading.value = false
  }
}

const filtered = computed(() =>
  !search.value ? items.value : items.value.filter(x => x.title?.toLowerCase().includes(search.value.toLowerCase()))
)
const paged = computed(() => filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

function partMetas(mt) {
  return Object.entries(mt?.quizzes || {}).filter(([k]) => k.startsWith('part_'))
    .sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }))
    .map(([key, meta]) => ({ key, ...meta }))
}

const showPicker = ref(false), pickerTitle = ref(''), pendingMt = ref(null), pendingQuiz = ref(null)
function openPicker(mt, quiz) {
  pendingMt.value = mt; pendingQuiz.value = quiz || mt.quizzes?.full
  pickerTitle.value = mt.title; showPicker.value = true
}
async function startQuiz(mode) {
  const quizId = pendingQuiz.value?.id
  if (!quizId) return
  const s = await practiceStore.startSession('reading', quizId)
  router.push(`/quiz/${s?.quiz?.id || quizId}?mode=${mode === 'exam' ? 'exam' : 'practice'}`)
}
onMounted(loadItems)
</script>
