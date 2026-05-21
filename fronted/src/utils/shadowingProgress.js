const STORAGE_KEY = 'shadowing-progress'
const META_KEY = 'shadowing-video-meta'

/**
 * @typedef {Object} ShadowingProgress
 * @property {string} video_id
 * @property {number} currentSegment
 * @property {number[]} dictationScores
 * @property {number[]} pronunciationScores
 * @property {number[]} flaggedSegments
 */

export function loadProgress(videoId) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const all = raw ? JSON.parse(raw) : {}
    return all[videoId] || {
      video_id: videoId,
      currentSegment: 0,
      dictationScores: [],
      pronunciationScores: [],
      flaggedSegments: [],
    }
  } catch {
    return {
      video_id: videoId,
      currentSegment: 0,
      dictationScores: [],
      pronunciationScores: [],
      flaggedSegments: [],
    }
  }
}

export function saveProgress(videoId, patch) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const all = raw ? JSON.parse(raw) : {}
    all[videoId] = { ...loadProgress(videoId), ...patch, video_id: videoId }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all))
  } catch { /* ignore */ }
}

export function saveVideoMeta(videoId, { title, level, sourceUrl } = {}) {
  try {
    const raw = localStorage.getItem(META_KEY)
    const all = raw ? JSON.parse(raw) : {}
    all[videoId] = {
      ...all[videoId],
      title: title ?? all[videoId]?.title,
      level: level ?? all[videoId]?.level,
      sourceUrl: sourceUrl ?? all[videoId]?.sourceUrl,
      lastVisitedAt: new Date().toISOString(),
    }
    localStorage.setItem(META_KEY, JSON.stringify(all))
  } catch { /* ignore */ }
}

/** Local fallback history from progress/meta keys. */
export function listLocalHistory() {
  try {
    const progRaw = localStorage.getItem(STORAGE_KEY)
    const metaRaw = localStorage.getItem(META_KEY)
    const prog = progRaw ? JSON.parse(progRaw) : {}
    const meta = metaRaw ? JSON.parse(metaRaw) : {}
    return Object.keys(prog)
      .map((videoId) => ({
        video_id: videoId,
        title: meta[videoId]?.title || videoId,
        level: meta[videoId]?.level || 'Intermediate',
        segment_count: 0,
        last_viewed_at: meta[videoId]?.lastVisitedAt || null,
        _local: true,
      }))
      .sort((a, b) => {
        const ta = a.last_viewed_at ? new Date(a.last_viewed_at).getTime() : 0
        const tb = b.last_viewed_at ? new Date(b.last_viewed_at).getTime() : 0
        return tb - ta
      })
  } catch {
    return []
  }
}

export function updateLocalHistoryMeta(videoId, { title, level } = {}) {
  saveVideoMeta(videoId, { title, level })
}

export function removeLocalHistory(videoId) {
  try {
    const progRaw = localStorage.getItem(STORAGE_KEY)
    const metaRaw = localStorage.getItem(META_KEY)
    const prog = progRaw ? JSON.parse(progRaw) : {}
    const meta = metaRaw ? JSON.parse(metaRaw) : {}
    delete prog[videoId]
    delete meta[videoId]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prog))
    localStorage.setItem(META_KEY, JSON.stringify(meta))
  } catch { /* ignore */ }
}
