/* =====================================================================
   Beidou Junior High — shared motion engine  (motion.js)
   - scroll progress bar + back-to-top
   - hero entrance + drifting ambient orbs
   - scroll-reveal with varied directions & stagger
   - reveal uses getBoundingClientRect on scroll (reliable everywhere) +
     a hard failsafe so content is NEVER left invisible
   - also rescues the page's legacy .rvl reveals (their IO can fail to fire)
   - honors prefers-reduced-motion
   ===================================================================== */
(function(){
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

    /* ---------- HERO: entrance + ambient orbs ---------- */
    var hero=document.querySelector('.banner,.title,.page-banner,.th-fest-hero,.unit-hero');
    if(hero){
      if(getComputedStyle(hero).position==='static') hero.style.position='relative';

      var inner=hero.querySelector(':scope > .wrap, :scope > .banner__inner, :scope > .th-fest-hero__inner') || hero;
      var kids=[].slice.call(inner.children);          /* capture BEFORE adding orbs */
      inner.classList.add('mo-hero');
      kids.forEach(function(c,i){ c.style.animationDelay=(0.14+i*0.13)+'s'; });

      var orbs=document.createElement('div');
      orbs.className='mo-orbs';
      [
        {s:280,t:'-8%', l:'-5%', c:'rgba(200,135,10,.55)', dx:'36px',  dy:'30px',  d:17},
        {s:210,t:'34%', l:'80%', c:'rgba(30,110,104,.55)', dx:'-42px', dy:'24px',  d:21},
        {s:150,t:'66%', l:'16%', c:'rgba(174,198,222,.50)',dx:'28px',  dy:'-32px', d:14}
      ].forEach(function(o){
        var d=document.createElement('div');
        d.className='mo-orb';
        d.style.cssText='width:'+o.s+'px;height:'+o.s+'px;top:'+o.t+';left:'+o.l+
          ';background:radial-gradient(circle at 35% 35%,'+o.c+',transparent 70%);'+
          '--dx:'+o.dx+';--dy:'+o.dy+';animation-duration:'+o.d+'s;';
        orbs.appendChild(d);
      });
      hero.insertBefore(orbs,hero.firstChild);
    }

    /* ---------- SCROLL-REVEAL ---------- */
    var SEL=['.section-head','.about-text','.timeline__row','.pillar','.principal-card',
      '.life-card','.contact','.card','.fcard','.hub-card','.lcard','.unit','.vc','.course',
      '.trad','.scn','.ag','.vocab','.result','.playlist-block','.news-grid > a',
      '.gallery img','.unit__word','.sec__head','.sec__title','.intro','.cta','.feature','.info-card',
      /* generic block patterns so every page's bespoke design is covered.
         :not([class*="__"]) keeps us on BLOCK roots, not their BEM children. */
      '[class*="-card"]:not([class*="__"])','[class*="__card"]',
      '[class*="__list"]','[class*="__grid"]','[class*="__row"]',
      '[class*="quote"]:not([class*="__"])','.en-block','.zh-block',
      'section > .wrap > p'];

    var cands=[].slice.call(document.querySelectorAll(SEL.join(',')));

    function inExcluded(el){
      return (hero && hero.contains(el)) ||
             el.closest('.subnav,.topbar,footer,.cb-credit,#mo-top') ||
             el.classList.contains('rvl') ||         /* leave legacy reveal alone */
             getComputedStyle(el).display==='none';  /* JS-toggled (quiz result/cards) — don't manage */
    }
    cands=cands.filter(function(el){return !inExcluded(el);});
    /* keep only LEAF matches (don't also reveal a container around matched
       children) -> preserves per-card stagger, never double-hides a wrapper */
    cands=cands.filter(function(el){
      return !cands.some(function(other){ return other!==el && el.contains(other); });
    });

    var VARIANTS=['mo-up','mo-up','mo-zoom','mo-left','mo-up','mo-right','mo-blur','mo-up'];
    var CALM={timeline__row:1,trad:1,vocab:1,result:1};   /* dense lists -> gentle up only */
    cands.forEach(function(el,i){
      el.classList.add('mo');
      var calm=false;
      for(var k in CALM){ if(el.classList.contains(k)){calm=true;break;} }
      el.classList.add(calm?'mo-up':VARIANTS[i%VARIANTS.length]);
    });

    /* Also drive the page's LEGACY .rvl reveals: their IntersectionObserver
       can fail to fire in some environments, leaving content stuck invisible.
       We rescue them here with the same reliable getBoundingClientRect path. */
    var legacy=[].slice.call(document.querySelectorAll('.rvl')).filter(function(el){
      return !(el.closest('.subnav,.topbar,footer,.cb-credit,#mo-top'));
    });

    function reveal(el){
      var cls=el.classList.contains('mo')?'mo-in':'in';   /* mo => new variants, rvl => legacy */
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

    /* Re-scan as layout settles (fonts/images) and after window load. Anything
       still hidden is genuinely off-screen, so it is never *visibly* stuck and
       reveals the moment it scrolls into view (scan runs on every scroll). The
       text stays in the DOM throughout, so screen readers / SEO are unaffected. */
    setTimeout(scan,300);
    setTimeout(scan,1200);
    window.addEventListener('load',scan);

    /* ---------- scroll handler (progress + back-to-top + reveal) ---------- */
    var ticking=false;
    function onScroll(){
      if(ticking) return; ticking=true;
      requestAnimationFrame(function(){
        var h=document.documentElement;
        var sc=h.scrollTop||document.body.scrollTop||0;
        var max=(h.scrollHeight-h.clientHeight)||1;
        bar.style.width=(sc/max*100)+'%';
        if(sc>500) toTop.classList.add('mo-show'); else toTop.classList.remove('mo-show');
        if(watch.length) scan();
        ticking=false;
      });
    }
    window.addEventListener('scroll',onScroll,{passive:true});
    window.addEventListener('resize',function(){ if(watch.length) scan(); },{passive:true});
    onScroll();

    /* ---------- speak buttons pulse while playing ---------- */
    document.addEventListener('click',function(ev){
      var b=ev.target.closest && ev.target.closest('.speak,.say,.ln__speak');
      if(!b) return;
      b.classList.add('mo-playing');
      setTimeout(function(){ b.classList.remove('mo-playing'); },2400);
    });
  });
})();
