#!/usr/bin/env python3
"""Backfill self-referencing <link rel="canonical"> into every content page.

Why: tracking params (?from=<school>, ?fbclid=…, ?utm_…) create duplicate URLs
of the same page. Without an explicit canonical, Google reports
"Duplicate without user-selected canonical" and won't index the param'd copies.
A self-referencing canonical on the clean URL tells Google "this clean URL is
the original", so every param'd variant folds into it automatically.

Idempotent. Run from anywhere:  python3 scripts/add_canonical.py [--apply]
Without --apply it does a dry run (lists what it would change, touches nothing).

The same canonical logic lives in build.py's write() so generated index pages
keep their canonical on rebuild — keep the two in sync if you change the rule.
"""

import re
import sys
from pathlib import Path

SITE = "https://changhua-bilingual.org"
ROOT = Path(__file__).resolve().parent.parent

# Files / dirs that are not indexable content pages.
SKIP_FILES = {"google61797ac71119d5f3.html"}  # Search Console verification token
SKIP_DIRS = {"scripts", "__pycache__"}

VIEWPORT_RX = re.compile(r'(<meta\s+name=["\']viewport["\'][^>]*>)', re.I)
HEAD_RX = re.compile(r'(<head[^>]*>)', re.I)
CANONICAL_RX = re.compile(r'rel=["\']canonical["\']', re.I)


def canonical_url(relpath: str) -> str:
    """Map a repo-relative file path to its clean public URL."""
    p = relpath.replace("\\", "/").lstrip("./").lstrip("/")
    if p == "index.html":
        return SITE + "/"
    if p.endswith("/index.html"):
        return SITE + "/" + p[: -len("index.html")]
    return SITE + "/" + p


def insert_canonical(html: str, url: str):
    """Return (new_html, changed). Inserts after viewport meta, else after <head>."""
    if CANONICAL_RX.search(html):
        return html, False
    tag = f'\n  <link rel="canonical" href="{url}">'
    m = VIEWPORT_RX.search(html)
    if m:
        i = m.end()
        return html[:i] + tag + html[i:], True
    m = HEAD_RX.search(html)
    if m:
        i = m.end()
        return html[:i] + tag + html[i:], True
    return html, False  # no <head> → fragment, skip


def main():
    apply = "--apply" in sys.argv
    changed = skipped_have = skipped_nohead = skipped_excluded = 0
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        parts = set(rel.parts)
        if rel.name in SKIP_FILES or parts & SKIP_DIRS:
            skipped_excluded += 1
            continue
        html = path.read_text(encoding="utf-8")
        if CANONICAL_RX.search(html):
            skipped_have += 1
            continue
        url = canonical_url(str(rel))
        new_html, ok = insert_canonical(html, url)
        if not ok:
            skipped_nohead += 1
            continue
        changed += 1
        if apply:
            path.write_text(new_html, encoding="utf-8")
        else:
            print(f"  + {rel}  ->  {url}")

    verb = "Inserted" if apply else "Would insert"
    print(
        f"\n{verb} canonical in {changed} files.  "
        f"already-had={skipped_have}  no-head(fragment)={skipped_nohead}  "
        f"excluded={skipped_excluded}"
    )
    if not apply:
        print("Dry run. Re-run with --apply to write changes.")


if __name__ == "__main__":
    main()
