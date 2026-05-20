<template>
  <div class="lb-page">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-[var(--ink)]">Bảng xếp hạng</h1>
      <p class="mt-0.5 text-[13px] text-[var(--ink3)]">Top học viên theo điểm XP tích lũy</p>
    </div>

    <!-- Top 3 podium -->
    <div v-if="!loading && topThree.length >= 3" class="podium mb-6">
      <!-- 2nd place -->
      <div class="podium-item podium-2">
        <div class="podium-avatar-wrap">
          <img :src="topThree[1].avatar_url || '/icon_profile.jpg'" :alt="topThree[1].display_name" class="podium-avatar" />
          <div class="podium-rank rank-2">2</div>
        </div>
        <div class="podium-name">{{ topThree[1].display_name }}</div>
        <div class="podium-xp">{{ topThree[1].xp.toLocaleString('vi-VN') }} XP</div>
        <div class="podium-bar bar-2"></div>
      </div>

      <!-- 1st place -->
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

      <!-- 3rd place -->
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

    <!-- Loading skeleton -->
    <div v-if="loading" class="ct-card overflow-hidden">
      <div v-for="i in 10" :key="i" class="flex items-center gap-4 border-b border-[var(--border)] px-5 py-3.5 last:border-0">
        <div class="h-4 w-6 animate-pulse rounded bg-[var(--bg2)]"></div>
        <div class="h-9 w-9 animate-pulse rounded-full bg-[var(--bg2)]"></div>
        <div class="flex-1 space-y-1.5">
          <div class="h-3.5 w-32 animate-pulse rounded bg-[var(--bg2)]"></div>
          <div class="h-3 w-20 animate-pulse rounded bg-[var(--bg2)]"></div>
        </div>
        <div class="h-4 w-16 animate-pulse rounded bg-[var(--bg2)]"></div>
      </div>
    </div>

    <!-- Leaderboard list (rank 4+) -->
    <div v-else class="ct-card overflow-hidden">
      <div
        v-for="entry in restList"
        :key="entry.user_id"
        class="lb-row"
        :class="{ 'lb-row--me': entry.is_current_user }"
      >
        <!-- Rank number -->
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

        <!-- Avatar -->
        <img
          :src="entry.avatar_url || '/icon_profile.jpg'"
          :alt="entry.display_name"
          class="lb-avatar"
        />

        <!-- Name & streak -->
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

        <!-- XP bar + number -->
        <div class="lb-xp-col">
          <div class="lb-xp-bar-wrap">
            <div
              class="lb-xp-bar"
              :style="{ width: `${Math.min(100, (entry.xp / (items[0]?.xp || 1)) * 100)}%` }"
            ></div>
          </div>
          <div class="lb-xp-num">{{ entry.xp.toLocaleString('vi-VN') }} XP</div>
        </div>
      </div>

      <div v-if="!restList.length && !loading" class="py-12 text-center text-[13px] text-[var(--ink3)]">
        Chưa có dữ liệu xếp hạng.
      </div>
    </div>

    <!-- Error state -->
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
const items   = ref([])

const topThree = computed(() => items.value.slice(0, 3))
const restList = computed(() => items.value.slice(3))

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const data = await leaderboardService.getLeaderboard(50)
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không thể tải bảng xếp hạng'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.lb-page { max-width: 700px; }

/* ── Podium ── */
.podium {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 12px;
  padding: 0 16px;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  max-width: 160px;
}

.podium-crown {
  margin-bottom: -4px;
}

.podium-avatar-wrap {
  position: relative;
}

.podium-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border);
}

.podium-avatar--large {
  width: 68px;
  height: 68px;
}

.podium-rank {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: white;
  border: 1.5px solid white;
}

.rank-1 { background: #f59e0b; }
.rank-2 { background: #9ca3af; }
.rank-3 { background: #b45309; }

.podium-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink);
  text-align: center;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.podium-xp {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink3);
}

.xp-gold { color: #d97706; }

.podium-bar {
  width: 100%;
  border-radius: 8px 8px 0 0;
}
.bar-1 { height: 64px; background: linear-gradient(180deg, #fde68a, #f59e0b); }
.bar-2 { height: 48px; background: linear-gradient(180deg, #e5e7eb, #9ca3af); }
.bar-3 { height: 36px; background: linear-gradient(180deg, #fde8c8, #b45309); }

/* ── List rows ── */
.lb-row {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border);
  padding: 12px 20px;
  transition: background 0.15s;
}
.lb-row:last-child { border-bottom: none; }
.lb-row:hover { background: var(--bg); }
.lb-row--me { background: #f0fdf4; }

.lb-rank { width: 32px; text-align: right; }
.lb-rank-num { font-size: 14px; font-weight: 700; color: var(--ink3); }

.lb-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.lb-info { flex: 1; min-width: 0; }
.lb-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 6px;
}
.lb-streak {
  font-size: 11px;
  color: var(--ink3);
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: 2px;
}

.lb-you-badge {
  font-size: 10px;
  font-weight: 700;
  background: #d1fae5;
  color: #065f46;
  padding: 1px 6px;
  border-radius: 20px;
}

.lb-xp-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 100px;
}

.lb-xp-bar-wrap {
  width: 80px;
  height: 4px;
  background: var(--bg2);
  border-radius: 2px;
  overflow: hidden;
}

.lb-xp-bar {
  height: 100%;
  background: #34d399;
  border-radius: 2px;
  transition: width 0.8s ease;
}

.lb-xp-num {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink2);
}
</style>
