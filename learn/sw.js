/* Changhua Mandarin — service worker.
 *
 * Shell and question banks: network first, falling back to cache when offline,
 * so a deploy is live immediately and no one ever runs a half-updated build.
 * Audio: cache-first and kept forever — the filenames are content hashes, so a
 * changed phrase gets a new name and the old file simply falls out of use.
 * The 536 clips are deliberately NOT precached; they arrive as they are played.
 */
var VERSION = 'v2';
var PREFIX = 'mandarin-shell-';
var SHELL = 'mandarin-shell-' + VERSION;
var AUDIO = 'mandarin-audio';           // unversioned: content-hashed filenames

var PRECACHE = [
  '/learn/',
  '/learn/manifest.json',
  '/learn/audio-manifest.json',
  '/assets/css/learn.css',
  '/assets/js/learn-engine.js',
  '/assets/logo/icon-192.png',
  '/assets/logo/icon-512.png',
  '/fets/mandarin-challenge/data/beginner.json',
  '/fets/mandarin-challenge/data/intermediate.json',
  '/fets/mandarin-challenge/data/advanced.json'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(SHELL)
      // Individually, so one 404 can't fail the whole install.
      .then(function (c) {
        return Promise.all(PRECACHE.map(function (u) {
          return c.add(u).catch(function () {});
        }));
      })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        // Only ever drop OUR OWN superseded shell. The other app on this origin
        // has its own shell cache and both share the audio cache; deleting
        // anything else would wipe a sibling app's offline copy.
        if (k.indexOf(PREFIX) === 0 && k !== SHELL) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Audio — cache first, never revalidated.
  if (url.pathname.indexOf('/learn/audio/') === 0 && url.pathname.slice(-4) === '.mp3') {
    e.respondWith(
      caches.open(AUDIO).then(function (c) {
        return c.match(req).then(function (hit) {
          if (hit) return hit;
          return fetch(req).then(function (res) {
            if (res && res.ok) c.put(req, res.clone());
            return res;
          });
        });
      })
    );
    return;
  }

  // Shell and banks — serve cached immediately, refresh in the background.
  if (url.pathname.indexOf('/learn/') === 0 ||
      url.pathname.indexOf('/assets/css/learn.css') === 0 ||
      url.pathname.indexOf('/assets/js/learn-engine.js') === 0 ||
      url.pathname.indexOf('/fets/mandarin-challenge/data/') === 0) {
    // Network first. Stale-while-revalidate would hand back the previous build
    // and only refresh afterwards, so every deploy landed one visit late — and
    // a visit that mixes a new page with the previous engine is simply broken.
    // Offline still works: the cached copy is the fallback, not the default.
    e.respondWith(
      caches.open(SHELL).then(function (c) {
        return fetch(req).then(function (res) {
          if (res && res.ok) c.put(req, res.clone());
          return res;
        }).catch(function () {
          return c.match(req);
        });
      })
    );
  }
});

/* Ask the page to pre-fetch a set of clips (the "download this unit" button). */
self.addEventListener('message', function (e) {
  var d = e.data || {};
  if (d.type !== 'prefetch-audio' || !d.urls) return;
  e.waitUntil(
    caches.open(AUDIO).then(function (c) {
      return Promise.all(d.urls.map(function (u) {
        return c.match(u).then(function (hit) { return hit || c.add(u).catch(function () {}); });
      }));
    })
  );
});
