#!/usr/bin/env python3
"""v2 — wrap hub festivals with each school's NATIVE topbar/head CSS extracted
verbatim from their index.html. Replaces the v1 generic .th-* chrome."""
import re, json, sys
from pathlib import Path

REPO = Path.home() / "Documents/Claude/repos/changhua-bilingual"
HUB_FESTIVALS = REPO / "festivals"
PALETTES = json.loads((REPO / "scripts/_taihe_pilot_palettes.json").read_text())

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

# === Step 1: detect school topbar from index.html ===
TOPBAR_PATTERNS = [
    # chungshan-style ".tb" bar: <div class="tb"><div class="tb__inner">…<nav>…</nav></div></div>
    r'<div class="tb"><div class="tb__inner">.*?</nav>\s*</div>\s*</div>',
    # subnav (dajuang, jianxin, dongshan, etc.)
    r'<nav class="subnav">.*?</nav>',
    # Any "<prefix>-topbar" wrapper div containing a <nav> (matches ymj-topbar,
    # wj-topbar, dcj-topbar, and any future <abbr>-topbar pattern).
    # MUST come before the bare "topbar" patterns below so we win on prefix matches.
    r'<div[^>]*class="[a-z][a-z0-9-]*-topbar[^"]*"[^>]*>.*?<nav[^>]*>.*?</nav>\s*</div>\s*</div>',
    r'<header[^>]*class="[a-z][a-z0-9-]*-topbar[^"]*"[^>]*>.*?</header>',
    # dongfang-style nav (just topbar-nav inside larger wrapper)
    r'<nav class="topbar"[^>]*>.*?</nav>',
    # "topbar" <div> pattern — has nested <nav>
    r'<div\s+class="topbar">.*?<nav[^>]*>.*?</nav>\s*</div>\s*</div>',
    # Tai-He pattern (topbar wrapper)
    r'<div\s+class="topbar"[^>]*>\s*<div class="topbar__inner">.*?</div>\s*</div>',
]

def extract_topbar(html):
    for pat in TOPBAR_PATTERNS:
        m = re.search(pat, html, re.DOTALL)
        if m:
            return m.group(0)
    # Last resort: take the first <nav> with >2 anchor children that has href values referencing pages we'd expect
    nav_matches = re.findall(r'<nav[^>]*>.*?</nav>', html, re.DOTALL)
    for nav in nav_matches:
        anchors = re.findall(r'<a[^>]*href="[^"]*"', nav)
        if len(anchors) >= 3:
            return nav
    return None

def extract_head_styles(html):
    """Return ALL <style>...</style> blocks from <head>."""
    head_m = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL)
    if not head_m: return ""
    head = head_m.group(1)
    styles = re.findall(r'<style[^>]*>.*?</style>', head, re.DOTALL)
    return "\n".join(styles)

def extract_external_stylesheets(html):
    """Return all <link rel="stylesheet" ...> tags from head."""
    head_m = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL)
    if not head_m: return ""
    head = head_m.group(1)
    # match google fonts + external CSS — keep them
    links = re.findall(r'<link[^>]+rel="stylesheet"[^>]*>', head)
    preconns = re.findall(r'<link[^>]+rel="preconnect"[^>]*>', head)
    return "\n".join(preconns + links)

def fix_relative_urls(markup, folder):
    """Rewrite relative hrefs in topbar to absolute /schools/<folder>/… so they
    work from /schools/<folder>/festivals/<festival>/ context."""
    def fix(m):
        val = m.group(1)
        # Skip absolute URLs, anchors, mailto, tel
        if val.startswith(('http://','https://','/','#','mailto:','tel:','javascript:')):
            return m.group(0)
        # Empty href or just ./ → school home
        if not val.strip() or val in ('./', '.'):
            return f'href="/schools/{folder}/"'
        # Strip leading ./ then absolutize
        new_val = f"/schools/{folder}/{val.lstrip('./')}"
        return f'href="{new_val}"'
    return re.sub(r'href="([^"]*)"', fix, markup)

def ensure_festivals_active(topbar_html, folder):
    """1) Strip ANY existing class="is-active" from every <a>
       2) Canonicalize ANY href containing 'festivals' to /schools/<folder>/festivals/
       3) Add is-active to the (now-canonical) Festivals link
       4) If no Festivals link exists at all, append one before </nav>."""
    # 1. Remove ALL is-active classes
    def strip_active(m):
        tag = m.group(0)
        new_tag = re.sub(r'\bis-active\b\s*', '', tag)
        new_tag = re.sub(r'class="\s*"', '', new_tag)
        return new_tag
    topbar_html = re.sub(r'<a[^>]*>', strip_active, topbar_html)

    fest_href = f'/schools/{folder}/festivals/'

    # 2. Canonicalize any href that contains 'festivals' (so old /festivals/?from=… or hub URLs get fixed too)
    def canonicalize(m):
        href = m.group(1)
        if 'festivals' in href.lower():
            return f'href="{fest_href}"'
        return m.group(0)
    topbar_html = re.sub(r'href="([^"]*)"', canonicalize, topbar_html)

    # 3. Set is-active on the canonical festivals link
    if fest_href in topbar_html:
        def add_active(m):
            tag = m.group(0)
            if 'class="' in tag:
                return re.sub(r'class="([^"]*)"', r'class="\1 is-active"', tag, count=1)
            return tag.rstrip('>') + ' class="is-active">'
        topbar_html = re.sub(
            r'<a[^>]*href="' + re.escape(fest_href) + r'"[^>]*>',
            add_active, topbar_html, count=1
        )
    else:
        # 4. Append before </nav>
        new_link = f'<a href="{fest_href}" class="is-active">Festivals</a>'
        topbar_html = re.sub(r'</nav>', new_link + '</nav>', topbar_html, count=1)
    return topbar_html

# Standard festival hero (sits below school topbar; uses school's :root colors via inheritance + opaque-color fallbacks)
def festival_hero(emoji, en, zh, festival_no_text, primary, secondary, accent, folder, mode="lesson"):
    eyebrow = "Festivals · 節慶英語" if mode=="lesson" else "Quiz · 小測驗"
    title = en if mode=="lesson" else f"Quiz · {en}"
    zh_text = zh if mode=="lesson" else f"{zh} 小測驗"
    crumb = (f'<a href="/schools/{folder}/festivals/">← All Festivals · 全部節慶</a>'
             if mode=="lesson"
             else '<a href="../">← Back to lesson · 回講義</a>')
    return f"""<header class="th-fest-hero">
  <div class="th-fest-hero__inner">
    <div class="th-fest-hero__emoji">{emoji}</div>
    <div>
      <span class="th-fest-hero__eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <div class="th-fest-hero__zh">{zh_text}</div>
      <div class="th-fest-hero__crumb">
        {crumb}
        &nbsp;&middot;&nbsp; {festival_no_text}
      </div>
    </div>
  </div>
</header>
"""

def festival_hero_css(primary, secondary, accent):
    return f"""<style>
/* Festival hero — sits below school's native topbar */
.th-fest-hero{{position:relative;color:#fff;overflow:hidden;min-height:240px;padding:36px 0 32px;display:flex;align-items:center;background:linear-gradient(135deg,{primary} 0%,{secondary} 100%);}}
@media (min-width:720px){{ .th-fest-hero{{min-height:320px;padding:56px 0 44px;}} }}
.th-fest-hero::after{{content:"";position:absolute;bottom:0;left:0;right:0;height:5px;background:linear-gradient(90deg,{primary} 0%,{secondary} 50%,{accent} 100%);pointer-events:none;z-index:2;}}
.th-fest-hero__inner{{max-width:1080px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:auto 1fr;gap:32px;align-items:center;position:relative;z-index:1;}}
@media (max-width:680px){{ .th-fest-hero__inner{{grid-template-columns:1fr;gap:16px;}} }}
.th-fest-hero__emoji{{font-size:84px;line-height:1;text-align:center;flex-shrink:0;filter:drop-shadow(0 2px 8px rgba(0,0,0,.35));}}
@media (min-width:720px){{ .th-fest-hero__emoji{{font-size:120px;}} }}
.th-fest-hero__eyebrow{{display:inline-flex;align-items:center;gap:10px;font-size:12px;letter-spacing:.32em;color:{accent};font-weight:700;text-transform:uppercase;margin-bottom:14px;padding:5px 14px;background:rgba(0,0,0,.30);border:1px solid rgba(255,255,255,.20);border-radius:99px;}}
.th-fest-hero h1{{font-family:'Playfair Display','PingFang TC',serif;font-size:clamp(32px,4.8vw,50px);font-weight:700;color:#fff;line-height:1.05;text-shadow:0 2px 6px rgba(0,0,0,.45);}}
.th-fest-hero .th-fest-hero__zh{{font-size:clamp(15px,1.9vw,20px);font-weight:500;letter-spacing:.06em;color:rgba(255,255,255,.92);margin-top:8px;font-family:'PingFang TC',sans-serif;text-shadow:0 1px 3px rgba(0,0,0,.45);}}
.th-fest-hero__crumb{{margin-top:14px;font-size:13.5px;color:rgba(255,255,255,.78);font-family:'PingFang TC',sans-serif;}}
.th-fest-hero__crumb a{{color:{accent};text-decoration:none;border-bottom:1px dashed rgba(255,255,255,.40);}}
.th-fest-hero__crumb a:hover{{color:#fff;}}
</style>
"""

def strip_hub_chrome(html):
    """Remove all hub-injected chrome from a hub festival HTML."""
    # leftover hub second-topbar (Festival English · Hub/Festivals/Handout/Quiz) —
    # duplicates the school's own topbar; drop it (nav stays via school topbar +
    # hero crumb + in-body Quiz/Handout links).
    html = re.sub(r'<nav class="fest-topbar">.*?</nav>\s*', '', html, count=1, flags=re.DOTALL)
    html = re.sub(r'<div[^>]*class="cb-back-strip[^"]*"[^>]*>.*?</div>\s*', '', html, count=1, flags=re.DOTALL)
    html = re.sub(r'<style>\s*\.cb-back-strip-fallback.*?</style>\s*', '', html, count=1, flags=re.DOTALL)
    html = re.sub(r'<script\s+src="(?:\.\./)+_shared/schoolbar\.js"\s*></script>\s*', '', html)
    html = re.sub(r'<footer[^>]*>.*?</footer>\s*', '', html, count=1, flags=re.DOTALL)
    # cb-back-link element + script
    html = re.sub(
        r'\s*<a\s+id="cb-back-link"[^>]*>\s*<span[^>]*>[^<]*</span>\s*<span[^>]*>[^<]*</span>\s*</a>\s*',
        '', html, count=1, flags=re.DOTALL)
    html = re.sub(
        r'\s*<script>\s*\(function\s*\(\s*\)\s*\{[^<]*?cb-back-link[^<]*?\}\s*\)\s*\(\s*\);?\s*</script>\s*',
        '', html, count=1, flags=re.DOTALL)
    return html

# === MAIN: process one school ===
def wrap_for_school(slug, meta):
    folder = meta["folder"]
    school_html = (REPO / "schools" / folder / "index.html").read_text()
    topbar = extract_topbar(school_html)
    if not topbar:
        print(f"  ✗ {slug}: no topbar found, skipping")
        return 0
    topbar = fix_relative_urls(topbar, folder)
    topbar = ensure_festivals_active(topbar, folder)

    school_styles = extract_head_styles(school_html)
    school_ext_links = extract_external_stylesheets(school_html)
    # If the school ships a topbar-only stylesheet, use it here so the full
    # site CSS doesn't override the festival template's .wrap/section/.sec__* .
    if (REPO / "schools" / folder / "topbar.css").exists():
        school_ext_links = school_ext_links.replace(
            f"/schools/{folder}/style.css", f"/schools/{folder}/topbar.css")

    # Hero CSS uses the palette for festival-specific banner
    hero_css = festival_hero_css(meta["primary"], meta["secondary"], meta["accent"])

    primary, secondary, accent = meta["primary"], meta["secondary"], meta["accent"]

    files = 0
    for fslug, emoji, en, zh in FEST_LIST:
        # ---- Lesson ----
        src = HUB_FESTIVALS / fslug / "index.html"
        if src.exists():
            h = src.read_text()
            m = re.search(r'<div class="strip__no">(.*?)</div>', h)
            fno = m.group(1).strip() if m else "Festival English Series"
            h = strip_hub_chrome(h)
            h = re.sub(r'<header class="strip">.*?</header>\s*', '', h, count=1, flags=re.DOTALL)
            # Inject school styles+ext links + hero css BEFORE </head>
            inject = school_ext_links + "\n" + school_styles + "\n" + hero_css
            h = h.replace('</head>', inject + "\n</head>", 1)
            # Inject school topbar + festival hero after <body>
            hero = festival_hero(emoji, en, zh, fno, primary, secondary, accent, folder, "lesson")
            h = re.sub(r'<body[^>]*>', lambda mt: mt.group(0) + '\n' + topbar + '\n' + hero, h, count=1)
            dst = REPO / "schools" / folder / "festivals" / fslug / "index.html"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(h)
            files += 1
        # ---- Quiz ----
        srcq = HUB_FESTIVALS / fslug / "quiz" / "index.html"
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
            inject = school_ext_links + "\n" + school_styles + "\n" + hero_css
            h = h.replace('</head>', inject + "\n</head>", 1)
            hero = festival_hero(emoji, en, zh, fno, primary, secondary, accent, folder, "quiz")
            h = re.sub(r'<body[^>]*>', lambda mt: mt.group(0) + '\n' + topbar + '\n' + hero, h, count=1)
            dst = REPO / "schools" / folder / "festivals" / fslug / "quiz" / "index.html"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(h)
            files += 1
    return files

def build_landing_for_school(slug, meta):
    folder = meta["folder"]
    school_html = (REPO / "schools" / folder / "index.html").read_text()
    topbar = extract_topbar(school_html)
    if not topbar:
        return False
    topbar = fix_relative_urls(topbar, folder)
    topbar = ensure_festivals_active(topbar, folder)
    school_styles = extract_head_styles(school_html)
    school_ext_links = extract_external_stylesheets(school_html)
    # If the school ships a topbar-only stylesheet, use it here so the full
    # site CSS doesn't override the festival template's .wrap/section/.sec__* .
    if (REPO / "schools" / folder / "topbar.css").exists():
        school_ext_links = school_ext_links.replace(
            f"/schools/{folder}/style.css", f"/schools/{folder}/topbar.css")
    primary, secondary, accent = meta["primary"], meta["secondary"], meta["accent"]
    hero_css = festival_hero_css(primary, secondary, accent)
    landing_hero = f"""<header class="th-fest-hero">
  <div class="th-fest-hero__inner">
    <div class="th-fest-hero__emoji">🎊</div>
    <div>
      <span class="th-fest-hero__eyebrow">Festivals · 節慶英語</span>
      <h1>Festivals Around the World</h1>
      <div class="th-fest-hero__zh">世界節慶英語 · {meta['zh']}</div>
      <div class="th-fest-hero__crumb">Every festival is a doorway into another culture · 每一個節慶，都是通往另一種文化的門</div>
    </div>
  </div>
</header>"""
    cards = [
        f'      <a class="th-fcard" href="/schools/{folder}/festivals/{fslug}/"><div class="em">{emoji}</div><div class="t">{en}</div><div class="z">{zh}</div><div class="go">Explore →</div></a>'
        for fslug, emoji, en, zh in FEST_LIST
    ]
    grid_css = f"""<style>
.th-fest-section{{padding:56px 24px;background:#fff;}}
@media (min-width:720px){{ .th-fest-section{{padding:80px 24px;}} }}
.th-fest-section .wrap{{max-width:1080px;margin:0 auto;}}
.th-fest-sec-head{{text-align:center;margin-bottom:40px;}}
.th-fest-sec-head .eyebrow{{display:inline-block;font-size:14px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;margin-bottom:10px;color:{secondary};}}
.th-fest-sec-head h2{{font-family:'Playfair Display',serif;font-size:clamp(30px,4.4vw,46px);font-weight:700;color:{primary};line-height:1.18;}}
.th-fest-sec-head h2 .zh{{font-family:'PingFang TC',sans-serif;font-size:19px;color:#5a606e;font-weight:500;display:block;margin-top:6px;letter-spacing:.04em;}}
.th-fest-sec-head .lede{{color:#5a606e;font-size:18px;max-width:680px;margin:16px auto 0;line-height:1.7;}}
.th-fgrid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;}}
@media (min-width:680px){{ .th-fgrid{{grid-template-columns:repeat(3,1fr);gap:22px;}} }}
@media (min-width:1000px){{ .th-fgrid{{grid-template-columns:repeat(4,1fr);}} }}
.th-fcard{{display:flex;flex-direction:column;align-items:center;text-align:center;background:#fff;border:1px solid #ebe5d6;border-radius:20px;padding:30px 18px;box-shadow:0 6px 16px -6px rgba(0,0,0,.15);transition:transform .2s, box-shadow .2s;color:inherit;text-decoration:none;}}
.th-fcard:hover{{transform:translateY(-5px);box-shadow:0 14px 32px -12px rgba(0,0,0,.25);}}
.th-fcard .em{{font-size:54px;line-height:1;transition:transform .25s;}}
.th-fcard:hover .em{{transform:scale(1.1) rotate(-4deg);}}
.th-fcard .t{{font-family:'Playfair Display',serif;font-size:21px;font-weight:700;color:{primary};margin-top:12px;line-height:1.15;}}
.th-fcard .z{{font-family:'PingFang TC',sans-serif;font-size:16px;color:#5a606e;margin-top:4px;}}
.th-fcard .go{{margin-top:12px;font-size:14px;font-weight:700;color:{secondary};font-family:'Playfair Display',serif;letter-spacing:.4px;}}
</style>"""
    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Festivals · 節慶英語 — {meta['name']}</title>
<meta name="description" content="Celebrate the world's festivals in English with {meta['name']} — Christmas, Lunar New Year, Mid-Autumn, Halloween and more, from the Changhua Bilingual Hub.">
{school_ext_links}
{school_styles}
{hero_css}
{grid_css}
<style>body{{background:#fff;color:#1f2530;font-family:'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif;font-size:20px;line-height:1.65;-webkit-font-smoothing:antialiased;margin:0;padding:0;}}</style>
<script defer src="/analytics.js"></script>
</head>
<body>
{topbar}
{landing_hero}
<section class="th-fest-section">
  <div class="wrap">
    <div class="th-fest-sec-head">
      <span class="eyebrow">Bilingual Festival Learning</span>
      <h2>Learn the world, one festival at a time<span class="zh">用節慶認識世界</span></h2>
      <p class="lede">From Lunar New Year to Christmas, each festival opens a window into another culture's customs, foods and stories. Sixteen bilingual festival lessons — produced and shared across the Changhua Bilingual Hub.</p>
    </div>
    <div class="th-fgrid">
{chr(10).join(cards)}
    </div>
  </div>
</section>
</body>
</html>
"""
    dst = REPO / "schools" / folder / "festivals" / "index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html)
    return True

# === MAIN — all schools except taihe ===
if sys.argv[1:] == ["--all"]:
    targets = list(PALETTES.keys())
elif sys.argv[1:]:
    targets = sys.argv[1:]
else:
    targets = ["dajuang"]

total_files = 0
ok_schools = 0
for slug in targets:
    if slug not in PALETTES:
        print(f"  ✗ {slug} not in palettes"); continue
    meta = PALETTES[slug]
    n = wrap_for_school(slug, meta)
    landing_ok = build_landing_for_school(slug, meta)
    total = n + (1 if landing_ok else 0)
    print(f"  ✓ {slug:18} {meta['zh']:14} ({total} pages: 32 lesson+quiz, {'+1 landing' if landing_ok else 'NO landing'})")
    total_files += total
    if n > 0: ok_schools += 1
print(f"\nDone: {ok_schools}/{len(targets)} schools, {total_files} files.")
