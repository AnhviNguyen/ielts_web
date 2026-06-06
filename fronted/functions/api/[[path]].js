const DEFAULT_API_ORIGIN = 'https://phuc7-linguaielts-api.hf.space'

export async function onRequest(context) {
  const apiOrigin = context.env.API_ORIGIN || DEFAULT_API_ORIGIN
  const url = new URL(context.request.url)
  const upstream = new URL(url.pathname.replace(/^\/api/, '') || '/', apiOrigin)
  upstream.search = url.search

  const headers = new Headers(context.request.headers)
  headers.set('host', upstream.host)
  headers.set('x-forwarded-proto', 'https')
  headers.set('x-forwarded-host', url.host)

  return fetch(upstream.toString(), {
    method: context.request.method,
    headers,
    body: ['GET', 'HEAD'].includes(context.request.method)
      ? undefined
      : context.request.body,
    redirect: 'manual',
  })
}
