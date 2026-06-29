#!/usr/bin/env python3
"""Run AFTER scripts/wrap_school_festivals.py chungshan.
Festivals live UNDER Lessons (reached from the Lessons-page card), so the
shared wrapper's auto-added 'Festivals' top-nav item is wrong here. This
rewrites every chungshan festival page's TOPBAR nav back to the canonical
4 items (Home/Principal/Lessons/News) with Lessons active. It only touches
the <nav class="tb__nav"> block, never the festival sub-nav."""
import re, glob, os

ROOT = os.path.dirname(os.path.abspath(__file__))
n = 0
for f in glob.glob(os.path.join(ROOT, 'festivals', '**', 'index.html'), recursive=True):
    h = open(f, encoding='utf-8').read()
    def fix(m):
        nav = m.group(0)
        nav = re.sub(r'<a href="/schools/chungshan/festivals/"[^>]*>Festivals</a>', '', nav)
        if 'lessons/" class="is-active"' not in nav:
            nav = nav.replace('<a href="/schools/chungshan/lessons/">Lessons</a>',
                              '<a href="/schools/chungshan/lessons/" class="is-active">Lessons</a>')
        return nav
    h2 = re.sub(r'<nav class="tb__nav">.*?</nav>', fix, h, count=1, flags=re.S)
    if h2 != h:
        open(f, 'w', encoding='utf-8').write(h2); n += 1
print(f'festival nav fixed: {n} files')
