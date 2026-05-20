<template>
  <header class="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between border-b border-[var(--border)] bg-white px-6">
    <div class="text-[15px] font-semibold text-[var(--ink)]">{{ pageTitle }}</div>

    <div class="flex items-center gap-2">
      <!-- Streak warning toast -->
      <Transition name="toast">
        <div
          v-if="showStreakWarning"
          class="mr-1 flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-[12px] font-medium text-amber-700"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          Streak có thể bị mất! Hãy làm bài hôm nay.
          <button @click="showStreakWarning = false" class="ml-1 opacity-60 hover:opacity-100">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </Transition>

      <!-- Streak badge -->
      <div class="hidden items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--bg)] px-2.5 py-1 text-[12px] font-semibold text-[var(--ink2)] sm:flex">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2c0 0-5 6-5 10a5 5 0 0 0 10 0c0-4-5-10-5-10z"/>
          <path d="M12 12c0 0-2 2.5-2 4a2 2 0 0 0 4 0c0-1.5-2-4-2-4z" fill="#f97316"/>
        </svg>
        {{ streak }}
      </div>

      <!-- XP badge -->
      <div class="hidden items-center gap-1.5 rounded-md border border-[#34d399] bg-[#f0fdf4] px-2.5 py-1 text-[12px] font-semibold text-[#15803d] sm:flex">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        {{ xp.toLocaleString('vi-VN') }} XP
      </div>

      <!-- Avatar dropdown -->
      <div class="relative" ref="dropdownRef">
        <button
          @click="toggleDropdown"
          class="flex h-8 w-8 items-center justify-center rounded-full overflow-hidden hover:ring-2 hover:ring-[#34d399] hover:ring-offset-1 transition-all"
        >
          <img
            :src="avatarSrc"
            :alt="initials"
            class="h-full w-full object-cover"
          />
        </button>

        <!-- Dropdown panel -->
        <Transition name="dropdown">
          <div
            v-if="dropdownOpen"
            class="absolute right-0 top-10 z-50 w-64 rounded-2xl border border-[var(--border)] bg-white shadow-xl"
          >
            <!-- User info header -->
            <div class="flex items-center gap-3 border-b border-[var(--border)] px-4 py-3.5">
              <img
                :src="avatarSrc"
                :alt="initials"
                class="h-10 w-10 rounded-full object-cover flex-shrink-0"
              />
              <div class="min-w-0">
                <div class="truncate text-[13px] font-semibold text-[var(--ink)]">{{ userName }}</div>
                <div class="truncate text-[11px] text-[var(--ink3)]">{{ auth.profile?.email }}</div>
              </div>
            </div>

            <!-- Stats row -->
            <div class="flex items-center justify-around border-b border-[var(--border)] px-3 py-2.5">
              <div class="flex flex-col items-center gap-0.5">
                <div class="flex items-center gap-1 text-[13px] font-bold text-[var(--ink)]">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2.5"><path d="M12 2c0 0-5 6-5 10a5 5 0 0 0 10 0c0-4-5-10-5-10z"/></svg>
                  {{ streak }}
                </div>
                <div class="text-[10px] text-[var(--ink3)]">Streak</div>
              </div>
              <div class="h-6 w-px bg-[var(--border)]"></div>
              <div class="flex flex-col items-center gap-0.5">
                <div class="flex items-center gap-1 text-[13px] font-bold text-[#059669]">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                  {{ xp.toLocaleString('vi-VN') }}
                </div>
                <div class="text-[10px] text-[var(--ink3)]">XP</div>
              </div>
              <div class="h-6 w-px bg-[var(--border)]"></div>
              <div class="flex flex-col items-center gap-0.5">
                <div class="text-[13px] font-bold text-[var(--ink)]">{{ auth.profile?.target_band ?? '—' }}</div>
                <div class="text-[10px] text-[var(--ink3)]">Target</div>
              </div>
            </div>

            <!-- Links -->
            <div class="py-1.5">
              <RouterLink
                to="/profile"
                class="flex items-center gap-2.5 px-4 py-2 text-[13px] text-[var(--ink2)] hover:bg-[var(--bg)] hover:text-[var(--ink)] transition-colors"
                @click="dropdownOpen = false"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
                Hồ sơ cá nhân
              </RouterLink>
              <RouterLink
                to="/leaderboard"
                class="flex items-center gap-2.5 px-4 py-2 text-[13px] text-[var(--ink2)] hover:bg-[var(--bg)] hover:text-[var(--ink)] transition-colors"
                @click="dropdownOpen = false"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 21H5a2 2 0 0 1-2-2v-5l3-7h12l3 7v5a2 2 0 0 1-2 2h-3m-8 0v-4a4 4 0 0 1 8 0v4m-8 0h8"/></svg>
                Bảng xếp hạng
              </RouterLink>
              <RouterLink
                to="/history"
                class="flex items-center gap-2.5 px-4 py-2 text-[13px] text-[var(--ink2)] hover:bg-[var(--bg)] hover:text-[var(--ink)] transition-colors"
                @click="dropdownOpen = false"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Lịch sử
              </RouterLink>
            </div>

            <!-- Divider + Logout -->
            <div class="border-t border-[var(--border)] py-1.5">
              <button
                @click="handleLogout"
                class="flex w-full items-center gap-2.5 px-4 py-2 text-[13px] text-[var(--rose)] hover:bg-[var(--rose-bg)] transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                Đăng xuất
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const auth   = useAuthStore()
const route  = useRoute()
const router = useRouter()

// ── Page title ────────────────────────────────────────────────────
const PAGE_TITLES = {
  '/dashboard':  'Dashboard',
  '/reading':    'Reading',
  '/listening':  'Listening',
  '/writing':    'Writing',
  '/speaking':   'Speaking',
  '/vocabulary': 'Từ vựng',
  '/history':    'Lịch sử',
  '/profile':    'Hồ sơ',
  '/leaderboard': 'Bảng xếp hạng',
}
const pageTitle = computed(() => PAGE_TITLES[route.path] ?? 'LinguaIELTS')

// ── User data ──────────────────────────────────────────────────────
const streak = computed(() => auth.profile?.streak ?? 0)
const xp     = computed(() => auth.profile?.xp ?? 0)
const userName = computed(() => auth.profile?.full_name || auth.profile?.email || 'User')
const initials = computed(() => {
  const n = auth.profile?.full_name || auth.profile?.email || 'U'
  return n.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})
const avatarSrc = computed(() => auth.profile?.avatar_url || '/icon_profile.jpg')

// ── Dropdown ──────────────────────────────────────────────────────
const dropdownOpen = ref(false)
const dropdownRef  = ref(null)

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function closeDropdown(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    dropdownOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', closeDropdown))
onUnmounted(() => document.removeEventListener('click', closeDropdown))

// ── Streak warning ────────────────────────────────────────────────
const showStreakWarning = ref(false)

onMounted(() => {
  // Hiển thị cảnh báo nếu streak > 0 nhưng chưa active hôm nay
  const lastActivity = auth.profile?.last_activity_date
  const today = new Date().toISOString().slice(0, 10)
  if (streak.value > 0 && lastActivity && lastActivity !== today) {
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
    if (lastActivity === yesterday) {
      showStreakWarning.value = true
      setTimeout(() => { showStreakWarning.value = false }, 8000)
    }
  }
})

// ── Actions ───────────────────────────────────────────────────────
function handleLogout() {
  dropdownOpen.value = false
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
</style>
