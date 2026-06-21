/* Shared behavior for /resources/tutoring/ lesson kits */
function say(t, btn){
  if(!('speechSynthesis' in window)) return;
  try{
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(t);
    u.lang = 'en-US'; u.rate = 0.9; u.pitch = 1;
    if(btn){ btn.classList.add('is-speaking');
      u.onend = function(){ btn.classList.remove('is-speaking'); };
      u.onerror = function(){ btn.classList.remove('is-speaking'); }; }
    window.speechSynthesis.speak(u);
  }catch(e){}
}
(function(){
  document.querySelectorAll('[data-speak]').forEach(function(b){
    b.addEventListener('click', function(){ say(b.getAttribute('data-speak'), b); });
  });
  /* scroll-spy on the sticky section nav */
  var nav = document.querySelector('.t-nav');
  if(nav){
    var links = [].slice.call(nav.querySelectorAll('a'));
    var secs = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
    var onScroll = function(){
      var y = window.scrollY + 110, cur = 0;
      for(var i=0;i<secs.length;i++){ if(secs[i] && secs[i].offsetTop <= y) cur = i; }
      links.forEach(function(a,i){ a.classList.toggle('active', i===cur); });
    };
    window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  }
  /* back to top */
  var top = document.querySelector('.t-top');
  if(top){
    top.addEventListener('click', function(){ window.scrollTo({top:0,behavior:'smooth'}); });
    window.addEventListener('scroll', function(){ top.classList.toggle('show', window.scrollY>600); }, {passive:true});
  }
})();
