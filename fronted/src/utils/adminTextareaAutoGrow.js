const SELECTOR = '.admin-page textarea.ct-input'

export function growTextarea(el) {
  if (!el || el.tagName !== 'TEXTAREA') return
  const min = Number.parseFloat(getComputedStyle(el).minHeight) || 52
  el.style.height = 'auto'
  el.style.height = `${Math.max(el.scrollHeight, min)}px`
}

export function bindTextarea(el) {
  if (!el?.matches?.(SELECTOR) || el.dataset.autoGrowBound) return
  el.dataset.autoGrowBound = '1'
  el.style.resize = 'none'
  el.style.overflow = 'hidden'
  growTextarea(el)
}

export function scanAdminTextareas() {
  document.querySelectorAll(SELECTOR).forEach((el) => {
    bindTextarea(el)
    growTextarea(el)
  })
}

let scanTimer = null

function scheduleScan() {
  clearTimeout(scanTimer)
  scanTimer = setTimeout(scanAdminTextareas, 40)
}

export function setupAdminTextareaAutoGrow(router) {
  document.addEventListener('input', (event) => {
    if (event.target?.matches?.(SELECTOR)) growTextarea(event.target)
  })

  document.addEventListener(
    'click',
    (event) => {
      if (event.target?.closest?.('.admin-page')) scheduleScan()
    },
    true,
  )

  router.afterEach((to) => {
    if (!to.path.startsWith('/admin')) return
    requestAnimationFrame(scanAdminTextareas)
    scheduleScan()
    setTimeout(scanAdminTextareas, 250)
  })
}
