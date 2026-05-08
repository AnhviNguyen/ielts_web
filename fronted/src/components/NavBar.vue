<!-- src/components/NavBar.vue — Top navigation bar -->
<template>
  <nav class="navbar" id="main-navbar">
    <div class="nav-inner">
      <!-- Logo -->
      <RouterLink to="/dashboard" class="nav-logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">QuizMaster</span>
      </RouterLink>

      <!-- Links -->
      <div class="nav-links" :class="{ open: menuOpen }">
        <RouterLink to="/dashboard" class="nav-link" @click="menuOpen = false">
          <span class="nav-icon">📊</span> Dashboard
        </RouterLink>
        <RouterLink to="/history" class="nav-link" @click="menuOpen = false">
          <span class="nav-icon">📋</span> History
        </RouterLink>
        <RouterLink to="/profile" class="nav-link" @click="menuOpen = false">
          <span class="nav-icon">👤</span> Profile
        </RouterLink>
      </div>

      <!-- User menu -->
      <div class="nav-user">
        <div class="avatar-btn" @click="dropdownOpen = !dropdownOpen" id="user-avatar-btn">
          <div class="avatar">{{ initials }}</div>
          <span class="username-text">{{ authStore.userName }}</span>
          <span class="chevron" :class="{ rotated: dropdownOpen }">▾</span>
        </div>

        <Transition name="dropdown">
          <div v-if="dropdownOpen" class="dropdown" v-click-outside="closeDropdown">
            <RouterLink to="/profile" class="dropdown-item" @click="dropdownOpen = false">
              ⚙️ &nbsp;Settings
            </RouterLink>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item danger" @click="handleLogout" id="logout-btn">
              🚪 &nbsp;Logout
            </button>
          </div>
        </Transition>
      </div>

      <!-- Mobile hamburger -->
      <button class="hamburger" @click="menuOpen = !menuOpen" id="hamburger-btn">
        <span></span><span></span><span></span>
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const authStore  = useAuthStore()
const router     = useRouter()
const dropdownOpen = ref(false)
const menuOpen   = ref(false)

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

// v-click-outside directive
const vClickOutside = {
  mounted(el, binding) {
    el._clickHandler = (e) => { if (!el.contains(e.target)) binding.value() }
    document.addEventListener('click', el._clickHandler)
  },
  unmounted(el) { document.removeEventListener('click', el._clickHandler) },
}
</script>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 64px;
  background: rgba(15,17,23,0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border);
}
.nav-inner {
  max-width: 1200px; margin: 0 auto;
  height: 100%;
  display: flex; align-items: center; gap: 1rem;
  padding: 0 1.5rem;
}

/* Logo */
.nav-logo {
  display: flex; align-items: center; gap: 0.5rem;
  text-decoration: none; font-weight: 800; font-size: 1.2rem;
  color: var(--color-text);
  flex-shrink: 0;
}
.logo-icon { font-size: 1.4rem; }
.logo-text { background: var(--grad-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* Links */
.nav-links {
  display: flex; align-items: center; gap: 0.25rem; flex: 1;
}
.nav-link {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.45rem 0.9rem;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: 0.9rem; font-weight: 500;
  text-decoration: none;
  transition: all var(--transition-fast);
}
.nav-link:hover, .nav-link.router-link-active {
  background: rgba(124,106,247,0.12);
  color: var(--color-primary);
}

/* User */
.nav-user { margin-left: auto; position: relative; }
.avatar-btn {
  display: flex; align-items: center; gap: 0.5rem;
  cursor: pointer; padding: 0.35rem 0.75rem;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}
.avatar-btn:hover { background: var(--color-surface-2); }
.avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--grad-primary);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.85rem; color: #fff;
  flex-shrink: 0;
}
.username-text { font-size: 0.9rem; font-weight: 500; }
.chevron { font-size: 0.75rem; transition: transform var(--transition-fast); color: var(--color-text-muted); }
.chevron.rotated { transform: rotate(180deg); }

/* Dropdown */
.dropdown {
  position: absolute; top: calc(100% + 8px); right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  min-width: 180px;
  box-shadow: var(--shadow-lg);
  overflow: hidden; z-index: 200;
}
.dropdown-item {
  display: block; width: 100%;
  padding: 0.65rem 1rem;
  font-size: 0.9rem; font-weight: 500;
  color: var(--color-text); text-decoration: none;
  background: none; border: none; cursor: pointer; text-align: left;
  transition: background var(--transition-fast);
}
.dropdown-item:hover { background: var(--color-surface-2); }
.dropdown-item.danger:hover { color: var(--color-danger); }
.dropdown-divider { height: 1px; background: var(--color-border); }

/* Transitions */
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px); }

/* Hamburger */
.hamburger { display: none; flex-direction: column; gap: 5px; background: none; border: none; cursor: pointer; padding: 4px; }
.hamburger span { display: block; width: 22px; height: 2px; background: var(--color-text); border-radius: 2px; transition: all 0.2s; }

@media (max-width: 768px) {
  .hamburger { display: flex; }
  .nav-links {
    position: fixed; top: 64px; left: 0; right: 0;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    flex-direction: column; padding: 1rem;
    transform: translateY(-100%); opacity: 0; pointer-events: none;
    transition: all 0.25s ease;
  }
  .nav-links.open { transform: translateY(0); opacity: 1; pointer-events: auto; }
  .username-text { display: none; }
}
</style>
