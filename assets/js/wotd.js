/* Word of the Day — gallery
   Fetches /assets/data/wotd.json (≈300 KB gzipped), renders cards,
   wires up search + school filter + lazy YouTube embed + load-more. */

(function () {
  'use strict';

  var PAGE_SIZE = 60;
  var ALL = []; // all items
  var FILTERED = []; // current filter result
  var rendered = 0;

  var qInput = document.getElementById('wotd-q');
  var schoolSel = document.getElementById('wotd-school');
  var grid = document.getElementById('wotd-grid');
  var countEl = document.getElementById('wotd-count');
  var emptyEl = document.getElementById('wotd-empty');
  var moreWrap = document.getElementById('wotd-loadmore-wrap');
  var moreBtn = document.getElementById('wotd-loadmore');
  var activeTheme = '';
  var activeLetter = '';

  if (!grid) return;

  // Read initial filter from URL (e.g. ?school=...&theme=...&letter=...)
  function paramsFromUrl() {
    var p = new URLSearchParams(window.location.search);
    return {
      q: p.get('q') || '',
      school: p.get('school') || '',
      theme: p.get('theme') || '',
      letter: p.get('letter') || '',
    };
  }
  function paramsToUrl() {
    var p = new URLSearchParams();
    if (qInput && qInput.value) p.set('q', qInput.value);
    if (schoolSel && schoolSel.value) p.set('school', schoolSel.value);
    if (activeTheme) p.set('theme', activeTheme);
    if (activeLetter) p.set('letter', activeLetter);
    var qs = p.toString();
    var url = window.location.pathname + (qs ? '?' + qs : '');
    history.replaceState(null, '', url);
  }

  // Map theme slug → card color class
  var THEME_COLOR = {
    'tasks': 't-blue',
    'physical-activities': 't-green',
    'festivals': 't-orange',
    'food-agriculture': 't-green',
    'learning-subjects': 't-purple',
    'clubs-teams': 't-orange',
    'facilities-equipment': 't-blue',
    'cultural-artistic': 't-purple',
    'health-safety': 't-pink',
    'picture-description': 't-orange',
  };

  // Extract base keyword (no POS tag) for bold-highlighting in sentence
  function baseKeyword(kw) {
    return kw.replace(/\s*\([nvr]|\(adj\)|\(adv\)|\(n\.\)|\(v\.\)/gi, '').replace(/\s*\([^)]+\)\s*$/, '').trim();
  }

  // Highlight the keyword inside a sentence by wrapping with <b>
  function highlightSentence(s, keyword) {
    var safe = escapeHtml(s);
    if (!keyword) return safe;
    // Build a tolerant regex: word stem (strip plurals/-ing/-ed)
    var stem = keyword.replace(/(ies|es|ing|ed|s)$/i, '');
    if (stem.length < 3) stem = keyword;
    try {
      var re = new RegExp('(' + stem.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[a-z]*)', 'gi');
      return safe.replace(re, '<b>$1</b>');
    } catch (e) {
      return safe;
    }
  }

  // Card template
  function cardHTML(item, idx) {
    var thumb = 'https://i.ytimg.com/vi/' + item.v + '/hqdefault.jpg';
    var kw = escapeHtml(item.k);
    kw = kw.replace(/\s*\(([a-z.]{1,5})\)\s*/i, ' <span class="pos">($1)</span>');
    var theme = item.t || 'picture-description';
    var colorClass = THEME_COLOR[theme] || 't-blue';
    var base = baseKeyword(item.k);

    var num = String(idx + 1);
    while (num.length < 3) num = '0' + num;

    var zh = item.kz ? '<p class="wotd-zh">' + escapeHtml(item.kz) + '</p>' : '';

    var ex2 = '';
    if (item.s2) {
      ex2 = '<div class="wotd-ex alt">'
          +   '<div class="en">' + highlightSentence(item.s2, base) + '</div>'
          +   (item.s2z ? '<div class="zh">' + escapeHtml(item.s2z) + '</div>' : '')
          + '</div>';
    }

    var school = item.sch
      ? '<div class="wotd-school" title="' + escapeAttr(item.sch) + '">' + escapeHtml(item.sch) + '</div>'
      : '';

    return '<article class="wotd-card ' + colorClass + '">'
      +   '<div class="wotd-head">'
      +     '<p class="wotd-num">Word ' + num + '</p>'
      +     '<h3 class="wotd-keyword">' + kw + '</h3>'
      +     zh
      +   '</div>'
      +   '<div class="wotd-yt" data-v="' + item.v + '" tabindex="0" role="button" aria-label="Play video for ' + escapeAttr(item.k) + '">'
      +     '<img loading="lazy" src="' + thumb + '" alt="" />'
      +   '</div>'
      +   '<div class="wotd-body">'
      +     '<div class="wotd-ex">'
      +       '<div class="en">' + highlightSentence(item.s1, base) + '</div>'
      +       (item.s1z ? '<div class="zh">' + escapeHtml(item.s1z) + '</div>' : '')
      +     '</div>'
      +     ex2
      +     school
      +   '</div>'
      + '</article>';
  }

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function escapeAttr(s) { return escapeHtml(s); }

  // Lazy YouTube embed: click thumbnail → swap to iframe
  function bindLazyEmbed(root) {
    root.querySelectorAll('.wotd-yt:not(.bound)').forEach(function (el) {
      el.classList.add('bound');
      el.addEventListener('click', function () { embed(el); });
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); embed(el); }
      });
    });
  }
  function embed(el) {
    if (el.classList.contains('loaded')) return;
    var v = el.getAttribute('data-v');
    var iframe = document.createElement('iframe');
    iframe.src = 'https://www.youtube-nocookie.com/embed/' + v + '?autoplay=1&rel=0';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;
    iframe.title = 'YouTube video';
    el.innerHTML = '';
    el.appendChild(iframe);
    el.classList.add('loaded');
  }

  // Render next page
  function renderMore() {
    var end = Math.min(rendered + PAGE_SIZE, FILTERED.length);
    var html = '';
    for (var i = rendered; i < end; i++) html += cardHTML(FILTERED[i], i);
    var tmp = document.createElement('div');
    tmp.innerHTML = html;
    var frag = document.createDocumentFragment();
    while (tmp.firstChild) frag.appendChild(tmp.firstChild);
    grid.appendChild(frag);
    bindLazyEmbed(grid);
    rendered = end;
    moreWrap.style.display = rendered < FILTERED.length ? 'block' : 'none';
    moreBtn.textContent = 'Load ' + Math.min(PAGE_SIZE, FILTERED.length - rendered) + ' more →';
  }

  // Run filter and reset render
  function applyFilter() {
    var q = (qInput ? qInput.value : '').trim().toLowerCase();
    var sch = (schoolSel ? schoolSel.value : '').trim();
    var hasQ = q.length > 0;
    FILTERED = ALL.filter(function (item) {
      if (sch && item.sch !== sch) return false;
      if (activeTheme && item.t !== activeTheme) return false;
      if (activeLetter && item.l !== activeLetter) return false;
      if (!hasQ) return true;
      var hay = (item.k + ' ' + (item.kz || '') + ' ' + item.s1 + ' ' + item.s1z + ' ' + (item.s2 || '') + ' ' + (item.s2z || '') + ' ' + (item.sch || '')).toLowerCase();
      return hay.indexOf(q) !== -1;
    });
    rendered = 0;
    grid.innerHTML = '';
    countEl.textContent = FILTERED.length.toLocaleString() + ' videos';
    if (FILTERED.length === 0) {
      emptyEl.hidden = false;
      moreWrap.style.display = 'none';
    } else {
      emptyEl.hidden = true;
      renderMore();
    }
    paramsToUrl();
  }

  function setActive(group, value) {
    document.querySelectorAll(group).forEach(function (b) {
      var matchAttr = group.indexOf('theme') !== -1 ? 'data-theme' : 'data-letter';
      var v = b.getAttribute(matchAttr) || '';
      b.classList.toggle('is-active', v === value);
    });
  }

  // Debounce input
  var debounce = null;
  function onInput() {
    clearTimeout(debounce);
    debounce = setTimeout(applyFilter, 120);
  }

  // ===== Bind ALL listeners IMMEDIATELY (before JSON loads) =====
  // If user types/clicks before JSON arrives, queue a pending filter call.
  var pendingApply = false;
  function applyFilterSafe() {
    if (ALL.length === 0) { pendingApply = true; return; }
    applyFilter();
  }

  if (qInput) qInput.addEventListener('input', function () {
    clearTimeout(debounce);
    debounce = setTimeout(applyFilterSafe, 120);
  });
  if (schoolSel) schoolSel.addEventListener('change', applyFilterSafe);
  if (moreBtn) moreBtn.addEventListener('click', renderMore);

  // Theme and letter filters are mutually exclusive — clicking one clears the other,
  // so the count shown on the clicked chip always equals what the user is about to see.
  document.querySelectorAll('.wotd-theme-chip').forEach(function (btn) {
    btn.addEventListener('click', function () {
      activeTheme = btn.getAttribute('data-theme') || '';
      activeLetter = '';
      setActive('.wotd-theme-chip', activeTheme);
      setActive('.wotd-az-chip', activeLetter);
      applyFilterSafe();
    });
  });
  document.querySelectorAll('.wotd-az-chip').forEach(function (btn) {
    btn.addEventListener('click', function () {
      activeLetter = btn.getAttribute('data-letter') || '';
      activeTheme = '';
      setActive('.wotd-az-chip', activeLetter);
      setActive('.wotd-theme-chip', activeTheme);
      applyFilterSafe();
    });
  });

  // Restore filter state from URL immediately (visual chip selection)
  var initEarly = paramsFromUrl();
  if (qInput && initEarly.q) qInput.value = initEarly.q;
  if (schoolSel && initEarly.school) schoolSel.value = initEarly.school;
  activeTheme = initEarly.theme || '';
  activeLetter = initEarly.letter || '';
  setActive('.wotd-theme-chip', activeTheme);
  setActive('.wotd-az-chip', activeLetter);

  // Top-contributors quick-filter — bind immediately (works after data loads)
  document.querySelectorAll('.wotd-top-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var s = btn.getAttribute('data-school');
      if (qInput) qInput.value = '';
      if (schoolSel) schoolSel.value = s;
      applyFilterSafe();
      window.scrollTo({ top: grid.getBoundingClientRect().top + window.scrollY - 100, behavior: 'smooth' });
    });
  });

  // Show a subtle "loading" hint so users know the data is coming
  if (countEl) countEl.textContent = 'Loading…';

  // Boot — load data
  fetch('/assets/data/wotd.json')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      ALL = data.items || [];
      applyFilter();
      pendingApply = false;
    })
    .catch(function (e) {
      console.error(e);
      if (countEl) countEl.textContent = 'Error loading';
      grid.innerHTML = '<p style="padding:40px;text-align:center;color:#888">Could not load the video library. Please refresh.</p>';
    });
})();
