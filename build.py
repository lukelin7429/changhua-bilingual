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
      Changhua Bilingual Hub
      <small>彰化雙語資源網</small>
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
      <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect (MCC)<br>彰化縣人師教育協會</a>
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
  <link rel="icon" href="/favicon.ico">
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
def build_home(townships_data, schools_data, wotd_items):
    townships = townships_data["townships"]
    schools = schools_data["schools"]
    idx = build_township_index(townships, schools)
    inline_idx = json.dumps(idx, ensure_ascii=False)

    total_schools = len(schools)
    townships_with_schools = sum(1 for t in idx.values() if t["school_count"])
    total_videos = len(wotd_items)
    contributing_schools = len({r["sch"] for r in wotd_items if r["sch"]})

    content = f"""
<section class="hub-hero">
  <div class="hub-hero-text">
    <p class="hub-eyebrow">Welcome / 歡迎</p>
    <h1 class="hub-h1">A bilingual gateway to <em style="color:var(--hub-primary)">Changhua</em>'s schools.</h1>
    <p>{total_schools} bilingual school sites, foreign English teacher profiles, and a growing library of classroom resources — all in one place.</p>
    <p class="hub-zh">彰化縣 {townships_with_schools} 個鄉鎮、{total_schools} 所合作學校的雙語網站、外籍英語教師介紹，以及共用教材，集中一站。</p>
    <div class="hub-hero-actions">
      <a class="hub-btn hub-btn--primary" href="/word-of-the-day/">Watch {total_videos:,} videos →</a>
      <a class="hub-btn hub-btn--ghost" href="/schools/">Browse Schools</a>
    </div>
  </div>
  <div class="hub-map-wrap">
    <div id="hub-map" data-geo="/assets/map/changhua-townships.geojson"></div>
  </div>
</section>

<section class="hub-section">
  <p class="hub-eyebrow">What's inside</p>
  <h2 class="hub-h2">Explore the Hub</h2>
  <div class="hub-feature-grid" style="margin-top:32px">
    <a class="hub-card hub-card--featured" href="/word-of-the-day/">
      <span class="hub-card-tag">Signature</span>
      <h3>Word of the Day 校園百科</h3>
      <p>Our flagship classroom-video library — every word taught in a real Changhua classroom, in two example sentences, by a real teacher.</p>
      <div class="hub-card-meta">{total_videos:,} videos · {contributing_schools} schools</div>
    </a>
    <a class="hub-card" href="/schools/">
      <h3>Schools 學校</h3>
      <p>Bilingual websites for every partner school in Changhua, grouped by township.</p>
      <div class="hub-card-meta">{total_schools} schools · {townships_with_schools} townships</div>
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
    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Directory</p>
  <h1 class="hub-h1">Bilingual School Sites</h1>
  <p style="font-size:1.05rem;color:var(--hub-ink-soft);max-width:60ch">
    {total} schools across {townships_with} townships in Changhua. Each card opens that school's own bilingual website.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:60ch">
    彰化縣 {townships_with} 個鄉鎮、{total} 所合作學校的雙語網站索引。點擊卡片開啟該校網站。
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

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Foreign English Teachers</p>
  <h1 class="hub-h1">Meet our FETs</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:60ch">
    {total} Foreign English Teachers placed across Changhua's partner schools — bringing classrooms a global voice.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:60ch">
    服務於彰化縣各合作學校的 {total} 位外籍英語教師——把世界帶進教室。
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

    content = f"""
<section class="wotd-hero">
  <div class="wotd-hero-inner">
    <p class="hub-eyebrow">Our signature collection</p>
    <h1 class="hub-h1">Word of the Day</h1>
    <p class="wotd-hero-sub">{len(items):,} bilingual classroom videos · {len(school_counts)} schools · every word lived in a real Changhua classroom.</p>
    <p class="hub-zh wotd-hero-sub">{len(items):,} 支雙語教室實拍影片，來自 {len(school_counts)} 所學校。每個單字都是真實課堂的活紀錄。</p>
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


def build_resources():
    content = """
<section class="hub-section">
  <p class="hub-eyebrow">Resources</p>
  <h1 class="hub-h1">Bilingual Resources</h1>
  <p style="font-size:1.08rem;color:var(--hub-ink-soft);max-width:62ch">
    Background, classroom material, and partner programs that surround Changhua's bilingual schools — for teachers, parents, and visitors.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch">
    彰化雙語校園背後的脈絡、共用教材與夥伴計畫——給老師、家長與訪客的入門資源。
  </p>

  <div class="hub-feature-grid" style="margin-top:48px">
    <a class="hub-card hub-card--featured" href="/resources/about-changhua/">
      <span class="hub-card-tag">Start here</span>
      <h3>About Changhua 認識彰化</h3>
      <p>1,074 km² · 1.2 million people · founded 1723 — Taiwan's name-sake of education. Geography, history, and the bilingual ecosystem at a glance.</p>
      <div class="hub-card-meta">Geography · History · Education</div>
    </a>
    <a class="hub-card" href="/resources/study-tour-centers/">
      <h3>Study Tour Centers 遊學中心</h3>
      <p>15 cross-county study tour destinations integrating local culture with experiential learning.</p>
      <div class="hub-card-meta">15 centers</div>
    </a>
    <a class="hub-card" href="/resources/classroom-english/">
      <h3>Classroom English 教室英語</h3>
      <p>10 everyday classroom situations with ready-to-use English phrases — greetings, instructions, feedback, wrap-up.</p>
      <div class="hub-card-meta">10 situations</div>
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
    <a class="hub-card" href="/word-of-the-day/">
      <h3>Word of the Day 校園百科</h3>
      <p>Our signature classroom-video library — 2,966 words taught in real Changhua classrooms.</p>
      <div class="hub-card-meta">2,966 videos · 150 schools</div>
    </a>
    <a class="hub-card" href="/festivals/">
      <h3>Festivals 節慶教材</h3>
      <p>Eight festival units shared across every partner school — Mother's Day, Mid-Autumn, Christmas, and more.</p>
      <div class="hub-card-meta">8 festivals · cross-campus</div>
    </a>
  </div>

  <h2 class="hub-h2" style="margin-top:80px">Partner Networks 夥伴網絡</h2>
  <div class="hub-feature-grid" style="margin-top:24px">
    <a class="hub-card" href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">
      <h3>CIEETRC</h3>
      <p>彰化縣國際教育暨英語教育資源中心 — Changhua's International &amp; English Education Resource Center.</p>
      <div class="hub-card-meta">Official site</div>
    </a>
    <a class="hub-card" href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">
      <h3>My Culture Connect</h3>
      <p>人師教育協會 — Non-profit that has placed 4,000+ foreign English teachers since 2002.</p>
      <div class="hub-card-meta">MCC · since 2002</div>
    </a>
    <a class="hub-card" href="https://education.chcg.gov.tw/" target="_blank" rel="noopener">
      <h3>彰化縣政府教育處</h3>
      <p>Department of Education, Changhua County Government — policy, supervision, and bilingual program funding.</p>
      <div class="hub-card-meta">Government</div>
    </a>
  </div>
</section>
""".strip()
    return page_shell("Resources", content, "/resources/")


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
    Ten everyday classroom situations with ready-to-use English phrases. Teachers can speak naturally; students hear the language used in context.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:62ch">
    十個教室日常情境的實用英文短句。老師可以自然開口，學生在情境中聽到語言的真實用法。
  </p>

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
    print("Done.")


if __name__ == "__main__":
    main()
