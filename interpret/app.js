/* 口譯練習室 Interpreting Lab — a phone-first quiz app for interpreting
 * between Mandarin and English in a county English office.
 *
 * Six modules, all multiple choice with one standard answer. Question banks
 * live in data/m1..m6.json. The correct answer is always written FIRST in the
 * JSON (a[0]); options are shuffled on every showing, so the right answer
 * lands evenly on A–D.
 *
 * Progress is kept in localStorage on this device only (key "cip-v1").
 * English 🔊 goes through speechSynthesis, which /assets/js/voice.js swaps
 * for natural-voice clips when one exists (audio/manifest/interpret.json).
 */
(function () {
  'use strict';

  var MODULES = [
    { id: 'm1', emoji: '🎧', title: '情境口譯', en: 'Scenario Interpreting', color: '#1a4791', soft: '#dbe3f0',
      desc: '外師業務八大情境：先自己開口說說看，再選出最好的譯法。' },
    { id: 'm2', emoji: '🗂️', title: '行政詞彙', en: 'Admin Terms', color: '#0f7a6a', soft: '#d6efe9',
      desc: '居留證、補休、議課、職務代理人等台灣教育行政用語，中英互譯。' },
    { id: 'm3', emoji: '🔍', title: '中式英文診斷', en: 'Chinglish Check', color: '#c2410c', soft: '#fde4d3',
      desc: '「辛苦了」「請配合」「原則上」怎麼說才自然？選出最道地的一句。' },
    { id: 'm4', emoji: '👂', title: '外師口語', en: 'FET Talk', color: '#7c3aed', soft: '#ece3fd',
      desc: '聽懂 swamped、heads-up、on the fence 這類課本不教的口語。' },
    { id: 'm5', emoji: '✉️', title: '訊息改寫', en: 'LINE & Email', color: '#a06c10', soft: '#feeed0',
      desc: '同一件事三種寫法，選出語氣最得體、資訊最清楚的訊息。' },
    { id: 'm6', emoji: '🌏', title: '文化解說', en: 'Culture Bridge', color: '#be185d', soft: '#fce1ee',
      desc: '用英文解釋普渡、尾牙、午休；用中文幫校長理解感恩節、potluck。' }
  ];
  var MOD = {}; MODULES.forEach(function (m) { MOD[m.id] = m; });
  var ROUND = 10;                 // questions per mixed round
  var KEY = 'cip-v1';
  var app = document.getElementById('app');
  var banks = {};                 // module id -> json

  /* ---------- storage ---------- */
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  var st = load();
  st.seen = st.seen || {}; st.wrong = st.wrong || []; st.best = st.best || {}; st.days = st.days || [];
  function save() { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} }
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function markDay() {
    var t = today();
    if (st.days.indexOf(t) < 0) { st.days.push(t); if (st.days.length > 400) st.days.shift(); }
  }
  function streak() {
    var n = 0, d = new Date();
    for (;;) {
      var k = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
      if (st.days.indexOf(k) >= 0) n++;
      else if (n > 0 || k !== today()) break;
      d.setDate(d.getDate() - 1);
    }
    return n;
  }

  /* ---------- data ---------- */
  function fetchBank(id) {
    if (banks[id]) return Promise.resolve(banks[id]);
    return fetch('data/' + id + '.json').then(function (r) { return r.json(); })
      .then(function (j) { banks[id] = j; return j; });
  }
  function allBanks() { return Promise.all(MODULES.map(function (m) { return fetchBank(m.id); })); }

  // Every question becomes {id, mod, set, dir, p, a[], n, x[], ex}
  function questionsOf(bank, setId) {
    var out = [];
    bank.sets.forEach(function (s) {
      if (setId && s.id !== setId) return;
      if (s.qs) s.qs.forEach(function (q, i) {
        out.push({ id: bank.id + '.' + s.id + '.' + i, mod: bank.id, set: s.id, dir: q.dir, p: q.p, a: q.a, n: q.n, x: q.x || [] });
      });
      if (s.terms) s.terms.forEach(function (t, i) { out.push(termQuestion(bank.id, s, t, i)); });
    });
    return out;
  }
  // Vocabulary: direction chosen per showing; distractors from the same set.
  function termQuestion(mid, s, t, i) {
    var dir = Math.random() < 0.5 ? 'ze' : 'ez';
    var pool = shuffle(s.terms.filter(function (o) { return o !== t; })).slice(0, 3);
    return {
      id: mid + '.' + s.id + '.' + i, mod: mid, set: s.id, dir: dir, term: true,
      p: dir === 'ze' ? t.zh : t.en,
      a: [dir === 'ze' ? t.en : t.zh].concat(pool.map(function (o) { return dir === 'ze' ? o.en : o.zh; })),
      n: (t.zh + '＝' + t.en) + (t.n ? '。' + t.n : ''), x: [], ex: t.ex
    };
  }
  function byId(id) {
    var parts = id.split('.'), bank = banks[parts[0]];
    if (!bank) return null;
    var qs = questionsOf(bank, parts[1]);
    for (var i = 0; i < qs.length; i++) if (qs[i].id === id) return qs[i];
    return null;
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  /* ---------- speech ---------- */
  var synth = window.speechSynthesis;
  function zhVoice() {
    if (!synth) return null;
    var vs = synth.getVoices();
    return vs.filter(function (v) { return /zh[-_]TW/i.test(v.lang); })[0] ||
           vs.filter(function (v) { return /^zh/i.test(v.lang); })[0] || null;
  }
  function say(text, lang) {
    if (!synth) return;
    synth.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = lang === 'zh' ? 'zh-TW' : 'en-US';
    u.rate = lang === 'zh' ? 0.95 : 0.92;
    if (lang === 'zh') { var v = zhVoice(); if (v) u.voice = v; }
    synth.speak(u);
  }
  var Rec = window.SpeechRecognition || window.webkitSpeechRecognition;

  /* ---------- helpers ---------- */
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function langOfPrompt(q) { return q.dir === 'ze' ? 'zh' : 'en'; }
  function langOfAnswer(q) { return q.dir === 'ze' ? 'en' : 'zh'; }
  function setTheme(m) {
    document.documentElement.style.setProperty('--mod', m ? m.color : '#1a4791');
    document.documentElement.style.setProperty('--mod-soft', m ? m.soft : '#dbe3f0');
  }
  function modStats(mid) {
    var c = 0, seen = 0;
    Object.keys(st.seen).forEach(function (k) {
      if (k.indexOf(mid + '.') === 0) { seen++; if (st.seen[k].c > 0) c++; }
    });
    return { seen: seen, mastered: c };
  }
  function bankSize(mid) { var b = banks[mid]; return b ? questionsOf(b).length : 0; }
  function speakBtn(text, lang, label) {
    return '<button class="spk" data-say="' + esc(text) + '" data-lang="' + lang + '" aria-label="播放">🔊' + (label ? ' <span>' + label + '</span>' : '') + '</button>';
  }
  app.addEventListener('click', function (e) {
    var b = e.target.closest('[data-say]');
    if (b) { e.preventDefault(); say(b.getAttribute('data-say'), b.getAttribute('data-lang')); }
  });

  /* ---------- views ---------- */
  function home() {
    setTheme(null);
    var total = 0, answered = 0, right = 0;
    Object.keys(st.seen).forEach(function (k) { answered += st.seen[k].c + st.seen[k].w; right += st.seen[k].c; });
    MODULES.forEach(function (m) { total += bankSize(m.id); });
    var acc = answered ? Math.round(right * 100 / answered) + '%' : '—';
    var h = '<header class="hero"><div class="hero-in">' +
      '<p class="eyebrow">CIEETRC · Interpreting Lab</p>' +
      '<h1>口譯練習室</h1>' +
      '<p class="lede">為外師業務量身打造的中英口譯練習：每天十題，越用越順口。</p>' +
      '</div></header>' +
      '<section class="stats reveal">' +
      '<div><b>' + streak() + '</b><span>連續天數</span></div>' +
      '<div><b>' + answered + '</b><span>累計作答</span></div>' +
      '<div><b>' + acc + '</b><span>答對率</span></div></section>' +
      '<section class="quick reveal">' +
      '<a class="btn primary" href="#/mix">🎲 今日十題（六單元綜合）</a>' +
      (st.wrong.length ? '<a class="btn ghost" href="#/wrong">📕 錯題本（' + st.wrong.length + '）</a>' : '') +
      '</section><h2 class="sec">六個單元 <small>都試試看，再告訴我們哪些最有用</small></h2><section class="mods">';
    MODULES.forEach(function (m, i) {
      var s = modStats(m.id), n = bankSize(m.id), pct = n ? Math.round(s.mastered * 100 / n) : 0;
      h += '<a class="mod reveal" style="--c:' + m.color + ';--s:' + m.soft + ';--d:' + (i * 60) + 'ms" href="#/m/' + m.id + '">' +
        '<span class="mod-emoji">' + m.emoji + '</span>' +
        '<span class="mod-tag">Module ' + (i + 1) + ' · ' + m.en + '</span>' +
        '<span class="mod-title">' + m.title + '</span>' +
        '<span class="mod-desc">' + m.desc + '</span>' +
        '<span class="bar"><i style="width:' + pct + '%"></i></span>' +
        '<span class="mod-meta">' + n + ' 題 · 已答對 ' + s.mastered + '</span></a>';
    });
    h += '</section><footer class="foot"><p>這是試用版。哪些單元最有用、哪些想要更多題目，請直接用 LINE 告訴林吉祥老師。</p>' +
      '<p class="small">學習紀錄只存在這支手機上。題目內容中的人名都是虛構的。</p>' +
      '<p class="small">My Culture Connect · 人師教育協會 · <a href="/">Changhua Bilingual Hub</a></p></footer>';
    app.innerHTML = h;
  }

  function moduleView(mid) {
    var m = MOD[mid], b = banks[mid]; setTheme(m);
    var h = '<header class="bar-top"><a href="#/" class="back">‹ 首頁</a><span>' + m.emoji + ' ' + m.title + '</span></header>' +
      '<section class="mod-hero reveal"><span class="big">' + m.emoji + '</span><h1>' + m.title + '</h1><p class="en">' + m.en + '</p><p>' + m.desc + '</p>' +
      '<a class="btn primary" href="#/q/' + mid + '/all">全部混合練習（' + ROUND + ' 題）</a></section><section class="sets">';
    b.sets.forEach(function (s, i) {
      var n = (s.qs || s.terms).length, best = st.best[mid + '.' + s.id];
      h += '<a class="set reveal" style="--d:' + (i * 50) + 'ms" href="#/q/' + mid + '/' + s.id + '">' +
        '<span class="set-emoji">' + s.emoji + '</span><span class="set-body"><span class="set-title">' + s.title + '</span>' +
        '<span class="set-en">' + s.en + ' · ' + n + ' 題</span></span>' +
        '<span class="set-best">' + (best != null ? best + '%' : '開始') + '</span></a>';
    });
    app.innerHTML = h + '</section>';
  }

  /* ---------- quiz ---------- */
  var run = null;   // {key, title, mod, qs, i, right, missed[], answered}

  function startRun(key, title, mod, qs) {
    run = { key: key, title: title, mod: mod, qs: qs, i: 0, right: 0, missed: [] };
    showQ();
  }

  function showQ() {
    var q = run.qs[run.i], m = MOD[q.mod]; setTheme(m);
    var opts = shuffle(q.a.map(function (t, k) { return { t: t, ok: k === 0 }; }));
    var pl = langOfPrompt(q), dirLabel = q.dir === 'ze' ? '中 → 英' : '英 → 中';
    var long = q.mod === 'm5' || q.mod === 'm6' || opts.some(function (o) { return o.t.length > 70; });
    var h = '<header class="bar-top"><a href="' + (run.mod ? '#/m/' + run.mod : '#/') + '" class="back">‹ 離開</a>' +
      '<span>' + esc(run.title) + '</span><span class="count">' + (run.i + 1) + ' / ' + run.qs.length + '</span></header>' +
      '<div class="progress"><i style="width:' + (run.i * 100 / run.qs.length) + '%"></i></div>' +
      '<section class="qcard pop"><p class="qmeta">' + m.emoji + ' ' + m.title + ' · <b>' + dirLabel + '</b></p>' +
      '<p class="prompt ' + pl + '">' + esc(q.p) + '</p>' +
      '<div class="qtools">' + speakBtn(q.p, pl, '聽題目') +
      (Rec && (q.mod === 'm1' || q.term) ? '<button class="mic" id="mic">🎙 先開口說說看</button>' : '') + '</div>' +
      '<p class="heard" id="heard" hidden></p></section>' +
      '<p class="ask">' + (q.mod === 'm3' ? '哪一句最自然？' : q.mod === 'm5' ? '哪一則訊息最得體？' : '最好的譯法／說法是？') + '</p>' +
      '<section class="opts' + (long ? ' long' : '') + '">';
    opts.forEach(function (o, k) {
      h += '<button class="opt ' + langOfAnswer(q) + '" data-ok="' + (o.ok ? 1 : 0) + '" style="--d:' + (k * 40) + 'ms">' +
        '<span class="key">' + 'ABCD'.charAt(k) + '</span><span class="txt">' + esc(o.t) + '</span></button>';
    });
    h += '</section><section id="fb"></section>';
    app.innerHTML = h;
    window.scrollTo(0, 0);
    var mic = document.getElementById('mic');
    if (mic) mic.onclick = function () { listen(langOfAnswer(q), mic); };
    Array.prototype.forEach.call(app.querySelectorAll('.opt'), function (btn) {
      btn.onclick = function () { answer(q, btn); };
    });
  }

  function listen(lang, btn) {
    var heard = document.getElementById('heard');
    try {
      var r = new Rec();
      r.lang = lang === 'en' ? 'en-US' : 'zh-TW';
      r.interimResults = false; r.maxAlternatives = 1;
      btn.disabled = true; btn.textContent = '🎙 聆聽中…請說';
      r.onresult = function (e) {
        heard.hidden = false;
        heard.innerHTML = '<span>你說的是：</span>' + esc(e.results[0][0].transcript) + '<br><small>跟下面的選項比比看。</small>';
      };
      r.onerror = function () { heard.hidden = false; heard.innerHTML = '<small>沒有收到聲音。可以先在心裡說一遍，再選答案。</small>'; };
      r.onend = function () { btn.disabled = false; btn.textContent = '🎙 再說一次'; };
      r.start();
    } catch (e) {
      heard.hidden = false; heard.innerHTML = '<small>這個瀏覽器不支援語音辨識，請先大聲說一遍，再選答案。</small>';
    }
  }

  function answer(q, btn) {
    var ok = btn.getAttribute('data-ok') === '1';
    Array.prototype.forEach.call(app.querySelectorAll('.opt'), function (b) {
      b.disabled = true;
      if (b.getAttribute('data-ok') === '1') b.classList.add('right');
    });
    if (!ok) btn.classList.add('wrong');
    var rec = st.seen[q.id] || { c: 0, w: 0 };
    var wi = st.wrong.indexOf(q.id);
    if (ok) { rec.c++; run.right++; if (wi >= 0 && run.key === 'wrong') st.wrong.splice(wi, 1); }
    else { rec.w++; run.missed.push(q); if (wi < 0) st.wrong.push(q.id); }
    st.seen[q.id] = rec; markDay(); save();

    var best = q.a[0], al = langOfAnswer(q);
    var h = '<div class="fb ' + (ok ? 'ok' : 'no') + ' pop"><p class="verdict">' + (ok ? '✔ 答對了！' : '✘ 再想想，正確答案是：') + '</p>' +
      '<p class="best ' + al + '">' + esc(best) + '</p>' +
      (al === 'en' ? speakBtn(best, 'en', '聽標準說法') : '') +
      '<p class="note">💡 ' + esc(q.n) + '</p>';
    if (q.x && q.x.length) {
      h += '<div class="alts"><p class="alts-h">也可以這樣說</p>';
      q.x.forEach(function (x) { h += '<p class="alt en">' + esc(x) + ' ' + speakBtn(x, 'en') + '</p>'; });
      h += '</div>';
    }
    if (q.ex) h += '<div class="alts"><p class="alts-h">例句</p><p class="alt en">' + esc(q.ex) + ' ' + speakBtn(q.ex, 'en') + '</p></div>';
    h += '<button class="btn primary next" id="next">' + (run.i + 1 < run.qs.length ? '下一題 →' : '看結果') + '</button></div>';
    var fb = document.getElementById('fb');
    fb.innerHTML = h;
    setTimeout(function () { fb.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60);
    document.getElementById('next').onclick = function () {
      run.i++;
      if (run.i < run.qs.length) showQ(); else result();
    };
  }

  function result() {
    var n = run.qs.length, pct = Math.round(run.right * 100 / n);
    if (run.key.indexOf('set:') === 0) {
      var k = run.key.slice(4);
      if (st.best[k] == null || pct > st.best[k]) st.best[k] = pct;
      save();
    }
    var msg = pct === 100 ? '全對！太厲害了 🎉' : pct >= 80 ? '很棒！只差一點點 👏' : pct >= 60 ? '不錯，錯的題目再看一次就記住了 💪' : '慢慢來，錯題本會幫你複習 🌱';
    var h = '<header class="bar-top"><a href="' + (run.mod ? '#/m/' + run.mod : '#/') + '" class="back">‹ 返回</a><span>' + esc(run.title) + '</span></header>' +
      '<section class="result pop"><p class="score">' + run.right + ' <small>/ ' + n + '</small></p><p class="msg">' + msg + '</p>' +
      '<div class="result-btns"><button class="btn primary" id="again">再練一次</button>' +
      '<a class="btn ghost" href="#/">回首頁</a></div></section>';
    if (run.missed.length) {
      h += '<h2 class="sec">這次答錯的題目</h2><section class="missed">';
      run.missed.forEach(function (q) {
        h += '<div class="miss"><p class="mp ' + langOfPrompt(q) + '">' + esc(q.p) + '</p><p class="ma ' + langOfAnswer(q) + '">→ ' + esc(q.a[0]) +
          (langOfAnswer(q) === 'en' ? ' ' + speakBtn(q.a[0], 'en') : '') + '</p></div>';
      });
      h += '</section>';
    }
    app.innerHTML = h;
    window.scrollTo(0, 0);
    document.getElementById('again').onclick = function () { route(); };
  }

  /* ---------- router ---------- */
  function route() {
    var h = location.hash.replace(/^#\/?/, '').split('/');
    if (synth) synth.cancel();
    if (!h[0]) return allBanks().then(home);
    if (h[0] === 'm' && MOD[h[1]]) return fetchBank(h[1]).then(function () { moduleView(h[1]); });
    if (h[0] === 'q' && MOD[h[1]]) return fetchBank(h[1]).then(function (b) {
      var m = MOD[h[1]];
      if (h[2] === 'all') return startRun('mod:' + h[1], m.title + '・混合', h[1], shuffle(questionsOf(b)).slice(0, ROUND));
      var s = b.sets.filter(function (x) { return x.id === h[2]; })[0];
      if (!s) { location.hash = '#/m/' + h[1]; return; }
      startRun('set:' + h[1] + '.' + s.id, s.title, h[1], shuffle(questionsOf(b, s.id)));
    });
    if (h[0] === 'mix') return allBanks().then(function () {
      // one or two from each module, weighted toward questions not yet answered right
      var picks = [];
      MODULES.forEach(function (m) {
        var qs = shuffle(questionsOf(banks[m.id]));
        qs.sort(function (a, b) { return ((st.seen[a.id] || {}).c || 0) - ((st.seen[b.id] || {}).c || 0); });
        picks = picks.concat(qs.slice(0, m.id === 'm1' || m.id === 'm2' || m.id === 'm3' || m.id === 'm4' ? 2 : 1));
      });
      startRun('mix', '今日十題', null, shuffle(picks).slice(0, ROUND));
    });
    if (h[0] === 'wrong') return allBanks().then(function () {
      var qs = st.wrong.map(byId).filter(Boolean);
      if (!qs.length) { location.hash = '#/'; return; }
      startRun('wrong', '錯題本', null, shuffle(qs).slice(0, ROUND));
    });
    location.hash = '#/';
  }
  window.addEventListener('hashchange', function () { route(); });
  if (synth && synth.onvoiceschanged !== undefined) synth.onvoiceschanged = function () {};
  route();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () { navigator.serviceWorker.register('sw.js').catch(function () {}); });
  }
})();
