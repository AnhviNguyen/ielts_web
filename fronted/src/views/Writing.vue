<template>
  <div>
    <section class="section-white section-compact">
      <div class="app-container">
        <div class="page-header page-header--row">
          <div>
            <h1 class="font-display">Writing</h1>
            <p class="page-subtitle">{{ total }} bộ đề · mỗi bộ gồm Task 1 + Task 2</p>
          </div>
          <div class="ml-auto w-full max-w-[220px]">
            <input v-model="search" class="ct-input w-full" placeholder="Tìm đề..." />
          </div>
        </div>
    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="i in 9" :key="i" class="h-40 animate-pulse rounded-xl bg-[var(--bg2)]"></div>
    </div>

    <template v-else>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="set in filtered"
          :key="set.id"
          class="ct-card flex flex-col overflow-hidden"
        >
          <div class="flex items-start gap-3 p-4 pb-3">
            <div class="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-lg bg-[var(--green-bg)] text-[10px] font-bold leading-tight text-[var(--spotify-green)]">
              <span>T1</span>
              <span class="text-[var(--ink3)]">+</span>
              <span>T2</span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="mb-1.5 line-clamp-2 text-[14px] font-semibold leading-snug text-[var(--ink)]">
                {{ set.title }}
              </div>
              <div class="flex flex-wrap items-center gap-1.5">
                <span class="inline-flex items-center rounded-full bg-[var(--blue-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--blue)]">Task 1</span>
                <span class="inline-flex items-center rounded-full bg-[var(--green-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--spotify-green-dark)]">Task 2</span>
                <span
                  v-if="writingStatus(set).fullyDone"
                  class="inline-flex items-center gap-1 rounded-full bg-[var(--green-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--spotify-green-dark)]"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                  Đã làm
                </span>
                <span
                  v-else-if="writingStatus(set).attempted"
                  class="inline-flex items-center gap-1 rounded-full bg-[var(--amber-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--text-warning)]"
                >
                  {{ writingStatus(set).task1Done ? 'T1 ✓' : '' }}{{ writingStatus(set).task1Done && writingStatus(set).task2Done ? ' · ' : '' }}{{ writingStatus(set).task2Done ? 'T2 ✓' : '' }}
                </span>
              </div>
              <p class="mt-2 line-clamp-2 text-[11px] text-[var(--ink3)]">{{ set.task1_title }}</p>
            </div>
          </div>

          <div class="flex items-center justify-between gap-3 border-t border-[var(--border)] px-4 py-3">
            <div class="text-[11px] text-[var(--ink3)]">60 phút · T1 ≥150 + T2 ≥250 từ</div>
            <button
              class="flex items-center gap-1.5 rounded-lg border border-[var(--border2)] bg-[var(--bg-surface)] px-3 py-1.5 text-[12px] font-semibold text-[var(--ink)] transition-[background,border-color] duration-200 ease-in-out hover:bg-[var(--bg2)]"
              @click="openPicker(set)"
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Start
            </button>
          </div>
        </div>

        <p v-if="!filtered.length && !loading" class="col-span-3 py-16 text-center text-[var(--ink3)]">
          Không tìm thấy đề phù hợp.
        </p>
      </div>

      <div class="mt-6">
        <Paginator v-model="page" :total="total" :page-size="PAGE_SIZE" @update:model-value="onPageChange" />
      </div>
    </template>

      </div>
    </section>

    <ModePickerModal v-model="showPicker" :test-title="pickerTitle" @confirm="startWriting" />
    <AiKeyRequiredModal :open="showGate" @close="goBack" @profile="goToProfile" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listWritingSets } from '@/services/writingService.js'
import { useCompletedQuizIds } from '@/composables/useCompletedQuizIds.js'
import { writingSetCompletion } from '@/utils/testCompletion.js'
import { useAiKeyGate } from '@/composables/useAiKeyGate.js'
import ModePickerModal from '@/components/ui/ModePickerModal.vue'
import Paginator from '@/components/ui/Paginator.vue'
import AiKeyRequiredModal from '@/components/ui/AiKeyRequiredModal.vue'
import { cloneRouterState } from '@/utils/routerState.js'
const router = useRouter()
const { showGate, hasAiKey, checkAiKey, goToProfile, goBack } = useAiKeyGate()
const { completedIds } = useCompletedQuizIds('writing')

const PAGE_SIZE = 9
const loading = ref(false)
const allSets = ref([])
const page = ref(1)
const search = ref('')

const total = computed(() => allSets.value.length)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  let items = allSets.value
  if (q) {
    items = items.filter((s) =>
      [s.title, s.task1_title, s.task2_title].join(' ').toLowerCase().includes(q),
    )
  }
  const start = (page.value - 1) * PAGE_SIZE
  return items.slice(start, start + PAGE_SIZE)
})

const showPicker = ref(false)
const pickerTitle = ref('')
const currentSet = ref(null)

function writingStatus(set) {
  return writingSetCompletion(set, completedIds.value)
}

async function openPicker(set) {
  const ok = await checkAiKey()
  if (!ok) return
  currentSet.value = set
  pickerTitle.value = set.title
  showPicker.value = true
}

function startWriting(mode) {
  if (!hasAiKey.value) {
    checkAiKey()
    return
  }
  const set = currentSet.value
  if (!set) return
  router.push({
    path: `/writing/editor/${set.task1_topic_id}`,
    state: cloneRouterState({
      writingSet: set,
      taskStep: 1,
      mode,
    }),
  })
}

function onPageChange(p) {
  page.value = p
}

async function loadItems() {
  loading.value = true
  try {
    const payload = await listWritingSets()
    allSets.value = payload.items || []
    if (page.value > 1 && (page.value - 1) * PAGE_SIZE >= allSets.value.length) {
      page.value = 1
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await checkAiKey()
  loadItems()
})
</script>
