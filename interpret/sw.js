/* 口譯練習室 — service worker.
 * Shell and question banks: network first, cache fallback (a deploy is live at
 * once; offline still works). Voice clips: cache-first (content-hashed names).
 * Only this app's own superseded caches are ever deleted.
 */
var VERSION = 'v1';
var PREFIX = 'interpret-shell-';
var SHELL = PREFIX + VERSION;
var AUDIO = 'interpret-audio';
var PRECACHE = [
  '/interpret/', '/interpret/app.js?v=1', '/interpret/manifest.json',
  '/interpret/data/m1.json', '/interpret/data/m2.json', '/interpret/data/m3.json',
  '/interpret/data/m4.json', '/interpret/data/m5.json', '/interpret/data/m6.json',
  '/assets/js/voice.js', '/audio/manifest/interpret.json',
  '/assets/logo/icon-192.png', '/assets/logo/icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) {
    return Promise.all(PRECACHE.map(function (u) { return c.add(u).catch(function () {}); }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) {
      if (k.indexOf(PREFIX) === 0 && k !== SHELL) return caches.delete(k);
    }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.indexOf('/audio/en/') === 0) {
    e.respondWith(caches.open(AUDIO).then(function (c) {
      return c.match(req).then(function (hit) {
        return hit || fetch(req).then(function (r) { if (r.ok) c.put(req, r.clone()); return r; });
      });
    }));
    return;
  }
  var mine = url.pathname.indexOf('/interpret/') === 0 || url.pathname === '/assets/js/voice.js' ||
             url.pathname === '/audio/manifest/interpret.json';
  if (!mine) return;
  e.respondWith(fetch(req).then(function (r) {
    if (r.ok) { var copy = r.clone(); caches.open(SHELL).then(function (c) { c.put(req, copy); }); }
    return r;
  }).catch(function () {
    return caches.match(req, { ignoreSearch: url.pathname === '/interpret/' }).then(function (hit) {
      return hit || caches.match('/interpret/');
    });
  }));
});
