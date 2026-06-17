const DEFAULT_API_ORIGIN = 'https://phuc7-linguaielts-api.hf.space'
const CONTENT_CACHE_TTL_SECONDS = 600
const CONTENT_CACHE_PREFIXES = [
  /^\/mock-tests(?:\/\d+)?$/,
  /^\/quizzes\/\d+$/,
  /^\/writing\/topics(?:\/\d+)?$/,
  /^\/mock-exams\/sets(?:\/[^/]+)?$/,
]

function isContentCacheable(request, upstreamPath) {
  if (request.method !== 'GET') return false
  if (!CONTENT_CACHE_PREFIXES.some((pattern) => pattern.test(upstreamPath))) return false
  const auth = request.headers.get('authorization') || ''
  return /^Bearer\s+\S+/.test(auth)
}

export async function onRequest(context) {
  const apiOrigin = context.env.API_ORIGIN || DEFAULT_API_ORIGIN
  const url = new URL(context.request.url)
  const upstreamPath = url.pathname
  const cachePath = upstreamPath.replace(/^\/api/, '') || '/'
  const upstream = new URL(upstreamPath, apiOrigin)
  upstream.search = url.search
  const cacheable = isContentCacheable(context.request, cachePath)
  const cacheKey = new Request(
    new URL(`/api-cache${cachePath}${url.search}`, url.origin).toString(),
    { method: 'GET' },
  )

  if (cacheable) {
    const cached = await caches.default.match(cacheKey)
    if (cached) {
      const headers = new Headers(cached.headers)
      headers.set('x-pages-cache', 'hit')
      return new Response(cached.body, {
        status: cached.status,
        statusText: cached.statusText,
        headers,
      })
    }
  }

  const headers = new Headers(context.request.headers)
  headers.set('host', upstream.host)
  headers.set('x-forwarded-proto', 'https')
  headers.set('x-forwarded-host', url.host)

  const response = await fetch(upstream.toString(), {
    method: context.request.method,
    headers,
    body: ['GET', 'HEAD'].includes(context.request.method)
      ? undefined
      : context.request.body,
    redirect: 'manual',
  })

  if (cacheable && response.ok) {
    const cachedHeaders = new Headers(response.headers)
    cachedHeaders.delete('set-cookie')
    cachedHeaders.set('cache-control', `public, max-age=${CONTENT_CACHE_TTL_SECONDS}`)
    cachedHeaders.set('x-pages-cache', 'miss')
    const cachedResponse = new Response(response.clone().body, {
      status: response.status,
      statusText: response.statusText,
      headers: cachedHeaders,
    })
    context.waitUntil(caches.default.put(cacheKey, cachedResponse.clone()))
    return cachedResponse
  }

  return response
}
