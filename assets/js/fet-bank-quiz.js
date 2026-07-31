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
 * The page sets window.__MC_CONFIG__ before loading this file.
 * Grading is client-side, same trust model as the other Hub quizzes
 * (see CONTRIBUTING.md §8).
 */
(function () {
  var cfg = window.__MC_CONFIG__;
  if (!cfg) return;

  var ROUND_SIZE = 20;
  var LEVELS = ['beginner', 'intermediate', 'advanced'];
  var $ = function (id) { return document.getElementById(id); };

  var state = {
    view: 'study',
    level: 'beginner',
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
    var ok = ('speechSynthesis' in window) && (!zhVoices.length || !!pickZhVoice());
    el.classList.toggle('hidden', ok);
  }
  if ('speechSynthesis' in window) {
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
  }
  function speak(text, btn) {
    if (!('speechSynthesis' in window) || !text) return;
    speechSynthesis.cancel();
    document.querySelectorAll('.speak.is-speaking').forEach(function (b) {
      b.classList.remove('is-speaking');
    });
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

  function studyItemHtml(q) {
    var opts = q.opts.map(function (o, i) {
      return '<li class="st__opt' + (i === q.ok ? ' is-ok' : '') + '">' +
        '<span class="k">' + String.fromCharCode(65 + i) + '</span><span>' + esc(o) + '</span></li>';
    }).join('');
    return '<div class="st' + (q.type === 'listen' ? ' st--listen' : '') + '" ' +
        'data-type="' + esc(q.type) + '" data-hay="' + esc(searchHaystack(q)) + '">' +
      '<div class="st__head">' +
        '<span class="st__id">' + esc(q.id) + '</span>' +
        '<span class="st__tag">' + esc(typeLabel(q.type)) + '</span>' +
        '<button type="button" class="speak" data-speak="' + esc(q.zh) + '" aria-label="Listen · 播放發音">🔊</button>' +
      '</div>' +
      '<div class="st__zh"><span class="st__hanzi">' + esc(q.zh) + '</span>' +
        '<span class="st__py">' + esc(q.py) + '</span></div>' +
      '<p class="st__q">' + esc(q.q) + '</p>' +
      '<ul class="st__opts">' + opts + '</ul>' +
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
    $('mcRoundSelect').innerHTML = opts.join('');
    $('mcRoundSelect').value = '';
    $('mcStartMeeting').disabled = true;
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
      var optHtml = state.optOrder[i].map(function (origIdx, slot) {
        return '<button type="button" class="opt" data-i="' + i + '" data-o="' + origIdx + '">' +
          '<span class="key">' + String.fromCharCode(65 + slot) + '</span><span>' + esc(q.opts[origIdx]) + '</span></button>';
      }).join('');
      return '<div class="mc-q" data-i="' + i + '" data-type="' + esc(q.type) + '">' +
        '<div class="mc-q__head">' +
          '<span class="mc-q__num">Q' + (i + 1) + '</span>' +
          '<span class="mc-q__tag">' + esc(typeLabel(q.type)) + '</span>' +
          '<button type="button" class="speak" data-speak="' + esc(q.zh) + '" aria-label="Listen · 播放發音">🔊</button>' +
        '</div>' +
        '<p class="mc-q__text">' + esc(q.q) + '</p>' +
        // Listening items hide the characters until the question is graded —
        // that is the whole point of the type.
        '<div class="mc-zh' + (isListen ? ' is-veiled' : '') + '">' +
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
    $('mcRetryWrongBtn').textContent = 'Practise these ' + wrongIds.length + ' again · 重練錯題';
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
      body: JSON.stringify({
        quiz: 'fet-mandarin-' + state.level,
        level: state.level,
        teacher_id: state.teacherId,
        teacher_name: state.teacherName,
        round: state.round,
        score: score,
        total: state.items.length,
        answers: detail,
        user_agent: navigator.userAgent
      })
    }).then(function () {
      note.textContent = 'Result recorded. 成績已登錄。';
    }).catch(function () {
      // The score is already on screen either way — never block on the sheet.
      note.textContent = 'Your score is shown above, but it could not be saved. Please tell Luke. 成績無法登錄，請告知承辦人。';
    });
  }

  // ---------------------------------------------------------------- wiring

  document.querySelectorAll('.mc-lvtab').forEach(function (tab) {
    tab.addEventListener('click', function () { setLevel(tab.dataset.level); });
  });
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
  $('mcHideAnswers').addEventListener('change', function () {
    document.body.classList.toggle('mc-hide-answers', this.checked);
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
    var id = $('mcTeacherId').value.trim();
    var name = $('mcTeacherName').value.trim();
    if (!id || !name) { $('mcGateError').classList.remove('hidden'); return; }
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

  // ---------------------------------------------------------------- boot

  preloadAll();
  setLevel('beginner');
})();
