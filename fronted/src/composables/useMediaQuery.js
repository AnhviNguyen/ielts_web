import { ref, onMounted, onUnmounted } from 'vue'

export function useMediaQuery(query) {
  const matches = ref(
    typeof window !== 'undefined' ? window.matchMedia(query).matches : false,
  )
  let mql = null

  function update() {
    matches.value = mql?.matches ?? false
  }

  onMounted(() => {
    mql = window.matchMedia(query)
    mql.addEventListener('change', update)
    update()
  })

  onUnmounted(() => {
    mql?.removeEventListener('change', update)
  })

  return matches
}
