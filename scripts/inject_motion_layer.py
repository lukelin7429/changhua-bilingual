#!/usr/bin/env python3
"""Idempotently add the site-wide motion layer (motion.css/motion.js) to every
Hub page that doesn't already have motion. Skips:
  - schools/  (each school carries its own motion.css/motion.js)
  - pages that already load hub.js (they get reveal from hub.js)
  - pages that already load motion.js (idempotent re-run)
  - _reference/, scripts/, the google site-verification stub
Inserts absolute-path tags: <link> before </head>, <script defer> before </body>.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = '  <link rel="stylesheet" href="/assets/css/motion.css">\n'
JS  = '<script defer src="/assets/js/motion.js"></script>\n'

SKIP_DIRS = ('_reference', 'scripts')
SKIP_FILES = {'google61797ac71119d5f3.html'}

added, skipped_hub, skipped_done, skipped_nohead = [], 0, 0, []

for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    top = rel.split(os.sep)[0]
    if top in SKIP_DIRS:
        dirnames[:] = []
        continue
    for fn in filenames:
        if not fn.endswith('.html') or fn in SKIP_FILES:
            continue
        path = os.path.join(dirpath, fn)
        with open(path, encoding='utf-8') as f:
            html = f.read()
        if '/assets/js/hub.js' in html:
            skipped_hub += 1
            continue
        if '/assets/js/motion.js' in html:
            skipped_done += 1
            continue
        if '</head>' not in html or '</body>' not in html:
            skipped_nohead.append(os.path.relpath(path, ROOT))
            continue
        # insert before the LAST </body> and the first </head>
        html = html.replace('</head>', CSS + '</head>', 1)
        idx = html.rfind('</body>')
        html = html[:idx] + JS + html[idx:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        added.append(os.path.relpath(path, ROOT))

print(f"ADDED motion layer to {len(added)} pages")
print(f"  skipped (already have hub.js): {skipped_hub}")
print(f"  skipped (already have motion.js): {skipped_done}")
if skipped_nohead:
    print(f"  SKIPPED (no </head> or </body>): {len(skipped_nohead)}")
    for p in skipped_nohead: print("    -", p)
