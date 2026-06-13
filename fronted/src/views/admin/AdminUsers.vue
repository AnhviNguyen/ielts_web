<template>
  <div class="admin-page mx-auto max-w-7xl space-y-4" :style="pageStyle">
    <AdminPageHeader module="users" title="Quản lý người dùng" subtitle="CRUD tài khoản: tạo, xem, sửa quyền, khóa/mở, reset XP và quản trị BXH." />

    <AdminCrudBar
      module="users"
      :can-archive="false"
      :show-save="false"
      :saving="creating"
      @create="openCreateModal"
      @refresh="loadUsers(data.page)"
    >
      <span class="ml-auto text-xs text-[var(--ink3)]">{{ data.total }} người dùng</span>
    </AdminCrudBar>

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
    <div v-if="success" class="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">{{ success }}</div>

    <section class="rounded-lg border border-[var(--border)] bg-white">
      <div v-if="loading" class="border-b border-[var(--border)] px-4 py-3 text-xs text-[var(--ink3)]">Đang tải...</div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[1080px] text-left text-sm">
          <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
            <tr>
              <th class="px-4 py-2">User</th>
              <th class="px-4 py-2">Role</th>
              <th class="px-4 py-2">Trạng thái</th>
              <th class="px-4 py-2">XP</th>
              <th class="px-4 py-2">Streak</th>
              <th class="px-4 py-2">Leaderboard</th>
              <th class="px-4 py-2 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in data.items" :key="user.id" class="border-t border-[var(--border)] hover:bg-emerald-50/20">
              <td class="px-4 py-3">
                <RouterLink :to="`/admin/users/${user.id}`" class="font-semibold text-[var(--ink)] hover:text-emerald-600">{{ user.full_name || user.email }}</RouterLink>
                <div class="text-xs text-[var(--ink3)]">{{ user.email }}</div>
              </td>
              <td class="px-4 py-3">
                <span class="rounded px-2 py-1 text-xs font-semibold" :class="user.role === 'admin' ? 'bg-violet-50 text-violet-700' : 'bg-[var(--bg)] text-[var(--ink2)]'">{{ user.role }}</span>
              </td>
              <td class="px-4 py-3">
                <span :class="user.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'" class="rounded px-2 py-1 text-xs font-semibold">
                  {{ user.is_active ? 'Active' : 'Locked' }}
                </span>
              </td>
              <td class="px-4 py-3 font-semibold tabular-nums">{{ user.xp }}</td>
              <td class="px-4 py-3 tabular-nums">{{ user.streak }} ngày</td>
              <td class="px-4 py-3">
                <span :class="user.is_leaderboard_hidden ? 'bg-amber-50 text-amber-700' : 'bg-[var(--bg)] text-[var(--ink2)]'" class="rounded px-2 py-1 text-xs font-semibold">
                  {{ user.is_leaderboard_hidden ? 'Ẩn' : 'Hiện' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap justify-end gap-1.5">
                  <RouterLink :to="`/admin/users/${user.id}`" class="ct-btn btn-sm">Xem</RouterLink>
                  <button class="ct-btn btn-sm" @click="toggleRole(user)">{{ user.role === 'admin' ? 'Hạ user' : 'Admin' }}</button>
                  <button class="ct-btn btn-sm" @click="toggleLock(user)">{{ user.is_active ? 'Khóa' : 'Mở' }}</button>
                  <button class="ct-btn btn-sm" @click="resetStats(user)">Reset XP</button>
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

    <!-- Create user modal -->
    <div v-if="showCreate" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @click.self="showCreate = false">
      <div class="w-full max-w-md rounded-xl border border-[var(--border)] bg-white p-5 shadow-xl">
        <h2 class="text-lg font-bold text-[var(--ink)]">Tạo người dùng mới</h2>
        <p class="mt-1 text-xs text-[var(--ink3)]">Tài khoản được kích hoạt và xác minh ngay (không cần OTP).</p>
        <form class="mt-4 space-y-3" @submit.prevent="submitCreate">
          <label class="block text-xs font-semibold text-[var(--ink3)]">
            Email
            <input v-model.trim="createForm.email" type="email" required class="ct-input mt-1 w-full" />
          </label>
          <label class="block text-xs font-semibold text-[var(--ink3)]">
            Họ tên
            <input v-model.trim="createForm.full_name" class="ct-input mt-1 w-full" />
          </label>
          <label class="block text-xs font-semibold text-[var(--ink3)]">
            Mật khẩu (≥10 ký tự)
            <input v-model="createForm.password" type="password" required minlength="10" class="ct-input mt-1 w-full" />
          </label>
          <label class="block text-xs font-semibold text-[var(--ink3)]">
            Role
            <select v-model="createForm.role" class="ct-input mt-1 w-full">
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </label>
          <div v-if="createError" class="text-sm text-rose-600">{{ createError }}</div>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="ct-btn" @click="showCreate = false">Hủy</button>
            <button type="submit" class="ct-btn ct-btn-accent" :disabled="creating">{{ creating ? 'Đang tạo...' : 'Tạo user' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { adminService } from '@/services/adminService.js'
import AdminCrudBar from '@/components/admin/AdminCrudBar.vue'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import { moduleStyle } from '@/components/admin/adminModules.js'

const pageStyle = moduleStyle('users')

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const error = ref('')
const success = ref('')
const showCreate = ref(false)
const createError = ref('')
const data = reactive({ items: [], total: 0, page: 1, page_size: 20, total_pages: 1 })
const filters = reactive({
  q: '',
  role: '',
  is_active: '',
  leaderboard_hidden: '',
  sort: 'created_desc',
})
const createForm = reactive({
  email: '',
  full_name: '',
  password: '',
  role: 'user',
})

function openCreateModal() {
  createError.value = ''
  Object.assign(createForm, { email: '', full_name: '', password: '', role: 'user' })
  showCreate.value = true
}

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

async function submitCreate() {
  creating.value = true
  createError.value = ''
  try {
    const created = await adminService.createUser({
      email: createForm.email,
      full_name: createForm.full_name || null,
      password: createForm.password,
      role: createForm.role,
      is_verified: true,
    })
    showCreate.value = false
    success.value = `Đã tạo user ${created.email}`
    await loadUsers(1)
    router.push(`/admin/users/${created.id}`)
  } catch (err) {
    createError.value = err.response?.data?.detail || 'Không tạo được user.'
  } finally {
    creating.value = false
  }
}

async function toggleRole(user) {
  const next = user.role === 'admin' ? 'user' : 'admin'
  if (!window.confirm(next === 'admin' ? `Cấp quyền admin cho ${user.email}?` : `Thu hồi quyền admin của ${user.email}?`)) return
  await adminService.updateUserRole(user.id, { role: next })
  success.value = `Đã cập nhật role → ${next}`
  await loadUsers(data.page)
}

async function toggleLock(user) {
  const reason = user.is_active ? window.prompt('Lý do khóa tài khoản?', user.lock_reason || '') : ''
  if (user.is_active && reason === null) return
  await adminService.updateUserStatus(user.id, { is_active: !user.is_active, lock_reason: reason })
  await loadUsers(data.page)
}

async function resetStats(user) {
  if (!window.confirm(`Reset XP và streak của ${user.email}?`)) return
  await adminService.resetXpStreak(user.id, { reset_xp: true, reset_streak: true })
  success.value = 'Đã reset XP/streak.'
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
