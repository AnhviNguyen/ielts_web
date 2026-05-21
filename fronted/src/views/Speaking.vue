<template>
  <div class="page-wrapper page-wrapper--constrained">
    <div class="skill-search-wrap mb-6 ml-auto">
      <svg class="skill-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input
        v-model="search"
        class="skill-search-input"
        placeholder="Tìm đề..."
        @input="page = 1"
      />
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="i in PAGE_SIZE" :key="i" class="h-48 animate-pulse rounded-2xl bg-[var(--bg2)]" />
    </div>

    <!-- Grid -->
    <template v-else>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <SkillTestCard
          v-for="mt in paged"
          :key="mt.id"
          :title="mt.title"
          :thumbnail="mt.thumbnail"
          :book-code="mt.book_code"
          skill-label="Speaking"
          :question-count="mt.quizzes?.full?.question_count"
          :time="mt.quizzes?.full?.time"
          :parts="partMetas(mt)"
          @start-full="openPicker(mt, mt.quizzes?.full)"
          @start-part="(p) => openPicker(mt, p)"
        />
        <p v-if="!paged.length" class="col-span-3 py-20 text-center text-[var(--ink3)]">
          Không tìm thấy đề phù hợp.
        </p>
      </div>

      <div class="mt-6">
        <Paginator v-model="page" :total="filtered.length" :page-size="PAGE_SIZE" />
      </div>
    </template>

    <ModePickerModal v-model="showPicker" :test-title="pickerTitle" @confirm="startQuiz" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listMockTests } from '@/services/mockTestService.js'
import SkillTestCard   from '@/components/ui/SkillTestCard.vue'
import ModePickerModal from '@/components/ui/ModePickerModal.vue'
import Paginator       from '@/components/ui/Paginator.vue'

const PAGE_SIZE = 9
const router  = useRouter()
const loading = ref(false)
const search  = ref('')
const items   = ref([])
const page    = ref(1)

const filtered = computed(() =>
  !search.value
    ? items.value
    : items.value.filter(x => x.title?.toLowerCase().includes(search.value.toLowerCase()))
)
const paged = computed(() =>
  filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE)
)

function partMetas(mt) {
  return Object.entries(mt?.quizzes || {})
    .filter(([k]) => k.startsWith('part_'))
    .sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }))
    .map(([key, meta]) => ({ key, ...meta }))
}

const showPicker  = ref(false)
const pickerTitle = ref('')
const pendingQuiz = ref(null)

function openPicker(mt, quiz) {
  pendingQuiz.value  = quiz || mt.quizzes?.full
  pickerTitle.value  = mt.title
  showPicker.value   = true
}
function startQuiz(mode) {
  const id = pendingQuiz.value?.id
  if (id) router.push(`/quiz/${id}?mode=${mode}`)
}

onMounted(async () => {
  loading.value = true
  try { items.value = await listMockTests({ skillId: 8 }) }
  finally { loading.value = false }
})
</script>
