<!-- src/components/NavBar.vue — Top navigation bar -->
<template>
  <nav id="main-navbar" class="fixed inset-x-0 top-0 z-[100] h-16 border-b border-[var(--color-border)] bg-[rgba(15,17,23,0.85)] backdrop-blur-2xl">
    <div class="mx-auto flex h-full max-w-[1200px] items-center gap-4 px-6">
      <RouterLink to="/dashboard" class="flex shrink-0 items-center gap-2 text-xl font-extrabold text-[var(--color-text)] no-underline">
        <span class="text-[1.4rem]">⚡</span>
        <span class="bg-[var(--grad-primary)] bg-clip-text text-transparent">QuizMaster</span>
      </RouterLink>

      <div
        class="flex flex-1 items-center gap-1 max-md:fixed max-md:inset-x-0 max-md:top-16 max-md:flex-col max-md:border-b max-md:border-[var(--color-border)] max-md:bg-[var(--color-surface)] max-md:p-4 max-md:transition-all max-md:duration-250"
        :class="menuOpen
          ? 'max-md:translate-y-0 max-md:opacity-100 max-md:pointer-events-auto'
          : 'max-md:-translate-y-full max-md:opacity-0 max-md:pointer-events-none'"
      >
        <RouterLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="flex items-center gap-1.5 rounded-[var(--radius-md)] px-3.5 py-2 text-sm font-medium text-[var(--color-text-muted)] no-underline transition-all hover:bg-[rgba(124,106,247,0.12)] hover:text-[var(--color-primary)] [&.router-link-active]:bg-[rgba(124,106,247,0.12)] [&.router-link-active]:text-[var(--color-primary)]"
          @click="menuOpen = false"
        >
          <span>{{ link.icon }}</span> {{ link.label }}
        </RouterLink>
      </div>

      <div class="relative ml-auto">
        <div
          id="user-avatar-btn"
          class="flex cursor-pointer items-center gap-2 rounded-[var(--radius-md)] px-3 py-1.5 transition-colors hover:bg-[var(--color-surface-2)]"
          @click="dropdownOpen = !dropdownOpen"
        >
          <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--grad-primary)] text-sm font-bold text-white">{{ initials }}</div>
          <span class="text-sm font-medium max-md:hidden">{{ authStore.userName }}</span>
          <span class="text-xs text-[var(--color-text-muted)] transition-transform" :class="{ 'rotate-180': dropdownOpen }">▾</span>
        </div>

        <Transition name="dropdown">
          <div
            v-if="dropdownOpen"
            v-click-outside="closeDropdown"
            class="absolute right-0 top-[calc(100%+8px)] z-[200] min-w-[180px] overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-lg)]"
          >
            <RouterLink to="/profile" class="block w-full px-4 py-2.5 text-left text-sm font-medium text-[var(--color-text)] no-underline transition-colors hover:bg-[var(--color-surface-2)]" @click="dropdownOpen = false">
              ⚙️ &nbsp;Settings
            </RouterLink>
            <div class="h-px bg-[var(--color-border)]"></div>
            <button id="logout-btn" type="button" class="block w-full cursor-pointer border-0 bg-transparent px-4 py-2.5 text-left text-sm font-medium text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-[var(--color-danger)]" @click="handleLogout">
              🚪 &nbsp;Logout
            </button>
          </div>
        </Transition>
      </div>

      <button id="hamburger-btn" type="button" class="hidden cursor-pointer flex-col gap-1.5 border-0 bg-transparent p-1 max-md:flex" @click="menuOpen = !menuOpen">
        <span class="block h-0.5 w-[22px] rounded-sm bg-[var(--color-text)] transition-all"></span>
        <span class="block h-0.5 w-[22px] rounded-sm bg-[var(--color-text)] transition-all"></span>
        <span class="block h-0.5 w-[22px] rounded-sm bg-[var(--color-text)] transition-all"></span>
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const authStore = useAuthStore()
const router = useRouter()
const dropdownOpen = ref(false)
const menuOpen = ref(false)

const navLinks = [
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/history', icon: '📋', label: 'History' },
  { to: '/profile', icon: '👤', label: 'Profile' },
]

const initials = computed(() => {
  const name = authStore.profile?.full_name || authStore.profile?.email || 'U'
  return name.charAt(0).toUpperCase()
})

function closeDropdown() { dropdownOpen.value = false }

async function handleLogout() {
  dropdownOpen.value = false
  authStore.logout()
  await router.push('/login')
}

const vClickOutside = {
  mounted(el, binding) {
    el._clickHandler = (e) => { if (!el.contains(e.target)) binding.value() }
    document.addEventListener('click', el._clickHandler)
  },
  unmounted(el) { document.removeEventListener('click', el._clickHandler) },
}
</script>
