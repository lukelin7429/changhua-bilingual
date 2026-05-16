/* Changhua Bilingual Hub — shared scripts
   Handles: mobile nav toggle, interactive township map, schools-page search.
   Pages opt in by including this script and adding the required markup. */

(function () {
  'use strict';

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

      gj.features.forEach(function (f) {
        var name = f.properties.name;
        var info = window.HUB_TOWNSHIP_INDEX[name]; // by zh name
        var path = document.createElementNS(svgNS, 'path');
        path.setAttribute('d', polysToPath(f.geometry.coordinates, f.geometry.type));
        path.setAttribute('class', 'township' + (info && info.school_count ? ' has-schools' : ''));
        path.setAttribute('data-name', name);
        if (info) {
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
        path.addEventListener('mousemove', function (e) {
          var rect = container.getBoundingClientRect();
          tip.textContent = info
            ? info.en + ' · ' + (info.school_count || 0) + ' schools'
            : name;
          tip.style.left = (e.clientX - rect.left) + 'px';
          tip.style.top = (e.clientY - rect.top) + 'px';
          tip.classList.add('visible');
        });
        path.addEventListener('mouseleave', function () { tip.classList.remove('visible'); });
        svg.appendChild(path);
      });

      container.innerHTML = '';
      container.appendChild(svg);
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

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { renderMap(); bindSearch(); });
  } else {
    renderMap(); bindSearch();
  }
})();
