/**
 * Shared quiz engine for FET pages (Mandarin Challenges / School Culture).
 * Each page sets window.__QZ_CONFIG__ = { webhookUrl, round, quizId, questions, hasSpeech }
 * before loading this file. Grading is client-side (same trust model as
 * schools/hsinmin/news/shadow-puppet/'s .qz quiz) — see CONTRIBUTING.md §8.
 */
(function () {
  var cfg = window.__QZ_CONFIG__;
  if (!cfg) return;

  var gate = document.getElementById('qzGate');
  var body = document.getElementById('qzBody');
  var list = document.getElementById('qzList');
  var results = document.getElementById('qzResults');
  var progressFill = document.getElementById('qzProgressFill');
  var answeredHint = document.getElementById('qzAnsweredHint');
  var submitBtn = document.getElementById('qzSubmitBtn');
  var startBtn = document.getElementById('qzStartBtn');
  var reviewBtn = document.getElementById('qzReviewBtn');

  var answers = {};
  var teacherId = '';
  var teacherName = '';
  var round = '';
  var level = '';

  var roundSelect = document.getElementById('qzRoundSelect');
  var levelSelect = document.getElementById('qzLevelSelect');

  if (roundSelect && cfg.meetings) {
    roundSelect.innerHTML = ['<option value="">— choose a round · 選擇場次 —</option>']
      .concat(cfg.meetings.map(function (label, i) {
        return '<option value="M' + (i + 1) + '">M' + (i + 1) + ' · ' + label + '</option>';
      })).join('');
  }

  // ----- Web Speech (Mandarin phrase playback, zh-TW) -----
  var zhVoices = [];
  function loadVoices() { zhVoices = (window.speechSynthesis ? speechSynthesis.getVoices() : []) || []; }
  if (cfg.hasSpeech && 'speechSynthesis' in window) {
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
  }
  function pickZhVoice() {
    if (!zhVoices.length) return null;
    return zhVoices.find(function (v) { return /zh[-_]TW/i.test(v.lang); })
      || zhVoices.find(function (v) { return /zh/i.test(v.lang); })
      || null;
  }
  function speak(text, btn) {
    if (!('speechSynthesis' in window)) return;
    speechSynthesis.cancel();
    document.querySelectorAll('.speak.is-speaking').forEach(function (b) { b.classList.remove('is-speaking'); });
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'zh-TW'; u.rate = 0.9;
    var v = pickZhVoice(); if (v) u.voice = v;
    if (btn) {
      btn.classList.add('is-speaking');
      u.onend = function () { btn.classList.remove('is-speaking'); };
      u.onerror = function () { btn.classList.remove('is-speaking'); };
    }
    speechSynthesis.speak(u);
  }

  function renderQuestions() {
    list.innerHTML = cfg.questions.map(function (item, i) {
      var speakBtn = (cfg.hasSpeech && item.speak)
        ? '<button type="button" class="speak" data-speak="' + item.speak.replace(/"/g, '&quot;') + '" aria-label="Listen to the phrase">🔊</button>'
        : '';
      var opts = item.opts.map(function (opt, oi) {
        var letter = String.fromCharCode(65 + oi);
        return '<button type="button" class="opt" data-oi="' + oi + '"><span class="key">' + letter + '</span>' + opt + '</button>';
      }).join('');
      return (
        '<div class="qz" data-index="' + i + '" data-correct="' + item.correct + '">' +
          '<div class="qz__q"><span class="num">Q' + (i + 1) + '.</span><span>' + item.q + '</span>' + speakBtn + '</div>' +
          '<div class="qz__zh">' + item.zh + '</div>' +
          '<div class="qz__opts">' + opts + '</div>' +
          '<div class="qz__fb">' + item.explain + '</div>' +
        '</div>'
      );
    }).join('');

    list.querySelectorAll('[data-speak]').forEach(function (b) {
      b.addEventListener('click', function () { speak(b.getAttribute('data-speak'), b); });
    });
    list.querySelectorAll('.qz').forEach(function (qDiv) {
      qDiv.querySelectorAll('.opt').forEach(function (optBtn) {
        optBtn.addEventListener('click', function () {
          if (qDiv.classList.contains('graded')) return;
          var idx = Number(qDiv.dataset.index);
          answers[idx] = Number(optBtn.dataset.oi);
          qDiv.querySelectorAll('.opt').forEach(function (o) { o.classList.remove('picked'); });
          optBtn.classList.add('picked');
          updateProgress();
        });
      });
    });
  }

  function updateProgress() {
    var total = cfg.questions.length;
    var answeredCount = Object.keys(answers).length;
    progressFill.style.width = (answeredCount / total * 100) + '%';
    answeredHint.textContent = answeredCount + ' / ' + total + ' answered';
    submitBtn.disabled = answeredCount < total;
  }

  startBtn.addEventListener('click', function () {
    teacherId = document.getElementById('qzTeacherId').value.trim();
    teacherName = document.getElementById('qzTeacherName').value.trim();
    round = roundSelect ? roundSelect.value : (cfg.round || '');
    level = levelSelect ? levelSelect.value : '';
    if (roundSelect && !round) {
      alert('Please choose which meeting this is for · 請選擇場次');
      return;
    }
    if (levelSelect && !level) {
      alert('Please choose whether this is your first year · 請選擇年資');
      return;
    }
    if (!teacherId || !teacherName) {
      alert('Please enter both your teacher ID and name · 請填寫編號與姓名');
      return;
    }
    gate.classList.add('hidden');
    body.classList.remove('hidden');
    renderQuestions();
    updateProgress();
  });

  submitBtn.addEventListener('click', function () {
    var qzs = Array.prototype.slice.call(list.querySelectorAll('.qz'));
    var score = 0;
    var detail = [];
    qzs.forEach(function (qDiv) {
      var idx = Number(qDiv.dataset.index);
      var correct = Number(qDiv.dataset.correct);
      var picked = answers[idx];
      var isCorrect = picked === correct;
      if (isCorrect) score++;
      detail.push({ q: idx, picked: picked, correct: isCorrect });
      qDiv.classList.add('graded');
      qDiv.querySelectorAll('.opt').forEach(function (optBtn) {
        var oi = Number(optBtn.dataset.oi);
        optBtn.disabled = true;
        if (oi === correct) optBtn.classList.add('is-correct');
        else if (oi === picked) optBtn.classList.add('is-wrong');
      });
    });

    var total = cfg.questions.length;
    var pct = Math.round((score / total) * 100);
    document.getElementById('qzScoreRing').style.setProperty('--pct', pct);
    document.getElementById('qzScoreNum').textContent = score + '/' + total;
    document.getElementById('qzResultHeadline').textContent =
      pct >= 80 ? 'Great job! 太棒了！' : pct >= 50 ? 'Good effort! 不錯的嘗試！' : 'Worth another look · 值得再看一次';
    document.getElementById('qzResultSub').textContent =
      'You scored ' + score + ' out of ' + total + ' (' + pct + '%). Scroll down to review each question.';

    body.classList.add('hidden');
    results.classList.remove('hidden');

    if (cfg.webhookUrl) {
      fetch(cfg.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({
          quiz: cfg.quizIdPrefix ? cfg.quizIdPrefix + level : cfg.quizId,
          teacher_id: teacherId,
          teacher_name: teacherName,
          level: level,
          round: round,
          score: score,
          total: total,
          answers: detail,
          user_agent: navigator.userAgent,
        }),
      }).then(function (res) { return res.text(); })
        .then(function (text) {
          // Apps Script answers HTTP 200 even when it caught an error, so a
          // resolved fetch is not proof the row was written. Check the body.
          var data;
          try { data = JSON.parse(text); } catch (e) { data = null; }
          if (!data || !data.ok) {
            console.error('school-culture submit: server reported failure', data && data.error);
            alert('Your score is shown on screen, but it could not be saved. Please tell Luke.\n成績無法登錄，請告知承辦人。');
          }
        })
        .catch(function () {
          alert('Your score is shown on screen, but it could not be saved. Please tell Luke.\n成績無法登錄，請告知承辦人。');
        });
    }
  });

  reviewBtn.addEventListener('click', function () {
    results.classList.add('hidden');
    body.classList.remove('hidden');
    list.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
})();
