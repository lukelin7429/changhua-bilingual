#!/usr/bin/env python3
"""Wrap fces (豐洲國小) festival pages with their native topbar from index.html.
fces lives at the root of fces.taiwan-bilingual.org, so URLs resolve to /
(not /schools/<slug>/ like the changhua schools)."""
import re
from pathlib import Path

REPO = Path.home() / "Documents/Claude/repos/fces-bilingual"

# From memory: 太保墨藍#1F3A5F + 赭金#B07D3C
PRIMARY   = "#1F3A5F"
SECONDARY = "#B07D3C"
ACCENT    = "#D89A3C"

# Festival metadata
FEST_LIST = [
    ("new-years-day","🎆","New Year's Day","元旦"),
    ("chinese-new-year","🧧","Lunar New Year","農曆新年"),
    ("lantern-festival","🏮","Lantern Festival","元宵節"),
    ("tomb-sweeping-day","🌳","Tomb-Sweeping Day","清明節"),
    ("easter","🐰","Easter","復活節"),
    ("earth-day","🌏","Earth Day","地球日"),
    ("world-book-day","📚","World Book Day","世界閱讀日"),
    ("mothers-day","💐","Mother's Day","母親節"),
    ("dragon-boat-festival","🐉","Dragon Boat Festival","端午節"),
    ("childrens-day-international","🎈","Children's Day","兒童節"),
    ("fathers-day","👔","Father's Day","父親節"),
    ("teachers-day","🍎","Teachers' Day","教師節"),
    ("mid-autumn-festival","🥮","Mid-Autumn Festival","中秋節"),
    ("halloween","🎃","Halloween","萬聖節"),
    ("thanksgiving","🦃","Thanksgiving","感恩節"),
    ("christmas","🎄","Christmas","聖誕節"),
]
FEST_META = {slug:(e,en,zh) for slug,e,en,zh in FEST_LIST}

def extract_topbar(html):
    m = re.search(r'<div class="topbar">.*?<nav[^>]*>.*?</nav>\s*</div>\s*</div>', html, re.DOTALL)
    return m.group(0) if m else None

def extract_head_styles(html):
    head_m = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL)
    if not head_m: return ""
    return "\n".join(re.findall(r'<style[^>]*>.*?</style>', head_m.group(1), re.DOTALL))

def extract_ext_stylesheets(html):
    head_m = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL)
    if not head_m: return ""
    head = head_m.group(1)
    return "\n".join(
        re.findall(r'<link[^>]+rel="preconnect"[^>]*>', head) +
        re.findall(r'<link[^>]+rel="stylesheet"[^>]*>', head)
    )

def fix_urls(markup):
    """fces lives at /, so relative URLs become /<rel>."""
    def fix(m):
        v = m.group(1)
        if v.startswith(('http://','https://','/','#','mailto:','tel:','javascript:')):
            return m.group(0)
        if not v.strip() or v in ('./','.'):
            return 'href="/"'
        return f'href="/{v.lstrip("./")}"'
    return re.sub(r'href="([^"]*)"', fix, markup)

def make_festivals_active(topbar):
    # Strip all is-active first
    topbar = re.sub(r'\bis-active\b\s*', '', topbar)
    topbar = re.sub(r'class="\s*"', '', topbar)
    # Add is-active to /festivals/ link
    def add_active(m):
        tag = m.group(0)
        if 'class="' in tag:
            return re.sub(r'class="([^"]*)"', r'class="\1 is-active"', tag, count=1)
        return tag.rstrip('>') + ' class="is-active">'
    topbar = re.sub(r'<a[^>]*href="/festivals/"[^>]*>', add_active, topbar, count=1)
    return topbar

def hero_lesson(emoji, en, zh, festival_no):
    return f"""<header class="th-fest-hero">
  <div class="th-fest-hero__inner">
    <div class="th-fest-hero__emoji">{emoji}</div>
    <div>
      <span class="th-fest-hero__eyebrow">Festivals · 節慶英語</span>
      <h1>{en}</h1>
      <div class="th-fest-hero__zh">{zh}</div>
      <div class="th-fest-hero__crumb">
        <a href="/festivals/">← All Festivals · 全部節慶</a>
        &nbsp;&middot;&nbsp; {festival_no}
      </div>
    </div>
  </div>
</header>
"""

def hero_quiz(emoji, en, zh, festival_no):
    return f"""<header class="th-fest-hero">
  <div class="th-fest-hero__inner">
    <div class="th-fest-hero__emoji">{emoji}</div>
    <div>
      <span class="th-fest-hero__eyebrow">Quiz · 小測驗</span>
      <h1>Quiz · {en}</h1>
      <div class="th-fest-hero__zh">{zh} 小測驗</div>
      <div class="th-fest-hero__crumb">
        <a href="../">← Back to lesson · 回講義</a>
        &nbsp;&middot;&nbsp; {festival_no}
      </div>
    </div>
  </div>
</header>
"""

HERO_CSS = f"""<style>
.th-fest-hero{{position:relative;color:#fff;overflow:hidden;min-height:240px;padding:36px 0 32px;display:flex;align-items:center;background:linear-gradient(135deg,{PRIMARY} 0%,{SECONDARY} 100%);}}
@media (min-width:720px){{ .th-fest-hero{{min-height:320px;padding:56px 0 44px;}} }}
.th-fest-hero::after{{content:"";position:absolute;bottom:0;left:0;right:0;height:5px;background:linear-gradient(90deg,{PRIMARY} 0%,{SECONDARY} 50%,{ACCENT} 100%);pointer-events:none;z-index:2;}}
.th-fest-hero__inner{{max-width:1080px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:auto 1fr;gap:32px;align-items:center;position:relative;z-index:1;}}
@media (max-width:680px){{ .th-fest-hero__inner{{grid-template-columns:1fr;gap:16px;}} }}
.th-fest-hero__emoji{{font-size:84px;line-height:1;text-align:center;flex-shrink:0;filter:drop-shadow(0 2px 8px rgba(0,0,0,.35));}}
@media (min-width:720px){{ .th-fest-hero__emoji{{font-size:120px;}} }}
.th-fest-hero__eyebrow{{display:inline-flex;align-items:center;gap:10px;font-size:12px;letter-spacing:.32em;color:{ACCENT};font-weight:700;text-transform:uppercase;margin-bottom:14px;padding:5px 14px;background:rgba(0,0,0,.30);border:1px solid rgba(255,255,255,.20);border-radius:99px;}}
.th-fest-hero h1{{font-family:'Playfair Display','PingFang TC',serif;font-size:clamp(32px,4.8vw,50px);font-weight:700;color:#fff;line-height:1.05;text-shadow:0 2px 6px rgba(0,0,0,.45);}}
.th-fest-hero .th-fest-hero__zh{{font-size:clamp(15px,1.9vw,20px);font-weight:500;letter-spacing:.06em;color:rgba(255,255,255,.92);margin-top:8px;font-family:'PingFang TC',sans-serif;text-shadow:0 1px 3px rgba(0,0,0,.45);}}
.th-fest-hero__crumb{{margin-top:14px;font-size:13.5px;color:rgba(255,255,255,.78);font-family:'PingFang TC',sans-serif;}}
.th-fest-hero__crumb a{{color:{ACCENT};text-decoration:none;border-bottom:1px dashed rgba(255,255,255,.40);}}
.th-fest-hero__crumb a:hover{{color:#fff;}}
</style>
"""

def strip_hub_chrome(html):
    # cb-back-strip (any class variant)
    html = re.sub(r'<div[^>]*class="cb-back-strip[^"]*"[^>]*>.*?</div>\s*', '', html, count=1, flags=re.DOTALL)
    # Standalone <style> for cb-back-strip variants
    html = re.sub(r'<style>\s*\.cb-back-strip[^{]*\{[^}]*\}.*?</style>\s*', '', html, count=1, flags=re.DOTALL)
    # cb-back-link element
    html = re.sub(r'\s*<a\s+id="cb-back-link"[^>]*>\s*<span[^>]*>[^<]*</span>\s*<span[^>]*>[^<]*</span>\s*</a>\s*',
                  '', html, count=1, flags=re.DOTALL)
    # Inline script for cb-back-link or back-link
    html = re.sub(r'\s*<script>\s*\(function\s*\(\s*\)\s*\{[^<]*?cb-back-link[^<]*?\}\s*\)\s*\(\s*\);?\s*</script>\s*',
                  '', html, count=1, flags=re.DOTALL)
    # External schoolbar.js
    html = re.sub(r'<script\s+src="(?:\.\./)+_shared/schoolbar\.js"\s*></script>\s*', '', html)
    html = re.sub(r'<script\s+src="/_shared/schoolbar\.js"\s*></script>\s*', '', html)
    # hub footer
    html = re.sub(r'<footer[^>]*>.*?</footer>\s*', '', html, count=1, flags=re.DOTALL)
    return html

# === main ===
home_html = (REPO / "index.html").read_text()
topbar = extract_topbar(home_html)
if not topbar:
    print("ERROR: no topbar found in fces/index.html"); exit(1)

topbar = fix_urls(topbar)
topbar = make_festivals_active(topbar)
school_styles = extract_head_styles(home_html)
school_links = extract_ext_stylesheets(home_html)

print(f"Wrapping {len(FEST_LIST)} festivals (lesson + quiz) for fces 豐洲國小…\n")
ok = 0
for fslug, emoji, en, zh in FEST_LIST:
    # Lesson
    src = REPO / "festivals" / fslug / "index.html"
    if src.exists():
        h = src.read_text()
        m = re.search(r'<div class="strip__no">(.*?)</div>', h)
        fno = m.group(1).strip() if m else "Festival English Series"
        h = strip_hub_chrome(h)
        h = re.sub(r'<header class="strip">.*?</header>\s*', '', h, count=1, flags=re.DOTALL)
        inject = school_links + "\n" + school_styles + "\n" + HERO_CSS
        h = h.replace('</head>', inject + '\n</head>', 1)
        chrome = topbar + '\n' + hero_lesson(emoji, en, zh, fno)
        h = re.sub(r'<body[^>]*>', lambda mt: mt.group(0) + '\n' + chrome, h, count=1)
        src.write_text(h)
        ok += 1
    # Quiz
    srcq = REPO / "festivals" / fslug / "quiz" / "index.html"
    if srcq.exists():
        h = srcq.read_text()
        m = re.search(r'<div class="head__brand">(.*?)</div>', h)
        fno = m.group(1).strip() if m else "Festival English Series"
        h = strip_hub_chrome(h)
        h = re.sub(r'<header class="head">.*?</header>\s*', '', h, count=1, flags=re.DOTALL)
        h = re.sub(r'<div class="foot">.*?</div>\s*', '', h, count=1, flags=re.DOTALL)
            # Rename quiz outer .wrap to .quiz-wrap (avoids collision with school topbar's internal .wrap)
            h = re.sub(r'\.wrap\{max-width:840px;[^}]*min-height:100vh[^}]*\}', lambda mt: mt.group(0).replace('.wrap', '.quiz-wrap', 1), h, count=1)
            h = re.sub(r'<div class="wrap">(\s*<main class="card")', r'<div class="quiz-wrap">\1', h, count=1)
        inject = school_links + "\n" + school_styles + "\n" + HERO_CSS
        h = h.replace('</head>', inject + '\n</head>', 1)
        chrome = topbar + '\n' + hero_quiz(emoji, en, zh, fno)
        h = re.sub(r'<body[^>]*>', lambda mt: mt.group(0) + '\n' + chrome, h, count=1)
        srcq.write_text(h)
        ok += 1
    print(f"  ✓ {fslug}")

print(f"\nDone: {ok}/{len(FEST_LIST)*2} pages wrapped in-place.")

# Sweep: delete _shared/schoolbar.js if exists
shared = REPO / "festivals" / "_shared"
if shared.exists():
    for f in shared.iterdir():
        if "schoolbar" in f.name:
            f.unlink()
            print(f"  removed {f.relative_to(REPO)}")
    # remove _shared if empty
    if not any(shared.iterdir()):
        shared.rmdir()
        print(f"  removed empty _shared/")
# Sweep: also absolutize assets/ paths so external CSS/JS load from any depth
import re as _re
for f in (REPO / "festivals").rglob("*.html"):
    t = f.read_text()
    t = _re.sub(r'\b(href|src)="assets/', r'\1="/assets/', t)
    f.write_text(t)
print("  also absolutized assets/ paths in wrapped pages")
