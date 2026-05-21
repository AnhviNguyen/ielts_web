/** Build API URLs for assets served by the backend (audio, images). */

export function imageUrl(fileId) {
  if (!fileId || typeof fileId !== 'string') return ''
  const id = fileId.trim()
  if (!id) return ''
  if (id.startsWith('http://') || id.startsWith('https://') || id.startsWith('/')) return id
  return `/api/images/${id}`
}
