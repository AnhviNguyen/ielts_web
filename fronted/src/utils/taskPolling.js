/**
 * Poll async Celery task endpoints until done or timeout.
 */
import apiClient from '@/api/client.js'

export function pollTaskResult(getUrl, { intervalMs = 3000, timeoutMs = 180000 } = {}) {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const { data: result } = await apiClient.get(getUrl)
        if (result.status === 'done') {
          clearInterval(interval)
          clearTimeout(timeout)
          resolve(result.result)
        } else if (result.status === 'error') {
          clearInterval(interval)
          clearTimeout(timeout)
          reject(new Error(result.detail || 'Task failed'))
        }
      } catch (e) {
        clearInterval(interval)
        clearTimeout(timeout)
        reject(e)
      }
    }, intervalMs)

    const timeout = setTimeout(() => {
      clearInterval(interval)
      reject(new Error('Timeout — tác vụ mất quá nhiều thời gian'))
    }, timeoutMs)
  })
}
