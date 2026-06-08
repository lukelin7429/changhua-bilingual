#!/usr/bin/env python3
"""Generate sitemap.xml for changhua-bilingual.org.

Walks every published index.html and maps it to its clean URL
(dir/index.html -> dir/). Excludes build/tooling/data dirs that are
not public pages. lastmod comes from file mtime. Idempotent.
"""
import os
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://changhua-bilingual.org"

# Directories that are not public, indexable pages.
EXCLUDE_DIRS = {
    ".git", "scripts", "__pycache__", "apps-script", ".claude",
    "data", "node_modules",
}


def url_for(rel_path: str) -> str:
    # rel_path is like "schools/foo/index.html" or "index.html"
    d = os.path.dirname(rel_path)
    if d == "":
        return BASE + "/"
    return f"{BASE}/{d}/"


def main() -> None:
    urls = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # prune excluded dirs in-place
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if "index.html" in filenames:
            full = os.path.join(dirpath, "index.html")
            rel = os.path.relpath(full, ROOT)
            mtime = datetime.date.fromtimestamp(os.path.getmtime(full))
            urls.append((url_for(rel), mtime.isoformat()))

    urls.sort(key=lambda u: u[0])

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        # homepage gets top priority; deeper pages slightly lower
        depth = loc[len(BASE):].strip("/").count("/")
        priority = "1.0" if loc == BASE + "/" else f"{max(0.4, 0.8 - depth * 0.1):.1f}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    out = os.path.join(ROOT, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {out} with {len(urls)} URLs")


if __name__ == "__main__":
    main()
