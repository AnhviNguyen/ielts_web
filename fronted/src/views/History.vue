<template>
  <div>
    <div class="mb-5 flex flex-wrap items-center gap-3">
      <FilterPills
        v-model="activeSkill"
        :options="skillFilters"
      />
      <div class="ml-auto w-full max-w-[220px]">
        <SearchInput v-model="search" placeholder="Tìm kiếm..." />
      </div>
    </div>

    <div v-if="filteredHistory.length" class="overflow-hidden rounded-[var(--r)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
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
          <button class="ml-2 whitespace-nowrap rounded-[var(--r-sm)] border border-[var(--border2)] bg-transparent px-3 py-1.5 text-xs font-semibold text-[var(--ink2)] transition-colors hover:bg-[var(--bg2)]">Xem lại</button>
        </template>
      </HistoryItem>
    </div>

    <EmptyState
      v-else
      icon="📋"
      title="Chưa có lịch sử"
      description="Hãy bắt đầu luyện tập để theo dõi tiến độ của bạn!"
      action-label="Bắt đầu ngay"
      action-to="/dashboard"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useIeltsStore } from '@/stores/ielts.js'
import HistoryItem from '@/components/ui/HistoryItem.vue'
import FilterPills from '@/components/ui/FilterPills.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const ielts = useIeltsStore()
const search = ref('')
const activeSkill = ref('all')

const skillFilters = [
  { id: 'all',        label: 'Tất cả' },
  { id: 'reading',    label: '📖 Reading' },
  { id: 'listening',  label: '🎧 Listening' },
  { id: 'writing',    label: '✍️ Writing' },
  { id: 'speaking',   label: '🎤 Speaking' },
  { id: 'vocabulary', label: '📚 Từ vựng' },
]

const filteredHistory = computed(() => {
  return ielts.history.filter(h => {
    const matchSkill  = activeSkill.value === 'all' || h.skill === activeSkill.value
    const matchSearch = search.value === '' || h.title.toLowerCase().includes(search.value.toLowerCase())
    return matchSkill && matchSearch
  })
})

onMounted(() => ielts.fetchHistory())
</script>
