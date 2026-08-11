// Transparent R2 proxy for site media.
//
// Routes: changhua-bilingual.org/schools/*  and  /learn/audio/*
//
// Two kinds of request are served from the R2 bucket (bound as PHOTOS, object
// keys prefixed with "changhua-bilingual"):
//   * image files anywhere under /schools/
//   * mp3 files under /learn/audio/  — the Mandarin pronunciation clips
// Everything else — pages, css, js, pdf — passes through to GitHub Pages.
//
// Photos fall back to origin when missing from R2, so nothing 404s between
// uploads. The learn clips have no origin copy (they are deliberately kept out
// of the Pages artifact), so a miss there is a genuine 404 and is reported as
// one rather than being silently proxied to a 404 page.

const IMAGE_EXT = /\.(jpg|jpeg|png|webp|gif)$/i;
const LEARN_AUDIO = /^\/learn\/audio\/[a-f0-9]{12}\.mp3$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const isLearnAudio = LEARN_AUDIO.test(url.pathname);
    const isPhoto = !isLearnAudio && IMAGE_EXT.test(url.pathname);

    if (!isLearnAudio && !isPhoto) {
      return fetch(request);
    }

    const key = "changhua-bilingual" + url.pathname;
    const object = await env.PHOTOS.get(key);

    if (object === null) {
      // Photos have a copy at origin; learn audio does not.
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
