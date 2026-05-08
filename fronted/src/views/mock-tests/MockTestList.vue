<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Mock Tests</h1>
        <p class="mt-0.5 text-[13px] text-[var(--ink3)]">{{ filtered.length }} bộ đề · Reading · Listening · Speaking</p>
      </div>
      <div class="ml-auto flex flex-wrap gap-2">
        <!-- Skill filter -->
        <div class="flex overflow-hidden rounded-lg border border-[var(--border)] bg-white text-[13px]">
          <button
            v-for="opt in skillOptions" :key="opt.value"
            class="border-r border-[var(--border)] px-3 py-2 font-medium last:border-r-0 transition-colors"
            :class="skillFilter === opt.value ? 'bg-[var(--purple)] text-white' : 'text-[var(--ink2)] hover:bg-[var(--bg)]'"
            @click="skillFilter = opt.value"
          >{{ opt.label }}</button>
        </div>
        <input v-model="search" class="ct-input" placeholder="Tìm đề..." />
      </div>
    </div>

    <div v-if="loading" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      <div v-for="i in 6" :key="i" class="h-64 animate-pulse rounded-xl bg-[var(--bg2)]"></div>
    </div>
    <p v-else-if="!filtered.length" class="py-20 text-center text-[var(--ink3)]">Không tìm thấy đề phù hợp.</p>
    <div v-else class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      <SkillTestCard
        v-for="mt in filtered" :key="mt.id"
        :title="mt.title"
        :thumbnail="mt.thumbnail"
        :book-code="mt.book_code"
        :skill-label="skillLabel(mt.skill_id)"
        :question-count="mt.quizzes?.full?.question_count"
        :time="mt.quizzes?.full?.time"
        :part-count="partCount(mt)"
        :parts="partMetas(mt)"
        @click="openPicker(mt, mt.quizzes?.full)"
        @start-full="openPicker(mt, mt.quizzes?.full)"
        @start-part="(p) => openPicker(mt, p)"
      />
    </div>

    <ModePickerModal v-model="showPicker" :test-title="pickerTitle" @confirm="startQuiz" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listMockTests } from '@/services/mockTestService.js'
import { usePracticeStore } from '@/stores/practice.js'
import SkillTestCard from '@/components/ui/SkillTestCard.vue'
import ModePickerModal from '@/components/ui/ModePickerModal.vue'

const router = useRouter()
const practiceStore = usePracticeStore()
const loading = ref(false), items = ref([]), search = ref(''), skillFilter = ref('all')

const skillOptions = [
  { label: 'Tất cả',    value: 'all' },
  { label: 'Reading',   value: '1' },
  { label: 'Listening', value: '2' },
  { label: 'Speaking',  value: '8' },
]

const filtered = computed(() =>
  items.value.filter(x => {
    const ms = skillFilter.value === 'all' || String(x.skill_id) === skillFilter.value
    const mt = !search.value || x.title?.toLowerCase().includes(search.value.toLowerCase())
    return ms && mt
  })
)

function skillLabel(id) {
  if (String(id) === '1') return 'Reading'
  if (String(id) === '2') return 'Listening'
  if (String(id) === '8') return 'Speaking'
  return 'Test'
}
function partCount(mt) { return Object.keys(mt?.quizzes || {}).filter(k => k.startsWith('part_')).length }
function partMetas(mt) {
  return Object.entries(mt?.quizzes || {}).filter(([k]) => k.startsWith('part_'))
    .sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }))
    .map(([key, meta]) => ({ key, ...meta }))
}

const showPicker = ref(false), pickerTitle = ref(''), pendingMt = ref(null), pendingQuiz = ref(null)
function openPicker(mt, quiz) { pendingMt.value = mt; pendingQuiz.value = quiz || mt.quizzes?.full; pickerTitle.value = mt.title; showPicker.value = true }
async function startQuiz(mode) {
  const quizId = pendingQuiz.value?.id || null
  const mt = pendingMt.value
  const subject = String(mt?.skill_id) === '2' ? 'listening' : 'reading'
  if (mode === 'exam') { if (quizId) router.push(`/quiz/${quizId}?mode=exam`) }
  else { const s = await practiceStore.startSession(subject, quizId); const id = s?.quiz?.id || quizId; if (id) router.push(`/quiz/${id}?mode=practice`) }
}

onMounted(async () => { loading.value = true; try { items.value = await listMockTests() } finally { loading.value = false } })
</script>
