/** Build API URLs for assets served by the backend (audio, images). */

export const DEFAULT_AVATAR = '/icon_profile.jpg'

export function avatarUrl(url) {
  if (!url || typeof url !== 'string') return DEFAULT_AVATAR
  const trimmed = url.trim()
  if (!trimmed) return DEFAULT_AVATAR
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed
  if (trimmed.startsWith('/')) return trimmed
  return `/uploads/${trimmed}`
}

export function isExternalAvatar(url) {
  return typeof url === 'string' && /^https?:\/\//.test(url.trim())
}

export function imageUrl(fileId) {
  if (!fileId || typeof fileId !== 'string') return ''
  const id = fileId.trim()
  if (!id) return ''
  if (id.startsWith('http://') || id.startsWith('https://')) return id
  if (id.startsWith('/api/images/')) return id.replace('/api/images/', '/images/')
  if (id.startsWith('/images/')) return id
  if (id.startsWith('/')) return id
  return `/images/${id}`
}
