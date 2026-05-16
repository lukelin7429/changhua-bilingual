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
      // GoatCounter's counter endpoint: /counter/PATH.json (path-encoded)
      // The `~` prefix means "starts with" — counts all sub-paths under it
      var encoded = encodeURIComponent('~' + path);
      var url = 'https://changhua-bilingual.goatcounter.com/counter/' + encoded + '.json';
      fetch(url, { credentials: 'omit' })
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(data){
          if (data && typeof data.count_unique === 'number') {
            n.textContent = data.count_unique.toLocaleString();
          } else if (data && typeof data.count === 'number') {
            n.textContent = data.count.toLocaleString();
          }
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
