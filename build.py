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
from pathlib import Path

import yaml

YT_ID_RX = re.compile(r"(?:v=|/shorts/|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})")

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
      <a href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">CIEETRC<br>彰化縣國際教育暨英語教育資源中心</a>
      <a href="https://www.twrses.org/" target="_blank" rel="noopener">人師教育協會（中文）<br>twrses.org</a>
      <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect (English)<br>mycultureconnect.org</a>
    </div>
    <div>
      <h4>Contact</h4>
      <a href="mailto:luke@mycultureconnect.org">luke@mycultureconnect.org</a>
      <a href="https://github.com/lukelin7429/changhua-bilingual" target="_blank" rel="noopener">View source on GitHub</a>
    </div>
  </div>
  <p class="hub-footer-credit">
    Source imagery and content credit: CIEETRC and MCC.
    Map data via <a href="https://github.com/ronnywang/twgeojson" target="_blank" rel="noopener">ronnywang/twgeojson</a>.
  </p>
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
    videos_rounded = f"{round_down(total_videos, 100):,}+"  # 2966 → 2,900+
    contributing_schools = len({r["sch"] for r in wotd_items if r["sch"]})
    contributing_rounded = f"{round_down(contributing_schools, 10)}+"

    content = f"""
<div class="hub-hero-wrap">
<section class="hub-hero">
  <div class="hub-hero-text">
    <p class="hub-eyebrow">Welcome / 歡迎</p>
    <h1 class="hub-h1">A bilingual gateway to <em style="color:var(--hub-primary)">Changhua</em>'s schools.</h1>
    <p>{schools_rounded} partner school sites, foreign English teacher profiles, and a growing library of classroom resources — all in one place.</p>
    <p class="hub-zh">{townships_rounded} 鄉鎮、{schools_rounded} 合作學校的雙語網站、外籍英語教師介紹，以及共用教材，集中一站。</p>
    <div class="hub-hero-actions">
      <a class="hub-btn hub-btn--primary" href="/word-of-the-day/">Watch {videos_rounded} videos →</a>
      <a class="hub-btn hub-btn--ghost" href="/schools/">Browse Schools</a>
    </div>
  </div>
  <div class="hub-map-wrap">
    <div id="hub-map" data-geo="/assets/map/changhua-townships.geojson"></div>
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
      <p>Bilingual websites for every partner school in Changhua, grouped by township.</p>
      <div class="hub-card-meta">{schools_rounded} schools · {townships_rounded} townships</div>
    </a>
    <a class="hub-card" href="/fets/">
      <h3>FETs 外籍教師</h3>
      <p>Meet the Foreign English Teachers placed across our partner schools.</p>
      <div class="hub-card-meta">Roster · Photos · Profiles</div>
    </a>
    <a class="hub-card" href="/resources/">
      <h3>Resources 教學資源</h3>
      <p>EduResources, Charming Changhua, Study Tour Centers, and cross-campus shared content.</p>
      <div class="hub-card-meta">Classroom-ready</div>
    </a>
    <a class="hub-card" href="/festivals/">
      <h3>Festivals 節慶教材</h3>
      <p>Eight festivals · one shared playbook. Embed the same units on every school's site.</p>
      <div class="hub-card-meta">8 festivals · cross-campus</div>
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
    Changhua's bilingual program runs on a tri-partite partnership — government policy, expert resources, and a non-profit that has brought 4,000+ foreign English teachers to the county since 2002.
  </p>
  <div class="hub-feature-grid">
    <a class="hub-card" href="https://education.chcg.gov.tw/" target="_blank" rel="noopener">
      <h3>彰化縣政府教育處</h3>
      <p>Sets policy &amp; funds the program through 學務管理及課程發展科 (Student Affairs &amp; Curriculum Development), including 精進教學計畫 and 教學卓越獎.</p>
      <div class="hub-card-meta">Department of Education</div>
    </a>
    <a class="hub-card" href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">
      <h3>CIEETRC</h3>
      <p>彰化縣國際教育暨英語教育資源中心 — produces shared resources, runs the SIEP testing program, co-publishes this Hub.</p>
      <div class="hub-card-meta">Resource center</div>
    </a>
    <div class="hub-card">
      <h3>人師教育協會 · My Culture Connect</h3>
      <p>Non-profit founded 2002. Recruits and places foreign English teachers; has connected 4,000+ teachers to Changhua classrooms.</p>
      <div class="hub-card-meta" style="margin-top:12px">Since 2002 · 4,000+ teachers</div>
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
    townships = townships_data["townships"]
    schools = schools_data["schools"]
    by_township = {}
    for s in schools:
        by_township.setdefault(s["township"], []).append(s)

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
                photo_html = f'<img class="photo" src="/assets/images/schools/{slug}.jpg" alt="{s["name"]}" loading="lazy">'
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
    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Directory</p>
  <h1 class="hub-h1">Bilingual School Sites</h1>
  <p style="font-size:1.05rem;color:var(--hub-ink-soft);max-width:60ch">
    {schools_r} partner schools across {townships_r} townships in Changhua. Each card opens that school's own bilingual website.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:60ch">
    彰化縣 {townships_r} 鄉鎮、{schools_r} 合作學校的雙語網站索引。點擊卡片開啟該校網站。
  </p>
  <div class="hub-search" style="margin-top:36px;max-width:560px">
    <input id="hub-search-input" type="search" placeholder="Search by school name, township, or slug…" autocomplete="off">
  </div>
  {''.join(blocks)}
</section>
""".strip()
    return page_shell("Schools", content, "/schools/")


def build_fets(fets_data, schools_data):
    fets = fets_data["fets"]

    def card(fet):
        name = fet.get("name", "")
        school_en = fet.get("school", "")
        school_zh = fet.get("school_zh", "")
        photo = fet.get("photo", "")
        site = fet.get("site", "")

        if photo:
            img_html = (
                f'<img src="/assets/images/fets/{photo}" alt="{name}" loading="lazy" '
                f'class="fet-photo">'
            )
        else:
            initials = "".join(w[0] for w in name.split()[:2]).upper()
            img_html = f'<div class="fet-photo fet-initials" aria-hidden="true">{initials}</div>'

        if site:
            wrap_open = f'<a class="fet-card" href="{site}" target="_blank" rel="noopener">'
            wrap_close = "</a>"
        else:
            wrap_open = '<div class="fet-card">'
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
    total = len(fets)
    total_r = f"{round_down(total, 10)}+"

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Foreign English Teachers</p>
  <h1 class="hub-h1">Meet our FETs</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:60ch">
    {total_r} Foreign English Teachers placed across Changhua's partner schools — bringing classrooms a global voice.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:60ch">
    服務於彰化縣各合作學校的 {total_r} 位外籍英語教師——把世界帶進教室。
  </p>

  <h2 class="hub-h2" style="margin-top:56px">Elementary &amp; Junior High <span style="font-family:var(--hub-zh-font);font-size:.7em;color:var(--hub-ink-faint);font-weight:400">國中小</span></h2>
  <div class="fet-grid" style="margin-top:24px">
    {''.join(elem_jh)}
  </div>

  <h2 class="hub-h2" style="margin-top:72px">Senior High <span style="font-family:var(--hub-zh-font);font-size:.7em;color:var(--hub-ink-faint);font-weight:400">高中</span></h2>
  <div class="fet-grid" style="margin-top:24px">
    {''.join(senior)}
  </div>
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
                "sch": (r.get("school") or "").strip(),
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
    top_schools = sorted(school_counts.items(), key=lambda x: -x[1])[:20]

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
        f'<button class="wotd-az-chip" data-letter="{L}">{L}<span class="ct">{letter_counts[L]}</span></button>'
        for L in letters
    )

    items_r = f"{round_down(len(items), 100):,}+"
    schools_r = f"{round_down(len(school_counts), 10)}+"
    content = f"""
<section class="wotd-hero">
  <div class="wotd-hero-inner">
    <p class="hub-eyebrow">Our signature collection</p>
    <h1 class="hub-h1">Word of the Day</h1>
    <p class="wotd-hero-sub">{items_r} bilingual classroom videos · {schools_r} schools · every word lived in a real Changhua classroom.</p>
    <p class="hub-zh wotd-hero-sub">{items_r} 支雙語教室實拍影片，來自 {schools_r} 所學校。每個單字都是真實課堂的活紀錄。</p>
  </div>
</section>

<section class="wotd-toolbar-wrap">
  <div class="wotd-toolbar">
    <div class="hub-search wotd-search">
      <input id="wotd-q" type="search" placeholder="🔎 Search English, 中文, or school name…" autocomplete="off" />
    </div>
    <select id="wotd-school" aria-label="Filter by school">
      <option value="">All schools · 全部 {len(school_counts)} 校</option>
      {''.join(f'<option value="{sch}">{sch} ({c})</option>' for sch, c in sorted(school_counts.items(), key=lambda x: -x[1]))}
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

<aside class="hub-section wotd-credits">
  <h2 class="hub-h2">Top contributing schools · 影片貢獻學校</h2>
  <p>Schools that have produced the most Word-of-the-Day videos. Tap a name to filter the gallery.</p>
  <ol class="wotd-top">
    {''.join(f'<li><button class="wotd-top-btn" data-school="{sch}"><strong>{sch}</strong><span>{c} videos</span></button></li>' for sch, c in top_schools)}
  </ol>
</aside>
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

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Resources</p>
  <h1 class="hub-h1">Bilingual Resources</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:62ch">
    Background, classroom material, and partner programs that surround Changhua's bilingual schools — for teachers, parents, and visitors.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch">
    彰化雙語校園背後的脈絡、共用教材與夥伴計畫——給老師、家長與訪客的入門資源。
  </p>
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
    Sixteen festivals — Spring &amp; Fall semester — each with a handout and a quiz, freely usable by every partner school.
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
      <div class="hub-card-meta">2,900+ videos · 150+ schools</div>
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

<!-- ===== Place & Travel ===== -->
<section class="hub-section" style="padding-top:24px">
  <h2 class="resources-h2">Place &amp; Travel <small>場域與遊學</small></h2>
  <div class="hub-feature-grid">
    <a class="hub-card" href="/resources/study-tour-centers/">
      <h3>Study Tour Centers 遊學中心</h3>
      <p>15 cross-county study-tour destinations integrating local culture with experiential learning.</p>
      <div class="hub-card-meta">15 centers</div>
    </a>
  </div>
</section>

<!-- ===== Partner Networks ===== -->
<section class="hub-section" style="padding-top:24px;padding-bottom:64px">
  <h2 class="resources-h2">Partner Networks <small>夥伴網絡</small></h2>
  <div class="hub-feature-grid">
    <a class="hub-card" href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">
      <h3>CIEETRC</h3>
      <p>彰化縣國際教育暨英語教育資源中心 — Changhua's International &amp; English Education Resource Center.</p>
      <div class="hub-card-meta">Official site →</div>
    </a>
    <div class="hub-card">
      <h3>人師教育協會 · My Culture Connect</h3>
      <p>Non-profit that has placed 4,000+ foreign English teachers since 2002. Two sites for two audiences.</p>
      <div class="hub-card-meta" style="margin-top:12px">MCC · since 2002</div>
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
    <a class="hub-card" href="https://education.chcg.gov.tw/" target="_blank" rel="noopener">
      <h3>彰化縣政府教育處</h3>
      <p>Department of Education, Changhua County Government — policy, supervision, and bilingual program funding.</p>
      <div class="hub-card-meta">Government →</div>
    </a>
  </div>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("Resources", content, "/resources/", extra)


def build_bilingual_campus_stub(slug, en, zh, brief):
    content = f"""
<section class="hub-section hub-section--narrow">
  <p class="hub-eyebrow">Resources · Bilingual Campus</p>
  <h1 class="hub-h1">{en}</h1>
  <p style="font-family:var(--hub-zh-font);font-size:1.4rem;color:var(--hub-ink);font-weight:600;letter-spacing:.04em;margin:8px 0 24px">{zh}</p>
  <p style="font-size:1.1rem;color:var(--hub-ink-soft);line-height:1.65;max-width:62ch">{brief}</p>

  <div style="margin-top:48px;padding:24px 28px;background:#fff8ec;border-left:6px solid #f5d997;border-radius:8px;color:#7a5300">
    <p style="margin:0;font-weight:600">📝 Content in development.</p>
    <p style="margin:8px 0 0;font-size:.95rem">This unit is being built out. Check back later for vocabulary lists, sample dialogues, and downloadable handouts.</p>
    <p class="hub-zh" style="margin:6px 0 0;font-size:.92rem;color:#7a5300">本主題仍在開發中。之後會補上單字表、對話範本與可下載講義。</p>
  </div>

  <p style="margin-top:48px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    return page_shell(en, content, "/resources/")


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
    教育在彰化從來不是邊角，而是縣的本名與本心。
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
</section>

<section class="hub-section hub-section--narrow" style="padding-top:24px">
  <h2 class="hub-h2">Geography &amp; landscape <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">地理</span></h2>
  <p>Sitting on Taiwan's west-coast plain, Changhua is <strong>87.69 % plain</strong> with the Bagua Plateau rising on the eastern edge.
  This is Taiwan's lowest county by average elevation — every village reachable within an hour from the county seat.</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">座落於台灣中部西岸，87.69% 為平原，東緣為八卦台地。
  全台海拔最低的縣，從彰化市出發一小時內可達任一鄉鎮。</p>

  <h2 class="hub-h2" style="margin-top:64px">Heritage &amp; culture <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">文化遺產</span></h2>
  <ul class="about-list">
    <li><strong>Bagua Mountain Great Buddha</strong> (八卦山大佛) — 22 m bronze Buddha, the county's iconic landmark.</li>
    <li><strong>Changhua Confucian Temple</strong> (彰化孔廟, 1726) — second-oldest in Taiwan, a five-minute walk from the Department of Education building.</li>
    <li><strong>Lukang Old Street &amp; Longshan Temple</strong> (鹿港老街、龍山寺) — Qing-era trading-port heritage.</li>
    <li><strong>"Taiwan's Rice Basket"</strong> — major rice-producing region, with Xihu Township as the grape capital.</li>
  </ul>

  <h2 class="hub-h2" style="margin-top:64px">Administrative divisions <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">行政區</span></h2>
  <p><strong>26 divisions</strong>: 2 cities (Changhua City &amp; Yuanlin City), 6 urban townships, 18 rural townships.</p>
  <ul class="about-list">
    <li><strong>Cities</strong>: Changhua 彰化 · Yuanlin 員林</li>
    <li><strong>Urban townships</strong>: Hemei 和美 · Lukang 鹿港 · Xihu 溪湖 · Tianzhong 田中 · Beidou 北斗 · Erlin 二林</li>
    <li><strong>Rural townships</strong> (18): Shenkang 伸港, Xianxi 線西, Fuxing 福興, Xiushui 秀水, Huatan 花壇, Fenyuan 芬園, Dacun 大村, Puyan 埔鹽, Puxin 埔心, Yongjing 永靖, Shetou 社頭, Ershui 二水, Tianwei 田尾, Pitou 埤頭, Xizhou 溪州, Zhutang 竹塘, Fangyuan 芳苑, Dacheng 大城.</li>
  </ul>

  <h2 class="hub-h2" style="margin-top:64px">Education ecosystem <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">教育生態</span></h2>
  <p>Changhua's bilingual education runs on a tri-partite partnership:</p>
  <ol class="about-list">
    <li><strong>Department of Education, Changhua County Government</strong> 教育處 — sets policy and funds the program through 學務管理及課程發展科 (Student Affairs &amp; Curriculum Development) under its 精進教學計畫 and 教學卓越獎.</li>
    <li><strong>CIEETRC</strong> 彰化縣國際教育暨英語教育資源中心 — produces resources and runs the SIEP testing program.</li>
    <li><strong>My Culture Connect</strong> 人師教育協會 — recruits and places foreign English teachers; since 2002 has placed over 4,000 teachers.</li>
  </ol>
  <p>The county is home to <strong>3 universities</strong> (National Changhua University of Education, Da Yeh, Jianguo Tech), <strong>12 senior high schools</strong>, and a dense network of junior high and elementary schools — over 100 of which participate in this Hub.</p>

  <h2 class="hub-h2" style="margin-top:64px">Why this Hub exists <span class="hub-zh" style="font-size:.6em;color:var(--hub-ink-faint);font-weight:400">本平台緣起</span></h2>
  <p>The bilingual sites of more than 100 partner schools were scattered across Google Sites, Canva, and dozens of subdomains. This Hub gathers them into one searchable directory, alongside the resources, foreign-teacher profiles, and 2,966+ classroom videos that connect them.</p>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">100 多所合作學校的雙語網站原本散落在 Google Sites、Canva 與數十個子網域。本平台把它們收進同一份可搜尋的索引，並串接共用資源、外師檔案，以及 2,966+ 部課堂影片。</p>
</section>
""".strip()
    extra = '<link rel="stylesheet" href="/assets/css/resources.css">'
    return page_shell("About Changhua", content, "/resources/", extra)


def build_study_tour_centers(schools_data):
    schools_by_slug = {s["slug"]: s for s in schools_data["schools"]}
    centers = [
        # Try to match to schools.yml slug where possible
        ("Changhua Arts High School", "彰化藝術高中", "Changhua City", None),
        ("Chungshan Elementary", "中山國小", "Changhua City", "chungshan"),
        ("Tongan Elementary", "同安國小", "Fenyuan", None),
        ("Wunde Elementary", "文德國小", "Fenyuan", "wunde"),
        ("Tianwei Junior High", "田尾國中", "Tianwei", None),
        ("Beidou Junior High", "北斗國中", "Beidou", "beidou-jh"),
        ("Ershui Junior High", "二水國中", "Ershui", None),
        ("Dajuang Elementary", "大莊國小", "Xizhou", "dajuang"),
        ("Lu Jiang International School", "鹿江國中小", "Lukang", "lujiang"),
        ("Lukang Elementary", "鹿港國小", "Lukang", "lukang"),
        ("Ma Tsuo Elementary", "媽厝國小", "Xihu", "matsuo"),
        ("Fangyuan Elementary", "芳苑國小", "Fangyuan", "fangyuan"),
        ("Guanxing Elementary", "廣興國小", "Erlin", "guangxing"),
        ("Dacheng Elementary", "大城國小", "Dacheng", "dacheng"),
        ("Changhua Fun Study Tour Center", "彰化特色遊學中心", "—", None),
    ]
    cards = []
    for en, zh, township, slug in centers:
        photo_html = ""
        link_html_open = "<div class=\"hub-school-card\">"
        link_html_close = "</div>"
        if slug and slug in schools_by_slug:
            sch = schools_by_slug[slug]
            link_html_open = f'<a class="hub-school-card" href="{sch["url"]}" target="_blank" rel="noopener">'
            link_html_close = "</a>"
            photo_path = ROOT / "assets" / "images" / "schools" / f"{slug}.jpg"
            if photo_path.exists():
                photo_html = f'<img class="photo" src="/assets/images/schools/{slug}.jpg" alt="{en}" loading="lazy">'
        if not photo_html:
            initials = zh[:2] if zh else en[:2]
            photo_html = f'<div class="photo-fallback" aria-hidden="true">{initials}</div>'
        cards.append(f"""
{link_html_open}
  {photo_html}
  <div class="body">
    <p class="name">{en}</p>
    <p class="zh">{zh}</p>
    <span class="badge">{township}</span>
  </div>
{link_html_close}
""".strip())

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Resources · Study Tour</p>
  <h1 class="hub-h1">Fun Study Tour Centers</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:62ch">
    A network of {len(centers)} cross-county study-tour destinations that integrate local culture with experiential learning. Originally curated by the Changhua County Education Department to promote school-based field trips and career exploration.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch">
    {len(centers)} 個跨縣特色遊學中心，整合在地文化與體驗式學習，由彰化縣政府教育處規劃，推動校本戶外教育與職業探索。
  </p>

  <h2 class="hub-h2" style="margin-top:56px">All centers · 全部中心</h2>
  <div class="hub-school-grid" style="margin-top:24px">
    {''.join(cards)}
  </div>

  <p style="margin-top:48px;color:var(--hub-ink-faint);font-size:.92rem">
    <a href="/resources/">← Back to Resources</a>
  </p>
</section>
""".strip()
    return page_shell("Study Tour Centers", content, "/resources/")


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
        qs_html = ''.join(f'<li>{q}</li>' for q in qs)
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
  <div class="sdg__prompts-wrap">
    <div class="sdg__prompts-label">Try this in class · 課堂試試看</div>
    <ul class="sdg__prompts">{qs_html}</ul>
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
    write("resources/study-tour-centers/index.html", build_study_tour_centers(schools))
    write("resources/classroom-english/index.html", build_classroom_english())
    write("resources/books-for-taiwan/index.html", build_books_for_taiwan())
    write("resources/eric-berman/index.html", build_eric_berman())
    write("resources/sdgs/index.html", build_sdgs())
    # Bilingual Campus pages — Classroom English + Announcements have full content; rest are stubs
    write("resources/bilingual-campus/announcements/index.html", build_announcements())
    for slug, en, zh, brief in BILINGUAL_CAMPUS:
        if slug in ("classroom-english", "announcements"):
            continue
        write(f"resources/bilingual-campus/{slug}/index.html", build_bilingual_campus_stub(slug, en, zh, brief))
    print("Done.")


if __name__ == "__main__":
    main()
