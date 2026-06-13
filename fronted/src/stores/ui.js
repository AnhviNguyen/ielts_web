import { defineStore } from 'pinia'
import { ref } from 'vue'

const THEME_KEY = 'lingua-theme'

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem(THEME_KEY, theme)
}

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const sidebarMobileOpen = ref(false)
  const isLargeScreen = ref(
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : true,
  )
  const theme = ref(localStorage.getItem(THEME_KEY) || 'dark')

  function updateScreenSize() {
    isLargeScreen.value = window.innerWidth >= 1024
    if (isLargeScreen.value) sidebarMobileOpen.value = false
  }

  function openMobileSidebar() {
    sidebarMobileOpen.value = true
  }

  function closeMobileSidebar() {
    sidebarMobileOpen.value = false
  }

  function toggleMobileSidebar() {
    sidebarMobileOpen.value = !sidebarMobileOpen.value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function initResponsive() {
    updateScreenSize()
    window.addEventListener('resize', updateScreenSize)
  }

  function setTheme(next) {
    const value = next === 'light' ? 'light' : 'dark'
    theme.value = value
    applyTheme(value)
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  function initTheme() {
    applyTheme(theme.value)
  }

  return {
    sidebarCollapsed,
    sidebarMobileOpen,
    isLargeScreen,
    theme,
    toggleSidebar,
    openMobileSidebar,
    closeMobileSidebar,
    toggleMobileSidebar,
    initResponsive,
    setTheme,
    toggleTheme,
    initTheme,
  }
})
