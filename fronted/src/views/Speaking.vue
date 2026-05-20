<template>
  <div class="page-wrapper">
    <div class="search-wrap mb-6 ml-auto">
      <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input
        v-model="search"
        class="search-input"
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

<style scoped>
.page-wrapper {
  padding-left: 1.25rem;
  padding-right: 1.25rem;
  max-width: 1280px;
  margin: 0 auto;
}

@media (min-width: 640px) {
  .page-wrapper {
    padding-left: 2rem;
    padding-right: 2rem;
  }
}

@media (min-width: 1024px) {
  .page-wrapper {
    padding-left: 3rem;
    padding-right: 3rem;
  }
}

/* ── Search ── */
.search-wrap {
  position: relative;
  align-self: flex-start;
  min-width: 200px;
}

@media (min-width: 640px) {
  .search-wrap {
    min-width: 240px;
  }
}

.search-icon {
  position: absolute;
  top: 50%;
  left: 0.75rem;
  transform: translateY(-50%);
  color: var(--ink3);
  pointer-events: none;
}

.search-input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 0.625rem;
  background: #fff;
  padding: 0.5rem 0.75rem 0.5rem 2.1rem;
  font-size: 13px;
  color: var(--ink);
  outline: none;
  transition: border-color 0.15s;
}

.search-input:focus {
  border-color: #34d399;
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.15);
}
</style>
