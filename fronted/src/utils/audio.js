export function buildAudioSrc(fileId) {
  const base = (import.meta.env.VITE_AUDIO_CDN_BASE || '').trim()
  const ext = (import.meta.env.VITE_AUDIO_CDN_EXT || '').trim() || '.mp3'
  if (!base) return ''
  return `${base.replace(/\/$/, '')}/${fileId}${ext.startsWith('.') ? ext : `.${ext}`}`
}

