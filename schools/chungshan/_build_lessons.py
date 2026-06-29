#!/usr/bin/env python3
# Generates Chungshan Lessons hub + Word-of-the-Day unit sub-pages from the
# parsed playlist (/tmp/chungshan_wotd.json). Re-run after editing categories.
import json, os, html, re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(ROOT, 'wotd_data.json')))
by_id = {d['id']: d for d in DATA}

# shot put had no example sentences in its description — supply two.
if 'IPxP-JuvB4Q' in by_id:
    sp = by_id['IPxP-JuvB4Q']
    sp['en'] = sp['en'] or 'shot put'
    sp['zh'] = sp['zh'] or '推鉛球'
    if not sp['exs']:
        sp['exs'] = [
            {'en': 'In the <b>shot put</b>, athletes push a heavy metal ball as far as they can.',
             'zh': '推鉛球比賽中，選手要把沉重的鉛球盡量推遠。'},
            {'en': 'She practices the <b>shot put</b> every week for the school sports day.',
             'zh': '她每週練習推鉛球，為校運動會做準備。'},
        ]

# ---- Units (order matters) ----
UNITS = [
    dict(slug='school-life', emoji='🏫', en='School Life & Routines', zh='校園日常的英文',
         g1='#5a5fa6', g2='#2e3270',
         desc='From washing hands to checking out library books — the words behind an ordinary day on the Chungshan campus.'),
    dict(slug='arts', emoji='🎵', en='Arts & Performance', zh='藝術與舞台',
         g1='#c79a3e', g2='#8a5f17',
         desc="Chinese orchestra, ocarinas, the school band, singing contests — Chungshan's stage, in English."),
    dict(slug='sports', emoji='🏃', en='Sports Day & PE', zh='運動場上的英文',
         g1='#c8593f', g2='#8f2f1c',
         desc='Swimming, relay races, the shot put, tee-ball — every word comes from a real moment in PE or on sports day.'),
    dict(slug='science', emoji='🔬', en='Science & Discovery', zh='科學探索',
         g1='#2f8f8a', g2='#155f5c',
         desc='Electromagnets, fossils, friction, the spring scale — the language of curiosity and hands-on science.'),
    dict(slug='festivals', emoji='🎉', en='Festivals & Special Days', zh='節慶與校園活動',
         g1='#b1568a', g2='#7a2f5b',
         desc='Christmas, the school anniversary, field trips, Mother’s Day — the celebrations that mark the Chungshan year.'),
]
USLUG = {u['slug']: u for u in UNITS}

# ---- term -> unit assignment (lowercase english) ----
ASSIGN = {
 'school-life': ['wash your hands','check out','sweep','clean','board game','toy','volunteer',
                 'tablet','bubble','playdough','farm','professional development','flag ceremony',
                 'storyteller','pin','fun game'],
 'arts': ['chinese music','ocarina','school band','performer','singing competition',
          'traditional lantern','decoupage','domino','top','portrait','tea','tour guide',
          "rubik's cube"],
 'sports': ['swing','kick','swimming class','swim team','relay race','tee-ball','agility training',
            'arm strength','core strength','softball throw','starting blocks','shot put','endurance',
            'climb','zipline','harness','dodgebee','sports day','enter the field','perform a dance'],
 'science': ['electromagnet','fossil','plant','pot','spring scale','friction','air pressure',
             'science museum','cpr','earthquake drill','catapult','wheel and axle','pulley'],
 'festivals': ['christmas','gingerbread house','christmas celebration','sticky rice ball',
               "mother's day",'pastry','anniversary','school anniversary','award presentation',
               'field trip'],
}
term2unit = {}
for u, terms in ASSIGN.items():
    for t in terms:
        term2unit[t] = u

# bucket each video (keep playlist order)
buckets = {u['slug']: [] for u in UNITS}
unassigned = []
for d in DATA:
    key = d['en'].strip().lower()
    u = term2unit.get(key)
    if u:
        buckets[u].append(d)
    else:
        unassigned.append(d['en'])
if unassigned:
    print('  !! UNASSIGNED:', unassigned)

TB = ('<div class="tb"><div class="tb__inner"><a class="tb__brand" href="/schools/chungshan/">'
      '<img class="tb__logo" src="/schools/chungshan/favicon-192.png" alt="Chungshan crest 中山國小校徽"><div class="tb__name">Chungshan Elementary<small>彰化市中山國小</small></div></a>'
      '<nav class="tb__nav"><a href="/schools/chungshan/">Home</a><a href="/schools/chungshan/principal/">Principal</a>'
      '<a href="/schools/chungshan/lessons/" class="is-active">Lessons</a><a href="/schools/chungshan/news/">News</a><a href="/schools/chungshan/festivals/">Festivals</a></nav>'
      '</div></div>')

FOOT = ('<footer class="ft"><div class="ft__inner"><div class="ft__brand"><img class="ft__logo" src="/schools/chungshan/favicon-192.png" alt="Chungshan crest 中山國小校徽"><div>'
        '<h4>Chungshan Elementary School</h4><div class="zh">彰化縣彰化市中山國民小學</div>'
        '<div class="ft__addr">50042 彰化縣彰化市中山路二段 678 號<br>Tel · 電話：(04) 722-2033</div></div></div>'
        '<div class="ft__col"><h5>This Site</h5><ul><li><a href="/schools/chungshan/">Home · 首頁</a></li>'
        '<li><a href="/schools/chungshan/principal/">Principal · 校長室</a></li>'
        '<li><a href="/schools/chungshan/news/">News · 最新消息</a></li></ul></div>'
        '<div class="ft__col"><h5>Connect</h5><div class="ft-ctas">'
        '<a class="cta-btn" href="https://cses.chc.edu.tw/" target="_blank" rel="noopener"><span class="cta-btn__ico">🌐</span>'
        '<span class="cta-btn__tx"><span class="cta-btn__t">Official Website</span><span class="cta-btn__zh">中山國小官網</span></span>'
        '<span class="cta-btn__arrow">↗</span></a>'
        '<a class="cta-btn" href="https://www.youtube.com/playlist?list=PL01OhMUI2G8WSth0Ydh_MaazCkPOXDSGs" target="_blank" rel="noopener" style="background:#FF0000;">'
        '<span class="cta-btn__ico">▶</span><span class="cta-btn__tx"><span class="cta-btn__t">English Channel</span>'
        '<span class="cta-btn__zh">中山英語影片播放清單</span></span><span class="cta-btn__arrow">↗</span></a></div></div></div>'
        '<div class="ft__bottom">Site by <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect</a> '
        '<a href="https://www.twrses.org/" target="_blank" rel="noopener">人師教育協會</a><br>'
        'Guided by <a href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">CIEETRC 彰化縣國際教育暨英語教育資源中心</a><br>'
        '<a href="https://changhua-bilingual.org/" target="_blank" rel="noopener">Changhua Bilingual Hub 彰化雙語資源網</a></div></footer>')

REVEAL = ("<script>(function(){if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return;"
          "var sel='.lcard,.unit,.vc,.pillar,.quote,.playlist-block,.scard';var els=[].slice.call(document.querySelectorAll(sel));"
          "if(!els.length)return;els.forEach(function(el){el.classList.add('rvl');});"
          "if(!('IntersectionObserver'in window)){els.forEach(function(el){el.classList.add('in');});return;}"
          "var io=new IntersectionObserver(function(en){en.forEach(function(e){if(!e.isIntersecting)return;"
          "var sibs=[].slice.call(e.target.parentNode.children).filter(function(n){return n.classList.contains('rvl');});"
          "e.target.style.transitionDelay=(Math.max(0,sibs.indexOf(e.target))*70)+'ms';e.target.classList.add('in');"
          "setTimeout(function(){e.target.style.transitionDelay='';},800);io.unobserve(e.target);});},"
          "{threshold:0.08,rootMargin:'0px 0px -5% 0px'});els.forEach(function(el){io.observe(el);});})();</script>")

# lessons-page CSS (unit cards) + unit-page CSS (vocab cards), indigo palette
LCSS = """
.units{display:grid;grid-template-columns:1fr;gap:24px;margin-top:8px;}
@media(min-width:720px){.units{grid-template-columns:repeat(2,1fr);gap:30px;}}
@media(min-width:1040px){.units{grid-template-columns:repeat(3,1fr);}}
.unit{background:#fff;border-radius:22px;border:1px solid var(--line);box-shadow:var(--shadow-sm);overflow:hidden;display:flex;flex-direction:column;transition:transform .25s,box-shadow .25s;text-decoration:none;color:inherit;position:relative;}
.unit:hover{transform:translateY(-8px) scale(1.01);box-shadow:0 30px 54px -20px var(--ua,#2e3270);}
.unit__hero{height:150px;display:flex;align-items:center;justify-content:center;font-size:78px;position:relative;overflow:hidden;}
@media(min-width:720px){.unit__hero{height:172px;font-size:96px;}}
.unit__hero::before{content:'';position:absolute;top:-30%;right:-25%;width:150px;height:150px;background:radial-gradient(circle,rgba(255,255,255,.4),transparent 60%);border-radius:50%;}
.unit__hero::after{content:'';position:absolute;bottom:-40%;left:-35%;width:170px;height:170px;background:radial-gradient(circle,rgba(255,255,255,.22),transparent 60%);border-radius:50%;}
.unit__emoji{position:relative;z-index:1;filter:drop-shadow(0 6px 12px rgba(0,0,0,.18));transition:transform .3s;}
.unit:hover .unit__emoji{transform:scale(1.12) rotate(-4deg);}
.unit__body{padding:24px 26px 28px;flex:1;display:flex;flex-direction:column;}
.unit__no{font-family:'Playfair Display',serif;font-size:13px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--gold-deep);}
.unit__title{font-family:'Playfair Display',serif;font-size:26px;font-weight:700;color:var(--green-deep);line-height:1.18;margin-top:6px;}
@media(min-width:720px){.unit__title{font-size:30px;}}
.unit__title-zh{font-size:17px;color:var(--ink);font-weight:600;margin-top:6px;}
.unit__desc{font-size:17px;color:var(--ink-soft);margin-top:14px;line-height:1.6;flex:1;}
.unit__cta{margin-top:20px;padding-top:16px;border-top:1px dashed var(--line);color:var(--gold-deep);font-family:'Playfair Display',serif;font-size:17px;font-weight:700;display:flex;justify-content:space-between;align-items:center;}
.unit__cta .arrow{transition:transform .2s;}.unit:hover .unit__cta .arrow{transform:translateX(5px);}
.unit__count{font-size:13px;color:var(--ink-soft);font-family:'Inter';letter-spacing:.04em;}
.playlist-block{background:linear-gradient(135deg,var(--cream),var(--green-soft));border-radius:22px;padding:30px 22px;border:1px solid var(--line);}
@media(min-width:720px){.playlist-block{padding:46px 40px;}}
.playlist-block h3{font-family:'Playfair Display',serif;font-size:26px;font-weight:700;color:var(--green-deep);text-align:center;}
@media(min-width:720px){.playlist-block h3{font-size:32px;}}
.playlist-block .zh{text-align:center;font-size:17px;color:var(--ink-soft);margin-top:6px;}
.video-frame{margin-top:22px;position:relative;width:100%;padding-bottom:56.25%;background:#000;border-radius:14px;overflow:hidden;box-shadow:var(--shadow);}
.video-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0;}
/* category card cover = a real video thumbnail (prettier than an emoji) */
.unit__hero::before,.unit__hero::after{display:none;}
.unit__thumb{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;transition:transform .4s ease;}
.unit:hover .unit__thumb{transform:scale(1.06);}
.unit__veil{position:absolute;inset:0;z-index:1;background:linear-gradient(to top,rgba(16,14,28,.62),rgba(16,14,28,.06) 55%);}
.unit__emoji{position:absolute;z-index:2;left:14px;bottom:10px;font-size:34px;filter:drop-shadow(0 2px 7px rgba(0,0,0,.55));}
.unit__play{position:absolute;z-index:2;right:14px;bottom:12px;width:46px;height:46px;border-radius:50%;background:rgba(0,0,0,.5);border:1.5px solid rgba(255,255,255,.8);color:#fff;display:flex;align-items:center;justify-content:center;font-size:17px;padding-left:3px;transition:background .25s,transform .25s;}
.unit:hover .unit__play{background:var(--brick);transform:scale(1.08);}
/* poem-tree signature feature card */
.sigcard{display:grid;grid-template-columns:1fr;background:#fff;border:1px solid var(--line);border-top:8px solid var(--brick);border-radius:22px;overflow:hidden;box-shadow:var(--shadow-sm);color:inherit;transition:transform .28s,box-shadow .28s;}
@media(min-width:760px){.sigcard{grid-template-columns:.9fr 1.1fr;}}
.sigcard:hover{transform:translateY(-8px);box-shadow:0 28px 54px -20px var(--brick);}
.sigcard__media{position:relative;min-height:210px;overflow:hidden;}
.sigcard__media img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .5s;}
.sigcard:hover .sigcard__media img{transform:scale(1.05);}
.sigcard__badge{position:absolute;z-index:2;left:16px;top:14px;background:var(--brick);color:#fff;font:700 12px/1 'Inter';letter-spacing:.12em;text-transform:uppercase;padding:7px 13px;border-radius:99px;}
.sigcard__body{padding:30px 32px 34px;display:flex;flex-direction:column;justify-content:center;}
.sigcard__body h3{font-family:'Playfair Display',serif;font-size:30px;color:var(--green-deep);font-weight:700;line-height:1.12;}
.sigcard__body .zh{font-family:'PingFang TC',sans-serif;font-size:19px;color:var(--ink);font-weight:600;margin-top:6px;}
.sigcard__body p{font-size:18px;color:var(--ink-soft);margin-top:14px;line-height:1.65;}
.sigcard__cta{margin-top:18px;font-family:'Playfair Display',serif;color:var(--brick);font-weight:700;font-size:18px;}
.sigcard:hover .sigcard__cta{text-decoration:underline;}
.sigcard--fest{border-top-color:var(--gold-deep);}
.sigcard--fest:hover{box-shadow:0 28px 54px -20px var(--gold-deep);}
.sigcard__media--fest{background:linear-gradient(135deg,#3c4587,#8a5f17);display:flex;align-items:center;justify-content:center;}
.sigcard__bigem{font-size:92px;filter:drop-shadow(0 4px 12px rgba(0,0,0,.32));transition:transform .5s ease;}
.sigcard--fest:hover .sigcard__bigem{transform:scale(1.08) rotate(-4deg);}
"""

UVCSS = """
.unit-hero{color:#fff;padding:46px 24px 58px;text-align:center;position:relative;overflow:hidden;}
@media(min-width:720px){.unit-hero{padding:66px 24px 80px;}}
.unit-hero__eyebrow{font-family:'Playfair Display',serif;font-size:13px;letter-spacing:5px;color:rgba(255,255,255,.85);text-transform:uppercase;font-weight:700;}
.unit-hero h1{font-family:'Playfair Display',serif;font-size:40px;font-weight:800;line-height:1.08;margin-top:10px;text-shadow:0 2px 14px rgba(0,0,0,.25);}
@media(min-width:720px){.unit-hero h1{font-size:60px;}}
.unit-hero__zh{font-size:20px;color:rgba(255,255,255,.92);margin-top:10px;letter-spacing:1.5px;}
.unit-hero__meta{display:inline-flex;gap:10px;margin-top:20px;padding:9px 22px;background:rgba(255,255,255,.16);border-radius:99px;font-size:15px;font-weight:600;letter-spacing:.06em;}
.unit-nav{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:26px 0 6px;flex-wrap:wrap;}
.unit-nav a{color:var(--green-deep);font-weight:700;font-size:16px;padding:10px 20px;border-radius:10px;border:2px solid var(--line);background:#fff;transition:all .15s;}
.unit-nav a:hover{background:var(--gold-soft);border-color:var(--gold);color:var(--gold-deep);}
.unit-nav a.center{background:var(--green-deep);color:#fff;border-color:var(--green-deep);}
.unit-nav a.center:hover{background:var(--gold);border-color:var(--gold);color:#fff;}
.vocabs{display:grid;grid-template-columns:1fr;gap:30px;margin:36px 0 26px;}
@media(min-width:880px){.vocabs{grid-template-columns:repeat(2,1fr);gap:34px;}}
.vc{background:#fff;border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow-sm);overflow:hidden;display:flex;flex-direction:column;border-top:8px solid var(--vca,var(--green));transition:transform .25s,box-shadow .25s;}
.vc:hover{transform:translateY(-6px);box-shadow:0 26px 48px -20px var(--vca,var(--green));}
.vc__head{padding:22px 26px 16px;}
.vc__num{font-family:'Playfair Display',serif;font-size:13px;font-weight:700;letter-spacing:2.5px;color:var(--gold-deep);text-transform:uppercase;}
.vc__term{font-family:'Playfair Display',serif;font-size:30px;font-weight:700;color:var(--green-deep);line-height:1.15;margin-top:6px;}
@media(min-width:720px){.vc__term{font-size:38px;}}
.vc__pos{font-size:.5em;color:var(--gold-deep);font-style:italic;font-weight:600;margin-left:6px;}
.vc__zh{font-family:'PingFang TC',sans-serif;font-size:20px;color:var(--ink);font-weight:600;margin-top:4px;letter-spacing:1px;}
@media(min-width:720px){.vc__zh{font-size:25px;}}
.vc__video{position:relative;width:100%;padding-bottom:56.25%;background:#000;}
.vc__video iframe{position:absolute;inset:0;width:100%;height:100%;border:0;}
.vc__body{padding:20px 26px 26px;}
.vc__ex{background:var(--cream);border-radius:12px;padding:13px 17px;border-left:4px solid var(--vca,var(--green));}
.vc__ex+.vc__ex{margin-top:12px;}
.vc__ex .en{font-size:18px;color:var(--ink);font-weight:600;line-height:1.5;}
@media(min-width:720px){.vc__ex .en{font-size:20px;}}
.vc__ex .en b{color:var(--green-deep);}
.vc__ex .zh{font-size:15px;color:var(--ink-soft);margin-top:6px;line-height:1.55;}
@media(min-width:720px){.vc__ex .zh{font-size:17px;}}
.say{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;flex:0 0 auto;margin-right:8px;vertical-align:-6px;border:none;border-radius:50%;background:var(--gold-soft);color:var(--gold-deep);font-size:14px;cursor:pointer;transition:transform .15s,background .15s;}
.say:hover{background:var(--gold);color:#fff;transform:scale(1.12);}
.say:active{transform:scale(.94);}
"""

HEAD = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<link rel="canonical" href="{canon}"><title>{title}</title>'
        '<meta name="description" content="{desc}">'
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
        '<link rel="icon" type="image/png" sizes="32x32" href="/schools/chungshan/favicon-32.png"><link rel="icon" type="image/png" sizes="192x192" href="/schools/chungshan/favicon-192.png"><link rel="apple-touch-icon" sizes="180x180" href="/schools/chungshan/favicon-180.png"><link rel="shortcut icon" href="/schools/chungshan/favicon.ico">'
        '<link rel="stylesheet" href="/schools/chungshan/style.css"><link rel="stylesheet" href="/assets/css/motion.css">'
        '<style>{css}</style></head><body>')

def esc(s): return html.escape(s, quote=True)
def plain(s): return re.sub(r'<[^>]+>', '', s)

# Web Speech 🔊 (read learning content aloud)
SAY = ("<script>(function(){function speak(t){try{speechSynthesis.cancel();var u=new SpeechSynthesisUtterance(t);"
       "u.lang='en-US';u.rate=.92;speechSynthesis.speak(u);}catch(e){}}"
       "document.addEventListener('click',function(e){var b=e.target.closest('.say');if(b){speak(b.getAttribute('data-say'));}});})();</script>")

# ---------- Lessons hub ----------
cards = []
for i, u in enumerate(UNITS, 1):
    n = len(buckets[u['slug']])
    cards.append(
      f'<a class="unit" href="word/{u["slug"]}/" style="--ua:{u["g2"]}">'
      f'<div class="unit__hero" style="background:linear-gradient(135deg,{u["g1"]},{u["g2"]});">'
      f'<img class="unit__thumb" src="https://i.ytimg.com/vi/{buckets[u["slug"]][0]["id"]}/hqdefault.jpg" alt="" loading="lazy">'
      f'<div class="unit__veil"></div><span class="unit__emoji">{u["emoji"]}</span><span class="unit__play">▶</span></div>'
      f'<div class="unit__body"><div class="unit__no">Unit {i:02d} · Word of the Day</div>'
      f'<div class="unit__title">{esc(u["en"])}</div><div class="unit__title-zh">{esc(u["zh"])}</div>'
      f'<div class="unit__desc">{esc(u["desc"])}</div>'
      f'<div class="unit__cta"><span class="unit__count">{n} words · {n} 部影片</span><span>Open <span class="arrow">→</span></span></div>'
      f'</div></a>')

total = sum(len(buckets[u['slug']]) for u in UNITS)
lessons = HEAD.format(
    canon='https://changhua-bilingual.org/schools/chungshan/lessons/',
    title='Lessons · 每日一字 · Chungshan Elementary',
    desc='Chungshan Word of the Day — 70+ short bilingual videos from across our campus, sorted into five themes. 中山國小每日一字雙語影片課程。',
    css=LCSS)
lessons += TB
lessons += ('<header class="chero is-photo" style="--photo:url(/schools/chungshan/photos/lessons-banner.jpg);"><div class="chero__fx"></div>'
            '<div class="chero__inner"><span class="eyebrow">Bilingual Curriculum · 雙語課程</span>'
            '<h1>Word of the Day</h1><div class="h1-zh">每日一字 · 校園裡的英文小故事</div></div>'
            '<div class="scrollcue" aria-hidden="true">⌄</div></header>')
lessons += ('<section><div class="wrap"><div class="sec__no">I.</div>'
            '<h2 class="sec__title">Word of the Day</h2><div class="sec__title-zh">每日一字 · 五大主題，點一個單元開始</div><div class="sec__rule"></div>'
            f'<p class="lead-zh" style="margin-top:0;">{total} short bilingual videos from real moments around the Chungshan campus — each with two example sentences in English and Chinese. '
            '每段都來自校園真實場景，附兩句中英例句。</p>'
            f'<div class="units">{"".join(cards)}</div></div></section>')
# ---- Signature Course: Poem Tree ----
lessons += ('<section><div class="wrap"><div class="sec__no">II.</div>'
            '<h2 class="sec__title">Signature &amp; Festival Lessons</h2><div class="sec__title-zh">特色課程 · 詩文樹與世界節慶</div><div class="sec__rule"></div>'
            '<a class="sigcard" href="poem-tree/">'
            '<div class="sigcard__media"><span class="sigcard__badge">Poem Tree · 詩文樹</span>'
            '<img src="/schools/chungshan/photos/news-banner.jpg" alt="The Poem Tree at Chungshan Elementary" loading="lazy"></div>'
            '<div class="sigcard__body"><h3>The Poem Tree</h3><div class="zh">詩文樹 · 彰化文學家的搖籃</div>'
            '<p>Meet the twelve literary alumni honored on Chungshan\'s Poem Tree — among them Lai He, the father of Taiwan\'s New Literature. '
            'Read their poems with English translations, learn the key words, and listen along. 認識詩文樹上的十二位文學家校友，讀他們的詩文與英譯，學關鍵字、聽發音。</p>'
            '<span class="sigcard__cta">Enter the lesson · 進入學習 →</span></div></a>'
            '<a class="sigcard sigcard--fest" href="/schools/chungshan/festivals/" style="margin-top:24px;">'
            '<div class="sigcard__media sigcard__media--fest"><span class="sigcard__badge" style="background:var(--gold-deep);">Festivals · 節慶英語</span>'
            '<span class="sigcard__bigem">🎊</span></div>'
            '<div class="sigcard__body"><h3>Festivals Around the World</h3><div class="zh">世界節慶英語 · 16 個節慶單元</div>'
            '<p>From Lunar New Year and the Lantern Festival to Halloween and Christmas — sixteen bilingual festival lessons, each with vocabulary, '
            'traditions, role-play and a quiz. 從農曆新年、元宵，到萬聖節、聖誕節——十六個雙語節慶單元，含單字、習俗、角色扮演與小測驗。</p>'
            '<span class="sigcard__cta" style="color:var(--gold-deep);">Explore the festivals · 進入節慶 →</span></div></a>'
            '</div></section>')

# ---- Classroom English (shared MCC playlist) ----
lessons += ('<section id="classroom-english"><div class="wrap"><div class="sec__no">III.</div>'
            '<h2 class="sec__title">Classroom English</h2><div class="sec__title-zh">課室英語 · 給老師的口袋句庫（影片版）</div><div class="sec__rule"></div>'
            '<div class="lead">The phrases teachers say between the lessons — taught on video.</div>'
            '<div class="lead-zh">老師在課堂裡每天會用上的英文句子——有人示範給你看。</div>'
            '<div class="credits"><div class="credits__cell"><div class="credits__label">Instructor</div><div class="credits__value">Sarah Thomas · Sarah Thomas 老師</div></div>'
            '<div class="credits__cell"><div class="credits__label">Producer</div><div class="credits__value">My Culture Connect · 人師</div></div>'
            '<div class="credits__cell"><div class="credits__label">Audience</div><div class="credits__value">In-service teachers · 在職教師</div></div></div>'
            '<div class="player"><div class="player__ratio"><iframe src="https://www.youtube-nocookie.com/embed/videoseries?list=PL01OhMUI2G8UDZ8tSZ6MTGyjXsGEJ24wZ&rel=0" title="Classroom English playlist by Sarah Thomas" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div></div>'
            '<a class="player-link" href="https://www.youtube.com/playlist?list=PL01OhMUI2G8UDZ8tSZ6MTGyjXsGEJ24wZ" target="_blank" rel="noopener"><span class="player-link__icon">▶</span><span class="player-link__text"><strong>Browse the full playlist on YouTube</strong><span>在 YouTube 開啟完整 playlist · 直接跳到想看的那一支</span></span><span class="player-link__arrow">↗</span></a>'
            '<div class="topics">'
            '<div class="topic"><div class="topic__no">01</div><div class="topic__en">Greetings &amp; Roll Call</div><div class="topic__zh">問候、點名</div></div>'
            '<div class="topic"><div class="topic__no">02</div><div class="topic__en">Pre-Class Preparation</div><div class="topic__zh">課前準備</div></div>'
            '<div class="topic"><div class="topic__no">03</div><div class="topic__en">Explanations</div><div class="topic__zh">講解</div></div>'
            '<div class="topic"><div class="topic__no">04</div><div class="topic__en">Pre-Teaching Activities</div><div class="topic__zh">課前教學活動</div></div>'
            '<div class="topic"><div class="topic__no">05</div><div class="topic__en">Feedback &amp; Praise</div><div class="topic__zh">回饋、讚美、糾正</div></div>'
            '<div class="topic"><div class="topic__no">06</div><div class="topic__en">Order &amp; Handouts</div><div class="topic__zh">教室管理、分發講義</div></div>'
            '<div class="topic"><div class="topic__no">07</div><div class="topic__en">Lesson Activities</div><div class="topic__zh">課堂教學活動</div></div>'
            '<div class="topic"><div class="topic__no">08</div><div class="topic__en">Assigning Homework</div><div class="topic__zh">分派作業</div></div>'
            '<div class="topic"><div class="topic__no">09</div><div class="topic__en">Class Conclusion</div><div class="topic__zh">課堂收尾</div></div>'
            '<div class="topic"><div class="topic__no">10</div><div class="topic__en">Examinations</div><div class="topic__zh">考試</div></div>'
            '</div></div></section>')

# ---- Bilingual Announcements (shared MCC playlist) ----
lessons += ('<section id="announcements"><div class="wrap"><div class="sec__no">IV.</div>'
            '<h2 class="sec__title">Bilingual Announcements</h2><div class="sec__title-zh">英語廣播 · 校園的英語之聲</div><div class="sec__rule"></div>'
            '<div class="lead">The morning intercom in two languages — written and recorded by the four school offices.</div>'
            '<div class="lead-zh">早上的校園廣播，雙語版本——由教務、學務、總務、輔導四個處室共同寫稿、共同上鏡。</div>'
            '<div class="credits is-broadcast"><div class="credits__cell"><div class="credits__label">Hosts</div><div class="credits__value">Sarah Thomas &amp; Susan Rose</div></div>'
            '<div class="credits__cell"><div class="credits__label">Producer</div><div class="credits__value">My Culture Connect · 人師</div></div>'
            '<div class="credits__cell"><div class="credits__label">Episodes</div><div class="credits__value">13 · 涵蓋四個處室</div></div></div>'
            '<div class="player"><div class="player__ratio"><iframe src="https://www.youtube-nocookie.com/embed/videoseries?list=PL01OhMUI2G8U2l5LnxUpEA_Uvi-5wdTKy&rel=0" title="Bilingual Announcements playlist" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div></div>'
            '<a class="player-link" href="https://www.youtube.com/playlist?list=PL01OhMUI2G8U2l5LnxUpEA_Uvi-5wdTKy" target="_blank" rel="noopener"><span class="player-link__icon">▶</span><span class="player-link__text"><strong>Browse the full playlist on YouTube</strong><span>在 YouTube 開啟完整 playlist · 13 集任你選擇</span></span><span class="player-link__arrow">↗</span></a>'
            '<div class="offices">'
            '<div class="office"><div class="office__title">Academic Affairs</div><div class="office__title-zh">教務處</div><ul class="office__list">'
            '<li><span class="ep">EP</span><span>Curriculum &amp; Instruction · 教學組</span></li><li><span class="ep">EP</span><span>Registrar · 註冊組</span></li>'
            '<li><span class="ep">EP</span><span>Equipment &amp; Facilities · 設備組</span></li><li><span class="ep">EP</span><span>Library · 圖書室</span></li>'
            '<li><span class="ep">EP</span><span>Information Technology · 資訊組</span></li></ul></div>'
            '<div class="office"><div class="office__title">Student Affairs</div><div class="office__title-zh">學務處</div><ul class="office__list">'
            '<li><span class="ep">EP</span><span>Discipline &amp; Activities · 訓育組</span></li><li><span class="ep">EP</span><span>Student Guidance · 生教組</span></li>'
            '<li><span class="ep">EP</span><span>Physical Education · 體育組</span></li></ul></div>'
            '<div class="office"><div class="office__title">General Affairs</div><div class="office__title-zh">總務處</div><ul class="office__list">'
            '<li><span class="ep">EP</span><span>Documents, Cashier, Maintenance · 文書、出納、事務</span></li></ul></div>'
            '<div class="office"><div class="office__title">Counseling Office</div><div class="office__title-zh">輔導室</div><ul class="office__list">'
            '<li><span class="ep">EP</span><span>Student support &amp; career guidance · 學生支持與生涯輔導</span></li></ul></div>'
            '</div></div></section>')

lessons += ('<section style="padding-top:0;"><div class="wrap"><div class="playlist-block">'
            '<h3>Watch the full playlist on YouTube</h3><div class="zh">不分單元，這裡是完整的中山英語影片清單</div>'
            '<div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/videoseries?list=PL01OhMUI2G8WSth0Ydh_MaazCkPOXDSGs&rel=0" title="Chungshan Word of the Day · full playlist" loading="lazy" allowfullscreen></iframe></div>'
            '</div></div></section>')
lessons += REVEAL + FOOT + '<script defer src="/assets/js/motion.js"></script></body></html>'
os.makedirs(os.path.join(ROOT, 'lessons'), exist_ok=True)
open(os.path.join(ROOT, 'lessons', 'index.html'), 'w').write(lessons)

# ---------- Unit pages ----------
for i, u in enumerate(UNITS):
    vids = buckets[u['slug']]
    nxt = UNITS[(i + 1) % len(UNITS)]
    vcs = []
    for j, d in enumerate(vids, 1):
        pos = f'<span class="vc__pos">({esc(d["pos"])})</span>' if d.get('pos') else ''
        exs = ''.join(
            f'<div class="vc__ex"><div class="en"><button class="say" data-say="{esc(plain(e["en"]))}" aria-label="Listen">🔊</button>{e["en"]}</div>'
            + (f'<div class="zh">{esc(e["zh"])}</div>' if e.get('zh') else '') + '</div>'
            for e in d['exs'])
        vcs.append(
          f'<article class="vc" style="--vca:{u["g2"]}"><div class="vc__head">'
          f'<div class="vc__num">Word {j:02d}</div>'
          f'<div class="vc__term">{esc(d["en"])} {pos}</div><div class="vc__zh">{esc(d["zh"])}</div></div>'
          f'<div class="vc__video"><iframe src="https://www.youtube-nocookie.com/embed/{d["id"]}?rel=0" title="{esc(d["en"])} · {esc(d["zh"])}" loading="lazy" allowfullscreen></iframe></div>'
          f'<div class="vc__body">{exs}</div></article>')
    navtop = (f'<div class="unit-nav"><a href="../../" class="center">← All Units · 回 Lessons</a>'
              f'<a href="../{nxt["slug"]}/">Next: {esc(nxt["en"])} →</a></div>')
    page = HEAD.format(
        canon=f'https://changhua-bilingual.org/schools/chungshan/lessons/word/{u["slug"]}/',
        title=f'{esc(u["en"])} · Chungshan Word of the Day',
        desc=f'{esc(u["en"])} — {len(vids)} bilingual Word-of-the-Day videos from Chungshan Elementary. {esc(u["zh"])}，{len(vids)} 部雙語影片。',
        css=UVCSS)
    page += TB
    page += (f'<header class="unit-hero" style="background:linear-gradient(135deg,{u["g1"]},{u["g2"]});">'
             f'<div class="unit-hero__eyebrow">Word of the Day · Unit {i+1:02d}</div>'
             f'<h1>{u["emoji"]} {esc(u["en"])}</h1><div class="unit-hero__zh">{esc(u["zh"])}</div>'
             f'<div class="unit-hero__meta">📺 {len(vids)} videos · {len(vids)} 部影片</div></header>')
    page += f'<div class="wrap">{navtop}<div class="vocabs">{"".join(vcs)}</div>{navtop}</div>'
    page += REVEAL + SAY + FOOT + '<script defer src="/assets/js/motion.js"></script></body></html>'
    os.makedirs(os.path.join(ROOT, 'lessons', 'word', u['slug']), exist_ok=True)
    open(os.path.join(ROOT, 'lessons', 'word', u['slug'], 'index.html'), 'w').write(page)

print('Lessons built. Per-unit counts:')
for u in UNITS:
    print(f"  {u['slug']:<12} {len(buckets[u['slug']])}")
print('total videos placed:', total, 'of', len(DATA))
