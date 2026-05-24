<template>
  <div class="mx-auto max-w-7xl space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Quản lý người dùng</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Tìm kiếm, khóa tài khoản, reset XP/streak và quản trị leaderboard.</p>
      </div>
    </div>

    <section class="rounded-lg border border-[var(--border)] bg-white p-4">
      <div class="grid gap-3 md:grid-cols-[1fr_140px_140px_170px_150px]">
        <input v-model.trim="filters.q" class="ct-input w-full" placeholder="Tìm email hoặc tên" @keyup.enter="loadUsers(1)" />
        <select v-model="filters.role" class="ct-input">
          <option value="">Role</option>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
        <select v-model="filters.is_active" class="ct-input">
          <option value="">Trạng thái</option>
          <option value="true">Active</option>
          <option value="false">Locked</option>
        </select>
        <select v-model="filters.leaderboard_hidden" class="ct-input">
          <option value="">Leaderboard</option>
          <option value="true">Đã ẩn</option>
          <option value="false">Đang hiện</option>
        </select>
        <select v-model="filters.sort" class="ct-input">
          <option value="created_desc">Mới nhất</option>
          <option value="xp_desc">XP cao</option>
          <option value="streak_desc">Streak cao</option>
          <option value="created_asc">Cũ nhất</option>
        </select>
      </div>
      <div class="mt-3 flex gap-2">
        <button class="ct-btn ct-btn-accent" @click="loadUsers(1)">Lọc</button>
        <button class="ct-btn" @click="resetFilters">Xóa lọc</button>
      </div>
    </section>

    <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>

    <section class="rounded-lg border border-[var(--border)] bg-white">
      <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
        <div class="text-sm font-semibold text-[var(--ink)]">{{ data.total }} người dùng</div>
        <div v-if="loading" class="text-xs text-[var(--ink3)]">Đang tải...</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
            <tr>
              <th class="px-4 py-2">User</th>
              <th class="px-4 py-2">Role</th>
              <th class="px-4 py-2">Trạng thái</th>
              <th class="px-4 py-2">XP</th>
              <th class="px-4 py-2">Streak</th>
              <th class="px-4 py-2">Leaderboard</th>
              <th class="px-4 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in data.items" :key="user.id" class="border-t border-[var(--border)]">
              <td class="px-4 py-3">
                <RouterLink :to="`/admin/users/${user.id}`" class="font-semibold text-[var(--ink)] hover:text-[#059669]">{{ user.full_name || user.email }}</RouterLink>
                <div class="text-xs text-[var(--ink3)]">{{ user.email }}</div>
              </td>
              <td class="px-4 py-3">
                <span class="rounded bg-[var(--bg)] px-2 py-1 text-xs font-semibold">{{ user.role }}</span>
              </td>
              <td class="px-4 py-3">
                <span :class="user.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'" class="rounded px-2 py-1 text-xs font-semibold">
                  {{ user.is_active ? 'Active' : 'Locked' }}
                </span>
              </td>
              <td class="px-4 py-3 font-semibold">{{ user.xp }}</td>
              <td class="px-4 py-3">{{ user.streak }} ngày</td>
              <td class="px-4 py-3">
                <span :class="user.is_leaderboard_hidden ? 'bg-amber-50 text-amber-700' : 'bg-[var(--bg)] text-[var(--ink2)]'" class="rounded px-2 py-1 text-xs font-semibold">
                  {{ user.is_leaderboard_hidden ? 'Ẩn' : 'Hiện' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-2">
                  <button class="ct-btn btn-sm" @click="toggleLock(user)">{{ user.is_active ? 'Khóa' : 'Mở' }}</button>
                  <button class="ct-btn btn-sm" @click="toggleLeaderboard(user)">{{ user.is_leaderboard_hidden ? 'Hiện BXH' : 'Ẩn BXH' }}</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !data.items.length">
              <td colspan="7" class="px-4 py-8 text-center text-sm text-[var(--ink3)]">Không tìm thấy người dùng.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="flex items-center justify-between border-t border-[var(--border)] px-4 py-3 text-sm">
        <button class="ct-btn btn-sm" :disabled="data.page <= 1" @click="loadUsers(data.page - 1)">Trước</button>
        <span class="text-[var(--ink3)]">Trang {{ data.page }} / {{ data.total_pages }}</span>
        <button class="ct-btn btn-sm" :disabled="data.page >= data.total_pages" @click="loadUsers(data.page + 1)">Sau</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const loading = ref(false)
const error = ref('')
const data = reactive({ items: [], total: 0, page: 1, page_size: 20, total_pages: 1 })
const filters = reactive({
  q: '',
  role: '',
  is_active: '',
  leaderboard_hidden: '',
  sort: 'created_desc',
})

function params(page) {
  const p = { page, page_size: data.page_size, sort: filters.sort }
  for (const key of ['q', 'role', 'is_active', 'leaderboard_hidden']) {
    if (filters[key] !== '') p[key] = filters[key]
  }
  return p
}

async function loadUsers(page = 1) {
  loading.value = true
  error.value = ''
  try {
    Object.assign(data, await adminService.listUsers(params(page)))
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không tải được danh sách user.'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, { q: '', role: '', is_active: '', leaderboard_hidden: '', sort: 'created_desc' })
  loadUsers(1)
}

async function toggleLock(user) {
  const reason = user.is_active ? window.prompt('Lý do khóa tài khoản?', user.lock_reason || '') : ''
  if (user.is_active && reason === null) return
  await adminService.updateUserStatus(user.id, { is_active: !user.is_active, lock_reason: reason })
  await loadUsers(data.page)
}

async function toggleLeaderboard(user) {
  const reason = !user.is_leaderboard_hidden ? window.prompt('Lý do ẩn khỏi bảng xếp hạng?', user.leaderboard_flag_reason || '') : ''
  if (!user.is_leaderboard_hidden && reason === null) return
  await adminService.updateLeaderboard(user.id, { is_leaderboard_hidden: !user.is_leaderboard_hidden, reason })
  await loadUsers(data.page)
}

onMounted(() => loadUsers())
</script>
