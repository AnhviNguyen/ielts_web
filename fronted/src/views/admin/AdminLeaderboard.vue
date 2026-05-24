<template>
  <div class="mx-auto max-w-7xl space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Quản trị bảng xếp hạng</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Kiểm tra XP/streak bất thường và ẩn user khỏi leaderboard công khai.</p>
      </div>
      <button class="ct-btn" @click="showAnomalies">Chỉ xem bất thường</button>
    </div>

    <section class="rounded-lg border border-[var(--border)] bg-white p-4">
      <div class="grid gap-3 md:grid-cols-[1fr_180px_120px]">
        <input v-model.trim="filters.q" class="ct-input" placeholder="Tìm email hoặc tên" @keyup.enter="loadLeaderboard(1)" />
        <select v-model="filters.hidden" class="ct-input">
          <option value="">Tất cả</option>
          <option value="false">Đang hiện</option>
          <option value="true">Đã ẩn</option>
        </select>
        <button class="ct-btn ct-btn-accent" @click="loadLeaderboard(1)">Lọc</button>
      </div>
    </section>

    <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>

    <section class="rounded-lg border border-[var(--border)] bg-white">
      <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
        <div class="text-sm font-semibold text-[var(--ink)]">{{ title }}</div>
        <div v-if="loading" class="text-xs text-[var(--ink3)]">Đang tải...</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
            <tr>
              <th class="px-4 py-2">User</th>
              <th class="px-4 py-2">XP</th>
              <th class="px-4 py-2">Streak</th>
              <th class="px-4 py-2">Attempts 24h</th>
              <th class="px-4 py-2">Band jump</th>
              <th class="px-4 py-2">Flags</th>
              <th class="px-4 py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in data.items" :key="user.id" class="border-t border-[var(--border)]">
              <td class="px-4 py-3">
                <RouterLink :to="`/admin/users/${user.id}`" class="font-semibold text-[var(--ink)] hover:text-[#059669]">{{ user.full_name || user.email }}</RouterLink>
                <div class="text-xs text-[var(--ink3)]">{{ user.email }}</div>
              </td>
              <td class="px-4 py-3 font-semibold">{{ user.xp }}</td>
              <td class="px-4 py-3">{{ user.streak }}</td>
              <td class="px-4 py-3">{{ user.attempts_24h }}</td>
              <td class="px-4 py-3">{{ user.max_band_jump }}</td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <span v-for="reason in user.reasons" :key="reason" class="rounded bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">{{ reason }}</span>
                  <span v-if="!user.reasons.length" class="text-xs text-[var(--ink3)]">—</span>
                </div>
              </td>
              <td class="px-4 py-3 text-right">
                <button class="ct-btn btn-sm" @click="toggleLeaderboard(user)">{{ user.is_leaderboard_hidden ? 'Hiện BXH' : 'Ẩn BXH' }}</button>
              </td>
            </tr>
            <tr v-if="!loading && !data.items.length">
              <td colspan="7" class="px-4 py-8 text-center text-sm text-[var(--ink3)]">Không có dữ liệu.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="!anomalyMode" class="flex items-center justify-between border-t border-[var(--border)] px-4 py-3 text-sm">
        <button class="ct-btn btn-sm" :disabled="data.page <= 1" @click="loadLeaderboard(data.page - 1)">Trước</button>
        <span class="text-[var(--ink3)]">Trang {{ data.page }} / {{ data.total_pages }}</span>
        <button class="ct-btn btn-sm" :disabled="data.page >= data.total_pages" @click="loadLeaderboard(data.page + 1)">Sau</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const loading = ref(false)
const error = ref('')
const anomalyMode = ref(false)
const data = reactive({ items: [], total: 0, page: 1, page_size: 20, total_pages: 1 })
const filters = reactive({ q: '', hidden: '' })
const title = computed(() => anomalyMode.value ? `${data.total} user bất thường` : `${data.total} user trên bảng xếp hạng`)

function params(page) {
  const p = { page, page_size: data.page_size }
  if (filters.q) p.q = filters.q
  if (filters.hidden !== '') p.hidden = filters.hidden
  return p
}

async function loadLeaderboard(page = 1) {
  anomalyMode.value = false
  loading.value = true
  error.value = ''
  try {
    Object.assign(data, await adminService.listLeaderboard(params(page)))
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không tải được leaderboard admin.'
  } finally {
    loading.value = false
  }
}

async function showAnomalies() {
  anomalyMode.value = true
  loading.value = true
  error.value = ''
  try {
    Object.assign(data, await adminService.listAnomalies())
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không tải được danh sách bất thường.'
  } finally {
    loading.value = false
  }
}

async function toggleLeaderboard(user) {
  const reason = !user.is_leaderboard_hidden ? window.prompt('Lý do ẩn khỏi bảng xếp hạng?', user.leaderboard_flag_reason || '') : ''
  if (!user.is_leaderboard_hidden && reason === null) return
  await adminService.updateLeaderboard(user.id, { is_leaderboard_hidden: !user.is_leaderboard_hidden, reason })
  if (anomalyMode.value) await showAnomalies()
  else await loadLeaderboard(data.page)
}

onMounted(() => loadLeaderboard())
</script>
