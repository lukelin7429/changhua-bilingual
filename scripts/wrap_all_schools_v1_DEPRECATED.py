#!/usr/bin/env python3
"""Batch-wrap 16 hub festivals (lesson + quiz) + generate Festivals landing
for every hub-platform school. Uses each school's palette+logo for the chrome
but keeps a uniform .th-* chrome structure (same as Taihe pilot)."""
import json, re, shutil
from pathlib import Path

REPO = Path.home() / "Documents/Claude/repos/changhua-bilingual"
HUB_FESTIVALS = REPO / "festivals"
PALETTES = json.loads((REPO / "scripts/_taihe_pilot_palettes.json").read_text())

# Festival metadata — emoji, EN name, ZH name (year-cycle order)
FEST_LIST = [
    ("new-years-day",   "🎆", "New Year's Day",    "元旦"),
    ("chinese-new-year","🧧", "Lunar New Year",    "農曆新年"),
    ("lantern-festival","🏮", "Lantern Festival",  "元宵節"),
    ("tomb-sweeping-day","🌳","Tomb-Sweeping Day", "清明節"),
    ("easter",          "🐰", "Easter",            "復活節"),
    ("earth-day",       "🌏", "Earth Day",         "地球日"),
    ("world-book-day",  "📚", "World Book Day",    "世界閱讀日"),
    ("mothers-day",     "💐", "Mother's Day",      "母親節"),
    ("dragon-boat-festival","🐉","Dragon Boat Festival","端午節"),
    ("childrens-day-international","🎈","Children's Day","兒童節"),
    ("fathers-day",     "👔", "Father's Day",      "父親節"),
    ("teachers-day",    "🍎", "Teachers' Day",     "教師節"),
    ("mid-autumn-festival","🥮","Mid-Autumn Festival","中秋節"),
    ("halloween",       "🎃", "Halloween",         "萬聖節"),
    ("thanksgiving",    "🦃", "Thanksgiving",      "感恩節"),
    ("christmas",       "🎄", "Christmas",         "聖誕節"),
]
FEST_META = {slug: (emoji, en, zh) for slug, emoji, en, zh in FEST_LIST}

LOGO_CANDIDATES = [
    "photos/logo.png", "photos/logo.jpg", "photos/logo.svg",
    "favicon-512.png", "favicon-180.png", "favicon-192.png",
    "photos/crest-180.png", "photos/crest-192.png",
]

def resolve_logo(folder):
    for cand in LOGO_CANDIDATES:
        p = REPO / "schools" / folder / cand
        if p.exists():
            return f"/schools/{folder}/{cand}"
    return None

def chrome_css(primary, secondary, accent, logo_url):
    """Generate .th-* CSS with school's palette. Self-contained (no var() so it
    can't clash with hub festival CSS variables)."""
    has_logo = logo_url is not None
    return f"""
<style>
/* === School chrome — namespaced .th-* to avoid clashing with hub festival CSS === */
.th-topbar{{background:rgba(255,255,255,.96);border-bottom:1px solid #ebe5d6;padding:14px 0;position:sticky;top:0;z-index:50;backdrop-filter:blur(8px);}}
.th-topbar__inner{{max-width:1080px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;gap:18px;}}
.th-topbar__brand{{display:flex;align-items:center;gap:12px;text-decoration:none;}}
.th-topbar__logo{{width:46px;height:46px;border-radius:50%;background:#fff;object-fit:contain;padding:3px;box-shadow:0 4px 10px -2px rgba(0,0,0,.18);border:1px solid #ebe5d6;display:block;}}
.th-topbar__badge{{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,{primary} 0%,{secondary} 100%);color:#fff;font-family:'Playfair Display',serif;font-size:21px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 10px -2px rgba(0,0,0,.18);}}
.th-topbar__name{{font-family:'Playfair Display','PingFang TC',serif;font-size:18px;font-weight:700;color:{primary};line-height:1.1;}}
.th-topbar__name small{{display:block;font-family:'PingFang TC',sans-serif;font-size:12px;font-weight:500;color:#5a606e;margin-top:3px;letter-spacing:.04em;}}
.th-topbar__nav{{display:flex;gap:22px;flex-wrap:wrap;justify-content:flex-end;}}
.th-topbar__nav a{{color:#1f2530;font-size:14.5px;font-weight:500;letter-spacing:.04em;text-decoration:none;transition:color .2s;}}
.th-topbar__nav a:hover{{color:{primary};}}
.th-topbar__nav a.is-active{{color:{primary};font-weight:700;}}
@media (max-width:620px){{
  .th-topbar__inner{{flex-direction:column;align-items:flex-start;gap:10px;}}
  .th-topbar__nav{{gap:14px;justify-content:flex-start;}}
  .th-topbar__nav a{{font-size:13.5px;}}
}}

.th-hero{{position:relative;color:#fff;overflow:hidden;min-height:260px;padding:44px 0 36px;display:flex;align-items:center;background:linear-gradient(135deg,{primary} 0%,{secondary} 100%);}}
@media (min-width:720px){{ .th-hero{{min-height:340px;padding:64px 0 48px;}} }}
.th-hero::after{{content:"";position:absolute;bottom:0;left:0;right:0;height:5px;background:linear-gradient(90deg,{primary} 0%,{secondary} 50%,{accent} 100%);pointer-events:none;z-index:2;}}
.th-hero__inner{{max-width:1080px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:auto 1fr;gap:36px;align-items:center;position:relative;z-index:1;}}
@media (max-width:680px){{ .th-hero__inner{{grid-template-columns:1fr;gap:18px;}} }}
.th-hero__emoji{{font-size:96px;line-height:1;text-align:center;flex-shrink:0;filter:drop-shadow(0 2px 8px rgba(0,0,0,.35));}}
@media (min-width:720px){{ .th-hero__emoji{{font-size:128px;}} }}
.th-hero__eyebrow{{display:inline-flex;align-items:center;gap:10px;font-size:12px;letter-spacing:.32em;color:{accent};font-weight:700;text-transform:uppercase;margin-bottom:14px;padding:5px 14px;background:rgba(0,0,0,.30);border:1px solid rgba(255,255,255,.20);border-radius:99px;}}
.th-hero h1{{font-family:'Playfair Display','PingFang TC',serif;font-size:clamp(34px,5vw,52px);font-weight:700;color:#fff;line-height:1.05;letter-spacing:.005em;text-shadow:0 2px 6px rgba(0,0,0,.45);}}
.th-hero .th-h1-zh{{font-size:clamp(16px,2vw,21px);font-weight:500;letter-spacing:.06em;color:rgba(255,255,255,.92);margin-top:8px;font-family:'PingFang TC',sans-serif;text-shadow:0 1px 3px rgba(0,0,0,.45);}}
.th-hero__crumb{{margin-top:14px;font-size:13.5px;color:rgba(255,255,255,.78);font-family:'PingFang TC',sans-serif;}}
.th-hero__crumb a{{color:{accent};text-decoration:none;border-bottom:1px dashed rgba(255,255,255,.40);}}
.th-hero__crumb a:hover{{color:#fff;}}

.th-footer{{background:{primary};color:#fff;padding:48px 0 32px;margin-top:48px;}}
.th-footer__inner{{max-width:1080px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:1fr;gap:30px;}}
@media (min-width:760px){{ .th-footer__inner{{grid-template-columns:1.4fr 1fr 1fr;gap:40px;}} }}
.th-footer__brand{{display:flex;align-items:flex-start;gap:14px;}}
.th-footer__brand img{{width:60px;height:60px;border-radius:50%;background:#fff;object-fit:contain;padding:5px;border:1px solid rgba(255,255,255,.18);box-shadow:0 6px 16px -4px rgba(0,0,0,.30);}}
.th-footer__brand .badge{{width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#fff 0%,rgba(255,255,255,.7) 100%);color:{primary};font-family:'Playfair Display',serif;font-size:28px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.th-footer__brand h4{{font-family:'Playfair Display',serif;font-size:22px;font-weight:700;color:#fff;line-height:1.15;}}
.th-footer__brand .name-zh{{font-size:14px;color:rgba(255,255,255,.78);font-weight:500;margin-top:3px;}}
.th-footer__col h5{{font-family:'Playfair Display',serif;font-size:13px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:{accent};margin-bottom:14px;}}
.th-footer__col ul{{list-style:none;padding:0;margin:0;}}
.th-footer__col li{{margin-bottom:8px;font-size:15px;color:rgba(255,255,255,.85);}}
.th-footer__col a{{color:rgba(255,255,255,.85);text-decoration:none;border-bottom:1px dashed rgba(255,255,255,.30);transition:color .2s;}}
.th-footer__col a:hover{{color:{accent};}}
.th-footer__bottom{{max-width:1080px;margin:32px auto 0;padding:18px 24px 0;border-top:1px solid rgba(255,255,255,.16);font-size:13px;color:rgba(255,255,255,.6);text-align:center;line-height:1.7;}}
.th-footer__bottom a{{color:{accent};text-decoration:none;}}

/* Landing-page extras */
.th-landing-section{{padding:56px 24px;background:#fff;}}
@media (min-width:720px){{ .th-landing-section{{padding:80px 24px;}} }}
.th-landing-section .wrap{{max-width:1080px;margin:0 auto;}}
.th-sec-head{{text-align:center;margin-bottom:40px;}}
.th-sec-head .eyebrow{{display:inline-block;font-size:14px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;margin-bottom:10px;color:{secondary};}}
.th-sec-head h2{{font-family:'Playfair Display',serif;font-size:clamp(30px,4.4vw,46px);font-weight:700;color:{primary};line-height:1.18;}}
.th-sec-head h2 .zh{{font-family:'PingFang TC',sans-serif;font-size:19px;color:#5a606e;font-weight:500;display:block;margin-top:6px;letter-spacing:.04em;}}
.th-sec-head .lede{{color:#5a606e;font-size:18px;max-width:680px;margin:16px auto 0;line-height:1.7;}}
.fgrid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;}}
@media (min-width:680px){{ .fgrid{{grid-template-columns:repeat(3,1fr);gap:22px;}} }}
@media (min-width:1000px){{ .fgrid{{grid-template-columns:repeat(4,1fr);}} }}
.fcard{{display:flex;flex-direction:column;align-items:center;text-align:center;background:#fff;border:1px solid #ebe5d6;border-radius:20px;padding:30px 18px;box-shadow:0 6px 16px -6px rgba(0,0,0,.15);transition:transform .2s, box-shadow .2s;color:inherit;text-decoration:none;}}
.fcard:hover{{transform:translateY(-5px);box-shadow:0 14px 32px -12px rgba(0,0,0,.25);}}
.fcard .em{{font-size:54px;line-height:1;transition:transform .25s;}}
.fcard:hover .em{{transform:scale(1.1) rotate(-4deg);}}
.fcard .t{{font-family:'Playfair Display',serif;font-size:21px;font-weight:700;color:{primary};margin-top:12px;line-height:1.15;}}
.fcard .z{{font-family:'PingFang TC',sans-serif;font-size:16px;color:#5a606e;margin-top:4px;}}
.fcard .go{{margin-top:12px;font-size:14px;font-weight:700;color:{secondary};font-family:'Playfair Display',serif;letter-spacing:.4px;}}

/* Base body on landing page only */
.th-landing body{{background:#fff;color:#1f2530;font-family:'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif;font-size:20px;line-height:1.65;-webkit-font-smoothing:antialiased;}}
</style>
"""

def school_initial(name):
    # First letter of English name for the text badge fallback
    return name.strip()[0].upper() if name else "?"

def topbar(slug, folder, name_en, name_zh, logo_url, active="festivals"):
    if logo_url:
        brand = f'<img class="th-topbar__logo" src="{logo_url}" alt="{name_en} logo">'
    else:
        brand = f'<div class="th-topbar__badge">{school_initial(name_en)}</div>'
    nav_items = [
        ("Home",       f"/schools/{folder}/"),
        ("Principal",  f"/schools/{folder}/principal/"),
        ("Lessons",    f"/schools/{folder}/lessons/"),
        ("News",       f"/schools/{folder}/news/"),
        ("Festivals",  f"/schools/{folder}/festivals/"),
    ]
    nav_html = "\n      ".join(
        f'<a href="{url}"{" class=\"is-active\"" if label.lower()==active.lower() else ""}>{label}</a>'
        for label, url in nav_items
    )
    return f"""<div class="th-topbar">
  <div class="th-topbar__inner">
    <a class="th-topbar__brand" href="/schools/{folder}/">
      {brand}
      <div class="th-topbar__name">{name_en}<small>{name_zh}</small></div>
    </a>
    <nav class="th-topbar__nav">
      {nav_html}
    </nav>
  </div>
</div>
"""

def hero_lesson(emoji, en, zh, festival_no_text, folder):
    return f"""<header class="th-hero">
  <div class="th-hero__inner">
    <div class="th-hero__emoji">{emoji}</div>
    <div>
      <span class="th-hero__eyebrow">Festivals · 節慶英語</span>
      <h1>{en}</h1>
      <div class="th-h1-zh">{zh}</div>
      <div class="th-hero__crumb">
        <a href="/schools/{folder}/festivals/">← All Festivals · 全部節慶</a>
        &nbsp;&middot;&nbsp; {festival_no_text}
      </div>
    </div>
  </div>
</header>
"""

def hero_quiz(emoji, en, zh, festival_no_text):
    return f"""<header class="th-hero">
  <div class="th-hero__inner">
    <div class="th-hero__emoji">{emoji}</div>
    <div>
      <span class="th-hero__eyebrow">Quiz · 小測驗</span>
      <h1>Quiz · {en}</h1>
      <div class="th-h1-zh">{zh} 小測驗</div>
      <div class="th-hero__crumb">
        <a href="../">← Back to lesson · 回講義</a>
        &nbsp;&middot;&nbsp; {festival_no_text}
      </div>
    </div>
  </div>
</header>
"""

def hero_landing(name_en, name_zh):
    return f"""<header class="th-hero">
  <div class="th-hero__inner">
    <div class="th-hero__emoji">🎊</div>
    <div>
      <span class="th-hero__eyebrow">Festivals · 節慶英語</span>
      <h1>Festivals Around the World</h1>
      <div class="th-h1-zh">世界節慶英語 · {name_zh}</div>
      <div class="th-hero__crumb">Every festival is a doorway into another culture · 每一個節慶，都是通往另一種文化的門</div>
    </div>
  </div>
</header>
"""

def footer(folder, name_en, name_zh, logo_url):
    if logo_url:
        brand_img = f'<img src="{logo_url}" alt="{name_en} logo">'
    else:
        brand_img = f'<div class="badge">{school_initial(name_en)}</div>'
    return f"""<footer class="th-footer">
  <div class="th-footer__inner">
    <div class="th-footer__brand">
      {brand_img}
      <div>
        <h4>{name_en}</h4>
        <div class="name-zh">{name_zh}</div>
      </div>
    </div>
    <div class="th-footer__col"><h5>This Site</h5><ul>
      <li><a href="/schools/{folder}/">Home</a></li>
      <li><a href="/schools/{folder}/principal/">Principal</a></li>
      <li><a href="/schools/{folder}/lessons/">Lessons</a></li>
      <li><a href="/schools/{folder}/news/">News</a></li>
      <li><a href="/schools/{folder}/festivals/">Festivals</a></li>
    </ul></div>
    <div class="th-footer__col"><h5>Related</h5><ul>
      <li><a href="https://changhua-bilingual.org/" target="_blank" rel="noopener">Changhua Bilingual Hub</a></li>
      <li><a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect 人師教育協會</a></li>
    </ul></div>
  </div>
  <div class="th-footer__bottom">
    &copy; {name_zh} &middot; {name_en} &nbsp;&middot;&nbsp;
    Bilingual website by My Culture Connect 人師教育協會 &nbsp;&middot;&nbsp;
    Part of the <a href="https://changhua-bilingual.org/" target="_blank" rel="noopener">Changhua Bilingual Hub</a>
  </div>
</footer>
"""

def strip_common(html):
    html = re.sub(r'<div[^>]*class="cb-back-strip[^"]*"[^>]*>.*?</div>\s*', '', html, count=1, flags=re.DOTALL)
    html = re.sub(r'<style>\s*\.cb-back-strip-fallback.*?</style>\s*', '', html, count=1, flags=re.DOTALL)
    html = re.sub(r'<script\s+src="(?:\.\./)+_shared/schoolbar\.js"\s*></script>\s*', '', html)
    html = re.sub(r'<footer[^>]*>.*?</footer>\s*', '', html, count=1, flags=re.DOTALL)
    return html

def inject_chrome(html, school_css, school_topbar, school_hero, school_footer):
    html = html.replace('</head>', school_css + '\n</head>', 1)
    chrome = school_topbar + school_hero
    html = re.sub(r'<body[^>]*>', lambda m: m.group(0) + '\n' + chrome, html, count=1)
    html = html.replace('</body>', school_footer + '\n</body>', 1)
    return html

def wrap_lesson_for(slug, festival_slug, school_meta):
    src = HUB_FESTIVALS / festival_slug / "index.html"
    if not src.exists(): return False
    html = src.read_text()
    emoji, en, zh = FEST_META[festival_slug]
    m = re.search(r'<div class="strip__no">(.*?)</div>', html)
    fno = m.group(1).strip() if m else "Festival English Series"
    html = strip_common(html)
    html = re.sub(r'<header class="strip">.*?</header>\s*', '', html, count=1, flags=re.DOTALL)
    folder = school_meta["folder"]
    css = chrome_css(school_meta["primary"], school_meta["secondary"], school_meta["accent"], school_meta["logo_url"])
    tb = topbar(slug, folder, school_meta["name"], school_meta["zh"], school_meta["logo_url"])
    he = hero_lesson(emoji, en, zh, fno, folder)
    ft = footer(folder, school_meta["name"], school_meta["zh"], school_meta["logo_url"])
    html = inject_chrome(html, css, tb, he, ft)
    dst = REPO / "schools" / folder / "festivals" / festival_slug / "index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html)
    return True

def wrap_quiz_for(slug, festival_slug, school_meta):
    src = HUB_FESTIVALS / festival_slug / "quiz" / "index.html"
    if not src.exists(): return False
    html = src.read_text()
    emoji, en, zh = FEST_META[festival_slug]
    m = re.search(r'<div class="head__brand">(.*?)</div>', html)
    fno = m.group(1).strip() if m else "Festival English Series"
    html = strip_common(html)
    html = re.sub(r'<header class="head">.*?</header>\s*', '', html, count=1, flags=re.DOTALL)
    html = re.sub(r'<div class="foot">.*?</div>\s*', '', html, count=1, flags=re.DOTALL)
    folder = school_meta["folder"]
    css = chrome_css(school_meta["primary"], school_meta["secondary"], school_meta["accent"], school_meta["logo_url"])
    tb = topbar(slug, folder, school_meta["name"], school_meta["zh"], school_meta["logo_url"])
    he = hero_quiz(emoji, en, zh, fno)
    ft = footer(folder, school_meta["name"], school_meta["zh"], school_meta["logo_url"])
    html = inject_chrome(html, css, tb, he, ft)
    dst = REPO / "schools" / folder / "festivals" / festival_slug / "quiz" / "index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html)
    return True

def build_landing(slug, school_meta):
    folder = school_meta["folder"]
    css = chrome_css(school_meta["primary"], school_meta["secondary"], school_meta["accent"], school_meta["logo_url"])
    tb = topbar(slug, folder, school_meta["name"], school_meta["zh"], school_meta["logo_url"])
    he = hero_landing(school_meta["name"], school_meta["zh"])
    ft = footer(folder, school_meta["name"], school_meta["zh"], school_meta["logo_url"])
    cards = []
    for fslug, emoji, en, zh in FEST_LIST:
        cards.append(f'      <a class="fcard" href="/schools/{folder}/festivals/{fslug}/"><div class="em">{emoji}</div><div class="t">{en}</div><div class="z">{zh}</div><div class="go">Explore →</div></a>')
    cards_html = "\n".join(cards)
    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Festivals · 節慶英語 — {school_meta['name']}</title>
<meta name="description" content="Celebrate the world's festivals in English with {school_meta['name']} — Christmas, Lunar New Year, Mid-Autumn, Halloween and more, from the Changhua Bilingual Hub.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
{css}
<style>body{{background:#fff;color:#1f2530;font-family:'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif;font-size:20px;line-height:1.65;-webkit-font-smoothing:antialiased;margin:0;padding:0;}}</style>
<script defer src="/analytics.js"></script>
</head>
<body>
{tb}
{he}
<section class="th-landing-section">
  <div class="wrap">
    <div class="th-sec-head">
      <span class="eyebrow">Bilingual Festival Learning</span>
      <h2>Learn the world, one festival at a time<span class="zh">用節慶認識世界</span></h2>
      <p class="lede">From Lunar New Year to Christmas, each festival opens a window into another culture's customs, foods and stories. Sixteen bilingual festival lessons — produced and shared across the Changhua Bilingual Hub.</p>
    </div>
    <div class="fgrid">
{cards_html}
    </div>
  </div>
</section>
{ft}
</body>
</html>
"""
    dst = REPO / "schools" / folder / "festivals" / "index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html)
    return True

# === MAIN ===
SKIP_SCHOOLS = {"taihe"}  # Taihe pilot is already done with its own style.css—don't overwrite

# Backup mingli's existing festivals page in case its custom content matters
mingli_backup = REPO / "scripts/_mingli_festivals_backup.html"
mingli_orig = REPO / "schools/mingli/festivals/index.html"
if mingli_orig.exists() and not mingli_backup.exists():
    mingli_backup.parent.mkdir(exist_ok=True)
    shutil.copy(mingli_orig, mingli_backup)
    print(f"Backed up mingli festivals → {mingli_backup.relative_to(REPO)}\n")

ok_schools = 0
total_files = 0
for slug, meta in PALETTES.items():
    if slug in SKIP_SCHOOLS:
        print(f"  ⊘ {slug} (skipped — pilot, owns its own style.css)")
        continue
    folder = meta["folder"]
    logo_url = resolve_logo(folder)
    school_meta = {**meta, "logo_url": logo_url}
    files = 0
    if build_landing(slug, school_meta): files += 1
    for fslug, _, _, _ in FEST_LIST:
        if wrap_lesson_for(slug, fslug, school_meta): files += 1
        if wrap_quiz_for(slug, fslug, school_meta): files += 1
    total_files += files
    ok_schools += 1
    logo_status = "with logo" if logo_url else "TEXT BADGE"
    print(f"  ✓ {slug:18} {meta['zh']:14} ({files} files, {logo_status})")

print(f"\nDone: {ok_schools} schools, {total_files} files generated.")
