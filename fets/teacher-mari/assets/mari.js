/* Teacher Mari's English Hub — interactions */
(function(){
  'use strict';

  /* ---- mobile nav ---- */
  var burger = document.querySelector('.burger');
  var menu = document.querySelector('.menu');
  if (burger && menu){
    burger.addEventListener('click', function(){ menu.classList.toggle('show'); });
    // submenu toggle on mobile
    menu.querySelectorAll('.has-sub>a').forEach(function(a){
      a.addEventListener('click', function(e){
        if (window.matchMedia('(max-width:720px)').matches){
          e.preventDefault();
          a.parentElement.classList.toggle('open');
        }
      });
    });
  }

  /* ---- reveal on scroll (IntersectionObserver + rAF fallback for preview) ---- */
  var items = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  function showInView(){
    var vh = window.innerHeight || document.documentElement.clientHeight;
    items.forEach(function(el){
      if (el.classList.contains('in')) return;
      var r = el.getBoundingClientRect();
      if (r.top < vh - 60 && r.bottom > 0) el.classList.add('in');
    });
  }
  if ('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
    }, {rootMargin:'0px 0px -8% 0px'});
    items.forEach(function(el){ io.observe(el); });
  }
  // always run a geometry pass too (covers previews where IO/rAF may be idle)
  window.addEventListener('scroll', showInView, {passive:true});
  window.addEventListener('resize', showInView);
  showInView();
  setTimeout(showInView, 350);
  // safety: never leave content hidden
  setTimeout(function(){ items.forEach(function(el){ el.classList.add('in'); }); }, 2600);

  /* ---- lightbox ---- */
  var triggers = Array.prototype.slice.call(document.querySelectorAll('[data-lb]'));
  if (triggers.length){
    var srcs = triggers.map(function(t){ return t.getAttribute('data-lb'); });
    var idx = 0;
    var lb = document.createElement('div');
    lb.className = 'lb';
    lb.innerHTML = '<button class="x" aria-label="Close">&times;</button>'+
      '<button class="nav-btn prev" aria-label="Previous">&#8249;</button>'+
      '<img alt="">'+
      '<button class="nav-btn next" aria-label="Next">&#8250;</button>';
    document.body.appendChild(lb);
    var lbImg = lb.querySelector('img');
    function open(i){ idx=(i+srcs.length)%srcs.length; lbImg.src=srcs[idx]; lb.classList.add('open'); }
    function close(){ lb.classList.remove('open'); lbImg.src=''; }
    triggers.forEach(function(t,i){ t.addEventListener('click', function(){ open(i); }); });
    lb.querySelector('.x').addEventListener('click', close);
    lb.querySelector('.prev').addEventListener('click', function(e){ e.stopPropagation(); open(idx-1); });
    lb.querySelector('.next').addEventListener('click', function(e){ e.stopPropagation(); open(idx+1); });
    lb.addEventListener('click', function(e){ if (e.target===lb) close(); });
    document.addEventListener('keydown', function(e){
      if (!lb.classList.contains('open')) return;
      if (e.key==='Escape') close();
      if (e.key==='ArrowLeft') open(idx-1);
      if (e.key==='ArrowRight') open(idx+1);
    });
  }
})();
