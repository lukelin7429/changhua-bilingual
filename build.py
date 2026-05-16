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
            cards.append(f"""
<a class="hub-school-card" href="{s['url']}" target="_blank" rel="noopener" data-search="{search_data}">
  <p class="name">{s['name']}</p>
  <p class="zh">{s.get('zh','')}</p>
  <span class="badge {badge_cls}">{badge_text}</span>
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


def load_wotd():
    rows = []
    with open(ROOT / "data" / "wotd.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            yt = (r.get("youtube") or "").strip()
            m = YT_ID_RX.search(yt)
            if not m:
                continue
            rows.append({
                "k": r["keyword"].strip(),
                "kz": (r.get("keyword_zh") or "").strip(),
                "s1": r["sentence_1"].strip(),
                "s1z": r["sentence_1_zh"].strip(),
                "s2": r["sentence_2"].strip(),
                "s2z": r["sentence_2_zh"].strip(),
                "sch": (r.get("school") or "").strip(),
                "v": m.group(1),
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
    for r in items:
        school_counts[r["sch"]] = school_counts.get(r["sch"], 0) + 1
    top_schools = sorted(school_counts.items(), key=lambda x: -x[1])[:20]

    # Write data file for client
    data_path = ROOT / "assets" / "data" / "wotd.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "items": items,
        "schools": sorted(school_counts.items(), key=lambda x: -x[1]),
        "generated_at": "build-time",
    }
    data_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  wrote /assets/data/wotd.json  ({data_path.stat().st_size:,} bytes, {len(items)} items)")

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
      <input id="wotd-q" type="search" placeholder="Search a word, a Chinese gloss, or a school…" autocomplete="off" />
    </div>
    <select id="wotd-school" aria-label="Filter by school">
      <option value="">All schools · 全部 {len(school_counts)} 校</option>
      {''.join(f'<option value="{sch}">{sch} ({c})</option>' for sch, c in sorted(school_counts.items(), key=lambda x: -x[1]))}
    </select>
    <div id="wotd-count" class="wotd-count">{len(items):,} videos</div>
  </div>
</section>

<section class="hub-section wotd-section">
  <div id="wotd-grid" class="wotd-grid" aria-live="polite"></div>
  <div id="wotd-loadmore-wrap" style="text-align:center;margin-top:40px;display:none">
    <button id="wotd-loadmore" class="hub-btn hub-btn--ghost">Load more →</button>
  </div>
  <div id="wotd-empty" class="wotd-empty" hidden>
    <p>No videos match. Try a different word or pick another school.</p>
  </div>
</section>

<aside class="hub-section wotd-credits">
  <h2 class="hub-h2">Top contributing schools</h2>
  <p>Schools that have produced the most Word-of-the-Day videos. Tap a name to filter the gallery.</p>
  <ol class="wotd-top">
    {''.join(f'<li><button class="wotd-top-btn" data-school="{sch}"><strong>{sch}</strong><span>{c} videos</span></button></li>' for sch, c in top_schools)}
  </ol>
</aside>
""".strip()
    extra_head = '<link rel="stylesheet" href="/assets/css/wotd.css">\n  <script defer src="/assets/js/wotd.js"></script>'
    return page_shell("Word of the Day", content, "/word-of-the-day/", extra_head)


def build_resources():
    # Static content — three groupings.
    bilingual_campus = [
        "School Tours", "Classroom English", "Morning Assembly", "School Teams & Clubs",
        "Announcements", "English Reading Corner", "International Sister School",
        "English Practice Corner", "Amazing Changhua", "School News",
        "Summer Fun Program", "English Self-Introduction", "One Minute English",
    ]
    issues = [
        "SDGs", "Bilingual Education", "International Education", "Agri-Food Education",
        "Environmental Education", "Disaster Risk", "Character Education",
        "Marine Education", "Technology Education",
    ]
    domains = [
        "Arts", "Math", "Social Studies", "Natural Science",
        "Integrative Activities", "Life Curriculum", "Technology Domain",
        "Health & Physical Education",
    ]
    wotd_themes = [
        ("Tasks", "校園百科"), ("Physical Activities", "體育活動"),
        ("Festivals & Celebrations", "節慶慶典"), ("Food & Agriculture", "食物與農業"),
        ("Learning Subjects", "學科"), ("Clubs & Teams", "社團"),
        ("Facilities & Equipment", "設施設備"), ("Cultural & Artistic Activities", "文化藝術"),
        ("Health & Safety", "健康安全"), ("Picture Description", "看圖說話"),
    ]

    def card_grid(items, label_fn):
        cards = []
        for it in items:
            label = label_fn(it)
            cards.append(f'<div class="hub-school-card" style="cursor:default"><p class="name">{label}</p></div>')
        return f'<div class="hub-school-grid">{"".join(cards)}</div>'

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Resources</p>
  <h1 class="hub-h1">Bilingual Resources</h1>
  <p style="font-size:1.05rem;color:var(--hub-ink-soft);max-width:60ch">
    Cross-campus classroom material — Word of the Day, EduResources, plus our Charming Changhua &amp; Study Tour pages.
  </p>

  <div style="margin-top:36px;padding:14px 18px;background:#fff8ec;border:1px solid #f5d997;border-radius:10px;color:#7a5300">
    <strong>Migration in progress.</strong> Resource content is being moved over from the legacy Google Sites hub. The categories below are placeholders; click-throughs land next.
  </div>

  <h2 class="hub-h2" style="margin-top:56px">Word of the Day · 校園百科</h2>
  <p class="hub-zh" style="color:var(--hub-ink-soft)">10 themes, A–Z index, classroom-ready.</p>
  {card_grid(wotd_themes, lambda t: f'<span>{t[0]}</span><br><span class="zh" style="color:var(--hub-ink-soft);font-size:.85em">{t[1]}</span>')}

  <h2 class="hub-h2" style="margin-top:64px">Bilingual Campus · 雙語生活化校園</h2>
  {card_grid(bilingual_campus, lambda t: t)}

  <h2 class="hub-h2" style="margin-top:64px">Issues · 議題</h2>
  {card_grid(issues, lambda t: t)}

  <h2 class="hub-h2" style="margin-top:64px">Domains · 領域</h2>
  {card_grid(domains, lambda t: t)}

  <h2 class="hub-h2" style="margin-top:64px">Charming Changhua &amp; Study Tour</h2>
  <p style="color:var(--hub-ink-soft)">15 study-tour centers across Changhua, plus the Charming Changhua introduction. Both pages are being rebuilt.</p>
</section>
""".strip()
    return page_shell("Resources", content, "/resources/")


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
    print("Done.")


if __name__ == "__main__":
    main()
