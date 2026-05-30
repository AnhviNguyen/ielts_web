<template>
  <div class="fe-hub">
    <!-- Header (giống Reading / Listening) -->
    <div class="mb-6">
      <RouterLink
        to="/dashboard"
        class="mb-3 inline-flex items-center gap-1.5 text-[12px] text-[var(--ink3)] transition-colors hover:text-[var(--ink)]"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Trang chủ
      </RouterLink>
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <h1 class="text-xl font-bold text-[var(--ink)]">Full Mock Exam</h1>
          <p class="mt-0.5 text-[13px] text-[var(--ink3)]">
            {{ sets.length }} bộ đề · 4 kỹ năng · Computer-delivered
          </p>
        </div>
        <div class="ml-auto w-full sm:w-64">
          <input
            v-model="search"
            class="ct-input w-full"
            placeholder="Tìm bộ đề..."
          />
        </div>
      </div>
    </div>

    <!-- Hero -->
    <section class="fe-hero mb-6 overflow-hidden rounded-2xl border border-[#a7f3d0]/60 bg-gradient-to-br from-[#ecfdf5] via-white to-[#f0fdf4] p-5 sm:p-6">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div class="max-w-xl">
          <span class="inline-flex items-center gap-1.5 rounded-full border border-[#6ee7b7]/50 bg-white/80 px-2.5 py-1 text-[11px] font-semibold text-[#047857]">
            <span class="h-1.5 w-1.5 rounded-full bg-[#34d399]" />
            Mô phỏng thi máy tính
          </span>
          <h2 class="mt-3 font-display text-lg font-bold text-[var(--ink)] sm:text-xl">
            Trải nghiệm trọn bộ IELTS trong một phiên
          </h2>
          <p class="mt-2 text-[13px] leading-relaxed text-[var(--ink2)]">
            Reading → Listening → Writing (Task 1 &amp; 2) → Speaking, timer theo chuẩn thi thật.
            Có thời gian nghỉ luyện tập giữa các phần.
          </p>
        </div>
        <div class="fe-pipeline shrink-0">
          <div
            v-for="(step, i) in pipelineSteps"
            :key="step.label"
            class="fe-pipeline__item"
          >
            <div class="fe-pipeline__icon" v-html="step.icon" />
            <span class="fe-pipeline__label">{{ step.label }}</span>
            <svg
              v-if="i < pipelineSteps.length - 1"
              class="fe-pipeline__arrow hidden sm:block"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </div>
        </div>
      </div>
    </section>

    <AppLoading v-if="loading" message="Đang tải bộ đề Full Mock..." />

    <div
      v-else-if="error"
      class="rounded-xl border border-rose-200 bg-rose-50 px-5 py-8 text-center text-[13px] text-rose-700"
    >
      {{ error }}
      <button type="button" class="ct-btn mt-4" @click="load">Thử lại</button>
    </div>

    <template v-else>
      <div v-if="pagedSets.length" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <FullExamSetCard
          v-for="set in pagedSets"
          :key="set.id"
          :set="set"
          @start="startSet"
        />
      </div>
      <div v-if="filteredSets.length" class="mt-6">
        <Paginator v-model="page" :total="filteredSets.length" :page-size="PAGE_SIZE" />
      </div>

      <div v-else-if="sets.length" class="fe-empty">
        <p>Không tìm thấy bộ đề phù hợp với «{{ search }}».</p>
        <button type="button" class="ct-btn mt-3" @click="search = ''">Xóa bộ lọc</button>
      </div>

      <div v-else class="fe-empty fe-empty--wide">
        <div class="fe-empty__icon" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 11l3 3L22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
        </div>
        <p class="font-semibold text-[var(--ink)]">Chưa có bộ đề Full Mock</p>
        <p class="mt-1 max-w-md text-[13px] text-[var(--ink3)]">
          Cần dữ liệu Reading + Listening (Orange Test) trên server. Kiểm tra thư mục
          <code class="rounded bg-[var(--bg2)] px-1">backend/data</code>.
        </p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listFullExamSets } from '@/services/fullExamService.js'
import { useFullExamStore } from '@/stores/fullExam.js'
import { stageRoute } from '@/utils/fullExamNav.js'
import AppLoading from '@/components/ui/AppLoading.vue'
import FullExamSetCard from '@/components/full-exam/FullExamSetCard.vue'
import Paginator from '@/components/ui/Paginator.vue'

const PAGE_SIZE = 9

const pipelineSteps = [
  { label: 'Reading', icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>` },
  { label: 'Listening', icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z"/></svg>` },
  { label: 'Writing', icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>` },
  { label: 'Speaking', icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>` },
]

const router = useRouter()
const fullExam = useFullExamStore()
const sets = ref([])
const search = ref('')
const page = ref(1)
const loading = ref(false)
const error = ref('')

const filteredSets = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return sets.value
  return sets.value.filter(
    (s) =>
      s.title?.toLowerCase().includes(q) ||
      s.book?.toLowerCase().includes(q) ||
      String(s.test_number).includes(q),
  )
})

const pagedSets = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredSets.value.slice(start, start + PAGE_SIZE)
})

watch(search, () => {
  page.value = 1
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    sets.value = await listFullExamSets(200)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Không tải được danh sách đề'
    sets.value = []
  } finally {
    loading.value = false
  }
}

function startSet(set) {
  fullExam.start(set)
  const session = fullExam.getSession()
  router.push(stageRoute(router, session, 'reading'))
}

onMounted(load)
</script>

<style scoped>
.fe-hero {
  box-shadow: 0 1px 0 rgba(52, 211, 153, 0.08);
}
.fe-pipeline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 4px;
  padding: 12px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--border);
}
.fe-pipeline__item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.fe-pipeline__icon {
  display: flex;
  height: 32px;
  width: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #ecfdf5;
  color: #059669;
}
.fe-pipeline__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink2);
}
.fe-pipeline__arrow {
  margin: 0 2px;
  color: var(--ink3);
  opacity: 0.5;
}
.fe-empty {
  border-radius: 16px;
  border: 1px dashed var(--border2);
  background: var(--bg);
  padding: 48px 24px;
  text-align: center;
  font-size: 13px;
  color: var(--ink3);
}
.fe-empty--wide {
  padding: 56px 32px;
}
.fe-empty__icon {
  display: inline-flex;
  margin-bottom: 12px;
  height: 64px;
  width: 64px;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: #ecfdf5;
  color: #34d399;
}
</style>
