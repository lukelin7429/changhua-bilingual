#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Teacher Mari's English Hub (faithful recreation of her Google Site)."""
import os, glob, re

ROOT = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(ROOT, 'photos')
BASE = '/fets/teacher-mari'          # site-absolute base
PB = BASE + '/photos'                # photos base

# ---------- asset resolver ----------
def img(folder, idx):
    """Return site path to the image whose index token == idx (jpg/png)."""
    for ext in ('png','jpg'):
        m = sorted(glob.glob(os.path.join(PHOTOS, folder, f'{folder}_{idx}_*.{ext}')))
        if m: return f'{PB}/{folder}/{os.path.basename(m[0])}'
    # drive_* style
    m = sorted(glob.glob(os.path.join(PHOTOS, folder, f'{idx}_*.jpg')))
    if m: return f'{PB}/{folder}/{os.path.basename(m[0])}'
    return None

def vid(folder, idx):
    m = sorted(glob.glob(os.path.join(PHOTOS, folder, f'{folder}_{idx}_*.mp4')))
    if not m: return None, None
    mp4 = f'{PB}/{folder}/{os.path.basename(m[0])}'
    return mp4, mp4[:-4] + '.jpg'

def gallery_imgs(folder, idxs):
    out = []
    for tok in idxs:
        p = img(folder, tok)
        if p: out.append(p)
    return out

# ---------- nav ----------
NAV = [
    ('home', 'Home', BASE + '/', [('about-me','About Me', BASE + '/about-me/')]),
    ('school', 'NanHsing Elementary School', BASE + '/nanhsing/', [
        ('mission','Mission and Vision', BASE + '/nanhsing/mission-and-vision/'),
        ('about-school','About My School', BASE + '/nanhsing/about-my-school/'),
    ]),
    ('bhub', 'Bilingual Hub', BASE + '/bilingual-hub/', [
        ('morning','Morning Assembly', BASE + '/bilingual-hub/morning-assembly/'),
        ('corner','English Corner', BASE + '/bilingual-hub/english-corner/'),
        ('club','English Club', BASE + '/bilingual-hub/english-club/'),
        ('reading','Reading Class', BASE + '/bilingual-hub/reading-class/'),
    ]),
    ('game', 'Game Hub', BASE + '/game-hub/', []),
]

def nav_html(active):
    lis = []
    for key, label, href, subs in NAV:
        here = ' here' if key == active or any(s[0]==active for s in subs) else ''
        if subs:
            sub = ''.join(f'<li><a href="{h}" class="{"here" if k==active else ""}">{t}</a></li>' for k,t,h in subs)
            lis.append(f'<li class="has-sub"><a href="{href}" class="{here.strip()}">{label}</a><ul class="sub">{sub}</ul></li>')
        else:
            lis.append(f'<li><a href="{href}" class="{here.strip()}">{label}</a></li>')
    return f'''<header class="nav"><div class="nav-in">
  <a class="brand" href="{BASE}/"><img src="{PB}/home/{logo()}" alt="Nanhsing Elementary School">
    <span><b>Teacher Mari</b><small>Nanhsing English Hub</small></span></a>
  <button class="burger" aria-label="Menu">&#9776;</button>
  <ul class="menu">{''.join(lis)}</ul>
</div></header>'''

def logo():
    m = sorted(glob.glob(os.path.join(PHOTOS,'home','home_00_*.png')))
    return os.path.basename(m[0]) if m else ''

# ---------- footer ----------
CB_CREDIT = ('<div class="cb-credit" style="background:#241f1b;color:rgba(255,255,255,.62);text-align:center;'
 "padding:20px 22px 22px;font-family:'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif;"
 'font-size:13px;line-height:1.9;letter-spacing:.02em;">Site by '
 '<a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener" style="color:#e6c179;text-decoration:none;border-bottom:1px dashed rgba(230,193,121,.45);">My Culture Connect</a> '
 '<a href="https://www.twrses.org/" target="_blank" rel="noopener" style="color:#e6c179;text-decoration:none;border-bottom:1px dashed rgba(230,193,121,.45);">人師教育協會</a><br>'
 'Guided by <a href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener" style="color:#e6c179;text-decoration:none;border-bottom:1px dashed rgba(230,193,121,.45);">CIEETRC 彰化縣國際教育暨英語教育資源中心</a><br>'
 '<a href="https://changhua-bilingual.org/" target="_blank" rel="noopener" style="color:#e6c179;text-decoration:none;border-bottom:1px dashed rgba(230,193,121,.45);">Changhua Bilingual Hub 彰化雙語資源網</a></div>')

PAGE_FOOT = f'''<footer class="page-foot">
  <div class="ml">Learning + Playing = Happy English Learners 💚</div>
  <div class="row">
    <a href="{BASE}/">Home</a><a href="{BASE}/about-me/">About Me</a>
    <a href="{BASE}/bilingual-hub/">Bilingual Hub</a><a href="{BASE}/game-hub/">Game Hub</a>
    <a href="/fets/">All FETs</a>
  </div>
  <p style="margin:14px 0 0;font-size:14px;opacity:.6">Teacher Mari · Mary Marilyn Quisay Mitra · Nanhsing Elementary School, Changhua</p>
</footer>'''

# ---------- building blocks ----------
def hero_img(src, eyebrow, h1, sub=''):
    cap = f'<div class="hero-cap"><div class="eyebrow">{eyebrow}</div><h1>{h1}</h1>{f"<p>{sub}</p>" if sub else ""}</div>'
    return f'''<section class="hero"><span class="orb b"></span><span class="orb c"></span><span class="orb d"></span>
  <img class="hero-art" src="{src}" alt="{h1}">
  {cap}<a class="scrolldown" href="#main" aria-label="Scroll down">⌄</a></section>'''

def hero_video(mp4, poster, eyebrow, h1, sub=''):
    cap = f'<div class="hero-cap"><div class="eyebrow">{eyebrow}</div><h1>{h1}</h1>{f"<p>{sub}</p>" if sub else ""}</div>'
    return f'''<section class="hero"><span class="orb b"></span><span class="orb c"></span><span class="orb d"></span>
  <video class="hero-art video" autoplay muted loop playsinline poster="{poster}"><source src="{mp4}" type="video/mp4"></video>
  {cap}<a class="scrolldown" href="#main" aria-label="Scroll down">⌄</a></section>'''

def video_embed(vid_id):
    return (f'<div class="vframe"><iframe src="https://www.youtube-nocookie.com/embed/{vid_id}" '
            'title="YouTube video" loading="lazy" allow="accelerator;encrypted-media;picture-in-picture" '
            'allowfullscreen></iframe></div>')

def gallery_block(imgs, kind='gallery'):
    cells = ''.join(f'<figure class="gi reveal" data-lb="{s}"><img src="{s}" loading="lazy" alt=""></figure>' for s in imgs)
    return f'<div class="{kind}">{cells}</div>'

def slides_block(imgs):
    cells = ''.join(f'<img src="{s}" loading="lazy" alt="" data-lb="{s}" class="reveal">' for s in imgs)
    return f'<div class="slides">{cells}</div>'

def page(out_rel, title, theme, active, hero, body, desc):
    canonical = f'https://changhua-bilingual.org{BASE}/{out_rel.replace("index.html","")}'.rstrip('/') + '/'
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Teacher Mari's English Hub</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{PB}/home/{logo()}" type="image/png">
<meta property="og:title" content="{title} · Teacher Mari's English Hub">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://changhua-bilingual.org{img('home','02')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Caveat:wght@600;700&family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{BASE}/assets/mari.css">
</head>
<body class="theme-{theme}">
{nav_html(active)}
{hero}
<main id="main">
{body}
</main>
{PAGE_FOOT}
{CB_CREDIT}
<script src="{BASE}/assets/mari.js" defer></script>
</body>
</html>'''
    dst = os.path.join(ROOT, out_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(html)
    print('wrote', out_rel)

def idxrange(a, b):
    return [f'{i:02d}' for i in range(a, b+1)]

# =========================================================
#  PAGE CONTENT
# =========================================================

# ---- HOME ----
home_split = f'''<section class="block"><div class="wrap split">
  <div class="reveal">
    <div class="sec-eyebrow">Welcome!</div>
    <h2 class="sec">Hello everyone! 👋</h2>
    <p class="lead">I'm <b>Mary Marilyn Quisay Mitra</b>, originally from the lively southern region of the Philippines. Presently, I serve as a Foreign English Teacher at <b>Nanhsing Elementary School</b> in Changhua City, Changhua County, Taiwan.</p>
    <p class="lead">I hold a Bachelor of Science degree in Office Administration from Father Saturnino Urios University, and I have also completed my <b>TESOL</b> certification. With close to seven years of experience teaching English online, I've developed a profound passion for guiding students in enhancing their language skills and boosting their confidence.</p>
    <p class="lead">This website is where I share my journey, insights, and resources as an educator — cultivating a supportive, enriching learning environment for my students and connecting with fellow educators and learners worldwide.
    <span class="zh">大家好，歡迎光臨！我是 Mary Marilyn Quisay Mitra，來自菲律賓南部，目前在彰化市南興國小擔任英語教師。我擁有 Father Saturnino Urios University 辦公室管理學士學位與 TESOL 認證，並有近七年的線上英語教學經驗。這個網站是我分享教學旅程、心得與資源的園地，期待與世界各地的師生交流。</span></p>
  </div>
  <div class="reveal"><div class="photo"><img src="{img('home','03')}" alt="Nanhsing campus"></div></div>
</div></section>
<div class="ribbon reveal">Learning + Playing = Happy English Learners <span class="heart">💚</span></div>
<section class="block tint"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">Say hello</div><h2 class="sec">Meet Teacher Mari</h2>
  <p>A short introduction video — come and say hi! 來看看自我介紹影片 🎬</p></div>
  <div class="video-wrap reveal">{video_embed('TU5jqxsM4N8')}</div>
</div></section>'''
page('index.html', 'Home', 'home', 'home',
     hero_img(img('home','02'), 'Storytime', "Teacher Mari's English Hub",
              'Foreign English Teacher · Nanhsing Elementary School, Changhua'),
     home_split, "Teacher Mari (Mary Marilyn Quisay Mitra), Foreign English Teacher at Nanhsing Elementary School, Changhua, Taiwan.")

# ---- ABOUT ME ----
about_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">About Me</div><h2 class="sec">A peek into my classroom</h2>
  <p>Moments from teaching, learning, and growing together at Nanhsing — in the classroom and around our beautiful campus. 教室內外的點滴。</p></div>
  {gallery_block(gallery_imgs('home_about-me', idxrange(4,19)))}
</div></section>
<div class="ribbon reveal">Learning + Playing = Happy English Learners <span class="heart">💚</span></div>'''
page('about-me/index.html', 'About Me', 'school', 'about-me',
     hero_img(img('home_about-me','02'), 'Get to know me', 'About Teacher Mari'),
     about_body, "Get to know Teacher Mari and her classroom at Nanhsing Elementary School.")

# ---- NANHSING (school landing) ----
school_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">School Tour with the Kids</div><h2 class="sec">Welcome to Nanhsing Elementary School</h2>
  <p>Take a tour of our school with the students as your guides! 跟著孩子們一起認識南興國小 🏫</p></div>
  <div class="video-wrap reveal">{video_embed('hZPajHYMRS0')}</div>
  <div class="subnav reveal">
    <a href="{BASE}/nanhsing/mission-and-vision/">Mission &amp; Vision →</a>
    <a href="{BASE}/nanhsing/about-my-school/">About My School →</a>
  </div>
</div></section>'''
page('nanhsing/index.html', 'NanHsing Elementary School', 'school', 'school',
     hero_img(img('nanhsing','02'), 'My Educational Hub', 'Nanhsing Elementary School'),
     school_body, "A tour of Nanhsing Elementary School in Changhua, with Teacher Mari and her students.")

# ---- MISSION & VISION ----
mission_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">Mission &amp; Vision</div><h2 class="sec">What we stand for</h2>
  <p>Nanhsing's guiding philosophy — six values that shape every lesson. 南興國小的辦學理念。</p></div>
  <div class="feature reveal"><img src="{img('nanhsing_mission','04')}" alt="Nanhsing education philosophy"></div>
  <div class="cards reveal" style="margin-top:34px">
    <div class="tcard c1"><span class="emoji">📖</span><h3>Reading</h3><span>閱讀</span></div>
    <div class="tcard c2"><span class="emoji">🎨</span><h3>Aesthetic</h3><span>美感</span></div>
    <div class="tcard c3"><span class="emoji">🌏</span><h3>International</h3><span>國際</span></div>
    <div class="tcard c4"><span class="emoji">🤝</span><h3>Service-Learning</h3><span>服務學習</span></div>
    <div class="tcard c2"><span class="emoji">✨</span><h3>Multiple</h3><span>多元</span></div>
    <div class="tcard c1"><span class="emoji">🎓</span><h3>Education</h3><span>教育</span></div>
  </div>
</div></section>
<section class="block tint"><div class="wrap">
  <div class="sec-head reveal"><h2 class="sec">Around our campus</h2></div>
  {gallery_block(gallery_imgs('nanhsing_mission', ['03','05','06']))}
</div></section>'''
page('nanhsing/mission-and-vision/index.html', 'Mission and Vision', 'school', 'mission',
     hero_img(img('nanhsing_mission','02'), 'Our heart', 'Mission &amp; Vision'),
     mission_body, "Nanhsing Elementary School's mission and vision: Reading, Aesthetic, International, Service-Learning, Multiple Education.")

# ---- ABOUT MY SCHOOL ----
school2_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">International Class Introduction</div><h2 class="sec">Our International Class</h2>
  <p>How English and international learning come alive at Nanhsing. 南興國小的國際班與英語學習 🌏</p></div>
  <div class="video-grid reveal">{video_embed('R2TmQq-qGqM')}{video_embed('_ZQv-BoQoM4')}</div>
</div></section>
<section class="block tint"><div class="wrap">
  <div class="sec-head reveal"><h2 class="sec">In class &amp; around school</h2></div>
  {gallery_block(gallery_imgs('nanhsing_about-school', ['drive_0','drive_1','drive_2','drive_3','drive_4','drive_5','drive_6','05','06','07','08']))}
</div></section>'''
page('nanhsing/about-my-school/index.html', 'About My School', 'school', 'about-school',
     hero_img(img('nanhsing_about-school','02'), 'About My School', 'International Class'),
     school2_body, "Nanhsing Elementary School's international class and English program, introduced by Teacher Mari.")

# ---- BILINGUAL HUB (landing) ----
mp4, poster = vid('bilingual-hub', '02')
bhub_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">Bilingual Initiatives</div><h2 class="sec">Where English comes to life</h2>
  <p>Teaching is my passion. I believe every child can learn with support and encouragement — so I make English learning fun and meaningful. Explore our four bilingual programs below! 探索四大雙語活動 👇</p></div>
  <div class="cards reveal">
    <a class="tcard c1" href="{BASE}/bilingual-hub/morning-assembly/"><span class="emoji">🎤</span><h3>Morning Assembly</h3><span>晨會英語時間</span></a>
    <a class="tcard c2" href="{BASE}/bilingual-hub/english-corner/"><span class="emoji">📚</span><h3>English Corner</h3><span>英語角</span></a>
    <a class="tcard c3" href="{BASE}/bilingual-hub/english-club/"><span class="emoji">🌟</span><h3>English Club</h3><span>英語社 / 補救教學</span></a>
    <a class="tcard c4" href="{BASE}/bilingual-hub/reading-class/"><span class="emoji">📖</span><h3>Reading Class</h3><span>閱讀課</span></a>
  </div>
</div></section>'''
page('bilingual-hub/index.html', 'Bilingual Hub', 'bilingual', 'bhub',
     hero_video(mp4, poster, 'Bilingual Initiatives', 'Bilingual Hub',
                'Teaching is my passion — making English fun &amp; meaningful for every child.'),
     bhub_body, "Teacher Mari's bilingual initiatives at Nanhsing: Morning Assembly, English Corner, English Club, and Reading Class.")

# ---- MORNING ASSEMBLY ----
mp4, poster = vid('bilingual_morning-assembly', '02')
ma_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">🎤🌟 Morning Assembly English Time 🌟🎤</div><h2 class="sec">English for the whole school</h2></div>
  <p class="lead reveal" style="max-width:820px;margin:0 auto 30px;text-align:center">Once a week during our Morning Assembly, everyone gathers in the assembly area for a fun English activity. We introduce the <b>Words of the Week</b> and <b>Sentence of the Week</b> to students and teachers alike — a great way to practice together, build confidence, and create a supportive English-learning environment across the whole school.
  <span class="zh">每週一次的晨會英語時間，全校師生一起在集合場玩英語：介紹「每週單字」與「每週一句」，一起練習、建立自信，打造支持彼此的英語學習環境。</span></p>
  {gallery_block(gallery_imgs('bilingual_morning-assembly', idxrange(4,25)))}
</div></section>
<div class="ribbon reveal">Learning + Playing = Happy English Learners <span class="heart">💚</span></div>'''
page('bilingual-hub/morning-assembly/index.html', 'Morning Assembly', 'bilingual', 'morning',
     hero_video(mp4, poster, 'Morning Assembly', 'Morning Assembly English Time'),
     ma_body, "Weekly whole-school Morning Assembly English Time at Nanhsing: Words of the Week and Sentence of the Week.")

# ---- ENGLISH CORNER ----
mp4, poster = vid('bilingual_english-corner', '02')
ec_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">📚✨ English Corner Fun! ✨📚</div><h2 class="sec">Letter by letter, word by word</h2></div>
  <p class="lead reveal" style="max-width:820px;margin:0 auto 30px;text-align:center">At our English Corner, learning becomes a fun adventure! Each session we explore a special letter and discover new words that start with it. Through games, pictures, and interactive activities, the kids learn while playing. From <b>"A is for Apple"</b> to <b>"B is for Ball,"</b> our students build their vocabulary step by step — smiling, laughing, and growing more confident in English every day!
  <span class="zh">在英語角，學習就是一場有趣的冒險！每次認識一個字母、發現以它開頭的單字，透過遊戲、圖片與互動活動邊玩邊學，從 A is for Apple 到 B is for Ball，一步步累積字彙與自信。</span></p>
  <div class="sec-head reveal" style="margin-top:18px"><h2 class="sec" style="font-size:24px">Our letter lessons</h2></div>
  {slides_block(gallery_imgs('bilingual_english-corner', idxrange(6,17)))}
</div></section>
<section class="block tint"><div class="wrap">
  <div class="sec-head reveal"><h2 class="sec">Fun in action</h2></div>
  {gallery_block(gallery_imgs('bilingual_english-corner', idxrange(19,29)))}
</div></section>'''
page('bilingual-hub/english-corner/index.html', 'English Corner', 'bilingual', 'corner',
     hero_video(mp4, poster, 'English Corner', 'English Corner Fun!'),
     ec_body, "English Corner at Nanhsing: exploring letters and vocabulary through games and pictures.")

# ---- ENGLISH CLUB ----
mp4, poster = vid('bilingual_english-club', '02')
club_idxs = idxrange(7,29) + idxrange(31,52)
club_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">📚 Remedial Class</div><h2 class="sec">English Club</h2>
  <p>Extra time, extra care — small-group practice that helps every learner catch up and shine. 小班補救教學，陪每個孩子打好基礎、發光發亮。</p></div>
  {gallery_block(gallery_imgs('bilingual_english-club', club_idxs))}
</div></section>
<div class="ribbon reveal">Learning + Playing = Happy English Learners <span class="heart">💚</span></div>'''
page('bilingual-hub/english-club/index.html', 'English Club', 'bilingual', 'club',
     hero_video(mp4, poster, 'English Club', 'Remedial Class'),
     club_body, "Teacher Mari's English Club at Nanhsing — small-group remedial English practice.")

# ---- READING CLASS ----
mp4, poster = vid('bilingual_reading-class', '02')
read_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">Reading Class</div><h2 class="sec">One story at a time</h2></div>
  <p class="lead reveal" style="max-width:820px;margin:0 auto 30px;text-align:center">Our Reading Class for <b>Grades 3 and 4</b> helps students build a strong foundation in English. They learn basic vocabulary, simple sentences, and enjoy short stories that are easy to understand. Through these stories, students not only improve their reading skills but also learn important values like kindness, respect, and responsibility. Learning to read, understand, and grow — one story at a time! 🌟📚
  <span class="zh">三、四年級的閱讀課幫助學生打好英語基礎：學習基本字彙、簡單句型，享受好讀的短篇故事。透過故事，孩子不只提升閱讀力，也學會善良、尊重與負責等重要價值。一次一個故事，閱讀、理解、成長！</span></p>
  {gallery_block(gallery_imgs('bilingual_reading-class', idxrange(4,31)))}
</div></section>'''
page('bilingual-hub/reading-class/index.html', 'Reading Class', 'bilingual', 'reading',
     hero_video(mp4, poster, 'Reading Class', 'Reading Class'),
     read_body, "Reading Class for Grades 3 and 4 at Nanhsing — vocabulary, simple sentences, and short stories with values.")

# ---- GAME HUB ----
mp4, poster = vid('game-hub', '02')
game_body = f'''<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div class="sec-eyebrow">🎮 Game Hub</div><h2 class="sec">Where learning meets fun</h2></div>
  <p class="lead reveal" style="max-width:820px;margin:0 auto 26px;text-align:center">Welcome to our Game Hub — where learning meets fun! Here, students can play interactive games based on the lessons we've learned in class, both in school and right here on the website. These games help reinforce vocabulary, practice sentence patterns, and build confidence in English in an exciting, engaging way. Play, learn, and enjoy English anytime, anywhere!
  <span class="zh">歡迎來到遊戲區！這裡有依照課堂內容設計的互動遊戲，無論在學校或在這個網站都能玩。透過遊戲複習單字、練習句型、建立英語自信——隨時隨地，邊玩邊學！</span></p>
  <div class="feature reveal" style="max-width:760px"><img src="{img('game-hub','04')}" alt="Game Hub"></div>
  <div class="gamezone reveal" style="margin-top:34px">
    <div class="big">🕹️ Let's Play!</div>
    <p style="font-size:18px;margin:10px auto 0;max-width:560px">Interactive vocabulary games run in class and on the original site. Ready to practice your English the fun way?</p>
    <a class="pill" href="https://www.twrses.org/" target="_blank" rel="noopener">Explore more English resources →</a>
    <p class="credit-note">This game is credited to <b>Teacher Zandra</b> from VNwithZan. Just edited a few. 🙏</p>
  </div>
</div></section>'''
page('game-hub/index.html', 'Game Hub', 'game', 'game',
     hero_video(mp4, poster, "Let's Play", 'Game Hub', 'by Teacher Mari'),
     game_body, "Teacher Mari's Game Hub — interactive English games that reinforce vocabulary and sentence patterns.")

print('\nDONE — 11 pages generated.')
