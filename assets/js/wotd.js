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

  if (!grid) return;

  // Read initial filter from URL (e.g. ?school=...)
  function paramsFromUrl() {
    var p = new URLSearchParams(window.location.search);
    return { q: p.get('q') || '', school: p.get('school') || '' };
  }
  function paramsToUrl() {
    var p = new URLSearchParams();
    if (qInput && qInput.value) p.set('q', qInput.value);
    if (schoolSel && schoolSel.value) p.set('school', schoolSel.value);
    var qs = p.toString();
    var url = window.location.pathname + (qs ? '?' + qs : '');
    history.replaceState(null, '', url);
  }

  // Card template
  function cardHTML(item) {
    var thumb = 'https://i.ytimg.com/vi/' + item.v + '/hqdefault.jpg';
    var kw = escapeHtml(item.k);
    // Highlight POS tag like "(v)" if present
    kw = kw.replace(/\s*\(([nvr]|adj|adv|n\.|v\.)\)\s*/i, ' <span class="pos">($1)</span>');
    var zh = item.kz ? '<p class="wotd-zh">' + escapeHtml(item.kz) + '</p>' : '';
    return ''
      + '<article class="wotd-card">'
      +   '<div class="wotd-yt" data-v="' + item.v + '" tabindex="0" role="button" aria-label="Play video for ' + escapeAttr(item.k) + '">'
      +     '<img loading="lazy" src="' + thumb + '" alt="" />'
      +   '</div>'
      +   '<div class="wotd-body">'
      +     '<h3 class="wotd-keyword">' + kw + '</h3>'
      +     zh
      +     '<hr class="wotd-divider">'
      +     '<p class="wotd-sentence">' + escapeHtml(item.s1) + '</p>'
      +     '<p class="wotd-sentence-zh">' + escapeHtml(item.s1z) + '</p>'
      +     (item.s2 ? '<p class="wotd-sentence">' + escapeHtml(item.s2) + '</p>' : '')
      +     (item.s2z ? '<p class="wotd-sentence-zh">' + escapeHtml(item.s2z) + '</p>' : '')
      +     (item.sch ? '<div class="wotd-school" title="' + escapeAttr(item.sch) + '">' + escapeHtml(item.sch) + '</div>' : '')
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
    for (var i = rendered; i < end; i++) html += cardHTML(FILTERED[i]);
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

  // Debounce input
  var debounce = null;
  function onInput() {
    clearTimeout(debounce);
    debounce = setTimeout(applyFilter, 120);
  }

  // Boot
  fetch('/assets/data/wotd.json')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      ALL = data.items || [];
      var init = paramsFromUrl();
      if (qInput && init.q) qInput.value = init.q;
      if (schoolSel && init.school) schoolSel.value = init.school;
      applyFilter();

      if (qInput) qInput.addEventListener('input', onInput);
      if (schoolSel) schoolSel.addEventListener('change', applyFilter);
      if (moreBtn) moreBtn.addEventListener('click', renderMore);

      // Top-contributors quick-filter
      document.querySelectorAll('.wotd-top-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var s = btn.getAttribute('data-school');
          if (qInput) qInput.value = '';
          if (schoolSel) schoolSel.value = s;
          applyFilter();
          window.scrollTo({ top: grid.getBoundingClientRect().top + window.scrollY - 100, behavior: 'smooth' });
        });
      });
    })
    .catch(function (e) {
      console.error(e);
      grid.innerHTML = '<p style="padding:40px;text-align:center;color:#888">Could not load the video library. Please refresh.</p>';
    });
})();
