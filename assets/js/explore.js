/* ===========================================================
   Explore — card wall renderer + self-check quiz
   Reads /explore/data/index.json. Adding a pack or chapter is a
   JSON edit plus an index.html; nothing here needs to change.

   The quiz is deliberately stateless: no localStorage, no Leitner
   scheduling, no upload. It is a self-check, not an assessment.
   =========================================================== */
(function () {
  'use strict';

  var DATA_URL = '/explore/data/index.json';
  var _cache = null;

  function loadData() {
    if (_cache) return _cache;
    _cache = fetch(DATA_URL, { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
    return _cache;
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function liveChapters(pack) {
    return (pack.chapters || []).filter(function (c) { return c.status === 'live'; });
  }

  /* ---------- Card wall (/explore/) ---------- */
  function packCard(pack) {
    var live = liveChapters(pack).length;
    var total = (pack.chapters || []).length;
    var isLive = pack.status === 'live';
    var cls = 'xp-card xp-card--' + esc(pack.theme) + (isLive ? '' : ' xp-card--soon');

    var tag = isLive
      ? '<span class="xp-tag">' + live + ' of ' + total + ' ready</span>'
      : '<span class="xp-tag xp-tag--soon">Coming soon · 準備中</span>';

    var cta = isLive
      ? '<span class="xp-card-cta">Start reading →</span>'
      : '<span class="xp-card-cta" style="color:var(--hub-ink-faint)">Not open yet · 尚未開放</span>';

    var inner =
      '<div class="xp-card-hero" aria-hidden="true">' + esc(pack.icon) + '</div>' +
      '<div class="xp-card-body">' +
        '<span class="xp-card-eyebrow">Topic Pack · 主題包' + tag + '</span>' +
        '<h2 class="xp-card-title">' + esc(pack.title) + '</h2>' +
        '<p class="xp-card-title-zh">' + esc(pack.title_zh) + '</p>' +
        '<p class="xp-card-desc">' + esc(pack.blurb) + '</p>' +
        '<p class="xp-card-desc-zh">' + esc(pack.blurb_zh) + '</p>' +
        cta +
      '</div>';

    return isLive
      ? '<a class="' + cls + '" href="/explore/' + esc(pack.slug) + '/">' + inner + '</a>'
      : '<div class="' + cls + '">' + inner + '</div>';
  }

  function renderWall(el) {
    loadData().then(function (data) {
      el.innerHTML = (data.packs || []).map(packCard).join('');
      el.classList.add('is-ready');
    }).catch(function () {
      el.innerHTML = '<p class="xp-empty">The topic list could not be loaded. Please refresh the page. · 主題清單載入失敗，請重新整理。</p>';
    });
  }

  /* ---------- Chapter list (/explore/<pack>/) ---------- */
  function chapterRow(pack, ch) {
    var isLive = ch.status === 'live';
    var meta = isLive
      ? '<p class="xp-chapter-meta"><span>' + ch.minutes + ' min read</span><span>' + ch.questions + ' self-check questions</span></p>'
      : '<p class="xp-chapter-meta"><span>Coming soon · 準備中</span></p>';

    var inner =
      '<div class="xp-chapter-n">' + esc(ch.n) + '</div>' +
      '<div>' +
        '<h3 class="xp-chapter-title">' + esc(ch.title) + '</h3>' +
        '<p class="xp-chapter-title-zh">' + esc(ch.title_zh) + '</p>' +
        '<p class="xp-chapter-desc">' + esc(ch.blurb) + '</p>' +
        meta +
      '</div>';

    return isLive
      ? '<a class="xp-chapter" href="/explore/' + esc(pack.slug) + '/' + esc(ch.slug) + '/">' + inner + '</a>'
      : '<div class="xp-chapter xp-chapter--soon">' + inner + '</div>';
  }

  function renderChapters(el) {
    var slug = el.getAttribute('data-pack');
    loadData().then(function (data) {
      var pack = (data.packs || []).filter(function (p) { return p.slug === slug; })[0];
      if (!pack) { el.innerHTML = '<p class="xp-empty">Topic pack not found.</p>'; return; }
      el.innerHTML = (pack.chapters || []).map(function (c) { return chapterRow(pack, c); }).join('');
      el.classList.add('is-ready');
    }).catch(function () {
      el.innerHTML = '<p class="xp-empty">The chapter list could not be loaded. Please refresh the page. · 章節清單載入失敗，請重新整理。</p>';
    });
  }

  /* ---------- Self-check quiz ---------- */
  function initQuiz(root) {
    var cards = [].slice.call(root.querySelectorAll('.qz'));
    if (!cards.length) return;
    var scoreEl = root.querySelector('.qz__score');
    var answered = 0, correct = 0;

    function paint() {
      if (!scoreEl) return;
      if (answered < cards.length) { scoreEl.classList.remove('is-on'); return; }
      var msg = correct === cards.length
        ? "All correct — you've got this one."
        : (correct >= Math.ceil(cards.length * 0.6)
            ? 'Solid. Re-read the sections behind anything you missed.'
            : 'Worth another pass through the chapter before you move on.');
      scoreEl.querySelector('.qz__score-text').innerHTML =
        esc(correct) + ' / ' + cards.length + ' — ' + esc(msg) +
        '<span class="zh">這個分數不會上傳，也不會被記錄。答錯的地方回上面重讀就好。</span>';
      scoreEl.classList.add('is-on');
    }

    function reset() {
      answered = 0; correct = 0;
      cards.forEach(function (card) {
        card.classList.remove('is-done');
        [].slice.call(card.querySelectorAll('.opt')).forEach(function (b) {
          b.disabled = false;
          b.classList.remove('is-ok', 'is-no', 'is-dim');
        });
      });
      if (scoreEl) scoreEl.classList.remove('is-on');
      root.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    cards.forEach(function (card) {
      var opts = [].slice.call(card.querySelectorAll('.opt'));
      opts.forEach(function (btn) {
        btn.addEventListener('click', function () {
          if (card.classList.contains('is-done')) return;
          var ok = btn.hasAttribute('data-ok');
          card.classList.add('is-done');
          answered++;
          if (ok) correct++;
          opts.forEach(function (b) {
            b.disabled = true;
            if (b.hasAttribute('data-ok')) b.classList.add('is-ok');
            else if (b === btn) b.classList.add('is-no');
            else b.classList.add('is-dim');
          });
          paint();
        });
      });
    });

    var resetBtn = root.querySelector('.qz__reset');
    if (resetBtn) resetBtn.addEventListener('click', reset);
  }

  /* ---------- Pronunciation buttons ----------
     Clips live in Cloudflare R2 and are served through the worker at
     /learn/audio/<hash>.mp3 — the same pool the Mandarin and School Culture
     apps use. A phrase with no entry in the manifest simply gets no button. */
  var MANIFEST_URL = '/learn/audio-manifest.json';
  var AUDIO_BASE = '/learn/audio/';
  var _manifest = null;

  function loadManifest() {
    if (_manifest) return _manifest;
    _manifest = fetch(MANIFEST_URL)
      .then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; });
    return _manifest;
  }

  function initAudio() {
    var els = [].slice.call(document.querySelectorAll('[data-audio]'));
    if (!els.length) return;

    loadManifest().then(function (manifest) {
      var player = new Audio();
      var active = null;

      function clear() {
        if (active) active.classList.remove('is-playing');
        active = null;
      }
      player.addEventListener('ended', clear);
      player.addEventListener('error', clear);

      els.forEach(function (el) {
        var hash = manifest[el.getAttribute('data-audio')];
        if (!hash) return;

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'xp-speak';
        btn.textContent = '🔊';
        btn.setAttribute('aria-label', 'Play pronunciation · 播放發音');

        btn.addEventListener('click', function () {
          player.pause();
          clear();
          player.src = AUDIO_BASE + hash + '.mp3';
          active = btn;
          btn.classList.add('is-playing');
          var p = player.play();
          if (p && p.catch) p.catch(clear);
        });

        el.appendChild(btn);
      });
    });
  }

  /* ---------- Boot ---------- */
  function boot() {
    var wall = document.querySelector('[data-explore-wall]');
    if (wall) renderWall(wall);
    var chapters = document.querySelector('[data-explore-chapters]');
    if (chapters) renderChapters(chapters);
    [].slice.call(document.querySelectorAll('[data-quiz]')).forEach(initQuiz);
    initAudio();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
