/* ============================================================
   Zhongzheng — Club sub-page helpers (TTS + interactive quiz)
   Self-contained, vanilla JS, no deps.
   ============================================================ */
(function () {
  /* ---------- 1. TTS via Web Speech API ---------- */
  function pickEnVoice() {
    var vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
    /* Prefer US English; fall back to any en-* voice; then any voice. */
    return vs.find(function (v) { return v.lang === 'en-US'; }) ||
           vs.find(function (v) { return /^en[-_]/.test(v.lang); }) ||
           vs[0] || null;
  }

  function speak(text, btn) {
    if (!('speechSynthesis' in window) || !text) return;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-US';
    u.rate = 0.88;
    u.pitch = 1.0;
    var v = pickEnVoice();
    if (v) u.voice = v;
    if (btn) {
      btn.classList.add('is-speaking');
      u.onend = u.onerror = function () { btn.classList.remove('is-speaking'); };
    }
    speechSynthesis.speak(u);
  }

  /* Hydrate any element with data-say (on .spk button) */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.spk');
    if (!btn) return;
    e.preventDefault();
    speak(btn.getAttribute('data-say'), btn);
  });

  /* Some browsers load voices async — touch once to populate. */
  if ('speechSynthesis' in window) {
    speechSynthesis.getVoices();
    if (typeof speechSynthesis.onvoiceschanged !== 'undefined') {
      speechSynthesis.onvoiceschanged = function () { speechSynthesis.getVoices(); };
    }
  }

  /* ---------- 2. Quiz ---------- */
  function setupQuiz(root) {
    var qs = root.querySelectorAll('.quiz__q');
    if (!qs.length) return;
    var total = qs.length;
    var answered = 0;
    var correct = 0;
    var resultEl = root.querySelector('.quiz__result');
    var resetBtn = root.querySelector('.quiz__reset');

    function reset() {
      answered = 0; correct = 0;
      qs.forEach(function (q) {
        q.classList.remove('done', 'is-wrong');
        var fb = q.querySelector('.quiz__fb');
        if (fb) { fb.textContent = ''; fb.classList.remove('show'); }
        q.querySelectorAll('button[data-opt]').forEach(function (b) {
          b.disabled = false;
          b.classList.remove('right', 'wrong');
        });
      });
      if (resultEl) resultEl.style.display = 'none';
    }
    reset();

    qs.forEach(function (q) {
      var ans = (q.getAttribute('data-answer') || '').toLowerCase();
      var why = q.getAttribute('data-why') || '';
      var whyZh = q.getAttribute('data-why-zh') || '';
      q.querySelectorAll('button[data-opt]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          if (q.classList.contains('done')) return;
          q.classList.add('done');
          answered++;
          var chosen = btn.getAttribute('data-opt').toLowerCase();
          var isRight = chosen === ans;
          if (isRight) correct++;
          else q.classList.add('is-wrong');
          /* Mark each option visually */
          q.querySelectorAll('button[data-opt]').forEach(function (b) {
            b.disabled = true;
            var v = b.getAttribute('data-opt').toLowerCase();
            if (v === ans) b.classList.add('right');
            else if (b === btn) b.classList.add('wrong');
          });
          /* Feedback line */
          var fb = q.querySelector('.quiz__fb');
          if (fb) {
            var prefix = isRight ? '✓ ' : '✗ ';
            var line = isRight
              ? 'Correct! ' + (why || '')
              : 'The right answer is "' + ans.toUpperCase() + '". ' + (why || '');
            fb.innerHTML = '<strong>' + prefix + '</strong>' + line +
              (whyZh ? '<br><span style="font-family:\'PingFang TC\',sans-serif;color:var(--ink-soft);font-size:14.5px">' + whyZh + '</span>' : '');
            fb.classList.add('show');
          }
          if (answered === total) showResult();
        });
      });
    });

    function showResult() {
      if (!resultEl) return;
      var pct = Math.round(correct / total * 100);
      var msg, msgZh;
      if (pct >= 90) { msg = 'Outstanding! You really know this.'; msgZh = '太厲害了！這個主題你已經掌握了。'; }
      else if (pct >= 70) { msg = 'Great work — solid grasp of the vocabulary.'; msgZh = '很棒！這些單字你已經學得很扎實。'; }
      else if (pct >= 50) { msg = 'Good start. Try reviewing the words above and try again.'; msgZh = '不錯的起步！再回去複習上面的單字，然後再試一次。'; }
      else { msg = "Don't worry — read the words and sentences again, then come back."; msgZh = '別擔心！先回上面再讀一次單字和句子，再回來挑戰。'; }
      resultEl.innerHTML =
        '<div class="quiz__score">You got <strong>' + correct + ' / ' + total + '</strong> right · ' + pct + '%</div>' +
        '<div class="quiz__msg">' + msg + '</div>' +
        '<div class="quiz__msg-zh">' + msgZh + '</div>';
      resultEl.style.display = 'block';
      resultEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        reset();
        root.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }

  document.querySelectorAll('.quiz').forEach(setupQuiz);
})();
