const CACHE_NAME = 'fuel-pulse-__BUILD_TIMESTAMP__';

// Static shell to pre-cache on install
const PRECACHE = ['/', '/manifest.webmanifest', '/favicon.svg'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(PRECACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== CACHE_NAME; })
            .map(function (k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;

  var url = new URL(e.request.url);

  // Network-first for JSON data files — always try fresh, fall back to cache
  if (url.pathname.endsWith('.json')) {
    e.respondWith(
      fetch(e.request)
        .then(function (res) {
          var clone = res.clone();
          caches.open(CACHE_NAME).then(function (c) { c.put(e.request, clone); });
          return res;
        })
        .catch(function () { return caches.match(e.request); })
    );
    return;
  }

  // Network-first for HTML pages — always fresh
  if (url.pathname.endsWith('/') || url.pathname.endsWith('.html') || !url.pathname.includes('.')) {
    e.respondWith(
      fetch(e.request)
        .then(function (res) {
          if (res.ok) {
            var clone = res.clone();
            caches.open(CACHE_NAME).then(function (c) { c.put(e.request, clone); });
          }
          return res;
        })
        .catch(function () { return caches.match(e.request); })
    );
    return;
  }

  // Cache-first for static assets (CSS, JS, fonts, images)
  e.respondWith(
    caches.match(e.request).then(function (cached) {
      if (cached) return cached;
      return fetch(e.request).then(function (res) {
        if (res.ok) {
          var clone = res.clone();
          caches.open(CACHE_NAME).then(function (c) { c.put(e.request, clone); });
        }
        return res;
      });
    })
  );
});
