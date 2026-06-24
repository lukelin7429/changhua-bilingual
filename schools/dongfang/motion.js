/* =====================================================================
   Dongfang Elementary — motion engine  (motion.js)
   - scroll progress bar + back-to-top button
   - hero entrance + drifting ambient orbs (grass / sun / sky / flame)
   - ken-burns: motion.css ::before pseudo handles the image
   - scroll-reveal with varied directions & stagger
   - reveal uses getBoundingClientRect on scroll (reliable everywhere)
   - hard failsafe so content is NEVER left invisible
   - honors prefers-reduced-motion
   ===================================================================== */
(function(){
  var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ready(fn){
    if(document.readyState!=='loading'){ fn(); }
    else{ document.addEventListener('DOMContentLoaded', fn); }
  }

  ready(function(){
    if(REDUCED) return;

    /* ---------- scroll progress bar ---------- */
    var bar = document.createElement('div');
    bar.id = 'mo-progress';
    document.body.appendChild(bar);

    /* ---------- back-to-top button ---------- */
    var toTop = document.createElement('button');
    toTop.id = 'mo-top';
    toTop.setAttribute('aria-label', 'Back to top');
    toTop.innerHTML = '↑';
    toTop.addEventListener('click', function(){
      window.scrollTo({ top:0, behavior:'smooth' });
    });
    document.body.appendChild(toTop);

    /* ---------- HERO: ken-burns + entrance + ambient orbs ----------- */
    var hero = document.querySelector('.pbanner');
    if(hero){
      if(getComputedStyle(hero).position==='static') hero.style.position = 'relative';
      var bn = hero.querySelector(':scope > .bn') || hero;
      var kids = [].slice.call(bn.children);
      bn.classList.add('mo-hero');
      kids.forEach(function(c,i){ c.style.animationDelay = (0.18+i*0.14)+'s'; });

      /* ambient orbs — green, gold, sky, flame */
      var orbs = document.createElement('div');
      orbs.className = 'mo-orbs';
      [
        {s:320,t:'-8%', l:'-5%', c:'rgba(47,158,68,.65)',   dx:'44px',  dy:'34px',  d:18},
        {s:240,t:'28%', l:'80%', c:'rgba(232,152,12,.60)',  dx:'-48px', dy:'28px',  d:22},
        {s:180,t:'60%', l:'10%', c:'rgba(47,127,196,.55)',  dx:'34px',  dy:'-38px', d:15},
        {s:150,t:'6%',  l:'55%', c:'rgba(232,71,43,.45)',   dx:'-28px', dy:'32px',  d:20}
      ].forEach(function(o){
        var d = document.createElement('div');
        d.className = 'mo-orb';
        d.style.cssText = 'width:'+o.s+'px;height:'+o.s+'px;top:'+o.t+';left:'+o.l+
          ';background:radial-gradient(circle at 35% 35%,'+o.c+',transparent 70%);'+
          '--dx:'+o.dx+';--dy:'+o.dy+';animation-duration:'+o.d+'s;';
        orbs.appendChild(d);
      });
      hero.insertBefore(orbs, hero.firstChild);
    }

    /* ---------- SCROLL-REVEAL ---------- */
    var SEL = [
      '.pillar','.unit','.vc','.feat','.spotlight','.about-photo',
      '.contact','.teaser','.playlist-block','.soccer-clip',
      '.ncard','[class*="-card"]:not([class*="__"])','[class*="__card"]',
      '.about > div','.sec-head','.lintro','.fcard','.scard',
      'section > .wrap > p'
    ];

    var cands = [].slice.call(document.querySelectorAll(SEL.join(',')));

    function inExcluded(el){
      return (hero && hero.contains(el)) ||
             !!el.closest('.topbar,footer,.cb-credit,#mo-top') ||
             el.classList.contains('rvl') ||
             getComputedStyle(el).display === 'none';
    }
    cands = cands.filter(function(el){ return !inExcluded(el); });
    /* keep only leaf matches — don't double-hide container + child */
    cands = cands.filter(function(el){
      return !cands.some(function(other){ return other !== el && el.contains(other); });
    });

    var VARIANTS = ['mo-up','mo-pop','mo-zoom','mo-left','mo-up','mo-right','mo-blur','mo-up'];
    var CALM = {vc:1,turn:1,'sow-item':1,topic:1};
    cands.forEach(function(el,i){
      el.classList.add('mo');
      var calm = false;
      for(var k in CALM){ if(el.classList.contains(k)){ calm=true; break; } }
      el.classList.add(calm ? 'mo-up' : VARIANTS[i % VARIANTS.length]);
    });

    /* rescue legacy .rvl elements */
    var legacy = [].slice.call(document.querySelectorAll('.rvl')).filter(function(el){
      return !(el.closest('.topbar,footer,.cb-credit,#mo-top'));
    });

    function reveal(el){
      var cls = el.classList.contains('mo') ? 'mo-in' : 'in';
      var sibs = [].slice.call(el.parentNode.children).filter(function(n){
        return n.classList && (n.classList.contains('mo') || n.classList.contains('rvl'));
      });
      el.style.transitionDelay = (Math.max(0, sibs.indexOf(el)) * 80) + 'ms';
      el.classList.add(cls);
    }

    var watch = cands.concat(legacy);
    function scan(){
      var vh = window.innerHeight || document.documentElement.clientHeight;
      for(var i = watch.length-1; i >= 0; i--){
        var r = watch[i].getBoundingClientRect();
        if(r.top < vh*0.9 && r.bottom > 0){ reveal(watch[i]); watch.splice(i,1); }
      }
    }
    scan();
    setTimeout(scan, 300);
    setTimeout(scan, 1200);
    window.addEventListener('load', scan);

    /* ---------- scroll handler ---------- */
    var ticking = false;
    function onScroll(){
      if(ticking) return; ticking = true;
      requestAnimationFrame(function(){
        var h = document.documentElement;
        var sc = h.scrollTop || document.body.scrollTop || 0;
        var max = (h.scrollHeight - h.clientHeight) || 1;
        bar.style.width = (sc/max*100) + '%';
        if(sc > 500) toTop.classList.add('mo-show');
        else toTop.classList.remove('mo-show');
        if(watch.length) scan();
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive:true });
    window.addEventListener('resize', function(){ if(watch.length) scan(); }, { passive:true });
    onScroll();

    /* ---------- speak buttons pulse while playing ---------- */
    document.addEventListener('click', function(ev){
      var b = ev.target.closest && ev.target.closest('.say,.speak,.sow__say');
      if(!b) return;
      b.classList.add('mo-playing');
      setTimeout(function(){ b.classList.remove('mo-playing'); }, 2400);
    });
  });
})();
