const CACHE_NAME = 'eduvault-v1';
const APP_SHELL = ['/static/manifest.json'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open('eduvault-offline-v2').then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
