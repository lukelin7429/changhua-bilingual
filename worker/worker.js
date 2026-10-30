// Transparent R2 proxy for site media.
//
// Routes: changhua-bilingual.org/schools/*, /learn/audio/* and /audio/*
//
// Three kinds of request are served from the R2 bucket (bound as PHOTOS, object
// keys prefixed with "changhua-bilingual"):
//   * image files anywhere under /schools/
//   * mp3 files under /learn/audio/  — the Mandarin pronunciation clips
//   * mp3 files under /audio/en/     — the English 🔊 clips (assets/js/voice.js)
// Everything else — pages, css, js, pdf, and the /audio/manifest/*.json files —
// passes through to GitHub Pages.
//
// Photos fall back to origin when missing from R2, so nothing 404s between
// uploads. The audio clips have no origin copy (they are deliberately kept out
// of the Pages artifact), so a miss there is a genuine 404 and is reported as
// one rather than being silently proxied to a 404 page.

const IMAGE_EXT = /\.(jpg|jpeg|png|webp|gif)$/i;
const AUDIO = /^\/(learn\/audio|audio\/en)\/[a-f0-9]{12}\.mp3$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const isAudio = AUDIO.test(url.pathname);
    const isPhoto = !isAudio && IMAGE_EXT.test(url.pathname);

    if (!isAudio && !isPhoto) {
      return fetch(request);
    }

    const key = "changhua-bilingual" + url.pathname;
    const object = await env.PHOTOS.get(key);

    if (object === null) {
      // Photos have a copy at origin; audio clips do not.
      if (isPhoto) return fetch(request);
      return new Response("Audio not found", {
        status: 404,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("etag", object.httpEtag);
    // Filenames are content hashes, so these can never go stale.
    headers.set("Cache-Control", "public, max-age=31536000, immutable");

    return new Response(object.body, { headers });
  },
};
