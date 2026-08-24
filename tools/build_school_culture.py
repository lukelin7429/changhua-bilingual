#!/usr/bin/env python3
"""Generate the nine School Culture module pages.

Each page is the month's briefing — the reading that explains the rules — wrapped
in the Hub's chrome. The questions are NOT repeated here: they all live in the
practice bank at /fets/school-culture/practice/, and each page links straight to
its own topic there. One copy of every question, one place to fix a mistake.

Source of truth:
    fets/school-culture/briefings/meta.json   page titles, deks, notices, sources
    fets/school-culture/briefings/NN.html     the briefing body

    python3 tools/build_school_culture.py

Type sizes are absolute px per CLAUDE.md (body 20/23, anything read 17/19 minimum,
breakpoint 720, no rem in this block).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "fets/school-culture/briefings"
sys.path.insert(0, str(ROOT / "tools"))
from asset_version import stamp_html  # noqa: E402

NAV = ('<ul class="hub-nav-list"><li><a class="hub-nav-link" href="/">Home</a></li>'
       '<li><a class="hub-nav-link" href="/schools/">Schools</a></li>'
       '<li><a class="hub-nav-link" href="/fets/" aria-current="page">FETs</a></li>'
       '<li><a class="hub-nav-link" href="/word-of-the-day/">Word of the Day</a></li>'
       '<li><a class="hub-nav-link" href="/resources/">Resources</a></li>'
       '<li><a class="hub-nav-link" href="/partners/">Partners</a></li></ul>')

CSS = """
    .sc-crumbs { max-width:1200px; margin:0 auto; padding:20px 24px 0; font-size:17px; color:var(--hub-ink-faint); }
    .sc-crumbs a { color:var(--hub-primary); text-decoration:none; }
    .sc-crumbs a:hover { text-decoration:underline; }
    @media (min-width:720px){ .sc-crumbs{ font-size:19px } }

    .scm { font-size:20px; line-height:1.68; color:var(--hub-ink); }
    @media (min-width:720px){ .scm{ font-size:23px } }
    .scm .zh { font-family:var(--hub-zh-font); }

    .scm-notice {
      border:1px solid var(--hub-line); border-left:5px solid var(--hub-primary);
      background:#eef5f4; border-radius:12px; padding:20px 22px; max-width:74ch; margin:0 0 44px;
    }
    .scm-notice h2 {
      margin:0 0 10px; font-family:var(--hub-en-font); font-size:15px; font-weight:700;
      letter-spacing:.09em; text-transform:uppercase; color:var(--hub-primary-deep);
    }
    .scm-notice p { margin:0 0 10px; font-size:18px; line-height:1.6; color:var(--hub-ink-soft); }
    .scm-notice p:last-child { margin-bottom:0; }
    @media (min-width:720px){ .scm-notice{ padding:24px 26px } .scm-notice p{ font-size:20px } }

    .scm h3 {
      font-family:var(--hub-serif); font-size:27px; font-weight:700; color:var(--hub-ink);
      margin:44px 0 16px; line-height:1.25; letter-spacing:-.01em;
    }
    @media (min-width:720px){ .scm h3{ font-size:33px } }
    .scm p { margin:0 0 18px; max-width:74ch; }
    .scm .lede { color:var(--hub-ink-soft); }
    .scm b, .scm strong { color:var(--hub-ink); font-weight:700; }
    .scm a { color:var(--hub-primary); font-weight:600; }
    .scm em { font-style:italic; }

    .offices { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; margin:0 0 8px; }
    .office { border:1px solid var(--hub-line); border-radius:14px; background:var(--hub-line-soft); padding:22px; }
    .office .cn { font-family:var(--hub-zh-font); font-size:26px; font-weight:600; color:var(--hub-primary); display:block; }
    .office .en { font-size:14px; font-weight:700; letter-spacing:.09em; text-transform:uppercase;
      color:var(--hub-ink-faint); display:block; margin:6px 0 12px; }
    .office p { font-size:18px; margin:0; color:var(--hub-ink-soft); line-height:1.6; max-width:none; }
    .office .ask { display:block; margin-top:12px; font-size:17px; color:var(--hub-ink-faint); }
    .office .ask b { color:var(--hub-ink-soft); font-weight:600; }
    @media (min-width:720px){ .office p{ font-size:20px } .office .ask{ font-size:19px } }

    .people { list-style:none; padding:0; margin:0 0 8px; display:flex; flex-direction:column; }
    .people li { display:flex; gap:22px; padding:20px 0; border-bottom:1px solid var(--hub-line); flex-wrap:wrap; }
    .people li:last-child { border-bottom:0; }
    .people .who { flex:0 0 260px; font-weight:700; font-size:19px; color:var(--hub-ink); }
    .people .who span { display:block; font-family:var(--hub-zh-font); font-weight:400; color:var(--hub-ink-faint); font-size:17px; margin-top:3px; }
    .people .what { flex:1 1 320px; font-size:19px; color:var(--hub-ink-soft); line-height:1.6; }
    @media (min-width:720px){ .people .who{ font-size:21px } .people .what{ font-size:21px } .people .who span{ font-size:19px } }

    .redline { border:1px solid #e8bdb6; background:#fbe7e4; border-radius:14px; padding:24px; margin:0 0 8px; }
    .redline .tag { font-size:14px; font-weight:700; letter-spacing:.13em; text-transform:uppercase; color:#b8493f; }
    .redline h3 { margin:10px 0 14px; font-size:25px; }
    @media (min-width:720px){ .redline h3{ font-size:29px } .redline{ padding:28px } }
    .redline p { font-size:18px; color:var(--hub-ink-soft); margin:0 0 14px; max-width:none; }
    .redline p:last-child { margin:0; }
    .redline a { color:#b8493f; }
    @media (min-width:720px){ .redline p{ font-size:20px } }

    .tbl-scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; margin:0 0 8px; }
    .scm table { width:100%; border-collapse:collapse; font-size:18px; min-width:560px; }
    @media (min-width:720px){ .scm table{ font-size:20px } }
    .scm th, .scm td { text-align:left; padding:14px 16px; border-bottom:1px solid var(--hub-line); vertical-align:top; }
    .scm th { font-size:15px; letter-spacing:.09em; text-transform:uppercase; color:var(--hub-ink-faint); font-weight:700; }
    .scm td.num { font-variant-numeric:tabular-nums; font-weight:700; color:var(--hub-primary); white-space:nowrap; }
    .scm tr:last-child td { border-bottom:0; }

    .scm-cta {
      display:block; text-decoration:none; color:inherit; margin:52px 0 0; max-width:74ch;
      border:1px solid var(--hub-line); border-left:5px solid var(--hub-primary); border-radius:14px;
      background:#fff; padding:24px 26px; box-shadow:var(--hub-shadow);
      transition:box-shadow .18s ease, transform .18s ease, border-color .18s ease;
    }
    .scm-cta, .scm-cta:hover, .scm-cta * { text-decoration:none; }
    .scm-cta:hover { box-shadow:var(--hub-shadow-hover); transform:translateY(-2px); border-color:var(--hub-primary); }
    .scm-cta:hover .go { text-decoration:underline; text-underline-offset:3px; }
    .scm-cta:focus-visible { outline:2px solid var(--hub-accent); outline-offset:3px; }
    .scm-cta .eb { display:block; font-size:14px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--hub-accent); margin-bottom:8px; }
    .scm-cta h2 { margin:0 0 8px; font-family:var(--hub-serif); font-size:27px; font-weight:700; color:var(--hub-ink); }
    .scm-cta p { margin:0; font-size:18px; line-height:1.6; color:var(--hub-ink-soft); }
    .scm-cta .go { display:inline-block; margin-top:14px; font-size:18px; font-weight:600; color:var(--hub-primary); }
    @media (min-width:720px){ .scm-cta h2{ font-size:31px } .scm-cta p{ font-size:20px } .scm-cta .go{ font-size:20px } }

    .scm-sources { margin-top:56px; padding-top:32px; border-top:1px solid var(--hub-line); }
    .scm-sources h2 { font-size:15px; letter-spacing:.12em; text-transform:uppercase; color:var(--hub-ink-faint); margin:0 0 16px; font-weight:700; }
    .scm-sources ul { margin:0; padding-left:22px; font-size:18px; color:var(--hub-ink-soft); line-height:1.7; }
    .scm-sources li { margin-bottom:9px; }
    @media (min-width:720px){ .scm-sources ul{ font-size:20px } }

    .scm-nav { display:flex; gap:16px; flex-wrap:wrap; margin-top:40px; }
    .scm-nav a {
      font-size:18px; font-weight:600; color:var(--hub-primary); text-decoration:none;
      border:1px solid var(--hub-line); border-radius:999px; padding:12px 24px;
      transition:border-color .15s ease;
    }
    .scm-nav a:hover { border-color:var(--hub-primary); text-decoration:none; }
    @media (min-width:720px){ .scm-nav a{ font-size:20px } }

    .cb-credit { background:#241f1b; color:#cfc6bb; padding:28px 24px; font-size:17px; line-height:1.9; text-align:center; }
    .cb-credit a { color:#e6c179; text-decoration:none; }
    .cb-credit a:hover { text-decoration:underline; }
    .cb-credit div + div { margin-top:2px; }
    @media (min-width:720px){ .cb-credit{ padding:32px 40px; font-size:18px } }
"""

CREDIT = """<div class="cb-credit">
  <div>Site by <a href="https://www.mycultureconnect.org" target="_blank" rel="noopener">My Culture Connect</a> · <a href="https://www.twrses.org" target="_blank" rel="noopener">人師教育協會</a></div>
  <div>Guided by <a href="https://www.cieetrc.chc.edu.tw" target="_blank" rel="noopener">CIEETRC 彰化縣國際教育暨英語教育資源中心</a></div>
  <div><a href="https://changhua-bilingual.org" target="_blank" rel="noopener">Changhua Bilingual Hub 彰化雙語資源網</a></div>
</div>"""


def page(m, briefing, prev_m, next_m):
    n, slug, title = m["n"], m["slug"], m["title"]
    plain = title.replace("&amp;", "&")
    nav = []
    if prev_m:
        nav.append(f'<a href="/fets/school-culture/{prev_m["n"]:02d}-{prev_m["slug"]}/">← Module {prev_m["n"]}</a>')
    nav.append('<a href="/fets/school-culture/">All nine modules</a>')
    if next_m:
        nav.append(f'<a href="/fets/school-culture/{next_m["n"]:02d}-{next_m["slug"]}/">Module {next_m["n"]} →</a>')

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://changhua-bilingual.org/fets/school-culture/{n:02d}-{slug}/">
  <title>Module {n} · {plain} · School Culture · Changhua Bilingual Hub</title>
  <meta name="description" content="{m['dek'][:150]}">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/logo/icon-32.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/assets/logo/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/logo/icon-180.png">
  <meta name="theme-color" content="#1f6e6e">
  <meta property="og:title" content="Module {n} · {plain}">
  <meta property="og:image" content="/assets/logo/icon-512.png">
  <meta property="og:type" content="article">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap">
  <link rel="stylesheet" href="/assets/css/hub.css">
  <style>{CSS}  </style>
</head>
<body>
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
      {NAV}
    </nav>
  </div>
</header>
<main>

<nav class="sc-crumbs" aria-label="Breadcrumb">
  <a href="/fets/">FETs</a> &nbsp;›&nbsp; <a href="/fets/school-culture/">School Culture</a> &nbsp;›&nbsp; Module {n}
</nav>

<section class="hub-curve-hero hub-curve-hero--fets">
  <svg class="hub-curve-hero-bg" viewBox="0 0 1200 600" preserveAspectRatio="none" aria-hidden="true"><path d="M 0,0 L 760,0 C 720,140 800,290 720,420 C 660,520 760,560 700,600 L 0,600 Z"/></svg>
  <div class="hub-curve-hero-inner">
    <div class="hub-curve-hero-block">
      <p class="hub-eyebrow">{m['eyebrow']}</p>
      <h1 class="hub-curve-hero-title">{title}</h1>
      <p class="hub-curve-hero-lede">{m['dek']}</p>
      <p class="hub-curve-hero-lede-zh">{m['dek_zh']}</p>
    </div>
    <aside class="hub-curve-hero-side">
      <p class="hub-curve-hero-pull">Module {n}<br>of nine.</p>
      <p class="hub-curve-hero-pull-zh">{m['read']}</p>
      <p class="hub-curve-hero-attr">Changhua Bilingual Hub</p>
    </aside>
  </div>
</section>

<section class="hub-section scm" style="padding-top:44px">

  <div class="scm-notice">{m['notice']}</div>

{briefing}

  <a class="scm-cta" href="/fets/school-culture/practice/?topic={n}">
    <span class="eb">Now check yourself · 接著練習</span>
    <h2>Module {n}'s questions</h2>
    <p>24 questions on what you have just read, in the practice bank. Answer one at a time and see the correct answer and the reason straight away. No score, no time limit, nothing recorded.</p>
    <span class="go">Practice Module {n} →</span>
  </a>

  <div class="scm-sources">
    <h2>{m.get('sources_heading', 'Sources for this module')}</h2>
    {m['sources']}
  </div>

  <nav class="scm-nav" aria-label="Module navigation">
    {chr(10).join('    ' + x for x in nav)}
  </nav>

</section>

</main>
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
</footer>
{CREDIT}
<script src="/assets/js/hub.js"></script>
</body>
</html>
"""


def main():
    meta = json.loads((SRC / "meta.json").read_text(encoding="utf-8"))
    for i, m in enumerate(meta):
        prev_m = meta[i - 1] if i else None
        next_m = meta[i + 1] if i + 1 < len(meta) else None
        briefing = (SRC / f"{m['n']:02d}.html").read_text(encoding="utf-8")
        out = ROOT / "fets/school-culture" / f"{m['n']:02d}-{m['slug']}" / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(stamp_html(page(m, briefing, prev_m, next_m), ROOT), encoding="utf-8")
        print(f"  wrote {out.relative_to(ROOT)}  ({out.stat().st_size:,} bytes)")
    print(f"\n{len(meta)} module pages")


if __name__ == "__main__":
    main()
