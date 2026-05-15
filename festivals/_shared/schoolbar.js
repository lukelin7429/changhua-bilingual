/* ============================================================
   School-aware top bar for the Festival English Series
   ============================================================
   Reads ?from=<slug> from the URL (or sessionStorage on subsequent
   pages), looks up the school in SCHOOLS, and injects a slim
   colored bar at the very top of <body> with a "Back to your
   school" link.

   To add a school: add one entry to SCHOOLS below.  No other
   change is needed — every festival page already includes this
   script.
   ============================================================ */

(function () {
  const SCHOOLS = {
    huatan: {
      name: 'Huatan Elementary',
      nameZh: '花壇國小',
      color: '#B5462E',
      colorDeep: '#7d2e1a',
      url: 'https://lukelin7429.github.io/changhua-bilingual/schools/huatan/'
    },
    hualong: {
      name: 'Hualong Elementary',
      nameZh: '華龍國小',
      color: '#E69585',
      colorDeep: '#C66E5C',
      url: 'https://lukelin7429.github.io/changhua-bilingual/schools/hualong/'
    },
    wenchang: {
      name: 'Wenchang Elementary',
      nameZh: '文昌國小',
      color: '#d44a4a',
      colorDeep: '#8a2828',
      url: 'https://changhua-bilingual.org/schools/wenchang/'
    },
    zhongzheng: {
      name: 'Zhongzheng Elementary',
      nameZh: '中正國小',
      color: '#C28A40',
      colorDeep: '#7a5217',
      url: 'https://changhua-bilingual.org/schools/zhongzheng/'
    },
    minsheng: {
      name: 'Minsheng Elementary',
      nameZh: '民生國小',
      color: '#7B1E1E',
      colorDeep: '#4d1212',
      url: 'https://changhua-bilingual.org/schools/minsheng/'
    },
    dajuang: {
      name: 'Dajuang Elementary',
      nameZh: '大莊國小',
      color: '#d97818',
      colorDeep: '#a85a0c',
      url: 'https://changhua-bilingual.org/schools/dajuang/'
    },
    dacheng: {
      name: 'Dacheng Elementary',
      nameZh: '大城國小',
      color: '#4760c5',
      colorDeep: '#2c3a8c',
      url: 'https://changhua-bilingual.org/schools/dacheng/'
    }
    /* Add more schools here as they adopt the Festival English Series. */
  };

  /* 1. Resolve school slug.  URL param wins; otherwise reuse the
        slug stored from an earlier page in this browser tab. */
  const params = new URLSearchParams(location.search);
  const fromParam = params.get('from');
  if (fromParam) {
    try { sessionStorage.setItem('festival_from', fromParam); } catch (e) {}
  }
  let slug = fromParam;
  if (!slug) {
    try { slug = sessionStorage.getItem('festival_from'); } catch (e) {}
  }
  if (!slug || !SCHOOLS[slug]) return;  /* visitor not from a school site */

  const s = SCHOOLS[slug];

  /* 2. Propagate ?from= to every same-origin link inside the
        festival pages, so navigating between hub / handout / quiz
        keeps the context even without sessionStorage. */
  function propagateContext() {
    const anchors = document.querySelectorAll('a[href]');
    anchors.forEach(function (a) {
      const href = a.getAttribute('href');
      if (!href) return;
      /* Skip external, anchors, mailto, tel, javascript: */
      if (/^(https?:)?\/\//.test(href) && href.indexOf(location.host) === -1) return;
      if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return;
      /* Only touch links that stay inside the festivals tree */
      try {
        const u = new URL(href, location.href);
        if (!u.pathname.includes('/festivals/')) return;
        if (u.searchParams.has('from')) return;
        u.searchParams.set('from', slug);
        a.setAttribute('href', u.pathname + u.search + u.hash);
      } catch (e) {}
    });
  }

  /* 3. Inject style for the school bar. */
  const style = document.createElement('style');
  style.textContent =
    '.schoolbar{background:' + s.color + ';color:#fff;padding:10px 22px;' +
    "font-family:'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif;" +
    'font-size:15px;letter-spacing:.3px;display:flex;align-items:center;justify-content:center;' +
    'gap:10px;box-shadow:inset 0 -3px 0 ' + s.colorDeep + ';line-height:1.4;text-align:center;}' +
    '.schoolbar a{color:#fff;text-decoration:none;font-weight:700;border-bottom:1px solid rgba(255,255,255,.4);padding-bottom:1px;}' +
    '.schoolbar a:hover{border-bottom-color:#fff;}' +
    '.schoolbar__arrow{font-size:18px;line-height:1;}' +
    '.schoolbar__series{opacity:.85;font-size:13px;letter-spacing:1px;text-transform:uppercase;font-weight:600;}' +
    '.schoolbar__sep{opacity:.5;}' +
    '@media (min-width:720px){.schoolbar{font-size:17px;padding:12px 24px;gap:14px;}.schoolbar__series{font-size:14.5px;}}';
  document.head.appendChild(style);

  /* 4. Inject the bar at the very top of <body>. */
  function injectBar() {
    if (document.querySelector('.schoolbar')) return;
    const bar = document.createElement('div');
    bar.className = 'schoolbar';
    bar.innerHTML =
      '<a href="' + s.url + '"><span class="schoolbar__arrow">←</span> Back to ' + s.nameZh + ' ' + s.name + '</a>' +
      '<span class="schoolbar__sep">·</span>' +
      '<span class="schoolbar__series">on Festival English Series</span>';
    document.body.insertAdjacentElement('afterbegin', bar);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { injectBar(); propagateContext(); });
  } else {
    injectBar();
    propagateContext();
  }
})();
