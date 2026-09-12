const CACHE_PREFIX = 'punto-cero-';
const CACHE_NAME = 'punto-cero-shell-v6';
const SHELL_ASSETS = [
  './',
  './index.html',
  './captura.html',
  './curaduria.html'
];

function cacheResponse(request, response) {
  if (!response || !response.ok) return response;
  const copy = response.clone();
  caches.open(CACHE_NAME).then(function(cache) {
    cache.put(request, copy).catch(function() {});
  });
  return response;
}

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) { return cache.addAll(SHELL_ASSETS); })
      .catch(function() {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.map(function(key) {
        if (key !== CACHE_NAME && key.startsWith(CACHE_PREFIX)) {
          return caches.delete(key);
        }
        return undefined;
      }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function(event) {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  const isHtml = request.mode === 'navigate';
  const isAudio = request.destination === 'audio' || /\.(mp3|wav)$/i.test(url.pathname);

  if (url.origin !== self.location.origin) return;
  if (isAudio) return;

  if (isHtml) {
    const network = fetch(request)
      .then(function(response) { return cacheResponse(request, response); });

    event.respondWith(
      network.catch(function() {
        return caches.match(request, { ignoreSearch: true }).then(function(cached) {
          return cached || caches.match('./index.html');
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(function(cached) {
      return cached || fetch(request).then(function(response) {
        return cacheResponse(request, response);
      });
    })
  );
});
