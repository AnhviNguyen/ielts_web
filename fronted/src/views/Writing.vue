<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <RouterLink to="/dashboard" class="mb-3 inline-flex items-center gap-1.5 text-[12px] text-[var(--ink3)] hover:text-[var(--ink)] transition-colors">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        Trang chủ
      </RouterLink>
    <div class="flex flex-wrap items-end gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Writing</h1>
        <p class="mt-0.5 text-[13px] text-[var(--ink3)]">{{ total }} đề luyện · Task 1 &amp; Task 2</p>
      </div>
      <div class="ml-auto flex flex-wrap items-center gap-2">
        <!-- Task filter -->
        <div class="flex overflow-hidden rounded-lg border border-[var(--border)] bg-white text-[12px]">
          <button
            v-for="opt in taskOpts"
            :key="opt.value"
            class="border-r border-[var(--border)] px-3 py-2 font-medium last:border-r-0 transition-colors"
            :class="taskFilter === opt.value ? 'bg-[#111] text-white' : 'text-[var(--ink2)] hover:bg-[var(--bg2)]'"
            @click="taskFilter = opt.value; page = 1; loadItems()"
          >{{ opt.label }}</button>
        </div>
        <input v-model="search" class="ct-input" placeholder="Tìm đề..." @input="page = 1" />
      </div>
    </div>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="i in 9" :key="i" class="h-40 animate-pulse rounded-xl bg-[var(--bg2)]"></div>
    </div>

    <template v-else>
      <!-- Cards — same layout as SkillTestCard / Cathoven -->
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="topic in filtered"
          :key="topic.id"
          class="ct-card flex flex-col overflow-hidden"
        >
          <!-- Header: icon + title + badge -->
          <div class="flex items-start gap-3 p-4 pb-3">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-[#f0fdf4] text-[13px] font-bold text-[#34d399]">
              T{{ topic.writing_task_type || '?' }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="mb-1.5 line-clamp-2 text-[14px] font-semibold leading-snug text-[var(--ink)]">
                {{ topic.title }}
              </div>
              <div class="flex flex-wrap items-center gap-1.5">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold"
                  :style="topic.writing_task_type === 1
                    ? 'background:#dbeafe;color:#1d4ed8'
                    : 'background:#f0fdf4;color:#065f46'"
                >Task {{ topic.writing_task_type || '?' }}</span>
                <span v-for="tag in (topic.tags || []).slice(0, 2)" :key="tag"
                  class="rounded-full bg-[var(--bg2)] px-2 py-0.5 text-[10px] text-[var(--ink3)]">{{ tag }}</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-between gap-3 border-t border-[var(--border)] px-4 py-3">
            <div class="text-[11px] text-[var(--ink3)]">
              {{ topic.writing_task_type === 1 ? '20 phút · ≥150 từ' : '40 phút · ≥250 từ' }}
            </div>
            <button
              class="flex items-center gap-1.5 rounded-lg border border-[var(--border2)] bg-white px-3 py-1.5 text-[12px] font-semibold text-[var(--ink)] transition-colors hover:bg-[var(--bg2)]"
              @click="openPicker(topic)"
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

      <!-- Pagination -->
      <div class="mt-6">
        <Paginator v-model="page" :total="total" :page-size="PAGE_SIZE" @update:model-value="loadItems" />
      </div>
    </template>

    <!-- Mode picker -->
    <ModePickerModal v-model="showPicker" :test-title="pickerTitle" @confirm="startWriting" />

  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listWritingTopics } from '@/services/mockTestService.js'
import ModePickerModal from '@/components/ui/ModePickerModal.vue'
import Paginator from '@/components/ui/Paginator.vue'

const router = useRouter()

const PAGE_SIZE = 9
const loading  = ref(false)
const items    = ref([])
const total    = ref(0)
const page     = ref(1)
const search   = ref('')
const taskFilter = ref(0)
const taskOpts = [
  { value: 0, label: 'Tất cả' },
  { value: 1, label: 'Task 1' },
  { value: 2, label: 'Task 2' },
]

const filtered = computed(() =>
  !search.value
    ? items.value
    : items.value.filter(x => (x.title + (x.prompt_text || '')).toLowerCase().includes(search.value.toLowerCase()))
)

const showPicker   = ref(false)
const pickerTitle  = ref('')
const currentTopic = ref(null)

function openPicker(topic) {
  currentTopic.value = topic
  pickerTitle.value  = topic.title
  showPicker.value   = true
}
function startWriting(mode) {
  router.push({
    path: `/writing/editor/${currentTopic.value.id}`,
    state: { topic: currentTopic.value, mode }
  })
}

async function loadItems() {
  loading.value = true
  try {
    const tt = taskFilter.value || undefined
    const payload = await listWritingTopics({ taskType: tt, page: page.value, pageSize: PAGE_SIZE })
    items.value = payload.items || []
    total.value = payload.total || 0
  } finally {
    loading.value = false
  }
}

watch(page, loadItems)
onMounted(loadItems)
</script>
