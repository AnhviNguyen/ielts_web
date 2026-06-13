import { onUnmounted, ref, watch } from 'vue'

/**
 * Tự động gọi syncFn khi source thay đổi (debounce).
 * pause() / resume() để tránh vòng lặp khi load từ server.
 */
export function useAutoJsonSync(source, syncFn, { debounceMs = 450 } = {}) {
  const jsonLive = ref(false)
  const jsonSyncing = ref(false)
  let pauseDepth = 0
  let timer = null

  function pause() {
    pauseDepth += 1
  }

  function resume() {
    pauseDepth = Math.max(0, pauseDepth - 1)
  }

  function runSync() {
    if (pauseDepth > 0) return
    jsonSyncing.value = true
    try {
      syncFn()
      jsonLive.value = true
    } catch {
      jsonLive.value = false
    } finally {
      jsonSyncing.value = false
    }
  }

  function scheduleSync() {
    if (pauseDepth > 0) return
    clearTimeout(timer)
    timer = setTimeout(runSync, debounceMs)
  }

  const stop = watch(source, scheduleSync, { deep: true })

  onUnmounted(() => {
    stop()
    clearTimeout(timer)
  })

  return { jsonLive, jsonSyncing, pause, resume, runSync }
}
