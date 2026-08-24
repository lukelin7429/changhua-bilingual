#!/usr/bin/env python3
"""Content-hash cache busting for the Hub's shared assets.

Everything under /assets/ is served with `max-age=14400`, so a returning
visitor keeps the old file for up to four hours after a deploy — with no
symptom other than "the change didn't happen". Stamping each reference with a
hash of the file's own contents makes the URL change exactly when the file
changes, which busts both the browser and the Cloudflare edge, and costs
nothing when it hasn't changed.

One implementation, used from two places:
  * build.py            — stamps the pages it generates, as it writes them
  * tools/stamp_assets.py — stamps the hand-written pages

Only absolute /assets/... references are touched. External URLs (Google Fonts)
and each school's own relative assets are left alone.
"""
import hashlib
import re
from pathlib import Path

# href="/assets/css/x.css"  or  src="/assets/js/x.js"  (optionally already stamped)
REF = re.compile(r'((?:href|src)=")(/assets/[^"?#]+\.(?:css|js))(?:\?v=[^"#]*)?((?:#[^"]*)?")')

_cache: dict[Path, str] = {}


def _hash(path: Path) -> str | None:
    if path in _cache:
        return _cache[path]
    try:
        h = hashlib.sha1(path.read_bytes()).hexdigest()[:8]
    except OSError:
        return None
    _cache[path] = h
    return h


def content_hash(path: Path) -> str:
    """Short hash of a file's contents, for versioning any asset URL."""
    return _hash(path) or "0"


def stamp_html(html: str, root: Path) -> str:
    """Return `html` with every /assets/*.{css,js} reference carrying ?v=<hash>."""
    def sub(m):
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        h = _hash(root / url.lstrip("/"))
        if h is None:          # referenced file missing: leave the URL untouched
            return m.group(0)
        return f"{prefix}{url}?v={h}{suffix}"
    return REF.sub(sub, html)


def clear_cache() -> None:
    """Forget hashed file contents (for a long-running process that rebuilds assets)."""
    _cache.clear()
