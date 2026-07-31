/**
 * Mandarin Challenge — question-bank quiz engine (FETs).
 * ------------------------------------------------------
 * Three levels, each backed by its own JSON bank under
 * /fets/mandarin-challenge/data/<level>.json
 *
 * Two modes:
 *   practice  — random draw from the whole bank, unlimited retries, NOT recorded
 *   meeting   — round M1..M9, a fixed 20-question slice, identical for everyone,
 *               submitted to the Google Sheet tab for that level
 *
 * The page sets window.__MC_CONFIG__ before loading this file.
 * Grading is client-side, same trust model as the other Hub quizzes
 * (see CONTRIBUTING.md §8).
 */
(function () {
  var cfg = window.__MC_CONFIG__;
  if (!cfg) return;

  var ROUND_SIZE = 20;
  var $ = function (id) { return document.getElementById(id); };

  var state = {
    level: null,        // 'beginner' | 'intermediate' | 'advanced'
    bank: null,         // parsed JSON for the current level
    mode: null,         // 'practice' | 'meeting'
    round: null,        // 'M1'..'M9' when mode === 'meeting'
    items: [],          // the questions actually being asked, in display order
    answers: {},        // itemIndex -> chosen option index
    optOrder: {},       // itemIndex -> array mapping displayed slot -> original option index
    teacherId: '',
    teacherName: '',
    showPinyin: true,
    lastWrong: []       // question ids missed on the previous attempt
  };

  var banks = {};       // level -> bank (cached after first fetch)

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
  function hasZhVoice() {
    // Before the voice list resolves we assume speech works rather than
    // flashing a warning at every visitor on first paint.
    return !zhVoices.length || !!pickZhVoice();
  }
  function updateVoiceNotice() {
    var el = $('mcVoiceNotice');
    if (!el) return;
    var ok = ('speechSynthesis' in window) && hasZhVoice();
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

  function show(screen) {
    ['mcLevelScreen', 'mcModeScreen', 'mcQuizScreen', 'mcResultScreen'].forEach(function (id) {
      var el = $(id);
      if (el) el.classList.toggle('hidden', id !== screen);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Round n (1-based) covers questions [(n-1)*20, n*20).
  function roundsAvailable(bank) {
    return Math.floor(bank.questions.length / ROUND_SIZE);
  }

  function roundLabel(n) {
    var m = cfg.meetings && cfg.meetings[n - 1];
    return m ? m : 'Meeting ' + n;
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

  // ---------------------------------------------------------------- screens

  function openLevel(level) {
    var err = $('mcLoadError');
    err.classList.add('hidden');
    loadBank(level).then(function (bank) {
      state.level = level;
      state.bank = bank;
      state.lastWrong = [];
      renderModeScreen();
      show('mcModeScreen');
    }).catch(function () {
      err.classList.remove('hidden');
    });
  }

  function renderModeScreen() {
    var bank = state.bank;
    var avail = roundsAvailable(bank);
    var total = bank.questions.length;

    $('mcModeLevelName').textContent = bank.label + ' · ' + bank.labelZh;
    $('mcModeLevelBlurb').textContent = bank.blurb;
    $('mcModeLevelBlurbZh').textContent = bank.blurbZh;
    $('mcBankCount').textContent = total + ' questions in this bank · 題庫共 ' + total + ' 題';

    var opts = ['<option value="">— choose a round · 選擇場次 —</option>'];
    for (var i = 1; i <= (cfg.meetings ? cfg.meetings.length : 9); i++) {
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
    // Fixed slice, fixed order, fixed option order — everyone sits the same paper.
    state.items = state.bank.questions.slice((n - 1) * ROUND_SIZE, n * ROUND_SIZE);
    beginQuiz();
  }

  function beginQuiz() {
    state.answers = {};
    state.optOrder = {};
    state.items.forEach(function (q, i) {
      var order = [0, 1, 2, 3];
      // Practice shuffles the options too; meeting rounds keep them fixed so
      // everyone's review discussion refers to the same A/B/C/D.
      state.optOrder[i] = (state.mode === 'practice') ? shuffled(order) : order;
    });
    renderQuiz();
    updateProgress();
    show('mcQuizScreen');
  }

  function renderQuiz() {
    var bank = state.bank;
    $('mcQuizTitle').textContent = bank.label + ' · ' + bank.labelZh;
    $('mcQuizSub').textContent = state.mode === 'meeting'
      ? state.round + ' · ' + roundLabel(Number(state.round.slice(1))) + ' — recorded · 此場次會登錄成績'
      : 'Practice · 自學練習 — not recorded · 不登錄成績';

    $('mcQuizList').innerHTML = state.items.map(function (q, i) {
      var isListen = q.type === 'listen';
      var order = state.optOrder[i];
      var optHtml = order.map(function (origIdx, slot) {
        var letter = String.fromCharCode(65 + slot);
        return '<button type="button" class="opt" data-i="' + i + '" data-o="' + origIdx + '">' +
          '<span class="key">' + letter + '</span><span>' + esc(q.opts[origIdx]) + '</span></button>';
      }).join('');

      // Listening items hide the characters until the question is graded —
      // that is the whole point of the type.
      var zhBlock =
        '<div class="mc-zh' + (isListen ? ' is-veiled' : '') + '">' +
          '<span class="mc-zh__hanzi">' + esc(q.zh) + '</span>' +
          '<span class="mc-zh__py">' + esc(q.py) + '</span>' +
        '</div>';

      return '<div class="mc-q" data-i="' + i + '" data-type="' + esc(q.type) + '">' +
        '<div class="mc-q__head">' +
          '<span class="mc-q__num">Q' + (i + 1) + '</span>' +
          '<span class="mc-q__tag">' + esc(typeLabel(q.type)) + '</span>' +
          '<button type="button" class="speak" data-speak="' + esc(q.speak) + '" ' +
            'aria-label="Listen · 播放發音">🔊</button>' +
        '</div>' +
        '<p class="mc-q__text">' + esc(q.q) + '</p>' +
        zhBlock +
        '<div class="mc-opts">' + optHtml + '</div>' +
        '<div class="mc-why"><strong>' + esc(q.zh) + '</strong> <em>' + esc(q.py) + '</em><br>' + esc(q.why) + '</div>' +
      '</div>';
    }).join('');

    applyPinyinVisibility();

    $('mcQuizList').querySelectorAll('[data-speak]').forEach(function (b) {
      b.addEventListener('click', function () { speak(b.getAttribute('data-speak'), b); });
    });
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

  function typeLabel(t) {
    return {
      word: 'Vocabulary 字詞',
      listen: 'Listening 聽力',
      expression: 'Expression 用語',
      dialogue: 'Response 應答',
      situation: 'Situation 情境',
      measure: 'Measure word 量詞',
      idiom: 'Idiom 成語'
    }[t] || t;
  }

  function applyPinyinVisibility() {
    document.body.classList.toggle('mc-no-pinyin', !state.showPinyin);
  }

  function updateProgress() {
    var total = state.items.length;
    var done = Object.keys(state.answers).length;
    $('mcProgressFill').style.width = (done / total * 100) + '%';
    $('mcAnsweredHint').textContent = done + ' / ' + total + ' answered · 已作答';
    $('mcSubmitBtn').disabled = done < total;
  }

  // ---------------------------------------------------------------- grading

  function grade() {
    var score = 0;
    var detail = [];
    var wrongIds = [];

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
        : 'Practice runs are not recorded — try again as often as you like. 自學練習不登錄成績，可以無限次重來。');

    // Score by question type, so a teacher can see what kind of Mandarin trips them up.
    var byType = {};
    detail.forEach(function (d) {
      byType[d.type] = byType[d.type] || { n: 0, ok: 0 };
      byType[d.type].n++;
      if (d.correct) byType[d.type].ok++;
    });
    $('mcTypeBreakdown').innerHTML = Object.keys(byType).map(function (t) {
      var b = byType[t];
      var p = Math.round(b.ok / b.n * 100);
      return '<div class="mc-bd">' +
        '<span class="mc-bd__label">' + esc(typeLabel(t)) + '</span>' +
        '<span class="mc-bd__bar"><i style="width:' + p + '%"></i></span>' +
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
              '<button type="button" class="speak" data-speak="' + esc(q.speak) + '" aria-label="Listen · 播放發音">🔊</button>' +
            '</div>' +
            '<p class="mc-wrong__ans"><strong>Answer:</strong> ' + esc(q.opts[q.ok]) + '</p>' +
            '<p class="mc-wrong__why">' + esc(q.why) + '</p>' +
          '</div>';
        }).join('');
      wrongBox.querySelectorAll('[data-speak]').forEach(function (b) {
        b.addEventListener('click', function () { speak(b.getAttribute('data-speak'), b); });
      });
    }

    $('mcRetryWrongBtn').classList.toggle('hidden', !wrongIds.length);
    $('mcRetryWrongBtn').textContent = 'Practise these ' + wrongIds.length + ' again · 重練錯題';
    show('mcResultScreen');
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

  document.querySelectorAll('[data-level]').forEach(function (card) {
    card.addEventListener('click', function () { openLevel(card.dataset.level); });
  });

  $('mcRoundSelect').addEventListener('change', function () {
    $('mcStartMeeting').disabled = !this.value;
  });

  $('mcStartMeeting').addEventListener('click', function () {
    var n = Number($('mcRoundSelect').value);
    if (!n) return;
    var id = $('mcTeacherId').value.trim();
    var name = $('mcTeacherName').value.trim();
    if (!id || !name) {
      $('mcGateError').classList.remove('hidden');
      return;
    }
    $('mcGateError').classList.add('hidden');
    state.teacherId = id;
    state.teacherName = name;
    startMeeting(n);
  });

  document.querySelectorAll('[data-practice]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      startPractice(Number(btn.dataset.practice));
    });
  });

  $('mcPinyinToggle').addEventListener('change', function () {
    state.showPinyin = this.checked;
    applyPinyinVisibility();
  });

  $('mcSubmitBtn').addEventListener('click', grade);

  $('mcQuitBtn').addEventListener('click', function () {
    if (Object.keys(state.answers).length &&
        !confirm('Leave this attempt? Your answers will be lost. 確定離開？作答會清空。')) return;
    show('mcModeScreen');
  });

  $('mcReviewBtn').addEventListener('click', function () {
    show('mcQuizScreen');
    $('mcQuizList').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  $('mcRetryWrongBtn').addEventListener('click', startWrongOnly);

  $('mcAnotherBtn').addEventListener('click', function () {
    renderModeScreen();
    show('mcModeScreen');
  });

  $('mcBackToLevels').addEventListener('click', function () { show('mcLevelScreen'); });
  $('mcResultToLevels').addEventListener('click', function () { show('mcLevelScreen'); });
})();
