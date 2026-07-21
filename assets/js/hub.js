/* Changhua Bilingual Hub — shared scripts
   Handles: mobile nav toggle, interactive township map, schools-page search.
   Pages opt in by including this script and adding the required markup. */

(function () {
  'use strict';

  // Reveal-all hook, assigned by initReveal(); called by search filters so a
  // matched-but-not-yet-revealed card is never left invisible.
  var revealRemaining = function () {};

  // ----- Scroll reveal (fade / rise with staggered delay) -----
  // getBoundingClientRect + scroll based (not IntersectionObserver/rAF) so it
  // works in every environment and never leaves content stuck hidden.
  function initReveal() {
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var sel = [
      'main .hub-h1', 'main .hub-h2', 'main .resources-h2',
      'main .hub-card', 'main .about-card', 'main .about-stat', 'main .sdg',
      'main .ce-card', 'main .theme', 'main .how__step', 'main .lesson',
      'main .dom-card', 'main .dom-role', 'main .dom-pillar',
      'main .dom-section-lede', 'main .dom-section-lede-zh',
      'main .bllc-card', 'main .bllc-stat', 'main .bllc-rule', 'main .bc-activity',
      'main .eh-hero-text', 'main .eh-portrait', 'main .eh-changhua', 'main .eh-role',
      'main .eh-vocab', 'main .eh-photo', 'main .eh-chips',
      'main .eh-section-lede', 'main .eh-section-lede-zh',
      'main .lcoy-intro', 'main .lcoy-stat', 'main .lcoy-stage', 'main .lcoy-benefit',
      'main .lcoy-model-step', 'main .lcoy-cert', 'main .lcoy-contact', 'main .lcoy-chips',
      'main .lcoy-section-lede', 'main .lcoy-section-lede-zh',
      'main .fet-card', 'main .qz'
    ].join(',');
    var els = Array.prototype.slice.call(document.querySelectorAll(sel));
    if (!els.length) return;
    els.forEach(function (el) { el.classList.add('rvl'); });

    function reveal(el) {
      var sibs = Array.prototype.slice.call(el.parentNode.children).filter(function (n) {
        return n.classList.contains('rvl');
      });
      el.style.transitionDelay = (Math.max(0, sibs.indexOf(el)) * 80) + 'ms';
      el.classList.add('in');
    }
    var ticking = false;
    function check() {
      ticking = false;
      var vh = window.innerHeight || document.documentElement.clientHeight;
      for (var i = els.length - 1; i >= 0; i--) {
        if (els[i].getBoundingClientRect().top < vh * 0.92) { reveal(els[i]); els.splice(i, 1); }
      }
    }
    function onScroll() { if (!ticking) { ticking = true; setTimeout(check, 60); } }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    check();                                 // reveal anything already in view
    window.addEventListener('load', check);  // re-check after images/fonts settle
    setTimeout(check, 250);                   // safety net
    revealRemaining = function () { els.slice().forEach(reveal); els.length = 0; };
  }

  // ----- Mobile nav toggle -----
  document.querySelectorAll('.hub-nav').forEach(function (nav) {
    var toggle = nav.querySelector('.hub-nav-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', function () { nav.classList.toggle('open'); });
  });

  // ----- Township map renderer -----
  // Looks for #hub-map container; expects window.HUB_TOWNSHIPS = [{slug, zh, en, school_count, town_id}, ...]
  function renderMap() {
    var container = document.getElementById('hub-map');
    if (!container || !window.HUB_TOWNSHIP_INDEX) return;

    var geoUrl = container.getAttribute('data-geo') || '/assets/map/changhua-townships.geojson';
    fetch(geoUrl).then(function (r) { return r.json(); }).then(function (gj) {
      var bounds = computeBounds(gj);
      var W = 600, H = 500, pad = 12;
      var sx = (W - 2 * pad) / (bounds.maxX - bounds.minX);
      var sy = (H - 2 * pad) / (bounds.maxY - bounds.minY);
      var s = Math.min(sx, sy);
      var ox = (W - s * (bounds.maxX - bounds.minX)) / 2;
      var oy = (H - s * (bounds.maxY - bounds.minY)) / 2;

      function proj(lng, lat) {
        var x = ox + (lng - bounds.minX) * s;
        var y = oy + (bounds.maxY - lat) * s;
        return x + ',' + y;
      }
      function ringToPath(ring) {
        return ring.map(function (p, i) {
          return (i === 0 ? 'M' : 'L') + proj(p[0], p[1]);
        }).join(' ') + ' Z';
      }
      function polysToPath(coords, type) {
        if (type === 'Polygon') {
          return coords.map(ringToPath).join(' ');
        } else { // MultiPolygon
          return coords.map(function (poly) { return poly.map(ringToPath).join(' '); }).join(' ');
        }
      }

      var svgNS = 'http://www.w3.org/2000/svg';
      var svg = document.createElementNS(svgNS, 'svg');
      svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', 'Map of Changhua County by township');

      // Tooltip
      var tip = document.createElement('div');
      tip.className = 'hub-map-tooltip';
      container.parentElement.style.position = 'relative';
      container.parentElement.appendChild(tip);

      // colour the map by geographic region of Changhua (4 hues)
      var REGION = {
        'xianxi':'coast','shenkang':'coast','lukang':'coast','fuxing':'coast',
        'fangyuan':'coast','dacheng':'coast','erlin':'coast','puyan':'coast',
        'changhua-city':'north','hemei':'north','huatan':'north','fenyuan':'north','xiushui':'north',
        'yuanlin-city':'central','dacun':'central','puxin':'central','yongjing':'central','xihu':'central','shetou':'central',
        'tianzhong':'south','beidou':'south','tianwei':'south','pitou':'south','xizhou':'south','zhutang':'south','ershui':'south'
      };
      gj.features.forEach(function (f) {
        var name = f.properties.name;
        var info = window.HUB_TOWNSHIP_INDEX[name];
        var path = document.createElementNS(svgNS, 'path');
        path.setAttribute('d', polysToPath(f.geometry.coordinates, f.geometry.type));
        var rg = info && REGION[info.slug] ? ' rg-' + REGION[info.slug] : '';
        path.setAttribute('class', 'township' + (info && info.school_count ? ' has-schools' : '') + rg);
        path.setAttribute('data-name', name);
        if (info && info.school_count) {
          path.setAttribute('tabindex', '0');
          path.setAttribute('role', 'link');
          path.setAttribute('aria-label', info.en + ' — ' + info.school_count + ' schools');
          path.addEventListener('click', function () {
            window.location.href = '/schools/#' + info.slug;
          });
          path.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); path.dispatchEvent(new MouseEvent('click')); }
          });
        }
        function showTip(e) {
          var rect = container.getBoundingClientRect();
          var zh = name;
          var en = info ? info.en : '';
          var count = info ? info.school_count : 0;
          tip.innerHTML = '<strong>' + zh + '</strong>'
            + (en ? '<span class="en">' + en + '</span>' : '')
            + (count > 0 ? ' · <span class="count">' + count + ' schools</span>' : (info ? ' · <span class="en">no partner schools yet</span>' : ''));
          tip.style.left = (e.clientX - rect.left) + 'px';
          tip.style.top = (e.clientY - rect.top - 14) + 'px';
          tip.classList.add('visible');
        }
        path.addEventListener('mouseenter', showTip);
        path.addEventListener('mousemove', showTip);
        path.addEventListener('mouseleave', function () { tip.classList.remove('visible'); });
        svg.appendChild(path);
      });

      container.innerHTML = '';
      container.appendChild(svg);

      // Legend
      var legend = document.createElement('div');
      legend.className = 'hub-map-legend';
      legend.innerHTML = '<span class="hub-map-legend-swatches">'
        + '<span class="rg-coast"></span><span class="lbl">Coast 海線</span>'
        + '<span class="rg-north"></span><span class="lbl">North 北彰</span>'
        + '<span class="rg-central"></span><span class="lbl">Central 中彰</span>'
        + '<span class="rg-south"></span><span class="lbl">South 南彰</span>'
        + '</span>';
      container.parentElement.appendChild(legend);
    }).catch(function (e) {
      container.innerHTML = '<div style="padding:40px;color:#888;text-align:center">Map could not load.</div>';
      console.error('Map load error', e);
    });
  }
  function computeBounds(gj) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    gj.features.forEach(function (f) {
      var c = f.geometry.coordinates;
      function eachRing(ring) {
        ring.forEach(function (p) {
          if (p[0] < minX) minX = p[0]; if (p[0] > maxX) maxX = p[0];
          if (p[1] < minY) minY = p[1]; if (p[1] > maxY) maxY = p[1];
        });
      }
      if (f.geometry.type === 'Polygon') c.forEach(eachRing);
      else c.forEach(function (poly) { poly.forEach(eachRing); });
    });
    return { minX: minX, minY: minY, maxX: maxX, maxY: maxY };
  }

  // ----- Schools page client-side search -----
  function bindSearch() {
    var input = document.getElementById('hub-search-input');
    if (!input) return;
    var cards = Array.prototype.slice.call(document.querySelectorAll('.hub-school-card'));
    var blocks = Array.prototype.slice.call(document.querySelectorAll('.hub-township-block'));

    function filter() {
      var q = input.value.trim().toLowerCase();
      cards.forEach(function (card) {
        var hay = (card.getAttribute('data-search') || '').toLowerCase();
        card.style.display = !q || hay.indexOf(q) !== -1 ? '' : 'none';
      });
      blocks.forEach(function (b) {
        var visible = b.querySelectorAll('.hub-school-card:not([style*="display: none"])').length;
        b.style.display = visible ? '' : 'none';
      });
    }
    input.addEventListener('input', filter);
  }

  // ----- FETs page client-side search -----
  function bindFetsSearch() {
    var input = document.getElementById('fets-search-input');
    if (!input) return;
    var cards = Array.prototype.slice.call(document.querySelectorAll('.fet-card'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('.fet-group'));
    var emptyEl = document.getElementById('fets-search-empty');

    function filter() {
      var q = input.value.trim().toLowerCase();
      var anyVisible = false;
      cards.forEach(function (card) {
        var hay = (card.getAttribute('data-search') || '').toLowerCase();
        var match = !q || hay.indexOf(q) !== -1;
        card.style.display = match ? '' : 'none';
        if (match) anyVisible = true;
      });
      groups.forEach(function (g) {
        var v = g.querySelectorAll('.fet-card:not([style*="display: none"])').length;
        g.style.display = v ? '' : 'none';
      });
      if (emptyEl) emptyEl.hidden = !q || anyVisible;
    }
    input.addEventListener('input', filter);
  }

  // ----- Resources page client-side search -----
  function bindResourcesSearch() {
    var input = document.getElementById('resources-search-input');
    if (!input) return;
    var cards = Array.prototype.slice.call(document.querySelectorAll('main .hub-card'));
    var allSections = Array.prototype.slice.call(document.querySelectorAll('main .hub-section'));
    var cardSections = allSections.filter(function (s) {
      return s.querySelectorAll('.hub-card').length > 0;
    });
    var emptyEl = document.getElementById('resources-search-empty');

    function filter() {
      revealRemaining(); // ensure no reveal-hidden card stays invisible after filtering
      var q = input.value.trim().toLowerCase();
      var anyVisible = false;
      cards.forEach(function (card) {
        var ds = card.getAttribute('data-search');
        var hay = ((ds !== null ? ds : card.textContent) || '').toLowerCase();
        var match = !q || hay.indexOf(q) !== -1;
        card.style.display = match ? '' : 'none';
        if (match) anyVisible = true;
      });
      cardSections.forEach(function (s) {
        var v = s.querySelectorAll('.hub-card:not([style*="display: none"])').length;
        s.style.display = v ? '' : 'none';
      });
      if (emptyEl) emptyEl.hidden = !q || anyVisible;
    }
    input.addEventListener('input', filter);
  }

  function initAll() {
    renderMap();
    bindSearch();
    bindFetsSearch();
    bindResourcesSearch();
    initReveal();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
