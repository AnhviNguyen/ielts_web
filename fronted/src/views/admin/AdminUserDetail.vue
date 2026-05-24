<template>
  <div class="mx-auto max-w-6xl space-y-4">
    <RouterLink to="/admin/users" class="text-sm font-semibold text-[var(--ink3)] hover:text-[var(--ink)]">← Quay lại danh sách</RouterLink>

    <div v-if="loading" class="rounded-lg border border-[var(--border)] bg-white p-6 text-sm text-[var(--ink3)]">Đang tải user...</div>
    <div v-else-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>

    <template v-else-if="user">
      <section class="rounded-lg border border-[var(--border)] bg-white p-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="text-xs font-bold uppercase text-[var(--ink3)]">User #{{ user.id }}</div>
            <h1 class="mt-1 text-2xl font-bold text-[var(--ink)]">{{ user.full_name || user.email }}</h1>
            <p class="mt-1 text-sm text-[var(--ink3)]">{{ user.email }}</p>
            <div class="mt-3 flex flex-wrap gap-2 text-xs font-semibold">
              <span class="rounded bg-[var(--bg)] px-2 py-1">{{ user.role }}</span>
              <span :class="user.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'" class="rounded px-2 py-1">{{ user.is_active ? 'Active' : 'Locked' }}</span>
              <span :class="user.is_leaderboard_hidden ? 'bg-amber-50 text-amber-700' : 'bg-[var(--bg)] text-[var(--ink2)]'" class="rounded px-2 py-1">{{ user.is_leaderboard_hidden ? 'Ẩn khỏi BXH' : 'Hiện trên BXH' }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <button class="ct-btn" @click="toggleLock">{{ user.is_active ? 'Khóa tài khoản' : 'Mở khóa' }}</button>
            <button class="ct-btn" @click="resetStats">Reset XP/Streak</button>
            <button class="ct-btn ct-btn-accent" @click="toggleLeaderboard">{{ user.is_leaderboard_hidden ? 'Hiện BXH' : 'Ẩn BXH' }}</button>
          </div>
        </div>
      </section>

      <section class="grid gap-4 md:grid-cols-4">
        <div v-for="card in cards" :key="card.label" class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="text-xs font-semibold uppercase text-[var(--ink3)]">{{ card.label }}</div>
          <div class="mt-2 text-2xl font-bold text-[var(--ink)]">{{ card.value }}</div>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">Profile</h2>
          <dl class="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div><dt class="text-xs text-[var(--ink3)]">Target band</dt><dd class="font-semibold">{{ user.target_band ?? '—' }}</dd></div>
            <div><dt class="text-xs text-[var(--ink3)]">Exam date</dt><dd class="font-semibold">{{ user.exam_date || '—' }}</dd></div>
            <div><dt class="text-xs text-[var(--ink3)]">Last activity</dt><dd class="font-semibold">{{ user.last_activity_date || '—' }}</dd></div>
            <div><dt class="text-xs text-[var(--ink3)]">Phone</dt><dd class="font-semibold">{{ user.phone || '—' }}</dd></div>
          </dl>
          <p v-if="user.lock_reason" class="mt-3 rounded bg-rose-50 p-3 text-xs text-rose-700">Khóa: {{ user.lock_reason }}</p>
          <p v-if="user.leaderboard_flag_reason" class="mt-3 rounded bg-amber-50 p-3 text-xs text-amber-700">BXH: {{ user.leaderboard_flag_reason }}</p>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">Progress</h2>
          <div class="mt-3 space-y-2">
            <div v-for="item in user.progress" :key="item.id" class="rounded-md bg-[var(--bg)] px-3 py-2">
              <div class="flex justify-between text-sm font-semibold"><span>{{ item.subject }}</span><span>{{ item.percentage }}%</span></div>
              <div class="mt-1 text-xs text-[var(--ink3)]">Band {{ item.band_score ?? '—' }} · {{ item.completed_questions }}/{{ item.total_questions }}</div>
            </div>
            <div v-if="!user.progress.length" class="text-sm text-[var(--ink3)]">Chưa có progress.</div>
          </div>
        </div>
      </section>

      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="border-b border-[var(--border)] px-4 py-3 text-sm font-bold">Lịch sử gần đây</div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[760px] text-left text-sm">
            <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
              <tr><th class="px-4 py-2">Ngày</th><th class="px-4 py-2">Skill</th><th class="px-4 py-2">Quiz</th><th class="px-4 py-2">Score</th><th class="px-4 py-2">Band</th><th class="px-4 py-2">Mode</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in user.recent_history" :key="item.id" class="border-t border-[var(--border)]">
                <td class="px-4 py-3">{{ formatDate(item.completed_at) }}</td>
                <td class="px-4 py-3">{{ item.subject || '—' }}</td>
                <td class="px-4 py-3">{{ item.quiz_id || '—' }}</td>
                <td class="px-4 py-3">{{ item.score ?? '—' }}/{{ item.total_questions ?? '—' }}</td>
                <td class="px-4 py-3">{{ item.band_score ?? '—' }}</td>
                <td class="px-4 py-3">{{ item.mode || '—' }}</td>
              </tr>
              <tr v-if="!user.recent_history.length"><td colspan="6" class="px-4 py-8 text-center text-sm text-[var(--ink3)]">Chưa có lịch sử.</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { adminService } from '@/services/adminService.js'

const route = useRoute()
const user = ref(null)
const loading = ref(true)
const error = ref('')

const cards = computed(() => [
  { label: 'XP', value: user.value?.xp ?? 0 },
  { label: 'Streak', value: user.value?.streak ?? 0 },
  { label: 'Vocab words', value: user.value?.vocab_word_count ?? 0 },
  { label: 'Practice sessions', value: user.value?.practice_summary?.total ?? 0 },
])

async function loadUser() {
  loading.value = true
  error.value = ''
  try {
    user.value = await adminService.getUser(route.params.id)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không tải được chi tiết user.'
  } finally {
    loading.value = false
  }
}

async function toggleLock() {
  const reason = user.value.is_active ? window.prompt('Lý do khóa tài khoản?', user.value.lock_reason || '') : ''
  if (user.value.is_active && reason === null) return
  user.value = await adminService.updateUserStatus(user.value.id, { is_active: !user.value.is_active, lock_reason: reason })
}

async function resetStats() {
  if (!window.confirm('Reset XP và streak của user này?')) return
  user.value = await adminService.resetXpStreak(user.value.id, { reset_xp: true, reset_streak: true })
}

async function toggleLeaderboard() {
  const reason = !user.value.is_leaderboard_hidden ? window.prompt('Lý do ẩn khỏi bảng xếp hạng?', user.value.leaderboard_flag_reason || '') : ''
  if (!user.value.is_leaderboard_hidden && reason === null) return
  user.value = await adminService.updateLeaderboard(user.value.id, { is_leaderboard_hidden: !user.value.is_leaderboard_hidden, reason })
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('vi-VN')
}

onMounted(loadUser)
</script>
