<template>
  <header class="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between border-b border-[var(--border)] bg-white px-6">
    <div class="text-[15px] font-semibold text-[var(--ink)]">{{ pageTitle }}</div>

    <div class="flex items-center gap-2">
      <!-- Streak -->
      <div class="hidden items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--bg)] px-2.5 py-1 text-[12px] font-semibold text-[var(--ink2)] sm:flex">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2c0 0-5 6-5 10a5 5 0 0 0 10 0c0-4-5-10-5-10z"/><path d="M12 12c0 0-2 2.5-2 4a2 2 0 0 0 4 0c0-1.5-2-4-2-4z" fill="#f97316"/></svg>
        {{ streak }}
      </div>

      <!-- XP -->
      <div class="hidden items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--bg)] px-2.5 py-1 text-[12px] font-semibold text-[var(--purple)] sm:flex">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        {{ xp.toLocaleString('vi-VN') }} XP
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        {{ xp.toLocaleString('vi-VN') }} XP
      </div>

      <!-- Avatar / Profile -->
      <RouterLink to="/profile" class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--purple)] text-[12px] font-bold text-white hover:bg-[var(--purple-d)] transition-colors">
        {{ initials }}
      </RouterLink>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const auth  = useAuthStore()
const route = useRoute()

const PAGE_TITLES = {
  '/':           'Mock Tests',
  '/dashboard':  'Dashboard',
  '/reading':    'Reading',
  '/listening':  'Listening',
  '/writing':    'Writing',
  '/speaking':   'Speaking',
  '/vocabulary': 'Từ vựng',
  '/history':    'Lịch sử',
  '/profile':    'Hồ sơ',
  '/guide':      'Hướng dẫn',
}
const pageTitle = computed(() => PAGE_TITLES[route.path] ?? 'LinguaIELTS')
const streak    = computed(() => auth.profile?.streak ?? 0)
const xp        = computed(() => auth.profile?.xp ?? 0)
const initials  = computed(() => {
  const n = auth.profile?.full_name || auth.profile?.email || 'U'
  return n.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})
</script>
