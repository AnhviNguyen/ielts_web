/** Build API URLs for assets served by the backend (audio, images). */

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
