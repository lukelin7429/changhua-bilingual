// ============================================================
// Changhua Bilingual Hub — Analytics & Visit Counter
// One central file for the whole site.  Edit here, not in 183 HTMLs.
// ============================================================

(function(){
  // --- 1. Google Analytics 4 (full backend — used by Luke only) ---
  var GA_ID = 'G-8J5V0KNF8F';
  var gaScript = document.createElement('script');
  gaScript.async = true;
  gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  document.head.appendChild(gaScript);
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', GA_ID, { anonymize_ip: true });

  // --- 2. GoatCounter (public visit counter — embedded on the page) ---
  // Privacy-first, no cookies, no consent banner required.
  window.goatcounter = window.goatcounter || {};
  var gc = document.createElement('script');
  gc.async = true;
  gc.src = '//gc.zgo.at/count.js';
  gc.setAttribute('data-goatcounter', 'https://changhua-bilingual.goatcounter.com/count');
  document.head.appendChild(gc);
})();

// --- 3. Visit counter renderer ---
// Any element with class `cb-counter-num` and a `data-cb-path` attribute
// will be populated with that path's visit count from GoatCounter.
// If no data-cb-path is set, defaults to current page path.
//
// Usage in HTML:
//   <span class="cb-counter-num" data-cb-path="/schools/dajuang/">----</span>
(function(){
  function loadCounters(){
    var nodes = document.querySelectorAll('.cb-counter-num');
    if (!nodes.length) return;
    nodes.forEach(function(n){
      var path = n.getAttribute('data-cb-path') || window.location.pathname;
      // GoatCounter's counter endpoint: /counter/PATH.json (path-encoded).
      // It returns ONLY the exact-path count (no wildcards), so this counts
      // landings on the school home page (a fair proxy for "visited the site").
      // Values are returned as strings — `Number()` handles both.
      var encoded = encodeURIComponent(path);
      var url = 'https://changhua-bilingual.goatcounter.com/counter/' + encoded + '.json';
      fetch(url, { credentials: 'omit' })
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(data){
          if (!data) return;
          var num = Number(data.count_unique || data.count || 0);
          if (!isNaN(num)) n.textContent = num.toLocaleString();
        })
        .catch(function(){ /* silent fail — keep the "----" placeholder */ });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadCounters);
  } else {
    loadCounters();
  }
})();

// --- 4. Mobile sub-nav hamburger ---
// Collapses .subnav links behind a ☰ button on phones (≤ 720px).
// Auto-detected; zero per-page HTML changes needed.
// Desktop unchanged.
(function(){
  // Inject CSS once
  var css = '' +
    '@media (max-width:720px){' +
      '.subnav{padding:0!important;}' +
      '.subnav-mobile-bar{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;}' +
      '.subnav-mobile-here{font-family:"Cormorant Garamond","PingFang TC",serif;font-weight:700;font-size:18px;color:#1c4d7e;letter-spacing:.4px;}' +
      '.subnav-mobile-toggle{display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;border:1.5px solid #c9d4e0;border-radius:10px;background:#fff;cursor:pointer;padding:0;color:#1c4d7e;transition:background .15s;}' +
      '.subnav-mobile-toggle:hover,.subnav-mobile-toggle:active{background:#e3eef8;}' +
      '.subnav-mobile-toggle svg{width:22px;height:22px;}' +
      '.subnav .subnav__inner,.subnav .wrap .subnav__inner{display:none!important;}' +
      '.subnav.is-open .subnav__inner{display:flex!important;flex-direction:column!important;align-items:stretch!important;padding:6px 18px 18px!important;gap:2px!important;border-top:1px solid #dde6ee;}' +
      '.subnav.is-open .subnav__inner a{text-align:center!important;padding:14px!important;border-radius:8px!important;}' +
      '.subnav .subnav__sep{display:none!important;}' +
    '}' +
    '@media (min-width:721px){.subnav-mobile-bar{display:none;}}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  function setupSubnav(){
    var subnavs = document.querySelectorAll('.subnav');
    subnavs.forEach(function(subnav){
      if (subnav.querySelector('.subnav-mobile-bar')) return; // idempotent

      // Figure out "where am I" — text for the mobile brand area
      var active = subnav.querySelector('a.is-active, a[aria-current]');
      var hereText = active ? active.textContent.trim() : 'Menu';

      // Build the mobile bar
      var bar = document.createElement('div');
      bar.className = 'subnav-mobile-bar';
      bar.innerHTML =
        '<span class="subnav-mobile-here">' + hereText + '</span>' +
        '<button class="subnav-mobile-toggle" aria-label="開啟選單 Toggle menu" aria-expanded="false">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
            '<line x1="3" y1="6" x2="21" y2="6"/>' +
            '<line x1="3" y1="12" x2="21" y2="12"/>' +
            '<line x1="3" y1="18" x2="21" y2="18"/>' +
          '</svg>' +
        '</button>';
      subnav.insertBefore(bar, subnav.firstChild);

      // Wire click
      var btn = bar.querySelector('.subnav-mobile-toggle');
      btn.addEventListener('click', function(){
        var open = subnav.classList.toggle('is-open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupSubnav);
  } else {
    setupSubnav();
  }
})();
