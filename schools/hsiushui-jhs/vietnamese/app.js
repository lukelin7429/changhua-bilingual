(function(){
'use strict';
var D=window.APP_DATA, $=function(s){return document.querySelector(s)};
var FS=[18,20,22,24,26], DAY=864e5, INT=[0,1,2,4,8,16];
var CARDS={}; D.forEach(function(u){u.cards.forEach(function(c){c.unit=u.id;CARDS[c.id]=c})});
var UN={}; D.forEach(function(u){UN[u.id]=u});

/* ---------- storage ---------- */
function load(k,d){try{var v=JSON.parse(localStorage.getItem(k));return v||d}catch(e){return d}}
function save(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
var S=load('xs_set',{fs:1,ph:'py'}), P=load('xs_prog',{});
function saveS(){save('xs_set',S)} function saveP(){save('xs_prog',P)}
function applyFs(){document.documentElement.style.fontSize=FS[S.fs]+'px';$('#fsm').disabled=S.fs===0;$('#fsp').disabled=S.fs===FS.length-1}

/* ---------- helpers ---------- */
function shuffle(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}return a}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function box(id){return (P[id]&&P[id].b)||0}
function dueList(){var n=Date.now();return Object.keys(P).filter(function(id){return CARDS[id]&&P[id].b>=1&&P[id].d<=n})}
function unitProg(u){var s=0;u.cards.forEach(function(c){s+=Math.min(box(c.id),3)});return Math.round(100*s/(3*u.cards.length))}
function phon(c,ex){
  var py=ex?c.ex_py:c.py, zy=ex?c.ex_zy:c.zy;
  if(S.ph==='py')return '<span class="ph">'+esc(py)+'</span>';
  if(S.ph==='zy')return '<span class="ph">'+esc(zy)+'</span>';
  return '<span class="ph">'+esc(py)+'<span class="zy">'+esc(zy)+'</span></span>';
}
function sizeCls(c){var n=c.chars.length;return n<=2?'s1':n<=4?'s2':'s3'}
function grade(id,ok,study){
  var p=P[id]||(P[id]={b:0,d:0}),n=Date.now();
  if(study){ if(ok&&p.b===0){p.b=1;p.d=n+DAY} }
  else if(ok){p.b=Math.min(p.b+1,5);p.d=n+INT[p.b]*DAY}
  else{p.b=1;p.d=n}
  saveP();
}

/* ---------- audio ---------- */
var cur=null, slow=false;
function play(id,ex){
  try{ if(cur){cur.pause()} cur=new Audio('audio/'+id+(ex?'_ex':'')+'.mp3'); cur.playbackRate=slow?0.65:1; cur.play().catch(function(){}); }catch(e){}
}

/* ---------- views ---------- */
var app=$('#app'), view={};
function setTitle(t,back){$('#title').innerHTML=t;$('#back').hidden=!back}

function home(){
  setTitle('Học tiếng Trung <small>學中文</small>',false);
  var due=dueList().length, h='';
  h+='<div class="card banner" data-go="#/review">📅 Ôn tập hôm nay · 今日複習<small>'+(due?due+' thẻ cần ôn':'Chưa có thẻ cần ôn — hãy học thẻ mới!')+'</small></div>';
  var lastG='';
  D.forEach(function(u){
    if(u.group!==lastG){lastG=u.group;h+='<h3 class="grp">'+(u.group==='class'?'📘 Dùng trong giờ học · 上課用語':'💬 Giao tiếp hằng ngày · 日常溝通')+'</h3>'}
    h+='<div class="card unit" style="--c:'+u.color+'" data-go="#/unit/'+u.id+'"><div class="ic">'+u.icon+'</div><div style="flex:1"><h2>'+esc(u.zh)+' · '+esc(u.vi)+'</h2><p>'+esc(u.desc)+'</p><div class="bar"><i style="width:'+unitProg(u)+'%"></i></div></div></div>';
  });
  h+='<p class="center dot">Bản thử nghiệm · 原型版 · '+D.length+' 單元 / '+Object.keys(CARDS).length+' 張卡</p>';
  app.innerHTML=h;
}

function unitPage(id){
  var u=UN[id]; setTitle(u.icon+' '+esc(u.zh),true);
  var h='<div class="btns"><button class="btn" data-go="#/study/'+id+'">📖 Học thẻ<small>學習</small></button><button class="btn warm" data-go="#/quiz/'+id+'">🎯 Luyện tập<small>練習</small></button></div><div class="card">';
  u.cards.forEach(function(c){
    h+='<div class="row" data-play="'+c.id+'"><div class="z">'+esc(c.zh)+'</div><div class="m"><div class="p">'+phon(c)+'</div><div class="v">'+esc(c.vi)+'</div></div><span class="dot">'+(box(c.id)>=3?'⭐':'')+'</span><button class="spk" data-play="'+c.id+'" aria-label="Nghe">🔊</button></div>';
  });
  app.innerHTML=h+'</div>';
}

/* --- study (flashcards) --- */
function study(id){
  var u=UN[id]; setTitle('📖 '+esc(u.zh),true);
  view={list:u.cards.map(function(c){return c.id}),i:0,total:u.cards.length,done:0,uid:id,shown:false};
  studyCard(true);
}
function studyCard(auto){
  var v=view;
  if(v.i>=v.list.length){
    app.innerHTML='<div class="card center"><div class="stars">🎉</div><h2>Giỏi lắm! 太棒了！</h2><p>Em đã xem hết '+v.total+' thẻ.</p><div class="btns"><button class="btn warm" data-go="#/quiz/'+v.uid+'">🎯 Luyện tập ngay</button><button class="btn alt" data-go="#/unit/'+v.uid+'">Về danh sách</button></div></div>';
    return;
  }
  var c=CARDS[v.list[v.i]], h='';
  h+='<div class="prog">'+(v.done)+' / '+v.total+' · còn '+(v.list.length-v.i)+'</div>';
  h+='<div class="card fc"><div class="pic">'+esc(c.icon)+'</div><div class="big '+sizeCls(c)+'">'+esc(c.zh)+'</div>'+phon(c);
  h+='<div class="audiobar"><button class="spk" data-sp="'+c.id+'" aria-label="Nghe">🔊</button><button class="slow'+(slow?' on':'')+'" data-slow>🐢 Chậm</button></div>';
  if(v.shown){
    h+='<div class="mean"><div class="vi">'+esc(c.vi)+'</div>';
    if(c.hv)h+='<div class="center"><span class="chip">Âm Hán–Việt: '+esc(c.hv)+'</span></div>';
    if(c.note)h+='<div class="note">💡 '+esc(c.note)+'</div>';
    if(c.ex)h+='<div class="ex"><b>'+esc(c.ex)+'</b> <button class="spk" style="width:2.2rem;height:2.2rem" data-spx="'+c.id+'">🔊</button><br>'+phon(c,true)+'<br>'+esc(c.ex_vi)+'</div>';
    h+='</div><div class="btns"><button class="btn alt" data-st="0">🔄 Chưa nhớ</button><button class="btn" data-st="1">✅ Đã nhớ</button></div>';
  }else{
    h+='<div class="btns"><button class="btn" data-show>👀 Xem nghĩa · 看意思</button></div>';
  }
  app.innerHTML=h+'</div>';
  if(auto&&!v.shown)play(c.id);
}

/* --- quiz --- */
function distract(c,pool,key,n){
  var o=shuffle(pool.filter(function(x){return x.id!==c.id&&x[key]!==c[key]}));
  var seen={},r=[];o.forEach(function(x){if(r.length<n&&!seen[x[key]]){seen[x[key]]=1;r.push(x)}});return r;
}
function buildQs(cards,pool,n){
  cards=shuffle(cards).sort(function(a,b){return box(a.id)-box(b.id)}).slice(0,n);
  return shuffle(cards).map(function(c){
    var types=['zh2vi','vi2zh','listen'];
    if(c.chars.length>=3&&c.chars.length<=9)types.push('arrange','arrange');
    var t=types[Math.floor(Math.random()*types.length)];
    return {c:c,t:t,pool:pool};
  });
}
function quiz(id,rev){
  var cards,pool=D.reduce(function(a,u){return a.concat(u.cards)},[]);
  if(rev){setTitle('📅 Ôn tập · 複習',true);cards=dueList().map(function(i){return CARDS[i]});}
  else{var u=UN[id];setTitle('🎯 '+esc(u.zh),true);cards=u.cards;pool=u.cards}
  if(!cards.length){app.innerHTML='<div class="card center"><div class="stars">🌱</div><h2>Chưa có thẻ cần ôn</h2><p>Hãy vào một bài và bấm “Học thẻ” trước nhé.</p><div class="btns"><button class="btn" data-go="#/">Về trang chủ</button></div></div>';return}
  view={qs:buildQs(cards,pool,10),i:0,score:0,uid:id,rev:rev,ans:false,arr:null};
  quizQ(true);
}
function quizQ(auto){
  var v=view;
  if(v.i>=v.qs.length){
    var r=v.score/v.qs.length, st=r>=.9?'⭐⭐⭐':r>=.6?'⭐⭐':'⭐';
    app.innerHTML='<div class="card center"><div class="stars">'+st+'</div><h2>'+v.score+' / '+v.qs.length+'</h2><p>'+(r>=.9?'Tuyệt vời! 太厲害了！':r>=.6?'Khá lắm! 不錯喔！':'Cố lên, luyện thêm nhé! 加油！')+'</p><div class="btns"><button class="btn warm" data-again>🔁 Làm lại</button><button class="btn alt" data-go="'+(v.rev?'#/':'#/unit/'+v.uid)+'">Quay về</button></div></div>';
    return;
  }
  var q=v.qs[v.i],c=q.c,h='<div class="prog">Câu '+(v.i+1)+' / '+v.qs.length+'</div><div class="card q">';
  v.ans=false;v.arr=null;
  if(q.t==='zh2vi'||q.t==='listen'){
    var ops=shuffle([c].concat(distract(c,q.pool,'vi',3)));q.ops=ops;
    if(q.t==='zh2vi'){h+='<div class="qt">Nghĩa của từ này là gì? 這是什麼意思？</div><div class="qz">'+esc(c.zh)+'</div>'+phon(c)}
    else{h+='<div class="qt">Nghe và chọn nghĩa đúng 🎧</div><div class="audiobar"><button class="spk" data-sp="'+c.id+'">🔊</button><button class="slow'+(slow?' on':'')+'" data-slow>🐢 Chậm</button></div>'}
    h+='<div class="opts">'+ops.map(function(o,i){return '<button class="opt" data-op="'+i+'">'+esc(o.vi)+'</button>'}).join('')+'</div>';
  }else if(q.t==='vi2zh'){
    var ops2=shuffle([c].concat(distract(c,q.pool,'zh',3)));q.ops=ops2;
    h+='<div class="qt">Chọn chữ Hán đúng · 選出正確的中文</div><div class="qz" style="font-size:1.3rem">'+esc(c.vi)+'</div><div class="opts">'+ops2.map(function(o,i){return '<button class="opt zh" data-op="'+i+'">'+esc(o.zh)+'</button>'}).join('')+'</div>';
  }else{
    var tk=c.chars.map(function(ch,i){return {ch:ch,p:(S.ph==='zy'?c.zys[i]:c.pys[i]),k:i}}),sh;
    var n=0;do{sh=shuffle(tk);n++}while(n<9&&sh.every(function(t,i){return t.ch===c.chars[i]}));
    v.arr={tk:sh,pick:[]};
    h+='<div class="qt">Sắp xếp thành câu đúng · 排出正確的句子</div><div class="qz" style="font-size:1.2rem">'+esc(c.vi)+'</div><div class="audiobar"><button class="spk" data-sp="'+c.id+'">🔊</button></div><div class="slot" id="slot"></div><div class="chips" id="chips"></div>';
  }
  h+='<div id="fb"></div></div>';
  app.innerHTML=h;
  if(v.arr)drawArr();
  if(auto&&q.t==='listen')play(c.id);
}
function drawArr(){
  var a=view.arr;
  $('#slot').innerHTML=a.pick.map(function(t,j){return '<button class="tk" data-un="'+j+'">'+esc(t.ch)+'<small>'+esc(t.p)+'</small></button>'}).join('');
  $('#chips').innerHTML=a.tk.map(function(t,j){return '<button class="tk'+(a.pick.indexOf(t)>=0?' used':'')+'" data-tk="'+j+'">'+esc(t.ch)+'<small>'+esc(t.p)+'</small></button>'}).join('');
}
function finishQ(ok,q){
  var v=view;v.ans=true;if(ok)v.score++;
  grade(q.c.id,ok,false);
  var c=q.c;
  $('#fb').innerHTML='<div class="fb '+(ok?'ok':'no')+'">'+(ok?'✔ Đúng rồi! 答對了！':'✘ Chưa đúng · 再試試')+'</div><div style="margin-top:.4rem"><b>'+esc(c.zh)+'</b> · '+esc(c.vi)+'<br>'+phon(c)+'</div><div class="btns"><button class="btn" data-next>Tiếp · 下一題 →</button></div>';
  play(c.id);
  $('#fb').scrollIntoView({block:'nearest',behavior:'smooth'});
}

/* ---------- settings sheet ---------- */
function sheet(){
  var s=$('#sheet');
  s.hidden=false;s.className='sheet';
  var fsb=FS.map(function(f,i){return '<button data-fs="'+i+'" class="'+(S.fs===i?'on':'')+'" style="font-size:'+(0.7+i*0.1)+'rem">'+(i===0?'Nhỏ':i===FS.length-1?'Lớn':'A')+'</button>'}).join('');
  s.innerHTML='<div class="box"><h3>Cài đặt · 設定</h3><div>Cỡ chữ · 字體大小</div><div class="seg">'+fsb+'</div><div>Phiên âm · 讀音標示</div><div class="seg"><button data-ph="py" class="'+(S.ph==='py'?'on':'')+'">Pinyin</button><button data-ph="zy" class="'+(S.ph==='zy'?'on':'')+'">注音</button><button data-ph="both" class="'+(S.ph==='both'?'on':'')+'">Cả hai</button></div><div class="btns"><button class="btn alt danger" data-reset>Xóa tiến độ · 清除進度</button><button class="btn" data-close>Xong · 完成</button></div><p class="dot">Mẹo: thêm vào màn hình chính để dùng như ứng dụng, không cần mạng. 加到主畫面後可離線使用。</p></div>';
}

/* ---------- routing ---------- */
function route(){
  var h=location.hash.replace(/^#\/?/,'').split('/');
  window.scrollTo(0,0);
  if(h[0]==='unit'&&UN[h[1]])unitPage(h[1]);
  else if(h[0]==='study'&&UN[h[1]])study(h[1]);
  else if(h[0]==='quiz'&&UN[h[1]])quiz(h[1],false);
  else if(h[0]==='review')quiz(null,true);
  else home();
}
function parent(){
  var h=location.hash.replace(/^#\/?/,'').split('/');
  if((h[0]==='study'||h[0]==='quiz')&&h[1])location.hash='#/unit/'+h[1];else location.hash='#/';
}

/* ---------- events ---------- */
document.addEventListener('click',function(e){
  var t=e.target.closest('button,[data-go],[data-play]');if(!t)return;
  var d=t.dataset;
  if(t.id==='back'){parent();return}
  if(t.id==='fsm'){S.fs=Math.max(0,S.fs-1);saveS();applyFs();return}
  if(t.id==='fsp'){S.fs=Math.min(FS.length-1,S.fs+1);saveS();applyFs();return}
  if(t.id==='cfg'){sheet();return}
  if(d.fs!==undefined){S.fs=+d.fs;saveS();applyFs();sheet();return}
  if(d.ph){S.ph=d.ph;saveS();sheet();route_keep();return}
  if(d.close!==undefined){$('#sheet').hidden=true;return}
  if(d.reset!==undefined){if(confirm('Xóa toàn bộ tiến độ? 確定要清除進度嗎？')){P={};saveP();$('#sheet').hidden=true;route()}return}
  if(d.go){location.hash=d.go;return}
  if(d.play){play(d.play);return}
  if(d.sp){play(d.sp);return}
  if(d.spx){play(d.spx,true);return}
  if(d.slow!==undefined){slow=!slow;t.classList.toggle('on',slow);return}
  if(d.show!==undefined){view.shown=true;studyCard(false);return}
  if(d.st!==undefined){
    var id=view.list[view.i],ok=d.st==='1';
    grade(id,ok,true);
    if(ok)view.done++;else view.list.push(id);
    view.i++;view.shown=false;studyCard(true);return;
  }
  if(d.op!==undefined&&!view.ans){
    var q=view.qs[view.i],o=q.ops[+d.op],ok2=o.id===q.c.id;
    var btns=document.querySelectorAll('.opt');
    btns.forEach(function(b,i){if(q.ops[i].id===q.c.id)b.classList.add('ok')});
    if(!ok2)t.classList.add('no');
    finishQ(ok2,q);return;
  }
  if(d.tk!==undefined&&!view.ans){
    var a=view.arr,tk=a.tk[+d.tk];if(a.pick.indexOf(tk)>=0)return;
    a.pick.push(tk);drawArr();
    if(a.pick.length===a.tk.length){
      var q2=view.qs[view.i],ok3=a.pick.every(function(x,i){return x.ch===q2.c.chars[i]});
      finishQ(ok3,q2);
    }
    return;
  }
  if(d.un!==undefined&&!view.ans){view.arr.pick.splice(+d.un,1);drawArr();return}
  if(d.next!==undefined){view.i++;quizQ(true);return}
  if(d.again!==undefined){var h=location.hash;route();return}
});
function route_keep(){var h=location.hash.replace(/^#\/?/,'').split('/');if(h[0]==='unit')unitPage(h[1]);else if(h[0]==='study'||h[0]==='quiz'||h[0]==='review'){/* keep session */ if(view.qs&&view.i<view.qs.length)quizQ(false);else if(view.list)studyCard(false)}else home()}
window.addEventListener('hashchange',route);
applyFs();route();
if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){})})}
})();
