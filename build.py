#!/usr/bin/env python3
"""Build script for the Changhua Bilingual Hub.

Reads YAML in data/, regenerates:
  /index.html
  /schools/index.html
  /fets/index.html
  /resources/index.html

Workflow: edit YAML → run `python3 build.py` → git commit & push.
"""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent

SECTIONS = [
    ("/", "Home"),
    ("/schools/", "Schools"),
    ("/fets/", "FETs"),
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
def build_home(townships_data, schools_data):
    townships = townships_data["townships"]
    schools = schools_data["schools"]
    idx = build_township_index(townships, schools)
    inline_idx = json.dumps(idx, ensure_ascii=False)

    total_schools = len(schools)
    townships_with_schools = sum(1 for t in idx.values() if t["school_count"])

    content = f"""
<section class="hub-hero">
  <div class="hub-hero-text">
    <p class="hub-eyebrow">Welcome / 歡迎</p>
    <h1 class="hub-h1">A bilingual gateway to <em style="color:var(--hub-primary)">Changhua</em>'s schools.</h1>
    <p>{total_schools} bilingual school sites, foreign English teacher profiles, and a growing library of classroom resources — all in one place.</p>
    <p class="hub-zh">彰化縣 {townships_with_schools} 個鄉鎮、{total_schools} 所合作學校的雙語網站、外籍英語教師介紹，以及共用教材，集中一站。</p>
    <div class="hub-hero-actions">
      <a class="hub-btn hub-btn--primary" href="/schools/">Browse Schools →</a>
      <a class="hub-btn hub-btn--ghost" href="/fets/">Meet the FETs</a>
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
    <a class="hub-card" href="/schools/">
      <h3>Schools 學校</h3>
      <p>Bilingual websites for every partner school in Changhua, grouped by township. Click through to each campus's own site.</p>
      <div class="hub-card-meta">{total_schools} schools · {townships_with_schools} townships</div>
    </a>
    <a class="hub-card" href="/fets/">
      <h3>FETs 外籍教師</h3>
      <p>Meet the Foreign English Teachers placed across our partner schools — elementary, junior high, and senior high.</p>
      <div class="hub-card-meta">Roster · Photos · Profiles</div>
    </a>
    <a class="hub-card" href="/resources/">
      <h3>Resources 教學資源</h3>
      <p>Word of the Day, EduResources, Charming Changhua, Study Tour Centers, and cross-campus shared content.</p>
      <div class="hub-card-meta">Classroom-ready</div>
    </a>
    <a class="hub-card" href="/festivals/">
      <h3>Festivals 節慶教材</h3>
      <p>Eight festivals · one shared playbook. Embed the same units on every school's site with a single line.</p>
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
    schools_by_slug = {s["slug"]: s for s in schools_data["schools"]}

    def card(fet):
        school_field = fet.get("school", "")
        if school_field in schools_by_slug:
            sch = schools_by_slug[school_field]
            school_display = f'{sch["name"]} <span class="zh" style="color:var(--hub-ink-faint);font-size:.85em">· {sch.get("zh","")}</span>'
        else:
            school_display = school_field
        photo = fet.get("photo", "")
        if photo:
            img_html = f'<img src="/assets/images/fets/{photo}" alt="{fet["name"]}" loading="lazy" style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:50%;background:var(--hub-line-soft)">'
        else:
            initials = "".join(w[0] for w in fet["name"].split()[:2]).upper()
            img_html = f'<div aria-hidden="true" style="width:100%;aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;background:var(--hub-line-soft);border-radius:50%;font-family:var(--hub-serif);font-size:1.8rem;color:var(--hub-primary)">{initials}</div>'
        site = fet.get("site", "")
        wrap_open = f'<a href="{site}" target="_blank" rel="noopener" class="hub-school-card" style="text-align:center">' if site else '<div class="hub-school-card" style="text-align:center">'
        wrap_close = "</a>" if site else "</div>"
        return f"""
{wrap_open}
  <div style="padding:0 16px 12px">{img_html}</div>
  <p class="name">{fet["name"]}</p>
  <p class="zh">{school_display}</p>
{wrap_close}
""".strip()

    elem = [card(f) for f in fets if f.get("segment") != "senior-high"]
    senior = [card(f) for f in fets if f.get("segment") == "senior-high"]

    content = f"""
<section class="hub-section">
  <p class="hub-eyebrow">Foreign English Teachers</p>
  <h1 class="hub-h1">Meet our FETs</h1>
  <p style="font-size:1.05rem;color:var(--hub-ink-soft);max-width:60ch">
    Foreign English Teachers placed across Changhua's partner schools — bringing classrooms a global voice.
  </p>
  <p class="hub-zh" style="color:var(--hub-ink-soft);max-width:60ch">
    服務於彰化縣各合作學校的外籍英語教師——把世界帶進教室。
  </p>

  <div style="margin-top:48px;padding:14px 18px;background:#fff8ec;border:1px solid #f5d997;border-radius:10px;color:#7a5300">
    <strong>Roster being rebuilt.</strong> The full FET list with photos and individual sites is being migrated from the legacy Hub. This page currently shows the structure and a sample.
  </div>

  <h2 class="hub-h2" style="margin-top:56px">Elementary &amp; Junior High</h2>
  <div class="hub-school-grid" style="margin-top:24px">
    {''.join(elem)}
  </div>

  <h2 class="hub-h2" style="margin-top:56px">Senior High</h2>
  <div class="hub-school-grid" style="margin-top:24px">
    {''.join(senior)}
  </div>
</section>
""".strip()
    return page_shell("FETs", content, "/fets/")


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
    print(f"Loaded: {len(townships['townships'])} townships, {len(schools['schools'])} schools, {len(fets['fets'])} fets")
    write("index.html", build_home(townships, schools))
    write("schools/index.html", build_schools(townships, schools))
    write("fets/index.html", build_fets(fets, schools))
    write("resources/index.html", build_resources())
    print("Done.")


if __name__ == "__main__":
    main()
