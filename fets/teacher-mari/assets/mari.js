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

  /* ---- speak helper (Web Speech) ---- */
  function say(text){
    try{
      if (!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-US'; u.rate = 0.92;
      window.speechSynthesis.speak(u);
    }catch(e){}
  }

  /* ---- Story Quiz game ---- */
  var quiz = document.getElementById('quiz');
  if (quiz && window.MARI_QUIZ){
    var QS = window.MARI_QUIZ, i = 0, score = 0, answered = false;
    var KEYS = ['A','B','C','D'];
    var bar = quiz.querySelector('.quiz-bar i');
    var body = quiz.querySelector('.quiz-body');
    var confettiBox = quiz.querySelector('.confetti');

    function render(){
      answered = false;
      var q = QS[i];
      bar.style.width = (i/QS.length*100) + '%';
      var opts = q.options.map(function(o, n){
        return '<button class="opt" data-i="'+n+'"><span class="key">'+KEYS[n]+'</span><span>'+o+'</span></button>';
      }).join('');
      body.innerHTML =
        '<div class="quiz-meta"><span>Question '+(i+1)+' of '+QS.length+'</span><span class="score">Score <b>'+score+'</b>/'+QS.length+'</span></div>'+
        '<div class="q-photo"><img src="'+q.photo+'" alt=""></div>'+
        '<div class="q-text"><button class="say-btn" title="Listen">🔊</button><span>'+q.q+'</span></div>'+
        '<p class="q-zh">'+q.zh+'</p>'+
        '<div class="opts">'+opts+'</div>'+
        '<div class="explain"></div>'+
        '<div class="quiz-next"><button class="btn-go">Next →</button></div>';
      var qtext = q.q;
      body.querySelector('.say-btn').addEventListener('click', function(){
        say(qtext + '. ' + q.options.map(function(o,n){return KEYS[n]+': '+o;}).join('. '));
      });
      say(qtext);
      var buttons = body.querySelectorAll('.opt');
      buttons.forEach(function(btn){
        btn.addEventListener('click', function(){ pick(btn, q, buttons); });
      });
      var next = body.querySelector('.btn-go');
      next.textContent = (i === QS.length-1) ? 'See my score! 🎉' : 'Next →';
      next.addEventListener('click', function(){ i++; (i<QS.length)?render():finish(); });
    }

    function pick(btn, q, buttons){
      if (answered) return;
      answered = true;
      var chosen = +btn.getAttribute('data-i');
      buttons.forEach(function(b){ b.disabled = true; });
      if (chosen === q.answer){
        btn.classList.add('correct'); score++; burst();
        say('Correct! ' + q.explainEn);
      } else {
        btn.classList.add('wrong','shake');
        buttons[q.answer].classList.add('correct');
        say('Good try. ' + q.explainEn);
      }
      var ex = body.querySelector('.explain');
      ex.innerHTML = '<b>'+(chosen===q.answer?'✅ Correct!':'💡 The answer is '+KEYS[q.answer]+'.')+'</b> '+q.explainEn+'<span class="zh">'+q.explainZh+'</span>';
      ex.classList.add('show');
      body.querySelector('.score b').textContent = score;
      body.querySelector('.btn-go').classList.add('show');
    }

    function finish(){
      bar.style.width = '100%';
      var stars = score>=5?'⭐⭐⭐⭐⭐':score>=4?'⭐⭐⭐⭐':score>=3?'⭐⭐⭐':score>=2?'⭐⭐':'⭐';
      var face = score>=4?'🌟':score>=3?'😄':'📚';
      var msg = score>=5?'Perfect! You are a Reading Star!':score>=3?'Great job! Keep reading!':'Nice try! Read the story again and play once more!';
      var zh = score>=5?'太棒了！你是閱讀小天才！':score>=3?'做得好！繼續閱讀！':'再讀一次故事，然後再玩一次吧！';
      body.innerHTML = '<div class="quiz-result"><div class="big">'+face+'</div>'+
        '<div class="stars">'+stars+'</div>'+
        '<h4>You scored '+score+' / '+QS.length+'!</h4>'+
        '<p>'+msg+'<br><span style="font-size:16px">'+zh+'</span></p>'+
        '<div class="quiz-next" style="text-align:center"><button class="btn-go show">Play again ↻</button></div></div>';
      burst(); burst();
      say('You scored '+score+' out of '+QS.length+'. '+msg);
      body.querySelector('.btn-go').addEventListener('click', function(){ i=0; score=0; render(); });
    }

    function burst(){
      if (!confettiBox) return;
      var colors = ['#ff7a3c','#ffd23f','#ff5d8f','#46e08a','#5b8def','#7b5cff'];
      for (var n=0; n<26; n++){
        var p = document.createElement('i');
        p.style.left = (Math.random()*100) + '%';
        p.style.background = colors[n % colors.length];
        p.style.animationDuration = (1.6 + Math.random()*1.4) + 's';
        p.style.animationDelay = (Math.random()*0.3) + 's';
        confettiBox.appendChild(p);
        (function(el){ setTimeout(function(){ el.remove(); }, 3200); })(p);
      }
    }

    render();
  }
})();
