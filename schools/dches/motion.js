/* Tai-He reveal-on-scroll — IntersectionObserver, staggered by sibling index.
   Respects prefers-reduced-motion. */
(function(){
  if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var sel='.rvl,.unit,.nc,.stat,.fet-spot,.pillar,.vc,.about__body p,.quote,.banner-figure,.contact';
  var els=[].slice.call(document.querySelectorAll(sel));
  if(!els.length)return;
  els.forEach(function(el){el.classList.add('rvl');});
  if(!('IntersectionObserver'in window)){els.forEach(function(el){el.classList.add('in');});return;}
  var io=new IntersectionObserver(function(en){en.forEach(function(e){
    if(!e.isIntersecting)return;
    var sibs=[].slice.call(e.target.parentNode.children).filter(function(n){return n.classList.contains('rvl');});
    e.target.style.transitionDelay=(Math.max(0,sibs.indexOf(e.target))*80)+'ms';
    e.target.classList.add('in');io.unobserve(e.target);
  });},{threshold:0.1,rootMargin:'0px 0px -6% 0px'});
  els.forEach(function(el){io.observe(el);});
})();
