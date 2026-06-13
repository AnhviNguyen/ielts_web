/** Direct Cloudinary delivery URLs for quiz audio/images. */

export function mediaFileStem(fileId) {
  let id = String(fileId || '').trim()
  if (!id) return ''
  if (id.startsWith('http://') || id.startsWith('https://')) return id
  id = id
    .replace(/^\/api\/images\//, '')
    .replace(/^\/images\//, '')
    .replace(/^\/api\/audio\//, '')
    .replace(/^\/audio\//, '')
  return id.split('.')[0]
}

export function cloudinaryCloudName() {
  return (import.meta.env.VITE_CLOUDINARY_CLOUD_NAME || '').trim()
}

export function cloudinaryAudioUrl(fileId) {
  const stem = mediaFileStem(fileId)
  const cloud = cloudinaryCloudName()
  if (!cloud || !stem || stem.startsWith('http')) return ''
  return `https://res.cloudinary.com/${cloud}/video/upload/audio/${stem}.mp3`
}

export function cloudinaryImageUrl(fileId) {
  const stem = mediaFileStem(fileId)
  const cloud = cloudinaryCloudName()
  if (!cloud || !stem || stem.startsWith('http')) return ''
  return `https://res.cloudinary.com/${cloud}/image/upload/images/${stem}.png`
}

export function usesCloudinaryCdn() {
  return Boolean(cloudinaryCloudName())
}
