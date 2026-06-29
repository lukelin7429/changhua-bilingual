#!/usr/bin/env python3
# Generates the Poem Tree signature-course learning page.
import os, html
ROOT = os.path.dirname(os.path.abspath(__file__))

def esc(s): return html.escape(s, quote=True)

VOCAB = [
    ("poem","n.","詩"),("tree","n.","樹"),("special","adj.","特殊的"),
    ("amazing","adj.","奇妙的；很棒的"),("story","n.","故事"),
    ("writing","n.","寫作；文章"),("writer","n.","作家"),
    ("used to","phr.","以前（曾經）做…"),("remember","v.","記得"),("history","n.","歷史"),
]
SENTS = [
    ("She wrote a poem about the sea.","她寫了一首關於大海的詩。"),
    ("There is a tall tree in our garden.","我們花園裡有一棵高大的樹。"),
    ("This is a special gift for your birthday.","這是給你生日的特殊禮物。"),
    ("The magic show was amazing.","魔術表演真的很奇妙。"),
    ("My grandmother tells the best stories.","我奶奶講的故事最棒。"),
    ("Tom's writing is about his cat.","湯姆的文章是關於他的貓。"),
    ("She wants to become a famous writer.","她想成為一名著名的作家。"),
    ("I used to play piano when I was young.","我小時候常彈鋼琴。"),
    ("Remember to turn off the lights.","記得關燈。"),
    ("We learned about ancient history in school.","我們在學校學習了古代歷史。"),
]
LISTEN_EN = ("Have you ever heard of a tree with stories on it? Chungshan Elementary School has a very special "
    "tree called the Poem Tree. This tree has poems and writings from 12 writers on it. These writers all "
    "used to go to this school. The Poem Tree helps us remember the school's history and the stories of these "
    "writers. One of the most famous writers on the tree is Lai He, a renowned Taiwanese author. The Poem Tree "
    "is a symbol of the school's pride in its heritage. It's a reminder of the importance of literature and the "
    "arts. The Poem Tree is a unique part of Chungshan Elementary School's history.")
LISTEN_ZH = ("你聽過一棵上面有故事的樹嗎？中山國小有一棵非常特別的樹，叫做詩文樹。樹上刻著十二位作家的詩與文章，"
    "這些作家都曾是這所學校的學生。詩文樹幫助我們記住學校的歷史，以及這些作家的故事。樹上最著名的作家之一是賴和，"
    "一位享譽盛名的台灣作家。詩文樹是學校對自身文化傳承引以為傲的象徵，提醒我們文學與藝術的重要，是中山國小歷史中獨一無二的一部分。")

POETS = [
 ("施至善","Shih Zhi-Shan","1881–?","A member of the Taiwan Cultural Association and a trailblazer of the new cultural movement; with Lai He and Wang Min-Chuan he was hailed as one of the “Three Pillars of Changhua.”","參與「台灣文化協會」，為新文化運動的開路者，與賴和、王敏川並稱「彰化三支柱」。"),
 ("黃呈聰","Huang Cheng-Tsung","1886–1963","Also known as Jian Ru; an early activist in anti-colonial and enlightenment movements and a pioneer of the vernacular-Chinese movement.","號劍如，早年投入抗日與文化啟蒙運動，為白話文運動的開路先鋒。"),
 ("吳上花","Wu Shang-Hua","1893–?","Nephew of the Changhua scholar Wu De-Gong; deeply versed in Classical Chinese and instrumental in founding the Chong Wen Society, the first literary society of the colonial era.","彰化碩儒吳德功之姪，漢文根基深厚，擅詩文，有功於日治第一個文社「崇文社」的創立。"),
 ("賴和","Lai He","1894–1943","The most emblematic figure of the Taiwanese spirit in the Japanese era and the leader who drove the flourishing of new Taiwanese literature — revered as the “Father of Taiwan’s New Literature.”","日本時代最具台灣精神的人物，帶動台灣新文學蓬勃發展，被尊為「台灣新文學之父」。"),
 ("楊宗城","Yang Zong-Cheng","1894–?","Styled Geng-Yun; studied Classical Chinese as a youth and joined Changhua's Ying poetry society; his collection Yi Yuan Shi Cao survives in an anthology.","字耕雲，幼習漢文，參與彰化舊詩社「應社」，詩作《逸園詩草》傳世。"),
 ("陳滿盈","Chen Man-Ying","1896–1965","Pen name Xu-Gu; a master of traditional Chinese poetry whose plain, tranquil verse on rural life sought harmony between people and nature.","字虛谷，傳統漢詩成就最高，文字素樸恬淡，題詠田野山水，追求人與自然的融合。"),
 ("黃朝琴","Huang Chao-Qin","1897–1972","Promoted national consciousness through the Taiwan People's Newspaper and championed the Taiwanese vernacular movement; postwar, the first Speaker of the Taiwan Provincial Parliament.","曾於《台灣民報》鼓吹民族思想，提倡台灣白話文運動，戰後任台灣省參議會首任議長。"),
 ("黃周","Huang Zhou","1899–1957","Known as Xing Min; his current-affairs essays carried moral lessons while his light prose was prized for its clarity — an intellectual devoted to awakening the public.","號醒民，時論寓教於文，小品清雋有味，以警醒民眾、振興文化自期。"),
 ("石錫動","Shi Xi-Dong","1900–1985","Styled Yi-Nan; grounded in classical poetry from childhood, he co-founded the “Flowing Thoughts Club” with Lai He and Chen Xu-Gu.","字逸南，自幼奠定傳統詩詞根基，與賴和、陳虛谷等創設「流連思索俱樂部」。"),
 ("楊松茂","Yang Song-Mao","1905–1959","Pen name Shou Yu; close to Lai He and shaped by him, his fighting, critical works spoke up for farmers and workers — the most prolific Chinese-language novelist of the colonial era.","筆名守愚，與賴和交厚並受其影響，作品充滿鬥志與批判，常為農工仗義執言，是日治時代中文小說創作最多者。"),
 ("賴賢穎","Lai Xian-Ying","1910–1981","Lai He's fifth brother; his novels and essays centered on farmers and explored the hardships of peasant life.","賴和五弟，小說與隨筆多以農民為主角，探討農民生活的疾苦。"),
 ("吳慶堂","Wu Qing-Tang","1911–1995","An avant-garde talent skilled in poetry, painting, drama, and photography; hardship and turbulent times lend his work a melancholy tone.","能詩能畫，亦擅戲劇與攝影，堪稱前衛青年；生活困頓與時代動盪，使作品常帶低抑愁鬱。"),
]

WORKS = [
 ("Yang Song-Mao","楊松茂",
  ["你別咀咒人生，你別怨嘆薄命；","要知現社會下的青年，誰不和你同病；","悲有何用，哭尤無異；","唯願向萬惡的社會，準備著猛烈的攻擊。"],
  ["Do not curse life, do not lament your fate;","Know that among the youth of this society, who does not share your plight?","What use is sorrow? Crying changes nothing;","I wish only to strike fiercely against this wicked world."]),
 ("Lai Xian-Ying","賴賢穎",
  ["鄉村的夜晚是夢般寂靜的，","然而沒有了狗吠的鄉村的夜，","更是沈靜——","幾乎令人要以為一切全皆死寂了。"],
  ["The village night is silent as a dream;","yet a country night without even the barking of dogs","is more silent still —","almost making you believe all the world has gone still."]),
 ("Huang Cheng-Tsung","黃呈聰",
  ["牧者為著羊兒發那樣的慈愛呢？","是慈悲心真的發露嗎？","究竟牧者為羊而存呢？","還是羊為牧者而存呢？"],
  ["Why does the shepherd show the lambs such tenderness?","Is it truly compassion welling up?","Does the shepherd exist for the sheep —","or the sheep for the shepherd?"]),
 ("Chen Man-Ying","陳滿盈（虛谷）",
  ["春來人歡樂，春去人寂寞，","來去無人知，但見花開落。"],
  ["When spring comes, people rejoice; when spring goes, they grieve.","Its coming and going pass unnoticed — only the flowers are seen to bloom and fall."]),
 ("Huang Chao-Qin","黃朝琴",
  ["中國的不進步，不能追隨天下，","亦皆教育不播及，","教育不普及皆在漢文字的難記。"],
  ["That China does not advance, that it cannot keep pace with the world,","is because education has not spread;","and education fails to spread because Chinese characters are so hard to memorize."]),
 ("Huang Zhou","黃周",
  ["魚類生於水中的動物，離了水就不能棲息，","然則魚在水中，就是被他們的命運所拘束的傀儡嗎？"],
  ["Fish are creatures born in the water; out of it they cannot live.","So are fish in the water merely puppets bound by their fate?"]),
]

def say_btn(text):
    return f'<button class="say" data-say="{esc(text)}" aria-label="Listen">🔊</button>'

CSS = """
.bt-back{display:inline-block;margin:22px 0 2px;font-weight:700;color:var(--green-deep);}
.bt-back:hover{color:var(--gold-deep);}
.intro-lead{font-family:'Playfair Display',serif;font-size:26px;color:var(--green-deep);font-weight:700;line-height:1.4;}
@media(min-width:720px){.intro-lead{font-size:32px;}}
.pt-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:8px;}
@media(min-width:680px){.pt-grid{grid-template-columns:repeat(3,1fr);}}
@media(min-width:980px){.pt-grid{grid-template-columns:repeat(5,1fr);}}
.ptv{background:#fff;border:1px solid var(--line);border-top:5px solid var(--gold);border-radius:14px;padding:16px 16px 18px;box-shadow:var(--shadow-sm);transition:transform .2s,box-shadow .2s;}
.ptv:nth-child(5n+2){border-top-color:var(--green);}.ptv:nth-child(5n+3){border-top-color:var(--brick);}
.ptv:nth-child(5n+4){border-top-color:#7048a6;}.ptv:nth-child(5n+5){border-top-color:#0c7b86;}
.ptv:hover{transform:translateY(-4px);box-shadow:var(--shadow);}
.ptv__term{font-family:'Playfair Display',serif;font-size:22px;font-weight:700;color:var(--green-deep);line-height:1.15;}
.ptv__pos{font-size:.6em;color:var(--gold-deep);font-style:italic;margin-left:3px;}
.ptv__zh{font-size:16px;color:var(--ink);font-weight:600;margin-top:4px;}
.ptv .say{margin-top:10px;}
.pt-sents{display:flex;flex-direction:column;gap:12px;margin-top:6px;}
.pts{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid var(--line);border-left:5px solid var(--green);border-radius:12px;padding:14px 18px;box-shadow:var(--shadow-sm);}
.pts:nth-child(even){border-left-color:var(--gold);}
.pts .say{flex:0 0 auto;margin-top:2px;}
.pts__en{font-size:19px;font-weight:600;color:var(--ink);line-height:1.5;}
.pts__zh{font-size:16px;color:var(--ink-soft);margin-top:5px;line-height:1.5;}
.pt-listen{background:linear-gradient(135deg,var(--green-soft),var(--gold-soft));border:1px solid var(--line);border-radius:18px;padding:26px 28px;box-shadow:var(--shadow-sm);}
.pt-listen .row{display:flex;gap:12px;align-items:flex-start;}
.pt-listen .say{flex:0 0 auto;}
.pt-listen p.en{font-size:19px;line-height:1.7;color:var(--ink);font-weight:500;}
@media(min-width:720px){.pt-listen p.en{font-size:21px;}}
.pt-listen p.zh{font-size:16px;line-height:1.75;color:var(--ink-soft);margin-top:16px;padding-top:16px;border-top:1px dashed var(--line);}
.poets{display:grid;grid-template-columns:1fr;gap:16px;margin-top:6px;}
@media(min-width:640px){.poets{grid-template-columns:1fr 1fr;}}
@media(min-width:980px){.poets{grid-template-columns:1fr 1fr 1fr;}}
.poet{background:#fff;border:1px solid var(--line);border-top:6px solid var(--accent,var(--gold));border-radius:16px;padding:20px 22px 22px;box-shadow:var(--shadow-sm);transition:transform .2s,box-shadow .2s;}
.poet:nth-child(6n+1){--accent:#3c4587;}.poet:nth-child(6n+2){--accent:#b3812f;}.poet:nth-child(6n+3){--accent:#b3472f;}
.poet:nth-child(6n+4){--accent:#7048a6;}.poet:nth-child(6n+5){--accent:#0c7b86;}.poet:nth-child(6n+6){--accent:#c0517a;}
.poet:hover{transform:translateY(-5px);box-shadow:0 22px 40px -18px var(--accent);}
.poet__name{font-family:'Playfair Display',serif;font-size:23px;font-weight:700;color:var(--green-deep);line-height:1.1;}
.poet__zh{font-family:'PingFang TC',sans-serif;font-size:18px;color:var(--ink);font-weight:600;margin-top:2px;}
.poet__dates{font-size:13px;color:var(--accent,var(--gold-deep));font-weight:700;letter-spacing:.05em;margin-top:6px;}
.poet__bio{font-size:16px;color:var(--ink-soft);margin-top:10px;line-height:1.6;}
.poet__bio .zh{display:block;color:var(--ink-soft);margin-top:6px;}
.poems{display:grid;grid-template-columns:1fr;gap:22px;margin-top:6px;}
@media(min-width:820px){.poems{grid-template-columns:1fr 1fr;}}
.poem{background:#fff;border:1px solid var(--line);border-left:6px solid var(--brick);border-radius:16px;padding:24px 26px 26px;box-shadow:var(--shadow-sm);}
.poem:nth-child(3n+2){border-left-color:var(--green);}.poem:nth-child(3n){border-left-color:var(--gold);}
.poem__zh{font-family:'Playfair Display','PingFang TC',serif;font-size:20px;color:var(--green-deep);line-height:1.9;font-weight:600;}
.poem__en{font-size:17px;color:var(--ink);line-height:1.7;margin-top:14px;padding-top:14px;border-top:1px dashed var(--line);font-style:italic;}
.poem__by{display:flex;align-items:center;gap:10px;margin-top:14px;font-family:'Playfair Display',serif;font-weight:700;color:var(--brick);font-size:16px;}
.say{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;flex:0 0 auto;border:none;border-radius:50%;background:var(--gold-soft);color:var(--gold-deep);font-size:15px;cursor:pointer;transition:transform .15s,background .15s;}
.say:hover{background:var(--gold);color:#fff;transform:scale(1.12);}
.say:active{transform:scale(.94);}
"""

SAY = ("<script>(function(){function speak(t){try{speechSynthesis.cancel();var u=new SpeechSynthesisUtterance(t);"
       "u.lang='en-US';u.rate=.9;speechSynthesis.speak(u);}catch(e){}}"
       "document.addEventListener('click',function(e){var b=e.target.closest('.say');if(b){speak(b.getAttribute('data-say'));}});})();</script>")

TB = ('<div class="tb"><div class="tb__inner"><a class="tb__brand" href="/schools/chungshan/">'
      '<img class="tb__logo" src="/schools/chungshan/favicon-192.png" alt="Chungshan crest 中山國小校徽"><div class="tb__name">Chungshan Elementary<small>彰化市中山國小</small></div></a>'
      '<nav class="tb__nav"><a href="/schools/chungshan/">Home</a><a href="/schools/chungshan/principal/">Principal</a>'
      '<a href="/schools/chungshan/lessons/" class="is-active">Lessons</a><a href="/schools/chungshan/news/">News</a><a href="/schools/chungshan/festivals/">Festivals</a></nav></div></div>')

FOOT = ('<footer class="ft"><div class="ft__inner"><div class="ft__brand"><img class="ft__logo" src="/schools/chungshan/favicon-192.png" alt="Chungshan crest 中山國小校徽"><div>'
        '<h4>Chungshan Elementary School</h4><div class="zh">彰化縣彰化市中山國民小學</div>'
        '<div class="ft__addr">50042 彰化縣彰化市中山路二段 678 號<br>Tel · 電話：(04) 722-2033</div></div></div>'
        '<div class="ft__col"><h5>This Site</h5><ul><li><a href="/schools/chungshan/">Home · 首頁</a></li>'
        '<li><a href="/schools/chungshan/lessons/">Lessons · 每日一字</a></li>'
        '<li><a href="/schools/chungshan/news/">News · 最新消息</a></li></ul></div>'
        '<div class="ft__col"><h5>Connect</h5><div class="ft-ctas">'
        '<a class="cta-btn" href="https://cses.chc.edu.tw/" target="_blank" rel="noopener"><span class="cta-btn__ico">🌐</span>'
        '<span class="cta-btn__tx"><span class="cta-btn__t">Official Website</span><span class="cta-btn__zh">中山國小官網</span></span><span class="cta-btn__arrow">↗</span></a></div></div></div>'
        '<div class="ft__bottom">Site by <a href="https://www.mycultureconnect.org/" target="_blank" rel="noopener">My Culture Connect</a> '
        '<a href="https://www.twrses.org/" target="_blank" rel="noopener">人師教育協會</a><br>'
        'Guided by <a href="https://www.cieetrc.chc.edu.tw/" target="_blank" rel="noopener">CIEETRC 彰化縣國際教育暨英語教育資源中心</a><br>'
        '<a href="https://changhua-bilingual.org/" target="_blank" rel="noopener">Changhua Bilingual Hub 彰化雙語資源網</a></div></footer>')

# build sections
vocab_html = ''.join(
    f'<div class="ptv"><div class="ptv__term">{esc(t)}<span class="ptv__pos">{esc(p)}</span></div>'
    f'<div class="ptv__zh">{esc(zh)}</div>{say_btn(t)}</div>' for t,p,zh in VOCAB)

sents_html = ''.join(
    f'<div class="pts">{say_btn(en)}<div><div class="pts__en">{esc(en)}</div><div class="pts__zh">{esc(zh)}</div></div></div>'
    for en,zh in SENTS)

poets_html = ''.join(
    f'<div class="poet"><div class="poet__name">{esc(en)}</div><div class="poet__zh">{esc(zh)}</div>'
    f'<div class="poet__dates">{esc(dates)}</div>'
    f'<div class="poet__bio">{esc(bio_en)}<span class="zh">{esc(bio_zh)}</span></div></div>'
    for zh,en,dates,bio_en,bio_zh in POETS)

poems_html = ''.join(
    f'<div class="poem"><div class="poem__zh">{"<br>".join(esc(l) for l in zh_lines)}</div>'
    f'<div class="poem__en">{"<br>".join(esc(l) for l in en_lines)}</div>'
    f'<div class="poem__by">{say_btn(" ".join(en_lines))} — {esc(en)} · {esc(zh)}</div></div>'
    for en,zh,zh_lines,en_lines in WORKS)

H = []
H.append('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">')
H.append('<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')
H.append('<link rel="canonical" href="https://changhua-bilingual.org/schools/chungshan/lessons/poem-tree/">')
H.append('<title>The Poem Tree · 詩文樹 · Chungshan Elementary</title>')
H.append('<meta name="description" content="Chungshan\'s signature course: the Poem Tree. Meet twelve literary alumni — including Lai He — read their poems with English translations, learn key words and sentences, and listen along. 中山國小特色課程 詩文樹。">')
H.append('<link rel="icon" type="image/png" sizes="32x32" href="/schools/chungshan/favicon-32.png"><link rel="icon" type="image/png" sizes="192x192" href="/schools/chungshan/favicon-192.png"><link rel="apple-touch-icon" sizes="180x180" href="/schools/chungshan/favicon-180.png"><link rel="shortcut icon" href="/schools/chungshan/favicon.ico">')
H.append('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
H.append('<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')
H.append('<link rel="stylesheet" href="/schools/chungshan/style.css"><link rel="stylesheet" href="/assets/css/motion.css">')
H.append(f'<style>{CSS}</style></head><body>')
H.append(TB)
H.append('<header class="chero is-photo" style="--photo:url(/schools/chungshan/photos/news-banner.jpg);"><div class="chero__inner">'
         '<span class="eyebrow">Signature Course · 特色課程</span><h1>The Poem Tree</h1>'
         '<div class="h1-zh">詩文樹 · 彰化文學家的搖籃</div></div><div class="scrollcue" aria-hidden="true">⌄</div></header>')

# Intro + video
H.append('<section><div class="wrap"><a class="bt-back" href="../">← Back to Lessons · 回課程</a>'
         '<div class="sec__no" style="margin-top:14px;">I.</div><h2 class="sec__title">A Tree of Stories</h2>'
         '<div class="sec__title-zh">一棵長滿故事的樹</div><div class="sec__rule"></div>'
         '<p class="intro-lead">Chungshan Elementary has a very special tree called the Poem Tree.</p>'
         '<div class="body"><p>This tree is amazing because it has stories on it. It carries poems and writings from '
         '<strong>twelve writers</strong>, and these writers all used to study at this school. The Poem Tree helps us '
         'remember the school’s history — and the stories of these writers.</p>'
         '<p class="zh">中山國小有一棵非常特別的樹，叫做<strong>詩文樹</strong>。樹上刻著<strong>十二位作家</strong>的詩和文章，'
         '這些作家都曾是這所學校的學生。詩文樹幫助我們記住學校的歷史，以及這些作家的故事。</p></div>'
         '<div class="player"><div class="player__ratio"><iframe src="https://www.youtube-nocookie.com/embed/UrCeIk85t-w?rel=0" '
         'title="The Poem Tree 詩文樹" loading="lazy" allowfullscreen></iframe></div>'
         '<div class="player__cap">▶ Watch: The Poem Tree · 詩文樹介紹短片</div></div></div></section>')

# Vocabulary
H.append('<section><div class="wrap"><div class="sec__no">II.</div><h2 class="sec__title">Key Words</h2>'
         '<div class="sec__title-zh">關鍵字 · 點 🔊 聽發音</div><div class="sec__rule"></div>'
         f'<div class="pt-grid">{vocab_html}</div></div></section>')

# Sentences
H.append('<section><div class="wrap"><div class="sec__no">III.</div><h2 class="sec__title">Example Sentences</h2>'
         '<div class="sec__title-zh">例句 · 點 🔊 跟著唸</div><div class="sec__rule"></div>'
         f'<div class="pt-sents">{sents_html}</div></div></section>')

# Advanced listening
H.append('<section><div class="wrap"><div class="sec__no">IV.</div><h2 class="sec__title">Advanced Listening</h2>'
         '<div class="sec__title-zh">進階聽力 · 完整短文朗讀</div><div class="sec__rule"></div>'
         f'<div class="pt-listen"><div class="row">{say_btn(LISTEN_EN)}<p class="en">{esc(LISTEN_EN)}</p></div>'
         f'<p class="zh">{esc(LISTEN_ZH)}</p></div></div></section>')

# Writers
H.append('<section><div class="wrap"><div class="sec__no">V.</div><h2 class="sec__title">The Twelve Writers</h2>'
         '<div class="sec__title-zh">詩文樹上的十二位文學家校友</div><div class="sec__rule"></div>'
         f'<div class="poets">{poets_html}</div></div></section>')

# Poems
H.append('<section><div class="wrap"><div class="sec__no">VI.</div><h2 class="sec__title">Poems from the Tree</h2>'
         '<div class="sec__title-zh">樹上的詩文 · 原文與英譯（點 🔊 聽英文）</div><div class="sec__rule"></div>'
         f'<div class="poems">{poems_html}</div>'
         '<a class="bt-back" href="../" style="margin-top:34px;">← Back to Lessons · 回課程</a></div></section>')

H.append(SAY + FOOT + '<script defer src="/assets/js/motion.js"></script></body></html>')

os.makedirs(os.path.join(ROOT, 'lessons', 'poem-tree'), exist_ok=True)
open(os.path.join(ROOT, 'lessons', 'poem-tree', 'index.html'), 'w').write('\n'.join(H))
print('Poem Tree page built:', len(VOCAB), 'words,', len(SENTS), 'sentences,', len(POETS), 'writers,', len(WORKS), 'poems')
