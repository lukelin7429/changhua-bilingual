#!/usr/bin/env python3
# Build Mingli "Topic Lessons" — clickable topic pages (feature video + vocab w/ examples),
# mirroring the mcc reference pages. Vocab sourced from playlist mini-lesson descriptions
# and the WOTD dataset. Also regenerates the Topic Lessons card grid in lessons/index.html.
import json, re, os, html

ROOT = os.path.expanduser("~/Documents/Claude/repos/changhua-bilingual")
LESSONS = os.path.join(ROOT, "schools/mingli/lessons")
wotd = {r['kw'].lower(): r for r in json.load(open("/tmp/wotd_clean.json"))}

def W(kw):  # pull (video_id, [sentences]) from WOTD dataset
    r = wotd[kw.lower()]; return r['id'], r['s']

POS = {'n':'n.', 'v':'v.', 'prep':'prep.', 'adv':'adv.', 'adj':'adj.'}
def esc(s): return html.escape(s, quote=True)
def bold(text, kw):
    base = kw.lower()
    cands = {kw, base, base+'s', base+'es', base+'ing', base+'ed'}
    if base.endswith('e'): cands |= {base[:-1]+'ing', base+'d'}
    if base.endswith('y'): cands |= {base[:-1]+'ies'}
    cands.add(base.split()[0])
    for c in sorted(cands, key=len, reverse=True):
        m = re.search(r'\b'+re.escape(c)+r'\b', text, re.I)
        if m: return esc(text[:m.start()])+'<b>'+esc(text[m.start():m.end()])+'</b>'+esc(text[m.end():])
    return esc(text)

# word tuple: (term, pos, zh, [(en,zh)...] or None->use WOTD, wotd_id or None)
def word(term, pos, zh, sents=None, use_wotd=False):
    vid = None
    if use_wotd:
        vid, ws = W(term)
        if sents is None: sents = ws
    return (term, pos, zh, sents or [], vid)

TOPICS = [
 dict(slug="scarecrow", emoji="🌾", en="Scarecrow", zh="稻草人",
   intro_en="Mingli students built real scarecrows from bamboo poles and dry grass — a hands-on farm lesson in keeping the birds away from the crops.",
   intro_zh="明禮的孩子用竹竿和乾草親手做出真正的稻草人——一堂「保護農作物」的食農英語課。",
   features=[("6-YZhY4lk20","Mini Lesson · How to make a scarecrow","稻草人主題英語教學"),
             ("shlRAZki9oI","News Clip · Mingli's scarecrow-making","明禮國小稻草人製作英語報導")],
   words=[
     word("scarecrow","n","稻草人",[("Scarecrows keep birds away from crops.","稻草人讓小鳥遠離農作物。"),("The teacher shows how to make a scarecrow.","老師示範如何製作稻草人。")],use_wotd=True),
     word("crop","n","農作物",[("Scarecrows keep birds away from crops.","稻草人讓小鳥遠離農作物。")]),
     word("tie","v","綁",[("The students tie the hay to make the scarecrow's arms and legs.","學生們綁稻草來做稻草人的手和腳。")]),
     word("hay","n","乾草",[("The students tie the hay to make the scarecrow's arms and legs.","學生們綁稻草來做稻草人的手和腳。")],use_wotd=True),
     word("stuff","v","塞",[("The students stuff the hay in the scarecrow's clothes.","學生們將稻草塞入稻草人的衣服。")]),
     word("pole","n","竿",None,use_wotd=True),
     word("instruction","n","指示說明",None,use_wotd=True),
   ]),
 dict(slug="computer-lab", emoji="💻", en="Computer Lab", zh="電腦教室",
   intro_en="A mini lesson filmed in Mingli's own computer room — the mouse, the keyboard, the tablet, and everything you do at a desktop computer.",
   intro_zh="在明禮自己的電腦教室實地拍攝的迷你課——滑鼠、鍵盤、平板，以及在桌機前會用到的每個字。",
   features=[("qMtjjMxNgao","Mini Lesson · In the computer lab","電腦教室英語教學")],
   words=[
     word("computer lab","n","電腦教室",[("The students are practicing their computer skills in the computer lab.","學生在電腦教室練習電腦技巧。")]),
     word("mouse","n","滑鼠",[("The student uses a mouse to click on the screen.","學生使用滑鼠在螢幕上點選。")]),
     word("keyboard","n","鍵盤",[("The students are typing on the keyboards.","學生正在鍵盤上打字。")]),
     word("tablet","n","平板",[("The students use a tablet with a computer.","學生使用電腦與平板。")],use_wotd=True),
     word("desktop computer","n","桌上型電腦",None,use_wotd=True),
     word("iPad","n","iPad",None,use_wotd=True),
     word("connect","v","連接",None,use_wotd=True),
     word("QR code","n","QR 碼",None,use_wotd=True),
   ]),
 dict(slug="tea-ceremony", emoji="🍵", en="Tea Ceremony", zh="茶道",
   intro_en="Tea leaves, teapot, pour, teacup — the vocabulary of Taiwan's tea culture, step by step, from preparing the pot to the first small sip.",
   intro_zh="茶葉、茶壺、倒入、茶杯——台灣茶文化的英語字彙，一步一步從備壺到啜飲第一口。",
   features=[("RuDpnhOPi2E","Mini Lesson · A tea ceremony, step by step","茶道英語教學")],
   words=[
     word("tea ceremony","n","茶道",[("During a tea ceremony, the host prepares and serves the tea.","在茶道中，主人會準備並奉茶。")],use_wotd=True),
     word("tea leaves","n","茶葉",[("First, the host puts tea leaves in the teapot.","首先，主人會將茶葉放入茶壺中。")]),
     word("teapot","n","茶壺",[("Next, the host pours hot water in the teapot.","接下來，主人會往茶壺裡倒入熱水。")]),
     word("pour","v","倒入",[("Then the host pours the tea into the guests' teacups.","然後，主人會將茶倒入客人的茶杯裡。")]),
     word("teacup","n","茶杯",[("Finally, the guests lift their teacups to their lips and take small sips.","最後，客人會把茶杯舉到嘴邊，喝一小口。")]),
     word("tea culture","n","茶文化",None,use_wotd=True),
   ]),
 dict(slug="croquet", emoji="🏑", en="Croquet", zh="槌球",
   intro_en="Mingli's signature sport — croquet court, mallet, wicket. A gentle outdoor game on the grass that every student learns.",
   intro_zh="明禮的招牌運動——槌球場、木槌、球門。一種在草地上進行、每位學生都會的溫和戶外遊戲。",
   features=[("lCSMia9u6Qg","Mini Lesson · How to play croquet","槌球英語教學")],
   words=[
     word("croquet","n","槌球",[("Croquet is a fun outdoor game.","槌球是一種有趣的戶外遊戲。")]),
     word("croquet court","n","槌球場",[("A croquet court is usually made of grass.","槌球場通常是草地。")]),
     word("mallet","n","木槌",[("People play croquet with mallets and balls on a grass field.","人們在草地上用木槌和球打槌球。")]),
     word("wicket","n","球門",[("In croquet, players take turns hitting the ball through a series of wickets.","在槌球運動中，球員輪流擊球穿過一系列小球門。")]),
   ]),
 dict(slug="school-anniversary", emoji="🎉", en="School Anniversary", zh="校慶",
   intro_en="Mingli Elementary turned 80. Group dances, running races, a new track unveiling — the whole celebration, told in English.",
   intro_zh="明禮國小八十歲了。團體舞、賽跑、新跑道揭幕——整場校慶，用英語說一遍。",
   features=[("Pu4xi8iUB9o","English News Report · Mingli's 80th Anniversary","八十週年校慶英文報導")],
   words=[
     word("anniversary","n","週年紀念",None,use_wotd=True),
     word("rehearsal","n","排練",None,use_wotd=True),
     word("relay race","n","接力賽跑",None,use_wotd=True),
     word("baton","n","接力棒",None,use_wotd=True),
     word("100 meter dash","n","一百公尺短跑",None,use_wotd=True),
     word("dance exercise","n","韻律舞",None,use_wotd=True),
     word("tire pushing game","n","滾輪胎",None,use_wotd=True),
     word("award presentation","n","頒獎",None,use_wotd=True),
     word("volunteer","n","志工",None,use_wotd=True),
   ]),
 dict(slug="tianzhong-pottery", emoji="🏺", en="Tianzhong Pottery", zh="田中陶藝",
   intro_en="Tianzhong is famous for its kiln. Pottery, the pottery wheel, the artist's hands — and why pottery is one of the hardest arts to master.",
   intro_zh="田中以窯場聞名。陶器、陶輪、藝術家的雙手——以及為什麼陶藝是最難精通的藝術之一。",
   features=[],
   words=[
     word("pottery","n","陶器",None,use_wotd=True),
     word("pottery wheel","n","陶輪",None,use_wotd=True),
     word("artist","n","藝術家",None,use_wotd=True),
     word("tea culture","n","茶文化",None,use_wotd=True),
   ]),
 dict(slug="math", emoji="➕", en="Math English", zh="數學英語",
   intro_en="Addition, minus, times — say the three core operations in English, with a short, clear bilingual video for each.",
   intro_zh="加法、減、乘——用英語說出三個核心運算，每個都有清楚簡短的雙語影片。",
   features=[],
   words=[
     word("addition","n","加法",None,use_wotd=True),
     word("minus","prep","減",None,use_wotd=True),
     word("times","prep","乘",None,use_wotd=True),
   ]),
 dict(slug="school-introduction", emoji="🏫", en="Mingli School Introduction", zh="學校英文介紹",
   intro_en="A small, close-knit rural school of 81 students in Tianzhong — proud of its Eco School status, its own farmland, and its agricultural education.",
   intro_zh="位於田中、81 位學生的小而緊密的鄉村小學——以生態學校、自有農田與食農教育為榮。",
   features=[("dyEPAIJILSM","English Introduction to Mingli","明禮國小英文簡介"),
             ("hV0y7mr58DI","Welcome to Mingli Elementary School","歡迎來到明禮國小"),
             ("zcRs7HOtkAE","Campus Locations · student version","校園地點（學生版）")],
   words=[
     word("county","n","縣",[("Mingli Elementary School is in Tianzhong Township, Changhua County.","明禮國小位於彰化縣田中鎮。")]),
     word("Eco School","n","生態學校",[("Mingli is proud to be part of the Eco Schools Global project.","明禮很自豪能成為台美生態學校的一員。")]),
     word("farmland","n","農田",[("The school has its own piece of farmland where students learn about agriculture.","學校有自己的一塊農田，學生在那裡學習農業。")]),
     word("agriculture","n","農業",[("Students see first-hand how food is grown and harvested.","學生親自觀察食物如何種植與收成。")]),
     word("croquet","n","槌球",[("Mingli offers sports clubs such as croquet, ping pong, and badminton.","明禮提供槌球、桌球和羽毛球等運動社團。")]),
     word("badminton","n","羽毛球",[("Mingli offers sports clubs such as croquet, ping pong, and badminton.","明禮提供槌球、桌球和羽毛球等運動社團。")]),
   ]),
]

CSS = """
  :root{--g-deep:#1a4330;--g:#2d7a52;--g-light:#52b788;--g-soft:#d8f3dc;
    --gold:#c8922a;--gold-soft:#fdf8e7;--gold-deep:#7d5a0a;--earth:#a0522d;--earth-soft:#f5e6d8;
    --ink:#1a2a1e;--ink-soft:#536653;--line:#d4e8d7;
    --shadow:0 14px 38px -16px rgba(26,67,48,.28);--shadow-sm:0 6px 16px -6px rgba(26,67,48,.16);}
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
  .thero{color:#fff;padding:44px 24px 52px;text-align:center;}
  @media(min-width:720px){.thero{padding:62px 24px 72px;}}
  .thero__eyebrow{font-family:'Playfair Display',serif;font-size:13px;letter-spacing:5px;text-transform:uppercase;color:rgba(255,255,255,.85);font-weight:700;}
  .thero__emoji{font-size:54px;line-height:1;margin:8px 0 4px;filter:drop-shadow(0 6px 12px rgba(0,0,0,.2));}
  @media(min-width:720px){.thero__emoji{font-size:68px;}}
  .thero h1{font-family:'Playfair Display',serif;font-size:36px;font-weight:800;line-height:1.12;text-shadow:0 3px 10px rgba(0,0,0,.25);}
  @media(min-width:720px){.thero h1{font-size:54px;}}
  .thero__zh{font-size:19px;color:rgba(255,255,255,.95);margin-top:6px;font-weight:600;letter-spacing:1px;}
  @media(min-width:720px){.thero__zh{font-size:24px;}}
  .thero__intro{max-width:720px;margin:16px auto 0;font-size:16px;color:rgba(255,255,255,.92);line-height:1.6;}
  @media(min-width:720px){.thero__intro{font-size:18px;}}
  .thero__intro .zh{display:block;font-size:14px;color:rgba(255,255,255,.8);margin-top:6px;}
  @media(min-width:720px){.thero__intro .zh{font-size:16px;}}
  .tback{padding:22px 0 0;}
  .tback a{color:var(--g-deep);text-decoration:none;font-weight:700;font-size:15px;padding:10px 18px;border-radius:10px;border:2px solid var(--line);background:#fff;transition:all .15s;display:inline-block;}
  @media(min-width:720px){.tback a{font-size:17px;}}
  .tback a:hover{background:var(--gold-soft);border-color:var(--gold);color:var(--gold-deep);}
  .sec-h{font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:var(--g-deep);margin:40px 0 4px;}
  @media(min-width:720px){.sec-h{font-size:36px;}}
  .sec-h-zh{font-size:16px;color:var(--ink-soft);margin-bottom:24px;}
  @media(min-width:720px){.sec-h-zh{font-size:18px;}}
  .feat{display:grid;grid-template-columns:1fr;gap:24px;}
  @media(min-width:820px){.feat.two{grid-template-columns:1fr 1fr;}}
  .feat-item{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:var(--shadow-sm);}
  .feat-item__ratio{position:relative;width:100%;padding-bottom:56.25%;background:#000;}
  .feat-item__ratio iframe{position:absolute;inset:0;width:100%;height:100%;border:0;}
  .feat-item__cap{padding:16px 20px;font-size:16px;color:var(--ink);}
  @media(min-width:720px){.feat-item__cap{font-size:18px;}}
  .feat-item__cap b{color:var(--g-deep);}
  .feat-item__cap .zh{display:block;font-size:14px;color:var(--ink-soft);margin-top:3px;}
  @media(min-width:720px){.feat-item__cap .zh{font-size:16px;}}
  .vocabs{display:grid;grid-template-columns:1fr;gap:26px;margin-bottom:10px;}
  @media(min-width:880px){.vocabs{grid-template-columns:repeat(2,1fr);gap:30px;}}
  .vc{background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow-sm);overflow:hidden;display:flex;flex-direction:column;border-top:8px solid var(--g);}
  .vc:nth-child(2n){border-top-color:var(--gold);}
  .vc:nth-child(3n){border-top-color:var(--earth);}
  .vc:nth-child(4n){border-top-color:var(--g-light);}
  .vc__head{padding:20px 24px 14px;}
  @media(min-width:720px){.vc__head{padding:24px 28px 16px;}}
  .vc__num{font-family:'Playfair Display',serif;font-size:13px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--gold-deep);}
  .vc__term{font-family:'Playfair Display',serif;font-size:28px;font-weight:800;color:var(--g-deep);line-height:1.15;margin-top:5px;}
  @media(min-width:720px){.vc__term{font-size:36px;}}
  .vc__pos{font-size:.5em;color:var(--gold-deep);font-style:italic;font-weight:600;margin-left:6px;}
  .vc__zh{font-size:19px;color:var(--ink);font-weight:600;margin-top:4px;letter-spacing:1px;}
  @media(min-width:720px){.vc__zh{font-size:24px;}}
  .vc__video{position:relative;width:100%;padding-bottom:56.25%;background:#000;}
  .vc__video iframe{position:absolute;inset:0;width:100%;height:100%;border:0;}
  .vc__body{padding:18px 24px 24px;}
  @media(min-width:720px){.vc__body{padding:22px 28px 28px;}}
  .vc__exs{display:flex;flex-direction:column;gap:12px;}
  .vc__ex{background:#f6faf6;border-radius:12px;padding:12px 16px;border-left:4px solid var(--g);}
  .vc__ex:nth-child(2){border-left-color:var(--gold);}
  .vc__ex .en{font-size:18px;color:var(--ink);font-weight:600;line-height:1.5;}
  @media(min-width:720px){.vc__ex .en{font-size:20px;}}
  .vc__ex .en b{color:var(--g);}
  .vc__ex .zh{font-size:15px;color:var(--ink-soft);margin-top:5px;line-height:1.55;}
  @media(min-width:720px){.vc__ex .zh{font-size:17px;}}
  footer{text-align:center;padding:40px 24px;font-size:15px;color:var(--ink-soft);line-height:1.65;border-top:1px solid var(--line);margin-top:48px;}
  @media(min-width:720px){footer{font-size:17px;}}
  footer .org{font-weight:600;color:var(--g-deep);}
"""

def subnav():
    items=[("Home","../../../"),("Principal","../../../principal/"),("English Life","../../../bilingual-campus/"),
           ("Lessons","../../"),("News","../../../news/"),("Festivals","https://changhua-bilingual.org/festivals/?from=mingli")]
    return "\n".join(f'      <a href="{h}"{" class=\"is-active\"" if n=="Lessons" else ""}>{n}</a>' for n,h in items)

GRAD = {  # per-topic hero gradient (mingli earthy palette)
 "scarecrow":("#5fbf86","#1a4330"),"computer-lab":("#5b7fb0","#2d4a72"),
 "tea-ceremony":("#b06d92","#5b3350"),"croquet":("#6cbf7a","#2d7a52"),
 "school-anniversary":("#e0b84a","#a8740c"),"tianzhong-pottery":("#c08043","#6b4423"),
 "math":("#5b7fb0","#2d4a72"),"school-introduction":("#3d9b8f","#1c5048"),
}

def build_topic(t):
    c1,c2=GRAD[t['slug']]
    # feature videos
    feat=""
    if t['features']:
        two=" two" if len(t['features'])>1 else ""
        items=[]
        for vid,cen,czh in t['features']:
            items.append(f"""      <div class="feat-item">
        <div class="feat-item__ratio"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" title="{esc(cen)}" loading="lazy" allowfullscreen></iframe></div>
        <div class="feat-item__cap"><b>{esc(cen)}</b><span class="zh">{esc(czh)}</span></div>
      </div>""")
        feat=f"""
  <h2 class="sec-h">Watch &amp; Learn</h2>
  <div class="sec-h-zh">主題影片 · 看影片學主題英文</div>
  <div class="feat{two}">
{chr(10).join(items)}
  </div>
"""
    # vocab cards
    cards=[]
    for j,(term,pos,zh,sents,vid) in enumerate(t['words'],1):
        video=f'\n      <div class="vc__video"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" title="{esc(term)} · {esc(zh)}" loading="lazy" allowfullscreen></iframe></div>' if vid else ""
        exs="\n".join(f'          <div class="vc__ex"><div class="en">{bold(en,term)}</div><div class="zh">{esc(z)}</div></div>' for en,z in sents)
        cards.append(f"""    <article class="vc">
      <div class="vc__head">
        <div class="vc__num">Word {j:02d}</div>
        <div class="vc__term">{esc(term)} <span class="vc__pos">({POS.get(pos,pos+'.')})</span></div>
        <div class="vc__zh">{esc(zh)}</div>
      </div>{video}
      <div class="vc__body">
        <div class="vc__exs">
{exs}
        </div>
      </div>
    </article>""")
    cards="\n\n".join(cards)
    nwords=len(t['words'])
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(t['en'])} · Topic Lesson · Mingli Elementary</title>
<meta name="description" content="Mingli topic lesson: {esc(t['en'])} ({esc(t['zh'])}). {nwords} key words with bilingual example sentences and videos filmed on campus. 明禮主題課程{esc(t['zh'])}，{nwords} 個關鍵字、雙語例句與校園實拍影片。">
<link rel="icon" type="image/png" sizes="32x32" href="/schools/mingli/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/schools/mingli/favicon-180.png">
<link rel="shortcut icon" href="/schools/mingli/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script defer src="/analytics.js"></script>
</head>
<body>

<nav class="topbar" role="navigation" aria-label="Site navigation">
  <div class="topbar-inner">
    <a class="topbar-name" href="../../../">Mingli Elementary<small>彰化縣田中鎮明禮國民小學</small></a>
    <div class="topbar-nav">
{subnav()}
    </div>
  </div>
</nav>

<header class="thero" style="background:linear-gradient(135deg,{c1} 0%,{c2} 100%);">
  <div class="thero__eyebrow">Topic Lesson · 主題課程</div>
  <div class="thero__emoji">{t['emoji']}</div>
  <h1>{esc(t['en'])}</h1>
  <div class="thero__zh">{esc(t['zh'])}</div>
  <p class="thero__intro">{esc(t['intro_en'])}<span class="zh">{esc(t['intro_zh'])}</span></p>
</header>

<div class="wrap">
  <div class="tback"><a href="../../">↑ All Topics · 回 Lessons</a></div>
{feat}
  <h2 class="sec-h">Words 實用單字</h2>
  <div class="sec-h-zh">{nwords} key words · {nwords} 個關鍵字，每個都附雙語例句</div>
  <div class="vocabs">

{cards}

  </div>

  <div class="tback" style="padding-bottom:8px;"><a href="../../">↑ All Topics · 回 Lessons</a></div>
</div>

<footer>
  © 彰化縣田中鎮明禮國民小學 · Mingli Elementary School &nbsp;·&nbsp;
  Topic lessons by <span class="org">My Culture Connect 人師教育協會</span> &nbsp;·&nbsp;
  Part of the <a href="https://changhua.mycultureconnect.org/" target="_blank" rel="noopener" style="color:var(--g-deep);">Changhua Bilingual Hub</a>
</footer>

</body>
</html>"""

# write topic pages
for t in TOPICS:
    d=os.path.join(LESSONS,"topics",t['slug']); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(build_topic(t))
    print("wrote topics/%s (%d feature, %d words)"%(t['slug'],len(t['features']),len(t['words'])))

# ---- Section II card grid (clickable) ----
DESC={
 "scarecrow":"Bamboo poles, dry grass and five key words — how Mingli students build a scarecrow to protect the crops.",
 "computer-lab":"Mouse, keyboard, tablet, desktop computer — a mini lesson filmed in Mingli's own computer room.",
 "tea-ceremony":"Tea leaves, teapot, pour, teacup — Taiwan's tea culture step by step, from the pot to the first sip.",
 "croquet":"Mingli's signature sport — croquet court, mallet, wicket — explained on the grass.",
 "school-anniversary":"Mingli's 80th in English — anniversary, relay race, rehearsal, award presentation and more.",
 "tianzhong-pottery":"Pottery, pottery wheel, the artist's hands — the English of Tianzhong's famous kiln.",
 "math":"Addition, minus, times — say the three core operations in English, one clear video each.",
 "school-introduction":"An 81-student Eco School in Tianzhong — county, farmland, agriculture, croquet, badminton.",
}
cards=[]
for t in TOPICS:
    cards.append(f"""      <a class="topic-card" href="topics/{t['slug']}/">
        <div class="topic-card__icon">{t['emoji']}</div>
        <h3 class="topic-card__title">{esc(t['en'])}</h3>
        <div class="topic-card__zh">{esc(t['zh'])}</div>
        <p class="topic-card__desc">{esc(DESC[t['slug']])}</p>
        <div class="topic-card__cta">Open lesson <span class="arrow">→</span></div>
      </a>""")
open("/tmp/mingli_topics_grid.html","w",encoding="utf-8").write("\n\n".join(cards))
print("\nwrote section II grid:",len(TOPICS),"linked cards")
