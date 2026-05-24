<template>
  <div class="lb-page">
    <div class="mb-6">
      <h1 class="text-xl font-bold text-[var(--ink)]">Bảng xếp hạng</h1>
      <p class="mt-0.5 text-[13px] text-[var(--ink3)]">{{ periodSubtitle }}</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <button
          v-for="p in periods"
          :key="p.id"
          type="button"
          class="rounded-full border px-3 py-1 text-[12px] font-medium transition-colors"
          :class="period === p.id
            ? 'border-[#34d399] bg-[#f0fdf4] text-[#15803d]'
            : 'border-[var(--border)] text-[var(--ink2)] hover:border-[var(--ink3)]'"
          @click="setPeriod(p.id)"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <!-- Current user rank (when outside top 10) -->
    <div
      v-if="!loading && currentUserEntry && !currentUserInTop"
      class="mb-5 flex items-center gap-4 rounded-xl border-2 border-[#34d399] bg-[#f0fdf4] px-5 py-4"
    >
      <div class="text-2xl font-black text-[#15803d]">#{{ currentUserRank }}</div>
      <img
        :src="currentUserEntry.avatar_url || '/icon_profile.jpg'"
        alt=""
        class="h-11 w-11 rounded-full object-cover"
      />
      <div class="flex-1 min-w-0">
        <div class="text-[14px] font-bold text-[var(--ink)]">
          {{ currentUserEntry.display_name }}
          <span class="lb-you-badge">Bạn</span>
        </div>
        <div class="text-[12px] text-[var(--ink3)]">{{ currentUserEntry.xp.toLocaleString('vi-VN') }} XP</div>
      </div>
    </div>

    <!-- Top 3 podium -->
    <div v-if="!loading && topThree.length >= 3" class="podium mb-6">
      <div class="podium-item podium-2">
        <div class="podium-avatar-wrap">
          <img :src="topThree[1].avatar_url || '/icon_profile.jpg'" :alt="topThree[1].display_name" class="podium-avatar" />
          <div class="podium-rank rank-2">2</div>
        </div>
        <div class="podium-name">{{ topThree[1].display_name }}</div>
        <div class="podium-xp">{{ topThree[1].xp.toLocaleString('vi-VN') }} XP</div>
        <div class="podium-bar bar-2"></div>
      </div>

      <div class="podium-item podium-1">
        <div class="podium-crown">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" stroke-width="1.5"><path d="M3 17h18l-3-9-4.5 5L12 7l-1.5 6L6 8l-3 9z"/></svg>
        </div>
        <div class="podium-avatar-wrap">
          <img :src="topThree[0].avatar_url || '/icon_profile.jpg'" :alt="topThree[0].display_name" class="podium-avatar podium-avatar--large" />
          <div class="podium-rank rank-1">1</div>
        </div>
        <div class="podium-name font-bold">{{ topThree[0].display_name }}</div>
        <div class="podium-xp xp-gold">{{ topThree[0].xp.toLocaleString('vi-VN') }} XP</div>
        <div class="podium-bar bar-1"></div>
      </div>

      <div class="podium-item podium-3">
        <div class="podium-avatar-wrap">
          <img :src="topThree[2].avatar_url || '/icon_profile.jpg'" :alt="topThree[2].display_name" class="podium-avatar" />
          <div class="podium-rank rank-3">3</div>
        </div>
        <div class="podium-name">{{ topThree[2].display_name }}</div>
        <div class="podium-xp">{{ topThree[2].xp.toLocaleString('vi-VN') }} XP</div>
        <div class="podium-bar bar-3"></div>
      </div>
    </div>

    <div v-if="loading" class="ct-card overflow-hidden">
      <div v-for="i in 10" :key="i" class="flex items-center gap-4 border-b border-[var(--border)] px-5 py-3.5 last:border-0">
        <div class="h-4 w-6 animate-pulse rounded bg-[var(--bg2)]"></div>
        <div class="h-9 w-9 animate-pulse rounded-full bg-[var(--bg2)]"></div>
        <div class="flex-1 space-y-1.5">
          <div class="h-3.5 w-32 animate-pulse rounded bg-[var(--bg2)]"></div>
        </div>
      </div>
    </div>

    <div v-else class="ct-card overflow-hidden">
      <div
        v-for="entry in displayList"
        :key="`${entry.user_id}-${entry.rank}`"
        class="lb-row"
        :class="{ 'lb-row--me': entry.is_current_user }"
      >
        <div class="lb-rank">
          <span
            class="lb-rank-num"
            :class="{
              'text-[#f59e0b]': entry.rank === 1,
              'text-[#9ca3af]': entry.rank === 2,
              'text-[#b45309]': entry.rank === 3,
            }"
          >{{ entry.rank }}</span>
        </div>
        <img :src="entry.avatar_url || '/icon_profile.jpg'" :alt="entry.display_name" class="lb-avatar" />
        <div class="lb-info">
          <div class="lb-name">
            {{ entry.display_name }}
            <span v-if="entry.is_current_user" class="lb-you-badge">Bạn</span>
          </div>
          <div class="lb-streak">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2"><path d="M12 2c0 0-5 6-5 10a5 5 0 0 0 10 0c0-4-5-10-5-10z"/></svg>
            {{ entry.streak }} ngày streak
          </div>
        </div>
        <div class="lb-xp-col">
          <div class="lb-xp-bar-wrap">
            <div
              class="lb-xp-bar"
              :style="{ width: `${Math.min(100, (entry.xp / (maxXp || 1)) * 100)}%` }"
            ></div>
          </div>
          <div class="lb-xp-num">{{ entry.xp.toLocaleString('vi-VN') }} {{ scoreLabel }}</div>
        </div>
      </div>

      <div v-if="!displayList.length" class="py-12 text-center text-[13px] text-[var(--ink3)]">
        Chưa có dữ liệu xếp hạng.
      </div>
    </div>

    <div v-if="error" class="mt-4 rounded-xl border border-[var(--rose-l)] bg-[var(--rose-bg)] p-4 text-[13px] text-[var(--rose)]">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { leaderboardService } from '@/services/leaderboardService.js'

const loading = ref(false)
const error   = ref('')
const period  = ref('all')
const topList = ref([])
const currentUserRank = ref(null)
const currentUserEntry = ref(null)

const periods = [
  { id: 'all', label: 'Tất cả (XP)' },
  { id: 'weekly', label: 'Tuần này' },
  { id: 'monthly', label: 'Tháng này' },
]

const periodSubtitle = computed(() => {
  if (period.value === 'weekly') return 'Top 10 hoạt động 7 ngày qua (điểm hoạt động)'
  if (period.value === 'monthly') return 'Top 10 hoạt động 30 ngày qua (điểm hoạt động)'
  return 'Top 10 học viên theo XP tích lũy'
})

const scoreLabel = computed(() => (period.value === 'all' ? 'XP' : 'điểm'))

const topThree = computed(() => topList.value.slice(0, 3))

/** Ranks 4–10 from top list (or full list if fewer than 3 for podium). */
const displayList = computed(() => {
  if (topList.value.length <= 3) return topList.value
  return topList.value.slice(3)
})

const maxXp = computed(() => topList.value[0]?.xp || 1)

const currentUserInTop = computed(() =>
  topList.value.some(e => e.is_current_user)
)

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const data = await leaderboardService.getLeaderboard(10, period.value)
    topList.value = data.top || []
    currentUserRank.value = data.current_user_rank ?? null
    currentUserEntry.value = data.current_user ?? null
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không thể tải bảng xếp hạng'
  } finally {
    loading.value = false
  }
}

function setPeriod(id) {
  if (period.value === id) return
  period.value = id
  load()
}

onMounted(load)
</script>
