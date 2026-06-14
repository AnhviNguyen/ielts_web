import { cloudinaryAudioUrl } from '@/utils/cloudinaryUrl.js'

export function buildAudioSrc(fileId) {
  if (!fileId) return ''
  const id = String(fileId).trim()
  if (id.startsWith('http://') || id.startsWith('https://')) return id
  const cloudinary = cloudinaryAudioUrl(id)
  if (cloudinary) return cloudinary
  const base = (import.meta.env.VITE_AUDIO_CDN_BASE || '').trim()
  const ext = (import.meta.env.VITE_AUDIO_CDN_EXT || '').trim() || '.mp3'
  if (!base) return ''
  return `${base.replace(/\/$/, '')}/${id}${ext.startsWith('.') ? ext : `.${ext}`}`
}

/** Prefer API-provided audio_url (Cloudinary), else build from file_id. */
export function partAudioSrc(part) {
  if (!part) return ''
  const url = part.audio_url
  if (url && String(url).trim()) return String(url).trim()
  return buildAudioSrc(part.file_id)
}

