#!/usr/bin/env python3
# Build Mingli "Word of the Day" — Dajuang-style themed unit pages + Lessons section.
# Source of truth: /tmp/wotd_clean.json (parsed from the mingli WOTD YouTube playlist).
import json, re, os, html

ROOT = os.path.expanduser("~/Documents/Claude/repos/changhua-bilingual")
LESSONS = os.path.join(ROOT, "schools/mingli/lessons")
recs = {r['kw'].lower(): r for r in json.load(open("/tmp/wotd_clean.json"))}

# ---- targeted data fixes ----
def fix(kw, **kw2):
    r = recs[kw.lower()]
    r.update(kw2)
recs['ipad']['s'] = [("iPad is an example of a tablet.", "iPad 是平板的一種。"),
                     ("The students are highlighting facts on their iPads.", "學生們用 iPad 在畫重點。")]
recs['pet']['s'][0] = ("The teacher is petting the cat.", "老師正在撫摸小貓。")
recs['professional development']['zh'] = "教師專業進修"

POS = {'n':'n.', 'v':'v.', 'prep':'prep.', 'adv':'adv.', 'adj':'adj.'}

# ---- unit definitions: (slug, emoji, en, zh, desc, grad1, grad2, [keywords]) ----
UNITS = [
 ("unit-1","🌾","Farm, Garden & Scarecrow","食農與稻草人",
  "From rice seedlings to handmade scarecrows — the words of Mingli's eco-farming classroom, where English grows right out of the soil.",
  "#5fbf86","#1a4330",
  ["seedling","okra seedling","taro","vegetable","farm","weed","mow","repot","potted plants","scarecrow","hay","pole","instruction"]),
 ("unit-2","🎨","Arts, Pottery & Crafts","藝術與陶藝手作",
  "Aroma stones, fluid paint, Tianzhong pottery, murals — the vocabulary of making something beautiful with your own hands.",
  "#e3ac3e","#7d5a0a",
  ["aroma stone","paint pouring","artist","balloon","pottery","pottery wheel","sewing machine","mural","bake"]),
 ("unit-3","🎵","Music, Tea & Culture","音樂・茶道・藝文",
  "The ocarina, the Chinese flute, a quiet tea ceremony, a hallway exhibit — the gentle, cultural side of campus English.",
  "#b06d92","#5b3350",
  ["ocarina","Chinese flute","tea ceremony","tea culture","exhibit"]),
 ("unit-4","🏃","Sports Day & PE","運動會與體育",
  "Relay batons, the 100-meter dash, tire-pushing, jump rope — every word you need on a Taiwan school sports day.",
  "#f0894d","#b34a16",
  ["relay race","baton","100 meter dash","dance exercise","dance","tire pushing game","jump rope competition","basketball","catch","rehearsal"]),
 ("unit-5","🎉","Celebrations & Visitors","校慶與訪客",
  "Mingli's 80th anniversary, award ceremonies, guest sign-ins, story-telling volunteers — the people and moments that fill the campus.",
  "#e0b84a","#a8740c",
  ["anniversary","award presentation","sign","check-in","volunteer","security guard","tour","tour bus"]),
 ("unit-6","📚","In the Classroom","教室裡的英文",
  "Blackboard, pencil case, worksheet, reward stamp — the everyday objects and habits of a Mingli classroom.",
  "#3d9b8f","#1c5048",
  ["blackboard","magnet","pencil case","pencil sharpener","worksheet","workbook","stamp","raise your hand","social studies"]),
 ("unit-7","💻","Tech & Numbers","數位與數學",
  "iPads, QR codes, the desktop computer — plus addition, minus and times. The digital and math words of class.",
  "#5b7fb0","#2d4a72",
  ["iPad","tablet","desktop computer","connect","QR code","addition","minus","times"]),
 ("unit-8","🩺","Daily Routines & Health","日常作息與健康",
  "Eye tests, height checks, brushing teeth, the after-lunch nap — staying healthy and following the school-day routine.",
  "#6cbf7a","#2d7a52",
  ["take a nap","line up","brush your teeth","eye test","height","nurse","upstairs/downstairs","observe","professional development","sink"]),
 ("unit-9","🙌","Everyday Action Words","日常動作字",
  "Put, carry, listen, read, pet the school cat — the simple action verbs that show up in every part of the school day.",
  "#b07a4a","#6b4423",
  ["put","carry","listen","read","pet"]),
]

PLAYLIST = "PL01OhMUI2G8V0WBX_Mdo-XKWJ7X-qdEwW"

def esc(s): return html.escape(s, quote=True)

def bold(text, kw):
    base = kw.lower()
    cands = {kw, base, base+'s', base+'es', base+'ing', base+'ed'}
    if base.endswith('e'): cands |= {base[:-1]+'ing', base+'d'}
    if base.endswith('y'): cands |= {base[:-1]+'ies'}
    # first word of multiword too
    cands.add(base.split()[0])
    for c in sorted(cands, key=len, reverse=True):
        m = re.search(r'\b'+re.escape(c)+r'\b', text, re.I)
        if m:
            return esc(text[:m.start()])+'<b>'+esc(text[m.start():m.end()])+'</b>'+esc(text[m.end():])
    return esc(text)

# ---------- per-unit page template ----------
def subnav(active):
    items = [("Home","../../../"),("Principal","../../../principal/"),
             ("English Life","../../../bilingual-campus/"),("Lessons","../../"),
             ("News","../../../news/"),("Festivals","https://changhua-bilingual.org/festivals/?from=mingli")]
    out=[]
    for name,href in items:
        cls=' class="is-active"' if name==active else ''
        out.append(f'      <a href="{href}"{cls}>{name}</a>')
    return "\n".join(out)

UNIT_CSS = """
  :root{
    --g-deep:#1a4330;--g:#2d7a52;--g-light:#52b788;--g-soft:#d8f3dc;
    --gold:#c8922a;--gold-soft:#fdf8e7;--gold-deep:#7d5a0a;
    --earth:#a0522d;--earth-soft:#f5e6d8;
    --ink:#1a2a1e;--ink-soft:#536653;--line:#d4e8d7;
    --shadow:0 14px 38px -16px rgba(26,67,48,.28);--shadow-sm:0 6px 16px -6px rgba(26,67,48,.16);
  }
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
  html{scroll-behavior:smooth;}
  body{background:#fff;color:var(--ink);font-family:'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif;font-size:20px;line-height:1.65;-webkit-font-smoothing:antialiased;}
  @media(min-width:720px){body{font-size:23px;}}
  .wrap{max-width:1080px;margin:0 auto;padding:0 24px;}
  .topbar{background:rgba(255,255,255,.94);border-bottom:1px solid var(--line);padding:12px 0;position:sticky;top:0;z-index:50;backdrop-filter:blur(8px);}
  .topbar-inner{max-width:1080px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;}
  .topbar-name{font-family:'Playfair Display',serif;font-size:17px;font-weight:700;color:var(--g-deep);line-height:1.15;text-decoration:none;}
  .topbar-name small{display:block;font-family:'PingFang TC','Inter',sans-serif;font-size:11.5px;font-weight:500;color:var(--ink-soft);margin-top:1px;}
  .topbar-nav{display:flex;gap:2px;flex-wrap:wrap;justify-content:flex-end;}
  .topbar-nav a{font-size:14.5px;font-weight:500;color:var(--ink-soft);text-decoration:none;padding:7px 11px;border-radius:8px;transition:all .15s;}
  .topbar-nav a:hover,.topbar-nav a.is-active{color:var(--g-deep);background:var(--g-soft);}
  @media(max-width:640px){.topbar-inner{flex-direction:column;align-items:flex-start;gap:6px;}.topbar-nav{gap:1px;}.topbar-nav a{font-size:13.5px;padding:5px 8px;}}
  .uhero{color:#fff;padding:46px 24px 56px;text-align:center;}
  @media(min-width:720px){.uhero{padding:66px 24px 78px;}}
  .uhero__eyebrow{font-family:'Playfair Display',serif;font-size:13px;letter-spacing:5px;text-transform:uppercase;color:rgba(255,255,255,.85);font-weight:700;}
  @media(min-width:720px){.uhero__eyebrow{font-size:15px;}}
  .uhero__emoji{font-size:56px;line-height:1;margin:10px 0 6px;filter:drop-shadow(0 6px 12px rgba(0,0,0,.2));}
  @media(min-width:720px){.uhero__emoji{font-size:72px;}}
  .uhero h1{font-family:'Playfair Display',serif;font-size:36px;font-weight:800;line-height:1.12;text-shadow:0 3px 10px rgba(0,0,0,.25);}
  @media(min-width:720px){.uhero h1{font-size:56px;}}
  .uhero__zh{font-size:19px;color:rgba(255,255,255,.95);margin-top:8px;font-weight:600;letter-spacing:1px;}
  @media(min-width:720px){.uhero__zh{font-size:24px;}}
  .uhero__meta{display:inline-flex;gap:18px;margin-top:20px;padding:10px 22px;background:rgba(255,255,255,.16);border-radius:99px;font-size:15px;font-weight:600;letter-spacing:.5px;}
  @media(min-width:720px){.uhero__meta{font-size:17px;}}
  .unav{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:22px 0 6px;flex-wrap:wrap;}
  .unav a{color:var(--g-deep);text-decoration:none;font-weight:700;font-size:15px;padding:10px 18px;border-radius:10px;border:2px solid var(--line);background:#fff;transition:all .15s;}
  @media(min-width:720px){.unav a{font-size:17px;}}
  .unav a:hover{background:var(--gold-soft);border-color:var(--gold);color:var(--gold-deep);}
  .unav a.center{background:var(--g-deep);color:#fff;border-color:var(--g-deep);}
  .unav a.center:hover{background:var(--gold);border-color:var(--gold);color:#fff;}
  .unav a.disabled{color:var(--ink-soft);background:var(--g-soft);pointer-events:none;border-color:var(--line);opacity:.6;}
  .vocabs{display:grid;grid-template-columns:1fr;gap:30px;margin:34px 0 24px;}
  @media(min-width:880px){.vocabs{grid-template-columns:repeat(2,1fr);gap:34px;}}
  .vc{background:#fff;border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow-sm);overflow:hidden;display:flex;flex-direction:column;border-top:8px solid var(--g);}
  .vc:nth-child(2n){border-top-color:var(--gold);}
  .vc:nth-child(3n){border-top-color:var(--earth);}
  .vc:nth-child(4n){border-top-color:var(--g-light);}
  .vc__head{padding:22px 26px 16px;}
  @media(min-width:720px){.vc__head{padding:28px 30px 18px;}}
  .vc__num{font-family:'Playfair Display',serif;font-size:13px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--gold-deep);}
  .vc__term{font-family:'Playfair Display',serif;font-size:30px;font-weight:800;color:var(--g-deep);line-height:1.15;margin-top:6px;}
  @media(min-width:720px){.vc__term{font-size:40px;}}
  .vc__pos{font-size:.5em;color:var(--gold-deep);font-style:italic;font-weight:600;letter-spacing:.5px;margin-left:6px;}
  .vc__zh{font-size:20px;color:var(--ink);font-weight:600;margin-top:4px;letter-spacing:1px;}
  @media(min-width:720px){.vc__zh{font-size:26px;}}
  .vc__video{position:relative;width:100%;padding-bottom:56.25%;background:#000;}
  .vc__video iframe{position:absolute;inset:0;width:100%;height:100%;border:0;}
  .vc__body{padding:20px 26px 26px;}
  @media(min-width:720px){.vc__body{padding:24px 30px 30px;}}
  .vc__exs{display:flex;flex-direction:column;gap:13px;}
  .vc__ex{background:#f6faf6;border-radius:12px;padding:13px 17px;border-left:4px solid var(--g);}
  .vc__ex:nth-child(2){border-left-color:var(--gold);}
  .vc__ex .en{font-size:18px;color:var(--ink);font-weight:600;line-height:1.5;}
  @media(min-width:720px){.vc__ex .en{font-size:20px;}}
  .vc__ex .en b{color:var(--g);}
  .vc__ex .zh{font-size:15px;color:var(--ink-soft);margin-top:5px;line-height:1.55;}
  @media(min-width:720px){.vc__ex .zh{font-size:17px;}}
  footer{text-align:center;padding:40px 24px;font-size:15px;color:var(--ink-soft);line-height:1.65;border-top:1px solid var(--line);}
  @media(min-width:720px){footer{font-size:17px;}}
  footer .org{font-weight:600;color:var(--g-deep);}
"""

def build_unit(i, u):
    slug,emoji,en,zh,desc,c1,c2,words = u
    nn=f"{i+1:02d}"
    cards=[]
    for j,w in enumerate(words,1):
        r=recs[w.lower()]
        term=esc(r['kw']); pos=POS.get(r['pos'],r['pos']+'.')
        zhw=esc(r['zh'])
        exs=[]
        for en_s,zh_s in r['s']:
            exs.append(f'          <div class="vc__ex">\n'
                       f'            <div class="en">{bold(en_s, r["kw"])}</div>\n'
                       f'            <div class="zh">{esc(zh_s)}</div>\n'
                       f'          </div>')
        exs="\n".join(exs)
        cards.append(f"""    <article class="vc">
      <div class="vc__head">
        <div class="vc__num">Word {j:02d}</div>
        <div class="vc__term">{term} <span class="vc__pos">({pos})</span></div>
        <div class="vc__zh">{zhw}</div>
      </div>
      <div class="vc__video"><iframe src="https://www.youtube-nocookie.com/embed/{r['id']}?rel=0" title="{term} · {zhw}" loading="lazy" allowfullscreen></iframe></div>
      <div class="vc__body">
        <div class="vc__exs">
{exs}
        </div>
      </div>
    </article>""")
    cards="\n\n".join(cards)
    prev=UNITS[i-1] if i>0 else None
    nxt=UNITS[i+1] if i<len(UNITS)-1 else None
    prev_html=f'<a href="../{prev[0]}/">← Unit {i} · {prev[3]}</a>' if prev else '<a class="disabled">← 第一單元</a>'
    nxt_html=f'<a href="../{nxt[0]}/">Unit {i+2} · {nxt[3]} →</a>' if nxt else '<a class="disabled">最後一單元 →</a>'
    nav=f'''    <a href="../../" class="center">↑ All Units · 回 Lessons</a>
    {prev_html}
    {nxt_html}'''
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Word of the Day · Unit {i+1} — {esc(en)} · Mingli Elementary</title>
<meta name="description" content="Mingli Word of the Day Unit {i+1}: {esc(en)} ({esc(zh)}) — {len(words)} bilingual vocabulary videos filmed on the Mingli campus. 明禮國小每日一字 第{i+1}單元{esc(zh)}，{len(words)} 個單字、{len(words)} 部校園實拍影片。">
<link rel="icon" type="image/png" sizes="32x32" href="/schools/mingli/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/schools/mingli/favicon-180.png">
<link rel="shortcut icon" href="/schools/mingli/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{UNIT_CSS}</style>
<script defer src="/analytics.js"></script>
</head>
<body>

<nav class="topbar" role="navigation" aria-label="Site navigation">
  <div class="topbar-inner">
    <a class="topbar-name" href="../../../">Mingli Elementary<small>彰化縣田中鎮明禮國民小學</small></a>
    <div class="topbar-nav">
{subnav("Lessons")}
    </div>
  </div>
</nav>

<header class="uhero" style="background:linear-gradient(135deg,{c1} 0%,{c2} 100%);">
  <div class="uhero__eyebrow">Word of the Day · Unit {nn}</div>
  <div class="uhero__emoji">{emoji}</div>
  <h1>{esc(en)}</h1>
  <div class="uhero__zh">{esc(zh)}</div>
  <div class="uhero__meta">📺 {len(words)} videos · {len(words)} 個單字影片</div>
</header>

<div class="wrap">
  <nav class="unav">
{nav}
  </nav>

  <div class="vocabs">

{cards}

  </div>

  <nav class="unav">
{nav}
  </nav>
</div>

<footer>
  © 彰化縣田中鎮明禮國民小學 · Mingli Elementary School &nbsp;·&nbsp;
  Word of the Day series by <span class="org">My Culture Connect 人師教育協會</span> &nbsp;·&nbsp;
  Part of the <a href="https://changhua.mycultureconnect.org/" target="_blank" rel="noopener" style="color:var(--g-deep);">Changhua Bilingual Hub</a>
</footer>

</body>
</html>"""

# ---------- write unit pages ----------
for i,u in enumerate(UNITS):
    d=os.path.join(LESSONS,"word",u[0])
    os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(build_unit(i,u))
    print("wrote",u[0],f"({len(u[7])} words)")

# ---------- Lessons WOTD section snippet ----------
cards=[]
for i,u in enumerate(UNITS):
    slug,emoji,en,zh,desc,c1,c2,words=u
    cards.append(f"""      <a class="wcard" href="word/{slug}/">
        <div class="wcard__hero" style="background:linear-gradient(135deg,{c1} 0%,{c2} 100%);"><span class="wcard__emoji">{emoji}</span></div>
        <div class="wcard__body">
          <div class="wcard__no">Unit {i+1:02d} · {len(words)} words</div>
          <div class="wcard__title">{esc(en)}</div>
          <div class="wcard__zh">{esc(zh)}</div>
          <div class="wcard__desc">{esc(desc)}</div>
          <div class="wcard__cta">Start Unit {i+1} <span class="arrow">→</span></div>
        </div>
      </a>""")
cards="\n\n".join(cards)
total=sum(len(u[7]) for u in UNITS)
section=f"""<!-- ===== III. Word of the Day ===== -->
<section>
  <div class="wrap">
    <div class="sec__no">III.</div>
    <h2 class="sec__title">Word of the Day</h2>
    <div class="sec__title-zh">每日一字 · {len(UNITS)} 個主題單元、{total} 個校園單字</div>
    <div class="sec__rule"></div>

    <div class="sec__lead">
      {total} short bilingual vocabulary videos, filmed right here on the Mingli campus and sorted into {len(UNITS)} themes — from eco-farming and pottery to sports day and the daily classroom. Pick a theme, press play, and learn the word in a real Mingli moment.
      <div class="sec__lead-zh">{total} 段在明禮校園實地拍攝的雙語單字短片，依主題分成 {len(UNITS)} 個單元——從食農、陶藝到運動會與教室日常。挑一個主題、按下播放，在真實的明禮場景裡學會這個字。</div>
    </div>

    <div class="wgrid">

{cards}

    </div>

    <div class="wplaylist">
      <h3>Watch the full playlist on YouTube</h3>
      <div class="wplaylist__zh">不想分單元的話，這裡是完整的明禮每日一字 YouTube 播放清單</div>
      <div class="wplaylist__frame">
        <iframe src="https://www.youtube-nocookie.com/embed/videoseries?list={PLAYLIST}&rel=0" title="Mingli Word of the Day · full playlist" loading="lazy" allowfullscreen></iframe>
      </div>
    </div>
  </div>
</section>"""
open("/tmp/mingli_wotd_section.html","w",encoding="utf-8").write(section)
print("\nwrote section snippet; total words:",total,"units:",len(UNITS))
