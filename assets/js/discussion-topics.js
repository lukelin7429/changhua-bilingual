/**
 * Discussion topics for the FET monthly meetings.
 * Renders topics.json, filtered by domain and by a bilingual search that
 * matches English, Chinese and the topic id.
 */
(function () {
  var $ = function (id) { return document.getElementById(id); };

  // The site nav is sticky and its height changes with the breakpoint, so the
  // filter bar has to be told where the bottom of it actually is.
  function trackNavHeight() {
    var nav = document.querySelector('.hub-nav');
    if (!nav) return;
    var set = function () {
      document.documentElement.style.setProperty(
        '--dc-navh', Math.round(nav.getBoundingClientRect().height) + 'px');
    };
    set();
    window.addEventListener('resize', set);
    if (window.ResizeObserver) new ResizeObserver(set).observe(nav);
  }
  trackNavHeight();
  var data = null;
  var active = 'all';

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function domains() {
    var out = [];
    data.areas.forEach(function (a) {
      a.domains.forEach(function (d) { out.push({ area: a, dom: d }); });
    });
    return out;
  }

  function paintChips() {
    var all = domains();
    var total = all.reduce(function (n, x) { return n + x.dom.topics.length; }, 0);
    var chips = ['<button type="button" class="dc-chip' + (active === 'all' ? ' is-on' : '') +
      '" data-key="all">All 全部 (' + total + ')</button>'];
    all.forEach(function (x) {
      chips.push('<button type="button" class="dc-chip' + (active === x.dom.key ? ' is-on' : '') +
        '" data-key="' + x.dom.key + '">' + x.dom.emoji + ' ' + esc(x.dom.en) +
        ' ' + esc(x.dom.zh) + ' (' + x.dom.topics.length + ')</button>');
    });
    $('dcChips').innerHTML = chips.join('');
    $('dcChips').querySelectorAll('.dc-chip').forEach(function (b) {
      b.addEventListener('click', function () {
        active = b.dataset.key;
        paintChips();
        paint($('dcSearch').value);
      });
    });
  }

  function paint(filter) {
    var f = (filter || '').trim().toLowerCase();
    var html = [], shown = 0, total = 0, lastArea = null;

    data.areas.forEach(function (area) {
      area.domains.forEach(function (dom) {
        total += dom.topics.length;
        if (active !== 'all' && active !== dom.key) return;
        var hits = dom.topics.filter(function (t) {
          return !f || (t.en + ' ' + t.zh + ' ' + t.id).toLowerCase().indexOf(f) !== -1;
        });
        if (!hits.length) return;
        shown += hits.length;

        if (area.key !== lastArea) {
          lastArea = area.key;
          html.push('<p class="dc-area">' + esc(area.en) + ' · ' + esc(area.zh) + '</p>');
        }
        html.push('<h2 class="dc-dom">' + dom.emoji + ' ' + esc(dom.en) + '</h2>' +
                  '<p class="dc-dom-zh">' + esc(dom.zh) + ' · ' + hits.length + ' 題</p>');
        html.push('<div class="dc-list">' + hits.map(function (t) {
          return '<div class="dc-topic">' +
            '<span class="dc-topic__id">' + esc(t.id) + '</span>' +
            '<span class="dc-topic__b">' +
              '<p class="dc-topic__en">' + esc(t.en) + '</p>' +
              '<p class="dc-topic__zh">' + esc(t.zh) + '</p>' +
            '</span></div>';
        }).join('') + '</div>');
      });
    });

    $('dcCount').textContent = f || active !== 'all'
      ? shown + ' of ' + total + ' topics · ' + shown + ' / ' + total + ' 題'
      : total + ' topics in ' + domains().length + ' areas · 共 ' + total + ' 題，' + domains().length + ' 個領域';
    $('dcList').innerHTML = html.length ? html.join('')
      : '<p class="dc-empty">Nothing matches that. 找不到符合的題目。</p>';
  }

  fetch('/fets/meetings/discussions/topics.json')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      data = d;
      var ey = $('dcYearEn'), zy = $('dcYearZh');
      if (ey) ey.textContent = d.yearEn;
      if (zy) zy.textContent = d.year;
      paintChips();
      paint('');
      $('dcSearch').addEventListener('input', function () { paint(this.value); });
    })
    .catch(function () {
      $('dcCount').textContent = '';
      $('dcList').innerHTML = '<p class="dc-empty">Could not load the topics. 題綱載入失敗。</p>';
    });
})();
