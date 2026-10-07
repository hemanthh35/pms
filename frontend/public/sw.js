self.addEventListener('push', (event) => {
  let data = { title: 'CivicAI', body: 'You have a new update.' }
  try { data = event.data.json() } catch { /* ignore non-JSON payloads */ }
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon.png',
      badge: '/icon.png',
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(self.clients.openWindow('/'))
})
