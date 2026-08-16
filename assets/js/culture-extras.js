/**
 * Campus Culture — the two read-only views the shared engine doesn't cover.
 *
 * The engine handles the practice decks. This adds:
 *   · the vocabulary browser (every term, with audio)
 *   · the rules reference (M3-M7, searchable, never drilled)
 * Both are plain lookup surfaces: no scoring, no scheduling, no state.
 */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var AUDIO = '/learn/audio/';
  var manifest = null;

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  var current = null;
  function play(zh, btn) {
    var h = manifest && manifest[zh];
    if (!h) return;
    if (current) current.pause();
    document.querySelectorAll('.lx-say.on').forEach(function (b) { b.classList.remove('on'); });
    current = new Audio(AUDIO + h + '.mp3');
    if (btn) {
      btn.classList.add('on');
      current.onended = current.onerror = function () { btn.classList.remove('on'); };
    }
    var p = current.play();
    if (p && p.catch) p.catch(function () { if (btn) btn.classList.remove('on'); });
  }

  function wireSpeak(root) {
    root.querySelectorAll('[data-zh]').forEach(function (b) {
      b.addEventListener('click', function () { play(b.getAttribute('data-zh'), b); });
    });
  }

  // ------------------------------------------------------------------ tabs

  var PANES = { practice: 'cuPractice', terms: 'cuTerms', rules: 'cuRules' };
  document.querySelectorAll('.cu-tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      document.querySelectorAll('.cu-tab').forEach(function (t) { t.classList.remove('is-on'); });
      tab.classList.add('is-on');
      Object.keys(PANES).forEach(function (k) {
        $(PANES[k]).classList.toggle('hidden', k !== tab.dataset.tab);
      });
    });
  });

  // -------------------------------------------------------------- vocabulary

  var terms = [];
  function paintTerms(filter) {
    var f = (filter || '').trim().toLowerCase();
    var hits = terms.filter(function (t) {
      return !f || (t.zh + ' ' + t.py + ' ' + t.en + ' ' + t.why).toLowerCase().indexOf(f) !== -1;
    });
    $('cuTermCount').textContent = f
      ? hits.length + ' of ' + terms.length + ' terms · ' + hits.length + ' / ' + terms.length + ' 個'
      : terms.length + ' terms · 共 ' + terms.length + ' 個';
    $('cuTermList').innerHTML = hits.length ? hits.map(function (t) {
      return '<div class="cu-term">' +
        '<span class="cu-term__zh">' + esc(t.zh) + '</span>' +
        '<span class="cu-term__py">' + esc(t.py) + '</span>' +
        '<button type="button" class="lx-say" data-zh="' + esc(t.zh) + '" aria-label="Play audio 播放發音">🔊</button>' +
        '<span class="cu-term__en">' + esc(t.en) + '</span>' +
        '<p class="cu-term__why">' + esc(t.why) + '</p>' +
      '</div>';
    }).join('') : '<p class="cu-empty">Nothing matches that. 找不到符合的。</p>';
    wireSpeak($('cuTermList'));
  }

  // ------------------------------------------------------------------ rules

  var rules = null;
  function paintRules(filter) {
    var f = (filter || '').trim().toLowerCase();
    var qs = rules.questions.filter(function (q) {
      return !f || (q.stem + ' ' + q.options.join(' ') + ' ' + q.why + ' ' + q.mt + ' ' + q.mz)
        .toLowerCase().indexOf(f) !== -1;
    });
    $('cuRuleCount').textContent = f
      ? qs.length + ' of ' + rules.questions.length + ' entries · ' + qs.length + ' / ' + rules.questions.length + ' 則'
      : rules.questions.length + ' entries in 5 modules · 共 ' + rules.questions.length + ' 則，5 個模組';

    if (!qs.length) {
      $('cuRuleList').innerHTML = '<p class="cu-empty">Nothing matches that. 找不到符合的。</p>';
      return;
    }
    var html = [], lastM = null;
    qs.forEach(function (q) {
      if (q.m !== lastM) {
        lastM = q.m;
        html.push('<h3 class="cu-mod">M' + q.m + ' · ' + esc(q.mt) + '</h3>' +
                  '<p class="cu-mod-zh">' + esc(q.mz) + '</p>');
      }
      html.push('<div class="cu-item">' +
        '<p class="cu-item__q">' + esc(q.stem) + '</p>' +
        '<p class="cu-item__a"><b>→</b><span>' + esc(q.options[q.answer]) + '</span></p>' +
        '<p class="cu-item__why">' + esc(q.why) + '</p>' +
      '</div>');
    });
    $('cuRuleList').innerHTML = html.join('');
  }

  // ------------------------------------------------------------------- boot

  Promise.all([
    fetch('/culture/data/terms.json').then(function (r) { return r.json(); }),
    fetch('/culture/data/reference.json').then(function (r) { return r.json(); }),
    fetch('/learn/audio-manifest.json').then(function (r) { return r.json(); })
      .catch(function () { return {}; }),
  ]).then(function (res) {
    terms = res[0].terms;
    rules = res[1];
    manifest = res[2];
    paintTerms('');
    paintRules('');
    $('cuTermSearch').addEventListener('input', function () { paintTerms(this.value); });
    $('cuRuleSearch').addEventListener('input', function () { paintRules(this.value); });
  }).catch(function () {
    $('cuTermList').innerHTML = '<p class="cu-empty">Could not load. 載入失敗。</p>';
    $('cuRuleList').innerHTML = '<p class="cu-empty">Could not load. 載入失敗。</p>';
  });
})();
