/**
 * Mandarin Challenge — question-bank engine (FETs).
 * -------------------------------------------------
 * Three levels, each backed by its own JSON bank under
 * /fets/mandarin-challenge/data/<level>.json
 *
 * Two views:
 *   study — the practice area: EVERY question in the level, laid out openly and
 *           grouped by the nine FET meeting rounds. Answers and explanations are
 *           visible by default; "Hide answers" turns it into a self-test.
 *   quiz  — practice quiz (random draw, not recorded) or a meeting round
 *           (fixed 20, identical for everyone, written to the Google Sheet).
 *
 * Audio: every phrase has a pre-generated Azure zh-TW clip (see tools/gen_audio.py),
 * shared with /learn/ and /culture/ and named by a hash of the phrase. We play the
 * recording; the device's own voice is only a fallback for a clip we cannot fetch.
 *
 * The page sets window.__MC_CONFIG__ before loading this file.
 * Grading is client-side, same trust model as the other Hub quizzes
 * (see CONTRIBUTING.md §8).
 */
(function () {
  var cfg = window.__MC_CONFIG__;
  if (!cfg) return;

  var ROUND_SIZE = 20;
  var LEVELS = ['survival', 'beginner', 'intermediate', 'advanced'];
  var $ = function (id) { return document.getElementById(id); };

  var state = {
    view: 'study',
    level: 'survival',
    bank: null,
    filterType: 'all',
    query: '',
    // quiz-only
    mode: null,         // 'practice' | 'meeting'
    round: null,        // 'M1'..'M9'
    items: [],
    answers: {},
    optOrder: {},
    teacherId: '',
    teacherName: '',
    lastWrong: []
  };

  var banks = {};

  var TYPE_LABEL = {
    word: 'Vocabulary 字詞',
    listen: 'Listening 聽力',
    expression: 'Expression 用語',
    dialogue: 'Response 應答',
    situation: 'Situation 情境',
    measure: 'Measure word 量詞',
    idiom: 'Idiom 成語'
  };
  function typeLabel(t) { return TYPE_LABEL[t] || t; }

  // ---------------------------------------------------------------- speech

  var zhVoices = [];
  function loadVoices() {
    zhVoices = (window.speechSynthesis ? speechSynthesis.getVoices() : []) || [];
    updateVoiceNotice();
  }
  function pickZhVoice() {
    return zhVoices.find(function (v) { return /zh[-_]TW/i.test(v.lang); })
      || zhVoices.find(function (v) { return /zh[-_]?(CN|HK|Hans|Hant)/i.test(v.lang); })
      || zhVoices.find(function (v) { return /^zh/i.test(v.lang); })
      || null;
  }
  function updateVoiceNotice() {
    var el = $('mcVoiceNotice');
    if (!el) return;
    // Before the voice list resolves, assume speech works rather than flashing
    // a warning at every visitor on first paint.
    // With recordings loaded the device voice no longer matters, so the warning
    // would be misleading — it only applies when we are relying on the fallback.
    var ok = !!manifest
      || (('speechSynthesis' in window) && (!zhVoices.length || !!pickZhVoice()));
    el.classList.toggle('hidden', ok);
  }
  if ('speechSynthesis' in window) {
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
  }
  /**
   * Last resort when the recording can't be fetched (manifest missing, offline,
   * or a phrase added since the last audio build). The device voice is uneven —
   * that unevenness is exactly why this page ships real clips — but a listening
   * prompt with no sound at all is worse than an uneven one.
   */
  function speakFallback(text, btn) {
    if (!('speechSynthesis' in window) || !text) return;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'zh-TW';
    u.rate = 0.85;
    var v = pickZhVoice();
    if (v) u.voice = v;
    if (btn) {
      btn.classList.add('is-speaking');
      u.onend = function () { btn.classList.remove('is-speaking'); };
      u.onerror = function () { btn.classList.remove('is-speaking'); };
    }
    speechSynthesis.speak(u);
  }
  // Pre-generated clips, keyed by phrase. Loaded once; failure is non-fatal and
  // simply leaves every 🔊 on the device-voice fallback.
  var manifest = null;
  var current = null;
  if (cfg.audioManifest) {
    fetch(cfg.audioManifest)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { if (m) { manifest = m; updateVoiceNotice(); } })
      .catch(function () { /* fallback voice still works */ });
  }

  function stopAll() {
    if (current) { current.pause(); current = null; }
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    document.querySelectorAll('.speak.is-speaking').forEach(function (b) {
      b.classList.remove('is-speaking');
    });
  }

  // Teachers asked to be able to slow the longer sentences down. The clips are
  // already voiced at -10%, so this is on top of that; the browser keeps the
  // pitch, so a slowed clip still sounds like speech rather than a drawl.
  var RATES = [0.6, 0.8, 1];
  var rate = 1;
  try {
    var savedRate = parseFloat(localStorage.getItem('chb-audio-rate'));
    if (RATES.indexOf(savedRate) !== -1) rate = savedRate;
  } catch (e) { /* private mode — just use normal speed */ }

  function setRate(r) {
    rate = r;
    try { localStorage.setItem('chb-audio-rate', String(r)); } catch (e) {}
    if (current) current.playbackRate = r;
    document.querySelectorAll('[data-rate]').forEach(function (b) {
      b.classList.toggle('is-on', parseFloat(b.dataset.rate) === r);
    });
  }

  function speak(text, btn) {
    if (!text) return;
    stopAll();
    var hash = manifest && manifest[text];
    if (!hash || !cfg.audioBase) { speakFallback(text, btn); return; }

    var a = new Audio(cfg.audioBase + hash + '.mp3');
    a.playbackRate = rate;
    if ('preservesPitch' in a) a.preservesPitch = true;
    current = a;
    if (btn) btn.classList.add('is-speaking');
    var failed = false;
    function fail() {
      if (failed) return;
      failed = true;
      if (btn) btn.classList.remove('is-speaking');
      current = null;
      speakFallback(text, btn);
    }
    a.onended = function () {
      if (btn) btn.classList.remove('is-speaking');
      current = null;
    };
    a.onerror = fail;
    var p = a.play();
    if (p && p.catch) p.catch(fail);
  }

  function wireSpeakButtons(root) {
    root.querySelectorAll('[data-speak]').forEach(function (b) {
      b.addEventListener('click', function () { speak(b.getAttribute('data-speak'), b); });
    });
  }

  // ---------------------------------------------------------------- helpers

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function shuffled(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function roundLabel(n) {
    var m = cfg.meetings && cfg.meetings[n - 1];
    return m ? m : 'Meeting ' + n;
  }
  function meetingCount() { return (cfg.meetings || []).length || 9; }
  function roundsAvailable(bank) { return Math.floor(bank.questions.length / ROUND_SIZE); }

  function showSection(id) {
    ['mcStudyView', 'mcQuizModeScreen', 'mcQuizScreen', 'mcResultScreen'].forEach(function (s) {
      var el = $(s);
      if (el) el.classList.toggle('hidden', s !== id);
    });
  }
  function scrollToTop(id) {
    var el = $(id);
    if (!el) return;
    var y = el.getBoundingClientRect().top + window.pageYOffset - 76;
    window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
  }

  // ---------------------------------------------------------------- loading

  function loadBank(level) {
    if (banks[level]) return Promise.resolve(banks[level]);
    return fetch(cfg.dataBase + level + '.json', { cache: 'no-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (bank) { banks[level] = bank; return bank; });
  }

  // Load every level up front so the tabs can show real counts and switching
  // levels is instant — three small JSON files, fetched in parallel.
  function preloadAll() {
    LEVELS.forEach(function (lv) {
      loadBank(lv).then(function (bank) {
        var el = document.querySelector('[data-count="' + lv + '"]');
        if (el) el.textContent = bank.questions.length + ' questions · ' + bank.questions.length + ' 題';
      }).catch(function () { /* the active level surfaces its own error */ });
    });
  }

  // ---------------------------------------------------------------- study view

  // Some items ask which Chinese phrase fits, so the options ARE the phrases.
  // Printing q.zh above them hands over the answer before a single option is
  // read. Detect that and keep the phrase — and its audio — hidden until the
  // answer is shown, exactly as listening items already do.
  function hanzi(s) {
    return (String(s == null ? '' : s).match(/[一-鿿]+/g) || []).join('');
  }

  function phraseGivesAnswer(q) {
    if (!q.zh || !q.opts) return false;
    var correct = q.opts[q.ok] || '';

    // The phrase we print IS the right option — 請問 above options A-D, one of
    // which is 請問.
    if (correct.indexOf(q.zh) !== -1) {
      return !q.opts.some(function (o, i) {
        return i !== q.ok && o.indexOf(q.zh) !== -1;
      });
    }

    // The right option sits INSIDE the phrase we print — options are 請假 /
    // 下班 / 開會 / 上課 and the phrase above them reads 我禮拜五要請假.
    var ck = hanzi(correct);
    if (ck.length >= 2 && q.zh.indexOf(ck) !== -1) {
      return !q.opts.some(function (o, i) {
        var c = hanzi(o);
        return i !== q.ok && c.length >= 2 && q.zh.indexOf(c) !== -1;
      });
    }

    return false;
  }

  function studyItemHtml(q) {
    var opts = q.opts.map(function (o, i) {
      return '<li class="st__opt' + (i === q.ok ? ' is-ok' : '') + '">' +
        '<span class="k">' + String.fromCharCode(65 + i) + '</span><span>' + esc(o) + '</span></li>';
    }).join('');
    var hide = q.type === 'listen' || phraseGivesAnswer(q);
    return '<div class="st' + (hide ? ' st--listen' : '') + '" ' +
        'data-type="' + esc(q.type) + '" data-hay="' + esc(searchHaystack(q)) + '">' +
      '<div class="st__head">' +
        '<span class="st__id">' + esc(q.id) + '</span>' +
        '<span class="st__tag">' + esc(typeLabel(q.type)) + '</span>' +
        '<button type="button" class="speak' + (phraseGivesAnswer(q) ? ' is-held" data-hold="1' : '') +
          '" data-speak="' + esc(q.zh) + '" aria-label="Listen · 播放發音">🔊</button>' +
      '</div>' +
      '<div class="st__zh"><span class="st__hanzi">' + esc(q.zh) + '</span>' +
        '<span class="st__py">' + esc(q.py) + '</span></div>' +
      '<p class="st__q">' + esc(q.q) + '</p>' +
      '<ul class="st__opts">' + opts + '</ul>' +
      '<button type="button" class="st__reveal">Show answer · 看答案</button>' +
      '<p class="st__why">' + esc(q.why) + '</p>' +
    '</div>';
  }

  function searchHaystack(q) {
    return (q.id + ' ' + q.zh + ' ' + q.py + ' ' + q.q + ' ' + q.opts.join(' ') + ' ' + q.why).toLowerCase();
  }

  function renderStudy() {
    var bank = state.bank;
    $('mcStudyBlurbZh').textContent = bank.blurbZh;

    var qs = bank.questions;
    var html = [];
    var nRounds = meetingCount();

    for (var r = 1; r <= nRounds; r++) {
      var slice = qs.slice((r - 1) * ROUND_SIZE, r * ROUND_SIZE);
      if (!slice.length) continue;
      html.push(
        '<div class="mc-round" data-round="M' + r + '">' +
          '<div class="mc-round__h">' +
            '<span class="mc-round__tag">M' + r + '</span>' +
            '<h2 class="mc-round__title">' + esc(roundLabel(r)) + '</h2>' +
            '<span class="mc-round__n">' + slice.length + ' questions</span>' +
          '</div>' +
          slice.map(studyItemHtml).join('') +
        '</div>'
      );
    }

    // Anything beyond the nine rounds is spare stock for substitutions.
    var spare = qs.slice(nRounds * ROUND_SIZE);
    if (spare.length) {
      html.push(
        '<div class="mc-round mc-round--spare" data-round="spare">' +
          '<div class="mc-round__h">' +
            '<span class="mc-round__tag">Spare</span>' +
            '<h2 class="mc-round__title">Extra practice · 備用題</h2>' +
            '<span class="mc-round__n">' + spare.length + ' questions</span>' +
          '</div>' +
          spare.map(studyItemHtml).join('') +
        '</div>'
      );
    }

    // Questions past the filled rounds but inside the nine — say so plainly
    // rather than silently showing fewer meetings than promised.
    var filled = Math.ceil(qs.length / ROUND_SIZE);
    if (filled < nRounds) {
      html.push(
        '<p class="mc-notice" style="margin-top:28px">' +
          'Rounds M' + (filled + 1) + '–M' + nRounds + ' are still being written. ' +
          'This level currently holds ' + qs.length + ' of the ' + (nRounds * ROUND_SIZE) + ' questions needed for all nine meetings.' +
          '<br><span style="font-family:var(--hub-zh-font)">M' + (filled + 1) + '–M' + nRounds +
          ' 的題目還在編寫中，這一級目前有 ' + qs.length + ' 題，九場會議共需 ' + (nRounds * ROUND_SIZE) + ' 題。</span>' +
        '</p>'
      );
    }

    $('mcStudyList').innerHTML = html.join('');
    wireSpeakButtons($('mcStudyList'));
    // Answers are hidden until the reader asks — one question at a time.
    $('mcStudyList').querySelectorAll('.st__reveal').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var card = btn.closest('.st');
        var open = card.classList.toggle('is-revealed');
        btn.textContent = open ? 'Hide answer · 收起答案' : 'Show answer · 看答案';
        var held = card.querySelector('.speak');
        if (held) held.classList.toggle('is-held', !open && held.dataset.hold === '1');
      });
    });
    renderTypeChips();
    applyFilters();
  }

  function renderTypeChips() {
    var counts = {};
    state.bank.questions.forEach(function (q) { counts[q.type] = (counts[q.type] || 0) + 1; });
    var chips = ['<button type="button" class="mc-chip' + (state.filterType === 'all' ? ' is-on' : '') +
      '" data-type="all">All 全部 (' + state.bank.questions.length + ')</button>'];
    Object.keys(counts).sort().forEach(function (t) {
      chips.push('<button type="button" class="mc-chip' + (state.filterType === t ? ' is-on' : '') +
        '" data-type="' + esc(t) + '">' + esc(typeLabel(t)) + ' (' + counts[t] + ')</button>');
    });
    var box = $('mcTypeChips');
    box.innerHTML = chips.join('');
    box.querySelectorAll('.mc-chip').forEach(function (c) {
      c.addEventListener('click', function () {
        state.filterType = c.dataset.type;
        box.querySelectorAll('.mc-chip').forEach(function (x) { x.classList.toggle('is-on', x === c); });
        applyFilters();
      });
    });
  }

  function applyFilters() {
    var q = state.query.trim().toLowerCase();
    var shown = 0;
    $('mcStudyList').querySelectorAll('.st').forEach(function (el) {
      var okType = state.filterType === 'all' || el.dataset.type === state.filterType;
      var okText = !q || el.dataset.hay.indexOf(q) !== -1;
      var on = okType && okText;
      el.classList.toggle('hidden', !on);
      if (on) shown++;
    });
    // hide a round heading whose questions are all filtered out
    $('mcStudyList').querySelectorAll('.mc-round').forEach(function (grp) {
      var any = grp.querySelector('.st:not(.hidden)');
      grp.classList.toggle('hidden', !any);
    });
    var total = state.bank.questions.length;
    $('mcStudyCount').textContent = (shown === total)
      ? 'Showing all ' + total + ' questions · 顯示全部 ' + total + ' 題'
      : 'Showing ' + shown + ' of ' + total + ' · 顯示 ' + shown + ' / ' + total + ' 題';
  }

  // ---------------------------------------------------------------- level & view

  function setLevel(level) {
    $('mcLoadError').classList.add('hidden');
    loadBank(level).then(function (bank) {
      state.level = level;
      state.bank = bank;
      state.lastWrong = [];
      document.querySelectorAll('.mc-lvtab').forEach(function (t) {
        var on = t.dataset.level === level;
        t.classList.toggle('is-on', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      if (state.view === 'study') renderStudy();
      else renderQuizModeScreen();
    }).catch(function () {
      $('mcLoadError').classList.remove('hidden');
    });
  }

  function setView(view) {
    state.view = view;
    document.querySelectorAll('.mc-view').forEach(function (b) {
      b.classList.toggle('is-on', b.dataset.view === view);
    });
    if (view === 'study') {
      renderStudy();
      showSection('mcStudyView');
    } else {
      renderQuizModeScreen();
      showSection('mcQuizModeScreen');
    }
  }

  // ---------------------------------------------------------------- quiz

  function renderQuizModeScreen() {
    var bank = state.bank;
    var avail = roundsAvailable(bank);
    var opts = ['<option value="">— choose a round · 選擇場次 —</option>'];
    for (var i = 1; i <= meetingCount(); i++) {
      var ready = i <= avail;
      opts.push(
        '<option value="' + i + '"' + (ready ? '' : ' disabled') + '>' +
        'M' + i + ' · ' + esc(roundLabel(i)) + (ready ? '' : ' — coming soon 題目準備中') +
        '</option>'
      );
    }
    // Changing level re-renders this panel, so keep whatever round was already
    // picked rather than making the teacher choose it again.
    var prev = $('mcRoundSelect').value;
    $('mcRoundSelect').innerHTML = opts.join('');
    $('mcRoundSelect').value = (prev && Number(prev) <= avail) ? prev : '';
    $('mcStartMeeting').disabled = !$('mcRoundSelect').value;
  }

  function startPractice(count) {
    var pool = state.bank.questions;
    state.mode = 'practice';
    state.round = null;
    state.items = shuffled(pool).slice(0, Math.min(count, pool.length));
    beginQuiz();
  }

  function startWrongOnly() {
    var ids = state.lastWrong;
    var pool = state.bank.questions.filter(function (q) { return ids.indexOf(q.id) !== -1; });
    if (!pool.length) return;
    state.mode = 'practice';
    state.round = null;
    state.items = shuffled(pool);
    beginQuiz();
  }

  function startMeeting(n) {
    state.mode = 'meeting';
    state.round = 'M' + n;
    state.items = state.bank.questions.slice((n - 1) * ROUND_SIZE, n * ROUND_SIZE);
    beginQuiz();
  }

  function beginQuiz() {
    state.answers = {};
    state.optOrder = {};
    state.items.forEach(function (q, i) {
      // Practice shuffles the options too; meeting rounds keep them fixed so
      // everyone's review discussion refers to the same A/B/C/D.
      state.optOrder[i] = (state.mode === 'practice') ? shuffled([0, 1, 2, 3]) : [0, 1, 2, 3];
    });
    renderQuiz();
    updateProgress();
    showSection('mcQuizScreen');
    scrollToTop('mcQuizScreen');
  }

  function renderQuiz() {
    var bank = state.bank;
    $('mcQuizTitle').textContent = bank.label + ' · ' + bank.labelZh;
    $('mcQuizSub').textContent = state.mode === 'meeting'
      ? state.round + ' · ' + roundLabel(Number(state.round.slice(1))) + ' — recorded · 此場次會登錄成績'
      : 'Practice · 自學測驗 — not recorded · 不登錄成績';

    $('mcQuizList').innerHTML = state.items.map(function (q, i) {
      var isListen = q.type === 'listen';
      // Listening items hide the characters but still play the audio — that is
      // the exercise. Phrase-choice items must hide both, or the 🔊 button
      // reads the answer aloud.
      var holdAudio = phraseGivesAnswer(q);
      var veil = isListen || holdAudio;
      var optHtml = state.optOrder[i].map(function (origIdx, slot) {
        return '<button type="button" class="opt" data-i="' + i + '" data-o="' + origIdx + '">' +
          '<span class="key">' + String.fromCharCode(65 + slot) + '</span><span>' + esc(q.opts[origIdx]) + '</span></button>';
      }).join('');
      return '<div class="mc-q" data-i="' + i + '" data-type="' + esc(q.type) + '">' +
        '<div class="mc-q__head">' +
          '<span class="mc-q__num">Q' + (i + 1) + '</span>' +
          '<span class="mc-q__tag">' + esc(typeLabel(q.type)) + '</span>' +
          '<button type="button" class="speak' + (holdAudio ? ' is-held' : '') +
            '" data-speak="' + esc(q.zh) + '" aria-label="Listen · 播放發音">🔊</button>' +
        '</div>' +
        '<p class="mc-q__text">' + esc(q.q) + '</p>' +
        '<div class="mc-zh' + (veil ? ' is-veiled' : '') + '">' +
          '<span class="mc-zh__hanzi">' + esc(q.zh) + '</span>' +
          '<span class="mc-zh__py">' + esc(q.py) + '</span>' +
        '</div>' +
        '<div class="mc-opts">' + optHtml + '</div>' +
        '<div class="mc-why"><strong>' + esc(q.zh) + '</strong> <em>' + esc(q.py) + '</em><br>' + esc(q.why) + '</div>' +
      '</div>';
    }).join('');

    wireSpeakButtons($('mcQuizList'));
    $('mcQuizList').querySelectorAll('.opt').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var card = btn.closest('.mc-q');
        if (card.classList.contains('graded')) return;
        var i = Number(btn.dataset.i);
        state.answers[i] = Number(btn.dataset.o);
        card.querySelectorAll('.opt').forEach(function (o) { o.classList.remove('picked'); });
        btn.classList.add('picked');
        updateProgress();
      });
    });
  }

  function updateProgress() {
    var total = state.items.length;
    var done = Object.keys(state.answers).length;
    $('mcProgressFill').style.width = (done / total * 100) + '%';
    $('mcAnsweredHint').textContent = done + ' / ' + total + ' answered · 已作答';
    $('mcSubmitBtn').disabled = done < total;
  }

  function grade() {
    var score = 0, detail = [], wrongIds = [];
    state.items.forEach(function (q, i) {
      var picked = state.answers[i];
      var isCorrect = picked === q.ok;
      if (isCorrect) score++; else wrongIds.push(q.id);
      detail.push({ id: q.id, type: q.type, picked: picked, correct: isCorrect });

      var card = $('mcQuizList').querySelector('.mc-q[data-i="' + i + '"]');
      card.classList.add('graded');
      card.classList.toggle('was-wrong', !isCorrect);
      card.querySelector('.mc-zh').classList.remove('is-veiled');
      var held = card.querySelector('.speak.is-held');
      if (held) held.classList.remove('is-held');
      card.querySelectorAll('.opt').forEach(function (btn) {
        var o = Number(btn.dataset.o);
        btn.disabled = true;
        if (o === q.ok) btn.classList.add('is-correct');
        else if (o === picked) btn.classList.add('is-wrong');
      });
    });
    state.lastWrong = wrongIds;
    renderResults(score, detail, wrongIds);
    if (state.mode === 'meeting') submitToSheet(score, detail);
  }

  function renderResults(score, detail, wrongIds) {
    var total = state.items.length;
    var pct = Math.round(score / total * 100);

    $('mcScoreRing').style.setProperty('--pct', pct);
    $('mcScoreNum').textContent = score + '/' + total;
    $('mcResultHeadline').textContent =
      pct >= 90 ? 'Excellent · 太厲害了！' :
      pct >= 70 ? 'Nicely done · 做得很好！' :
      pct >= 50 ? 'Good progress · 有進步！' :
                  'Plenty to pick up · 還有很多可以學';
    $('mcResultSub').textContent =
      'You scored ' + score + ' out of ' + total + ' (' + pct + '%). ' +
      (state.mode === 'meeting'
        ? 'This round has been recorded. 本場次成績已登錄。'
        : 'Practice runs are not recorded — try again as often as you like. 自學測驗不登錄成績，可以無限次重來。');

    // Score by question type, so a teacher can see what kind of Mandarin trips them up.
    var byType = {};
    detail.forEach(function (d) {
      byType[d.type] = byType[d.type] || { n: 0, ok: 0 };
      byType[d.type].n++;
      if (d.correct) byType[d.type].ok++;
    });
    $('mcTypeBreakdown').innerHTML = Object.keys(byType).map(function (t) {
      var b = byType[t];
      return '<div class="mc-bd">' +
        '<span class="mc-bd__label">' + esc(typeLabel(t)) + '</span>' +
        '<span class="mc-bd__bar"><i style="width:' + Math.round(b.ok / b.n * 100) + '%"></i></span>' +
        '<span class="mc-bd__num">' + b.ok + '/' + b.n + '</span>' +
      '</div>';
    }).join('');

    var wrongBox = $('mcWrongList');
    if (!wrongIds.length) {
      wrongBox.innerHTML = '<p class="mc-allright">No mistakes this time. 這次全對！</p>';
    } else {
      var byId = {};
      state.items.forEach(function (q) { byId[q.id] = q; });
      wrongBox.innerHTML =
        '<h3 class="mc-wrong-h">What to review · 需要複習的 ' + wrongIds.length + ' 題</h3>' +
        wrongIds.map(function (id) {
          var q = byId[id];
          return '<div class="mc-wrong">' +
            '<div class="mc-wrong__top">' +
              '<span class="mc-wrong__zh">' + esc(q.zh) + '</span>' +
              '<span class="mc-wrong__py">' + esc(q.py) + '</span>' +
              '<button type="button" class="speak" data-speak="' + esc(q.zh) + '" aria-label="Listen · 播放發音">🔊</button>' +
            '</div>' +
            '<p class="mc-wrong__ans"><strong>Answer:</strong> ' + esc(q.opts[q.ok]) + '</p>' +
            '<p class="mc-wrong__why">' + esc(q.why) + '</p>' +
          '</div>';
        }).join('');
      wireSpeakButtons(wrongBox);
    }

    $('mcRetryWrongBtn').classList.toggle('hidden', !wrongIds.length);
    $('mcRetryWrongBtn').textContent = 'Practice these ' + wrongIds.length + ' again · 重練錯題';
    showSection('mcResultScreen');
    scrollToTop('mcResultScreen');
  }

  function submitToSheet(score, detail) {
    if (!cfg.webhookUrl) return;
    var note = $('mcSaveNote');
    note.textContent = 'Saving your result… 正在登錄成績…';
    note.classList.remove('hidden');
    fetch(cfg.webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      // One routing key for all four levels, with the level in its own field.
      // The sheet is chosen by the assignment, not by the level — that is what
      // the level COLUMN is for — so adding a level needs no Apps Script change
      // and no redeploy. Sending fet-mandarin-<level> instead made every new
      // level fall through to a missing spreadsheet until someone redeployed,
      // which is how both the per-level and the culture keys broke.
      body: JSON.stringify({
        quiz: 'fet-mandarin-challenge',
        level: state.level,
        teacher_id: state.teacherId,
        teacher_name: state.teacherName,
        round: state.round,
        score: score,
        total: state.items.length,
        answers: detail,
        user_agent: navigator.userAgent
      })
    }).then(function (res) { return res.text(); })
      .then(function (text) {
        // Apps Script always answers HTTP 200, even when it caught an error
        // server-side (e.g. writing to the wrong/missing spreadsheet) — a
        // resolved fetch is not proof the row was written, only that Google
        // received the request. Parse the body and check {ok:true} for real.
        var data;
        try { data = JSON.parse(text); } catch (e) { data = null; }
        if (data && data.ok) {
          note.textContent = 'Result recorded. 成績已登錄。';
        } else {
          console.error('submitToSheet: server reported failure', data && data.error);
          note.textContent = 'Your score is shown above, but it could not be saved. Please tell Luke. 成績無法登錄，請告知承辦人。';
        }
      })
      .catch(function () {
        // The score is already on screen either way — never block on the sheet.
        note.textContent = 'Your score is shown above, but it could not be saved. Please tell Luke. 成績無法登錄，請告知承辦人。';
      });
  }

  // ---------------------------------------------------------------- wiring

  // The level tabs and the submission form's level menu are two ways of saying
  // the same thing, so each keeps the other honest.
  document.querySelectorAll('.mc-lvtab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      setLevel(tab.dataset.level);
      if ($('mcLevelSelect')) $('mcLevelSelect').value = tab.dataset.level;
    });
  });
  if ($('mcLevelSelect')) {
    $('mcLevelSelect').addEventListener('change', function () {
      if (this.value) setLevel(this.value);
    });
  }
  document.querySelectorAll('.mc-view').forEach(function (b) {
    b.addEventListener('click', function () { setView(b.dataset.view); });
  });

  $('mcSearch').addEventListener('input', function () {
    state.query = this.value;
    applyFilters();
  });
  $('mcPinyinToggle').addEventListener('change', function () {
    document.body.classList.toggle('mc-no-pinyin', !this.checked);
  });
  $('mcShowAll').addEventListener('change', function () {
    document.body.classList.toggle('mc-show-all', this.checked);
  });

  document.querySelectorAll('[data-practice]').forEach(function (btn) {
    btn.addEventListener('click', function () { startPractice(Number(btn.dataset.practice)); });
  });
  $('mcRoundSelect').addEventListener('change', function () {
    $('mcStartMeeting').disabled = !this.value;
  });
  $('mcStartMeeting').addEventListener('click', function () {
    var n = Number($('mcRoundSelect').value);
    if (!n) return;
    var lvlSel = $('mcLevelSelect');
    if (lvlSel && !lvlSel.value) {
      $('mcGateError').textContent = 'Please choose your level. 請選擇級別。';
      $('mcGateError').classList.remove('hidden');
      return;
    }
    var id = $('mcTeacherId').value.trim();
    var name = $('mcTeacherName').value.trim();
    if (!id || !name) {
      $('mcGateError').textContent =
        'Please fill in both your teacher ID and your name. 請填寫編號與姓名。';
      $('mcGateError').classList.remove('hidden');
      return;
    }
    $('mcGateError').classList.add('hidden');
    state.teacherId = id;
    state.teacherName = name;
    startMeeting(n);
  });

  $('mcSubmitBtn').addEventListener('click', grade);
  $('mcQuitBtn').addEventListener('click', function () {
    if (Object.keys(state.answers).length &&
        !confirm('Leave this attempt? Your answers will be lost. 確定離開？作答會清空。')) return;
    showSection('mcQuizModeScreen');
  });
  $('mcReviewBtn').addEventListener('click', function () {
    showSection('mcQuizScreen');
    scrollToTop('mcQuizScreen');
  });
  $('mcRetryWrongBtn').addEventListener('click', startWrongOnly);
  $('mcAnotherBtn').addEventListener('click', function () {
    renderQuizModeScreen();
    showSection('mcQuizModeScreen');
    scrollToTop('mcQuizModeScreen');
  });
  $('mcBackToStudy').addEventListener('click', function () { setView('study'); });

  document.querySelectorAll('[data-rate]').forEach(function (b) {
    b.addEventListener('click', function () { setRate(parseFloat(b.dataset.rate)); });
  });
  setRate(rate);   // reflect the remembered choice in the buttons

  // Jump straight to the monthly submission fields — this is what most
  // teachers actually came here to find, buried two panels down otherwise.
  var jumpBtn = $('mcJumpMonthly');
  if (jumpBtn) {
    jumpBtn.addEventListener('click', function (e) {
      e.preventDefault();
      setView('quiz');
      scrollToTop('mcMeetingPanel');
    });
  }

  // ---------------------------------------------------------------- boot

  preloadAll();
  setLevel('beginner');
  if (location.hash === '#mcMeetingPanel') {
    setView('quiz');
    setTimeout(function () { scrollToTop('mcMeetingPanel'); }, 60);
  }
})();
