/**
 * Changhua Mandarin — learning engine.
 * ------------------------------------
 * Reads the Mandarin Challenge banks (the single source of truth, never
 * modified here) and turns each question into several kinds of exercise.
 * Scheduling is a five-box Leitner system; progress lives in localStorage and
 * syncs to the existing Apps Script endpoint when a teacher ID is set.
 *
 * The page sets window.__LEARN_CONFIG__ before loading this file.
 */
(function () {
  var cfg = window.__LEARN_CONFIG__;
  if (!cfg) return;

  var STORE = 'chb-learn-v1';
  var SESSION_SIZE = 12;      // items per round — about 3-4 minutes
  var MAX_REVIEWS = 8;        // of which at most this many are due reviews
  var BOX_DAYS = [0, 1, 3, 7, 21];
  var LEVELS = ['beginner', 'intermediate', 'advanced'];

  var $ = function (id) { return document.getElementById(id); };
  var today = function () { return Math.floor(Date.now() / 86400000); };

  var banks = {};             // level -> bank json
  var manifest = null;        // zh -> audio hash
  var state = null;

  var run = {                 // the round in progress
    level: null, queue: [], pos: 0, right: 0, wrong: 0, wrongIds: []
  };

  // ------------------------------------------------------------ persistence

  function blank() {
    return { v: 1, teacher: null, xp: 0, streak: { n: 0, last: 0 }, items: {} };
  }

  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(STORE) || 'null');
      if (s && s.v === 1) return s;
    } catch (e) { /* private mode, or corrupt — start fresh */ }
    return blank();
  }

  function save() {
    try { localStorage.setItem(STORE, JSON.stringify(state)); }
    catch (e) { /* quota or private mode — the round still works */ }
  }

  function itemState(id) {
    return state.items[id] || (state.items[id] = { b: 0, d: 0, n: 0, w: 0, u: 0 });
  }

  // ------------------------------------------------------------------ audio

  var current = null;

  /**
   * Last resort when the recording can't be fetched (R2 not populated yet, or
   * offline with a clip that was never cached). The device voice is uneven —
   * that is exactly why this app ships real recordings — but a listening
   * question with no sound at all is unanswerable, so anything beats silence.
   */
  function speakFallback(zh, btn) {
    if (!('speechSynthesis' in window)) return;
    var voices = speechSynthesis.getVoices() || [];
    var v = voices.filter(function (x) { return /zh[-_]TW/i.test(x.lang); })[0]
         || voices.filter(function (x) { return /^zh/i.test(x.lang); })[0];
    if (!v && voices.length) return;          // no Chinese voice at all
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(zh);
    u.lang = 'zh-TW';
    u.rate = 0.85;
    if (v) u.voice = v;
    if (btn) {
      u.onend = u.onerror = function () { btn.classList.remove('on'); };
    }
    speechSynthesis.speak(u);
  }

  function play(zh, btn) {
    if (!manifest) return;
    var h = manifest[zh];
    if (!h) return;
    if (current) { current.pause(); current = null; }
    document.querySelectorAll('.lx-say.on').forEach(function (b) { b.classList.remove('on'); });
    var a = new Audio(cfg.audioBase + h + '.mp3');
    current = a;
    if (btn) btn.classList.add('on');
    a.onended = function () { if (btn) btn.classList.remove('on'); };
    a.onerror = function () { speakFallback(zh, btn); };
    var p = a.play();
    if (p && p.catch) p.catch(function () { speakFallback(zh, btn); });
  }

  // -------------------------------------------------------------- selection

  function shuffled(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), t = a[i];
      a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /** Pick the round: due reviews first, then unseen items in bank order. */
  function buildQueue(level) {
    var qs = banks[level].questions, d = today();
    var due = [], fresh = [];
    qs.forEach(function (q) {
      var s = state.items[q.id];
      if (!s || !s.n) fresh.push(q);
      else if (s.d <= d) due.push(q);
    });
    due.sort(function (a, b) { return state.items[a.id].d - state.items[b.id].d; });
    var picked = due.slice(0, MAX_REVIEWS);
    picked = picked.concat(fresh.slice(0, SESSION_SIZE - picked.length));
    // Nothing new and nothing due — revise the weakest items instead of
    // showing an empty round.
    if (!picked.length) {
      picked = qs.slice()
        .filter(function (q) { return state.items[q.id]; })
        .sort(function (a, b) { return state.items[b.id].w - state.items[a.id].w; })
        .slice(0, SESSION_SIZE);
    }
    return shuffled(picked);
  }

  /** Three distractor phrases from the same level, preferring similar length. */
  function otherPhrases(level, q, n) {
    var pool = banks[level].questions.filter(function (o) {
      return o.id !== q.id && o.zh !== q.zh;
    });
    pool.sort(function (a, b) {
      return Math.abs(a.zh.length - q.zh.length) - Math.abs(b.zh.length - q.zh.length);
    });
    return shuffled(pool.slice(0, Math.max(n * 4, 12))).slice(0, n);
  }

  // ------------------------------------------------------- exercise choice

  /**
   * Which exercise to show. Scenario-style questions (idiom, expression,
   * situation, dialogue) carry their meaning in the English stem, so they only
   * work as stem-based or listening items. Short vocabulary items support the
   * character-recognition drills, which is what the bank could not test before.
   */
  function chooseExercise(q) {
    var scenario = /^(idiom|expression|situation|dialogue)$/.test(q.type);
    var s = state.items[q.id] || { n: 0 };
    var kinds = scenario ? ['stem', 'listen'] : ['stem', 'listen', 'audio2zh', 'meaning2zh', 'pinyin2zh'];
    // Items written as listening questions must never show their characters —
    // the stem ("Listen. What is being said?") gives the answer away next to
    // the very characters it is asking about.
    if (q.type === 'listen') kinds = ['listen', 'audio2zh'];
    // Otherwise the first encounter is the plain stem question, so the learner
    // meets the phrase with its meaning before being drilled on the characters.
    if (!s.n) return kinds[0];
    // Offset the rotation per item, otherwise every item at the same exposure
    // count shows the same exercise and a whole round looks identical.
    var off = 0;
    for (var i = 0; i < q.id.length; i++) off += q.id.charCodeAt(i);
    return kinds[(s.n + off) % kinds.length];
  }

  // ------------------------------------------------------------- rendering

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function sayBtn(zh, big) {
    return '<button type="button" class="lx-say' + (big ? ' lx-say--big' : '') +
      '" data-zh="' + esc(zh) + '" aria-label="Play audio 播放發音">🔊</button>';
  }

  function render() {
    var q = run.queue[run.pos];
    if (!q) return finish();
    var kind = chooseExercise(q);
    var head, opts, correctIdx;

    if (kind === 'stem') {
      head = '<div class="lx-zh">' + esc(q.zh) + ' ' + sayBtn(q.zh) +
        '<span class="lx-py">' + esc(q.py) + '</span></div>' +
        '<p class="lx-q">' + esc(q.q) + '</p>';
      opts = q.opts.map(esc);
      correctIdx = q.ok;

    } else if (kind === 'listen') {
      head = '<p class="lx-instr">Listen, then choose the meaning · 聽完選出意思</p>' +
        '<div class="lx-audio">' + sayBtn(q.zh, true) + '</div>';
      opts = q.opts.map(esc);
      correctIdx = q.ok;

    } else if (kind === 'audio2zh') {
      head = '<p class="lx-instr">Listen, then choose the characters · 聽完選出漢字</p>' +
        '<div class="lx-audio">' + sayBtn(q.zh, true) + '</div>';
      var d1 = otherPhrases(run.level, q, 3);
      var set1 = shuffled([q].concat(d1));
      opts = set1.map(function (o) { return '<span class="lx-opt-zh">' + esc(o.zh) + '</span>'; });
      correctIdx = set1.indexOf(q);

    } else if (kind === 'meaning2zh') {
      head = '<p class="lx-instr">Which characters mean this? · 哪一個是這個意思？</p>' +
        '<p class="lx-prompt-en">' + esc(q.opts[q.ok]) + '</p>';
      var d2 = otherPhrases(run.level, q, 3);
      var set2 = shuffled([q].concat(d2));
      opts = set2.map(function (o) { return '<span class="lx-opt-zh">' + esc(o.zh) + '</span>'; });
      correctIdx = set2.indexOf(q);

    } else { // pinyin2zh
      head = '<p class="lx-instr">Which characters match this pinyin? · 哪一個符合這個拼音？</p>' +
        '<p class="lx-prompt-py">' + esc(q.py) + '</p>';
      var d3 = otherPhrases(run.level, q, 3);
      var set3 = shuffled([q].concat(d3));
      opts = set3.map(function (o) { return '<span class="lx-opt-zh">' + esc(o.zh) + '</span>'; });
      correctIdx = set3.indexOf(q);
    }

    $('lxProgress').style.width = (run.pos / run.queue.length * 100) + '%';
    $('lxCount').textContent = (run.pos + 1) + ' / ' + run.queue.length;
    // Clear the previous question's graded/done state, or this one is unanswerable.
    $('lxCard').className = 'lx-card';
    $('lxCard').innerHTML =
      '<div class="lx-head">' + head + '</div>' +
      '<div class="lx-opts">' + opts.map(function (o, i) {
        return '<button type="button" class="lx-opt" data-i="' + i + '">' + o + '</button>';
      }).join('') + '</div>' +
      '<div class="lx-why"><strong>' + esc(q.zh) + '</strong> <em>' + esc(q.py) + '</em> ' +
      sayBtn(q.zh) + '<span>' + esc(q.why) + '</span></div>';

    $('lxCard').querySelectorAll('.lx-say').forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.stopPropagation();
        play(b.getAttribute('data-zh'), b);
      });
    });
    $('lxCard').querySelectorAll('.lx-opt').forEach(function (b) {
      b.addEventListener('click', function () { answer(q, Number(b.dataset.i), correctIdx, b); });
    });
    $('lxNext').classList.add('hidden');

    // Listening exercises play themselves once — that is the exercise.
    if (kind === 'listen' || kind === 'audio2zh') {
      setTimeout(function () { play(q.zh, $('lxCard').querySelector('.lx-say--big')); }, 250);
    }
  }

  function answer(q, picked, correctIdx, btn) {
    var card = $('lxCard');
    if (card.classList.contains('done')) return;
    card.classList.add('done');
    var ok = picked === correctIdx;

    card.querySelectorAll('.lx-opt').forEach(function (b, i) {
      b.disabled = true;
      if (i === correctIdx) b.classList.add('right');
      else if (i === picked) b.classList.add('wrong');
    });
    if (!ok) btn.classList.add('shake');
    card.classList.add('graded');

    var s = itemState(q.id);
    s.n++;
    s.u = Date.now();
    if (ok) {
      run.right++;
      s.b = Math.min(s.b + 1, BOX_DAYS.length - 1);
      state.xp += 10;
    } else {
      run.wrong++;
      run.wrongIds.push(q.id);
      s.w++;
      s.b = 0;
    }
    s.d = today() + BOX_DAYS[s.b];
    save();

    if (ok) play(q.zh, card.querySelector('.lx-why .lx-say'));
    $('lxNext').classList.remove('hidden');
    $('lxNext').focus();
  }

  function next() {
    run.pos++;
    if (run.pos >= run.queue.length) return finish();
    render();
  }

  function finish() {
    var d = today();
    if (state.streak.last !== d) {
      state.streak.n = (state.streak.last === d - 1) ? state.streak.n + 1 : 1;
      state.streak.last = d;
    }
    save();
    if (window.__LEARN_SYNC__) window.__LEARN_SYNC__.push(state);

    var total = run.queue.length;
    var pct = Math.round(run.right / total * 100);
    $('lxDoneScore').textContent = run.right + ' / ' + total;
    $('lxDoneStreak').textContent = state.streak.n;
    $('lxDoneXp').textContent = state.xp;
    $('lxDoneHead').textContent =
      pct === 100 ? 'Perfect round · 全對！' :
      pct >= 75 ? 'Nicely done · 做得好！' :
      pct >= 50 ? 'Good progress · 有進步' : 'Worth another go · 再練一次';

    var byId = {};
    banks[run.level].questions.forEach(function (q) { byId[q.id] = q; });
    var uniq = run.wrongIds.filter(function (v, i, a) { return a.indexOf(v) === i; });
    $('lxDoneWrong').innerHTML = uniq.length
      ? '<h3>Worth reviewing · 需要複習</h3>' + uniq.map(function (id) {
          var q = byId[id];
          return '<div class="lx-rev"><span class="zh">' + esc(q.zh) + '</span>' +
            '<em>' + esc(q.py) + '</em>' + sayBtn(q.zh) +
            '<span class="en">' + esc(q.opts[q.ok]) + '</span></div>';
        }).join('')
      : '<p class="lx-allright">No mistakes this round. 這回合全對！</p>';
    $('lxDoneWrong').querySelectorAll('.lx-say').forEach(function (b) {
      b.addEventListener('click', function () { play(b.getAttribute('data-zh'), b); });
    });

    show('lxDone');
  }

  // ---------------------------------------------------------------- screens

  function show(id) {
    ['lxHome', 'lxRound', 'lxDone'].forEach(function (s) {
      $(s).classList.toggle('hidden', s !== id);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function levelStats(level) {
    var qs = banks[level] ? banks[level].questions : [];
    var d = today(), learned = 0, due = 0;
    qs.forEach(function (q) {
      var s = state.items[q.id];
      if (s && s.n) { learned++; if (s.d <= d) due++; }
    });
    return { total: qs.length, learned: learned, due: due };
  }

  function paintHome() {
    $('lxStreak').textContent = state.streak.n;
    $('lxXp').textContent = state.xp;
    LEVELS.forEach(function (lv) {
      var st = levelStats(lv), el = $('lxCard-' + lv);
      if (!el) return;
      var pct = st.total ? Math.round(st.learned / st.total * 100) : 0;
      el.querySelector('.lx-bar i').style.width = pct + '%';
      el.querySelector('.lx-lvstat').textContent =
        st.total ? (st.learned + ' / ' + st.total + ' seen · ' + st.due + ' due 待複習') : 'loading…';
    });
  }

  function start(level) {
    run = { level: level, queue: buildQueue(level), pos: 0, right: 0, wrong: 0, wrongIds: [] };
    $('lxRoundTitle').textContent = banks[level].label + ' · ' + banks[level].labelZh;
    show('lxRound');
    render();
  }

  // ------------------------------------------------------------------- boot

  function loadAll() {
    var jobs = LEVELS.map(function (lv) {
      return fetch(cfg.dataBase + lv + '.json').then(function (r) { return r.json(); })
        .then(function (b) { banks[lv] = b; });
    });
    jobs.push(
      fetch(cfg.manifestUrl)
        .then(function (r) { return r.json(); })
        .then(function (m) { manifest = m; })
        .catch(function () { manifest = {}; })     // no audio yet: stay usable
    );
    return Promise.all(jobs);
  }

  state = load();

  loadAll().then(function () {
    paintHome();
    $('lxLoading').classList.add('hidden');
    LEVELS.forEach(function (lv) {
      var el = $('lxCard-' + lv);
      if (el) el.addEventListener('click', function () { start(lv); });
    });
  }).catch(function () {
    $('lxLoading').textContent = 'Could not load the question banks. 題庫載入失敗。';
  });

  $('lxNext').addEventListener('click', next);
  $('lxQuit').addEventListener('click', function () { paintHome(); show('lxHome'); });
  $('lxAgain').addEventListener('click', function () { start(run.level); });
  $('lxHomeBtn').addEventListener('click', function () { paintHome(); show('lxHome'); });

  window.__LEARN__ = {
    state: function () { return state; },
    reset: function () { state = blank(); save(); paintHome(); }
  };
})();
