/**
 * Banco POS — Service Worker (Phase 0: PWA shell)
 *
 * Scope: /pos  (served from /pos/sw.js with Service-Worker-Allowed: /pos)
 *
 * Strategy (P0 — installable + read-resilient, NO offline writes yet):
 *   - App shell + vendored libs + static assets: CACHE-FIRST (instant load, works on flaky/no net)
 *   - /pos pages (HTML): NETWORK-FIRST, fall back to cache when offline
 *   - /api/* and /pos/refresh: NETWORK-ONLY (sales/auth still require the server in P0)
 *
 * Phases 1–2 build on this: P1 adds an IndexedDB catalog read-cache; P2 adds the
 * offline sales OUTBOX + background sync. Bump CACHE_NAME on any shell change.
 */
const CACHE_NAME = 'banco-pos-v77';

// The shell we want available instantly / offline. Kept small + safe (GET, same-origin).
const SHELL = [
  '/pos/scan',
  '/static/vendor/tailwind.js',
  '/static/vendor/alpine.min.js',
  '/static/vendor/html2canvas.min.js',
  '/static/pos-scanner.js',
  '/static/pos/catalog-cache.js',
  '/static/pos/icons/icon-192.png',
  '/static/pos/icons/icon-512.png',
  '/static/pos/manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      // addAll is atomic — one miss fails install. Add individually + tolerate misses
      // so a single renamed asset can't brick the SW.
      Promise.all(SHELL.map((url) => cache.add(url).catch(() => null)))
    )
  );
  // BL-011: do NOT skipWaiting automatically — let the new SW WAIT so the page can show a
  // "New version — tap to update" nudge; the cashier picks the moment (never mid-sale).
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// BL-011: page → SW. Activate the waiting worker only when the user taps the update nudge.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle our own origin + GET. Everything else (POST sales, cross-origin) passes through.
  if (req.method !== 'GET' || url.origin !== location.origin) return;

  // Sales + auth stay live in P0 — never serve a stale sale/token from cache.
  // /pos/callback is BYPASSED so the browser follows the OAuth 302 → /pos/dashboard#token=…
  // NATIVELY: when the SW follows that redirect via fetch(), the #token FRAGMENT is dropped and
  // the dashboard bounces back to login (the "press Login twice" bug on mobile). Let the browser do it.
  if (url.pathname.startsWith('/api/') || url.pathname === '/pos/refresh' || url.pathname === '/pos/callback') return;

  // Static assets + vendored libs: cache-first, then fill the cache on first hit.
  const isStatic = url.pathname.startsWith('/static/');
  if (isStatic) {
    event.respondWith(
      caches.match(req).then((cached) =>
        cached || fetch(req).then((resp) => {
          if (resp && resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, clone));
          }
          return resp;
        })
      )
    );
    return;
  }

  // /pos pages: network-first (fresh when online), fall back to cache when offline.
  if (url.pathname === '/pos' || url.pathname.startsWith('/pos/')) {
    event.respondWith(
      fetch(req).then((resp) => {
        if (resp && resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, clone));
        }
        return resp;
      }).catch(() =>
        caches.match(req).then((cached) => cached || caches.match('/pos/scan'))
      )
    );
  }
});
