import { cloudinaryAudioUrl } from '@/utils/cloudinaryUrl.js'

export function buildAudioSrc(fileId) {
  if (!fileId) return ''
  const cloudinary = cloudinaryAudioUrl(fileId)
  if (cloudinary) return cloudinary
  const base = (import.meta.env.VITE_AUDIO_CDN_BASE || '').trim()
  const ext = (import.meta.env.VITE_AUDIO_CDN_EXT || '').trim() || '.mp3'
  if (!base) return ''
  return `${base.replace(/\/$/, '')}/${fileId}${ext.startsWith('.') ? ext : `.${ext}`}`
}

