import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fetchNotifications,
  getNotificationSettings,
  markAllNotificationsRead,
  markNotificationRead,
  updateNotificationSettings,
} from '@/services/notificationService.js'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const settings = ref(null)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const data = await fetchNotifications()
      items.value = data.items || []
      unreadCount.value = data.unread_count ?? 0
    } catch {
      items.value = []
      unreadCount.value = 0
    } finally {
      loading.value = false
    }
  }

  async function loadSettings() {
    try {
      settings.value = await getNotificationSettings()
    } catch {
      settings.value = null
    }
  }

  async function markRead(id) {
    await markNotificationRead(id)
    const row = items.value.find((n) => n.id === id)
    if (row && !row.is_read) {
      row.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  async function markAllRead() {
    await markAllNotificationsRead()
    items.value.forEach((n) => { n.is_read = true })
    unreadCount.value = 0
  }

  async function saveSettings(body) {
    settings.value = await updateNotificationSettings(body)
    return settings.value
  }

  return {
    items,
    unreadCount,
    settings,
    loading,
    load,
    loadSettings,
    markRead,
    markAllRead,
    saveSettings,
  }
})
