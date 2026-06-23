/**
 * Fetch YouTube captions for Shadowing.
 *
 * Oracle VPS: server IP is blocked — needs Webshare proxy on backend OR
 * browser fetches signed timedtext URL (CORS allowed by YouTube).
 */
import apiClient from '@/api/client.js'

const INNERTUBE_PLAYER = 'https://www.youtube.com/youtubei/v1/player'
const INNERTUBE_WEB_KEY = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
const ANDROID_CLIENT = {
  clientName: 'ANDROID',
  clientVersion: '20.10.38',
  hl: 'en',
  gl: 'US',
}
const WEB_CLIENT = {
  clientName: 'WEB',
  clientVersion: '2.20260618.05.00',
  hl: 'en',
  gl: 'US',
}

const CAPTION_HELP_NO_CC =
  'Video này không có phụ đề tiếng Anh (CC). Thử video TED/BBC hoặc bật phụ đề trên YouTube.'
const CAPTION_HELP_BLOCKED =
  'YouTube chặn IP server Oracle cho video này. Thêm Webshare free (YOUTUBE_WEBSHARE_USERNAME/PASSWORD trong .env) hoặc thử video khác có phụ đề EN.'

function listPreferredCaptionTracks(tracks, langs = ['en', 'en-us', 'en-gb']) {
  if (!tracks?.length) return []
  const lowered = langs.map((l) => l.toLowerCase())
  const ordered = []
  const seen = new Set()

  const add = (track) => {
    const url = track?.baseUrl || ''
    if (url && !seen.has(url)) {
      seen.add(url)
      ordered.push(track)
    }
  }

  for (const lang of lowered) {
    for (const track of tracks) {
      const code = (track.languageCode || '').toLowerCase()
      if ((code === lang || code.startsWith(`${lang}-`)) && track.kind !== 'asr') add(track)
    }
  }
  for (const lang of lowered) {
    for (const track of tracks) {
      const code = (track.languageCode || '').toLowerCase()
      if (code === lang || code.startsWith(`${lang}-`)) add(track)
    }
  }
  for (const track of tracks) add(track)
  return ordered
}

function pickCaptionTrack(tracks, langs = ['en']) {
  return listPreferredCaptionTracks(tracks, langs)[0] || null
}

function captionUrlFromTrack(track) {
  let url = track.baseUrl
  if (!url.includes('fmt=')) {
    url += (url.includes('?') ? '&' : '?') + 'fmt=json3'
  }
  return {
    captionUrl: url,
    language: (track.languageCode || 'en').split('-')[0],
  }
}

function parseTimedTextXml3(raw) {
  const segments = []
  const tagRe = /<[^>]+>/g
  const pRe = /<p\s+t="(\d+)"\s+d="(\d+)"[^>]*>(.*?)<\/p>/gs
  let m
  while ((m = pRe.exec(raw)) !== null) {
    const text = m[3].replace(tagRe, '').trim()
    if (text) {
      segments.push({
        text,
        start: Number(m[1]) / 1000,
        duration: Math.max(0.1, Number(m[2]) / 1000),
      })
    }
  }
  if (segments.length) return segments
  const textRe = /<text\s+start="([\d.]+)"\s+dur="([\d.]+)"[^>]*>(.*?)<\/text>/gs
  while ((m = textRe.exec(raw)) !== null) {
    const text = m[3].replace(tagRe, '').trim()
    if (text) {
      segments.push({
        text,
        start: Number(m[1]),
        duration: Math.max(0.1, Number(m[2])),
      })
    }
  }
  return segments
}

function parseJson3(raw) {
  const data = JSON.parse(raw)
  const segments = []
  for (const event of data.events || []) {
    if (!event.segs) continue
    const text = event.segs.map((s) => s.utf8 || '').join('').trim()
    if (!text || text === '\n') continue
    segments.push({
      text: text.replace(/[\u266a\u266b]/g, '').trim(),
      start: (event.tStartMs || 0) / 1000,
      duration: Math.max(0.1, (event.dDurationMs || 100) / 1000),
    })
  }
  return segments.filter((s) => s.text)
}

function parseVtt(raw) {
  const segments = []
  const timeRe =
    /(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})/
  const tagRe = /<[^>]+>/g
  const lines = raw.split(/\r?\n/)
  let i = 0
  while (i < lines.length) {
    const m = lines[i].match(timeRe)
    if (m) {
      const toSec = (h, min, s, ms) =>
        Number(h) * 3600 + Number(min) * 60 + Number(s) + Number(ms) / 1000
      const start = toSec(m[1], m[2], m[3], m[4])
      const end = toSec(m[5], m[6], m[7], m[8])
      i += 1
      const textLines = []
      while (i < lines.length && lines[i].trim()) {
        const cleaned = lines[i].replace(tagRe, '').trim()
        if (cleaned) textLines.push(cleaned)
        i += 1
      }
      const text = textLines.join(' ')
      if (text) segments.push({ text, start, duration: Math.max(0.1, end - start) })
    } else {
      i += 1
    }
  }
  return segments
}

export function parseTimedTextContent(raw) {
  const text = (raw || '').trim()
  if (!text) return []
  if (text.startsWith('{')) return parseJson3(text)
  if (text.includes('<timedtext') || text.includes('<p t=') || text.includes('<text start=')) {
    return parseTimedTextXml3(text)
  }
  return parseVtt(text)
}

async function fetchCaptionContentInBrowser(captionUrl) {
  const res = await fetch(captionUrl, {
    credentials: 'omit',
    headers: { Accept: 'text/xml, application/json, text/vtt, */*' },
  })
  if (!res.ok) {
    throw new Error(`Browser fetch caption failed (${res.status})`)
  }
  const raw = await res.text()
  const segments = parseTimedTextContent(raw)
  if (!segments.length) throw new Error('Phụ đề trống')
  return segments
}

async function fetchCaptionContentViaServer(captionUrl) {
  const { data } = await apiClient.post('/shadowing/video/proxy-caption', {
    caption_url: captionUrl,
  })
  return data.segments || []
}

async function resolveCaptionMetasFromBrowserInnertube(videoId) {
  const clients = [
    { client: ANDROID_CLIENT, key: '' },
    { client: WEB_CLIENT, key: `?key=${INNERTUBE_WEB_KEY}` },
  ]
  for (const { client, key } of clients) {
    try {
      const res = await fetch(`${INNERTUBE_PLAYER}${key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context: { client },
          videoId,
        }),
      })
      if (!res.ok) continue
      const player = await res.json()
      const tracks =
        player?.captions?.playerCaptionsTracklistRenderer?.captionTracks || []
      const preferred = listPreferredCaptionTracks(tracks)
      if (preferred.length) {
        return preferred.map((track) => captionUrlFromTrack(track))
      }
    } catch {
      /* try next client */
    }
  }
  return []
}

async function getCaptionUrlFromApi(videoId) {
  const { data } = await apiClient.get(`/shadowing/video/${videoId}/caption-url`)
  return { captionUrl: data.caption_url, language: data.language || 'en' }
}

async function getCaptionSegmentsFromApi(videoId) {
  const { data } = await apiClient.get(`/shadowing/video/${videoId}/caption-segments`, {
    timeout: 180000,
  })
  return { segments: data.segments || [], language: data.language || 'en' }
}

async function fetchFromCaptionUrl(meta) {
  try {
    const segments = await fetchCaptionContentInBrowser(meta.captionUrl)
    return { segments, language: meta.language || 'en' }
  } catch {
    const segments = await fetchCaptionContentViaServer(meta.captionUrl)
    if (!segments.length) throw new Error('Proxy caption empty')
    return { segments, language: meta.language || 'en' }
  }
}

async function fetchFromCaptionMetas(metas) {
  const errors = []
  for (const meta of metas) {
    try {
      return await fetchFromCaptionUrl(meta)
    } catch (e) {
      errors.push(e?.response?.data?.detail || e.message)
    }
  }
  if (errors.length) throw new Error(errors[errors.length - 1])
  throw new Error('Không tải được phụ đề')
}

function buildCaptionError(errors) {
  const joined = errors.join(' | ').toLowerCase()
  if (joined.includes('login_required') || joined.includes('chặn ip server')) {
    return CAPTION_HELP_BLOCKED
  }
  if (
    joined.includes('no caption') ||
    joined.includes('caption tracks') ||
    joined.includes('phụ đề trống')
  ) {
    return CAPTION_HELP_NO_CC
  }
  return CAPTION_HELP_BLOCKED
}

/**
 * @returns {Promise<{ segments: Array<{text,start,duration}>, language: string }>}
 */
export async function fetchYoutubeCaptionsClient(videoId) {
  const errors = []

  // 1. Server full fetch (works when Webshare/cookies configured on VPS)
  try {
    const data = await getCaptionSegmentsFromApi(videoId)
    if (data.segments.length) return data
  } catch (e) {
    errors.push(`server-segments: ${e?.response?.data?.detail || e.message}`)
  }

  // 2. Server signed URL → browser or server proxy fetch
  let metas = []
  try {
    const meta = await getCaptionUrlFromApi(videoId)
    if (meta?.captionUrl) metas.push(meta)
  } catch (e) {
    errors.push(`caption-url: ${e?.response?.data?.detail || e.message}`)
  }

  if (metas.length) {
    try {
      return await fetchFromCaptionMetas(metas)
    } catch (e) {
      errors.push(`caption-fetch: ${e?.response?.data?.detail || e.message}`)
    }
  }

  // Browser InnerTube blocked by CORS on production — skip (server uses Supadata/Apify).
  console.warn('Caption fetch failed:', errors)
  throw new Error(buildCaptionError(errors))
}
