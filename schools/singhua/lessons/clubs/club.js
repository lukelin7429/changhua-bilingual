/* SingHua club pages: read-aloud (Web Speech), dialogue play-all, matching game, quiz.
   Each page sets window.CLUB_WORDS = [{en, zh}, ...] before loading this file. */
(function () {
  var hasTTS = 'speechSynthesis' in window;

  function stopAll() {
    if (hasTTS) speechSynthesis.cancel();
    document.querySelectorAll('.is-speaking').forEach(function (el) { el.classList.remove('is-speaking'); });
  }
  function say(text, btn, onEnd) {
    if (!hasTTS || !text) { if (onEnd) onEnd(); return; }
    try {
      var u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-US'; u.rate = 0.85;
      if (btn) btn.classList.add('is-speaking');
      u.onend = u.onerror = function () { if (btn) btn.classList.remove('is-speaking'); if (onEnd) onEnd(); };
      speechSynthesis.speak(u);
    } catch (e) { if (onEnd) onEnd(); }
  }

  // single 🔊 buttons
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.speak');
    if (!b) return;
    stopAll();
    say(b.getAttribute('data-say'), b);
  });

  // ▶ play the whole dialogue, line by line
  var playBtn = document.querySelector('.playall');
  if (playBtn) {
    playBtn.addEventListener('click', function () {
      stopAll();
      var lines = [].slice.call(document.querySelectorAll('.dlg .line'));
      var i = 0;
      (function next() {
        if (i > 0) lines[i - 1].classList.remove('is-speaking');
        if (i >= lines.length) return;
        var line = lines[i++];
        line.classList.add('is-speaking');
        say(line.getAttribute('data-say'), null, function () { setTimeout(next, 350); });
      })();
    });
  }

  function confetti(big) {
    var n = big ? 90 : 18, colors = ['#D42A2A', '#EB7A2E', '#F2B705', '#3C9A4A', '#2F6FC0', '#1B3570'];
    for (var i = 0; i < n; i++) {
      var d = document.createElement('div');
      d.className = 'confetti';
      d.style.left = (Math.random() * 100) + 'vw';
      d.style.background = colors[Math.floor(Math.random() * colors.length)];
      d.style.animationDuration = (1.1 + Math.random() * 1.3) + 's';
      d.style.animationDelay = (Math.random() * (big ? 0.5 : 0.15)) + 's';
      d.style.width = (7 + Math.random() * 7) + 'px';
      d.style.height = (10 + Math.random() * 8) + 'px';
      document.body.appendChild(d);
      (function (el) { setTimeout(function () { el.remove(); }, big ? 3400 : 2700); })(d);
    }
  }

  // matching game (English ↔ 中文), shuffled every round
  var WORDS = window.CLUB_WORDS || [];
  var enCol = document.getElementById('gEn'), zhCol = document.getElementById('gZh');
  var sc = document.getElementById('gScore'), done = document.getElementById('gDone'), reset = document.getElementById('gReset');
  if (enCol && zhCol && WORDS.length) {
    var selEn = null, matched = 0;
    var shuffle = function (a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; };
    var fx = function (el, cls) { el.classList.add(cls); setTimeout(function () { el.classList.remove(cls); }, 520); };
    var tile = function (w, zh) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'gtile' + (zh ? ' zh' : '');
      b.textContent = zh ? w.zh : w.en; b.dataset.k = w.en;
      return b;
    };
    var pickEn = function (b) {
      if (b.classList.contains('done')) return;
      if (selEn) selEn.classList.remove('sel');
      selEn = b; b.classList.add('sel');
      stopAll(); say(b.dataset.k);
    };
    var pickZh = function (b) {
      if (b.classList.contains('done') || !selEn) return;
      if (b.dataset.k === selEn.dataset.k) {
        var e = selEn;
        e.classList.remove('sel'); e.classList.add('done'); b.classList.add('done');
        fx(e, 'pop'); fx(b, 'pop'); confetti(false);
        selEn = null; matched++; sc.textContent = matched;
        if (matched === WORDS.length) { done.classList.add('show'); confetti(true); }
      } else { fx(b, 'shake'); fx(selEn, 'shake'); }
    };
    var build = function () {
      enCol.innerHTML = ''; zhCol.innerHTML = ''; selEn = null; matched = 0;
      sc.textContent = '0'; done.classList.remove('show');
      shuffle(WORDS).forEach(function (w) { var b = tile(w, false); b.addEventListener('click', function () { pickEn(b); }); enCol.appendChild(b); });
      shuffle(WORDS).forEach(function (w) { var b = tile(w, true); b.addEventListener('click', function () { pickZh(b); }); zhCol.appendChild(b); });
    };
    if (reset) reset.addEventListener('click', build);
    build();
  }

  // quiz: one try per question, feedback in Chinese after answering
  var qs = [].slice.call(document.querySelectorAll('.qz'));
  var scoreEl = document.getElementById('qzScore');
  var right = 0, answered = 0;
  qs.forEach(function (q) {
    var opts = [].slice.call(q.querySelectorAll('.opt'));
    var fb = q.querySelector('.qz__fb');
    opts.forEach(function (o) {
      o.addEventListener('click', function () {
        if (q.dataset.done) return;
        q.dataset.done = '1'; answered++;
        var good = opts.filter(function (x) { return x.dataset.ok === '1'; })[0];
        opts.forEach(function (x) { x.disabled = true; });
        good.classList.add('is-correct');
        if (o === good) {
          right++;
          fb.className = 'qz__fb show ok';
          fb.innerHTML = '✓ Correct! 答對了！ ' + fb.dataset.exp;
          confetti(false);
        } else {
          o.classList.add('is-wrong');
          fb.className = 'qz__fb show no';
          var ans = good.querySelector('.opt__t');
          var stop = /[.!?]$/.test(ans.textContent.trim()) ? ' ' : '。';
          fb.innerHTML = '✗ Not quite. 正確答案是 <b>' + good.querySelector('.key').textContent + '. ' + ans.innerHTML + '</b>' + stop + fb.dataset.exp;
        }
        if (answered === qs.length && scoreEl) {
          scoreEl.textContent = 'Score 得分：' + right + ' / ' + qs.length + (right === qs.length ? ' 🎉 Perfect! 全對！' : '');
          if (right === qs.length) confetti(true);
        }
      });
    });
  });
})();
