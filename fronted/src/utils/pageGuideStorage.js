const STORAGE_KEY = 'lingua-page-tours-v2'

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function writeAll(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

function userKey(userScope) {
  return String(userScope || 'anonymous')
}

export function hasSeenPageGuide(userScope, guideKey) {
  if (!guideKey) return true
  const bucket = readAll()[userKey(userScope)]
  return Boolean(bucket?.[guideKey])
}

export function markPageGuideSeen(userScope, guideKey) {
  if (!guideKey) return
  const all = readAll()
  const uk = userKey(userScope)
  all[uk] = { ...(all[uk] || {}), [guideKey]: Date.now() }
  writeAll(all)
}

export function resetPageGuides(userScope) {
  const all = readAll()
  delete all[userKey(userScope)]
  writeAll(all)
}
