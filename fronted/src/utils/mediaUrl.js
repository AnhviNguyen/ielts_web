/** Build CDN URLs for quiz audio/images (Cloudinary when configured). */

import { cloudinaryImageUrl, mediaFileStem } from '@/utils/cloudinaryUrl.js'

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
  const cloudinary = cloudinaryImageUrl(id)
  if (cloudinary) return cloudinary
  const stem = mediaFileStem(id)
  if (!stem) return ''
  if (id.startsWith('/')) return id
  return `/api/images/${stem}`
}

