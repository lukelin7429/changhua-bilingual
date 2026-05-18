#!/usr/bin/env python3
"""Build script for the Changhua Bilingual Hub.

Reads YAML in data/, regenerates:
  /index.html
  /schools/index.html
  /fets/index.html
  /resources/index.html

Workflow: edit YAML → run `python3 build.py` → git commit & push.
"""

import csv
import json
import re
import sys
from pathlib import Path

import yaml

YT_ID_RX = re.compile(r"(?:v=|/shorts/|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})")

sys.path.insert(0, str(Path(__file__).parent / "data"))
from sdgs_content import SDG_CONTENT  # noqa: E402

ROOT = Path(__file__).parent

SECTIONS = [
    ("/", "Home"),
    ("/schools/", "Schools"),
    ("/fets/", "FETs"),
    ("/word-of-the-day/", "Word of the Day"),
    ("/resources/", "Resources"),
]


def load_yaml(name):
    with open(ROOT / "data" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def nav_html(current_path):
    items = []
    for href, label in SECTIONS:
        attr = ' aria-current="page"' if href == current_path else ""
        items.append(f'<li><a class="hub-nav-link" href="{href}"{attr}>{label}</a></li>')
    return f"""
<header class="hub-nav" role="banner">
  <div class="hub-nav-inner">
    <a class="hub-brand" href="/">
      <img class="hub-brand-icon" src="/assets/logo/icon-180.png" alt="" width="40" height="40">
      <span class="hub-brand-wordmark">
        Changhua Bilingual Hub
        <small>彰化雙語資源網</small>
      </span>
    </a>
    <button class="hub-nav-toggle" aria-label="Toggle menu" aria-expanded="false">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
    </button>
    <nav aria-label="Primary">
      <ul class="hub-nav-list">{''.join(items)}</ul>
    </nav>
  </div>
</header>
""".strip()


def footer_html():
    return """
<footer class="hub-footer">
  <div class="hub-footer-inner">
    <div>
      <h4>About</h4>
      <p>A directory of bilingual school sites, foreign-teacher profiles, and classroom resources across Changhua County.</p>
      <p class="hub-zh">由人師教育協會（My Culture Connect）與彰化縣國際教育暨英語教育資源中心共同維護。</p>
    </div>
    <div>
      <h4>Producing Units</h4>
      <a href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">CIEETRC<br>英語教育資源中心</a>
      <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect<br>人師教育協會</a>
    </div>
    <div>
      <h4>Contact</h4>
      <a href="mailto:luke@mycultureconnect.org">luke@mycultureconnect.org</a>
    </div>
  </div>
  <p class="hub-footer-credit">Map data: <a href="https://github.com/ronnywang/twgeojson" target="_blank" rel="noopener">ronnywang/twgeojson</a></p>
</footer>
""".strip()


def page_shell(title, content, current_path, extra_head=""):
    nav = nav_html(current_path)
    footer = footer_html()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · Changhua Bilingual Hub</title>
  <meta name="description" content="Bilingual education resources across Changhua County, Taiwan.">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/logo/icon-32.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/assets/logo/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/logo/icon-180.png">
  <meta name="theme-color" content="#1f6e6e">
  <meta property="og:title" content="{title} · Changhua Bilingual Hub">
  <meta property="og:image" content="/assets/logo/icon-512.png">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap">
  <link rel="stylesheet" href="/assets/css/hub.css">
  {extra_head}
</head>
<body>
{nav}
<main>
{content}
</main>
{footer}
<script src="/assets/js/hub.js"></script>
</body>
</html>
"""


# -------- Index data computed from YAML --------
def build_township_index(townships, schools):
    counts = {}
    for s in schools:
        counts[s["township"]] = counts.get(s["township"], 0) + 1
    out = {}
    for t in townships:
        out[t["zh"]] = {
            "slug": t["slug"],
            "zh": t["zh"],
            "en": t["en"],
            "zip": t["zip"],
            "school_count": counts.get(t["slug"], 0),
        }
    return out


# -------- Page builders --------
def round_down(n, step):
    """Round down to nearest multiple of step (e.g. 106 → 100)."""
    return (n // step) * step


def build_home(townships_data, schools_data, wotd_items):
    townships = townships_data["townships"]
    schools = schools_data["schools"]
    idx = build_township_index(townships, schools)
    inline_idx = json.dumps(idx, ensure_ascii=False)

    # Use rounded-down phrasing for volatile counts; keep exact for stable facts
    total_schools = len(schools)
    schools_rounded = f"{round_down(total_schools, 10)}+"  # 106 → 100+
    townships_with_schools = sum(1 for t in idx.values() if t["school_count"])
    townships_rounded = f"{round_down(townships_with_schools, 5)}+"  # 25 → 20+
    total_videos = len(wotd_items)
    videos_rounded = "3,000"  # Luke 2026-05-17: hardcoded rounded-up aspirational number
    contributing_schools = len({r["sch"] for r in wotd_items if r["sch"]})
    # Luke 2026-05-17: hardcoded conservative count — match WOTD page hero ("100+ schools").
    # Raw 116 canonical schools, but ~22 have ≤2 videos so the real "participating" count is closer to 100.
    contributing_rounded = "100+"
    # Cache-buster for the township geojson (browsers cache fetched JSON aggressively)
    geojson_path = ROOT / "assets" / "map" / "changhua-townships.geojson"
    geojson_v = int(geojson_path.stat().st_mtime)

    content = f"""
<div class="hub-hero-wrap">
<section class="hub-hero">
  <div class="hub-hero-text">
    <p class="hub-eyebrow">Welcome / 歡迎</p>
    <h1 class="hub-h1">A bilingual gateway to <em style="color:var(--hub-primary)">Changhua</em>'s schools.</h1>
    <p>{schools_rounded} school sites, foreign English teacher profiles, and a growing library of classroom resources — all in one place.</p>
    <p class="hub-zh">{townships_rounded} 鄉鎮、{schools_rounded} 學校的雙語網站、外籍英語教師介紹，以及共用教材，集中一站。</p>
    <div class="hub-hero-actions">
      <a class="hub-btn hub-btn--primary" href="/word-of-the-day/">Watch {videos_rounded} videos →</a>
      <a class="hub-btn hub-btn--ghost" href="/schools/">Browse Schools</a>
    </div>
  </div>
  <div class="hub-map-wrap">
    <div id="hub-map" data-geo="/assets/map/changhua-townships.geojson?v={geojson_v}"></div>
  </div>
</section>
</div>

<section class="hub-section">
  <p class="hub-eyebrow">What's inside</p>
  <h2 class="hub-h2">Explore the Hub</h2>
  <div class="hub-feature-grid" style="margin-top:32px">
    <a class="hub-card hub-card--featured" href="/word-of-the-day/">
      <span class="hub-card-tag">Signature</span>
      <h3>Word of the Day 校園百科</h3>
      <p>Our flagship classroom-video library — every word taught in a real Changhua classroom, in two example sentences, by a real teacher.</p>
      <div class="hub-card-meta">{videos_rounded} videos · {contributing_rounded} schools</div>
    </a>
    <a class="hub-card" href="/schools/">
      <h3>Schools 學校</h3>
      <p>Bilingual websites for every school in Changhua, grouped by township.</p>
      <div class="hub-card-meta">{schools_rounded} schools · {townships_rounded} townships</div>
    </a>
    <a class="hub-card" href="/fets/">
      <h3>FETs 外籍教師</h3>
      <p>Meet the Foreign English Teachers placed across Changhua schools.</p>
      <div class="hub-card-meta">Roster · Photos · Profiles</div>
    </a>
    <a class="hub-card" href="/resources/">
      <h3>Resources 教學資源</h3>
      <p>Festivals, SDGs, Classroom English, About Changhua, partner networks — the full library lives here.</p>
      <div class="hub-card-meta">Classroom-ready</div>
    </a>
  </div>
</section>

<section class="home-changhua">
  <div class="home-changhua-inner">
    <div class="home-changhua-text">
      <p class="hub-eyebrow" style="color:#ffd28a">Discover Changhua · 認識彰化</p>
      <h2 class="hub-h2" style="color:#fff;font-size:clamp(1.8rem,3vw,2.4rem);margin-bottom:18px">
        A county whose name means <em style="color:#ffd28a">to manifest refined civilization</em>.
      </h2>
      <p style="color:rgba(255,255,255,.92);max-width:60ch;font-size:1.05rem;line-height:1.65">
        Changhua County (彰化縣) was founded in <strong>1723</strong> — its very name comes from the Qing-era phrase <strong>"建學立師以彰雅化"</strong>: <em>establish schools and teachers to manifest refined civilization</em>. Education is built into our county's identity.
      </p>
      <p class="hub-zh" style="color:rgba(255,255,255,.85);max-width:60ch;font-size:1rem;line-height:1.75;margin-top:14px">
        彰化於 1723 年（清雍正元年）設縣，得名於「建學立師以彰雅化」。教育在彰化從來不是邊角，而是縣的本名與本心。
      </p>
      <div style="margin-top:24px">
        <a class="hub-btn hub-btn--primary" href="/resources/about-changhua/" style="background:#ffd28a;color:var(--hub-primary-deep)">Read more →</a>
      </div>
    </div>
    <div class="home-changhua-stats">
      <div class="home-stat">
        <p class="home-stat-num">1,074<span class="unit">km²</span></p>
        <p class="home-stat-label">Total area<br><span class="zh">全台最小縣</span></p>
      </div>
      <div class="home-stat">
        <p class="home-stat-num">1.2<span class="unit">M</span></p>
        <p class="home-stat-label">Population<br><span class="zh">全台人口最多縣</span></p>
      </div>
      <div class="home-stat">
        <p class="home-stat-num">1723</p>
        <p class="home-stat-label">Founded<br><span class="zh">清雍正元年</span></p>
      </div>
      <div class="home-stat">
        <p class="home-stat-num">26</p>
        <p class="home-stat-label">Townships<br><span class="zh">2 市 + 6 鎮 + 18 鄉</span></p>
      </div>
    </div>
  </div>
</section>

<section class="hub-section">
  <p class="hub-eyebrow">The bilingual ecosystem · 雙語教育生態</p>
  <h2 class="hub-h2">Three partners. One mission.</h2>
  <p style="color:var(--hub-ink-soft);max-width:62ch;margin-bottom:32px">
    Changhua's bilingual program runs on a tri-partite partnership — government policy, expert resources, and a non-profit that has brought foreign English teachers to the county since 2009.
  </p>
  <div class="hub-feature-grid">
    <a class="hub-card" href="https://newboe.chc.edu.tw/" target="_blank" rel="noopener">
      <h3>彰化縣政府教育處</h3>
      <p>Sets county-wide bilingual education policy and channels Ministry of Education funding to schools through the Student Affairs &amp; Curriculum Development Division (學務管理及課程發展科). Flagship programs include the Teaching Enhancement Program (精進教學計畫), the Teaching Excellence Awards (教學卓越獎), and bilingual immersion grants that place foreign English teachers in classrooms across all 26 townships.</p>
      <div class="hub-card-meta">Department of Education</div>
    </a>
    <a class="hub-card" href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">
      <h3>CIEETRC</h3>
      <p>Changhua County's International &amp; English Education Resource Center (彰化縣國際教育暨英語教育資源中心), hosted at Minsheng Elementary School. Produces shared bilingual teaching materials, runs the SIEP testing program for county schools, organises professional development for English teachers, and serves as the curatorial home of this Hub.</p>
      <div class="hub-card-meta">Resource center</div>
    </a>
    <div class="hub-card">
      <h3>人師教育協會 · My Culture Connect</h3>
      <p>Non-profit that recruits, trains, and places foreign English teachers across Changhua's elementary and junior-high schools. Handles host-school matching, day-to-day placement coordination, and on-the-ground support for teachers and host campuses alike. Serving the county since 2009.</p>
      <div class="hub-card-meta" style="margin-top:12px">In Changhua since 2009</div>
      <div class="partner-links">
        <a href="https://www.twrses.org/" target="_blank" rel="noopener" class="partner-link">
          <span class="partner-link__label">中文站</span>
          <span class="partner-link__url">twrses.org →</span>
        </a>
        <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener" class="partner-link">
          <span class="partner-link__label">English site</span>
          <span class="partner-link__url">mycultureconnect.org →</span>
        </a>
      </div>
    </div>
  </div>
</section>
""".strip()

    extra_head = f"<script>window.HUB_TOWNSHIP_INDEX = {inline_idx};</script>"
    return page_shell("Welcome", content, "/", extra_head)


def build_schools(townships_data, schools_data):
    townships = townships_data["townships"]  # already ZIP-sorted in main()
    schools = schools_data["schools"]

    # Group schools by township slug
    by_township = {}
    for s in schools:
        by_township.setdefault(s["township"], []).append(s)

    # Within each township: senior-high → junior-high → elementary, A-Z by name
    level_priority = {"senior-high": 0, "junior-high": 1, "elementary": 2}
    for ss in by_township.values():
        ss.sort(key=lambda s: (
            level_priority.get(s.get("level", "elementary"), 2),
            s["name"].lower(),
        ))

    blocks = []
    for t in townships:
        ss = by_township.get(t["slug"], [])
        if not ss:
            continue
        cards = []
        for s in ss:
            level = s.get("level", "elementary")
            badge_cls = "jh" if level == "junior-high" else ("sh" if level == "senior-high" else "")
            badge_text = {"junior-high": "JHS", "senior-high": "HS", "elementary": "ES"}.get(level, "ES")
            search_data = f"{s['name']} {s.get('zh','')} {t['en']} {t['zh']} {s['slug']}"
            slug = s["slug"]
            # Photo: /assets/images/schools/<slug>.jpg if it exists, else fallback to Chinese char tile
            photo_path = ROOT / "assets" / "images" / "schools" / f"{slug}.jpg"
            if photo_path.exists():
                mtime = int(photo_path.stat().st_mtime)
                photo_html = f'<img class="photo" src="/assets/images/schools/{slug}.jpg?v={mtime}" alt="{s["name"]}" loading="lazy">'
            else:
                zh = s.get("zh","") or s["name"]
                # show first 2 chars
                fallback = zh[:2] if zh else s["name"][:2]
                photo_html = f'<div class="photo-fallback" aria-hidden="true">{fallback}</div>'
            cards.append(f"""
<a class="hub-school-card" href="{s['url']}" target="_blank" rel="noopener" data-search="{search_data}">
  {photo_html}
  <div class="body">
    <p class="name">{s['name']}</p>
    <p class="zh">{s.get('zh','')}</p>
    <span class="badge {badge_cls}">{badge_text}</span>
  </div>
</a>
""".strip())
        blocks.append(f"""
<section id="{t['slug']}" class="hub-township-block">
  <header class="hub-township-head">
    <h2>{t['en']}</h2>
    <span class="zh">{t['zh']}</span>
    <span class="meta">{len(ss)} schools · {t['zip']}</span>
  </header>
  <div class="hub-school-grid">
    {''.join(cards)}
  </div>
</section>
""".strip())

    total = len(schools)
    townships_with = len(by_township)
    schools_r = f"{round_down(total, 10)}+"
    townships_r = f"{round_down(townships_with, 5)}+"

    hero = curve_hero(
        variant="schools",
        eyebrow="Directory",
        title_html="Schools of<br>Changhua.",
        lede_en=f"{schools_r} schools across {townships_r} townships, each with its own bilingual website — listed by ZIP from 500 to 530.",
        lede_zh=f"彰化 {townships_r} 鄉鎮、{schools_r} 所學校的雙語網站索引，依郵遞區號（500–530）排列。",
        pull_en="One county.<br>One bilingual map.",
        pull_zh="一個縣，一張雙語地圖。",
        attr="Changhua Bilingual Hub",
    )

    content = f"""
{hero}

<section class="hub-section">
  <div class="hub-search" style="max-width:560px">
    <input id="hub-search-input" type="search" placeholder="Search by school name, township, or slug…" autocomplete="off">
  </div>
  {''.join(blocks)}
</section>
""".strip()
    return page_shell("Schools", content, "/schools/")


def curve_hero(variant, eyebrow, title_html, lede_en, lede_zh, pull_en, pull_zh, attr):
    """MCC-style hero: asymmetric color block on the left (~60% width) carved
    out by an SVG curve; pull-quote sits in the white space on the right.
    variant: schools | fets | resources | wotd."""
    bg_svg = (
        '<svg class="hub-curve-hero-bg" viewBox="0 0 1200 600" '
        'preserveAspectRatio="none" aria-hidden="true">'
        '<path d="M 0,0 L 760,0 C 720,140 800,290 720,420 '
        'C 660,520 760,560 700,600 L 0,600 Z"/>'
        '</svg>'
    )
    return f"""
<section class="hub-curve-hero hub-curve-hero--{variant}">
  {bg_svg}
  <div class="hub-curve-hero-inner">
    <div class="hub-curve-hero-block">
      <p class="hub-eyebrow">{eyebrow}</p>
      <h1 class="hub-curve-hero-title">{title_html}</h1>
      <p class="hub-curve-hero-lede">{lede_en}</p>
      <p class="hub-curve-hero-lede-zh">{lede_zh}</p>
    </div>
    <aside class="hub-curve-hero-side">
      <p class="hub-curve-hero-pull">{pull_en}</p>
      <p class="hub-curve-hero-pull-zh">{pull_zh}</p>
      <p class="hub-curve-hero-attr">{attr}</p>
    </aside>
  </div>
</section>
""".strip()


def editorial_hero(variant, eyebrow, title_html, lede_en, lede_zh, pull_en, pull_zh, attr):
    """Editorial-magazine style hero: serif headline left, pull-quote right.
    variant is one of: schools, fets, resources (drives the accent color)."""
    return f"""
<section class="hub-editorial-hero hub-editorial-hero--{variant}">
  <div class="hub-editorial-hero-inner">
    <div class="hub-editorial-hero-left">
      <p class="hub-eyebrow">{eyebrow}</p>
      <h1 class="hub-editorial-hero-title">{title_html}</h1>
      <p class="hub-editorial-hero-lede">{lede_en}</p>
      <p class="hub-editorial-hero-lede-zh">{lede_zh}</p>
    </div>
    <aside class="hub-editorial-hero-right">
      <p class="hub-editorial-hero-pull">{pull_en}</p>
      <p class="hub-editorial-hero-pull-zh">{pull_zh}</p>
      <p class="hub-editorial-hero-attr">{attr}</p>
    </aside>
  </div>
</section>
""".strip()


def build_fets(fets_data, schools_data):
    fets = fets_data["fets"]

    def card(fet):
        name = fet.get("name", "")
        school_en = fet.get("school", "")
        school_zh = fet.get("school_zh", "")
        photo = fet.get("photo", "")
        site = fet.get("site", "")
        search_data = f"{name} {school_en} {school_zh}".strip()

        if photo:
            img_html = (
                f'<img src="/assets/images/fets/{photo}" alt="{name}" loading="lazy" '
                f'class="fet-photo">'
            )
        else:
            initials = "".join(w[0] for w in name.split()[:2]).upper()
            img_html = f'<div class="fet-photo fet-initials" aria-hidden="true">{initials}</div>'

        if site:
            wrap_open = f'<a class="fet-card" href="{site}" data-search="{search_data}" target="_blank" rel="noopener">'
            wrap_close = "</a>"
        else:
            wrap_open = f'<div class="fet-card" data-search="{search_data}">'
            wrap_close = "</div>"

        zh_line = f'<p class="fet-school-zh">{school_zh}</p>' if school_zh else ""
        return f"""
{wrap_open}
  {img_html}
  <p class="fet-name">{name}</p>
  <p class="fet-school">{school_en}</p>
  {zh_line}
{wrap_close}
""".strip()

    elem_jh = [card(f) for f in fets if f.get("segment") in ("elementary", "junior-high")]
    senior = [card(f) for f in fets if f.get("segment") == "senior-high"]
    past = [card(f) for f in fets if f.get("segment") == "past"]
    total = len(fets)
    total_r = f"{round_down(total, 10)}+"

    past_section = ""
    if past:
        past_section = f"""
  <div class="fet-group" style="margin-top:72px">
    <h2 class="hub-h2">Past FETs <span style="font-family:var(--hub-zh-font);font-size:.7em;color:var(--hub-ink-faint);font-weight:400">離職的外師</span></h2>
    <p style="color:var(--hub-ink-soft);max-width:60ch;margin-top:-8px">
      With gratitude to the teachers whose service in Changhua has concluded.
    </p>
    <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:60ch">
      感謝以下曾在彰化任教、現已結束服務的外籍英語教師。
    </p>
    <div class="fet-grid" style="margin-top:24px">
      {''.join(past)}
    </div>
  </div>
"""

    hero = curve_hero(
        variant="fets",
        eyebrow="Foreign English Teachers",
        title_html="Meet our<br>FETs.",
        lede_en=f"{total_r} teachers placed across Changhua schools — bringing a global voice to every classroom.",
        lede_zh=f"{total_r} 位外籍英語教師，分布彰化校園——把世界帶進每一間教室。",
        pull_en="A global voice<br>in every classroom.",
        pull_zh="教室裡的世界。",
        attr="Changhua Bilingual Hub",
    )

    content = f"""
{hero}

<section class="hub-section">
  <div class="hub-search" style="max-width:560px;margin-bottom:40px">
    <input id="fets-search-input" type="search" placeholder="Search teacher or school… · 搜尋外師或學校" autocomplete="off">
  </div>
  <p id="fets-search-empty" class="hub-search-empty" hidden>No matching teachers. Try a different name or school. · 沒有相符的外師，請換個關鍵字。</p>

  <div class="fet-group">
    <h2 class="hub-h2">Elementary &amp; Junior High <span style="font-family:var(--hub-zh-font);font-size:.7em;color:var(--hub-ink-faint);font-weight:400">國中小</span></h2>
    <div class="fet-grid" style="margin-top:24px">
      {''.join(elem_jh)}
    </div>
  </div>

  <div class="fet-group" style="margin-top:72px">
    <h2 class="hub-h2">Senior High <span style="font-family:var(--hub-zh-font);font-size:.7em;color:var(--hub-ink-faint);font-weight:400">高中</span></h2>
    <div class="fet-grid" style="margin-top:24px">
      {''.join(senior)}
    </div>
  </div>
{past_section}
</section>
""".strip()
    return page_shell("FETs", content, "/fets/")


WOTD_THEMES = [
    ("tasks", "Tasks", "校園百科", [
        "sweep","clean","mop","wipe","wash","dust","tidy","pick up","trash","garbage","recycle",
        "attendance","line up","raise hand","stand up","sit down","line","queue","duty","chore",
        "homework","assignment","report","journal","schedule","timetable","bell","greeting","greet",
    ]),
    ("physical-activities", "Physical Activities", "體育活動", [
        "soccer","basketball","baseball","football","badminton","volleyball","tennis","table tennis","ping pong",
        "swim","swimming","jump rope","jump","run","running","throw","kick","catch","dodgeball",
        "exercise","sport","gym","pe","race","relay","dance","stretch","push-up","sit-up","track","field",
        "archery","skip","hike","hiking","cycling","bike","skate","skating",
    ]),
    ("festivals", "Festivals & Celebrations", "節慶慶典", [
        "christmas","new year","halloween","easter","thanksgiving","valentine","mother's day","father's day",
        "lunar","lantern","mid-autumn","mid autumn","dragon boat","moon cake","mooncake","tomb sweeping",
        "festival","celebrate","celebration","graduation","ceremony","parade","carnival","party","birthday",
        "joss paper","red turtle cake","red envelope","red packet","fireworks","firecracker",
    ]),
    ("food-agriculture", "Food & Agriculture", "食物與農業", [
        "rice","noodle","bread","dumpling","cake","pizza","cookie","soup","tea","milk","juice",
        "apple","banana","orange","grape","pear","watermelon","strawberry","mango","pineapple","tomato",
        "vegetable","cabbage","carrot","onion","potato","pepper","cucumber","corn","peanut","bean",
        "fruit","fish","meat","chicken","beef","pork","egg",
        "farm","field","plant","seed","crop","harvest","grow","garden","greenhouse","tractor",
        "rice field","paddy","oyster","grape","mushroom","moringa",
        "cook","bake","fry","boil","kitchen","menu","recipe","lunch","breakfast","dinner","snack",
    ]),
    ("learning-subjects", "Learning Subjects", "學科", [
        "math","mathematics","science","chinese","english","japanese","french","social studies","history",
        "geography","biology","chemistry","physics","art","music","pe","computer","information",
        "subject","class","lesson","course",
    ]),
    ("clubs-teams", "Clubs & Teams", "社團", [
        "club","team","band","choir","orchestra","drum","drumming","cheerleading","squad","group",
        "society","association","scout","practice","rehearsal","competition","contest",
        "singing contest","talent show","performance","perform",
    ]),
    ("facilities-equipment", "Facilities & Equipment", "設施設備", [
        "library","playground","classroom","auditorium","gym","gymnasium","hallway","corridor","stairs",
        "lab","laboratory","cafeteria","office","clinic","computer room","music room","art room",
        "blackboard","whiteboard","desk","chair","table","book","textbook","backpack","pencil","pen",
        "ruler","scissors","glue","tape","eraser","crayon","marker","notebook","paper","map","globe",
        "recorder","piano","keyboard","violin","guitar","flute","drum","triangle",
        "broom","mop","dustpan","sink","faucet","trash can","bin","bucket","ladder","scale",
        "projector","screen","microphone","speaker","camera",
        "mobile library","reading corner","bulletin board",
    ]),
    ("cultural-artistic", "Cultural & Artistic", "文化藝術", [
        "calligraphy","painting","draw","drawing","sketch","clay","pottery","sculpt","origami","craft",
        "weave","knit","embroider","print","stamp","poster",
        "dance","sing","song","poem","poetry","story","storytelling","theater","drama","puppet",
        "culture","tradition","traditional","heritage","temple","shrine","museum","exhibit","exhibition",
        "kite","fan","mask",
    ]),
    ("health-safety", "Health & Safety", "健康安全", [
        "wash your hands","wash hands","brush teeth","sleep","rest","health","healthy","clean",
        "doctor","nurse","clinic","medicine","cold","cough","fever","sick","ill","hospital",
        "safety","safe","danger","emergency","fire","drill","earthquake","helmet","seat belt",
        "traffic","crosswalk","sidewalk","cross the street","look both ways",
        "wear","glove","mask","sanitize","sanitizer","tissue","bandage","first aid",
    ]),
]
WOTD_FALLBACK = ("picture-description", "Picture Description", "看圖說話")


def classify_keyword(keyword, sentence_1):
    text = (keyword + " " + (sentence_1 or "")).lower()
    # Try each theme — first match wins (in priority order)
    for slug, _en, _zh, kws in WOTD_THEMES:
        for kw in kws:
            if kw in text:
                return slug
    return WOTD_FALLBACK[0]


def load_wotd():
    rows = []
    with open(ROOT / "data" / "wotd.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            yt = (r.get("youtube") or "").strip()
            m = YT_ID_RX.search(yt)
            if not m:
                continue
            kw = r["keyword"].strip()
            s1 = r["sentence_1"].strip()
            theme = classify_keyword(kw, s1)
            # Initial letter (A-Z) — strip POS tags etc.
            base = re.sub(r"[^A-Za-z]", "", kw)
            letter = base[0].upper() if base else "#"
            rows.append({
                "k": kw,
                "kz": (r.get("keyword_zh") or "").strip(),
                "s1": s1,
                "s1z": r["sentence_1_zh"].strip(),
                "s2": r["sentence_2"].strip(),
                "s2z": r["sentence_2_zh"].strip(),
                "sch": canonical_school((r.get("school") or "").strip()),
                "v": m.group(1),
                "t": theme,
                "l": letter,
            })
    return rows


def normalize_school(name):
    """Strip 彰化縣XX鄉/鎮/市 prefix to get the bare school name for grouping."""
    if not name:
        return ""
    n = name
    n = re.sub(r"^彰化縣[^國市鄉鎮]*[市鎮鄉]", "", n)
    return n.strip() or name.strip()


# Canonicalize school-name variants (extra spaces, typos, missing prefixes)
# so the dropdown / counts treat one school as one school.
SCHOOL_CANONICAL_MAP = {
    # 多空格 / 空白
    "彰化縣 溪州鄉溪州國小": "彰化縣溪州鄉溪州國小",
    "彰化縣溪州鄉 溪州國小": "彰化縣溪州鄉溪州國小",
    "彰化縣 芳苑鄉新寶國小": "彰化縣芳苑鄉新寶國小",
    "彰化縣芳苑鄉 新寶國小": "彰化縣芳苑鄉新寶國小",
    "彰化縣芳苑鄉新寶國小 彰化縣芳苑鄉新寶國小": "彰化縣芳苑鄉新寶國小",
    "彰化縣員林市 饒明國小": "彰化縣員林市饒明國小",
    "彰化縣社頭鄉 湳雅國小": "彰化縣社頭鄉湳雅國小",
    "彰化縣彰化市 中山國小": "彰化縣彰化市中山國小",
    "彰化縣彰化市 快官國小": "彰化縣彰化市快官國小",
    "彰化縣田中鎮 三潭國小": "彰化縣田中鎮三潭國小",
    "彰化縣田中鎮 田中國小": "彰化縣田中鎮田中國小",
    "彰化縣社頭鄉 朝興國小": "彰化縣社頭鄉朝興國小",
    "彰化縣芳苑鄉 路上國小": "彰化縣芳苑鄉路上國小",
    "彰化縣和美鎮 新庄國小": "彰化縣和美鎮新庄國小",
    "彰化縣 二水國小": "彰化縣二水鄉二水國小",
    "彰化縣二水國小": "彰化縣二水鄉二水國小",
    # typos
    "彰化線福興鄉永豐國小": "彰化縣福興鄉永豐國小",  # 線→縣
    "彰化縣芳園鄉文德國小": "彰化縣芬園鄉文德國小",  # 芳→芬
    "彰化縣新港鄉大同國小": "彰化縣伸港鄉大同國小",  # 新→伸
    "彰化縣港鄉新港國小": "彰化縣伸港鄉新港國小",      # 補 伸
    "彰化縣社頭心湳雅國小": "彰化縣社頭鄉湳雅國小",  # 心→鄉
    "彰化縣社頭湳雅國小": "彰化縣社頭鄉湳雅國小",      # 補 鄉
    "湳雅國小": "彰化縣社頭鄉湳雅國小",
    "彰化縣員林鎮饒明國小": "彰化縣員林市饒明國小",  # 鎮→市
    "彰化縣鹿鳴國中雙語資源網": "彰化縣鹿港鎮鹿鳴國中",
    "彰化顯鹿港鎮鹿鳴國中": "彰化縣鹿港鎮鹿鳴國中",  # 顯→縣 typo in Excel
    # 缺彰化縣前綴
    "彰化市中山國小": "彰化縣彰化市中山國小",
    "彰化市大成國小": "彰化縣彰化市大成國小",
    "彰化市平和國小": "彰化縣彰化市平和國小",
    "彰化市彰興國中": "彰化縣彰化市彰興國中",
    "彰化縣彰興國中": "彰化縣彰化市彰興國中",
    "彰化市東芳國小": "彰化縣彰化市東芳國小",
    "彰化市民生國小": "彰化縣彰化市民生國小",
    # 2026-05-17 後續發現的簡寫（缺鄉鎮）變體
    "彰化縣明禮國小": "彰化縣田中鎮明禮國小",
    "彰化縣中和國小": "彰化縣埤頭鄉中和國小",
    "彰化縣太平國小": "彰化縣埔心鄉太平國小",
    "彰化縣路上國小": "彰化縣芳苑鄉路上國小",
    "彰化縣溪州國中": "彰化縣溪州鄉溪州國中",
    "彰化縣溪州國小": "彰化縣溪州鄉溪州國小",
    "彰化縣溪州鄉溪洲國小": "彰化縣溪州鄉溪州國小",  # 洲→州
    "彰化縣伸港新大同國小": "彰化縣伸港鄉大同國小",
    "彰化縣二林國小": "彰化縣二林鎮二林國小",
    "彰化縣二水鄉源泉": "彰化縣二水鄉源泉國小",
    "彰化顯鹿港鎮鹿鳴國中": "彰化縣鹿港鎮鹿鳴國中",  # 顯→縣
    "彰化縣溪州鄉成功國小西畔分校": "彰化縣溪州鄉成功國小暨西畔分校",
}


def canonical_school(name):
    """Map any known school-name variant to its canonical form."""
    if not name:
        return ""
    return SCHOOL_CANONICAL_MAP.get(name.strip(), name.strip())


def build_wotd():
    items = load_wotd()
    # Build school facets — count per (display name)
    school_counts = {}
    theme_counts = {}
    letter_counts = {}
    for r in items:
        school_counts[r["sch"]] = school_counts.get(r["sch"], 0) + 1
        theme_counts[r["t"]] = theme_counts.get(r["t"], 0) + 1
        letter_counts[r["l"]] = letter_counts.get(r["l"], 0) + 1
    # Drop the empty-school bucket — those videos are uncredited and shouldn't
    # appear as a phantom "" row in the filter dropdown.
    school_counts.pop("", None)

    # Theme metadata for UI
    themes_meta = [(slug, en, zh, theme_counts.get(slug, 0)) for slug, en, zh, _ in WOTD_THEMES]
    themes_meta.append((WOTD_FALLBACK[0], WOTD_FALLBACK[1], WOTD_FALLBACK[2], theme_counts.get(WOTD_FALLBACK[0], 0)))

    # Write data file for client
    data_path = ROOT / "assets" / "data" / "wotd.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "items": items,
        "schools": sorted(school_counts.items(), key=lambda x: -x[1]),
        "themes": [{"slug": s, "en": en, "zh": zh, "count": c} for s, en, zh, c in themes_meta],
        "generated_at": "build-time",
    }
    data_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  wrote /assets/data/wotd.json  ({data_path.stat().st_size:,} bytes, {len(items)} items)")

    theme_chips = ''.join(
        f'<button class="wotd-theme-chip" data-theme="{slug}"><span class="en">{en}</span><span class="zh">{zh}</span><span class="ct">{c}</span></button>'
        for slug, en, zh, c in themes_meta if c > 0
    )

    letters = sorted(letter_counts.keys())
    az_chips = ''.join(
        f'<button class="wotd-az-chip" data-letter="{L}" title="{letter_counts[L]} words starting with {L}">{L}</button>'
        for L in letters
    )

    items_r = "3,000"  # Luke 2026-05-17: match home hero aspirational round
    # Luke 2026-05-17: conservative count — gut-check beats raw dedup (raw 148 → canonical ~122, but
    # ~22 schools have ≤2 videos so the "real participating" count is ~100). Hard-set to 100+.
    schools_r = "100+"

    hero = curve_hero(
        variant="wotd",
        eyebrow="Our signature collection",
        title_html="Word of<br>the Day.",
        lede_en=f"{items_r} bilingual classroom videos from {schools_r} schools — every word filmed in a real Changhua classroom, by a real teacher.",
        lede_zh=f"{items_r} 支來自 {schools_r} 所彰化學校的雙語教室實拍影片——每個單字都在真實課堂裡發生。",
        pull_en="One word a day,<br>in a real classroom.",
        pull_zh="每天一個字，在真實的教室裡。",
        attr="Changhua Bilingual Hub",
    )

    content = f"""
{hero}

<section class="wotd-toolbar-wrap">
  <div class="wotd-toolbar">
    <div class="hub-search wotd-search">
      <input id="wotd-q" type="search" placeholder="🔎 Search English, 中文, or school name…" autocomplete="off" />
    </div>
    <select id="wotd-school" aria-label="Filter by school">
      <option value="">All schools · 全部學校</option>
      {''.join(f'<option value="{sch}">{sch}</option>' for sch in sorted(school_counts.keys()))}
    </select>
    <div id="wotd-count" class="wotd-count">{len(items):,} videos</div>
  </div>
</section>

<section class="hub-section wotd-filters">
  <h2 class="wotd-filter-label">Browse by theme · 主題瀏覽</h2>
  <div class="wotd-theme-row">
    <button class="wotd-theme-chip wotd-theme-chip--all is-active" data-theme="">All themes<span class="ct">{len(items)}</span></button>
    {theme_chips}
  </div>

  <h2 class="wotd-filter-label" style="margin-top:32px">Browse A–Z · 字母索引</h2>
  <div class="wotd-az-row">
    <button class="wotd-az-chip wotd-az-chip--all is-active" data-letter="">All</button>
    {az_chips}
  </div>
</section>

<section class="hub-section wotd-section" style="padding-top:24px">
  <div id="wotd-grid" class="wotd-grid" aria-live="polite"></div>
  <div id="wotd-loadmore-wrap" style="text-align:center;margin-top:40px;display:none">
    <button id="wotd-loadmore" class="hub-btn hub-btn--ghost">Load more →</button>
  </div>
  <div id="wotd-empty" class="wotd-empty" hidden>
    <p>No videos match. Try a different word, pick another school, or clear the filters.</p>
  </div>
</section>
""".strip()
    extra_head = '<link rel="stylesheet" href="/assets/css/wotd.css">\n  <script defer src="/assets/js/wotd.js"></script>'
    return page_shell("Word of the Day", content, "/word-of-the-day/", extra_head)


BILINGUAL_CAMPUS = [
    # (slug, en, zh, brief_en)
    ("school-tours",          "School Tours",            "校園導覽",       "Guided tours in English — gates, classrooms, library, playground."),
    ("classroom-english",     "Classroom English",       "教室英語",       "Ten everyday classroom situations with ready-to-use phrases — video series by Sarah Thomas."),
    ("morning-assembly",      "Morning Assembly",        "朝會",           "The school's daily English ritual: pledge, news, weather, words of the day."),
    ("school-teams-clubs",    "School Teams & Clubs",    "校隊與社團",     "Sports teams, arts clubs, and after-school groups — vocabulary and roleplay."),
    ("announcements",         "Bilingual Announcements", "校園廣播英語",   "13-episode bilingual series on the four administrative offices — by Sarah Thomas &amp; Susan Rose."),
    ("english-reading-corner","English Reading Corner",  "英文閱讀角",     "Designated spaces and routines for sustained English reading."),
    ("intl-sister-school",    "International Sister School","國際姊妹校", "Video letters, Zoom meet-ups, and exchange visits between campuses."),
    ("english-practice-corner","English Practice Corner","英語練習角",     "Drop-in spots for spontaneous speaking practice with FETs."),
    ("amazing-changhua",      "Amazing Changhua",        "探索彰化",       "Local-culture mini-projects — temples, food, agriculture, festivals."),
    ("school-news",           "School News",             "校園新聞",       "Student-produced English news bulletins about campus life."),
    ("summer-fun-program",    "Summer Fun Program",      "暑期樂活營",     "Bilingual summer camps mixing academics, sports, and crafts."),
    ("english-self-intro",    "English Self-Introduction","英文自介",      "Structured templates teaching students to introduce themselves confidently."),
    ("one-minute-english",    "One Minute English",      "一分鐘英文",     "Sixty-second daily English clips students can watch and shadow."),
]


def build_resources():
    # Build Bilingual Campus card grid
    bc_cards = []
    for slug, en, zh, brief in BILINGUAL_CAMPUS:
        # Classroom English already has a full page; others link to stub pages we'll build alongside
        href = f"/resources/{slug}/" if slug == "classroom-english" else f"/resources/bilingual-campus/{slug}/"
        bc_cards.append(f"""
<a class="hub-card" href="{href}">
  <h3>{en} <small style="font-family:var(--hub-zh-font);font-size:.65em;color:var(--hub-ink-faint);font-weight:500;letter-spacing:.04em">· {zh}</small></h3>
  <p>{brief}</p>
</a>""".strip())

    hero = curve_hero(
        variant="resources",
        eyebrow="Library",
        title_html="Resources for<br>the classroom.",
        lede_en="Background, classroom material, and partner programs that surround Changhua's bilingual schools — for teachers, parents, and visitors.",
        lede_zh="彰化雙語校園背後的脈絡、共用教材與夥伴計畫——給老師、家長與訪客的入門資源。",
        pull_en="Festivals, words,<br>and field stories.",
        pull_zh="節慶、單字、田野故事。",
        attr="Changhua Bilingual Hub",
    )

    content = f"""
{hero}

<section class="hub-section" style="padding-top:48px;padding-bottom:8px">
  <div class="hub-search" style="max-width:560px">
    <input id="resources-search-input" type="search" placeholder="Search resources… · 搜尋資源" autocomplete="off">
  </div>
  <p id="resources-search-empty" class="hub-search-empty" hidden>No matching resources. Try another keyword. · 沒有相符的資源，請換個關鍵字。</p>
</section>

<!-- ===== Background & Identity ===== -->
<section class="hub-section" style="padding-top:0">
  <h2 class="resources-h2">Background &amp; Identity <small>背景與識別</small></h2>
  <div class="hub-feature-grid">
    <a class="hub-card hub-card--featured" href="/resources/about-changhua/">
      <span class="hub-card-tag">Start here</span>
      <h3>About Changhua 認識彰化</h3>
      <p>1,074 km² · 1.2 million people · founded 1723 — Taiwan's name-sake of education. Geography, history, and the bilingual ecosystem at a glance.</p>
      <div class="hub-card-meta">Geography · History · Education</div>
    </a>
    <a class="hub-card" href="/resources/books-for-taiwan/">
      <h3>Books for Taiwan</h3>
      <p>An American-volunteer project (since 2012) collecting English-language books for Taiwanese schools and libraries.</p>
      <div class="hub-card-meta">Amy Lin · since 2012</div>
    </a>
    <a class="hub-card" href="/resources/eric-berman/">
      <h3>Eric Berman 故事集</h3>
      <p>Four short bilingual classroom stories — kite-making, attendance, a law lecture, and a first-grade opening ceremony.</p>
      <div class="hub-card-meta">4 stories · EN + 中文</div>
    </a>
  </div>
</section>

<!-- ===== Festival English Series ===== -->
<section class="hub-section" style="padding-top:24px">
  <h2 class="resources-h2">Festival English Series <small>節慶英文</small></h2>
  <p style="color:var(--hub-ink-soft);max-width:60ch;margin-bottom:24px">
    Sixteen festivals — Spring &amp; Fall semester — each with a handout and a quiz, freely usable by every Changhua school.
  </p>
  <div class="hub-feature-grid">
    <a class="hub-card hub-card--featured" href="/festivals/">
      <span class="hub-card-tag">All festivals</span>
      <h3>Festival English Hub 節慶英文總覽</h3>
      <p>Full year of festival lessons. Each unit includes vocabulary, traditions, roleplay, and a quiz. Embed on any school's site with one line.</p>
      <div class="hub-card-meta">16 festivals · cross-campus</div>
    </a>
    <a class="hub-card" href="/festivals/chinese-new-year/">
      <h3>🧧 Lunar New Year</h3>
      <p>春節 · The story of Nian, twelve words, the reunion dinner and red envelopes.</p>
      <div class="hub-card-meta">📖 Handout · 📝 Quiz</div>
    </a>
    <a class="hub-card" href="/festivals/mid-autumn-festival/">
      <h3>🌕 Mid-Autumn Festival</h3>
      <p>中秋節 · Moon cakes, family reunion under the full moon, and the legend of Chang'e.</p>
      <div class="hub-card-meta">📖 Handout · 📝 Quiz</div>
    </a>
    <a class="hub-card" href="/festivals/christmas/">
      <h3>🎄 Christmas</h3>
      <p>聖誕節 · Carols, decorations, and Western traditions — for the school's annual Christmas show.</p>
      <div class="hub-card-meta">📖 Handout · 📝 Quiz</div>
    </a>
  </div>
</section>

<!-- ===== Classroom Material ===== -->
<section class="hub-section" style="padding-top:24px">
  <h2 class="resources-h2">Classroom Material <small>課堂教材</small></h2>
  <div class="hub-feature-grid">
    <a class="hub-card" href="/word-of-the-day/">
      <h3>Word of the Day 校園百科</h3>
      <p>Our signature classroom-video library — every word taught in a real Changhua classroom.</p>
      <div class="hub-card-meta">3,000 videos · 100+ schools</div>
    </a>
    <a class="hub-card" href="/resources/classroom-english/">
      <h3>Classroom English 教室英語</h3>
      <p>10 everyday classroom situations with ready-to-use English phrases.</p>
      <div class="hub-card-meta">10 situations</div>
    </a>
    <a class="hub-card" href="/resources/sdgs/">
      <h3>17 SDGs 永續發展目標</h3>
      <p>The UN's 17 Sustainable Development Goals — each adapted for elementary &amp; junior-high classrooms with discussion prompts.</p>
      <div class="hub-card-meta">17 goals · classroom-ready</div>
    </a>
  </div>
</section>

<!-- ===== Bilingual Campus ===== -->
<section class="hub-section" style="padding-top:24px">
  <h2 class="resources-h2">Bilingual Campus <small>雙語生活化校園 · 13 topics</small></h2>
  <p style="color:var(--hub-ink-soft);max-width:62ch;margin-bottom:24px">
    Thirteen everyday-school themes for embedding English into campus life — beyond the classroom. Each topic gets its own unit; we'll expand them over time.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch;margin-bottom:24px">
    十三個校園日常主題，把英語自然融入校園生活——不只是課堂。每個主題各自獨立、陸續展開。
  </p>
  <div class="hub-feature-grid">
    {''.join(bc_cards)}
  </div>
</section>

""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("Resources", content, "/resources/", extra)


def render_bilingual_topic(
    page_title, current_path,
    h1_en, h1_zh,
    hero_en, hero_zh,
    moe_en, moe_zh, core_principle,
    sections_h2_en, sections_h2_zh,
    sections_intro_en, sections_intro_zh,
    sections,
    checklist_h2_en, checklist_h2_zh,
    checklist_items,
    companion_h2_en, companion_h2_zh,
    companion_cards,
):
    """Render a Bilingual Campus topic page (Morning Assembly style).

    sections: list of dicts. Required keys: n, color, en, zh, duration, what_en, what_zh.
              Optional: script (list of (speaker, text) tuples), vocab (list of (en, zh) tuples),
                        tips_en, tips_zh.
    checklist_items: list of (en, zh) tuples.
    companion_cards: list of dicts {href, title, desc, meta}.
    """
    section_html_parts = []
    for a in sections:
        body_blocks = [
            f"""<div class=\"bc-what\">
      <h3 class=\"bc-h3\">What it is · 做法</h3>
      <p>{a['what_en']}</p>
      <p class=\"hub-zh\">{a['what_zh']}</p>
    </div>"""
        ]
        if a.get("script"):
            script_html = ''.join(
                f'<div class="bc-script-line"><strong>{speaker}</strong><span>{text}</span></div>'
                for speaker, text in a["script"]
            )
            body_blocks.append(f"""<div class=\"bc-script\">
      <h3 class=\"bc-h3\">Sample script · 範本對話</h3>
      <div class=\"bc-script-box\">{script_html}</div>
    </div>""")
        if a.get("vocab"):
            chips = ''.join(
                f'<span class="chip">{en} <small>{zh}</small></span>'
                for en, zh in a["vocab"]
            )
            body_blocks.append(f"""<div class=\"bc-vocab-wrap\">
      <h3 class=\"bc-h3\">Key vocabulary · 關鍵詞彙</h3>
      <div class=\"bc-vocab\">{chips}</div>
    </div>""")
        if a.get("tips_en"):
            body_blocks.append(f"""<div class=\"bc-tips\">
      <h3 class=\"bc-h3\">Implementation tip · 實施建議</h3>
      <p>{a['tips_en']}</p>
      <p class=\"hub-zh\">{a['tips_zh']}</p>
    </div>""")
        section_html_parts.append(f"""
<article class="bc-activity t-{a['color']}">
  <header class="bc-activity-head">
    <span class="bc-activity-num">Activity {a['n']:02d}</span>
    <h2 class="bc-activity-title">{a['en']}</h2>
    <p class="bc-activity-zh">{a['zh']}</p>
    <span class="bc-activity-duration">⏱ {a['duration']}</span>
  </header>
  <div class="bc-activity-body">
    {''.join(body_blocks)}
  </div>
</article>
""".strip())

    checklist_html = ''.join(
        f'<label><input type="checkbox"> {en}<br><span class="hub-zh">{zh}</span></label>'
        for en, zh in checklist_items
    )

    companion_html = ''.join(
        f"""<a class="hub-card" href="{c['href']}">
      <h3>{c['title']}</h3>
      <p>{c['desc']}</p>
      <div class="hub-card-meta">{c['meta']}</div>
    </a>"""
        for c in companion_cards
    )

    content = f"""
<section class="hub-section hub-section--narrow" style="padding-bottom:0">
  <p class="hub-eyebrow">Resources · Bilingual Campus</p>
  <h1 class="hub-h1">{h1_en} <small style="font-family:var(--hub-zh-font);font-size:.45em;color:var(--hub-ink-faint);font-weight:500;letter-spacing:.05em;margin-left:8px">{h1_zh}</small></h1>
  <p style="font-size:1.1rem;color:var(--hub-ink-soft);max-width:62ch;line-height:1.65">{hero_en}</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch;line-height:1.75">{hero_zh}</p>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:24px">
  <div class="bc-moe-card">
    <p class="hub-eyebrow" style="color:var(--c-blue-deep);margin-bottom:8px">Why it matters · 政策對齊</p>
    <p>{moe_en}</p>
    <p class="hub-zh">{moe_zh}</p>
    <p><strong>Core principle · 核心原則</strong>: {core_principle}</p>
  </div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px;padding-bottom:64px">
  <h2 class="resources-h2">{sections_h2_en} <small>{sections_h2_zh}</small></h2>
  <p style="color:var(--hub-ink-soft);max-width:62ch;margin-bottom:24px">{sections_intro_en}</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch;margin-bottom:32px">{sections_intro_zh}</p>
  <div class="bc-grid">{''.join(section_html_parts)}</div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:0;padding-bottom:80px">
  <h2 class="resources-h2">{checklist_h2_en} <small>{checklist_h2_zh}</small></h2>
  <div class="bc-checklist">{checklist_html}</div>
</section>

<section class="hub-section hub-section--narrow" style="padding-bottom:64px">
  <h2 class="resources-h2">{companion_h2_en} <small>{companion_h2_zh}</small></h2>
  <div class="hub-feature-grid">{companion_html}</div>
  <p style="margin-top:48px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/bilingual-campus.css">'
    return page_shell(page_title, content, current_path, extra)


def build_morning_assembly():
    sections = [
        {
            "n": 1, "color": "blue",
            "en": "Opening Greeting & Pledge Echo",
            "zh": "雙語問候與國旗下宣示",
            "duration": "2 minutes · 兩分鐘",
            "what_en": "The principal or duty teacher opens the assembly in English; students echo a short bilingual pledge before the national anthem.",
            "what_zh": "由校長或值週老師以英文開場，學生在國歌之前以雙語齊聲覆誦短句宣示。",
            "script": [
                ("Teacher (在司令台): ", "Good morning, everyone! How are you today?"),
                ("Students (台下): ", "Good morning! We are fine, thank you!"),
                ("Teacher: ", "Let's stand up straight, take a deep breath, and start our day together."),
                ("Students: ", "Today I will listen, learn, and be kind. 今天我會傾聽、學習、待人友善。"),
            ],
            "tips_en": "Keep the opening short. The same four lines, repeated every day, become a comforting daily ritual — and the English sticks because it's repeated.",
            "tips_zh": "開場簡短就好。同樣的四句話每天重複，變成學生熟悉的儀式——重複久了，英文自然就留下了。",
        },
        {
            "n": 2, "color": "green",
            "en": "Word of the Day Spotlight",
            "zh": "本日校園百科一字",
            "duration": "1–2 minutes · 一到兩分鐘",
            "what_en": "Play one short Word of the Day video from the Hub on the assembly screen. The 'word announcer' (a rotating student role) reads the word, the Chinese, and one example sentence.",
            "what_zh": "在升旗台螢幕播放 Hub 上的「校園百科」短片一支。當週「報字員」（學生輪值）朗讀單字、中文、與一句例句。",
            "script": [
                ("Word Announcer: ", "Today's word is **calligraphy**, 書法 — c-a-l-l-i-g-r-a-p-h-y."),
                ("Announcer: ", "Calligraphy means the art of beautiful writing. 書法就是把字寫得很美的藝術。"),
                ("Announcer: ", "Listen — 'My grandfather practices calligraphy every Sunday.' 我爺爺每個星期天練書法。"),
                ("Announcer: ", "Now you say it: 'Calligraphy.' Great. See you tomorrow!"),
            ],
            "tips_en": "Use the Hub's WotD library — 2,955 ready-made videos with school credits already attached. Pick one whose contributing school is YOUR school for extra pride.",
            "tips_zh": "直接用 Hub 的 WotD 影片庫——2,955 支現成影片，學校credit 都已就位。挑你「自己學校」拍的那一支播，學生看到自己學校名字會特別有共鳴。",
        },
        {
            "n": 3, "color": "orange",
            "en": "Weather Report (Weekly Friday)",
            "zh": "週五氣象播報",
            "duration": "2–3 minutes · 兩到三分鐘",
            "what_en": "On Fridays, two student weather reporters give a 30-second bilingual forecast for the weekend, written collaboratively in English class earlier in the week.",
            "what_zh": "每週五，兩位學生氣象主播以中英文播報本週末天氣，內容於該週英文課事先共同擬稿。",
            "script": [
                ("Reporter A: ", "Good morning! Here is your weekend weather report."),
                ("Reporter B: ", "Saturday will be sunny with a high of 28 degrees. 星期六晴朗，最高溫 28 度。"),
                ("Reporter A: ", "Sunday will be cloudy with a chance of rain in the afternoon. 星期天多雲，下午可能有雨。"),
                ("Reporter B: ", "Remember to bring an umbrella! Have a great weekend!"),
            ],
            "tips_en": "Rotate the reporter pair every week so every 5th-6th grader gets a turn over the year. The collaborative writing in class is half the learning.",
            "tips_zh": "每週輪換主播搭檔，讓五六年級每位學生一年內都有機會上場。事前在英文課集體擬稿，這個過程本身就是一半的學習。",
        },
        {
            "n": 4, "color": "purple",
            "en": "Birthday Roll Call",
            "zh": "本週生日點名",
            "duration": "1 minute · 一分鐘",
            "what_en": "Once a week, the duty teacher reads the names of students with birthdays that week and the whole school sings 'Happy Birthday' in English.",
            "what_zh": "每週一次，值週老師唸出本週生日的學生姓名，全校用英文齊唱 Happy Birthday。",
            "script": [
                ("Teacher: ", "This week, we celebrate the birthdays of: 王小明, 林雅婷, 陳家豪. Please stand up!"),
                ("Teacher: ", "Everyone, ready? One, two, three —"),
                ("All: ", "Happy birthday to you, happy birthday to you, happy birthday dear friends, happy birthday to you!"),
                ("Teacher: ", "Make a wish! Have a wonderful birthday week."),
            ],
            "tips_en": "Use a simple shared Google Sheet to pre-collect each week's birthdays. Pin the song lyrics on the back wall so even shy students can join.",
            "tips_zh": "用共用 Google Sheet 預先收集每週生日。把英文歌詞貼在後牆，連最害羞的學生也跟得上。",
        },
        {
            "n": 5, "color": "blue",
            "en": "Honor Class / Team Acknowledgment",
            "zh": "榮譽班級／隊伍表揚",
            "duration": "2 minutes · 兩分鐘",
            "what_en": "Recognize the cleanest classroom, the winning team in a recent contest, or a class with perfect attendance — entirely in English, then translated.",
            "what_zh": "表揚整潔比賽優勝班級、近期競賽得獎隊伍，或全勤班級——全英文表揚後再附中文翻譯。",
            "script": [
                ("Teacher: ", "This week's Cleanest Classroom Award goes to… Class 5-3! Congratulations!"),
                ("Teacher: ", "本週「整潔比賽優勝班級」是五年三班，恭喜！"),
                ("Teacher: ", "Class 5-3, please come to the front to receive the flag. Let's give them a big hand!"),
            ],
            "tips_en": "Use the same English phrasing every week — 'Congratulations!', 'Please come to the front!', 'Big hand!' Familiarity turns ceremony language into vocabulary students own.",
            "tips_zh": "每週用相同的英文句型——「Congratulations!」、「Please come to the front!」、「Big hand!」。重複的儀式語言會變成學生自己的詞彙。",
        },
        {
            "n": 6, "color": "orange",
            "en": "Festival Countdown / Cultural Moment",
            "zh": "節慶倒數／文化時刻",
            "duration": "2 minutes · 兩分鐘",
            "what_en": "On the week leading up to a festival (Mother's Day, Mid-Autumn, Christmas…), a 1-minute bilingual introduction with two key vocabulary words and one tradition.",
            "what_zh": "節慶前一週（母親節、中秋節、聖誕節⋯），用一分鐘雙語介紹兩個關鍵單字與一個習俗。",
            "script": [
                ("Announcer: ", "Next Sunday is **Mother's Day** — 母親節. The word 'appreciation' means 感謝."),
                ("Announcer: ", "On Mother's Day we show appreciation with cards, hugs, or simply by helping with the housework."),
                ("Announcer: ", "母親節我們用卡片、擁抱、或者幫忙家事，來表達感謝。"),
                ("Announcer: ", "This week's challenge: write one thank-you sentence in English for your mom. Bring it to class on Friday!"),
            ],
            "tips_en": "Tie this to the Hub's Festival English Series — 16 festival units already prepared with vocabulary and roleplay. Hand out the festival's handout to the announcer the week before.",
            "tips_zh": "搭配 Hub 的「節慶英文」16 個單元，單字、習俗、角色扮演都已準備好。播報前一週把講義交給播報員即可。",
        },
        {
            "n": 7, "color": "purple",
            "en": "Question of the Week",
            "zh": "本週大哉問",
            "duration": "1 minute · 一分鐘 (Mon) + 2 minutes · 兩分鐘 (Fri)",
            "what_en": "On Monday, the principal poses one open question in English. On Friday, two student volunteers share their thoughts. Questions can be small ('What's your favorite breakfast?') or big ('If you could change one thing about our school, what would it be?').",
            "what_zh": "週一校長以英文提出一個開放性問題，週五由兩位志願學生分享想法。問題可小可大：從「最愛的早餐」到「想改變學校的一件事」。",
            "script": [
                ("Monday — Principal: ", "This week's question: **What's something you learned this month that surprised you?**"),
                ("Principal: ", "本週的問題：這個月你學到什麼讓你覺得驚奇的事？"),
                ("Friday — Student volunteer: ", "I was surprised that Changhua is Taiwan's smallest county. 我很驚訝彰化是台灣最小的縣。"),
                ("Volunteer 2: ", "I was surprised to learn how rice grows. 我很驚訝原來米是這樣種出來的。"),
            ],
            "tips_en": "Keep a 'Question Jar' — let students submit ideas. Builds participation and gives the principal a steady stream of fresh prompts.",
            "tips_zh": "設一個「問題罐」讓學生投稿，校長有源源不絕的素材，學生也有參與感。",
        },
        {
            "n": 8, "color": "green",
            "en": "Story Minute",
            "zh": "一分鐘故事",
            "duration": "1–2 minutes · 一到兩分鐘",
            "what_en": "Once a month, a teacher or invited guest tells a 60-second story in English about a real classroom moment, a local hero, or a memory from their own school days. Theme = the school's monthly value (kindness, perseverance, curiosity).",
            "what_zh": "每月一次，老師或受邀來賓用一分鐘英文講一個真實的故事——某個課堂瞬間、在地英雄、或自己學生時代的回憶。主題對應該月校本品格教育（仁慈、堅毅、好奇心）。",
            "script": [
                ("Teacher: ", "One year, we had a new student from another city. She was quiet and didn't make friends."),
                ("Teacher: ", "But one boy in her class started saying 'Good morning' to her every single day."),
                ("Teacher: ", "After three weeks, she smiled back. After six weeks, she had three best friends."),
                ("Teacher: ", "Sometimes 'kindness' is just two small words, every day. 仁慈，有時候就是每天兩個小小的字。"),
            ],
            "tips_en": "Real stories beat abstract values. The teacher's job is to land one image students can carry to first period. End with a Chinese reflection sentence so meaning is locked in.",
            "tips_zh": "真實的故事勝過抽象的價值。老師的任務是給學生一個帶得進第一節課的畫面。結尾用中文總結，讓意義落地。",
        },
    ]

    return render_bilingual_topic(
        page_title="Morning Assembly", current_path="/resources/",
        h1_en="Morning Assembly", h1_zh="升旗 · 雙語日課",
        hero_en="The flag-raising assembly is the one school moment when <strong>every student is in the same place, at the same time, listening together</strong>. It's the highest-leverage four minutes in your bilingual program — and the easiest place to make English feel like part of the school's daily life, not a special-occasion language.",
        hero_zh="升旗是整個學校一週中唯一一段「全校學生在同一地方、同一時間、同時聆聽」的時段。也是雙語生活化最高槓桿的四分鐘——也是把英語從「特別場合的語言」轉成「校園生活一部份」最容易切入的場域。",
        moe_en="This page aligns with the Ministry of Education's <strong>2030 雙語國家政策</strong> implementation guidelines on \"Bilingual Daily Life on Campus\" (雙語生活化校園) — specifically the call to integrate English into existing school routines rather than create separate English-only events.",
        moe_zh="本頁設計對齊教育部 <strong>2030 雙語國家政策</strong>之「雙語生活化校園」實施要點——強調將英語融入既有校園作息，而非另闢英語專屬活動。",
        core_principle="升旗本來就要做的事，用雙語做就好。English doesn't add to what schools already do at assembly — it just turns existing moments into language exposure.",
        sections_h2_en="Eight ready-to-use activities", sections_h2_zh="八個立即可用的活動",
        sections_intro_en="Each activity below includes the rationale, a sample bilingual script, and an implementation tip from real Changhua campuses. Mix and match across the week — you don't need all eight on the same day.",
        sections_intro_zh="以下八個活動皆附做法、範本對話、與彰化校園的實施建議。一週搭配輪替即可，不用單日全部上場。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("A duty teacher who is comfortable saying short English lines (1–2 sentences max)", "一位能自在說 1–2 句英文短句的值週老師"),
            ("A monthly rotation schedule for student announcers (5th–6th grade) so every student gets a turn", "學生報播輪值表（高年級），讓每位學生一年至少上場一次"),
            ("A printable script binder kept on the flagpole/stage podium", "司令台或國旗台旁邊放一本可印的腳本資料夾"),
            ("Pre-recorded backup audio on a USB for days when announcers are absent", "隨身碟備好錄音備案，學生缺席時可播放"),
            ("Family-day script — a once-a-month version where parents are invited to watch", "親師日版本——每月一次邀請家長到校觀看"),
            ("Bilingual school-wide poster of the daily greetings (so even kindergarteners can chant along)", "全校張貼雙語問候語海報，讓幼稚園學生也能跟著唸"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "3,000 videos to spotlight at assembly — pick your own school's contributions for instant pride.", "meta": "For Activity 02"},
            {"href": "/festivals/", "title": "Festival English Series", "desc": "16 festival handouts — pull one the week before each holiday for Activity 06.", "meta": "For Activity 06"},
            {"href": "/resources/bilingual-campus/announcements/", "title": "Bilingual Announcements", "desc": "Sarah Thomas &amp; Susan Rose's 13-episode broadcast playlist — train your student announcers with it.", "meta": "Training material"},
        ],
    )


# ----- School Tours · 校園導覽 ------------------------------------------------
def build_school_tours():
    sections = [
        {"n": 1, "color": "blue",
         "en": "The Front Gate · 校門口", "zh": "歡迎與校史開場",
         "duration": "1–2 minutes · 一到兩分鐘",
         "what_en": "Two student guides welcome visitors at the gate, ask their country of origin, and walk them through what they'll see in the next 15 minutes.",
         "what_zh": "兩位學生導覽員在校門口迎接訪客，請對方介紹自己的國家，並告訴對方接下來 15 分鐘會看到的內容。",
         "script": [
             ("Guide A: ", "Good morning! Welcome to our school. May I ask your name?"),
             ("Guide B: ", "We are so happy to meet you. Where are you from?"),
             ("Guide A: ", "Today we will show you our library, our classroom, and our playground. Are you ready?"),
             ("Guide B: ", "Please follow us. Watch your step!"),
         ],
         "vocab": [("welcome", "歡迎"), ("school motto", "校訓"), ("security guard", "警衛"), ("principal", "校長"), ("watch your step", "小心台階")],
         "tips_en": "Pair shy and confident students together. Print the script on a small card the guides can hold — visitors expect this and it lowers anxiety.",
         "tips_zh": "讓害羞和外向的學生兩兩搭配。把腳本印在小卡片上讓導覽員握著——訪客其實期待這樣的工具，孩子也比較放鬆。"},
        {"n": 2, "color": "green",
         "en": "Principal's Office & School History · 校長室與校史", "zh": "用英文介紹百年校史",
         "duration": "2 minutes · 兩分鐘",
         "what_en": "A short introduction of the principal, the founding year, the student count (rounded), and one award or distinction the school is proud of.",
         "what_zh": "簡介校長、創校年（不寫死數字，用「百年以上」「超過五十年」等表達）、學生人數（取整數），與學校最自豪的一項榮譽。",
         "script": [
             ("Guide A: ", "This is our principal's office. Our school was founded in 1955."),
             ("Guide B: ", "We have around 200 students from Grade 1 to Grade 6."),
             ("Guide A: ", "Last year, our calligraphy team won the county championship."),
             ("Guide B: ", "Our principal will say a few words. Please come in."),
         ],
         "vocab": [("founded in", "創立於"), ("award", "榮譽"), ("champion", "冠軍"), ("around", "大約"), ("history", "歷史")],
         "tips_en": "Encourage 'around' / 'about' instead of exact numbers — easier to remember and more natural English. Update once a year, not constantly.",
         "tips_zh": "教學生用「around」「about」代替精確數字——既好記，英文也更自然。一年更新一次即可，不必每月改。"},
        {"n": 3, "color": "orange",
         "en": "The Library · 圖書館", "zh": "書區與閱讀風景",
         "duration": "2 minutes · 兩分鐘",
         "what_en": "Tour of book sections (picture books, chapter books, English shelf), reading nooks, and the weekly reading routine.",
         "what_zh": "介紹書區（繪本、章節書、英文書架）、閱讀角落，以及每週固定的閱讀時間。",
         "script": [
             ("Guide A: ", "Welcome to our library. We have over 5,000 books."),
             ("Guide B: ", "This shelf is for picture books. This one is for chapter books."),
             ("Guide A: ", "Here is our English shelf — these are books donated by foreign teachers."),
             ("Guide B: ", "Every Wednesday, we read silently here for 30 minutes. Do you like reading?"),
         ],
         "vocab": [("library", "圖書館"), ("picture book", "繪本"), ("chapter book", "章節書"), ("donate", "捐贈"), ("silent reading", "默讀")],
         "tips_en": "If your library has a 'foreign teachers donated this' shelf, lead visitors to it — they almost always smile and recognize a title.",
         "tips_zh": "如果圖書館裡有「外師捐書」專區，特別帶訪客過去看——他們幾乎一定會笑、認出某本書，氣氛立刻溫暖起來。"},
        {"n": 4, "color": "purple",
         "en": "The Classroom · 教室", "zh": "走進日常上課的空間",
         "duration": "2–3 minutes · 兩到三分鐘",
         "what_en": "Brief tour of a typical classroom — seating, smart screen, schedule on the wall, student artwork. Ideally enter a class during a non-test period so visitors see real teaching.",
         "what_zh": "簡介一般教室——座位安排、智慧螢幕、牆上課表、學生作品。最好挑非考試時段，讓訪客看見真正在上的課。",
         "script": [
             ("Guide A: ", "This is our Grade 5 classroom. There are 28 students in this class."),
             ("Guide B: ", "On the wall, you can see our weekly schedule and our class agreements."),
             ("Guide A: ", "These are paintings from our last art class. Do you like them?"),
             ("Guide B: ", "Please say hello to our classmates. Class — let's welcome our guests!"),
         ],
         "vocab": [("classroom", "教室"), ("smart screen", "智慧螢幕"), ("schedule", "課表"), ("agreement", "約定"), ("artwork", "作品")],
         "tips_en": "Brief the teacher of the chosen class one day in advance. A 20-second classroom interaction often becomes the visitor's strongest memory of the tour.",
         "tips_zh": "提前一天通知該班導師。教室裡短短 20 秒的互動，往往是訪客整趟參訪最印象深刻的一段。"},
        {"n": 5, "color": "blue",
         "en": "The Cafeteria · 學生餐廳", "zh": "用英文介紹台灣校園午餐",
         "duration": "1–2 minutes · 一到兩分鐘",
         "what_en": "Visitors are almost always curious about Taiwan's school lunch system. Show the kitchen window, today's menu, and the recycling station.",
         "what_zh": "訪客對台灣的營養午餐制度幾乎都好奇。帶他們看廚房窗口、今日菜單、與餐後分類回收站。",
         "script": [
             ("Guide A: ", "This is our cafeteria. We eat lunch in our classroom, but the food is prepared here."),
             ("Guide B: ", "Today's lunch is rice, fish, vegetables, and miso soup."),
             ("Guide A: ", "After eating, every class takes turns washing the lunch boxes."),
             ("Guide B: ", "We separate food waste, plastic, and paper. The school is very strict about this!"),
         ],
         "vocab": [("cafeteria", "餐廳"), ("school lunch", "營養午餐"), ("menu", "菜單"), ("recycle", "回收"), ("food waste", "廚餘")],
         "tips_en": "If visitors arrive at lunch time, invite them to eat with the students. The shared meal is the most memorable bilingual exchange of the day.",
         "tips_zh": "若訪客剛好在午餐時間到，邀他們和學生一起吃飯。共桌一餐，比任何導覽都更能成就雙語交流。"},
        {"n": 6, "color": "green",
         "en": "The Playground · 操場", "zh": "全校最熱鬧的空間",
         "duration": "1–2 minutes · 一到兩分鐘",
         "what_en": "End the tour at the playground — running track, basketball court, weekly assembly area. Open question time here under the trees.",
         "what_zh": "在操場作為導覽尾聲——跑道、籃球場、每週升旗集合處。在大樹下開放訪客提問。",
         "script": [
             ("Guide A: ", "This is where we have morning assembly every Monday."),
             ("Guide B: ", "The basketball court is for Grades 5 and 6 during recess."),
             ("Guide A: ", "We have a 200-meter track around the field. Some students run every morning."),
             ("Guide B: ", "Do you have any questions about our school? We will try our best to answer!"),
         ],
         "vocab": [("playground", "操場"), ("track", "跑道"), ("basketball court", "籃球場"), ("recess", "下課時間"), ("question", "問題")],
         "tips_en": "Always end at the playground with open Q&A. Students who were quiet during the scripted tour often light up when asked about their hobbies or favorite teacher.",
         "tips_zh": "導覽結尾一定要回到操場開放問答。腳本講過的孩子常會緊張，但被問「最喜歡哪位老師、最愛什麼運動」時，反而閃閃發亮。"},
    ]
    return render_bilingual_topic(
        page_title="School Tours", current_path="/resources/",
        h1_en="School Tours", h1_zh="校園導覽 · 雙語走讀",
        hero_en="A campus tour led by students is one of the highest-confidence English-speaking moments of the year. Foreign visitors, parents, and sister-school delegates often visit Taiwanese schools — turn that visit into a vocabulary-rich student stage instead of a teacher monologue.",
        hero_zh="學生帶隊導覽校園，是全年最能讓學生展現英文自信的場合之一。外國訪客、家長、姊妹校代表常造訪台灣學校——把這個場合留給學生當主角，比老師獨白更能累積詞彙。",
        moe_en="Aligns with Bilingual Daily Life on Campus implementation guideline 4: \"Use existing school resources as bilingual learning materials.\" School tours convert physical campus assets into living English vocabulary.",
        moe_zh="對齊雙語生活化校園實施要點第 4 條：「善用校園既有資源作為雙語學習素材」。校園導覽把實體校園資產轉化為活的英文詞彙。",
        core_principle="學校本來就要接待訪客，讓學生當主角就好。Tour-giving turns visitor reception into a student-led teachable moment instead of a teacher-only task.",
        sections_h2_en="Six classroom-ready stations", sections_h2_zh="六個立即上線的雙語站",
        sections_intro_en="Each station below comes with a bilingual script, key vocabulary, and a tip from real Changhua campuses. Pair students up, hand them the cards, and rehearse twice in English class before the visit.",
        sections_intro_zh="以下六站皆附中英對話、關鍵詞彙、與彰化校園的實施建議。學生兩兩搭配，握著小卡，英文課裡彩排兩次即可上場。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Master vocabulary cards (laminated, one per station)", "每站詞彙小卡（過塑、好攜帶）"),
            ("Two rehearsal sessions in English class before the visit", "訪客來訪前在英文課裡彩排兩次"),
            ("Student guide pairs — never solo", "學生導覽員兩兩搭檔——不單獨上場"),
            ("Backup teacher to step in if a student freezes", "備援老師站在後方，學生卡住時可即時銜接"),
            ("Photo permission noted in the tour announcement", "事先在訪客通知中註明拍照同意事項"),
            ("Bilingual visitor feedback form (4 questions, takes 2 min)", "雙語訪客回饋單（四題，兩分鐘填完）"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "Pull station-specific vocabulary from the Hub's 3,000 video library to brief students.", "meta": "Vocabulary source"},
            {"href": "/resources/bilingual-campus/morning-assembly/", "title": "Morning Assembly", "desc": "Use morning assembly the week before a visit to announce the tour and recruit student guides.", "meta": "Pre-visit ramp-up"},
            {"href": "/resources/bilingual-campus/intl-sister-school/", "title": "International Sister School", "desc": "Sister-school delegates are the most common tour audience — see the sister-school workflow.", "meta": "Frequent audience"},
        ],
    )


# ----- English Self-Introduction · 英文自介 -----------------------------------
def build_english_self_intro():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Grade 1–2 Template · 低年級範本", "zh": "四句話起步",
         "duration": "4 sentences · 30 seconds",
         "what_en": "The simplest self-introduction — four sentences students can master in two weeks. Builds on what they already know from textbooks plus one favorite item to make it personal.",
         "what_zh": "最簡單的自我介紹——四句話，兩週內可以背熟。建立在課本既有句型上，加一個「最愛」讓內容個人化。",
         "script": [
             ("Student: ", "Hello! My name is Lin Yating."),
             ("Student: ", "I am eight years old."),
             ("Student: ", "I am in Grade 2, Class 3."),
             ("Student: ", "My favorite animal is a panda. Thank you!"),
         ],
         "vocab": [("hello", "你好"), ("name", "名字"), ("years old", "歲"), ("favorite", "最愛的"), ("thank you", "謝謝")],
         "tips_en": "Don't correct pronunciation in performance — only in rehearsal. The goal at this age is courage, not accuracy. Applaud loudly after every student.",
         "tips_zh": "上台不糾音，只在練習時糾。這個年紀的目標是「敢開口」，不是「完美」。每位學生講完都熱烈鼓掌。"},
        {"n": 2, "color": "green",
         "en": "Grade 3–4 Template · 中年級範本", "zh": "擴充到家庭與興趣",
         "duration": "8 sentences · 1 minute",
         "what_en": "Add family members, school, and one hobby. Introduce the pattern 'I like ___ because ___.' to give students a tool for expansion.",
         "what_zh": "加入家庭成員、就讀學校、與一個興趣。教「I like ___ because ___」的擴充句型，給學生延展的工具。",
         "script": [
             ("Student: ", "Hi everyone! I am Chen Jiahao, and I am ten years old."),
             ("Student: ", "I study at Tianzhong Elementary School. I am in Grade 4."),
             ("Student: ", "I have one sister and a small dog at home."),
             ("Student: ", "I like drawing because it helps me feel calm. My favorite color is blue."),
             ("Student: ", "On weekends, I play badminton with my dad. Thanks for listening!"),
         ],
         "vocab": [("study at", "就讀於"), ("hobby", "興趣"), ("because", "因為"), ("weekend", "週末"), ("listen", "聆聽")],
         "tips_en": "Make 'because' the new word of the month — it transforms a list of facts into a personality. The first time a student uses 'because' unprompted, mark the moment.",
         "tips_zh": "把「because」當成本月關鍵字——它把「事實清單」變成「個性」。學生第一次自然用出 because，要特別記下。"},
        {"n": 3, "color": "orange",
         "en": "Grade 5–6 Template · 高年級範本", "zh": "加入夢想與特殊技能",
         "duration": "12 sentences · 90 seconds",
         "what_en": "Move beyond facts to dreams and opinions. Add a future-tense sentence ('I want to be ___') and an opinion sentence ('I think ___ is important').",
         "what_zh": "從「事實」進階到「夢想與觀點」。加入未來式（I want to be ___）與意見句（I think ___ is important）。",
         "script": [
             ("Student: ", "Good afternoon! I'm Wang Yuting, a sixth grader from Lukang Elementary School."),
             ("Student: ", "My family is small — just my mom, my older brother, and me."),
             ("Student: ", "I love reading mystery novels, and I have read more than thirty books this year."),
             ("Student: ", "In the future, I want to be a journalist because I think the truth is important."),
             ("Student: ", "My special skill is calligraphy. I have been practicing for four years."),
             ("Student: ", "Thank you for listening. Do you have any questions for me?"),
         ],
         "vocab": [("in the future", "未來"), ("journalist", "記者"), ("truth", "真相"), ("special skill", "特長"), ("practice", "練習")],
         "tips_en": "End with a question to the audience — this turns a monologue into a conversation and trains students to receive English questions, not just deliver scripts.",
         "tips_zh": "結尾向聽眾提問——把獨白變成對話，也訓練學生「接英文問題」的能力，不只是背稿。"},
        {"n": 4, "color": "purple",
         "en": "Junior High Template · 國中範本", "zh": "段落型自介",
         "duration": "Connected paragraph · 2 minutes",
         "what_en": "Move from sentence-list format to a connected paragraph with transition words. Add a 'something not on the resume' sentence — a memorable detail that makes the student a person, not a profile.",
         "what_zh": "從「句子清單」進入「段落結構」，加入轉折詞。加一句「履歷上看不到的事」——一個讓聽眾記住的個人細節。",
         "script": [
             ("Student: ", "Hello. My name is Lin Pinghao, and I'm a ninth grader at Yuanlin Junior High."),
             ("Student: ", "I've grown up here in Changhua, and I think it's a place that gets quieter the more you explore it."),
             ("Student: ", "In addition to my schoolwork, I'm part of the chorus and the eco club."),
             ("Student: ", "However, what I really love — and few people know this — is cooking with my grandmother on Sundays."),
             ("Student: ", "I'd like to study food science in the future, so this self-introduction is also a small thank-you to her."),
         ],
         "vocab": [("in addition to", "除了"), ("however", "然而"), ("get quieter", "變得安靜"), ("food science", "食品科學"), ("thank-you", "感謝")],
         "tips_en": "Coach students to slow down at the 'however' sentence — that's where the personality lives. Speeding through the resume part is fine; the personal sentence is the one to land.",
         "tips_zh": "教學生在「however」那句放慢——個性就藏在這裡。前面條列式的部分可以快，那一句個人話一定要落得到。"},
        {"n": 5, "color": "blue",
         "en": "Presentation Tips · 上台技巧", "zh": "讓內容被聽見的方法",
         "duration": "Coaching session · 30 minutes",
         "what_en": "Four habits that turn an OK self-intro into a confident one — eye contact (look at 3 people), pacing (one second between sentences), volume (the back of the room must hear you), and smile (just at the start and end).",
         "what_zh": "四個習慣，把普通自介變成自信自介——眼神（看三個聽眾）、節奏（句句之間停一秒）、音量（最後排聽得到）、微笑（開頭與結尾各一次）。",
         "script": [
             ("Coach: ", "Look up. Choose three people in the room — front-left, center, back-right."),
             ("Coach: ", "Between each sentence, count to one in your head. The pause is where listeners catch up."),
             ("Coach: ", "Smile at the start, smile at the end. In the middle, just be calm."),
             ("Coach: ", "If you make a mistake, do not say sorry. Just keep going."),
         ],
         "vocab": [("eye contact", "眼神接觸"), ("pause", "停頓"), ("volume", "音量"), ("calm", "冷靜"), ("keep going", "繼續")],
         "tips_en": "Record students with a phone, then watch together once. Most fix their own habits in a single viewing — much faster than verbal feedback from the teacher.",
         "tips_zh": "用手機錄下學生練習，一起看一次回放。多數學生會自己發現問題並修正，比老師口頭糾正快得多。"},
    ]
    return render_bilingual_topic(
        page_title="English Self-Introduction", current_path="/resources/",
        h1_en="English Self-Introduction", h1_zh="英文自介 · 自信表達的第一塊磚",
        hero_en="A confident English self-introduction is the foundation of every other English speaking moment — sister-school meet-ups, contest entries, foreign visitors. We teach it in stages: 4 sentences in Grade 1, expanding to 12+ sentences by Grade 6, and a connected paragraph in junior high.",
        hero_zh="一段自信的英文自介，是其他所有英文口說場合的基礎——姊妹校連線、比賽、外賓接待都要用。我們分階段教：一年級 4 句，到六年級擴展為 12 句以上，國中則進入段落結構。",
        moe_en="Speaking ability is one of the four core competencies of the 12-year Basic Education English curriculum. Self-introduction is the highest-frequency speaking task across a student's school career.",
        moe_zh="口說能力是十二年國教英文領域四大核心素養之一。自我介紹是學生整個求學歷程中使用頻率最高的口說任務。",
        core_principle="自介不是「會講英文」，是「敢開口」的第一塊磚。Confidence is the deliverable; vocabulary follows.",
        sections_h2_en="Templates by grade band", sections_h2_zh="各年段範本",
        sections_intro_en="The same task — introduce yourself in English — scales across grade bands. Each template below builds on the previous one, so a Grade 5 student already knows the Grade 1 foundation. Print the template, rehearse, record, refine.",
        sections_intro_zh="同樣是「英文自介」，不同年段有不同深度。下方範本層層遞進，五年級的學生本就會一年級的基礎。印出來、彩排、錄影、修正。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Grade-band template printed for each student", "每位學生一張該年段範本"),
            ("Recording phone (the student's own is fine)", "錄影手機（學生自己的就行）"),
            ("Pair rehearsal partner — every student practices with one other", "兩兩搭檔練習——每位學生都和另一位演練"),
            ("Audience etiquette taught once at the start of the year", "聽眾禮儀於開學時教一次"),
            ("Application moments mapped out (contest, visitor, sister-school meet)", "羅列出可用的場合（比賽、訪客、姊妹校連線）"),
            ("Yearly recording saved to the student portfolio", "每年錄影歸檔到學生學習履歷"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/bilingual-campus/morning-assembly/", "title": "Morning Assembly", "desc": "Have the week's student announcer open with a 30-second self-intro — built-in practice for every announcer.", "meta": "Built-in practice"},
            {"href": "/resources/bilingual-campus/intl-sister-school/", "title": "International Sister School", "desc": "Self-intro is the centerpiece of every sister-school first contact. Pair this page with the sister-school workflow.", "meta": "Highest-stakes use"},
            {"href": "/resources/bilingual-campus/school-news/", "title": "School News", "desc": "Student anchors deliver a sign-off self-intro each episode — a weekly practice loop.", "meta": "Weekly practice"},
        ],
    )


# ----- English Reading Corner · 英文閱讀角 ------------------------------------
def build_english_reading_corner():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Setting Up the Space · 空間規劃", "zh": "從一張地毯開始",
         "duration": "One-time setup · 4–6 hours",
         "what_en": "The physical setup matters more than the book count. A rug, soft lighting, and labeled shelves at child height invite use; a tall locked bookshelf does the opposite.",
         "what_zh": "空間規劃比藏書量更關鍵。一張地毯、暖光、與學童高度可及的標示書架最能吸引使用；高大上鎖的書櫃則完全相反。",
         "script": [
             ("Teacher (to class): ", "This is our new English reading corner. Take off your shoes when you come in."),
             ("Teacher: ", "Books with a blue dot are Level 1 — these are the easiest. Red dots are harder."),
             ("Teacher: ", "Please pick a book, sit on the rug, and read silently for ten minutes."),
             ("Teacher: ", "When you finish, write the title and one sentence in your reading log."),
         ],
         "vocab": [("rug", "地毯"), ("shelf", "書架"), ("label", "標籤"), ("level", "級數"), ("reading log", "閱讀紀錄")],
         "tips_en": "Spend 60% of your budget on the rug, lighting, and shelving. Books can be donated, borrowed from the school library, or rotated quarterly. The corner that gets used is the corner that feels good.",
         "tips_zh": "60% 的預算花在地毯、燈光、書架。書可以收捐贈、跟學校圖書館借、每季輪換。會被使用的閱讀角，是「待起來舒服」的閱讀角。"},
        {"n": 2, "color": "green",
         "en": "Daily 10-Minute Reading Routine · 每日 10 分鐘", "zh": "早自修就讀",
         "duration": "10 minutes · daily",
         "what_en": "The single most effective routine is silent reading at the start of homeroom. No questions, no quiz, no reading log on the first month — just the habit.",
         "what_zh": "單一最有效的閱讀慣性：早自修一進教室就默讀。第一個月不問問題、不考試、不寫紀錄——就只是養成習慣。",
         "script": [
             ("Teacher: ", "Good morning. Please get your reading book from your bag."),
             ("Teacher: ", "We will read silently for ten minutes. The timer will tell us when to stop."),
             ("Teacher: ", "If you finish a book, place it back on the shelf and pick a new one quietly."),
             ("Teacher (after 10 min): ", "Stop. Mark your page. Tell your partner one word you saw today."),
         ],
         "vocab": [("silent reading", "默讀"), ("timer", "計時器"), ("mark your page", "做頁標"), ("partner", "搭檔"), ("one word", "一個字")],
         "tips_en": "Resist the urge to assess. The day you add a quiz is the day half the class starts faking. Trust the routine — measurable gains show up in 8 weeks.",
         "tips_zh": "忍住「想評量」的衝動。一加考試，一半的孩子立刻開始假裝。相信習慣本身——8 週後成效自然顯現。"},
        {"n": 3, "color": "orange",
         "en": "Book Curation by Level · 分級選書", "zh": "讓孩子找得到自己讀得懂的書",
         "duration": "Once per term · 2 hours",
         "what_en": "Color-code books by level (blue dot = beginner, green = intermediate, red = advanced). Students self-select; the teacher only nudges the ones who pick too easy or too hard for three weeks in a row.",
         "what_zh": "用顏色貼紙標示級數（藍 = 入門、綠 = 中級、紅 = 進階）。學生自選；老師只在連續三週都選太簡單或太難的孩子身上輕輕提醒。",
         "script": [
             ("Teacher: ", "If you read a blue-dot book and it felt easy, try a green-dot book next time."),
             ("Teacher: ", "If you read a red-dot book and gave up, that's okay. Choose a green one."),
             ("Teacher: ", "There is no right level. There is only the level that helps you finish."),
             ("Student (asking): ", "Teacher, what level am I? "),
             ("Teacher: ", "The level that lets you read three sentences without stopping."),
         ],
         "vocab": [("beginner", "入門"), ("intermediate", "中級"), ("advanced", "進階"), ("give up", "放棄"), ("right level", "適合的級數")],
         "tips_en": "Don't tell students their official 'level' — it becomes an identity. The phrase 'three sentences without stopping' is a self-test they can use anywhere, any book.",
         "tips_zh": "不要告訴孩子他「正式的級數」——會被當成身分。教他們用「三句話不停下來」當作自我檢測，到哪本書都能用。"},
        {"n": 4, "color": "purple",
         "en": "Reading Challenge Chart · 閱讀挑戰表", "zh": "讓進度被看見",
         "duration": "Ongoing · resets each term",
         "what_en": "A wall chart with every student's name and a row of empty boxes. One sticker per finished book — small, simple, visible. Resets each term so no one falls 'too far behind' for the year.",
         "what_zh": "一張掛在牆上的表，每位學生一行空格。讀完一本貼一張貼紙——小、簡單、看得見。每學期重新開始，沒人會「整年落後太多」。",
         "script": [
             ("Teacher: ", "You finished 'Frog and Toad Are Friends'? Excellent. Pick a sticker."),
             ("Student: ", "Can I have the dinosaur one?"),
             ("Teacher: ", "Of course. Put it in the box next to your name."),
             ("Teacher (to class): ", "Look at our chart growing. Every sticker is a book that someone finished. That is the whole goal."),
         ],
         "vocab": [("chart", "挑戰表"), ("sticker", "貼紙"), ("finished", "完成"), ("excellent", "很棒"), ("the whole goal", "全部的目標")],
         "tips_en": "Resist 'prizes for reading the most.' Competition kills intrinsic motivation. Stickers themselves are enough — the visible row is the reward.",
         "tips_zh": "不要設「讀最多得獎」。競賽會殺死內在動機。貼紙本身就夠了——那一行看得見的成果，就是獎賞。"},
        {"n": 5, "color": "blue",
         "en": "Book Sharing Time · 分享時間", "zh": "讓書活起來",
         "duration": "10 minutes · weekly (Friday)",
         "what_en": "Every Friday, three students share one sentence about a book they finished this week. Just one sentence — recommend it or don't, but be specific.",
         "what_zh": "每週五，三位學生各用一句話分享本週讀完的書。就一句——推薦或不推薦，但要具體。",
         "script": [
             ("Student 1: ", "I read 'Charlotte's Web.' The ending made me cry, but in a good way."),
             ("Student 2: ", "I read 'Diary of a Wimpy Kid.' It is funny but a little too long for me."),
             ("Student 3: ", "I read a picture book about a cat who paints. I want to find more by this writer."),
             ("Teacher: ", "Three books, three honest opinions. That is reading. Thank you, everyone."),
         ],
         "vocab": [("recommend", "推薦"), ("ending", "結局"), ("opinion", "意見"), ("writer", "作者"), ("specific", "具體")],
         "tips_en": "Teach 'specific' over 'positive' — a real opinion ('too long for me') is more valuable than fake praise ('it was good'). Reading becomes honest.",
         "tips_zh": "教孩子「具體」比「正向」更重要——真實的意見（「對我來說太長了」）比客套（「很好看」）有價值。閱讀才會誠實。"},
    ]
    return render_bilingual_topic(
        page_title="English Reading Corner", current_path="/resources/",
        h1_en="English Reading Corner", h1_zh="英文閱讀角 · 一個學年讀的書比課本多",
        hero_en="A well-curated English reading corner reads more books across a school year than any textbook can cover. Don't just put a bookshelf in the corner — design the routines that make students return to it.",
        hero_zh="一個用心策劃的英文閱讀角，一整學年讀完的書比課本多得多。重點不是把書架放進角落，而是設計讓學生主動回來的閱讀慣性。",
        moe_en="The reading-corner model aligns with the 12-year curriculum's emphasis on self-directed learning and multi-modal literacy, plus the 2030 bilingual policy's principle of low-stakes, high-frequency English exposure.",
        moe_zh="閱讀角模式對齊十二年國教「自主學習」與「多元識讀」素養，並符合 2030 雙語政策「低門檻、高頻率英文接觸」的原則。",
        core_principle="閱讀角的勝負在「慣性」，不在「藏書量」。The win condition is the habit, not the bookshelf inventory.",
        sections_h2_en="Five steps to a working corner", sections_h2_zh="五個步驟，做出能用的閱讀角",
        sections_intro_en="Each step below is in order — the space, then the routine, then curation, then visibility, then sharing. Skip a step and the corner stalls. Start with one class for a term before scaling.",
        sections_intro_zh="以下五步有順序——先空間，再慣性，再分級，再可視化，再分享。跳一步就會停滯。先從一個班做一學期，再擴展。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("30+ books appropriate to school size", "符合學校規模的 30 本以上書籍"),
            ("Sign-out system (paper sheet or QR code)", "借書登記制（紙本或 QR Code）"),
            ("Weekly book swap with another class", "與另一班每週交換書籍"),
            ("FET-led \"book talk\" twice per month", "外師主持的 Book Talk，每月兩次"),
            ("Parent donation drive for used English books", "向家長徵集二手英文書"),
            ("Yearly inventory and level audit", "每年盤點與重新分級"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/books-for-taiwan/", "title": "Books for Taiwan", "desc": "Long-running donation initiative — apply for English book bundles for your reading corner.", "meta": "Book source"},
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "Pull a 'reading-related' word from the Hub for daily warm-ups before silent reading.", "meta": "Warm-up vocab"},
            {"href": "/resources/eric-berman/", "title": "Eric Berman", "desc": "Storytelling teacher — his style is a model for FET-led book talks.", "meta": "Storytelling model"},
        ],
    )


# ----- Amazing Changhua · 探索彰化 -------------------------------------------
def build_amazing_changhua():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Lukang Old Street · 鹿港老街", "zh": "三百年的廟宇與街屋",
         "duration": "Field-trip script · 3 hours",
         "what_en": "Lukang's 300-year-old streets and temples — Mazu Temple, Longshan Temple, Nine-Turn Lane — are Changhua's most photographed cultural site. A bilingual student-led tour for visitors makes the place visible to the world.",
         "what_zh": "鹿港三百年的老街與廟宇——天后宮、龍山寺、九曲巷——是彰化最常被拍攝的文化景點。學生帶外賓走一趟雙語導覽，等於把這個地方介紹給世界。",
         "script": [
             ("Student guide: ", "Welcome to Lukang. This town is over 300 years old."),
             ("Guide: ", "This is Mazu Temple. Mazu is the goddess of the sea. Fishermen and sailors pray here for safe trips."),
             ("Guide: ", "These small alleys are called 'Nine-Turn Lane' — they were built narrow to slow down sea winds."),
             ("Guide: ", "Before we leave, try a bowl of 'meat ball' — Lukang's most famous food."),
         ],
         "vocab": [("temple", "廟宇"), ("goddess", "女神"), ("pray", "祈禱"), ("alley", "巷弄"), ("over 300 years old", "三百多年歷史")],
         "tips_en": "Pre-teach 'over' as in 'over 300 years' — students often default to exact numbers and freeze when uncertain. 'Over' is a confidence word.",
         "tips_zh": "提前教「over」（如 over 300 years）——學生常執著精確數字，不確定就卡住。「Over」是個讓孩子自信的詞。"},
        {"n": 2, "color": "green",
         "en": "Bagua Mountain & The Great Buddha · 八卦山大佛", "zh": "彰化的標誌",
         "duration": "Landmark intro · 1–2 minutes",
         "what_en": "The 22-meter Great Buddha statue on Bagua Mountain is visible from anywhere in Changhua City. Every Changhua child should be able to introduce it in English to a visitor.",
         "what_zh": "八卦山上 22 公尺高的大佛像，從彰化市任何角落都看得見。每位彰化的孩子都該能用英文向訪客介紹這座像。",
         "script": [
             ("Student: ", "This is the Great Buddha of Bagua Mountain. It is 22 meters tall."),
             ("Student: ", "From this hill, you can see all of Changhua City."),
             ("Student: ", "The statue was built in 1961 — older than my grandfather."),
             ("Student: ", "Many families come here on Sundays. The view at sunset is the most beautiful."),
         ],
         "vocab": [("statue", "雕像"), ("meters tall", "公尺高"), ("hill", "山丘"), ("view", "景色"), ("sunset", "夕陽")],
         "tips_en": "The phrase 'older than my grandfather' is a child-natural way to express age. Use it as a model — every Changhua landmark gets a personal comparison.",
         "tips_zh": "「older than my grandfather」是孩子最自然的年齡表達方式。當示範句——彰化每個地標都可以配一個個人比喻。"},
        {"n": 3, "color": "orange",
         "en": "Rice Country · 米鄉", "zh": "彰化平原的兩季稻",
         "duration": "Field-trip or classroom · varies",
         "what_en": "Changhua plains produce some of Taiwan's best rice — Erlin and Tianzhong are nationally known. Help students introduce the two-crop calendar (March planting, July first harvest; August planting, December second harvest).",
         "what_zh": "彰化平原出產台灣最好的米——二林、田中全國知名。讓學生介紹兩季稻的時程（三月種，七月收一期；八月種，十二月收二期）。",
         "script": [
             ("Student: ", "Changhua is a famous rice region in Taiwan."),
             ("Student: ", "We have two crops a year — one in summer, one in winter."),
             ("Student: ", "In March, farmers plant young rice in the paddy field."),
             ("Student: ", "In July, the rice turns golden. That is harvest time. The whole village smells like rice."),
         ],
         "vocab": [("paddy field", "稻田"), ("plant", "種植"), ("harvest", "收成"), ("golden", "金黃色的"), ("village", "村莊")],
         "tips_en": "If your school has a rice paddy nearby, a 30-minute walk for vocabulary on-site beats any classroom lesson. Smell, color, sound all become language anchors.",
         "tips_zh": "如果學校附近有稻田，30 分鐘的現場走讀勝過任何教室課。氣味、顏色、聲音都成為英文詞彙的記憶錨點。"},
        {"n": 4, "color": "purple",
         "en": "Mazu Pilgrimage · 媽祖遶境", "zh": "九天八夜的信仰之旅",
         "duration": "Annual · March",
         "what_en": "The 9-day Mazu pilgrimage from Dajia to Beigang crosses Changhua every March. It's the largest religious procession in Taiwan and one of the most distinctive cultural events students can speak about with pride.",
         "what_zh": "每年三月，從大甲到北港九天八夜的媽祖遶境會穿越彰化。這是全台最大的宗教遶境，也是學生最能驕傲介紹的文化盛事。",
         "script": [
             ("Student: ", "Every March, the Mazu Pilgrimage passes through our town."),
             ("Student: ", "Mazu is the goddess who protects fishermen and travelers."),
             ("Student: ", "The pilgrimage is nine days long. Devotees walk over 300 kilometers."),
             ("Student: ", "Our family gives food and water to walkers as they pass our street. It is a way of saying thank you."),
         ],
         "vocab": [("pilgrimage", "遶境"), ("devotee", "信徒"), ("palanquin", "神轎"), ("blessing", "祝福"), ("hospitality", "好客")],
         "tips_en": "Many students have personally walked some of the pilgrimage with their family. Invite those students to share — first-person experience beats any textbook explanation of culture.",
         "tips_zh": "很多學生其實跟家人走過部分遶境。邀請這些學生分享——第一人稱的經驗，遠勝任何課本上的文化解說。"},
        {"n": 5, "color": "blue",
         "en": "Local Food · 在地小吃", "zh": "從一碗肉圓開始",
         "duration": "Tasting + presentation · 45 minutes",
         "what_en": "Changhua's signature foods — meat balls (rou-yuan), oyster omelette, baked egg cookies — are the easiest entry point for cultural English. Pair a tasting with student-prepared mini-introductions.",
         "what_zh": "彰化的招牌小吃——肉圓、蚵仔煎、蛋黃酥——是文化英文最容易切入的點。安排品嚐活動，搭配學生事先準備的雙語小簡介。",
         "script": [
             ("Student: ", "This is 'rou-yuan,' or meat ball. It is Changhua's most famous food."),
             ("Student: ", "The outside is made from sweet potato flour. It is chewy and a little soft."),
             ("Student: ", "Inside, there is pork, mushroom, and a special sauce."),
             ("Student: ", "Try one bite. If you like it, the shop on the corner has been making them for sixty years."),
         ],
         "vocab": [("meat ball / rou-yuan", "肉圓"), ("oyster omelette", "蚵仔煎"), ("chewy", "Q 彈"), ("sauce", "醬料"), ("signature dish", "招牌菜")],
         "tips_en": "Don't translate 'rou-yuan' to 'meat ball' alone — students should learn that some food names stay in Taiwanese. 'Rou-yuan' IS the word; the English translation is the gloss.",
         "tips_zh": "不要把「肉圓」直譯成 meat ball 就結束——讓學生知道有些食物名稱保留台語讀音才正確。「Rou-yuan」就是那個字；meat ball 只是補充解釋。"},
    ]
    return render_bilingual_topic(
        page_title="Amazing Changhua", current_path="/resources/",
        h1_en="Amazing Changhua", h1_zh="探索彰化 · 用英文認識家鄉",
        hero_en="Bilingual education isn't just about importing global English — it's about telling our own story to the world. Changhua's temples, food, agriculture, and festivals deserve English words so students can become ambassadors of the place they come from.",
        hero_zh="雙語教育不只是「進口國際英文」，更是「把自己的故事用英文講出去」。彰化的廟宇、美食、農業、節慶值得有英文版本，讓學生成為自己家鄉的文化大使。",
        moe_en="Aligns with the Bilingual Daily Life guideline on \"Local culture in bilingual education\" and the 2030 policy's call to integrate Taiwanese content — not only imported topics — into English learning.",
        moe_zh="對齊雙語生活化「本土文化融入雙語教育」要點，並回應 2030 政策強調「將台灣本土內容融入英語學習」、而非單向引入外國主題的訴求。",
        core_principle="學生不只是學「英文」，更是用英文當「家鄉的代言人」。Students aren't only learning English — they're becoming the place where they live, told in another language.",
        sections_h2_en="Five Changhua icons, ready for English", sections_h2_zh="五個彰化代表，配好英文",
        sections_intro_en="Each section below gives a bilingual introduction script, the most useful vocabulary, and an implementation tip — for when foreign visitors come, for sister-school exchanges, or simply as cultural enrichment in regular English class.",
        sections_intro_zh="以下五個主題各附中英對話、最實用的詞彙、與實施建議——可用於外賓接待、姊妹校交流，或日常英文課的文化加值。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Field trip pre-vocab session (2 weeks before visit)", "校外教學前兩週的詞彙預習課"),
            ("Student-made bilingual brochure for each landmark", "每個景點一份學生製作的雙語小手冊"),
            ("\"Show a foreigner around Changhua\" Grade 6 culminating project", "六年級畢業專案：用英文帶外國人玩彰化"),
            ("Sister-school exchange topic: my hometown", "姊妹校交流題目：我的家鄉"),
            ("Annual Changhua Day with English bilingual showcase", "每年一次彰化日，搭配英文雙語展演"),
            ("Local elder interview project — record family memory", "在地耆老訪談——記錄家族記憶"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/about-changhua/", "title": "About Changhua", "desc": "Hub's main Changhua background page — geography, history, schools, deep facts.", "meta": "Background reading"},
            {"href": "/festivals/", "title": "Festival English Series", "desc": "Mid-Autumn, Lantern, and Mazu festival units — perfectly aligned with this page's Mazu section.", "meta": "Festival deep-dives"},
            {"href": "/resources/bilingual-campus/school-tours/", "title": "School Tours", "desc": "Many sister-school delegates come to see Changhua — combine the school tour with an Amazing Changhua field trip.", "meta": "Visitor pairing"},
        ],
    )


# ----- School News · 校園新聞 -------------------------------------------------
def build_school_news():
    sections = [
        {"n": 1, "color": "blue",
         "en": "News Team Roles · 新聞部成員", "zh": "六個角色，全班都有任務",
         "duration": "Team setup · 45 minutes",
         "what_en": "Six rotating roles let an entire class participate without overcrowding the screen — anchor, on-location reporter, weather, sports, camera operator, and an editor who never appears.",
         "what_zh": "六個輪值角色，全班都能參與、又不會擠在鏡頭前——主播、外景記者、氣象、體育、攝影、後製剪輯（不露臉）。",
         "script": [
             ("Anchor: ", "Good morning! I'm Yuting, your anchor today. Here is this week's top story."),
             ("Reporter (on location): ", "I'm at the playground. Yesterday our basketball team played their first game of the season."),
             ("Weather: ", "Today will be sunny, with a high of 26 degrees. Tomorrow, rain in the afternoon."),
             ("Sports: ", "In sports news, the volleyball team is preparing for the county tournament next week."),
         ],
         "vocab": [("anchor", "主播"), ("on location", "外景"), ("top story", "頭條"), ("season", "賽季"), ("tournament", "錦標賽")],
         "tips_en": "Rotate roles every two episodes — every student should sit in every chair across a semester. The shy student often becomes the best editor.",
         "tips_zh": "每兩集輪換角色——一學期下來每位學生都坐過每個位置。最害羞的孩子往往成為最好的剪輯師。"},
        {"n": 2, "color": "green",
         "en": "Weekly Episode Template · 每週節目模板", "zh": "3 分鐘的結構",
         "duration": "Episode runtime · 3 minutes",
         "what_en": "A consistent 3-minute structure: 30s opener → 50s segment 1 → 50s segment 2 → 50s segment 3 → 20s sign-off. The same shape every week means students don't have to reinvent format.",
         "what_zh": "固定的 3 分鐘結構：30 秒開場 → 50 秒第一段 → 50 秒第二段 → 50 秒第三段 → 20 秒結尾。每週同樣節奏，學生不必每次重新發明格式。",
         "script": [
             ("Anchor: ", "Welcome back to Changhua School News. I'm Yuting and this is your three-minute weekly update."),
             ("Anchor: ", "Our top story this week: the bilingual reading marathon results. Let's go to our reporter on location."),
             ("Reporter: ", "[on location segment] ..."),
             ("Anchor: ", "That's all from us today. See you next Monday morning. Have a great week!"),
         ],
         "vocab": [("segment", "段落"), ("transition", "轉場"), ("update", "更新"), ("throw to", "切到"), ("sign off", "結尾"),],
         "tips_en": "The hardest part isn't reading — it's the smooth transition between segments. Practice transitions twice for every once you practice the segments themselves.",
         "tips_zh": "最難的不是讀稿，是段落之間的銜接。轉場練習時間應該是「段落練習」的兩倍。"},
        {"n": 3, "color": "orange",
         "en": "Anchor Script Template · 主播稿模板", "zh": "從歡迎到再見",
         "duration": "Script prep · 90 minutes weekly",
         "what_en": "A reusable Word document with [BLANK] fields for the week's content. Anchors only need to fill in the story names, dates, and names — the connecting language is already there.",
         "what_zh": "一份可重複使用的 Word 模板，預留 [BLANK] 待填位置。主播只需填入本週的故事、日期、姓名——銜接語言已經寫好。",
         "script": [
             ("Template — Opening: ", "Welcome to Changhua School News for [DATE]. I'm [NAME] and here are the headlines."),
             ("Template — Segment intro: ", "Our [first / second / third] story this week is about [TOPIC]. Let's hear from [REPORTER NAME]."),
             ("Template — Sign-off: ", "That's the news for [DATE]. From all of us at [SCHOOL NAME], have a wonderful week ahead."),
             ("Template — Backup: ", "We had a small technical problem with one of our stories. We will bring it to you next week. Thank you for your patience."),
         ],
         "vocab": [("template", "模板"), ("blank", "空格"), ("headlines", "頭條"), ("backup", "備案"), ("patience", "耐心")],
         "tips_en": "Print the script in 14pt with double spacing. Smaller fonts cause stumbles. The bigger the font, the smoother the read.",
         "tips_zh": "稿子用 14pt 雙倍行距印。字小會卡。字越大，讀得越順。"},
        {"n": 4, "color": "purple",
         "en": "Recording & Editing · 錄製與後製", "zh": "一支手機就夠了",
         "duration": "Production · 60 minutes weekly",
         "what_en": "Use a tripod-mounted phone, free editing apps (CapCut, iMovie), and built-in caption tools. Don't aim for broadcast quality — aim for student-watchable quality.",
         "what_zh": "用三腳架架手機、免費剪輯 App（CapCut、iMovie）、內建字幕工具。不必追求廣播品質，達到「學生愛看」的程度就好。",
         "script": [
             ("Director: ", "Quiet on set. We are recording in three, two, one — action."),
             ("Anchor (mid-take): ", "Sorry, let me start again."),
             ("Director: ", "No problem. Let's go again — three, two, one — action."),
             ("Director: ", "And cut! Good take. Let's add the captions in editing."),
         ],
         "vocab": [("take", "鏡次"), ("retake", "重來"), ("action", "開始（拍）"), ("cut", "切（停拍）"), ("caption", "字幕")],
         "tips_en": "Always add Chinese captions — non-fluent students watch the captions to catch up. Bilingual captioning doubles the educational value of every episode.",
         "tips_zh": "字幕中英文都要上——英文還不流利的學生靠中文字幕跟上。雙語字幕讓每一集的教育價值翻倍。"},
        {"n": 5, "color": "blue",
         "en": "Distribution · 發布", "zh": "三個頻道，全校都看得到",
         "duration": "Weekly publishing · 15 minutes",
         "what_en": "Three channels: (a) Monday morning playback at assembly, (b) classroom TV during homeroom that week, (c) school YouTube channel for parents and alumni. Same content, three audiences.",
         "what_zh": "三個發布管道：(a) 週一升旗播放，(b) 該週早自修教室電視播放，(c) 學校 YouTube 頻道給家長與校友。同樣的內容，三種觀眾。",
         "script": [
             ("Principal (Monday assembly): ", "Before our anthem, let's watch this week's School News. Anchors, take a bow!"),
             ("Homeroom teacher (in class): ", "We'll watch the School News during the first five minutes. Eyes on the screen."),
             ("Parent (at home, on YouTube): ", "Look — Yuting was on the news this week. She was really good!"),
             ("Alumnus (overseas): ", "Subscribed. Watching my old school's news makes me homesick in a good way."),
         ],
         "vocab": [("publish", "發布"), ("subscribe", "訂閱"), ("playback", "重播"), ("alumnus", "校友"), ("homesick", "想家")],
         "tips_en": "Your school's YouTube channel becomes a 5-year archive of student growth. Parents will rewatch their child's segments decades later. Treat the channel like a yearbook.",
         "tips_zh": "學校 YouTube 頻道會累積成五年的學生成長檔案。家長幾十年後仍會回看自己孩子的段落。把頻道當畢業紀念冊經營。"},
    ]
    return render_bilingual_topic(
        page_title="School News", current_path="/resources/",
        h1_en="School News", h1_zh="校園新聞 · 學生主播訓練班",
        hero_en="A weekly 3-minute student-produced English news bulletin teaches more sustained spoken English than any 40-minute class. Anchors prepare for hours; everyone watching learns from someone their own age.",
        hero_zh="一週一支 3 分鐘的學生英文校園新聞，教會學生的口說英文比一堂 40 分鐘的課還多。主播事前準備數小時；觀眾從同齡人身上學。",
        moe_en="Implements the 2030 bilingual policy's principle of \"student-led bilingual production\" — high-leverage authentic-task speaking with a real audience and weekly cadence.",
        moe_zh="實踐 2030 雙語政策「學生主導之雙語產出」原則——高槓桿、真實任務的口說訓練，有真實觀眾、固定週期。",
        core_principle="一週一支三分鐘，比一堂四十分鐘還有效。Three minutes a week, repeated, beats a lesson plan that aims for an hour.",
        sections_h2_en="Five components of a running news team", sections_h2_zh="五個讓新聞部運轉的元件",
        sections_intro_en="The five components below assemble into a working weekly broadcast. Read in order — roles first, then format, then script, then production, then distribution. Don't optimize for polish; optimize for sustainability.",
        sections_intro_zh="以下五個元件組裝成一支可運行的週播節目。順序：先角色、再格式、再腳本、再製作、再發布。重點不在精緻，在「能持續做下去」。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Anchor pair — rotate every 2 weeks", "主播搭檔——每兩週輪換"),
            ("Editing teacher or student — one weekly owner", "剪輯老師或學生——每週一位負責人"),
            ("Weekly story planning meeting (Fridays for next Monday)", "每週故事企劃會議（週五規劃下週一）"),
            ("Backup story bank for slow weeks", "備案故事庫（沒新聞的週用）"),
            ("Parent permission for student on-screen appearance", "學生入鏡家長同意書"),
            ("Archive folder on Google Drive or school server", "雲端歸檔（Google Drive 或學校伺服器）"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/bilingual-campus/announcements/", "title": "Bilingual Announcements", "desc": "Sarah Thomas &amp; Susan Rose's 13-episode broadcast playlist — best training material for anchors.", "meta": "Anchor training"},
            {"href": "/resources/bilingual-campus/morning-assembly/", "title": "Morning Assembly", "desc": "Monday-morning assembly is the primary distribution channel for School News.", "meta": "Distribution channel"},
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "Pull a 'word of the week' segment from the Hub library and weave it into each episode.", "meta": "Weekly segment"},
        ],
    )


# ----- International Sister School · 國際姊妹校 ------------------------------
def build_intl_sister_school():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Finding a Partner School · 尋找夥伴學校", "zh": "從免費的國際媒合計畫開始",
         "duration": "Setup · 6–10 weeks",
         "what_en": "Several free or low-cost matching programs exist — ePals, iEARN, MOFA's Taiwan-friendly school network. Apply through one rather than cold-emailing schools abroad; the platform handles time-zone matching and basic vetting.",
         "what_zh": "幾個免費或低成本的媒合平台——ePals、iEARN、外交部的台灣友校網絡。透過平台申請，比直接寫信給海外學校有效；平台會處理時區媒合與初步審核。",
         "script": [
             ("Coordinating teacher: ", "We are an elementary school in Changhua, Taiwan. We have around 200 students from Grade 1 to Grade 6."),
             ("Teacher: ", "We are looking for a partner school in a country where English is the main language."),
             ("Teacher: ", "Our goal is two video meet-ups per semester, plus a pen-pal letter exchange."),
             ("Teacher: ", "We can communicate in English. Our preferred time zone is GMT+8."),
         ],
         "vocab": [("partnership", "夥伴關係"), ("exchange", "交流"), ("MOU", "備忘錄"), ("time zone", "時區"), ("coordinator", "聯絡人")],
         "tips_en": "Match by school size and rural/urban character, not just country. A rural Changhua school often connects more meaningfully with a small-town American or Australian school than with a big-city one.",
         "tips_zh": "以學校規模和城鄉特性媒合，不只看國家。彰化的小型鄉村學校，常和美國或澳洲的小鎮學校更投緣，反而不一定是大城市裡的學校。"},
        {"n": 2, "color": "green",
         "en": "Video Letter Exchange · 影片信", "zh": "兩分鐘自介短片",
         "duration": "Per round · 4 weeks production",
         "what_en": "The simplest first contact: every student records a 30-second self-intro. Edit four into a 2-minute class video. Send via Google Drive or WeTransfer. Partner school responds with theirs.",
         "what_zh": "最簡單的初接觸：每位學生錄一段 30 秒自介，剪成 2 分鐘班級影片。透過 Google Drive 或 WeTransfer 寄送，夥伴校再回寄他們的版本。",
         "script": [
             ("Student 1 (on camera): ", "Hi! I'm Yating, I'm ten years old, and I live in Changhua, Taiwan."),
             ("Student 2: ", "Hello from Taiwan! My favorite food is rou-yuan. That's a kind of meat ball."),
             ("Student 3: ", "I have one brother and a dog. I like reading comic books."),
             ("Class together: ", "We hope you will visit Changhua one day. Bye!"),
         ],
         "vocab": [("record", "錄影"), ("edit", "剪輯"), ("class video", "班級短片"), ("send", "寄送"), ("respond", "回應")],
         "tips_en": "Watch the partner school's video together as a class. Pause and discuss every detail — house style, accent, classroom look. The first video sets the tone for the year.",
         "tips_zh": "全班一起看夥伴校寄來的影片，每個細節都暫停討論——他們的家、口音、教室樣子。第一支影片定下一整年的調性。"},
        {"n": 3, "color": "orange",
         "en": "Live Zoom Meet-Up · 即時連線", "zh": "30 分鐘的真實互動",
         "duration": "Per meet-up · 30 minutes",
         "what_en": "A 30-minute Zoom with a structured agenda: 5 min ice-breaker → 10 min mini-tour of each classroom (camera walk) → 10 min Q&A → 5 min farewells. Don't open the screen without an agenda.",
         "what_zh": "30 分鐘的 Zoom，要有議程：5 分鐘破冰 → 10 分鐘各班教室小導覽（用相機走一圈）→ 10 分鐘問答 → 5 分鐘道別。沒議程的連線就是混亂。",
         "script": [
             ("Teacher (host): ", "Hello everyone! Can you hear us? Thumbs up if you can hear."),
             ("Student: ", "Hi! My name is Pinghao. Can I ask you a question?"),
             ("Partner-school student: ", "Sure! What do you want to know?"),
             ("Student: ", "What time is it in your school right now? It is 9 in the morning here."),
         ],
         "vocab": [("greet", "問候"), ("share screen", "分享螢幕"), ("thumbs up", "比讚"), ("ask a question", "提問"), ("time difference", "時差")],
         "tips_en": "Pre-write 8–10 questions in English class the day before. Tape them to each student's desk. Even shy students will ask one if they don't have to invent it on the spot.",
         "tips_zh": "連線前一天的英文課裡預擬 8–10 個問題，貼在每位學生桌上。即使害羞的孩子，只要不必當下發明，都會敢問。"},
        {"n": 4, "color": "purple",
         "en": "Pen-Pal Letters · 筆友通信", "zh": "兩個月一封的紙本溫度",
         "duration": "Per round · 8-week cycle",
         "what_en": "Despite all the digital tools, physical letters still produce the deepest writing. Bimonthly handwritten letters, mailed in a class envelope. Students keep their pen-pal's letters in a portfolio.",
         "what_zh": "再多數位工具，紙本信件仍會逼出最深的寫作。兩個月一輪手寫信，整班裝同一個信封寄出。學生把收到的信收進個人學習履歷。",
         "script": [
             ("Letter template (opening): ", "Dear [PEN-PAL NAME], How are you? I hope you are well."),
             ("Body: ", "My name is [NAME]. I am [AGE] years old. I live in Changhua with my family."),
             ("Body: ", "Last month, I went to the Mazu Pilgrimage with my grandmother. It was crowded but exciting."),
             ("Sign-off: ", "I am looking forward to your letter. Please tell me about your school. Your friend, [NAME]."),
         ],
         "vocab": [("greeting", "問候"), ("sign-off", "結尾"), ("address", "地址"), ("postage", "郵資"), ("look forward to", "期待")],
         "tips_en": "Photograph every outgoing letter. When a student loses theirs (it happens), the photo is the only record. Also: parents love seeing the photos.",
         "tips_zh": "每封寄出的信都拍照。學生弄丟（很常發生）時，照片是唯一的紀錄。家長也喜歡看到照片。"},
        {"n": 5, "color": "blue",
         "en": "Exchange Visit Preparation · 互訪準備", "zh": "從第二年起，把連線變成真實見面",
         "duration": "Annual · 4-day visit",
         "what_en": "After 1–2 years of online exchange, plan an in-person visit (your side hosts first; reciprocal visit follows). Even if only 4–6 students go, the rest of the school participates as hosts.",
         "what_zh": "經過 1–2 年的線上交流後，安排實地互訪（先由我方接待，下一年回訪）。即便只去 4–6 位學生，全校都能以接待者身份參與。",
         "script": [
             ("Host family parent: ", "Welcome to our home! Please come in. Are you tired?"),
             ("Visiting student: ", "Thank you. I'm a little tired but very excited."),
             ("Host student: ", "This is your room. The bathroom is over there. Do you want some water?"),
             ("Host family parent: ", "Dinner will be at 7. We are having rou-yuan and stir-fried vegetables."),
         ],
         "vocab": [("host", "接待"), ("homestay", "寄宿家庭"), ("gift", "禮物"), ("customs", "習俗"), ("reciprocal visit", "回訪")],
         "tips_en": "Brief host families in writing two weeks before. Most awkwardness comes from over-formality. Coach families: 'Be normal. Eat at your normal time. Watch your normal TV. They are here to see your real life.'",
         "tips_zh": "出發前兩週書面提醒接待家庭。大多數尷尬來自「過度客氣」。教家庭：「就照平常過。平常時間吃飯、平常電視一起看。他們是來看你們真實生活的。」"},
    ]
    return render_bilingual_topic(
        page_title="International Sister School", current_path="/resources/",
        h1_en="International Sister School", h1_zh="國際姊妹校 · 同齡學生的真實連結",
        hero_en="A sister-school relationship gives students someone real — same age, on the other side of the world — to speak English to. Even a 20-minute Zoom meet-up per semester transforms how students think about why they're learning the language.",
        hero_zh="姊妹校關係給學生一個「真實的人」——同齡、住在地球另一端——去說英文。即便每學期一次 20 分鐘的 Zoom 連線，都能改變學生對「為什麼要學英文」的想像。",
        moe_en="International exchange aligns with the 12-year curriculum's \"Global Citizenship\" core competency and the 2030 bilingual policy's \"International perspective\" pillar.",
        moe_zh="國際交流對齊十二年國教「全球公民素養」核心素養，與 2030 雙語政策「國際視野」支柱。",
        core_principle="姊妹校的勝負在「持續」，不在「華麗」。Sustained quarterly contact beats a one-time spectacular visit.",
        sections_h2_en="Five stages from match to visit", sections_h2_zh="從媒合到互訪的五階段",
        sections_intro_en="The five stages below are in order — match, video letters, live meet-ups, pen-pal letters, then in-person visits. Each stage assumes the prior one is working. Don't skip to Zoom before video letters; don't fly people without two years of online history.",
        sections_intro_zh="以下五個階段有順序——先媒合、再影片信、再連線、再筆友、最後實地互訪。每階段都建立在前一階段的基礎上。不要跳過影片信直接 Zoom；不要在沒有兩年線上交流前先飛人去見面。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Designated coordinating teacher — one on each side", "雙方各一位專責的聯絡老師"),
            ("Calendar of 2 meet-ups per semester (booked at year start)", "每學期 2 次連線（學年初就排好）"),
            ("Bilingual permission slip + photo release", "雙語同意書與肖像授權書"),
            ("Backup activities for tech failure", "技術故障備案"),
            ("Parent debrief after each meet-up (5 min email)", "每次連線後 5 分鐘家長回顧（電郵）"),
            ("Yearly reflection ceremony — what we learned about them", "年度反思儀式：我們從對方身上學到什麼"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/bilingual-campus/english-self-intro/", "title": "English Self-Introduction", "desc": "Self-intro is the centerpiece of every sister-school first contact. Master that page before reaching out.", "meta": "Prerequisite"},
            {"href": "/resources/bilingual-campus/school-tours/", "title": "School Tours", "desc": "When sister-school delegates visit, the school tour is the main agenda — combine the two pages.", "meta": "Visit day pairing"},
            {"href": "/resources/bilingual-campus/amazing-changhua/", "title": "Amazing Changhua", "desc": "\"My hometown\" is the most-requested sister-school topic. Use the Changhua page as content scaffold.", "meta": "Topic content"},
        ],
    )


# ----- English Practice Corner · 英語練習角 ----------------------------------
def build_english_practice_corner():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Setting Up the Corner · 角落設定", "zh": "找一張桌子就開幕",
         "duration": "One-time setup · 2 hours",
         "what_en": "Find a corner near the FET's office or a high-traffic area like the library entrance. A small sign, two chairs, and a 'prompt of the week' card are enough. No registration, no schedule.",
         "what_zh": "在外師辦公室附近或圖書館入口等人流多的地方設置。一個小招牌、兩張椅子、一張本週對話提示卡就夠。不報名、不排課表。",
         "script": [
             ("FET (sitting at the corner): ", "Hi! I'm here for the next 20 minutes. Come and chat anytime."),
             ("Student (passing by): ", "Hello, teacher. What's the prompt today?"),
             ("FET: ", "Today's prompt is: 'What was the funniest thing that happened to you this week?'"),
             ("Student: ", "Oh, I have one. Can I tell you in English?"),
         ],
         "vocab": [("drop-in", "隨到隨聊"), ("recess", "下課時間"), ("prompt", "提示"), ("sign", "招牌"), ("twenty minutes", "二十分鐘")],
         "tips_en": "20 minutes is the magic number — long enough for 4-5 student conversations, short enough that the FET doesn't burn out. Better to do this 3x/week reliably than 5x/week unevenly.",
         "tips_zh": "20 分鐘是黃金時間——可以聊 4-5 位學生，外師也不會累。穩定每週三次，遠勝忽多忽少做五次。"},
        {"n": 2, "color": "green",
         "en": "Daily Prompt Cards · 每日對話卡", "zh": "20 張卡輪流用",
         "duration": "Setup once · use all year",
         "what_en": "20 prompt cards on a ring — questions like 'What did you eat for breakfast?', 'If you could fly, where would you go?', 'What's a small thing that made you smile this week?' Rotate one per day.",
         "what_zh": "20 張用書圈穿在一起的對話卡，題目像「今天早餐吃什麼？」「如果會飛，你想去哪裡？」「這週讓你嘴角上揚的小事是什麼？」每天換一張。",
         "script": [
             ("Card 1 (front EN): ", "What's something you learned this week?"),
             ("Card 1 (back ZH hint): ", "本週你學到什麼？提示：可以是課本上的，也可以是課本外的。"),
             ("Card 2 (front EN): ", "If you had one extra hour today, what would you do with it?"),
             ("Card 2 (back ZH hint): ", "今天如果多了一小時，你會用來做什麼？"),
         ],
         "vocab": [("prompt card", "對話卡"), ("rotate", "輪換"), ("hint", "提示"), ("extra hour", "多出來的一小時"), ("for example", "例如")],
         "tips_en": "Mix easy and hard prompts. The easy ones get shy students through the door; the hard ones reward those who come back. Don't sort prompts by difficulty on the card itself — let chance decide.",
         "tips_zh": "簡單和困難的題目混合。簡單的讓害羞學生進來，困難的獎勵常客。卡片本身不要標難度——讓隨機決定。"},
        {"n": 3, "color": "orange",
         "en": "FET Conversation Routines · 外師對話例行", "zh": "讓對話自然發生的小技巧",
         "duration": "Coaching · 30 minutes onboarding",
         "what_en": "Five lightweight habits that make the corner feel safe — greet by name when you can, reference last week's chat, listen twice as much as you speak, never correct grammar unprompted, end with a warm send-off.",
         "what_zh": "五個讓角落感覺安全的小習慣——能叫名字就叫名字、提到上次聊過的事、聽比說多兩倍、不主動糾文法、結尾要熱情送別。",
         "script": [
             ("FET (greeting): ", "Yating! Welcome back. How was the volleyball game on Saturday?"),
             ("Student: ", "We lost, but my serve was better this time."),
             ("FET (listening, not correcting): ", "Tell me more about your serve. What did you change?"),
             ("FET (closing): ", "Thanks for stopping by. See you next time. Have a great rest of your day!"),
         ],
         "vocab": [("greet by name", "叫得出名字的問候"), ("listen", "聆聽"), ("never correct", "不糾正"), ("send-off", "送別"), ("see you next time", "下次見")],
         "tips_en": "If a student says 'I goed to the store,' do NOT correct them in the moment. Note it mentally and weave 'went' into your next 3 sentences. They will absorb without embarrassment.",
         "tips_zh": "如果學生說「I goed to the store」，當下千萬不要糾正。記在心裡，接下來三句話自然多用「went」幾次。學生會吸收，但不會被羞辱。"},
        {"n": 4, "color": "purple",
         "en": "Self-Service Activities · 自助活動", "zh": "外師不在時也能用",
         "duration": "Ongoing · refresh monthly",
         "what_en": "When the FET is in a class or absent: a small basket of self-service materials — tongue twisters laminated cards, joke-of-the-week sheet, two short reading passages, a 'leave a message for our FET' notebook.",
         "what_zh": "外師上課中或請假時，提供一籃自助材料——繞口令過塑卡、本週笑話、兩段短文、「留言給外師」筆記本。",
         "script": [
             ("Tongue twister card: ", "She sells sea shells by the sea shore. (Try this 3 times fast!)"),
             ("Joke of the week: ", "Why don't scientists trust atoms? — Because they make up everything!"),
             ("Reading passage: ", "Did you know that octopuses have three hearts? Two pump blood to the gills, and the third pumps blood to the rest of the body."),
             ("Notebook prompt: ", "Tell our FET about your favorite movie. We will read your message together this Friday."),
         ],
         "vocab": [("tongue twister", "繞口令"), ("joke", "笑話"), ("reading passage", "短文"), ("notebook", "留言本"), ("message", "訊息")],
         "tips_en": "The notebook is the secret weapon. Students often write more bravely than they speak. The FET reads aloud the best entries each Friday — public praise without putting the student on the spot.",
         "tips_zh": "留言本是秘密武器。學生「寫」比「說」更敢。外師每週五朗讀最棒的留言——公開表揚，但又不讓學生被聚光燈追到。"},
    ]
    return render_bilingual_topic(
        page_title="English Practice Corner", current_path="/resources/",
        h1_en="English Practice Corner", h1_zh="英語練習角 · 下課十分鐘的英文",
        hero_en="A drop-in spot — usually a corner near the FET's office — where any student can have a 60-second English chat during recess. Low stakes, high frequency. The goal isn't to teach; it's to make speaking English feel like a normal thing to do at school.",
        hero_zh="一個下課可以隨時走進去的小角落——通常設在外師辦公室附近——任何學生都能找他做 60 秒英文閒聊。低門檻、高頻率。目的不是教學，是讓「在學校說英文」變成稀鬆平常的事。",
        moe_en="Reduces affective filter through casual, unevaluated speaking opportunities — directly implements the 雙語生活化校園 principle of \"casual encounters with English in daily routines.\"",
        moe_zh="透過無評量壓力的隨機口說機會，降低情意過濾——直接實踐「雙語生活化校園」要點中「英語融入日常作息」的精神。",
        core_principle="說英文不必到課堂才能說，下課十分鐘也算。Speaking English isn't a class. It's a recess.",
        sections_h2_en="Four pieces of a working corner", sections_h2_zh="一個有效角落的四個元件",
        sections_intro_en="The four pieces below assemble into a sustainable practice corner. The corner runs on the FET's energy, so keep it modest in scope — better to do less, reliably, than more, sporadically.",
        sections_intro_zh="以下四個元件組裝成一個能持續運作的練習角。整個角落靠外師的能量驅動，所以範圍要節制——做得少而穩，勝過做得多但散。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Bilingual sign at the door (\"English Practice Corner · 英語練習角\")", "雙語門口招牌"),
            ("Daily prompt board (rotating, visible from the hallway)", "每日提示板（輪換、從走廊看得見）"),
            ("Optional student log (one-line entry, low pressure)", "學生使用紀錄（一句話登錄、不強迫）"),
            ("Backup self-service materials always available", "備用自助材料隨時可用"),
            ("Monthly refresh of prompts (so regulars stay engaged)", "每月更新題目（讓常客保持新鮮感）"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/classroom-english/", "title": "Classroom English", "desc": "FETs use the corner to extend the language students hear in classroom routines — pair this with classroom English.", "meta": "Vocabulary bridge"},
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "Pick today's prompt card to feature the WotD word — natural reinforcement.", "meta": "Daily integration"},
            {"href": "/resources/bilingual-campus/morning-assembly/", "title": "Morning Assembly", "desc": "Announce the week's prompt at morning assembly — drives students to the corner during recess.", "meta": "Awareness driver"},
        ],
    )


# ----- School Teams & Clubs · 校隊與社團 -------------------------------------
def build_school_teams_clubs():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Joining a Club · 加入社團", "zh": "從報名到第一次出席",
         "duration": "Sign-up week · 30 minutes",
         "what_en": "The first English-rich moment of the club year is sign-up. Bilingual sign-up forms, an English question-asking ritual, and a welcome handshake from older students set the tone.",
         "what_zh": "社團年度的第一個英文密集時刻是報名。雙語報名表、英文提問儀式、學長姐英文歡迎握手，奠定整年的調性。",
         "script": [
             ("New member: ", "Hello. I want to join the basketball club. Where can I sign up?"),
             ("Returning student: ", "Welcome! Sign here. What grade are you in?"),
             ("New member: ", "Grade 4."),
             ("Returning student: ", "Great. We practice every Tuesday at 3:30. Bring your sports shoes. See you next week!"),
         ],
         "vocab": [("sign up", "報名"), ("schedule", "時間表"), ("meeting", "聚會"), ("equipment", "裝備"), ("see you next week", "下週見")],
         "tips_en": "Have older students run the sign-up table, not teachers. Older students naturally use the same simple English a Grade-4 needs. Plus it gives them leadership ownership.",
         "tips_zh": "讓高年級學生顧報名桌，不要老師顧。高年級會自然用四年級孩子聽得懂的簡單英文。也讓他們承擔起社團的責任。"},
        {"n": 2, "color": "orange",
         "en": "Sports Team Practice · 運動隊練習", "zh": "球場上的英文",
         "duration": "Every practice · 5 minutes warm-up",
         "what_en": "Sports vocabulary is the easiest English students will ever learn — they NEED these words to play. Teach 'pass,' 'shoot,' 'foul,' 'time-out' in the first practice and reinforce every session.",
         "what_zh": "運動詞彙是學生最容易學的英文——他們「需要」這些字才能玩。第一次練習就教 pass / shoot / foul / time-out，之後每次練習都重複使用。",
         "script": [
             ("Coach: ", "Today we warm up first. Five minutes of jogging — go!"),
             ("Coach (during play): ", "Good pass! Now shoot! Yes!"),
             ("Coach (calling pause): ", "Time-out. Everyone, listen up. Let's talk about defense."),
             ("Coach (closing): ", "Good practice today. Cool down. See you on Thursday."),
         ],
         "vocab": [("warm up", "暖身"), ("pass", "傳球"), ("shoot", "投籃"), ("defense", "防守"), ("time-out", "暫停")],
         "tips_en": "Use ONLY English for sports calls during practice — even if the coach also speaks Mandarin. The chaos of a game is the perfect context: students figure out 'pass' the second time they hear it.",
         "tips_zh": "練習中發號施令一律用英文——即使教練也會中文。比賽的混亂正是最好的語境：學生第二次聽到 pass 就會懂。"},
        {"n": 3, "color": "purple",
         "en": "Art / Music Club · 藝術音樂社團", "zh": "器材與創作的英文",
         "duration": "Per meeting · 5 minutes setup",
         "what_en": "Art and music clubs offer rich vocabulary tied directly to physical objects — brushes, palettes, scores, instruments. Label every shared item bilingually. The label becomes the lesson.",
         "what_zh": "美術社與音樂社提供大量與實體物品直接連結的詞彙——畫筆、調色盤、樂譜、樂器。把每件共用器材貼雙語標籤。標籤就是教材。",
         "script": [
             ("Music teacher: ", "Today we will practice page 12 in your score. Flutes, start. Strings, ready."),
             ("Art teacher: ", "Please get your brush, your palette, and one piece of paper from the shelf."),
             ("Art teacher: ", "Mix red and blue. What color do you get? Yes — purple!"),
             ("Music teacher: ", "From the top, everyone — one, two, three, four!"),
         ],
         "vocab": [("brush", "畫筆"), ("palette", "調色盤"), ("score", "樂譜"), ("rehearsal", "排練"), ("from the top", "從頭")],
         "tips_en": "End every art/music session with a 30-second 'show your work in English' — students hold up their piece and say one sentence about it. Builds presentation muscle alongside creative skill.",
         "tips_zh": "每次美術／音樂社結尾留 30 秒「英文展示作品」——學生舉起作品，用一句英文介紹。創作能力與表達能力同步建立。"},
        {"n": 4, "color": "green",
         "en": "Service / Eco Club · 服務生態社", "zh": "公益行動的英文",
         "duration": "Per project · 60 minutes",
         "what_en": "Service clubs (cleaning, recycling, beach clean-ups, food bank visits) give students English tied to action verbs and civic vocabulary — 'volunteer,' 'donate,' 'recycle,' 'community.'",
         "what_zh": "公益社團（打掃、回收、淨灘、食物銀行訪問）讓學生學到與行動相關的英文與公民詞彙——volunteer、donate、recycle、community。",
         "script": [
             ("Club leader: ", "Today we are going to the beach to clean up trash. Wear gloves. Bring your water bottle."),
             ("Volunteer: ", "What kind of trash do we collect?"),
             ("Leader: ", "Plastic, bottles, and cigarette butts. We separate them into three bags."),
             ("Leader (after): ", "Good job, everyone! We collected three bags of plastic. That is three less bags in the ocean."),
         ],
         "vocab": [("volunteer", "志工"), ("donate", "捐贈"), ("recycle", "回收"), ("community", "社區"), ("clean up", "清理")],
         "tips_en": "Document service projects with bilingual photo captions — those become great content for school news, sister-school exchanges, and parent newsletters. One project, four content uses.",
         "tips_zh": "服務專案要拍照並寫雙語圖說——可以同時用於校園新聞、姊妹校交流、家長通訊。一個專案，四種用途。"},
        {"n": 5, "color": "blue",
         "en": "Tournament Day · 比賽日", "zh": "比賽中的英文",
         "duration": "Per tournament · all day",
         "what_en": "Tournament day brings out cheering and sportsmanship vocabulary in a way no class can replicate. Pre-teach a small set of cheers and post-game phrases — 'Good game,' 'Well played,' 'See you next time.'",
         "what_zh": "比賽日帶出加油與運動家風範的詞彙，是任何課堂都比不上的真實情境。事先教一組加油詞和賽後用語——「Good game」「Well played」「下次再戰」。",
         "script": [
             ("Cheerleader: ", "Go, team, go! Let's go, let's go, L-E-T-S G-O!"),
             ("Coach (timeout): ", "Catch your breath. Drink water. We have two more minutes."),
             ("Player (post-game, to opponent): ", "Good game. Well played. See you next time."),
             ("Coach (closing): ", "Win or lose, we played with respect. That's what matters."),
         ],
         "vocab": [("opponent", "對手"), ("referee", "裁判"), ("sportsmanship", "運動家風範"), ("good game", "好球"), ("respect", "尊重")],
         "tips_en": "Teach 'Good game' as the unconditional post-match phrase — whether you win, lose, or tie. It's the one piece of English that travels with these students for life.",
         "tips_zh": "教孩子「Good game」是賽後無條件的招呼——贏、輸、平手都說。這句英文會跟孩子一輩子。"},
    ]
    return render_bilingual_topic(
        page_title="School Teams & Clubs", current_path="/resources/",
        h1_en="School Teams & Clubs", h1_zh="校隊與社團 · 興趣即詞彙",
        hero_en="After-school clubs are where students develop deeper English vocabulary tied to their passions — not the textbook list, but words they actually want to know. Basketball, choir, robotics, eco-club: each becomes a vocabulary universe.",
        hero_zh="課後社團是學生發展深層英文詞彙的地方——不是課本上的單字，而是學生「真心想知道」的詞。籃球、合唱、機器人、生態社團，每一個都是一座詞彙宇宙。",
        moe_en="Implements the 2030 bilingual policy's guideline on \"Bilingual extracurricular activities\" — clubs are the most natural place for sustained authentic English use.",
        moe_zh="實踐 2030 雙語政策「雙語課外活動」要點——社團是最自然的、能長期使用真實英文的場域。",
        core_principle="社團不是「多教一點英文」，是「英文就在你已經愛的事情裡」。Clubs aren't a place to add more English — English is just already there, in what students already love.",
        sections_h2_en="Five club-life moments, ready for English", sections_h2_zh="社團生活的五個雙語時刻",
        sections_intro_en="The five moments below cover the typical year of any club — joining, practicing, creating, serving, competing. Pull the section that matches your club type; don't try to apply all five everywhere.",
        sections_intro_zh="以下五個時刻涵蓋任何社團的典型年度——入社、練習、創作、服務、比賽。挑符合你社團類型的段落用，不必五段全套照搬。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Club English glossary — 3–5 words per week, taught in opening minutes", "社團英文詞彙表——每週 3-5 字，社團開始時教"),
            ("Mid-year showcase with bilingual MC", "期中成果發表，雙語主持"),
            ("\"English Club Moment\" — at least one session/month run entirely in English", "「英文社團日」——每月至少一次社團全程英文"),
            ("Bilingual coaching cards for the coach (cheat-sheet style)", "教練雙語小抄（cheat sheet 樣式）"),
            ("End-of-year reflection (bilingual, what we learned)", "年末雙語反思：今年學到的"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "Many WotD videos feature sport, art, and ecology vocabulary — perfect for club opening minutes.", "meta": "Vocabulary source"},
            {"href": "/festivals/", "title": "Festival English Series", "desc": "Festival vocabulary often crosses with club projects (art club for Lantern Festival, service club for Mid-Autumn).", "meta": "Theme overlap"},
            {"href": "/resources/bilingual-campus/morning-assembly/", "title": "Morning Assembly", "desc": "Use morning assembly to announce upcoming tournaments and showcase club results.", "meta": "Awareness driver"},
        ],
    )


# ----- Summer Fun Program · 暑期樂活營 ---------------------------------------
def build_summer_fun_program():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Daily Camp Schedule · 每日營隊作息", "zh": "從上午到下午的雙語節奏",
         "duration": "Per camp day · 8:30am–3:30pm",
         "what_en": "A consistent daily schedule is half the camp. Morning briefing in English, four rotating activity blocks, lunch, two more blocks, closing circle. Repeat for 5 days.",
         "what_zh": "穩定的每日作息就是營隊的一半。早晨英文集合 → 4 個輪替活動 → 午餐 → 2 個活動 → 結業圈圈。5 天循環。",
         "script": [
             ("Camp leader (morning): ", "Good morning, campers! Today is Day Three. Let's check the schedule on the board."),
             ("Camp leader: ", "Group A — you start at the science station. Group B — start at sports. Switch in 45 minutes."),
             ("Camp leader (afternoon closing): ", "Everyone sit in a circle. What was your favorite moment today? Share one word."),
             ("Camper: ", "Splash! (from water games this morning)"),
         ],
         "vocab": [("schedule", "作息"), ("rotation", "輪換"), ("group", "組別"), ("camper", "營員"), ("closing circle", "結業圈圈")],
         "tips_en": "Use 'Day One,' 'Day Two,' 'Day Three' rather than dates — feels more like camp and easier for English. By Day Five, students will count down on their own.",
         "tips_zh": "用 Day One / Day Two 而非日期——更有營隊感、英文也好理解。第五天時學生會自己倒數。"},
        {"n": 2, "color": "green",
         "en": "Activity Buckets · 活動分類", "zh": "四種主題，輪流上場",
         "duration": "Per block · 45 minutes",
         "what_en": "Four activity buckets cover camp without exhausting any teacher: SPORTS (outdoor games), CRAFTS (art and making), SCIENCE (simple experiments), DRAMA (skits and storytelling). Each bucket has 5 prepped activities — one per day.",
         "what_zh": "四種活動分類就足以涵蓋一整週、不操爆任何老師：運動（戶外遊戲）、手作（藝術與動手做）、科學（簡單實驗）、戲劇（短劇與說故事）。每類預備 5 個活動——每日一個。",
         "script": [
             ("Sports station leader: ", "Today's game is 'Capture the Flag.' Two teams. The blue team's flag is over there. Ready?"),
             ("Crafts station leader: ", "Today we are making paper boats. Take one piece of paper. Watch — fold, fold, fold."),
             ("Science station leader: ", "What happens when we mix baking soda and vinegar? Let's see! Pour it in — wow!"),
             ("Drama station leader: ", "Today's story is 'The Tortoise and the Hare.' Who wants to be the tortoise? The hare?"),
         ],
         "vocab": [("station", "站別"), ("rotation", "輪換"), ("supplies", "物料"), ("experiment", "實驗"), ("skit", "短劇")],
         "tips_en": "Stagger the four stations so no two are loud at the same time. Sports outside, drama in the gym, crafts in the cafeteria, science in a classroom — geography prevents overlap.",
         "tips_zh": "四站錯開避免吵：運動在戶外、戲劇在禮堂、手作在餐廳、科學在教室——靠空間區隔解決音量衝突。"},
        {"n": 3, "color": "orange",
         "en": "English-Integrated Games · 英文遊戲", "zh": "玩中學的設計",
         "duration": "Per game · 15–30 minutes",
         "what_en": "Three classics that work at any skill level — Bingo (with vocabulary cards instead of numbers), Scavenger Hunt (English clues hidden around the school), Charades (act out the word the FET shows you).",
         "what_zh": "三個經典遊戲，任何程度都能玩——賓果（用詞彙卡而非數字）、尋寶（藏英文線索在校園各處）、比手畫腳（外師給字，學生比劃，全組猜）。",
         "script": [
             ("Bingo caller: ", "Next word — 'rainbow.' If you have 'rainbow' on your card, mark it!"),
             ("Scavenger hunt leader: ", "Clue number three: 'I am red, round, and grow on a tree. The teacher eats me at lunch.' Where do we go?"),
             ("Charades player (acting): ", "[swimming motion]"),
             ("Team: ", "Swim! Swimming! Pool!"),
         ],
         "vocab": [("turn", "輪到"), ("score", "得分"), ("winner", "贏家"), ("again", "再一次"), ("guess", "猜")],
         "tips_en": "Charades is the highest-leverage English game in camp — total physical commitment unlocks vocabulary even shy kids will shout. Mix in 2-3 rounds every day.",
         "tips_zh": "比手畫腳是營隊裡英文槓桿最大的遊戲——全身投入會逼出連害羞孩子都不自覺喊出來的詞彙。每天混 2-3 輪。"},
        {"n": 4, "color": "purple",
         "en": "Closing Showcase · 成果發表", "zh": "最後一天的舞台",
         "duration": "Friday afternoon · 60 minutes",
         "what_en": "On Day 5, each group performs a 3-minute skit they wrote together. Parents are invited. The skit doesn't need to be polished — bumbling through it together is the achievement.",
         "what_zh": "第五天，每組演一齣 3 分鐘自編短劇，邀家長到場觀賞。短劇不必精緻——能一起跌跌撞撞演完，就是成就。",
         "script": [
             ("MC (camper): ", "Welcome to our Camp Showcase! First up, the Lion Group will perform 'A Day at the Beach.'"),
             ("Group performer: ", "It's a sunny day. Let's go to the beach!"),
             ("Group performer 2: ", "I forgot my swimsuit! Oh no!"),
             ("MC: ", "Let's give them a big hand. Next up — the Tiger Group with 'The Lost Dog.'"),
         ],
         "vocab": [("perform", "演出"), ("audience", "觀眾"), ("applause", "掌聲"), ("MC", "主持人"), ("thank you", "謝謝")],
         "tips_en": "Record every group's performance and share the videos with parents via QR code. The video becomes the family memento — and shows up at the kid's wedding twenty years later.",
         "tips_zh": "每組演出都錄影，用 QR Code 分享給家長。這支影片會變成家族紀念品——二十年後孩子的婚禮上會被重播。"},
        {"n": 5, "color": "blue",
         "en": "Parent Reception · 家長迎接", "zh": "結業時的家長英文",
         "duration": "Friday · 30 minutes",
         "what_en": "After the showcase, a 30-minute parent reception. Each camper introduces their parents to one teacher in English ('This is my mom. This is Teacher Sarah.'). A 2-sentence ceremony bridges school and home.",
         "what_zh": "成果發表後，30 分鐘的家長交流。每位營員用英文把家長介紹給一位老師：「這是我媽媽。這是 Sarah 老師。」兩句話的儀式，連結學校與家庭。",
         "script": [
             ("Camper: ", "Mom, this is Teacher Sarah. She teaches our drama class."),
             ("Parent: ", "Hello. Thank you for taking care of my child this week."),
             ("Teacher: ", "It was my pleasure. Your son is very brave on stage."),
             ("Camper (closing): ", "We made paper boats today. Can I show you?"),
         ],
         "vocab": [("introduce", "介紹"), ("parent", "家長"), ("certificate", "證書"), ("congratulations", "恭喜"), ("family", "家庭")],
         "tips_en": "Give parents a printed bilingual 'phrases for tonight' card when they arrive — five short English sentences they can use with the FET. Adult anxiety drops; parent-teacher relationship deepens.",
         "tips_zh": "家長到場時發一張雙語「今晚可以說的話」卡——五句可以對外師說的短英文。大人焦慮感降低，親師關係加深。"},
    ]
    return render_bilingual_topic(
        page_title="Summer Fun Program", current_path="/resources/",
        h1_en="Summer Fun Program", h1_zh="暑期樂活營 · 一週密集雙語",
        hero_en="When the school year ends, English doesn't have to. A one-week summer camp built around games, crafts, and sports — all in light English — gives students 25 hours of bilingual time per year. Better still: students sign up voluntarily.",
        hero_zh="學年結束，英文不必跟著放假。一週暑期營以遊戲、手作、運動為主軸，全程以輕鬆英文進行，能為學生每年多累積 25 小時的雙語時間。重點是：學生自願報名。",
        moe_en="Aligns with Ministry of Education's \"夏日樂學\" summer enrichment program and 2030 bilingual policy's voluntary out-of-class learning opportunities.",
        moe_zh="對齊教育部「夏日樂學」暑期增能計畫，並符合 2030 雙語政策「自願性課外英語接觸機會」精神。",
        core_principle="暑假最稀缺的不是時間，是「孩子願意學英文的時間」。Summer's scarcest resource isn't hours — it's hours when kids choose to use English.",
        sections_h2_en="Five days, five layers", sections_h2_zh="五天，五個層次",
        sections_intro_en="The five sections below give you the full camp shape — daily schedule, activity buckets, English-rich games, the closing performance, and the parent reception. Print, adapt, run.",
        sections_intro_zh="以下五段給你完整營隊架構——每日作息、活動分類、英文密集遊戲、成果發表、家長交流。印出來、改寫、執行。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("5-day curriculum mapped to your grade band", "符合該年段的 5 日課程表"),
            ("FET + local teacher pair per group (never solo FET)", "每組外師＋本地老師搭檔（不單獨外師）"),
            ("Camp T-shirts (identity matters — kids wear them for years)", "營隊 T 恤（孩子的歸屬感，會穿好幾年）"),
            ("Daily attendance + photo release on file", "每日出席表＋肖像授權書存檔"),
            ("Parent reception schedule communicated week before", "家長交流時程提前一週通知"),
            ("Post-camp 5-minute parent survey", "結營後 5 分鐘家長問卷"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/resources/classroom-english/", "title": "Classroom English", "desc": "Camp leaders use the same 10 classroom situations daily — refresh them before camp starts.", "meta": "Leader prep"},
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "Use 5 WotD videos as 'Word of the Day' moments at camp opening each morning.", "meta": "Daily opener"},
            {"href": "/festivals/", "title": "Festival English Series", "desc": "If camp coincides with a festival week, pull the matching festival unit as a Day-3 theme.", "meta": "Theme integration"},
        ],
    )


# ----- One Minute English · 一分鐘英文 ---------------------------------------
def build_one_minute_english():
    sections = [
        {"n": 1, "color": "blue",
         "en": "Daily Clip Structure · 每日短片結構", "zh": "60 秒怎麼分配",
         "duration": "Per clip · 60 seconds",
         "what_en": "A 60-second clip is exactly long enough to teach one word with two examples. Structure: 5s opening (word + Chinese) → 30s meaning and example → 25s repeat-after-me. Shorter feels rushed; longer loses attention.",
         "what_zh": "60 秒剛好夠教一個字、兩個例句。結構：5 秒開場（單字＋中文）→ 30 秒意思與例句 → 25 秒跟讀。再短會匆促，再長會分心。",
         "script": [
             ("Narrator: ", "Today's word — 'curious.' 好奇的."),
             ("Narrator: ", "Curious means 'wanting to know more about something.' For example: 'The cat is curious about the box.'"),
             ("Narrator: ", "Another example: 'I am curious about your weekend. Tell me!'"),
             ("Narrator: ", "Now you say it — 'curious.' One more time — 'curious.' Great. See you tomorrow!"),
         ],
         "vocab": [("introduce", "介紹"), ("example", "例句"), ("repeat after me", "跟著我說"), ("see you tomorrow", "明天見"), ("curious", "好奇的")],
         "tips_en": "End every clip with the same sign-off — 'See you tomorrow!' Repetition of the closing turns it into a daily ritual; students start chanting along with the speaker by Week 2.",
         "tips_zh": "每支短片用同一句結尾——「明天見！」重複的結尾變成日常儀式，第二週開始學生就會自動跟著喊。"},
        {"n": 2, "color": "green",
         "en": "Sourcing Clips · 影片來源", "zh": "現成可用的庫",
         "duration": "Sourcing once · use all year",
         "what_en": "Three reliable sources: (1) The Hub's Word of the Day library — 3,000 ready clips with Changhua schools' credits. (2) BBC Learning English daily clips. (3) Sesame Street YouTube channel for younger grades.",
         "what_zh": "三個可靠的影片來源：(1) Hub 的校園百科 — 3,000 支現成影片，附上彰化各校 credits。(2) BBC Learning English 每日短片。(3) Sesame Street YouTube 頻道（適合低年級）。",
         "script": [
             ("Teacher (to class): ", "Today's clip is from our own Hub. Watch — this is from Changhua Elementary."),
             ("Clip: ", "[plays Word of the Day video]"),
             ("Teacher: ", "Did you notice the school name at the end? That's from Changhua's Hub library."),
             ("Student: ", "Teacher, can our class make one next month?"),
             ("Teacher: ", "Yes — and it will live in the Hub forever. Let's pick our word this Friday."),
         ],
         "vocab": [("source", "來源"), ("channel", "頻道"), ("subscribe", "訂閱"), ("playlist", "播放清單"), ("credit", "署名")],
         "tips_en": "Always prefer Hub clips when available — students light up seeing a Taiwan-made clip with a Changhua school's name. Generic BBC clips work; Hub clips are personal.",
         "tips_zh": "優先用 Hub 的影片——學生看到台灣自製、彰化學校署名的影片，眼睛會發亮。BBC 也可以用，但 Hub 才是「自己的」。"},
        {"n": 3, "color": "orange",
         "en": "Classroom Routine · 教室常規", "zh": "讓播放變成儀式",
         "duration": "Per session · 90 seconds",
         "what_en": "Same time, same place, same opening signal. Most schools play it after the bell, before homeroom announcements. The teacher waits at the front, says 'Eyes on the screen' once, and the room quiets within 5 seconds.",
         "what_zh": "同樣時間、同樣地點、同樣開場訊號。多數學校在鐘響後、早自修宣布事項前播放。老師站在前面，說一次「Eyes on the screen」，全班 5 秒內安靜。",
         "script": [
             ("Teacher (bell rings): ", "Good morning. Bags on the floor. Eyes on the screen."),
             ("Clip plays for 60 seconds: ", "[plays]"),
             ("Teacher: ", "Today's word — 'curious.' Everyone, together — 'curious.'"),
             ("Class: ", "Curious!"),
         ],
         "vocab": [("ready", "準備好"), ("repeat", "重複"), ("again", "再一次"), ("listen", "聆聽"), ("together", "一起")],
         "tips_en": "Resist the urge to discuss the word. The clip is for exposure, not comprehension testing. If a student is curious, they'll ask later in the corridor — that's the right time, not in the classroom.",
         "tips_zh": "別忍不住要討論。短片是用來「接觸」，不是「測驗」。學生若好奇，他會在走廊問你——那才是對的時機，不是在教室裡。"},
        {"n": 4, "color": "purple",
         "en": "Student-Made Clips · 學生自製短片", "zh": "六年級為低年級拍",
         "duration": "Production · 4 hours per clip",
         "what_en": "Once a month, Grade 6 students produce one One-Minute clip themselves — picked word, written script, recorded with a phone, edited with free software. Younger grades love watching older students teach them.",
         "what_zh": "每月一次，六年級學生自己製作一支一分鐘短片——選字、寫腳本、用手機錄、用免費軟體剪輯。低年級看高年級教自己，會特別投入。",
         "script": [
             ("Production team meeting (Grade 6): ", "Our word this month is 'patient.' That's 耐心的."),
             ("Team: ", "Who wants to be the speaker? Pinghao? Okay. Let's write the script."),
             ("Speaker (on camera): ", "Hi, Grade 1 friends! Today's word is 'patient.' My grandmother is very patient with me when I learn to cook."),
             ("Editor: ", "Add the captions and the school logo at the end. Done — let's send it to Miss Wang."),
         ],
         "vocab": [("record", "錄影"), ("edit", "剪輯"), ("audience", "觀眾"), ("narrate", "旁白"), ("upload", "上傳")],
         "tips_en": "Make the Grade 6 production a yearly tradition. By the time these students leave, they have a portfolio of 5–6 clips — a real video resume to take to junior high. Some win county prizes.",
         "tips_zh": "六年級拍短片做成年度傳統。學生畢業時各自累積 5–6 支作品——是一份真正的「影片履歷」帶到國中。有的還能得縣級獎項。"},
    ]
    return render_bilingual_topic(
        page_title="One Minute English", current_path="/resources/",
        h1_en="One Minute English", h1_zh="一分鐘英文 · 每日 60 秒影音英文",
        hero_en="A 60-second English clip every school day. Watched at the start of homeroom, before lunch, or in any spare minute. Over a school year, that's 60+ hours of casual English — and the shadowing builds pronunciation no class can give.",
        hero_zh="每個上學日 60 秒的英文短片。在早自修開始、午餐前、或任何空檔播放。一學年累積超過 60 小時輕量英文——而 shadowing 跟讀建立的口音感，是任何一堂課都給不了的。",
        moe_en="Implements the 2030 policy's \"Daily exposure to English\" principle — high-frequency, low-friction touchpoints that accumulate into significant exposure over a year.",
        moe_zh="實踐 2030 雙語政策「每日英語接觸」原則——高頻率、低門檻的小接觸，一年下來累積成可觀的曝光時數。",
        core_principle="一天一分鐘，比一週一小時更有效。One minute a day beats one hour a week.",
        sections_h2_en="Four components of a working daily clip", sections_h2_zh="一支能用的每日短片，四個元件",
        sections_intro_en="The four sections below assemble into a sustainable daily-clip routine — clip structure, sourcing, classroom routine, and a monthly student-production loop. The first three are mandatory; the fourth is the icing.",
        sections_intro_zh="以下四個元件組裝成可持續的每日短片常規——影片結構、影片來源、教室常規、學生月度自製。前三項必備，第四項是錦上添花。",
        sections=sections,
        checklist_h2_en="Implementation checklist", checklist_h2_zh="實施檢核表",
        checklist_items=[
            ("Daily playlist scheduled in advance (one week at a time)", "每日播放清單預排（一次排一週）"),
            ("Speaker / screen ready before bell rings", "鐘響前播放器與螢幕都備妥"),
            ("Shadow protocol consistent (\"Now you say it — together\")", "跟讀流程一致（「現在你說 — 一起」）"),
            ("Weekly review — which clip stuck?", "每週回顧——哪支最印象深刻？"),
            ("Student-made archive folder (saved for years)", "學生自製作品的歸檔資料夾（保留多年）"),
        ],
        companion_h2_en="Companion Hub resources", companion_h2_zh="搭配 Hub 其他資源",
        companion_cards=[
            {"href": "/word-of-the-day/", "title": "Word of the Day", "desc": "The Hub's 3,000 clip library is the primary source for daily One Minute English. Start here.", "meta": "Primary source"},
            {"href": "/resources/bilingual-campus/morning-assembly/", "title": "Morning Assembly", "desc": "Morning assembly's Word of the Day Spotlight uses the same clip library — pair the routines.", "meta": "Same source"},
            {"href": "/resources/bilingual-campus/school-news/", "title": "School News", "desc": "Student-made One Minute clips can become a regular segment on School News.", "meta": "Distribution channel"},
        ],
    )


def build_about_changhua():
    content = """
<section class="hub-section hub-section--narrow">
  <p class="hub-eyebrow">About Changhua</p>
  <h1 class="hub-h1">A county whose name means <em style="color:var(--hub-primary)">to manifest refined civilization</em>.</h1>
  <p style="font-size:1.15rem;color:var(--hub-ink-soft);max-width:62ch;line-height:1.6;margin-top:24px">
    Changhua County (彰化縣) was founded in 1723 — its very name comes from the Qing-era phrase
    <strong>"建學立師以彰雅化"</strong>: <em>establish schools and teachers to manifest refined civilization</em>.
    Education isn't an afterthought here. It is built into the county's identity.
  </p>
  <p class="hub-zh" style="font-size:1.05rem;color:var(--hub-ink-soft);max-width:62ch;line-height:1.7;margin-top:18px">
    彰化縣於 1723 年（清雍正元年）設縣，得名於「<strong>建學立師以彰雅化</strong>」。
    教育在彰化從來不是邊角，而是縣的本名與本心。三百年來，這片台灣中部最小、人口最多的平原，孕育了鹿港的商埠文化、八卦山的信仰地景、賴和的新文學，以及一代又一代守在課堂裡的老師。
  </p>

  <div class="about-stats">
    <div class="about-stat">
      <p class="about-stat-num">1,074<span class="unit">km²</span></p>
      <p class="about-stat-en">Total area</p>
      <p class="about-stat-zh">Taiwan's smallest county · 全台最小縣</p>
    </div>
    <div class="about-stat">
      <p class="about-stat-num">1.2<span class="unit">million</span></p>
      <p class="about-stat-en">Population</p>
      <p class="about-stat-zh">Most populous county · 全台人口最多縣</p>
    </div>
    <div class="about-stat">
      <p class="about-stat-num">1723</p>
      <p class="about-stat-en">Founded</p>
      <p class="about-stat-zh">清雍正元年設縣</p>
    </div>
  </div>

  <div class="about-quote">
    <p class="about-quote-text">"Establish schools and teachers, so that refined civilization may be made visible."</p>
    <p class="about-quote-zh">「建學立師以彰雅化」——這八個字是雍正皇帝為新設立的縣賜下的期許，也是「彰化」二字的出處。三百年來，這份命名一直是這片土地的本心。</p>
    <span class="about-quote-cite">Emperor Yongzheng · 1723</span>
  </div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">Geography &amp; landscape <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">地理</span></h2>
  <p>Sitting on Taiwan's west-coast plain between the Dadu and Zhuoshui Rivers, Changhua is <strong>87.69 % plain</strong> with the Bagua Plateau rising on the eastern edge. The Taiwan Strait shoreline on the west forms one of the country's largest <strong>tidal flats</strong> — home to oyster farms, mudskippers, and fiddler crabs. This is Taiwan's lowest county by average elevation: every village is reachable within an hour from the county seat.</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">座落於台灣中部西岸，介於大肚溪與濁水溪之間，87.69% 為平原，東緣為八卦台地。西側緊鄰台灣海峽，擁有全台最大潮間帶之一——蚵田、彈塗魚、招潮蟹皆在此繁衍。全台海拔最低的縣，從彰化市出發一小時內可達任一鄉鎮。</p>

  <div class="about-callout">
    <p><strong>Three landscape zones in one county:</strong> coastal tidal flats (Fangyuan, Dacheng, Wanggong) feed Taiwan's oyster &amp; clam industry; the central plain (Yuanlin, Tianzhong, Tianwei) is the rice-and-flower heartland; the Bagua Plateau (Bagua Mountain, Eight Trigrams Mountain) holds the county's spiritual landmarks.</p>
    <p class="hub-zh" style="color:var(--hub-ink-soft);font-size:.95rem">一縣三貌：西海岸潮間帶供養全台蚵業，中央彰化平原是稻米與花卉重鎮，八卦山則是信仰與文化地景的所在。</p>
  </div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">What Changhua is famous for <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">在地物產與產業</span></h2>
  <p style="color:var(--hub-ink-soft)">Eighteen townships, eighteen specialties. From bawan to bicycles, this is what Taiwan thinks of when it thinks of Changhua.</p>

  <div class="about-grid about-grid--3">
    <div class="about-card about-card--orange">
      <span class="about-card-icon">🥟</span>
      <h4>Bawan · Meatball<span class="about-card-zh">彰化肉圓</span></h4>
      <p>The translucent steamed-then-fried pork dumpling that Taiwanese kids associate, by reflex, with Changhua. Two rival traditions: Changhua City (deep-fried) and Beidou (steamed).</p>
    </div>
    <div class="about-card about-card--purple">
      <span class="about-card-icon">🍇</span>
      <h4>Grapes &amp; wine<span class="about-card-zh">溪湖／大村葡萄</span></h4>
      <p>Xihu and Dacun townships produce most of Taiwan's table grapes — black Kyoho in summer, Golden Muscat in winter — and run small-batch wineries open to visitors.</p>
    </div>
    <div class="about-card about-card--green">
      <span class="about-card-icon">🌸</span>
      <h4>Tianwei flowers<span class="about-card-zh">田尾公路花園</span></h4>
      <p>Taiwan's largest cluster of nurseries and florists. Six kilometres of greenhouses along Highway 1, supplying flowers to the entire island.</p>
    </div>
    <div class="about-card about-card--blue">
      <span class="about-card-icon">🧦</span>
      <h4>Shetou socks<span class="about-card-zh">社頭織襪</span></h4>
      <p>One small town. <strong>~70 % of Taiwan's socks.</strong> Family-run knitting mills have made Shetou the sock capital of the country since the 1960s.</p>
    </div>
    <div class="about-card about-card--orange">
      <span class="about-card-icon">🌊</span>
      <h4>Wanggong oysters<span class="about-card-zh">王功蚵</span></h4>
      <p>Ox-cart rides take you out across the tidal flats at low tide to harvest oysters. Wanggong Fishing Port is the place to eat them — oyster omelette, oyster vermicelli, fried oysters.</p>
    </div>
    <div class="about-card about-card--purple">
      <span class="about-card-icon">🚲</span>
      <h4>Bicycles &amp; baking<span class="about-card-zh">員林食品與工業</span></h4>
      <p>Yuanlin and Dacun host bicycle-component factories and snack giants (think pineapple cakes, mochi, and Taiwan's biggest pineapple-tart maker). A small-town manufacturing powerhouse.</p>
    </div>
    <div class="about-card about-card--green">
      <span class="about-card-icon">🍚</span>
      <h4>Rice &amp; agriculture<span class="about-card-zh">米鄉</span></h4>
      <p>Called <em>"Taiwan's rice basket."</em> The Zhuoshui-fed paddies of Ershui, Tianzhong, and Xizhou yield some of the island's most-praised rice — and pomelo, asparagus, lychee on the side.</p>
    </div>
    <div class="about-card about-card--blue">
      <span class="about-card-icon">🪟</span>
      <h4>Lukang glass &amp; crafts<span class="about-card-zh">鹿港玻璃／工藝</span></h4>
      <p>Stained-glass mazu temples, hand-blown glass shrines, lantern-makers, tin-smiths, woodcarvers. Lukang remains Taiwan's densest concentration of traditional craftspeople.</p>
    </div>
    <div class="about-card about-card--orange">
      <span class="about-card-icon">🍜</span>
      <h4>Street-food culture<span class="about-card-zh">小吃文化</span></h4>
      <p>Changhua scallion pancake-wrapped braised pork rice (爌肉飯), Lukang oyster vermicelli (麵線糊), Yuanlin chicken-foot jelly (雞腳凍), Beidou rice dumplings (肉粽). A whole atlas of regional snacks.</p>
    </div>
  </div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">Iconic places to visit <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">必訪景點</span></h2>
  <p style="color:var(--hub-ink-soft)">If you only have a weekend in Changhua, start here.</p>

  <div class="about-grid about-grid--3">
    <div class="about-card about-card--blue">
      <span class="about-card-icon">🪷</span>
      <h4>Bagua Mountain Great Buddha<span class="about-card-zh">八卦山大佛</span></h4>
      <p>A <strong>22 m bronze Buddha</strong> overlooking Changhua City since 1961 — the county's most-photographed landmark. The skywalk behind it gives the best sunset view of the central plain.</p>
    </div>
    <div class="about-card about-card--orange">
      <span class="about-card-icon">🛕</span>
      <h4>Lukang Old Street &amp; Longshan Temple<span class="about-card-zh">鹿港老街、龍山寺</span></h4>
      <p>Once Taiwan's second-largest port (<em>一府二鹿三艋舺</em>). Today: Qing-era brick lanes, hand-made pastries, and the 1786 Longshan Temple — often called "the Forbidden City of Taiwan" for its woodwork.</p>
    </div>
    <div class="about-card about-card--green">
      <span class="about-card-icon">🚂</span>
      <h4>Changhua Roundhouse<span class="about-card-zh">彰化扇形車庫</span></h4>
      <p>Taiwan's <strong>only surviving fan-shaped locomotive depot</strong> (1922). A working turntable rotates real steam and diesel engines for railway fans. Free to visit.</p>
    </div>
    <div class="about-card about-card--purple">
      <span class="about-card-icon">🌊</span>
      <h4>Wanggong Fishing Port<span class="about-card-zh">王功漁港</span></h4>
      <p>Sunset over the oyster farms, ox-cart rides at low tide, and the red-and-white Wanggong Lighthouse. The west-coast Changhua experience in one afternoon.</p>
    </div>
    <div class="about-card about-card--blue">
      <span class="about-card-icon">🏛️</span>
      <h4>Changhua Confucian Temple<span class="about-card-zh">彰化孔廟</span></h4>
      <p>Built in 1726 — <strong>Taiwan's second-oldest Confucian temple.</strong> A five-minute walk from the county's Department of Education building. Confucius would approve.</p>
    </div>
    <div class="about-card about-card--green">
      <span class="about-card-icon">🌷</span>
      <h4>Tianwei Highway Garden<span class="about-card-zh">田尾公路花園</span></h4>
      <p>Six kilometres of nurseries and flower farms — a slow drive past every orchid, rose, hydrangea, and bonsai you can imagine. Best in spring and autumn.</p>
    </div>
  </div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">Cultural figures &amp; festivals <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">人物與節慶</span></h2>
  <p style="color:var(--hub-ink-soft)">A county's character lives in the people it produces and the rituals it keeps.</p>

  <div class="about-grid">
    <div class="about-card">
      <span class="about-card-icon">✍️</span>
      <h4>Lai Ho (賴和, 1894–1943)<span class="about-card-zh">「台灣新文學之父」</span></h4>
      <p>Doctor, poet, and social-reformer born in Changhua City. Wrote in Taiwanese and Chinese during the Japanese era to give voice to ordinary farmers. His former clinic is now the Lai Ho Memorial Hall.</p>
    </div>
    <div class="about-card">
      <span class="about-card-icon">📜</span>
      <h4>Chen Hsu-ku (陳虛谷, 1896–1965)<span class="about-card-zh">和美詩人</span></h4>
      <p>Poet and resistance writer from Hemei. With Lai Ho, anchored the Changhua literary circle that pushed back against colonial censorship through verse and short fiction.</p>
    </div>
    <div class="about-card">
      <span class="about-card-icon">🌾</span>
      <h4>Wu Sheng (吳晟, 1944–)<span class="about-card-zh">當代田園詩人</span></h4>
      <p>Contemporary poet and environmentalist who still farms in Xizhou. His poems about Taiwanese soil, mothers, and trees are taught in classrooms across the country.</p>
    </div>
    <div class="about-card about-card--orange">
      <span class="about-card-icon">🐉</span>
      <h4>Lukang Dragon Boat Festival<span class="about-card-zh">鹿港慶端陽</span></h4>
      <p>Changhua's signature summer festival. Dragon-boat races on the Fulu River, lion dances, lantern parades, and Lukang's old streets at full festival pitch. Mid-June.</p>
    </div>
    <div class="about-card about-card--orange">
      <span class="about-card-icon">⛩️</span>
      <h4>Baishatun Mazu pilgrimage<span class="about-card-zh">白沙屯媽祖進香</span></h4>
      <p>Each spring, the Baishatun Mazu palanquin makes a nine-day pilgrimage that traditionally crosses Changhua — drawing tens of thousands of pilgrims through Lukang and Yuanlin.</p>
    </div>
    <div class="about-card about-card--orange">
      <span class="about-card-icon">🪔</span>
      <h4>Lukang Lantern Festival<span class="about-card-zh">鹿港燈會</span></h4>
      <p>Old Street lit by thousands of hand-painted lanterns for two weeks after Lunar New Year. A century-old tradition that draws photographers from across Asia.</p>
    </div>
  </div>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">Administrative divisions <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">行政區</span></h2>
  <p><strong>26 divisions</strong>: 2 cities (Changhua City &amp; Yuanlin City), 6 urban townships, 18 rural townships.</p>
  <ul class="about-list">
    <li><strong>Cities</strong>: Changhua 彰化 · Yuanlin 員林</li>
    <li><strong>Urban townships</strong>: Hemei 和美 · Lukang 鹿港 · Xihu 溪湖 · Tianzhong 田中 · Beidou 北斗 · Erlin 二林</li>
    <li><strong>Rural townships</strong> (18): Shenkang 伸港, Xianxi 線西, Fuxing 福興, Xiushui 秀水, Huatan 花壇, Fenyuan 芬園, Dacun 大村, Puyan 埔鹽, Puxin 埔心, Yongjing 永靖, Shetou 社頭, Ershui 二水, Tianwei 田尾, Pitou 埤頭, Xizhou 溪州, Zhutang 竹塘, Fangyuan 芳苑, Dacheng 大城.</li>
  </ul>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">Education ecosystem <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">教育生態</span></h2>
  <p>Changhua's bilingual education runs on a tri-partite partnership:</p>
  <ol class="about-list">
    <li><strong>Department of Education, Changhua County Government</strong> (教育處) — sets policy and funds the bilingual program through the Student Affairs &amp; Curriculum Development Division (學務管理及課程發展科), via initiatives like the Teaching Enhancement Program (精進教學計畫) and the Teaching Excellence Awards (教學卓越獎).</li>
    <li><strong>CIEETRC</strong> (彰化縣國際教育暨英語教育資源中心) — produces shared resources and runs the SIEP testing program.</li>
    <li><strong>My Culture Connect</strong> (人師教育協會) — recruits and places foreign English teachers in Changhua schools. Serving the county since 2009.</li>
  </ol>
  <p>The county is home to <strong>3 universities</strong> — <strong>National Changhua University of Education</strong> (NCUE, 國立彰化師範大學, one of Taiwan's three flagship teacher-training universities), Da Yeh University, and Chienkuo Technology University — plus <strong>12 senior high schools</strong> and a dense network of junior high and elementary schools, over 100 of which participate in this Hub.</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">彰化縣擁有 3 所大專院校（國立彰化師範大學、大葉大學、建國科技大學）、12 所高中，以及綿密的國中小網路——其中超過 100 所學校加入本資源網。</p>
</section>

<section class="hub-section hub-section--narrow" style="padding-top:32px">
  <h2 class="hub-h2">Why this Hub exists <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">本平台緣起</span></h2>
  <p>The bilingual sites of more than 100 Changhua schools were scattered across Google Sites, Canva, and dozens of subdomains. This Hub gathers them into one searchable directory, alongside the resources, foreign-teacher profiles, and 3,000 classroom videos that connect them.</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">彰化縣 100 多所學校的雙語網站原本散落在 Google Sites、Canva 與數十個子網域。本平台把它們收進同一份可搜尋的索引，並串接共用資源、外師檔案，以及 3,000 部課堂影片。</p>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("About Changhua", content, "/resources/", extra)


def build_classroom_english():
    situations = [
        ("Greetings &amp; Attendance", "問候語＆點名", "blue", [
            ("Good morning, everyone!", "大家早安！"),
            ("Let me take attendance.", "讓我來點名。"),
            ("Is everyone here today?", "今天大家都到了嗎？"),
            ("Who's absent today?", "今天誰沒來？"),
            ("Please say 'present' when I call your name.", "我叫到名字時請說「到」。"),
        ]),
        ("Pre-Class Preparation", "課前準備", "green", [
            ("Please take out your textbook.", "請拿出課本。"),
            ("Open to page 24.", "翻到第 24 頁。"),
            ("Have your pencil and notebook ready.", "準備好鉛筆和筆記本。"),
            ("Turn off your phones, please.", "請關掉手機。"),
            ("Let's get started.", "我們開始吧。"),
        ]),
        ("Explanations", "講解", "orange", [
            ("Listen carefully to this part.", "這個部分要仔細聽。"),
            ("Does everyone understand?", "大家都明白嗎？"),
            ("Let me say that again, more slowly.", "我再說一次，慢一點。"),
            ("Can you give me an example?", "可以給我一個例子嗎？"),
            ("That's right!", "答對了！"),
        ]),
        ("Pre-Class Activities", "課前教學活動", "purple", [
            ("Today we'll start with a warm-up game.", "今天我們先玩個暖身遊戲。"),
            ("Pair up with the student next to you.", "和你旁邊的同學配對。"),
            ("Stand up and stretch.", "站起來伸展一下。"),
            ("Let's review what we learned yesterday.", "讓我們複習昨天學的。"),
        ]),
        ("Feedback", "回饋", "blue", [
            ("Great job, everyone!", "大家做得很棒！"),
            ("Well done, you tried your best.", "做得好，你盡力了。"),
            ("Almost — try one more time.", "差一點 — 再試一次。"),
            ("That's a creative answer.", "這個答案很有創意。"),
            ("I'm proud of you.", "我以你為榮。"),
        ]),
        ("Classroom Management", "教室管理", "green", [
            ("Please raise your hand.", "請舉手。"),
            ("Eyes on me, please.", "請看老師。"),
            ("Quiet down, please.", "請安靜。"),
            ("Sit up straight.", "坐直。"),
            ("Wait your turn.", "輪到你再說。"),
        ]),
        ("In-Class Activities", "課堂教學活動", "orange", [
            ("Let's form groups of four.", "我們分成四人一組。"),
            ("You have ten minutes for this activity.", "這個活動有十分鐘。"),
            ("Who wants to go first?", "誰想先來？"),
            ("Share your answer with the class.", "和全班分享你的答案。"),
            ("Take turns speaking.", "輪流發言。"),
        ]),
        ("Assignment Distribution", "分派作業", "purple", [
            ("Your homework for tonight is...", "今晚的回家作業是⋯⋯"),
            ("This is due next Wednesday.", "下週三交。"),
            ("Please write it neatly.", "請寫整齊。"),
            ("Don't forget to put your name on it.", "別忘了寫上名字。"),
            ("Any questions about the assignment?", "對作業有任何問題嗎？"),
        ]),
        ("Class Closing", "課堂收尾", "blue", [
            ("Let's wrap up.", "我們收尾吧。"),
            ("What did we learn today?", "今天我們學了什麼？"),
            ("See you tomorrow!", "明天見！"),
            ("Have a great weekend.", "週末愉快。"),
            ("Don't forget your homework.", "別忘了作業。"),
        ]),
        ("Tests &amp; Exams", "考試", "green", [
            ("Put away everything except your pencil.", "除了鉛筆，其他東西都收起來。"),
            ("Read each question carefully.", "每題都要仔細讀。"),
            ("You have 40 minutes.", "你們有 40 分鐘。"),
            ("If you finish early, check your answers.", "提早寫完就檢查答案。"),
            ("Pencils down, please.", "請放下筆。"),
        ]),
    ]

    sections = []
    for i, (en, zh, color, phrases) in enumerate(situations, 1):
        items = ''.join(
            f'<li class="ce-phrase"><span class="en">{p_en}</span><span class="zh">{p_zh}</span></li>'
            for p_en, p_zh in phrases
        )
        sections.append(f"""
<article class="ce-card t-{color}">
  <div class="ce-head">
    <p class="ce-num">Situation {i:02d}</p>
    <h2 class="ce-title">{en}</h2>
    <p class="ce-zh">{zh}</p>
  </div>
  <ul class="ce-phrases">{items}</ul>
</article>
""".strip())

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Resources · Classroom English</p>
  <h1 class="hub-h1">Classroom English</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:62ch">
    Ten everyday classroom situations with ready-to-use English phrases — taught by <strong>Sarah Thomas</strong> for My Culture Connect. Watch the full series below, then keep the phrase list nearby for daily reference.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch">
    十個教室日常情境的實用英文短句——由 <strong>Sarah Thomas</strong> 為人師教育協會主講。先看完整系列影片，再把下方的短句清單放在手邊。
  </p>

  <div class="playlist-wrap">
    <div class="playlist-frame">
      <iframe
        src="https://www.youtube-nocookie.com/embed/videoseries?list=PL01OhMUI2G8UDZ8tSZ6MTGyjXsGEJ24wZ&rel=0"
        title="Classroom English playlist · Sarah Thomas · My Culture Connect"
        allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen></iframe>
    </div>
    <p class="playlist-credit">
      🎬 Playlist by <strong>Sarah Thomas</strong> · produced by <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect 人師教育協會</a>
    </p>
  </div>

  <h2 class="resources-h2" style="margin-top:64px">Phrase reference · 短句參考</h2>
  <div class="ce-grid">
    {''.join(sections)}
  </div>

  <p style="margin-top:48px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("Classroom English", content, "/resources/", extra)


def build_announcements():
    content = """
<section class="hub-section">
  <p class="hub-eyebrow">Resources · Bilingual Campus</p>
  <h1 class="hub-h1">Bilingual Announcements <small style="font-family:var(--hub-zh-font);font-size:.45em;color:var(--hub-ink-faint);font-weight:500;letter-spacing:.05em">校園廣播英語</small></h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:62ch">
    A 13-episode bilingual series introducing the four administrative offices that keep a Taiwan elementary school running — taught by <strong>Sarah Thomas</strong> and <strong>Susan Rose</strong> for My Culture Connect.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch">
    13 集雙語影片，介紹台灣國小四大處室——教務處 5 集、學務處 3 集、總務處、輔導室。由 <strong>Sarah Thomas</strong> 與 <strong>Susan Rose</strong> 為人師教育協會主講。
  </p>

  <div class="playlist-wrap">
    <div class="playlist-frame">
      <iframe
        src="https://www.youtube-nocookie.com/embed/videoseries?list=PL01OhMUI2G8U2l5LnxUpEA_Uvi-5wdTKy&rel=0"
        title="Bilingual Announcements playlist · Sarah Thomas & Susan Rose · My Culture Connect"
        allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen></iframe>
    </div>
    <p class="playlist-credit">
      🎬 Playlist by <strong>Sarah Thomas</strong> &amp; <strong>Susan Rose</strong> · produced by <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect 人師教育協會</a>
    </p>
  </div>

  <h2 class="resources-h2" style="margin-top:64px">What's covered · 內容大綱</h2>
  <div class="hub-feature-grid">
    <div class="hub-card">
      <h3>教務處 Academic Affairs</h3>
      <p>The hub of curriculum, exams, and student records — 5 episodes covering schedules, course planning, and the everyday work of academic administration.</p>
      <div class="hub-card-meta">5 episodes</div>
    </div>
    <div class="hub-card">
      <h3>學務處 Student Affairs</h3>
      <p>Safety, conduct, and student life — 3 episodes on discipline, campus events, and supporting student wellbeing.</p>
      <div class="hub-card-meta">3 episodes</div>
    </div>
    <div class="hub-card">
      <h3>總務處 General Affairs</h3>
      <p>Facilities, budget, and operations — how the school's physical environment is maintained and procured.</p>
      <div class="hub-card-meta">2 episodes</div>
    </div>
    <div class="hub-card">
      <h3>輔導室 Counseling Office</h3>
      <p>Student wellbeing, family liaison, and special-education support — the office that listens.</p>
      <div class="hub-card-meta">3 episodes</div>
    </div>
  </div>

  <h2 class="resources-h2" style="margin-top:64px">For schools using this · 學校使用方式</h2>
  <p>This playlist is freely embeddable. Schools can use it on their announcement page, in morning assemblies, or as a starting reference for staff who handle bilingual broadcasts.</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">本 playlist 可自由嵌入。各校可放在「廣播」單元、朝會播放，或當作雙語廣播輪值人員的入門參考。</p>

  <p style="margin-top:48px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("Bilingual Announcements", content, "/resources/", extra)


def build_books_for_taiwan():
    content = """
<section class="hub-section hub-section--narrow">
  <p class="hub-eyebrow">Resources · Books for Taiwan</p>
  <h1 class="hub-h1">Books for Taiwan</h1>
  <p style="font-size:1.15rem;color:var(--hub-ink-soft);line-height:1.65;margin-top:24px">
    A volunteer-run program started in <strong>April 2012</strong> by <strong>Amy Lin</strong>. American volunteers — predominantly young professionals and students — collect and donate English-language books and audiovisual materials to schools, libraries, and correctional facilities throughout Taiwan.
  </p>
  <p class="hub-zh" style="font-size:1.05rem;color:var(--hub-ink-soft);line-height:1.7;margin-top:18px">
    由 Amy Lin 於 2012 年 4 月發起的志工計畫。美國志工——以年輕專業人士與學生為主——募集並捐贈英文書籍與視聽教材給台灣的學校、圖書館與矯正機構。
  </p>

  <h2 class="hub-h2" style="margin-top:56px">What's collected <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">收集項目</span></h2>
  <ul class="about-list">
    <li>Children's literature 童書</li>
    <li>Young adult books 青少年讀物</li>
    <li>Hardcover general-interest volumes 精裝叢書</li>
    <li>Cookbooks 食譜</li>
    <li>Audiovisual media (CDs, DVDs) 視聽教材</li>
  </ul>
  <p>Materials are sourced primarily from American libraries that are deaccessioning their collections.</p>

  <h2 class="hub-h2" style="margin-top:56px">Where books go <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">捐贈對象</span></h2>
  <p>Books arrive at schools, public libraries, and correctional facilities across Taiwan. Recipients have included rural elementary schools (in Changhua and beyond), prison libraries, and culinary programs that benefit from authentic Western cookbooks.</p>

  <h2 class="hub-h2" style="margin-top:56px">Why it matters <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">計畫的意義</span></h2>
  <p>Three stated goals:</p>
  <ol class="about-list">
    <li><strong>Build comfort and curiosity with English</strong> — Taiwanese students see English as living, not just academic.</li>
    <li><strong>Support culinary &amp; vocational learning</strong> — culinary students prepare authentic Western cuisine from primary-source recipes.</li>
    <li><strong>Carry warmth across the Pacific</strong> — American donors send not just books but a gesture of optimism and connection.</li>
  </ol>

  <p style="margin-top:56px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    return page_shell("Books for Taiwan", content, "/resources/")


SDGS = [
    # (n, icon, en, zh, group_en, group_zh, color, en_summary, zh_summary, [prompts])
    (1,  "💰", "No Poverty",                            "終結貧窮",           "People",      "人類",       "#E5243B",
         "Make sure everyone has enough to live a safe, healthy life.",
         "讓每個人都能擁有安全、健康的生活。",
         ["Are there students in your school who don't have lunch money? How can you help?",
          "What's one thing your family does to help neighbors in need?",
          "Brainstorm 3 ways your class could support a local charity."]),
    (2,  "🌾", "Zero Hunger",                           "消除飢餓",           "People",      "人類",       "#DDA63A",
         "Everyone deserves enough food — and the right kind of food.",
         "每個人都應該擁有足夠且營養的食物。",
         ["How does your school's lunch program reduce food waste?",
          "Where does the rice on your plate come from? (Hint: probably a Changhua farm!)",
          "Plan a 'sharing meal' where each student brings something to share."]),
    (3,  "🏥", "Good Health & Well-being",              "健康與福祉",         "People",      "人類",       "#4C9F38",
         "Stay healthy in body and mind — at every age.",
         "在每個年齡都能身心健康。",
         ["What 3 habits keep you healthy at school?",
          "How does your school help students who feel sad or stressed?",
          "Plan a 10-minute daily exercise routine you can do at home."]),
    (4,  "📚", "Quality Education",                     "優質教育",           "People",      "人類",       "#C5192D",
         "Every child gets to go to school and learn well.",
         "讓每個孩子都能上學並好好學習。",
         ["Why is bilingual education important for your future?",
          "What's one subject you wish your school taught more of?",
          "Interview a senior in your family — what was school like in their time?"]),
    (5,  "👫", "Gender Equality",                       "性別平等",           "People",      "人類",       "#FF3A21",
         "Boys and girls should have the same chances, choices, and respect.",
         "男生女生應該擁有同樣的機會、選擇與尊重。",
         ["Are there activities at your school that only boys or only girls do? Why?",
          "Name 3 women in science, sports, or leadership you admire.",
          "What does fair sharing of housework look like at your home?"]),
    (6,  "💧", "Clean Water & Sanitation",              "潔淨水與衛生",       "Planet",      "地球",       "#26BDE2",
         "Clean water for drinking, washing, and farming — for everyone.",
         "讓每個人都有乾淨的水可以喝、洗、灌溉。",
         ["Track your water use for one day. Where could you save?",
          "How does Changhua's water travel from the mountains to your tap?",
          "What happens to the dirty water after it goes down the drain?"]),
    (7,  "⚡", "Affordable & Clean Energy",             "可負擔的潔淨能源",   "Prosperity",  "繁榮",       "#FCC30B",
         "Use energy that doesn't pollute and that everyone can afford.",
         "使用不污染、人人負擔得起的能源。",
         ["Count the lights and devices on at your home right now. Could any be off?",
          "What's the difference between solar energy and coal energy?",
          "If your school had a solar roof, what could it power?"]),
    (8,  "💼", "Decent Work & Economic Growth",         "尊嚴就業與經濟成長", "Prosperity",  "繁榮",       "#A21942",
         "Everyone should have a fair job that pays enough and is safe.",
         "每個人都該有公平、安全、足夠的工作。",
         ["What do your parents do for work? What do they like about it?",
          "What's one job in Changhua that didn't exist 20 years ago?",
          "Interview a local farmer or shopkeeper about their work."]),
    (9,  "🏗️", "Industry, Innovation & Infrastructure", "產業創新與基礎建設", "Prosperity",  "繁榮",       "#FD6925",
         "Build strong roads, bridges, and ideas to help society grow.",
         "建造堅固的道路、橋樑與創新點子，幫助社會進步。",
         ["What's the newest building in your town? What's it used for?",
          "What invention has changed your life the most?",
          "Design a bridge or road that connects two parts of your town."]),
    (10, "🤝", "Reduced Inequalities",                  "減少不平等",         "Prosperity",  "繁榮",       "#DD1367",
         "Everyone deserves the same chances, no matter who they are.",
         "不論身分背景，每個人都該有同樣的機會。",
         ["Have you ever been treated unfairly? How did it feel?",
          "How does your school welcome new students from other places?",
          "Plan a 'kindness day' at your school where every student is included."]),
    (11, "🏙️", "Sustainable Cities & Communities",      "永續城鄉",           "Prosperity",  "繁榮",       "#FD9D24",
         "Make our towns safer, cleaner, and more welcoming.",
         "讓城市與鄉村更安全、乾淨、宜居。",
         ["What's the prettiest place in your township? Why?",
          "How could your school playground be safer?",
          "Suggest one small change that would make your neighborhood greener."]),
    (12, "🛒", "Responsible Consumption & Production",  "責任消費與生產",     "Planet",      "地球",       "#BF8B2E",
         "Buy less, use longer, throw away less.",
         "少買、耐用、少丟棄。",
         ["How many things in your school bag are reusable?",
          "What's one item your family threw away that could have been used longer?",
          "Plan a class 'swap day' where everyone trades books or toys."]),
    (13, "🌍", "Climate Action",                        "氣候行動",           "Planet",      "地球",       "#3F7E44",
         "Help slow down climate change before it's too late.",
         "在來不及之前，一起減緩氣候變遷。",
         ["How is the weather in Changhua different from your grandparents' time?",
          "Name 3 things your family does that release CO₂.",
          "Plan one 'no electricity' hour for your home each week."]),
    (14, "🐠", "Life Below Water",                      "海洋生態",           "Planet",      "地球",       "#0A97D9",
         "Protect the oceans, rivers, and the creatures that live in them.",
         "保護海洋、河川與其中的生物。",
         ["Changhua faces the Taiwan Strait. What sea creatures live near your coast?",
          "Trace a piece of trash from your home — could it reach the ocean?",
          "Design a poster to tell people not to litter at the beach."]),
    (15, "🌳", "Life on Land",                          "陸地生態",           "Planet",      "地球",       "#56C02B",
         "Protect forests, fields, and the animals that share our home.",
         "保護森林、田野與我們的動物鄰居。",
         ["Name 5 trees or birds you can see in your school yard.",
          "What's one animal that used to live near Changhua but is now rare?",
          "Plant a seed at home and write a journal about how it grows."]),
    (16, "🕊️", "Peace, Justice & Strong Institutions",  "和平、正義與健全制度", "Peace",     "和平",       "#00689D",
         "Be fair, be peaceful, and trust each other to keep promises.",
         "公平、和平，並彼此信任、信守承諾。",
         ["What rules at your school make everyone feel safe?",
          "Have you ever solved a disagreement peacefully? How?",
          "Why do we have laws? What would happen without them?"]),
    (17, "🌐", "Partnerships for the Goals",            "多元夥伴關係",       "Partnership", "夥伴關係",   "#19486A",
         "Work together — schools, families, governments — to reach all the goals.",
         "學校、家庭、政府一起合作，達成所有目標。",
         ["Who are your school's partners (e.g. the Education Department, MCC, foreign teachers)?",
          "What's one goal your class could tackle together this year?",
          "Pick one SDG from above and plan a class project around it."]),
]


def build_sdgs():
    # 5P groups for section headings
    PILLARS = [
        ("People",      "人類",         "Five goals that ensure no one is left behind: ending poverty, hunger, and inequality; protecting health, education, and dignity for all.",
                                        "五項確保「不讓任何人被遺忘」的目標：消除貧窮、飢餓與不平等；守護每個人的健康、教育與尊嚴。", [1,2,3,4,5]),
        ("Prosperity",  "繁榮",         "Five goals that build a fair, modern economy: clean energy, decent work, innovation, equality, and sustainable cities.",
                                        "五項建立公平現代經濟的目標：潔淨能源、尊嚴就業、創新、平等、永續城市。", [7,8,9,10,11]),
        ("Planet",      "地球",         "Five goals that protect the Earth: clean water, responsible consumption, climate action, oceans, and land.",
                                        "五項保護地球的目標：潔淨水、責任消費、氣候行動、海洋與陸地生態。", [6,12,13,14,15]),
        ("Peace",       "和平",         "One goal anchoring fairness, safety, and trust in our institutions.",
                                        "一項目標，為公平、安全與制度信任奠基。", [16]),
        ("Partnership", "夥伴關係",     "One goal that reminds us: alone we go faster, together we go farther.",
                                        "一項目標提醒我們：獨行快、眾行遠。", [17]),
    ]
    by_n = {n: t for t in SDGS for nn in [t[0]] if (n := nn)}

    def card_html(t):
        n, icon, en, zh, group_en, group_zh, color, en_sum, zh_sum, qs = t
        # URL-safe slug from English title
        slug = re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")
        base = f"/resources/sdgs/{n:02d}-{slug}"
        return f"""
<article class="sdg" style="--sdg:{color}">
  <div class="sdg__head">
    <div class="sdg__icon">{icon}</div>
    <div class="sdg__main">
      <div class="sdg__meta">
        <span class="sdg__no">SDG {n:02d}</span>
        <span class="sdg__pillar">{group_en} · {group_zh}</span>
      </div>
      <div class="sdg__title">{en}</div>
      <div class="sdg__zh">{zh}</div>
    </div>
  </div>
  <div class="sdg__brief">{en_sum}</div>
  <div class="sdg__brief-zh">{zh_sum}</div>
  <div class="sdg__buttons">
    <a class="sdg-btn sdg-btn--handout" href="{base}/">📖 Handout · 講義</a>
    <a class="sdg-btn sdg-btn--quiz" href="{base}/quiz/">📝 Quiz · 測驗</a>
  </div>
</article>
""".strip()

    sections_html = []
    for pillar_en, pillar_zh, blurb_en, blurb_zh, indices in PILLARS:
        cards = ''.join(card_html(by_n[i]) for i in indices)
        sections_html.append(f"""
<section class="pillar">
  <h2 class="pillar__title">{pillar_en} <small>{pillar_zh} · {len(indices)} goal{'s' if len(indices)>1 else ''}</small></h2>
  <p class="pillar__brief">{blurb_en}</p>
  <p class="pillar__brief-zh">{blurb_zh}</p>
  <div class="sdg-grid">{cards}</div>
</section>
""".strip())

    content = f"""
<header class="sdg-head-strip">
  <div class="sdg-head-strip__brand">United Nations 2030 Agenda · 彰化雙語資源網</div>
  <h1 class="sdg-head-strip__title">17 Sustainable Development Goals</h1>
  <div class="sdg-head-strip__zh">永續發展目標 · 17 項全球共同承諾</div>
  <div class="sdg-head-strip__sub">A classroom-ready adaptation for elementary &amp; junior-high students in Changhua.</div>
</header>

<section class="sdg-intro wrap">
  <div class="sdg-intro__title">5 pillars · 17 goals · one shared planet.</div>
  <div class="sdg-intro__zh">五大支柱、十七項目標、一個共有的星球。</div>
  <p class="sdg-intro__body">The UN's 17 SDGs are the world's shared to-do list for the year 2030. Below, we group them into the UN's five "P" pillars — <strong>People, Prosperity, Planet, Peace, Partnership</strong> — and adapt each goal for Changhua's classrooms.</p>
  <p class="sdg-intro__body hub-zh">聯合國 17 項永續發展目標（SDGs）是全世界共同努力到 2030 年的目標。下面依聯合國「5P」框架（人類、繁榮、地球、和平、夥伴關係）分組，並為彰化教室改編每項目標。</p>
</section>

<main class="wrap sdg-main">
  {''.join(sections_html)}
</main>

<p style="text-align:center;padding:24px 0 48px;color:var(--hub-ink-faint);font-size:.95rem">
  <a href="/resources/">← Back to Resources</a>
</p>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/sdgs.css">'
    return page_shell("17 SDGs", content, "/resources/", extra)


def build_sdg_handout(n, icon, en, zh, group_en, group_zh, color, en_sum, zh_sum, prompts):
    content = SDG_CONTENT.get(n)
    slug = re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")
    base = f"/resources/sdgs/{n:02d}-{slug}"

    vocab_html = ""
    activity_html = ""
    if content:
        vocab_rows = ''.join(
            f'<tr><td class="vocab-en">{w_en}</td><td class="vocab-zh">{w_zh}</td><td class="vocab-def">{def_en}<br><span class="zh">{def_zh}</span></td></tr>'
            for w_en, w_zh, def_en, def_zh in content["vocab"]
        )
        vocab_html = f"""
<section class="sdg-detail-section">
  <h2 class="sdg-detail-h2">Vocabulary <span class="zh">單字</span></h2>
  <table class="sdg-vocab">
    <thead><tr><th>English</th><th>中文</th><th>Definition · 釋義</th></tr></thead>
    <tbody>{vocab_rows}</tbody>
  </table>
</section>
""".strip()

        act = content["activity"]
        activity_html = f"""
<section class="sdg-detail-section">
  <h2 class="sdg-detail-h2">Classroom Activity <span class="zh">課堂活動</span></h2>
  <div class="sdg-activity">
    <h3 class="sdg-activity-title">{act['title_en']}</h3>
    <p class="sdg-activity-zh-title">{act['title_zh']}</p>
    <p class="sdg-activity-body">{act['body_en']}</p>
    <p class="sdg-activity-body zh">{act['body_zh']}</p>
  </div>
</section>
""".strip()

    prompts_html = ''.join(f'<li>{p}</li>' for p in prompts)

    page = f"""
<article class="sdg-detail" style="--sdg:{color}">
  <header class="sdg-detail-hero">
    <div class="sdg-detail-icon">{icon}</div>
    <div class="sdg-detail-head">
      <p class="sdg-detail-eyebrow">SDG {n:02d} · {group_en} 人類&prosperity&planet&peace&partnership / {group_zh}</p>
      <h1 class="sdg-detail-title">{en}</h1>
      <p class="sdg-detail-zh">{zh}</p>
    </div>
  </header>

  <section class="sdg-detail-section">
    <h2 class="sdg-detail-h2">In one sentence <span class="zh">一句話</span></h2>
    <p class="sdg-detail-lede">{en_sum}</p>
    <p class="sdg-detail-lede zh">{zh_sum}</p>
  </section>

  {vocab_html}

  {activity_html}

  <section class="sdg-detail-section">
    <h2 class="sdg-detail-h2">Discussion prompts <span class="zh">討論題</span></h2>
    <ul class="sdg-detail-prompts">{prompts_html}</ul>
  </section>

  <div class="sdg-detail-cta">
    <a class="sdg-btn sdg-btn--quiz sdg-btn-big" href="{base}/quiz/">📝 Take the quiz · 開始測驗 →</a>
  </div>

  <p style="margin-top:40px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/sdgs/">← All 17 SDGs</a> · <a href="/resources/">← Resources</a>
  </p>
</article>
""".strip()

    # Replace the typo placeholder
    page = page.replace(f"{group_en} 人類&prosperity&planet&peace&partnership / {group_zh}", f"{group_en} · {group_zh}")

    extra = '<link rel="stylesheet" href="/assets/css/sdgs.css">'
    return page_shell(f"SDG {n:02d} · {en}", page, "/resources/", extra)


def build_sdg_quiz(n, icon, en, zh, group_en, group_zh, color, en_sum, zh_sum):
    content = SDG_CONTENT.get(n)
    if not content:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")
    base = f"/resources/sdgs/{n:02d}-{slug}"
    questions = content["quiz"]

    q_html_blocks = []
    for i, q in enumerate(questions, 1):
        opts = q["options"]
        opt_html = ''.join(
            f'<label class="quiz-opt"><input type="radio" name="q{i}" value="{j}"><span class="opt-letter">{chr(65+j)}</span><span class="opt-text"><strong>{en_text}</strong><br><span class="zh">{zh_text}</span></span></label>'
            for j, (en_text, zh_text) in enumerate(opts)
        )
        q_html_blocks.append(f"""
<article class="quiz-q" data-q="{i-1}">
  <p class="quiz-q-num">Question {i}</p>
  <h3 class="quiz-q-en">{q['q_en']}</h3>
  <p class="quiz-q-zh">{q['q_zh']}</p>
  <div class="quiz-opts">{opt_html}</div>
  <div class="quiz-feedback" hidden>
    <p class="quiz-feedback-en">{q['explain_en']}</p>
    <p class="quiz-feedback-zh">{q['explain_zh']}</p>
  </div>
</article>
""".strip())

    correct_array = json.dumps([q["correct"] for q in questions])

    page = f"""
<article class="quiz-page" style="--sdg:{color}">
  <header class="quiz-hero">
    <div class="sdg-detail-icon">{icon}</div>
    <div>
      <p class="sdg-detail-eyebrow">SDG {n:02d} · Quiz · 測驗</p>
      <h1 class="quiz-title">{en}</h1>
      <p class="sdg-detail-zh">{zh}</p>
    </div>
  </header>

  <p class="quiz-instructions">Five questions · 五題選擇題. Pick the best answer for each. When you're done, hit Submit.</p>
  <p class="quiz-instructions zh">五題選擇題。每題選最佳答案，全部完成後按 Submit。</p>

  <form id="quiz-form" class="quiz-form">
    {''.join(q_html_blocks)}
    <div class="quiz-submit-wrap">
      <button type="submit" class="sdg-btn sdg-btn--quiz sdg-btn-big">Submit · 交卷</button>
    </div>
  </form>

  <div id="quiz-result" class="quiz-result" hidden>
    <p class="quiz-score-label">Your score · 你的得分</p>
    <p class="quiz-score-big"><span id="quiz-score">0</span> / {len(questions)}</p>
    <p id="quiz-grade" class="quiz-grade"></p>
    <div class="quiz-result-cta">
      <button type="button" id="quiz-retry" class="sdg-btn sdg-btn--handout">↻ Try again · 再試一次</button>
      <a class="sdg-btn sdg-btn--quiz" href="{base}/">📖 Review handout</a>
    </div>
  </div>

  <p style="margin-top:40px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="{base}/">← Back to handout</a> · <a href="/resources/sdgs/">All SDGs</a>
  </p>
</article>

<script>
(function(){{
  var CORRECT = {correct_array};
  var form = document.getElementById('quiz-form');
  var result = document.getElementById('quiz-result');
  var scoreEl = document.getElementById('quiz-score');
  var gradeEl = document.getElementById('quiz-grade');
  var retry = document.getElementById('quiz-retry');
  form.addEventListener('submit', function(e){{
    e.preventDefault();
    var score = 0;
    CORRECT.forEach(function(c, i){{
      var qEl = form.querySelector('[data-q="' + i + '"]');
      var chosen = qEl.querySelector('input:checked');
      var fb = qEl.querySelector('.quiz-feedback');
      var inputs = qEl.querySelectorAll('input');
      inputs.forEach(function(inp){{ inp.disabled = true; }});
      // mark correct option
      var correctLabel = qEl.querySelectorAll('.quiz-opt')[c];
      correctLabel.classList.add('is-correct');
      if (chosen){{
        var chosenIdx = parseInt(chosen.value, 10);
        if (chosenIdx === c){{ score++; }}
        else {{ chosen.closest('.quiz-opt').classList.add('is-wrong'); }}
      }}
      fb.hidden = false;
    }});
    scoreEl.textContent = score;
    var pct = score / CORRECT.length;
    if (pct === 1) gradeEl.textContent = '🌟 Perfect! 滿分！';
    else if (pct >= 0.8) gradeEl.textContent = '✨ Great work! 太厲害了！';
    else if (pct >= 0.6) gradeEl.textContent = '👍 Good effort! 表現不錯！';
    else gradeEl.textContent = '💪 Read the handout and try again. 看講義再來一次。';
    result.hidden = false;
    result.scrollIntoView({{behavior:'smooth', block:'center'}});
  }});
  retry.addEventListener('click', function(){{
    form.reset();
    form.querySelectorAll('input').forEach(function(inp){{ inp.disabled = false; }});
    form.querySelectorAll('.quiz-opt').forEach(function(o){{ o.classList.remove('is-correct','is-wrong'); }});
    form.querySelectorAll('.quiz-feedback').forEach(function(fb){{ fb.hidden = true; }});
    result.hidden = true;
    form.scrollIntoView({{behavior:'smooth', block:'start'}});
  }});
}})();
</script>
""".strip()

    extra = '<link rel="stylesheet" href="/assets/css/sdgs.css">'
    return page_shell(f"SDG {n:02d} Quiz · {en}", page, "/resources/", extra)


def build_eric_berman():
    stories = [
        ("Kite-Making at Siling Elementary", "西陵國小放風箏",
         "Siling Elementary has a long tradition of crafting kites. When students from New York visited, they joined the workshop — making kites by hand, decorating them with markers, and then taking them out to the school track to fly.",
         "西陵國小有悠久的風箏製作傳統。當紐約來的學生來訪時，他們加入了風箏工作坊——親手做風箏、用麥克筆裝飾，然後把風箏帶到學校跑道上放飛。"),
        ("Taking Attendance", "課堂點名",
         "Taking attendance is an important part of every class. The teacher calls each student's name and records whether they are present or absent. It teaches students to listen for their names and to respond clearly — a small daily ritual that builds language confidence.",
         "點名是每堂課的重要環節。老師叫出每個學生的名字，記錄他們是否到課。這教學生聽自己的名字並清楚回應——這個微小的日常儀式，建立了語言的自信。"),
        ("A Lecture on Law at Datong Elementary", "大同國小法律講座",
         "A visiting teacher gave a presentation about law at Datong Elementary. He explained why laws matter in society and described career paths that work with the law — including judges, prosecutors, and legal practitioners. Students asked thoughtful questions about fairness and rules.",
         "一位訪問老師到大同國小演講法律。他說明法律在社會中的重要性，介紹了與法律相關的職涯選項——包括法官、檢察官與律師。學生們提出關於公平與規則的深度問題。"),
        ("First Grade Orientation at Datong", "大同國小一年級開學典禮",
         "Datong Elementary holds an opening ceremony for new first graders. Parents accompany their children through symbolic gates representing politeness, intelligence, and diligent study. It marks the start of six years of elementary education — and the families' shared commitment to learning.",
         "大同國小為新生一年級舉辦開學典禮。家長陪伴孩子穿越象徵「禮貌、聰明、勤學」三道門。這標誌著六年小學教育的起點——以及家庭對學習的共同承諾。"),
    ]
    cards = []
    for i, (en_title, zh_title, en_body, zh_body) in enumerate(stories, 1):
        cards.append(f"""
<article class="story-card">
  <p class="story-num">Story {i:02d}</p>
  <h2 class="story-title">{en_title}</h2>
  <p class="story-title-zh">{zh_title}</p>
  <div class="story-body">
    <p class="story-en">{en_body}</p>
    <p class="story-zh">{zh_body}</p>
  </div>
</article>
""".strip())
    content = f"""
<section class="hub-section hub-section--narrow">
  <p class="hub-eyebrow">Resources · Eric Berman 故事集</p>
  <h1 class="hub-h1">Four classroom stories.</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:60ch">
    Four short bilingual stories about everyday classroom life in Changhua — produced by Eric Berman for the legacy Bilingual Hub.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">由 Eric Berman 為舊版彰化雙語資源網製作的四則雙語故事，記錄彰化校園的日常。</p>

  <div class="story-list">
    {''.join(cards)}
  </div>

  <p style="margin-top:48px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("Eric Berman 故事集", content, "/resources/", extra)


def write(path, html):
    p = ROOT / path.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    print(f"  wrote {path}  ({len(html):,} bytes)")


def main():
    townships = load_yaml("townships.yml")
    # Sort townships by ZIP code (500 → 530) — matches the legacy Changhua hub order
    townships["townships"].sort(key=lambda t: int(t["zip"]))
    schools = load_yaml("schools.yml")
    fets = load_yaml("fets.yml")
    wotd_items = load_wotd()
    print(f"Loaded: {len(townships['townships'])} townships, {len(schools['schools'])} schools, {len(fets['fets'])} fets, {len(wotd_items)} wotd videos")
    write("index.html", build_home(townships, schools, wotd_items))
    write("schools/index.html", build_schools(townships, schools))
    write("fets/index.html", build_fets(fets, schools))
    write("word-of-the-day/index.html", build_wotd())
    write("resources/index.html", build_resources())
    write("resources/about-changhua/index.html", build_about_changhua())
    write("resources/classroom-english/index.html", build_classroom_english())
    write("resources/books-for-taiwan/index.html", build_books_for_taiwan())
    write("resources/eric-berman/index.html", build_eric_berman())
    write("resources/sdgs/index.html", build_sdgs())
    # 17 SDG handout + quiz pages
    for sdg in SDGS:
        n, icon, en, zh, group_en, group_zh, color, en_sum, zh_sum, prompts = sdg
        slug = re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")
        write(f"resources/sdgs/{n:02d}-{slug}/index.html",
              build_sdg_handout(n, icon, en, zh, group_en, group_zh, color, en_sum, zh_sum, prompts))
        quiz_html = build_sdg_quiz(n, icon, en, zh, group_en, group_zh, color, en_sum, zh_sum)
        if quiz_html:
            write(f"resources/sdgs/{n:02d}-{slug}/quiz/index.html", quiz_html)
    # Bilingual Campus pages — all 13 have full content
    write("resources/bilingual-campus/announcements/index.html", build_announcements())
    write("resources/bilingual-campus/morning-assembly/index.html", build_morning_assembly())
    write("resources/bilingual-campus/school-tours/index.html", build_school_tours())
    write("resources/bilingual-campus/english-self-intro/index.html", build_english_self_intro())
    write("resources/bilingual-campus/english-reading-corner/index.html", build_english_reading_corner())
    write("resources/bilingual-campus/amazing-changhua/index.html", build_amazing_changhua())
    write("resources/bilingual-campus/school-news/index.html", build_school_news())
    write("resources/bilingual-campus/intl-sister-school/index.html", build_intl_sister_school())
    write("resources/bilingual-campus/english-practice-corner/index.html", build_english_practice_corner())
    write("resources/bilingual-campus/school-teams-clubs/index.html", build_school_teams_clubs())
    write("resources/bilingual-campus/summer-fun-program/index.html", build_summer_fun_program())
    write("resources/bilingual-campus/one-minute-english/index.html", build_one_minute_english())
    print("Done.")


if __name__ == "__main__":
    main()
