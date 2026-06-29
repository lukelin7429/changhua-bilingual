#!/usr/bin/env python3
"""One-time cleanup: remove the shared festival template's leftover second
topbar <nav class="fest-topbar"> (Festival English · Hub/Festivals/Handout/
Quiz) from EVERY school's festival pages. It duplicates each school's own
topbar and links back to the hub.

Safety: a page is only modified if, after removing fest-topbar, it still
contains a primary school nav (tb__nav / subnav / *-topbar / topbar__inner),
so we never leave a page with no navigation.
"""
import glob, re, os
from collections import Counter

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.chdir(REPO)

FEST = re.compile(r'<nav class="fest-topbar">.*?</nav>\s*', re.S)
SCHOOL_NAV = re.compile(r'class="tb__nav"|class="subnav"|class="[a-z0-9_-]*topbar|topbar__inner')

changed, skipped = Counter(), []
for f in glob.glob('schools/*/festivals/**/index.html', recursive=True):
    h = open(f, encoding='utf-8').read()
    if '<nav class="fest-topbar"' not in h:
        continue
    stripped = FEST.sub('', h, count=1)
    # safety: must still have a real school nav after removal
    if not SCHOOL_NAV.search(FEST.sub('', stripped)):
        skipped.append(f); continue
    open(f, 'w', encoding='utf-8').write(stripped)
    changed[f.split('/')[1]] += 1

total = sum(changed.values())
print(f'fest-topbar removed from {total} files across {len(changed)} schools:')
for s, n in sorted(changed.items()):
    print(f'  {s:16} {n}')
if skipped:
    print(f'\n⚠️ skipped (would leave no nav) — {len(skipped)}:')
    for f in skipped: print('   ', f)
