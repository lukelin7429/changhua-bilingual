// Transparent R2 proxy for schools/ photos.
//
// Route: changhua-bilingual.org/schools/*
// Image-extension requests are served from the R2 bucket (bound as PHOTOS,
// object keys prefixed with "changhua-bilingual"); everything else — pages,
// css, js, pdf, audio — passes through unchanged to GitHub Pages origin.
// If a photo isn't found in R2 (e.g. added to the repo but not yet synced),
// falls back to origin too, so nothing 404s between R2 uploads.

const IMAGE_EXT = /\.(jpg|jpeg|png|webp|gif)$/i;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (!IMAGE_EXT.test(url.pathname)) {
      return fetch(request);
    }

    const key = "changhua-bilingual" + url.pathname;
    const object = await env.PHOTOS.get(key);

    if (object === null) {
      return fetch(request);
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("etag", object.httpEtag);
    headers.set("Cache-Control", "public, max-age=31536000, immutable");

    return new Response(object.body, { headers });
  },
};
