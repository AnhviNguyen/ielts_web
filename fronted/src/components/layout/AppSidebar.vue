<template>
  <nav
    class="fixed inset-y-0 left-0 z-50 flex flex-col bg-[#111] transition-all duration-200"
    :class="collapsed ? 'w-16' : 'w-[220px]'"
  >
    <!-- Brand -->
    <div class="flex h-14 shrink-0 items-center justify-between border-b border-white/10 px-4">
      <RouterLink v-if="!collapsed" to="/" class="flex items-center gap-2 min-w-0">
        <span class="text-[15px] font-bold text-white tracking-tight">Lingua<span class="text-[#34d399]">IELTS</span></span>
      </RouterLink>
      <button
        @click="toggle"
        class="ml-auto flex h-7 w-7 items-center justify-center rounded text-white/40 hover:bg-white/10 hover:text-white transition-colors"
        :title="collapsed ? 'Mở rộng' : 'Thu nhỏ'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline v-if="collapsed" points="9 18 15 12 9 6"/>
          <polyline v-else points="15 18 9 12 15 6"/>
        </svg>
      </button>
    </div>

    <!-- Nav -->
    <div class="flex-1 overflow-y-auto overflow-x-hidden py-3" :class="collapsed ? 'px-2' : 'px-3'">
      <template v-for="group in navGroups" :key="group.label">
        <p v-if="!collapsed" class="mb-1 mt-4 px-2 text-[9px] font-bold uppercase tracking-widest text-white/25 first:mt-1">{{ group.label }}</p>
        <RouterLink
          v-for="item in group.items" :key="item.to"
          :to="item.to"
          :title="collapsed ? item.label : undefined"
          class="mb-0.5 flex items-center rounded-lg px-2 py-2 text-[13px] font-medium text-white/50 transition-colors hover:bg-white/8 hover:text-white"
          :class="collapsed ? 'justify-center' : 'gap-2.5'"
          active-class="bg-white/10 !text-[#34d399]"
        >
          <span class="flex h-5 w-5 shrink-0 items-center justify-center" v-html="item.icon"></span>
          <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
        </RouterLink>
      </template>
    </div>

    <!-- User -->
    <div class="shrink-0 border-t border-white/10 p-3">
      <RouterLink
        to="/profile"
        class="flex items-center gap-2.5 rounded-lg px-1 py-2 hover:bg-white/8 transition-colors"
        :class="collapsed ? 'justify-center' : ''"
      >
        <!-- Avatar: show user image or default icon_profile.jpg -->
        <div class="relative h-8 w-8 shrink-0">
          <img
            :src="avatarSrc"
            :alt="userName"
            class="h-8 w-8 rounded-full object-cover"
          />
        </div>
        <div v-if="!collapsed" class="min-w-0">
          <div class="truncate text-[12px] font-semibold text-white">{{ userName }}</div>
          <div class="text-[10px] text-white/40">{{ streak }} ngày streak</div>
        </div>
      </RouterLink>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { useUiStore } from '@/stores/ui.js'

const auth = useAuthStore()
const ui   = useUiStore()
const collapsed = computed(() => ui.sidebarCollapsed)
function toggle() { ui.toggleSidebar() }

const userName  = computed(() => auth.profile?.full_name || auth.profile?.email || 'User')
const streak    = computed(() => auth.profile?.streak ?? 0)
const initials  = computed(() => userName.value.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2))
const avatarSrc = computed(() => auth.profile?.avatar_url || '/icon_profile.jpg')

const NAV_ICON = {
  dashboard: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
  reading:   `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  listening: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
  writing:   `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  speaking:  `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
  mock:      `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>`,
  vocab:     `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
  shadowing: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>`,
  history:     `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  leaderboard: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21H5a2 2 0 0 1-2-2v-5l3-7"/><path d="M16 21h3a2 2 0 0 0 2-2v-5l-3-7"/><path d="M9 7h6m-6 0V3h6v4m-6 0L8 21m7-14 1 14"/></svg>`,
  admin: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 4v5c0 5-3 8-7 9-4-1-7-4-7-9V7l7-4z"/><path d="M9 12l2 2 4-4"/></svg>`,
  users: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
}

const navGroups = computed(() => {
  const groups = [
  {
    label: 'Tổng quan',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: NAV_ICON.dashboard },
    ]
  },
  {
    label: 'Luyện tập',
    items: [
      { to: '/reading',   label: 'Reading',   icon: NAV_ICON.reading },
      { to: '/listening', label: 'Listening', icon: NAV_ICON.listening },
      { to: '/writing',   label: 'Writing',   icon: NAV_ICON.writing },
      { to: '/speaking',  label: 'Speaking',  icon: NAV_ICON.speaking },
      { to: '/full-exam', label: 'Full Mock', icon: NAV_ICON.mock },
      { to: '/shadowing', label: 'Shadowing', icon: NAV_ICON.shadowing },
    ]
  },
  {
    label: 'Học tập',
    items: [
      { to: '/vocabulary',  label: 'Từ vựng',         icon: NAV_ICON.vocab },
      { to: '/history',     label: 'Lịch sử',          icon: NAV_ICON.history },
      { to: '/leaderboard', label: 'Bảng xếp hạng',   icon: NAV_ICON.leaderboard },
    ]
  },
  ]
  if (auth.profile?.role === 'admin') {
    groups.push({
      label: 'Admin',
      items: [
        { to: '/admin', label: 'Tổng quan admin', icon: NAV_ICON.admin },
        { to: '/admin/users', label: 'Người dùng', icon: NAV_ICON.users },
        { to: '/admin/leaderboard', label: 'Quản trị BXH', icon: NAV_ICON.leaderboard },
        { to: '/admin/system-vocab', label: 'System vocab', icon: NAV_ICON.vocab },
        { to: '/admin/content/writing', label: 'Writing CMS', icon: NAV_ICON.writing },
        { to: '/admin/content/speaking', label: 'Speaking CMS', icon: NAV_ICON.speaking },
        { to: '/admin/content/mock-tests', label: 'Mock CMS', icon: NAV_ICON.mock },
      ],
    })
  }
  return groups
})
</script>
