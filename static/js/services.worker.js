// Nama cache biar gampang diupdate
const CACHE_NAME = "bel-otomatis-v1";

// File yang dicache waktu install
const urlsToCache = [
  "/",
  "/schedules",
  "/settings",
  "/static/css/style.css",
  "/static/js/service-worker.js",
  "/static/sounds/default.mp3",
];

// 🔹 Install service worker
self.addEventListener("install", event => {
  console.log("🔧 Service Worker: Install");
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log("📦 Caching files...");
      return cache.addAll(urlsToCache);
    })
  );
});

// 🔹 Aktivasi (hapus cache lama kalau ada)
self.addEventListener("activate", event => {
  console.log("⚡ Service Worker: Activated");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    )
  );
});

// 🔹 Fetch handler (ambil dari cache dulu, kalau tidak ada ambil dari server)
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        console.log("✅ Load from cache:", event.request.url);
        return response;
      }
      console.log("🌐 Fetch from network:", event.request.url);
      return fetch(event.request);
    })
  );
});