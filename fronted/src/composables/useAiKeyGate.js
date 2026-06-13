import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/services/authService.js'

/** True when user configured a personal OpenRouter API key. */
export function isPersonalAiKeyConfigured(settings) {
  return Boolean(settings?.has_key && settings.provider === 'openrouter')
}

export function useAiKeyGate() {
  const router = useRouter()
  const checking = ref(false)
  const showGate = ref(false)
  const hasAiKey = ref(false)

  async function checkAiKey() {
    checking.value = true
    try {
      const data = await authService.getAiSettings()
      hasAiKey.value = isPersonalAiKeyConfigured(data)
      showGate.value = !hasAiKey.value
    } catch {
      hasAiKey.value = false
      showGate.value = true
    } finally {
      checking.value = false
    }
    return hasAiKey.value
  }

  function requireAiKey() {
    if (hasAiKey.value) return true
    showGate.value = true
    return false
  }

  function goToProfile() {
    router.push('/profile')
  }

  function goBack() {
    if (window.history.length > 1) router.back()
    else router.push('/dashboard')
  }

  return { checking, showGate, hasAiKey, checkAiKey, requireAiKey, goToProfile, goBack }
}
