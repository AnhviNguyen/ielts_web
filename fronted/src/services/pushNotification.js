import apiClient from '@/api/client.js'

export function isPushNotificationSupported() {
  return (
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  )
}

export async function registerServiceWorker() {
  if (!isPushNotificationSupported()) {
    throw new Error('Browser does not support Web Push')
  }
  return navigator.serviceWorker.register('/sw.js')
}

export async function requestNotificationPermission() {
  if (!('Notification' in window)) return 'unsupported'
  if (Notification.permission === 'granted') return 'granted'
  if (Notification.permission === 'denied') return 'denied'
  return Notification.requestPermission()
}

export async function getCurrentSubscription() {
  if (!isPushNotificationSupported()) return null
  const registration = await navigator.serviceWorker.ready
  return registration.pushManager.getSubscription()
}

export async function subscribeUserToPush() {
  const registration = await registerServiceWorker()
  const permission = await requestNotificationPermission()
  if (permission !== 'granted') {
    throw new Error('Notification permission was not granted')
  }

  const { data } = await apiClient.get('/users/me/notifications/push/vapid-public-key')
  const publicKey = data.public_key
  if (!publicKey) {
    throw new Error('VAPID public key is missing')
  }

  let subscription = await registration.pushManager.getSubscription()
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    })
  }

  const subscriptionJson = subscription.toJSON()
  await apiClient.post('/users/me/notifications/push/subscribe', {
    endpoint: subscriptionJson.endpoint,
    keys: {
      p256dh: subscriptionJson.keys?.p256dh,
      auth: subscriptionJson.keys?.auth,
    },
  })
  return subscription
}

export async function unsubscribeUserFromPush() {
  const subscription = await getCurrentSubscription()
  if (!subscription) return false

  const endpoint = subscription.endpoint
  try {
    await apiClient.post('/users/me/notifications/push/unsubscribe', { endpoint })
  } finally {
    await subscription.unsubscribe()
  }
  return true
}

export async function sendTestPushNotification() {
  const { data } = await apiClient.post('/users/me/notifications/push/test', {
    title: 'LinguaIELTS',
    body: 'Thông báo Web Push đang hoạt động.',
    url: '/dashboard?tab=study',
  })
  return data
}

export function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = `${base64String}${padding}`
    .replace(/-/g, '+')
    .replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; i += 1) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}
