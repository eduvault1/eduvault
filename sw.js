// static/sw.js - EduVault Offline Cache Manager
const CACHE_NAME = 'eduvault-offline-v1';

// Static files and pages to save in phone memory
const ASSETS_TO_CACHE = [
  '/',
  '/resources',
  '/subject/Entrance',
  '/subject/Mathematics',
  '/subject/Biology',
  '/subject/Physics',
  '/subject/Chemistry',
  '/tutor',
  '/static/manifest.json',
  '/static/edu1.jpg',
  '/static/edu2.jpg',
  '/static/edu3.jpg',
  '/static/edu4.jpg',
  '/static/edu5.jpg',
  '/static/founder.jpg'
];

// Install Service Worker and cache all static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[EduVault] Caching offline assets...');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate & clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Intercept network requests: Serve from Phone Memory if Offline
self.addEventListener('fetch', event => {
  // AI endpoint ALWAYS requires internet
  if (event.request.url.includes('/api/tutor') || event.request.url.includes('/api/chat')) {
    return; // Pass through to network
  }

  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        // Return cached page/file immediately
        fetch(event.request).then(networkResponse => {
          if (networkResponse.status === 200) {
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, networkResponse));
          }
        }).catch(() => {/* Ignore network error when offline */});
        return cachedResponse;
      }

      // If not in cache, try fetching from network
      return fetch(event.request).then(response => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseToCache));
        return response;
      }).catch(() => {
        // Fallback for offline API calls
        return caches.match('/');
      });
    })
  );
});
