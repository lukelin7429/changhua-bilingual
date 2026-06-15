/* =====================================================================
   Changhua Bilingual Hub — site-wide motion engine  (motion.js)
   - scroll progress bar + back-to-top
   - hero entrance + drifting ambient light blooms
   - scroll-reveal with varied directions & stagger
   - reveal uses getBoundingClientRect on scroll (reliable everywhere) +
     hard failsafes so content is NEVER left invisible
   - honors prefers-reduced-motion

   Designed to drop onto ANY bespoke Hub page (festivals, disaster-english,
   1-on-1 topics, soccer program, partner pages, quizzes …) without
   touching its typography, colours or layout. Pages that already run
   hub.js get their reveal from there and should NOT load this too.
   ===================================================================== */
(function(){
  'use strict';
  var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ready(fn){
    if(document.readyState!=='loading'){fn();}
    else{document.addEventListener('DOMContentLoaded',fn);}
  }

  ready(function(){
    if(REDUCED) return;               /* leave the page calm & fully visible */

    /* ---------- scroll progress bar ---------- */
    var bar=document.createElement('div');
    bar.id='mo-progress';
    document.body.appendChild(bar);

    /* ---------- back-to-top button ---------- */
    var toTop=document.createElement('button');
    toTop.id='mo-top';
    toTop.setAttribute('aria-label','Back to top');
    toTop.innerHTML='↑';
    toTop.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
    document.body.appendChild(toTop);

    /* ---------- HERO: entrance + ambient light blooms ---------- */
    var hero=document.querySelector(
      '.strip,.head,.hero,.banner,.page-banner,.unit__hero,.th-fest-hero');
    if(hero){
      if(getComputedStyle(hero).position==='static') hero.style.position='relative';
      if(getComputedStyle(hero).overflow==='visible') hero.style.overflow='hidden';

      var inner=hero.querySelector(
        ':scope > .wrap, :scope > .banner__inner, :scope > .hero-inner, '+
        ':scope > .hero__top, :scope > .th-fest-hero__inner') || hero;
      var kids=[].slice.call(inner.children);          /* capture BEFORE adding orbs */
      inner.classList.add('mo-hero');
      kids.forEach(function(c,i){ c.style.animationDelay=(0.14+i*0.12)+'s'; });

      var orbs=document.createElement('div');
      orbs.className='mo-orbs';
      [
        {s:300,t:'-12%',l:'-6%', dx:'36px',  dy:'30px',  d:17},
        {s:220,t:'30%', l:'82%', dx:'-42px', dy:'24px',  d:21},
        {s:160,t:'62%', l:'14%', dx:'28px',  dy:'-30px', d:14}
      ].forEach(function(o){
        var d=document.createElement('div');
        d.className='mo-orb';
        d.style.cssText='width:'+o.s+'px;height:'+o.s+'px;top:'+o.t+';left:'+o.l+
          ';--dx:'+o.dx+';--dy:'+o.dy+';animation-duration:'+o.d+'s;';
        orbs.appendChild(d);
      });
      hero.insertBefore(orbs,hero.firstChild);
    }

    /* ---------- SCROLL-REVEAL ----------
       Targets BLOCK ROOTS used across the Hub's bespoke page families.
       Skill-built pages: section heads + content cards.
       Landing pages: topic / lesson / festival / week cards.
       Generic fallbacks catch any *-card / *-item / *-block root. */
    var SEL=[
      /* section heads (festival/disaster/soccer/1-on-1 lesson pages) */
      '.sec__title','.sec__title-zh',
      /* skill-page content blocks */
      '.ag','.vocab','.ln','.trad','.drill','.v','.step','.line','.who',
      '.cue','.pattern','.tip','.w2card','.origin','.idea','.note',
      /* landing-grid cards */
      '.fest','.theme','.lesson','.week','.unit',
      /* partner / one-off page blocks */
      '.role-card','.award-card','.story-block','.pillar','.principal-card',
      '.life-card','.feature','.info-card','.course','.lcard','.card',
      '.grid-section',
      /* generic block patterns so every bespoke design is covered.
         :not([class*="__"]) keeps us on BLOCK roots, not their BEM kids. */
      '[class*="-card"]:not([class*="__"])',
      '[class*="-item"]:not([class*="__"])',
      '[class*="-block"]:not([class*="__"])',
      '[class*="-tile"]:not([class*="__"])'
    ];

    var cands=[].slice.call(document.querySelectorAll(SEL.join(',')));

    function inExcluded(el){
      return (hero && hero.contains(el)) ||
             el.closest('.topbar,.cb-back-strip-fallback,footer,.cb-credit,#mo-top') ||
             el.classList.contains('rvl') ||         /* leave legacy reveal alone */
             getComputedStyle(el).display==='none';  /* JS-toggled (quiz result) — don't manage */
    }
    cands=cands.filter(function(el){return !inExcluded(el);});
    /* keep only LEAF matches -> preserves per-card stagger, never double-
       hides a wrapper around already-matched children */
    cands=cands.filter(function(el){
      return !cands.some(function(other){ return other!==el && el.contains(other); });
    });

    var VARIANTS=['mo-up','mo-up','mo-zoom','mo-left','mo-up','mo-right','mo-blur','mo-up'];
    /* dense / repetitive lists -> gentle up only (no zoom/blur jitter) */
    var CALM={vocab:1,trad:1,drill:1,ln:1,v:1,line:1,cue:1,pattern:1,ag:1};
    cands.forEach(function(el,i){
      el.classList.add('mo','mo-lift');
      var calm=false;
      for(var k in CALM){ if(el.classList.contains(k)){calm=true;break;} }
      el.classList.add(calm?'mo-up':VARIANTS[i%VARIANTS.length]);
    });

    /* Also rescue any LEGACY .rvl reveals whose IntersectionObserver may
       not fire here, using the same reliable getBoundingClientRect path. */
    var legacy=[].slice.call(document.querySelectorAll('.rvl')).filter(function(el){
      return !(el.closest('.topbar,footer,.cb-credit,#mo-top'));
    });

    function reveal(el){
      var cls=el.classList.contains('mo')?'mo-in':'in';   /* mo => new, rvl => legacy */
      var sibs=[].slice.call(el.parentNode.children).filter(function(n){
        return n.classList && (n.classList.contains('mo')||n.classList.contains('rvl'));
      });
      el.style.transitionDelay=(Math.max(0,sibs.indexOf(el))*70)+'ms';
      el.classList.add(cls);
    }

    var watch=cands.concat(legacy);
    function scan(){
      var vh=window.innerHeight||document.documentElement.clientHeight;
      for(var i=watch.length-1;i>=0;i--){
        var r=watch[i].getBoundingClientRect();
        if(r.top < vh*0.9 && r.bottom > 0){ reveal(watch[i]); watch.splice(i,1); }
      }
    }
    scan();                       /* reveal above-the-fold immediately (no flash) */
    setTimeout(scan,300);
    setTimeout(scan,1200);
    window.addEventListener('load',scan);

    /* ---------- scroll handler (progress + back-to-top + reveal) ----------
       Reveal scan runs DIRECTLY (not inside requestAnimationFrame) so it
       fires in every environment — some headless/preview engines never run
       rAF, which would otherwise leave below-the-fold content stuck hidden.
       A simple time throttle keeps it cheap. */
    var ticking=false;
    function tick(){
      ticking=false;
      var h=document.documentElement;
      var sc=h.scrollTop||document.body.scrollTop||0;
      var max=(h.scrollHeight-h.clientHeight)||1;
      bar.style.width=(sc/max*100)+'%';
      if(sc>500) toTop.classList.add('mo-show'); else toTop.classList.remove('mo-show');
      if(watch.length) scan();
    }
    function onScroll(){ if(!ticking){ ticking=true; setTimeout(tick,60); } }
    window.addEventListener('scroll',onScroll,{passive:true});
    window.addEventListener('resize',onScroll,{passive:true});
    tick();

    /* ---------- speak buttons pulse while playing ---------- */
    document.addEventListener('click',function(ev){
      var b=ev.target.closest && ev.target.closest('.speak,.ln__speak,.chip-say');
      if(!b) return;
      b.classList.add('mo-playing');
      setTimeout(function(){ b.classList.remove('mo-playing'); },2400);
    });
  });
})();
