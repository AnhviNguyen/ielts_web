/** DOM helpers for spotlight page tours. */

export function waitForElement(selector, timeout = 5000, interval = 120) {
  return new Promise((resolve) => {
    const started = Date.now()

    const tick = () => {
      const el = document.querySelector(selector)
      if (el) {
        const { width, height } = el.getBoundingClientRect()
        if (width > 0 || height > 0) {
          resolve(el)
          return
        }
      }
      if (Date.now() - started >= timeout) {
        resolve(el || null)
        return
      }
      setTimeout(tick, interval)
    }

    tick()
  })
}

export function padRect(rect, padding = 8) {
  return {
    top: rect.top - padding,
    left: rect.left - padding,
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
  }
}

export function computeTooltipPosition(highlight, tooltipWidth, tooltipHeight, preferred = 'bottom') {
  const gap = 14
  const margin = 12
  const vw = window.innerWidth
  const vh = window.innerHeight

  const candidates = [preferred, 'bottom', 'top', 'right', 'left'].filter(
    (v, i, arr) => arr.indexOf(v) === i,
  )

  for (const side of candidates) {
    let top = 0
    let left = 0

    if (side === 'bottom') {
      top = highlight.top + highlight.height + gap
      left = highlight.left + highlight.width / 2 - tooltipWidth / 2
    } else if (side === 'top') {
      top = highlight.top - tooltipHeight - gap
      left = highlight.left + highlight.width / 2 - tooltipWidth / 2
    } else if (side === 'right') {
      top = highlight.top + highlight.height / 2 - tooltipHeight / 2
      left = highlight.left + highlight.width + gap
    } else {
      top = highlight.top + highlight.height / 2 - tooltipHeight / 2
      left = highlight.left - tooltipWidth - gap
    }

    left = Math.max(margin, Math.min(left, vw - tooltipWidth - margin))
    top = Math.max(margin, Math.min(top, vh - tooltipHeight - margin))

    const fits =
      (side === 'bottom' && top + tooltipHeight <= vh - margin) ||
      (side === 'top' && top >= margin) ||
      (side === 'right' && left + tooltipWidth <= vw - margin) ||
      (side === 'left' && left >= margin)

    if (fits || side === candidates[candidates.length - 1]) {
      return { top, left, side }
    }
  }

  return { top: margin, left: margin, side: 'bottom' }
}
