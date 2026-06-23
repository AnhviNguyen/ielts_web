<template>
  <div>
    <section class="section-white section-compact">
      <div class="app-container">
        <div class="page-header" data-tour="page-header">
          <h1 class="font-display">Lịch sử luyện tập</h1>
          <p class="page-subtitle">Theo dõi các bài đã làm theo kỹ năng</p>
        </div>
    <div class="mb-5 flex flex-wrap items-center gap-3" data-tour="history-filters">
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="f in skillFilters"
          :key="f.id"
          class="history-filter-btn"
          :class="{ active: activeSkill === f.id }"
          @click="onSkillChange(f.id)"
        >
          <span v-html="f.icon" class="filter-icon"></span>
          {{ f.label }}
        </button>
      </div>
      <div class="ml-auto w-full max-w-[220px]">
        <SearchInput v-model="search" placeholder="Tìm kiếm..." />
      </div>
    </div>

    <AppLoading v-if="loading" message="Đang tải lịch sử..." />

    <div v-else-if="loadError" class="rounded-xl border border-[var(--rose-l)] bg-[var(--rose-bg)] p-4 text-[13px] text-[var(--rose)]">
      {{ loadError }}
      <button class="link-btn ml-2" @click="loadPage(currentPage)">Thử lại</button>
    </div>

    <template v-else>
      <div
        v-if="filteredHistory.length"
        data-tour="history-list"
        class="overflow-hidden rounded-[var(--r)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]"
      >
        <HistoryItem
          v-for="item in filteredHistory"
          :key="item.id"
          :skill-id="item.skill"
          :title="item.title"
          :date="item.date"
          :duration="item.duration"
          :score="item.score"
          :mode="item.mode"
        >
          <template #actions>
            <RouterLink
              v-if="item.session_id"
              :to="{ name: 'ReviewAnswer', params: { sessionId: item.session_id } }"
              class="history-action-btn history-action-btn--primary"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
              Xem lời giải
            </RouterLink>
            <RouterLink
              v-else-if="item.quiz_id && (item.skill === 'reading' || item.skill === 'listening')"
              :to="{ name: 'ReviewAnswerByQuiz', params: { quizId: item.quiz_id } }"
              class="history-action-btn history-action-btn--primary"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
              Xem lời giải
            </RouterLink>
            <RouterLink
              v-else-if="item.skill === 'writing' && item.id"
              :to="{ name: 'WritingResult', params: { historyId: item.id } }"
              class="history-action-btn history-action-btn--primary"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Xem phản hồi AI
            </RouterLink>
            <RouterLink
              v-else-if="item.skill === 'speaking' && item.quiz_id"
              :to="{ path: '/speaking/result', state: { fetchSummary: true, quiz_id: item.quiz_id, question: item.title } }"
              class="history-action-btn history-action-btn--primary"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
              Xem kết quả
            </RouterLink>
            <button v-else class="history-action-btn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              Xem lại
            </button>
          </template>
        </HistoryItem>
      </div>

      <EmptyState
        v-else
        title="Chưa có lịch sử"
        description="Hãy bắt đầu luyện tập để theo dõi tiến độ của bạn!"
        action-label="Bắt đầu ngay"
        action-to="/dashboard"
      />

      <div v-if="total > 0" class="mt-5 flex flex-wrap items-center justify-between gap-3">
        <p class="text-[12px] text-[var(--ink3)]">
          Hiển thị {{ rangeLabel }} / {{ total }} bài
        </p>
        <Paginator v-model="currentPage" :total="total" :page-size="pageSize" @update:model-value="loadPage" />
      </div>
    </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { historyService, mapHistoryItem } from '@/services/historyService.js'
import HistoryItem from '@/components/ui/HistoryItem.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Paginator from '@/components/ui/Paginator.vue'
import AppLoading from '@/components/ui/AppLoading.vue'

const PAGE_SIZE = 15

const search       = ref('')
const activeSkill  = ref('all')
const historyItems = ref([])
const total        = ref(0)
const currentPage  = ref(1)
const pageSize     = PAGE_SIZE
const loading      = ref(false)
const loadError    = ref('')

const SVG = {
  all:       `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
  reading:   `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  listening: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
  writing:   `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  speaking:  `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
  vocabulary:`<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
}

const skillFilters = [
  { id: 'all',        label: 'Tất cả',    icon: SVG.all },
  { id: 'reading',    label: 'Reading',   icon: SVG.reading },
  { id: 'listening',  label: 'Listening', icon: SVG.listening },
  { id: 'writing',    label: 'Writing',   icon: SVG.writing },
  { id: 'speaking',   label: 'Speaking',  icon: SVG.speaking },
]

const filteredHistory = computed(() =>
  historyItems.value.filter(h => {
    const matchSearch = !search.value || h.title.toLowerCase().includes(search.value.toLowerCase())
    return matchSearch
  })
)

const rangeLabel = computed(() => {
  if (!total.value) return '0'
  const start = (currentPage.value - 1) * pageSize + 1
  const end = Math.min(currentPage.value * pageSize, total.value)
  return `${start}–${end}`
})

async function loadPage(page = 1) {
  loading.value = true
  loadError.value = ''
  currentPage.value = page
  try {
    const params = { page, page_size: pageSize }
    if (activeSkill.value !== 'all') {
      params.subject = activeSkill.value.charAt(0).toUpperCase() + activeSkill.value.slice(1)
    }
    const data = await historyService.list(params)
    historyItems.value = (data.items || []).map(mapHistoryItem)
    total.value = data.total ?? 0
  } catch (err) {
    loadError.value = err.response?.data?.detail || 'Không thể tải lịch sử'
    historyItems.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSkillChange(skill) {
  activeSkill.value = skill
  loadPage(1)
}

watch(search, () => { /* client-side filter only */ })

onMounted(() => loadPage(1))
</script>
