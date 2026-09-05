const CACHE_NAME = 'ihsg-screener-pro-v2';

// Daftar file statis yang di-cache untuk akses cepat
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  'https://cdn.tailwindcss.com'
];

// Tahap Install: Caching file statis
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching app shell');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Tahap Activate: Menghapus cache versi lama jika ada pembaruan
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Clearing old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Tahap Fetch: Menggunakan strategi Network First untuk API & Cache First untuk file statis
self.addEventListener('fetch', (event) => {
  // Biarkan data API (Yahoo / AllOrigins) selalu mengambil data terbaru dari jaringan
  if (event.request.url.includes('yahoo.com') || event.request.url.includes('allorigins.win')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Untuk aset aplikasi (HTML/JS/CSS), ambil dari cache terlebih dahulu
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});
