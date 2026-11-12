
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {CSS2DRenderer, CSS2DObject} from 'three/addons/renderers/CSS2DRenderer.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {mergeGeometries,mergeVertices} from 'three/addons/utils/BufferGeometryUtils.js';

const DATA=await (await fetch('model-data.json')).json();
const TEXSRC=new Proxy({},{get:(_,k)=>`img/${String(k)}.jpg`});
const L10N=window.L10N;let LANG=window.LANG_NOW;
const T_=(zh,en)=>LANG==='en'?en:zh;
const VIEW=document.getElementById('viewer');const VW=()=>VIEW.clientWidth,VH=()=>VIEW.clientHeight;
/* 年代：每期為 Google Earth Pro 歷史影像在該年底時點顯示的影像（同一相機，逐年掃描後去除重複） */
const SAMPLED=[2003,2006,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026];
const L0={sat:.95,warm:.02,con:1,vig:.32,grain:.02,tilt:1,bloom:.12,sun:[.42,.82,.42],sunCol:0xfff4e6,sunI:2.5,hemiSky:0xd6e4ef,hemiGnd:0x7f7c6a,hemiI:.95,sky:[0x8fb3d6,0xe2e8ea,0xe2e8ea],fog:0xe0e6e8,fogD:[300,1000],grow:1,clouds:.35};
const lk=o=>Object.assign({},L0,o);
const ERAS=[
 {y:2003,tex:'2003',tag:'最早期',date:'2003 年底以前的影像',text:'可取得的最早一期彩色影像。操場北側還沒有活動中心，是一整排網球場與水泥球場；紅土跑道中央是泥土草地。南側教室群屋頂多為深灰色，東南側禮堂是紅、白兩色屋頂。',
  look:lk({sat:.78,warm:.07,con:.96,vig:.42,grain:.05,sky:[0xa9bccb,0xe6e3da,0xe6e3da],fog:0xe3e0d6,grow:.7,clouds:.25})},
 {y:2011,tex:'2011',tag:'黑白影像',date:'2011 年影像',text:'這一期 Google Earth 只有黑白衛星影像。操場北側西半部已蓋起活動中心（大跨度屋頂），東半部仍是球場。',
  look:lk({sat:.06,warm:0,con:1.06,vig:.45,grain:.06,sky:[0xb8bcc0,0xe4e4e2,0xe4e4e2],fog:0xdedede,grow:.78,clouds:.2})},
 {y:2013,tex:'2013',tag:'彩色回歸',date:'2013 年影像',text:'彩色影像。活動中心屋頂是淺灰色金屬板；北側球場邊停了不少車。敬業樓屋頂為淺黃色。',
  look:lk({sat:.9,warm:.04,grow:.82})},
 {y:2014,tex:'2014',tag:'紅土跑道',date:'2014 年影像',text:'與 2013 年配置相同。紅土跑道顏色鮮明，操場中央草地偏黃。',
  look:lk({sat:.92,warm:.05,grow:.84})},
 {y:2015,tex:'2015',tag:'樂群樓屋頂',date:'2015 年影像',text:'沿東側道路的樂群樓屋頂整修，從空中看是一條亮白色長條。',
  look:lk({sat:.95,warm:.03,grow:.86})},
 {y:2016,tex:'2016',tag:'第一片光電',date:'2016 年影像',text:'活動中心屋頂鋪上太陽能光電板，敬業樓屋頂也出現一組光電板，是校園最早的屋頂光電。此期影像有薄霧。',
  look:lk({sat:.9,con:.97,grow:.88,clouds:.45})},
 {y:2017,tex:'2017',tag:'',date:'2017 年影像',text:'配置與 2016 年相同。操場南側到博愛樓之間的樹林越來越密。',
  look:lk({grow:.9})},
 {y:2018,tex:'2018',tag:'',date:'2018 年影像',text:'活動中心與敬業樓的光電板清楚可見；其餘教室棟仍是深灰色屋頂。',
  look:lk({grow:.92})},
 {y:2019,tex:'2019',tag:'',date:'2019 年影像',text:'與 2018 年相同配置，影像色調偏暖、略帶霧氣。',
  look:lk({warm:.04,con:.97,grow:.94,clouds:.4})},
 {y:2020,tex:'2020',tag:'',date:'2020 年影像（2021 年沿用）',text:'2020 年底的影像一直沿用到 2021 年底。校園樹冠已遮住大半中庭。',
  look:lk({sat:1,grow:.96})},
 {y:2022,tex:'2022',tag:'屋頂光電',date:'2022 年影像（2023 年沿用）',text:'教室棟屋頂全面鋪上深藍色光電板：勤學樓、樂群樓、弘道樓與博愛樓都換了顏色。',
  look:lk({sat:1.02,grow:.98})},
 {y:2024,tex:'2024',tag:'',date:'2024 年影像',text:'北側四座籃球場劃線清晰；除了中正堂，校內屋頂幾乎都是光電板。',
  look:lk({sat:1.04,grow:1})},
 {y:2025,tex:'2025',tag:'最清晰',date:'2025 年影像',text:'目前解析度最好的一期，建物輪廓即從這期量測。操場草地、紅土跑道、司令台與南側教室群的光電屋頂一覽無遺。',
  look:lk({sat:1.05,grow:1.02,clouds:.4})},
 {y:2026,tex:'2026sk',tag:'動畫黃昏版',sk:true,date:'2026 年影像（截至 11 月）',text:'最新一期影像：北側籃球場整片開挖施工，堆放鋼構材料。這一期改用動畫電影般的畫面重繪（靈感來自新海誠的作品）：傍晚斜陽、積雲高聳的藍天、窗玻璃反光、空中的光塵與鏡頭光暈，電線沿著校門前的道路延伸。',
  look:lk({sat:1.2,warm:.03,con:1.06,vig:.34,grain:.012,tilt:.55,bloom:.5,sun:[-.82,.12,-.55],sunCol:0xffc07a,sunI:3.6,hemiSky:0xa8d0ff,hemiGnd:0x8a7a74,hemiI:1.25,sky:[0x1650c8,0x62b8ff,0xffc58f],fog:0xc9d6ea,fogD:[420,1700],grow:1.08,clouds:1})}
];

const ERA_EN={"2003": {"tagEn": "Earliest", "dateEn": "Imagery from 2003 or earlier", "textEn": "The earliest color image available. North of the field there is no Activity Center yet, just a row of tennis and concrete courts, and the middle of the red-clay track is dirt and grass. Most classroom roofs on the south side are dark gray, and the auditorium in the southeast corner has a red-and-white roof."}, "2011": {"tagEn": "Black & white", "dateEn": "2011 imagery", "textEn": "For this year, Google Earth only has a black-and-white satellite image. The Activity Center, with its long-span roof, now stands on the west half of the courts north of the field. The east half is still courts."}, "2013": {"tagEn": "Color again", "dateEn": "2013 imagery", "textEn": "Color imagery again. The Activity Center has a light-gray metal roof, and many cars are parked beside the north courts. Jingye Hall has a pale yellow roof."}, "2014": {"tagEn": "Red-clay track", "dateEn": "2014 imagery", "textEn": "Same layout as 2013. The red-clay track stands out clearly, and the grass in the middle of the field looks yellowish."}, "2015": {"tagEn": "Lequn Hall roof", "dateEn": "2015 imagery", "textEn": "The roof of Lequn Hall, along the road on the east side, was renovated. From the air it shows up as a long, bright white strip."}, "2016": {"tagEn": "First solar panels", "dateEn": "2016 imagery", "textEn": "Solar panels go up on the Activity Center roof, and a set also appears on Jingye Hall: the first rooftop solar on campus. This image is a little hazy."}, "2017": {"tagEn": "", "dateEn": "2017 imagery", "textEn": "Same layout as 2016. The trees between the south side of the field and Bo'ai Hall keep growing thicker."}, "2018": {"tagEn": "", "dateEn": "2018 imagery", "textEn": "The solar panels on the Activity Center and Jingye Hall are easy to see. The other classroom buildings still have dark gray roofs."}, "2019": {"tagEn": "", "dateEn": "2019 imagery", "textEn": "Same layout as 2018. The image has a warm tint and a little haze."}, "2020": {"tagEn": "", "dateEn": "2020 imagery (still shown in 2021)", "textEn": "The late-2020 image was still the one shown at the end of 2021. Tree canopy now covers most of the central courtyard."}, "2022": {"tagEn": "Solar roofs", "dateEn": "2022 imagery (still shown in 2023)", "textEn": "Dark blue solar panels now cover the classroom roofs. Qinxue, Lequn, Hongdao and Bo'ai halls all changed color."}, "2024": {"tagEn": "", "dateEn": "2024 imagery", "textEn": "The lines on the four basketball courts to the north are crisp. Apart from Zhongzheng Auditorium, almost every roof on campus is covered with solar panels."}, "2025": {"tagEn": "Sharpest", "dateEn": "2025 imagery", "textEn": "The sharpest image so far, and the one the building outlines were measured from. The grass field, red-clay track, assembly stage and the solar roofs of the southern classroom buildings are all clearly visible."}, "2026": {"tagEn": "Anime sunset", "dateEn": "2026 imagery (through November)", "textEn": "The latest image: the basketball courts to the north have been dug up for construction, with steel materials stacked on site. This year is redrawn like a scene from an animated film (inspired by the work of Makoto Shinkai): low evening sun, towering clouds in a blue sky, glinting windows, floating specks of light and lens flare, with power lines running along the road in front of the school gate."}};
ERAS.forEach(e=>Object.assign(e,{tagZh:e.tag,dateZh:e.date,textZh:e.text},ERA_EN[e.y]||{}));
/* ---------- 基本設定 ---------- */
const stageEl=document.getElementById('stage');
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
renderer.setSize(VW(),VH());
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;
/* 反射環境（只給車漆、玻璃、金屬用） */
const ENV=(()=>{const pg=new THREE.PMREMGenerator(renderer);const t=pg.fromScene(new RoomEnvironment(),.04).texture;pg.dispose();return t})();
stageEl.appendChild(renderer.domElement);
const labelRenderer=new CSS2DRenderer({element:document.getElementById('labels')});
labelRenderer.setSize(VW(),VH());
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(36,VW()/VH(),1,6000);
const controls=new OrbitControls(camera,renderer.domElement);
window.__bd={get camera(){return camera},get controls(){return controls}};controls.enableDamping=true;controls.dampingFactor=.07;
controls.maxPolarAngle=1.42;controls.minDistance=30;controls.maxDistance=1000;controls.autoRotateSpeed=.6;

function rng(seed){return function(){seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function pip(p,poly){let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if(((a[1]>p[1])!==(b[1]>p[1]))&&(p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]))c=!c}return c}

/* ---------- 地理（公尺；x 向東、z 向南；原點在司令台北側） ---------- */
const BX0=-146,BZ0=-163,W=292,D=326;
const TRACK={cx:0,cz:-50};

/* ---------- 影像材質 ---------- */
const loader=new THREE.TextureLoader();
const TEX={};
function getTex(k){if(!TEX[k]){const t=loader.load(TEXSRC[k]);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=renderer.capabilities.getMaxAnisotropy();t.generateMipmaps=true;TEX[k]=t}return TEX[k]}
// 依世界座標把衛星影像投影到任何表面（屋頂、街屋頂面）
function projMat(opts={}){
 const m=new THREE.MeshStandardMaterial({map:getTex('2025'),roughness:opts.r??.88,metalness:opts.m??0,side:opts.side??THREE.FrontSide});
 m.onBeforeCompile=s=>{
  s.vertexShader=s.vertexShader.replace('#include <common>','#include <common>\nvarying vec2 vGUV;').replace('#include <begin_vertex>',`#include <begin_vertex>
   vec4 gW=vec4(transformed,1.0);
   #ifdef USE_INSTANCING
   gW=instanceMatrix*gW;
   #endif
   gW=modelMatrix*gW;
   vGUV=vec2((gW.x-(${BX0}.0))/${W}.0,1.0-(gW.z-(${BZ0}.0))/${D}.0);`);
  s.fragmentShader=s.fragmentShader.replace('#include <common>','#include <common>\nvarying vec2 vGUV;').replace('#include <map_fragment>','diffuseColor*=texture2D(map,vGUV);').replace('#include <color_fragment>','');
 };
 m.customProgramCacheKey=()=>'gproj';
 return m;
}
const projMats=[];function pm(o){const m=projMat(o);projMats.push(m);return m}
function setProjTex(k){const t=getTex(k);for(const m of projMats){m.map=t;m.needsUpdate=true}}

/* ---------- 底座 ---------- */
const baseGroup=new THREE.Group();scene.add(baseGroup);
const woodC=document.createElement('canvas');woodC.width=1024;woodC.height=64;
{const g=woodC.getContext('2d');g.fillStyle='#4f3524';g.fillRect(0,0,1024,64);const r=rng(7);for(let i=0;i<140;i++){g.strokeStyle=`rgba(${30+r()*40|0},${18+r()*20|0},10,${.15+r()*.25})`;g.lineWidth=.5+r()*1.5;g.beginPath();const y=r()*64;g.moveTo(0,y);for(let x=0;x<=1024;x+=64)g.lineTo(x,y+Math.sin(x*.01+i)*2*r());g.stroke()}}
const woodTex=new THREE.CanvasTexture(woodC);woodTex.colorSpace=THREE.SRGBColorSpace;
const plinth=new THREE.Mesh(new THREE.BoxGeometry(W+8,7,D+8),new THREE.MeshStandardMaterial({map:woodTex,roughness:.55,metalness:.05}));
plinth.position.set(0,-3.55,0);plinth.receiveShadow=plinth.castShadow=true;baseGroup.add(plinth);
const plateC=document.createElement('canvas');plateC.width=1280;plateC.height=96;
const plateTex=new THREE.CanvasTexture(plateC);plateTex.colorSpace=THREE.SRGBColorSpace;
const plate=new THREE.Mesh(new THREE.PlaneGeometry(80,6),new THREE.MeshStandardMaterial({map:plateTex,metalness:.6,roughness:.35}));
plate.position.set(0,-3.5,D/2+4.06);baseGroup.add(plate);
function drawPlate(e){const g=plateC.getContext('2d');const gr=g.createLinearGradient(0,0,0,96);gr.addColorStop(0,'#d9b56a');gr.addColorStop(.5,'#b48a3c');gr.addColorStop(1,'#8c6a2a');g.fillStyle=gr;g.fillRect(0,0,1280,96);
 g.strokeStyle='rgba(60,40,10,.6)';g.lineWidth=3;g.strokeRect(6,6,1268,84);g.fillStyle='#3a2a10';g.textAlign='center';g.textBaseline='middle';
 g.font='700 40px "PingFang TC","Microsoft JhengHei",sans-serif';g.fillText('彰化縣北斗鎮 彰化縣立北斗國民中學',640,40);g.font='500 24px "Inter",sans-serif';g.fillText(`BEIDOU JUNIOR HIGH SCHOOL  ·  ${e.y<=2003?'≤2003':e.y}  ·  IMAGERY © GOOGLE`,640,74);plateTex.needsUpdate=true}

/* ---------- 地面：當期正射影像 ---------- */
const groundMat=new THREE.MeshStandardMaterial({map:getTex('2025'),roughness:.93});
const ground=new THREE.Mesh(new THREE.PlaneGeometry(W,D),groundMat);
ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);

/* ---------- 材質工具 ---------- */
const texCache=new Map();
function canvasTex(key,w,h,draw,rep){if(texCache.has(key))return texCache.get(key);const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;if(rep){t.wrapS=t.wrapT=THREE.RepeatWrapping}texCache.set(key,t);return t}
function facadeTex(len,floors,sk,old,variant){
 const key=`f${Math.round(len)}_${floors}_${sk}_${old}_${variant}`;
 const ppm=16,w=Math.min(2048,Math.max(64,Math.round(len*ppm))),h=Math.round(floors*3.6*ppm+10);
 return canvasTex(key,w,h,(g)=>{
  let seed=(w*131+floors*17+(sk?7:0)+(old?3:0))>>>0;const rnd=()=>(seed=(seed*1664525+1013904223)>>>0)/4294967296;
  const wall=old?'#e2dccd':'#f1ede4',band=old?'#d6cdbb':'#e7e0d3',shade=sk?'#2f3654':'#3d3c3a',brick=sk?'#c75b42':'#9a5642',frame=sk?'#d9d2c8':'#c9ccc9';
  const glassTop=sk?'#ffe1a8':'#b7c9d3',glassBot=sk?'#e88a52':'#5d7584';
  g.fillStyle=wall;g.fillRect(0,0,w,h);
  // 磁磚縫
  g.fillStyle='rgba(90,80,60,.06)';for(let y=h;y>0;y-=4)g.fillRect(0,y,w,1);for(let x=0;x<w;x+=8)g.fillRect(x,0,1,h);
  const fh=3.6*ppm;
  for(let f=0;f<floors;f++){const y0=h-(f+1)*fh;
   if(variant==='end'){g.fillStyle=band;g.fillRect(0,y0+fh-6,w,6);g.fillStyle='rgba(0,0,0,.10)';g.fillRect(0,y0+fh-6,w,1.5);
    const ww=Math.min(w*.32,22),wx=w/2-ww/2,wy=y0+12,wh=fh-26;g.fillStyle=frame;g.fillRect(wx-2,wy-2,ww+4,wh+4);
    const gr=g.createLinearGradient(0,wy,0,wy+wh);gr.addColorStop(0,glassTop);gr.addColorStop(1,glassBot);g.fillStyle=gr;g.fillRect(wx,wy,ww,wh);
    g.fillStyle=frame;g.fillRect(wx+ww/2-1,wy,2,wh);g.fillRect(wx,wy+wh*.3,ww,2);continue}
   // 走廊陰影（上深下淺）
   const ch=fh*.6,sg=g.createLinearGradient(0,y0,0,y0+ch);sg.addColorStop(0,'rgba(10,10,12,.95)');sg.addColorStop(1,'rgba(40,40,44,.75)');
   g.fillStyle=shade;g.fillRect(0,y0+3,w,ch);g.fillStyle=sg;g.globalAlpha=.55;g.fillRect(0,y0+3,w,ch);g.globalAlpha=1;
   const bays=Math.max(1,Math.round(len/4));const bw=w/bays;
   for(let b=0;b<bays;b++){const x=b*bw,wx=x+bw*.14,wy=y0+9,ww=bw*.72,wh=ch*.72;
    g.fillStyle=frame;g.fillRect(wx-2,wy-2,ww+4,wh+4);
    const gr=g.createLinearGradient(0,wy,0,wy+wh);gr.addColorStop(0,glassTop);gr.addColorStop(1,glassBot);g.fillStyle=gr;
    g.globalAlpha=sk?(.6+.4*((b*7+f*3)%5)/4):.9;g.fillRect(wx,wy,ww,wh);g.globalAlpha=1;
    // 窗框分隔與氣窗
    g.fillStyle=frame;const panes=3;for(let k=1;k<panes;k++)g.fillRect(wx+ww*k/panes-1,wy,2,wh);g.fillRect(wx,wy+wh*.28,ww,2);
    // 窗簾／室內
    if(rnd()<.35){g.fillStyle=sk?'rgba(255,230,190,.35)':'rgba(240,240,230,.35)';g.fillRect(wx+2,wy+wh*.3+2,ww/panes-3,wh*.7-3)}
    // 柱子
    g.fillStyle=wall;g.fillRect(x,y0,Math.max(3,bw*.07),fh);g.fillStyle='rgba(0,0,0,.18)';g.fillRect(x+Math.max(3,bw*.07),y0+3,2,ch)}
   // 欄杆女兒牆
   const py=y0+ch+3,ph=fh-ch-3;g.fillStyle=band;g.fillRect(0,py,w,ph);
   g.fillStyle='rgba(255,255,255,.55)';g.fillRect(0,py,w,2);g.fillStyle='rgba(0,0,0,.16)';g.fillRect(0,py+2,w,1.5);
   g.fillStyle='rgba(120,125,130,.9)';g.fillRect(0,py-5,w,1.5);for(let x=0;x<w;x+=10)g.fillRect(x,py-5,1,5);
   // 雨漬
   for(let k=0;k<w/22;k++){const sx=rnd()*w,sl=ph*(.4+rnd()*.6);const st=g.createLinearGradient(0,py+3,0,py+3+sl);st.addColorStop(0,'rgba(70,65,55,.16)');st.addColorStop(1,'rgba(70,65,55,0)');g.fillStyle=st;g.fillRect(sx,py+3,2+rnd()*3,sl)}
   if(f===0){g.fillStyle=brick;g.fillRect(0,h-9,w,9);const gg=g.createLinearGradient(0,h-26,0,h-9);gg.addColorStop(0,'rgba(60,55,45,0)');gg.addColorStop(1,'rgba(60,55,45,.18)');g.fillStyle=gg;g.fillRect(0,h-26,w,17)}}
  // 頂部壓簷
  g.fillStyle=band;g.fillRect(0,0,w,6);g.fillStyle='rgba(0,0,0,.15)';g.fillRect(0,6,w,1.5);
  if(old){g.fillStyle='rgba(80,70,50,.06)';for(let i=0;i<w;i+=7)g.fillRect(i,0,2,h)}
 });
}
function edgeList(p){const out=[];for(let i=0;i<p.length;i++){const a=p[i],b=p[(i+1)%p.length];const dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz);let nx=dz/len,nz=-dx/len;const mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2;if(pip([mx+nx*.3,mz+nz*.3],p)){nx=-nx;nz=-nz}out.push({a,b,len,mx,mz,nx,nz})}return out}
function centroid(p){let x=0,z=0;for(const q of p){x+=q[0];z+=q[1]}return[x/p.length,z/p.length]}
function shapeOf(p,scale=1,c=[0,0]){const s=new THREE.Shape();p.forEach((q,i)=>{const x=c[0]+(q[0]-c[0])*scale,z=c[1]+(q[1]-c[1])*scale;i?s.lineTo(x,-z):s.moveTo(x,-z)});s.closePath();return s}

/* ---------- 校內建物 ---------- */
const bldGroup=new THREE.Group();scene.add(bldGroup);
const pickables=[];
const roofMat=pm({r:.8}),roofMatD=pm({r:.6,side:THREE.DoubleSide});
let showLabels=true;
function addLabel(grp,text,y,c,pri=0){const el=document.createElement('div');el.className='lbl'+(showLabels?'':' hide');el.textContent=text;el.dataset.pri=pri;const lo=new CSS2DObject(el);lo.position.set(c[0],y,c[1]);grp.add(lo)}
function clearGroup(G){for(const c of [...G.children]){c.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.isCSS2DObject&&o.element)o.element.remove()});G.remove(c)}}
function wallsFor(grp,b,h,sk,old,y0=0){
 const floors=Math.max(1,Math.round(h/3.6));
 for(const E of edgeList(b.p)){
  const t=facadeTex(E.len,floors,sk,old,E.len<14?'end':'long');
  const m=new THREE.Mesh(new THREE.PlaneGeometry(E.len,h),new THREE.MeshStandardMaterial({map:t,roughness:.75}));
  m.position.set(E.mx,y0+h/2,E.mz);m.rotation.y=Math.atan2(E.nx,E.nz);m.castShadow=m.receiveShadow=true;grp.add(m);pickables.push(m);m.userData.grp=grp;
 }
}
function parapet(grp,b,h,col){const pmM=new THREE.MeshStandardMaterial({color:col,roughness:.8});
 for(const E of edgeList(b.p)){const m=new THREE.Mesh(new THREE.BoxGeometry(E.len,1,.35),pmM);m.position.set(E.mx-E.nx*.17,h+.5,E.mz-E.nz*.17);m.rotation.y=Math.atan2(E.nx,E.nz);m.castShadow=true;grp.add(m)}}
function flatRoof(grp,b,h){const g=new THREE.ShapeGeometry(shapeOf(b.p));g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,roofMat);m.position.y=h+.02;m.receiveShadow=true;m.castShadow=true;grp.add(m);pickables.push(m);m.userData.grp=grp}
function hipRoof(grp,b,h,rise){
 const c=centroid(b.p),k=.42,P=b.p,pos=[];
 const top=P.map(q=>[c[0]+(q[0]-c[0])*k,c[1]+(q[1]-c[1])*k]);
 for(let i=0;i<P.length;i++){const j=(i+1)%P.length;const a=P[i],bb=P[j],ta=top[i],tb=top[j];
  pos.push(a[0],h,a[1], bb[0],h,bb[1], tb[0],h+rise,tb[1], a[0],h,a[1], tb[0],h+rise,tb[1], ta[0],h+rise,ta[1])}
 pos.push(top[0][0],h+rise,top[0][1],top[2][0],h+rise,top[2][1],top[1][0],h+rise,top[1][1], top[0][0],h+rise,top[0][1],top[3][0],h+rise,top[3][1],top[2][0],h+rise,top[2][1]);
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(new Array(pos.length/3*2).fill(0),2));g.computeVertexNormals();
 const m=new THREE.Mesh(g,roofMatD);m.castShadow=m.receiveShadow=true;grp.add(m);pickables.push(m);m.userData.grp=grp}
function vaultRoof(grp,b,h,sk){
 const xs=b.p.map(q=>q[0]),zs=b.p.map(q=>q[1]);const x0=Math.min(...xs),x1=Math.max(...xs),z0=Math.min(...zs),z1=Math.max(...zs);
 const lx=x1-x0,lz=z1-z0,cx=(x0+x1)/2,cz=(z0+z1)/2,s=3.2,half=lz/2,R=(half*half+s*s)/(2*s),th=2*Math.asin(half/R);
 const g=new THREE.CylinderGeometry(R,R,lx+.8,48,1,true,-th/2,th);g.rotateX(-Math.PI/2);g.rotateY(Math.PI/2);
 const m=new THREE.Mesh(g,roofMatD);m.position.set(cx,h+s-R,cz);m.castShadow=m.receiveShadow=true;grp.add(m);pickables.push(m);m.userData.grp=grp;
 const sh=new THREE.Shape();sh.moveTo(-half,0);sh.absarc(0,s-R,R,Math.PI/2+th/2,Math.PI/2-th/2,true);sh.lineTo(-half,0);
 const eg=new THREE.ShapeGeometry(sh,24);const em=new THREE.MeshStandardMaterial({color:sk?0xf3e9e6:0xdcd9d2,side:THREE.DoubleSide});
 for(const sx of [-1,1]){const e=new THREE.Mesh(eg,em);e.rotation.y=Math.PI/2;e.position.set(cx+sx*lx/2,h,cz);grp.add(e)}
}
function buildStage(grp,b,sk){
 // 司令台：後棟＋朝北半圓雨庇（白色帶狀簷口、紅柱，參考環景照）
 const xs=b.p.map(q=>q[0]),zs=b.p.map(q=>q[1]);const x0=Math.min(...xs),x1=Math.max(...xs),z0=Math.min(...zs),z1=Math.max(...zs);
 const cx=(x0+x1)/2,lx=x1-x0;
 const white=new THREE.MeshStandardMaterial({color:sk?0xfbf4ec:0xece8df,roughness:.7});
 const red=new THREE.MeshStandardMaterial({color:sk?0xd0503e:0x9e3b30,roughness:.6});
 const back={p:[[x0,z0+8],[x1,z0+8],[x1,z1],[x0,z1]]};
 wallsFor(grp,back,6,sk,false);flatRoof(grp,back,6);parapet(grp,back,6,sk?0xf7efe6:0xe6e0d4);
 const R=lx/2-.4;
 const plat=new THREE.Mesh(new THREE.CylinderGeometry(R,R,1.2,40,1,false,Math.PI/2,Math.PI),white);plat.position.set(cx,.6,z0+8);plat.castShadow=plat.receiveShadow=true;grp.add(plat);
 const canopy=new THREE.Mesh(new THREE.CylinderGeometry(R+.6,R+.6,.5,40,1,false,Math.PI/2,Math.PI),white);canopy.position.set(cx,6.6,z0+8);canopy.castShadow=true;grp.add(canopy);pickables.push(canopy);canopy.userData.grp=grp;
 const signT=canvasTex(`stage_${sk}`,1024,64,(g,w,h)=>{g.fillStyle=sk?'#fff8f0':'#efebe3';g.fillRect(0,0,w,h);g.fillStyle=sk?'#c43f32':'#8e2f27';g.fillRect(0,h-6,w,6);g.font='700 40px "PingFang TC","Microsoft JhengHei",sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText('司　令　台',w/2,h/2-2)});
 const band=new THREE.Mesh(new THREE.CylinderGeometry(R+.65,R+.65,1.5,40,1,true,Math.PI/2,Math.PI),new THREE.MeshStandardMaterial({map:signT,roughness:.7}));band.position.set(cx,7.3,z0+8);grp.add(band);
 for(const a of [Math.PI*.62,Math.PI*1.38]){const c=new THREE.Mesh(new THREE.BoxGeometry(.7,5.4,.7),red);c.position.set(cx+Math.sin(a)*R*.86,3.9,z0+8+Math.cos(a)*R*.86);c.castShadow=true;grp.add(c)}
 const steps=new THREE.Mesh(new THREE.BoxGeometry(5,.6,2),white);steps.position.set(cx,.3,z0+8-R-.8);grp.add(steps);
}
function buildBuildings(e){
 clearGroup(bldGroup);pickables.length=0;
 const sk=!!e.sk,old=e.y<2011;
 for(const b of DATA.B){
  if(b.from&&e.y<b.from)continue;
  const grp=new THREE.Group();grp.userData.b=b;bldGroup.add(grp);const c=centroid(b.p);
  if(b.kind==='stage'){buildStage(grp,b,sk);if(!b.nolabel)addLabel(grp,bName(b),10,c,area(b.p));continue}
  const h=b.h;
  wallsFor(grp,b,h,sk,old);
  if(b.kind==='hip'){hipRoof(grp,b,h,3.2)}
  else if(b.kind==='vault'){vaultRoof(grp,b,h,sk)}
  else{flatRoof(grp,b,h);parapet(grp,b,h,old?0xd9d2c2:(sk?0xf7efe6:0xece6da))}
  if(!b.nolabel)addLabel(grp,bName(b),h+(b.kind==='vault'||b.kind==='hip'?5:2.5),c,area(b.p));
 }
}

/* ---------- 校園附屬：圍牆、校門、旗桿、球門、施工中塔吊 ---------- */
const fixtures=new THREE.Group();scene.add(fixtures);
const GATE={x:-9,z:99,rot:-Math.atan2(220,300)};
function buildFixtures(e){
 clearGroup(fixtures);const sk=!!e.sk;
 const wallM=new THREE.MeshStandardMaterial({color:sk?0xf2e8de:0xe2dccf,roughness:.85});
 const capM=new THREE.MeshStandardMaterial({color:sk?0xc95a40:0x9e5644,roughness:.7});
 const C=DATA.CAMPUS;
 for(let i=0;i<C.length;i++){const a=C[i],b=C[(i+1)%C.length];const len=Math.hypot(b[0]-a[0],b[1]-a[1]);const ang=Math.atan2(b[1]-a[1],b[0]-a[0]);
  const mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2;
  const n=Math.max(1,Math.round(len/12));
  for(let k=0;k<n;k++){const t0=k/n,t1=(k+1)/n;const px=a[0]+(b[0]-a[0])*(t0+t1)/2,pz=a[1]+(b[1]-a[1])*(t0+t1)/2;if(Math.hypot(px-GATE.x,pz-GATE.z)<9)continue;const L=len/n;
   const w=new THREE.Mesh(new THREE.BoxGeometry(L,1.4,.3),wallM);w.position.set(px,.7,pz);w.rotation.y=-ang;w.castShadow=w.receiveShadow=true;fixtures.add(w);
   const c=new THREE.Mesh(new THREE.BoxGeometry(L,.16,.45),capM);c.position.set(px,1.48,pz);c.rotation.y=-ang;fixtures.add(c)}}
 // 校門
 const gate=new THREE.Group();gate.position.set(GATE.x,0,GATE.z);gate.rotation.y=GATE.rot;fixtures.add(gate);
 for(const x of [-6.5,6.5]){const p=new THREE.Mesh(new THREE.BoxGeometry(1.6,4.4,1.6),capM);p.position.set(x,2.2,0);p.castShadow=true;gate.add(p)}
 const signC=canvasTex(`gate_${sk}`,768,96,(g,w,h)=>{g.fillStyle=sk?'#2a2f45':'#2c2a26';g.fillRect(0,0,w,h);g.fillStyle=sk?'#ffe2b0':'#e9dcc0';g.font='700 52px "PingFang TC","Microsoft JhengHei",sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText('彰化縣立北斗國民中學',w/2,h/2+3)});
 const sm=new THREE.MeshStandardMaterial({map:signC});
 const beam=new THREE.Mesh(new THREE.BoxGeometry(14.6,1.4,.9),[capM,capM,capM,capM,sm,sm]);beam.position.set(0,4.6,0);beam.castShadow=true;gate.add(beam);
 // 旗桿（圓環廣場）
 const poleM=new THREE.MeshStandardMaterial({color:0xb8b8b8,roughness:.4,metalness:.6});
 for(const dx of [-3,0,3]){const p=new THREE.Mesh(new THREE.CylinderGeometry(.09,.13,11,8),poleM);p.position.set(-14+dx,5.5,84);p.castShadow=true;fixtures.add(p)}
 // 足球門
 const goalM=new THREE.MeshStandardMaterial({color:0xf4f4f0,roughness:.5});
 for(const x of [-50,51]){const g=new THREE.Group();g.position.set(x,0,-50);
  for(const z of [-3.66,3.66]){const p=new THREE.Mesh(new THREE.CylinderGeometry(.07,.07,2.44,6),goalM);p.position.set(0,1.22,z);g.add(p)}
  const bar=new THREE.Mesh(new THREE.CylinderGeometry(.07,.07,7.32,6),goalM);bar.rotation.x=Math.PI/2;bar.position.y=2.44;g.add(bar);fixtures.add(g)}
 // 2026：北側球場施工中（影像可見開挖與鋼構材料）
 if(e.y>=2026){
  const yel=new THREE.MeshStandardMaterial({color:0xf2b233,roughness:.5,metalness:.3});
  const crane=new THREE.Group();crane.position.set(52,0,-118);fixtures.add(crane);
  const mast=new THREE.Mesh(new THREE.BoxGeometry(1.4,32,1.4),yel);mast.position.y=16;mast.castShadow=true;crane.add(mast);
  const jib=new THREE.Mesh(new THREE.BoxGeometry(42,1,1),yel);jib.position.set(-12,32.5,0);jib.castShadow=true;crane.add(jib);
  const cw=new THREE.Mesh(new THREE.BoxGeometry(4,2,2),new THREE.MeshStandardMaterial({color:0x777777}));cw.position.set(8,31.5,0);crane.add(cw);
  const cab=new THREE.Mesh(new THREE.BoxGeometry(2,2,2),new THREE.MeshStandardMaterial({color:0xffffff}));cab.position.set(1.6,30.5,0);crane.add(cab);
  const rope=new THREE.Mesh(new THREE.CylinderGeometry(.05,.05,20,4),new THREE.MeshStandardMaterial({color:0x333333}));rope.position.set(-24,22.5,0);crane.add(rope);
  const fM=new THREE.MeshStandardMaterial({color:0x3c6fb0,roughness:.6});
  for(const [x0,z0,x1,z1] of [[-2,-128,72,-128],[-2,-98,72,-98],[-2,-128,-2,-98],[72,-128,72,-98]]){const L=Math.hypot(x1-x0,z1-z0);const f=new THREE.Mesh(new THREE.BoxGeometry(L||.2,2,.15),fM);f.position.set((x0+x1)/2,1,(z0+z1)/2);f.rotation.y=-Math.atan2(z1-z0,x1-x0);fixtures.add(f)}
 }
}

/* ---------- 街區：依當期影像判讀的屋頂格（2 m），頂面直接貼影像 ---------- */
const T=DATA.TOWN;const GW=T.GW,GH=T.GH,CELL=T.cell;
let maxCells=0;for(const k in T.eras){let n=0;const s=T.eras[k];for(let i=0;i<s.length;i++)if(s.charCodeAt(i)>48)n++;maxCells=Math.max(maxCells,n)}
const townGeo=new THREE.BoxGeometry(1,1,1);townGeo.translate(0,.5,0);
const sideMat=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.82});
sideMat.onBeforeCompile=s=>{
 s.vertexShader=s.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;').replace('#include <begin_vertex>',`#include <begin_vertex>
  vec4 tw=vec4(transformed,1.0);
  #ifdef USE_INSTANCING
  tw=instanceMatrix*tw;
  #endif
  vWP=(modelMatrix*tw).xyz;vWN=normal;`);
 s.fragmentShader=s.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;uniform float uSk;').replace('#include <color_fragment>',`#include <color_fragment>
  float fl=floor(vWP.y/3.2),fy=fract(vWP.y/3.2);float hz=abs(vWN.x)>.5?vWP.z:vWP.x;float bay=floor(hz/2.0),fx=fract(hz/2.0);
  float side=step(abs(vWN.y),.5);float rid=fract(sin(dot(vec2(bay,fl)+floor(vWP.xz/6.0)*7.0,vec2(12.9898,78.233)))*43758.5453);
  diffuseColor.rgb*=1.0-.05*step(.92,fract(vWP.y/.25))*side;
  float up=step(3.0,vWP.y);
  float inW=step(.30,fy)*step(fy,.78)*step(.14,fx)*step(fx,.86)*up*side;
  float inG=step(.33,fy)*step(fy,.75)*step(.17,fx)*step(fx,.83)*inW;
  vec3 glass=mix(vec3(.13,.17,.21),vec3(.42,.5,.56),smoothstep(.33,.75,fy));
  float lit=uSk*step(.5,rid);glass=mix(glass,vec3(1.0,.80,.55),lit);
  diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.78,.79,.8),inW*(1.-inG));
  diffuseColor.rgb=mix(diffuseColor.rgb,glass,inG*.95);
  diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.78,.79,.8),inG*step(abs(fx-.5),.012));
  float grille=inG*step(rid,.45)*max(step(.86,fract(fx*11.)),step(.9,fract(fy*5.5)));
  diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.2,.21,.22),grille);
  float ac=step(.45,rid)*step(rid,.62)*step(.6,fx)*step(fx,.85)*step(.12,fy)*step(fy,.27)*up*side;
  diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.83,.83,.8)*(.9+.1*step(.5,fract(fy*40.))),ac);
  float gf=(1.-up)*side*step(.15,vWP.y)*step(vWP.y,2.75)*step(.06,fx)*step(fx,.94);
  vec3 shop=rid>.5?vec3(.6,.61,.62)*(.86+.14*step(.5,fract(vWP.y*7.))):vec3(.1,.1,.11);
  diffuseColor.rgb=mix(diffuseColor.rgb,shop,gf);
  diffuseColor.rgb*=1.0-.12*(1.0-step(.08,fy));`);
 s.uniforms.uSk=sideUni.uSk;
};
const sideUni={uSk:{value:0}};
const topMat=pm({r:.9});
const townMesh=new THREE.InstancedMesh(townGeo,[sideMat,sideMat,topMat,sideMat,sideMat,sideMat],maxCells);
townMesh.castShadow=townMesh.receiveShadow=true;townMesh.instanceColor=new THREE.InstancedBufferAttribute(new Float32Array(maxCells*3),3);scene.add(townMesh);
const TOWN=['#efeae0','#e6dfd2','#d9d6cf','#f3efe8','#e8d9c7','#d5cdc0','#cfd5d6','#eadfd0','#e4d3c3','#ddd0bc','#c9c2b6','#f0e6d8'];
const tankGeo=mergeGeometries([new THREE.CylinderGeometry(.62,.62,1.25,16).translate(0,1.1,0).toNonIndexed(),new THREE.SphereGeometry(.62,16,6,0,Math.PI*2,0,Math.PI/2).scale(1,.3,1).translate(0,1.72,0).toNonIndexed(),new THREE.BoxGeometry(1.1,.48,1.1).translate(0,.24,0).toNonIndexed()]);
const tanks=new THREE.InstancedMesh(tankGeo,new THREE.MeshStandardMaterial({color:0xffffff,roughness:.28,metalness:.85,envMap:ENV}),Math.ceil(maxCells*.06)+8);tanks.castShadow=true;scene.add(tanks);
function layoutTanks(s){const m=new THREE.Matrix4(),c=new THREE.Color();let n=0;
 for(let j=0;j<GH;j++)for(let i=0;i<GW;i++){const f=s.charCodeAt(j*GW+i)-48;if(f<2)continue;const hsh=((i*73856093)^(j*19349663))>>>0;if(hsh%23!==0||n>=tanks.count)continue;
  m.makeTranslation(BX0+(i+.5)*CELL,f*3.2+.4,BZ0+(j+.5)*CELL);tanks.setMatrixAt(n,m);tanks.setColorAt(n,c.set(hsh%5===0?0x2f6fb3:0xe4e8ec));n++}
 for(let k=n;k<tanks.count;k++)tanks.setMatrixAt(k,new THREE.Matrix4().makeScale(0,0,0));tanks.instanceMatrix.needsUpdate=true;if(tanks.instanceColor)tanks.instanceColor.needsUpdate=true}
const TOWN_SK=['#fbf3ea','#f4ebe0','#efe9e4','#fff8f0','#f6e4d2','#e9e2da','#e3e8ee','#f8ecdc','#efe0d4','#f2e6d6','#e6e2e6','#fbf0e4'];
function layoutTown(e){
 const s=T.eras[String(e.y)];const m=new THREE.Matrix4(),q=new THREE.Quaternion(),sc=new THREE.Vector3(),p=new THREE.Vector3(),c=new THREE.Color();
 const pal=e.sk?TOWN_SK:TOWN;let n=0;
 for(let j=0;j<GH;j++)for(let i=0;i<GW;i++){const f=s.charCodeAt(j*GW+i)-48;if(f<=0)continue;
  const lot=((Math.floor(i/2)*73856093)^(Math.floor(j/5)*19349663))>>>0;
  p.set(BX0+(i+.5)*CELL,0,BZ0+(j+.5)*CELL);sc.set(CELL+.02,f*3.2+.4,CELL+.02);m.compose(p,q,sc);townMesh.setMatrixAt(n,m);
  c.set(pal[lot%pal.length]);if(e.y<2011)c.offsetHSL(0,-.06,-.05);if(e.y===2011){const l=c.getHSL({}).l;c.setHSL(0,0,l*.95)}townMesh.setColorAt(n,c);n++}
 townMesh.count=n;layoutTanks(s);townMesh.instanceMatrix.needsUpdate=true;townMesh.instanceColor.needsUpdate=true;sideUni.uSk.value=e.sk?1:0;
}

/* ---------- 樹木（位置判讀自 2025 年影像） ---------- */
const treeSpecs=DATA.TREES.map((t,i)=>({x:t[0],z:t[1],s:t[2],ph:(i*2.399)%6.28}));
const trunkGeo=(()=>{const g=new THREE.CylinderGeometry(.15,.3,1,7,4);g.translate(0,.5,0);const p=g.attributes.position;for(let i=0;i<p.count;i++){const y=p.getY(i);p.setX(i,p.getX(i)+Math.sin(y*4.2)*.05);p.setZ(i,p.getZ(i)+Math.cos(y*3.1)*.04)}g.computeVertexNormals();return g})();
const blobGeo=(()=>{let g=new THREE.IcosahedronGeometry(1,2);g.deleteAttribute('normal');g.deleteAttribute('uv');g=mergeVertices(g);const p=g.attributes.position,v=new THREE.Vector3(),col=[];
 for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i);const n=Math.sin(v.x*4.1+v.y*2.3)*Math.sin(v.y*3.7-v.z*2.9)*Math.sin(v.z*4.3+v.x*1.7);v.multiplyScalar(1+n*.24+Math.sin(v.x*11+v.z*9)*.05);if(v.y<-.25)v.y=-.25+(v.y+.25)*.5;p.setXYZ(i,v.x,v.y,v.z);
  const sh=THREE.MathUtils.clamp(.52+.5*(v.y+.5)/1.5,.5,1.05);col.push(sh,sh,sh*.97)}
 g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.computeVertexNormals();return g})();
const leafMat=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.9,vertexColors:true});
leafMat.onBeforeCompile=s=>{
 s.vertexShader=s.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vLP;').replace('#include <begin_vertex>','#include <begin_vertex>\nvLP=position;');
 s.fragmentShader=s.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 vLP;\nfloat h3(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}\nfloat vn(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z);}')
  .replace('#include <color_fragment>','#include <color_fragment>\n{vec3 q=vLP*4.5;float k=.55*vn(q)+.3*vn(q*2.4+7.)+.15*vn(q*6.1+3.);diffuseColor.rgb*=.62+.7*k;}')
  .replace('#include <normal_fragment_maps>','#include <normal_fragment_maps>\n{vec3 q=vLP*4.5*2.4+7.;float n0=vn(q);vec3 gq=vec3(vn(q+vec3(.12,0,0)),vn(q+vec3(0,.12,0)),vn(q+vec3(0,0,.12)))-n0;normal=normalize(normal-gq*5.5);\n float rim=1.-abs(dot(normalize(vNormal),normalize(vViewPosition)));if(rim>.5&&vn(vLP*9.)+.35*(rim-.5)/.5>.78)discard;}');
};
const trunks=new THREE.InstancedMesh(trunkGeo,new THREE.MeshStandardMaterial({color:0x5a4434,roughness:1}),treeSpecs.length);trunks.castShadow=true;
const blobs=new THREE.InstancedMesh(blobGeo,leafMat,treeSpecs.length*3);blobs.castShadow=true;blobs.receiveShadow=true;
scene.add(trunks,blobs);
let treeGrow=1,treeGrowTarget=1,treeMode=0;
function layoutTrees(grow,mode){
 const m=new THREE.Matrix4(),q=new THREE.Quaternion(),s=new THREE.Vector3(),p=new THREE.Vector3(),c=new THREE.Color();const up=new THREE.Vector3(0,1,0);let bi=0;
 treeSpecs.forEach((t,i)=>{const sc=t.s*grow;const h=2.3*sc;s.set(1,h,1);p.set(t.x,0,t.z);q.setFromAxisAngle(up,t.ph);m.compose(p,q,s);trunks.setMatrixAt(i,m);
  for(let k=0;k<3;k++){const a=t.ph+k*2.1,rr=1.05*sc;const sz=(k?1.55+((k+i)%3)*.35:2.25)*sc;
   p.set(t.x+Math.cos(a)*rr*(k?1:0),h+sz*.42+(k?-.15:.35)*sc,t.z+Math.sin(a)*rr*(k?1:0));s.set(sz,sz*.82,sz);q.setFromAxisAngle(up,a+i);m.compose(p,q,s);blobs.setMatrixAt(bi,m);
   if(mode===2){c.setHSL(.26+((i*7+k)%5)*.012,.6,.40+k*.04)}else if(mode===1){c.setHSL(0,0,.38+k*.04)}else{c.setHSL(.255+((i*7+k)%5)*.012,.5,.28+k*.03)}
   blobs.setColorAt(bi,c);bi++}});
 trunks.instanceMatrix.needsUpdate=blobs.instanceMatrix.needsUpdate=true;if(blobs.instanceColor)blobs.instanceColor.needsUpdate=true;
}

/* ---------- 電線桿（校門前道路） ---------- */
const poleGroup=new THREE.Group();scene.add(poleGroup);
(function(){
 const pmM=new THREE.MeshStandardMaterial({color:0x8d8a84,roughness:.7});
 const wireM=new THREE.LineBasicMaterial({color:0x2a2c35,transparent:true,opacity:.85});
 const P=DATA.POLE;const poles=[];
 for(let i=0;i<P.length-1;i++){const a=P[i],b=P[i+1];const L=Math.hypot(b[0]-a[0],b[1]-a[1]);const n=Math.max(1,Math.round(L/24));for(let k=0;k<n;k++){const t=k/n;poles.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t])}}
 poles.push(P[P.length-1]);
 const inside=poles.filter(p=>p[0]>BX0+2&&p[0]<BX0+W-2&&p[1]>BZ0+2&&p[1]<BZ0+D-2);
 for(const [x,z] of inside){const p=new THREE.Mesh(new THREE.CylinderGeometry(.14,.2,10,6),pmM);p.position.set(x,5,z);p.castShadow=true;poleGroup.add(p);
  const arm=new THREE.Mesh(new THREE.BoxGeometry(2.4,.12,.12),pmM);arm.position.set(x,9.4,z);poleGroup.add(arm);
  const tr=new THREE.Mesh(new THREE.CylinderGeometry(.35,.35,.9,8),pmM);tr.position.set(x+.5,8.2,z+.3);poleGroup.add(tr)}
 for(let i=0;i<inside.length-1;i++){const a=inside[i],b=inside[i+1];for(const o of [-1,0,1]){const pts=[];for(let k=0;k<=12;k++){const t=k/12;pts.push(new THREE.Vector3(a[0]+(b[0]-a[0])*t+o*1.1,9.4-Math.sin(Math.PI*t)*.9,a[1]+(b[1]-a[1])*t))}
  poleGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),wireM))}}
})();

/* ---------- 路徑工具 ---------- */
function mkPath(pts,loop){const P=pts.map(p=>new THREE.Vector2(p[0],p[1]));if(loop)P.push(P[0].clone());const cum=[0];for(let i=1;i<P.length;i++)cum.push(cum[i-1]+P[i].distanceTo(P[i-1]));return{P,cum,len:cum[cum.length-1],loop}}
function pathAt(path,s,o){const L=path.len;if(path.loop)s=((s%L)+L)%L;else s=Math.max(0,Math.min(L,s));
 let lo=1,hi=path.cum.length-1;while(lo<hi){const mid=(lo+hi)>>1;if(path.cum[mid]<s)lo=mid+1;else hi=mid}
 const i=lo,a=path.P[i-1],b=path.P[i];const seg=(path.cum[i]-path.cum[i-1])||1;const t=(s-path.cum[i-1])/seg;
 o.x=a.x+(b.x-a.x)*t;o.z=a.y+(b.y-a.y)*t;o.dx=(b.x-a.x)/seg;o.dz=(b.y-a.y)/seg;return o}
function clipPath(pts,m=3){const P=mkPath(pts,false),o={};let best=[],run=[];
 for(let s=0;s<=P.len;s+=2){pathAt(P,s,o);const ins=o.x>BX0+m&&o.x<BX0+W-m&&o.z>BZ0+m&&o.z<BZ0+D-m;if(ins)run.push([o.x,o.z]);else{if(run.length>best.length)best=run;run=[]}}
 if(run.length>best.length)best=run;return best}
function offsetPts(pts,off){return pts.map((p,i)=>{const a=pts[Math.max(0,i-1)],b=pts[Math.min(pts.length-1,i+1)];const dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz)||1;return[p[0]-dz/l*off,p[1]+dx/l*off]})}
const lifeR=rng(314);const _o={};
const PS=1.5; // 人物放大倍率（微縮模型上看得見）

/* ---------- 車流（右側通行；時間加速） ---------- */
const RD=DATA.ROADS.map(r=>({id:r.id,w:r.w,pts:clipPath(r.pts)})).filter(r=>r.pts.length>8);
const vehGroup=new THREE.Group();scene.add(vehGroup);
const carCols=[0xf4f4f2,0x15171c,0x9aa3ad,0xa3141c,0x23447f,0xd9d4c8,0x4b5866,0xe8e8e6,0x6d7378,0xf4f4f2,0x15171c];
const paint=c=>new THREE.MeshPhysicalMaterial({color:c,roughness:.3,metalness:.5,clearcoat:1,clearcoatRoughness:.08,envMap:ENV,envMapIntensity:1});
const carMats=carCols.map(paint),taxiM=paint(0xf2c230),truckM=paint(0x2c62b8);
const glassM=new THREE.MeshPhysicalMaterial({color:0x0c1219,roughness:.04,metalness:.9,envMap:ENV,envMapIntensity:1.4});
const tireM=new THREE.MeshStandardMaterial({color:0x1a1a1c,roughness:.9});
const trimM=new THREE.MeshStandardMaterial({color:0x24262a,roughness:.6});
const chromeM=new THREE.MeshStandardMaterial({color:0xd5d9de,roughness:.22,metalness:1,envMap:ENV});
const bedM=new THREE.MeshStandardMaterial({color:0x9aa1a8,roughness:.5,metalness:.6,envMap:ENV});
const headM=new THREE.MeshStandardMaterial({color:0xfdf6e3,emissive:0xfff0cc,emissiveIntensity:.7,roughness:.2});
const tailM=new THREE.MeshStandardMaterial({color:0xa81616,emissive:0x900c0c,emissiveIntensity:.9,roughness:.3});
const skinM=new THREE.MeshStandardMaterial({color:0xe2b48c,roughness:.7});
const helmetMs=[0xd23b2e,0xf2f2f0,0x2c4f8f,0x1d1f24,0xf0b429,0x8fb8d8].map(c=>new THREE.MeshPhysicalMaterial({color:c,roughness:.25,clearcoat:1,envMap:ENV}));
const clothMs=[0x3a4a5c,0x8a2f2a,0xd8d2c4,0x2f5f3a,0x1f2a44,0xe9e4da,0x6b5a7a].map(c=>new THREE.MeshStandardMaterial({color:c,roughness:.85}));
const pantsMs=[0x1f2a44,0x2a2f3a,0x4a5a6e,0x5a5048].map(c=>new THREE.MeshStandardMaterial({color:c,roughness:.85}));
// 側面輪廓擠出：pts 為 [前後 z, 高 y]，車頭朝 +z
function sideX(pts,width,bev=.06){const sh=new THREE.Shape();pts.forEach(([z,y],i)=>i?sh.lineTo(z,y):sh.moveTo(z,y));sh.closePath();
 const g=new THREE.ExtrudeGeometry(sh,{depth:Math.max(.01,width-2*bev),bevelEnabled:true,bevelThickness:bev,bevelSize:bev,bevelSegments:2,curveSegments:3});
 g.translate(0,0,-(width-2*bev)/2);g.rotateY(-Math.PI/2);return g}
const bx=(w,h,d,x,y,z)=>new THREE.BoxGeometry(w,h,d).translate(x,y,z);
const cyl=(r,w,x,y,z,seg=14)=>new THREE.CylinderGeometry(r,r,w,seg).rotateZ(Math.PI/2).translate(x,y,z);
function mergeBy(list){const by={};for(const [k,g] of list)(by[k]=by[k]||[]).push(g.index?g.toNonIndexed():g);const o={};for(const k in by)o[k]=mergeGeometries(by[k]);return o}
function wheels(list,r,x,zs,y=r){for(const z of zs)for(const sx of [-1,1]){list.push(['tire',cyl(r,.24,sx*x,y,z)]);list.push(['chrome',cyl(r*.58,.26,sx*(x+.01),y,z,10)]);list.push(['trim',cyl(r*.2,.27,sx*(x+.02),y,z,8)])}}
const CAR_T={
 sedan:(()=>{const L=[];L.push(['paint',sideX([[-2.2,.3],[2.15,.3],[2.25,.52],[2.18,.76],[1.1,.92],[-1.65,.96],[-2.18,.86],[-2.27,.55]],1.76)]);
  L.push(['glass',sideX([[1.08,.9],[.35,1.36],[-.95,1.37],[-1.68,.94]],1.5,.05)]);L.push(['paint',sideX([[.33,1.34],[-.93,1.35],[-.92,1.41],[.31,1.4]],1.5,.03)]);
  L.push(['trim',bx(1.74,.16,.14,0,.36,2.22)],['trim',bx(1.74,.16,.14,0,.38,-2.27)],['head',bx(.36,.12,.06,-.58,.66,2.24)],['head',bx(.36,.12,.06,.58,.66,2.24)],['tail',bx(.42,.12,.06,-.6,.72,-2.3)],['tail',bx(.42,.12,.06,.6,.72,-2.3)],['trim',bx(.7,.1,.05,0,.5,2.27)],['paint',bx(.08,.08,.18,-.92,1.0,.9)],['paint',bx(.08,.08,.18,.92,1.0,.9)]);
  wheels(L,.34,.8,[1.35,-1.35]);return mergeBy(L)})(),
 suv:(()=>{const L=[];L.push(['paint',sideX([[-2.2,.42],[2.15,.42],[2.25,.66],[2.18,.96],[1.3,1.08],[-2.15,1.12],[-2.27,.66]],1.84)]);
  L.push(['glass',sideX([[1.26,1.05],[.6,1.66],[-2.02,1.7],[-2.12,1.1]],1.6,.05)]);L.push(['paint',sideX([[.58,1.64],[-2.0,1.68],[-1.98,1.77],[.55,1.74]],1.62,.03)]);
  L.push(['trim',bx(1.82,.2,.14,0,.48,2.22)],['trim',bx(1.82,.2,.14,0,.5,-2.27)],['head',bx(.38,.13,.06,-.6,.86,2.24)],['head',bx(.38,.13,.06,.6,.86,2.24)],['tail',bx(.14,.4,.06,-.82,1.0,-2.3)],['tail',bx(.14,.4,.06,.82,1.0,-2.3)],['chrome',bx(1.5,.05,.05,0,1.8,-.7)]);
  wheels(L,.4,.84,[1.38,-1.38]);return mergeBy(L)})(),
 truck:(()=>{const L=[];L.push(['body',sideX([[.95,.45],[2.18,.45],[2.24,.68],[2.16,1.1],[.95,1.12]],1.66)]);
  L.push(['glass',sideX([[2.14,1.08],[1.98,1.72],[.97,1.74],[.97,1.08]],1.6,.05)]);L.push(['body',sideX([[1.96,1.7],[.96,1.72],[.96,1.86],[1.9,1.84]],1.66,.04)]);
  L.push(['trim',bx(1.6,.2,.12,0,.5,2.24)],['head',bx(.3,.16,.06,-.58,.8,2.25)],['head',bx(.3,.16,.06,.58,.8,2.25)],['trim',bx(1.2,.25,3.5,0,.55,-.8)],
   ['bed',bx(1.72,.1,3.2,0,.8,-.8)],['bed',bx(.05,.36,3.2,-.84,1.03,-.8)],['bed',bx(.05,.36,3.2,.84,1.03,-.8)],['bed',bx(1.72,.36,.05,0,1.03,-2.38)],['bed',bx(1.72,.7,.06,0,1.2,.78)],['tail',bx(.2,.12,.06,-.7,.62,-2.42)],['tail',bx(.2,.12,.06,.7,.62,-2.42)]);
  wheels(L,.33,.78,[1.5,-1.55]);return mergeBy(L)})()
};
function makeCar(){const g=new THREE.Group();const r=lifeR();const type=r<.55?'sedan':r<.85?'suv':'truck';const P=CAR_T[type];
 const taxi=type==='sedan'&&lifeR()<.14;const pm=taxi?taxiM:carMats[(lifeR()*carMats.length)|0];
 const M={paint:pm,body:truckM,glass:glassM,tire:tireM,trim:trimM,chrome:chromeM,bed:bedM,head:headM,tail:tailM};
 for(const k in P){const m=new THREE.Mesh(P[k],M[k]);if(k==='paint'||k==='body'||k==='bed')m.castShadow=true;g.add(m)}
 if(taxi){const t=new THREE.Mesh(new THREE.BoxGeometry(.7,.2,.3),new THREE.MeshStandardMaterial({color:0xf6f1e0,emissive:0x504020,roughness:.4}));t.position.set(0,1.52,-.3);g.add(t)}
 g.scale.setScalar(1.15);return g}
const SC_T=mergeBy((()=>{const L=[];
 L.push(['paint',sideX([[-.86,.34],[.02,.34],[.1,.52],[-.12,.8],[-.78,.82],[-.92,.6]],.42,.05)]);
 L.push(['paint',sideX([[.3,.28],[.52,.28],[.6,.88],[.5,1.06],[.42,1.06],[.36,.5]],.5,.05)]);
 L.push(['trim',bx(.36,.07,.5,0,.31,.12)],['trim',bx(.34,.1,.62,0,.87,-.4)],['trim',bx(.64,.045,.045,0,1.12,.47)],['chrome',bx(.05,.32,.05,0,.95,.5)],
  ['head',bx(.16,.1,.05,0,.86,.62)],['tail',bx(.18,.07,.05,0,.66,-.94)]);
 for(const z of [.62,-.62]){L.push(['tire',cyl(.25,.11,0,.25,z)],['chrome',cyl(.13,.12,0,.25,z,10)])}return L})());
const RIDER=(()=>{const L=[];
 const torso=new THREE.CylinderGeometry(.17,.2,.56,10).scale(1,1,.72).rotateX(.22).translate(0,1.24,-.34);L.push(['shirt',torso]);
 for(const sx of [-1,1]){const a=new THREE.Vector3(sx*.2,1.42,-.26),b=new THREE.Vector3(sx*.28,1.13,.45);const d=b.clone().sub(a);const arm=new THREE.CylinderGeometry(.05,.045,d.length(),7);
  arm.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize()));arm.translate((a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2);L.push(['shirt',arm]);
  L.push(['skin',new THREE.SphereGeometry(.05,8,6).translate(b.x,b.y,b.z)]);
  L.push(['pants',bx(.15,.15,.5,sx*.12,.97,-.12)],['pants',bx(.13,.56,.13,sx*.13,.66,.14)],['trim',bx(.12,.08,.24,sx*.13,.38,.2)])}
 L.push(['skin',new THREE.CylinderGeometry(.05,.05,.1,8).translate(0,1.55,-.24)],['helmet',new THREE.SphereGeometry(.16,14,10).scale(1,1,1.1).translate(0,1.7,-.22)],['trim',bx(.26,.09,.04,0,1.67,-.05)]);
 return mergeBy(L)})();
function makeScooter(){const g=new THREE.Group();const pm=carMats[(lifeR()*carMats.length)|0];
 const M={paint:pm,trim:trimM,chrome:chromeM,head:headM,tail:tailM,tire:tireM,shirt:clothMs[(lifeR()*clothMs.length)|0],pants:pantsMs[(lifeR()*pantsMs.length)|0],skin:skinM,helmet:helmetMs[(lifeR()*helmetMs.length)|0]};
 for(const P of [SC_T,RIDER])for(const k in P){const m=new THREE.Mesh(P[k],M[k]);if(k==='paint'||k==='shirt')m.castShadow=true;g.add(m)}
 g.scale.setScalar(PS*.92);return g}
const vehicles=[];
for(const r of RD){
 for(const dir of [1,-1]){
  const base=dir>0?r.pts:[...r.pts].reverse();
  const carP=mkPath(offsetPts(base,Math.min(r.w/4,4.2)),false),scP=mkPath(offsetPts(base,Math.max(1.6,r.w/2-1.6)),false);
  const nCar=Math.max(1,Math.round(carP.len/(r.w>12?42:70))),nSc=Math.max(1,Math.round(scP.len/(r.w>12?30:55)));
  for(let i=0;i<nCar;i++){const g=makeCar();vehGroup.add(g);vehicles.push({g,road:r.id,path:carP,s:(i+lifeR()*.5)*carP.len/nCar,v:8+lifeR()*3})}
  for(let i=0;i<nSc;i++){const g=makeScooter();vehGroup.add(g);vehicles.push({g,road:r.id,path:scP,s:(i+lifeR()*.6)*scP.len/nSc,v:7+lifeR()*3,bob:lifeR()*6})}
 }
}

/* ---------- 人物（學生、路人；同一組 InstancedMesh） ---------- */
const walkers=[];
const M=(px,py)=>[(px-1970)*.2,(py-1065)*.2];
function stadiumPts(R,L,cx,cz){const p=[];for(let i=0;i<=24;i++){const a=-Math.PI/2+Math.PI*i/24;p.push([cx+L+Math.cos(a)*R,cz+Math.sin(a)*R])}for(let i=0;i<=24;i++){const a=Math.PI/2+Math.PI*i/24;p.push([cx-L+Math.cos(a)*R,cz+Math.sin(a)*R])}return p}
const CAMPUS_PATHS=[
 {pts:[[-9,99],[-14,84],[-3,62],[4,38],[5,10]],n:7},
 {pts:[[7,10],[50,10],[92,10]],n:6},
 {pts:[[10,42],[45,44],[60,42],[62,52]],n:5},
 {pts:[[-2,99],[40,99],[92,99]],n:6},
 {pts:[[-60,-96],[0,-96],[70,-96]],n:6},
 {pts:[[-64,12],[-30,35],[9,62]],n:6},
 {pts:[[-90,-10],[-70,0],[-45,8],[-8,4]],n:4},
 {pts:[[-20,-140],[0,-112],[30,-108],[60,-120]],n:5},
 {pts:[[96,-110],[96,-40],[96,40],[96,105]],n:5}
];
const uniformCols=[0xf6f5f0,0xf6f5f0,0x2f5fa8,0xf6f5f0,0x2d3a52,0xe8e2d0];
for(const cp of CAMPUS_PATHS){const P=mkPath(cp.pts,false);for(let i=0;i<cp.n;i++)walkers.push({path:P,s:lifeR()*P.len,v:(1.2+lifeR()*.6)*1.8,dir:lifeR()<.5?1:-1,col:uniformCols[(lifeR()*uniformCols.length)|0],ph:lifeR()*6,pong:true})}
const runP=mkPath(stadiumPts(38.5,49,0,-50),true);
for(let i=0;i<9;i++)walkers.push({path:runP,s:lifeR()*runP.len,v:4.6+lifeR()*1.6,dir:1,col:[0x2f5fa8,0xd23b2e,0xf6f5f0][i%3],ph:lifeR()*6,run:true});
// 校外人行道
const streetCols=[0x7a8796,0xc8b79a,0x3d4a5a,0xa8463a,0xe9e4da,0x4f6b4a,0xd6a14a];
for(const r of RD){for(const side of [1,-1]){const P=mkPath(offsetPts(r.pts,side*(r.w/2+1.4)),false);const n=Math.max(1,Math.round(P.len/45));for(let i=0;i<n;i++)walkers.push({path:P,s:lifeR()*P.len,v:(1.1+lifeR()*.5)*1.8,dir:lifeR()<.5?1:-1,col:streetCols[(lifeR()*streetCols.length)|0],ph:lifeR()*6,pong:true,road:r.id})}}
const NW=walkers.length;
const HUM=(()=>{ // 腳底 y=0、面向 +z、身高約 1.7 m
 const leg=mergeGeometries([new THREE.CylinderGeometry(.078,.058,.8,8).translate(0,-.4,0).toNonIndexed(),new THREE.BoxGeometry(.11,.07,.25).translate(0,-.825,.05).toNonIndexed()]);
 const arm=mergeGeometries([new THREE.CylinderGeometry(.05,.04,.6,7).translate(0,-.3,0).toNonIndexed(),new THREE.SphereGeometry(.048,8,6).translate(0,-.62,0).toNonIndexed()]);
 const torso=new THREE.LatheGeometry([[0,0],[.155,0],[.17,.08],[.16,.25],[.175,.42],[.2,.5],[.17,.56],[.06,.61],[0,.62]].map(([r,y])=>new THREE.Vector2(r,y)),14).scale(1,1,.66).translate(0,.84,0);
 const head=mergeGeometries([new THREE.CylinderGeometry(.045,.05,.12,8).translate(0,1.47,0).toNonIndexed(),new THREE.SphereGeometry(.105,16,12).scale(.9,1.1,1).translate(0,1.6,.01).toNonIndexed(),new THREE.SphereGeometry(.03,6,4).translate(0,1.59,.11).toNonIndexed()]);
 const hair=new THREE.SphereGeometry(.112,16,10,0,Math.PI*2,0,Math.PI*.56).scale(.96,1.06,1.04).translate(0,1.615,-.015);
 const bag=new THREE.BoxGeometry(.28,.34,.13).translate(0,1.12,-.17);
 return {leg,arm,torso,head,hair,bag}})();
const SKINS=[0xf1c9a5,0xe8b994,0xdcaa82,0xc99a72,0xf3d2b3],HAIRS=[0x17130f,0x221a14,0x2e2219,0x111111,0x3b2a1e],BAGS=[0x1f3b73,0x222222,0xa3262b,0x2f5f3a,0x5a4a8a,0x2a6f8f];
const IM=(geo,rough)=>{const m=new THREE.InstancedMesh(geo,new THREE.MeshStandardMaterial({color:0xffffff,roughness:rough}),NW);m.castShadow=true;scene.add(m);return m};
const hTorso=IM(HUM.torso,.8),hLegL=IM(HUM.leg,.8),hLegR=IM(HUM.leg,.8),hArmL=IM(HUM.arm,.6),hArmR=IM(HUM.arm,.6),hHead=IM(HUM.head,.6),hHair=IM(HUM.hair,.5),hBag=IM(HUM.bag,.7);
const HPARTS=[hTorso,hLegL,hLegR,hArmL,hArmR,hHead,hHair,hBag];
{const c=new THREE.Color();walkers.forEach((w,i)=>{const student=w.road==null;w.skin=SKINS[(lifeR()*SKINS.length)|0];
 const pants=w.run?0x1f2a44:student?0x1f2a44:[0x2a2f3a,0x3d4a5a,0x6b6258,0x1d1f24,0x4a5a6e][(lifeR()*5)|0];
 hTorso.setColorAt(i,c.set(w.col));hLegL.setColorAt(i,c.set(pants));hLegR.setColorAt(i,c);hArmL.setColorAt(i,c.set(w.skin));hArmR.setColorAt(i,c);hHead.setColorAt(i,c);
 hHair.setColorAt(i,c.set(HAIRS[(lifeR()*HAIRS.length)|0]));hBag.setColorAt(i,c.set(BAGS[(lifeR()*BAGS.length)|0]));w.bag=student&&!w.run&&lifeR()<.65});
 for(const m of HPARTS)m.instanceColor.needsUpdate=true}
const _lm=new THREE.Matrix4(),_lr=new THREE.Matrix4(),_lean=new THREE.Matrix4(),_zero=new THREE.Matrix4().makeScale(0,0,0);
function limb(im,i,x,y,a,rz){_lm.makeTranslation(x,y,0);_lr.makeRotationX(a);_lm.multiply(_lr);_lr.makeRotationZ(rz);_lm.multiply(_lr);_lm.premultiply(_m);im.setMatrixAt(i,_lm)}
const _m=new THREE.Matrix4(),_q=new THREE.Quaternion(),_s=new THREE.Vector3(),_p=new THREE.Vector3(),_up=new THREE.Vector3(0,1,0);

/* ---------- 神社路鳥居（舊北斗神社參道） ---------- */
const torii=new THREE.Group();scene.add(torii);
{const shu=new THREE.MeshStandardMaterial({color:0xd2452c,roughness:.55}),blk=new THREE.MeshStandardMaterial({color:0x1d1d1f,roughness:.5});
 const X=110.4,Z=120,span=8.5;
 for(const sx of [-1,1]){const p=new THREE.Mesh(new THREE.CylinderGeometry(.42,.5,8.4,14),shu);p.position.set(X+sx*span,4.2,Z);p.castShadow=true;torii.add(p);
  const ft=new THREE.Mesh(new THREE.CylinderGeometry(.62,.62,.7,14),blk);ft.position.set(X+sx*span,.35,Z);torii.add(ft)}
 const nuki=new THREE.Mesh(new THREE.BoxGeometry(span*2+2.2,.5,.42),shu);nuki.position.set(X,6.5,Z);nuki.castShadow=true;torii.add(nuki);
 const shim=new THREE.Mesh(new THREE.BoxGeometry(span*2+3.6,.55,.7),shu);shim.position.set(X,8.25,Z);torii.add(shim);
 const kasG=new THREE.BoxGeometry(span*2+5.4,.6,1.0,24,1,1);const pa=kasG.attributes.position;for(let i=0;i<pa.count;i++){const x=pa.getX(i)/(span+2.7);pa.setY(i,pa.getY(i)+x*x*x*x*.75)}kasG.computeVertexNormals();
 const kas=new THREE.Mesh(kasG,blk);kas.position.set(X,8.85,Z);kas.castShadow=true;torii.add(kas);
 const gak=new THREE.Mesh(new THREE.BoxGeometry(1.1,1.6,.3),blk);gak.position.set(X,7.35,Z+.25);torii.add(gak);
 const el=document.createElement('div');el.className='lbl torii';el.dataset.zh='⛩ 神社路（舊北斗神社參道）';el.dataset.en='⛩ Shrine Road (old approach to Beidou Shrine)';el.textContent=T_(el.dataset.zh,el.dataset.en);el.dataset.pri=1e6;const lo=new CSS2DObject(el);lo.position.set(X,12,Z);torii.add(lo)}

/* ---------- 北斗奠安宮 媽祖遶境 ---------- */
const procRoute=(()=>{const se=DATA.ROADS.find(r=>r.id==='se').pts;const pts=[];for(const p of se){if(p[0]<110.4)pts.push(p)}pts.push([110.4,148]);pts.push([110.4,-175]);return mkPath(clipPath(pts),false)})();
const proc={active:false,s:0,next:25,group:new THREE.Group(),members:[],tail:0,v:3.4};
scene.add(proc.group);proc.group.visible=false;
const rigs=[],hmc=new Map();
const hm=(c,r)=>{const k=c+'_'+r;if(!hmc.has(k))hmc.set(k,new THREE.MeshStandardMaterial({color:c,roughness:r}));return hmc.get(k)};
function person(shirt,pants=0x2a2f3a,head=0x2a2420){const g=new THREE.Group();const sk=SKINS[(lifeR()*SKINS.length)|0];
 const mk=(geo,c,r=.75)=>{const m=new THREE.Mesh(geo,hm(c,r));m.castShadow=true;return m};
 g.add(mk(HUM.torso,shirt),mk(HUM.head,sk,.6),mk(HUM.hair,head,.5));
 const limbs=[];for(const [x,y,geo,c,s,rz] of [[-.095,.86,HUM.leg,pants,1,0],[.095,.86,HUM.leg,pants,-1,0],[-.215,1.37,HUM.arm,sk,-.8,-.07],[.215,1.37,HUM.arm,sk,.8,.07]]){
  const p=new THREE.Group();p.position.set(x,y,0);const m=mk(geo,c);m.rotation.z=rz;p.add(m);g.add(p);limbs.push([p,s])}
 g.userData.limbs=limbs;g.userData.ph=lifeR()*6;rigs.push(g);return g}
function flagTex(txt,bg,fg){return canvasTex('flag_'+txt+bg,128,256,(g,w,h)=>{g.fillStyle=bg;g.fillRect(0,0,w,h);g.strokeStyle=fg;g.lineWidth=10;g.strokeRect(5,5,w-10,h-10);g.fillStyle=fg;g.font='900 46px "PingFang TC","Microsoft JhengHei",sans-serif';g.textAlign='center';g.textBaseline='middle';[...txt].forEach((ch,i)=>g.fillText(ch,w/2,40+i*(h-80)/Math.max(1,txt.length-1)))})}
function flagBearer(txt,bg,fg,tall=5.2){const g=person(0xf2c230,0x8e2f27);const pole=new THREE.Mesh(new THREE.CylinderGeometry(.05,.05,tall,6),new THREE.MeshStandardMaterial({color:0x7a5a3a}));pole.position.set(.35,tall/2+.4,0);g.add(pole);
 const f=new THREE.Mesh(new THREE.PlaneGeometry(.9,1.9),new THREE.MeshStandardMaterial({map:flagTex(txt,bg,fg),side:THREE.DoubleSide,roughness:.8}));f.position.set(.82,tall-.6,0);f.rotation.y=Math.PI/2;g.add(f);g.userData.flag=f;return g}
function giant(face,robe){const g=new THREE.Group();const r=new THREE.Mesh(new THREE.CylinderGeometry(.55,1.0,2.7,10),new THREE.MeshStandardMaterial({color:robe,roughness:.7}));r.position.y=1.65;r.castShadow=true;g.add(r);
 const sh=new THREE.Mesh(new THREE.BoxGeometry(2.0,.5,.8),new THREE.MeshStandardMaterial({color:0xd7a733,roughness:.4,metalness:.4}));sh.position.y=2.95;g.add(sh);
 const hd=new THREE.Mesh(new THREE.SphereGeometry(.58,14,10),new THREE.MeshStandardMaterial({color:face,roughness:.5}));hd.position.y=3.55;hd.scale.set(1,1.15,1);hd.castShadow=true;g.add(hd);
 const hat=new THREE.Mesh(new THREE.CylinderGeometry(.35,.55,.5,8),new THREE.MeshStandardMaterial({color:0xd7a733,metalness:.5,roughness:.35}));hat.position.y=4.2;g.add(hat);
 for(const sx of [-1,1]){const a=new THREE.Mesh(new THREE.CylinderGeometry(.13,.16,1.6,6),new THREE.MeshStandardMaterial({color:robe}));a.position.set(sx*1.0,2.1,0);a.rotation.z=sx*.35;g.add(a)}
 g.userData.giant=true;return g}
function parasol(){const g=person(0xf2c230,0x8e2f27);const pole=new THREE.Mesh(new THREE.CylinderGeometry(.05,.05,3.6,6),new THREE.MeshStandardMaterial({color:0x7a5a3a}));pole.position.y=2.2;g.add(pole);
 const u=new THREE.Group();u.position.y=3.9;g.add(u);
 const l1=new THREE.Mesh(new THREE.CylinderGeometry(1.1,1.25,.8,16),new THREE.MeshStandardMaterial({color:0xc8302a,roughness:.6}));u.add(l1);
 const l2=new THREE.Mesh(new THREE.CylinderGeometry(1.15,1.15,.25,16),new THREE.MeshStandardMaterial({color:0xe8b530,metalness:.4,roughness:.4}));l2.position.y=-.45;u.add(l2);
 const top=new THREE.Mesh(new THREE.SphereGeometry(.18,8,6),l2.material);top.position.y=.55;u.add(top);g.userData.spin=u;return g}
function palanquin(){const g=new THREE.Group();const red=new THREE.MeshStandardMaterial({color:0xb3262b,roughness:.45}),gold=new THREE.MeshStandardMaterial({color:0xe2b33c,roughness:.3,metalness:.6});
 const body=new THREE.Mesh(new THREE.BoxGeometry(1.4,1.7,1.5),red);body.position.y=2.15;body.castShadow=true;g.add(body);
 const roof=new THREE.Mesh(new THREE.ConeGeometry(1.25,1.0,4),gold);roof.rotation.y=Math.PI/4;roof.position.y=3.5;roof.castShadow=true;g.add(roof);
 const fin=new THREE.Mesh(new THREE.SphereGeometry(.2,8,6),gold);fin.position.y=4.1;g.add(fin);
 const win=new THREE.Mesh(new THREE.PlaneGeometry(.8,.9),new THREE.MeshStandardMaterial({color:0xffd27a,emissive:0x6a3a08,emissiveIntensity:.6}));win.position.set(0,2.25,.76);g.add(win);
 for(const sx of [-.55,.55]){const p=new THREE.Mesh(new THREE.BoxGeometry(.12,.12,5.4),gold);p.position.set(sx,1.45,0);g.add(p)}
 for(const [x,z] of [[-.55,2.3],[.55,2.3],[-.55,-2.3],[.55,-2.3]]){const b=person(0xf2c230,0x8e2f27);b.position.set(x,0,z);g.add(b)}
 const el=document.createElement('div');el.className='lbl proc';el.dataset.zh='北斗奠安宮 天上聖母';el.dataset.en='Mazu · Beidou Dian\'an Temple';el.textContent=T_(el.dataset.zh,el.dataset.en);el.dataset.pri=2e6;const lo=new CSS2DObject(el);lo.position.set(0,6.2,0);lo.visible=false;g.add(lo);
 g.userData.bob=true;g.userData.label=lo;return g}
{let off=0;const add=(g,gap,lateral=0)=>{off+=gap;g.scale.multiplyScalar(PS*.85);proc.group.add(g);proc.members.push({g,off,lat:lateral,ph:lifeR()*6})};
 const lead=person(0x3a3a3a,0x3a3a3a);const um=new THREE.Mesh(new THREE.ConeGeometry(.6,.4,10),new THREE.MeshStandardMaterial({color:0x1d1d1f}));um.position.y=1.86;lead.add(um);add(lead,0);
 add(flagBearer('天上聖母','#c8302a','#f2c230'),3.2,-1.2);add(flagBearer('北斗奠安宮','#f2c230','#b3262b'),0,1.2);
 for(let i=0;i<4;i++){add(flagBearer('令','#2c4f8f','#f2c230',3.6),2.4,-1.4);add(flagBearer('令','#2f6f3a','#f2c230',3.6),0,1.4)}
 const drum=new THREE.Group();const dm=new THREE.Mesh(new THREE.CylinderGeometry(.7,.7,.7,14),new THREE.MeshStandardMaterial({color:0xb3262b}));dm.rotation.z=Math.PI/2;dm.position.y=1.4;drum.add(dm);const cart=new THREE.Mesh(new THREE.BoxGeometry(1.4,.5,1.8),new THREE.MeshStandardMaterial({color:0x6b4a2e}));cart.position.y=.6;drum.add(cart);add(drum,3.4);
 add(giant(0x2f8a4a,0x2a5a3a),4.4,-1.5);add(giant(0xc8302a,0x6a2a2a),0,1.5);
 add(parasol(),4.6);add(palanquin(),4.4);
 for(let i=0;i<14;i++)add(person(i%3?0xf2c230:0xf6f5f0,0x2a2f3a),i%2?0:2.0,(i%2?1:-1)*1.1);
 proc.tail=off}
// 鞭炮火花
const sparkN=160;const sparkGeo=new THREE.BufferGeometry();const sparkPos=new Float32Array(sparkN*3),sparkVel=new Float32Array(sparkN*3),sparkLife=new Float32Array(sparkN);
sparkGeo.setAttribute('position',new THREE.BufferAttribute(sparkPos,3));
const sparks=new THREE.Points(sparkGeo,new THREE.PointsMaterial({color:0xffb04a,size:.9,transparent:true,opacity:.95,blending:THREE.AdditiveBlending,depthWrite:false}));sparks.frustumCulled=false;scene.add(sparks);
const smokeTex=canvasTex('smoke',64,64,(g)=>{const gr=g.createRadialGradient(32,32,2,32,32,32);gr.addColorStop(0,'rgba(235,235,235,.75)');gr.addColorStop(1,'rgba(235,235,235,0)');g.fillStyle=gr;g.fillRect(0,0,64,64)});
const smokes=[];for(let i=0;i<14;i++){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:smokeTex,transparent:true,depthWrite:false,opacity:0}));sp.scale.set(5,5,1);scene.add(sp);smokes.push({sp,life:0})}
let burstT=0;
function burst(x,z){let k=0;for(let i=0;i<sparkN&&k<60;i++){if(sparkLife[i]<=0){sparkPos[i*3]=x+(lifeR()-.5)*2;sparkPos[i*3+1]=.6;sparkPos[i*3+2]=z+(lifeR()-.5)*2;sparkVel[i*3]=(lifeR()-.5)*6;sparkVel[i*3+1]=2+lifeR()*6;sparkVel[i*3+2]=(lifeR()-.5)*6;sparkLife[i]=.5+lifeR()*.7;k++}}
 for(const s of smokes){if(s.life<=0){s.sp.position.set(x+(lifeR()-.5)*3,1.5,z+(lifeR()-.5)*3);s.life=2.4;break}}}
function startProc(){if(proc.active)return;proc.active=true;proc.s=0;proc.group.visible=true;document.getElementById('notice').hidden=false;document.getElementById('tProc').setAttribute('aria-pressed','true')}
function endProc(t){proc.active=false;proc.group.visible=false;for(const mb of proc.members)if(mb.g.userData.label)mb.g.userData.label.visible=false;proc.next=t+80+Math.random()*100;document.getElementById('notice').hidden=true;document.getElementById('tProc').setAttribute('aria-pressed','false')}
document.getElementById('tProc').onclick=()=>{proc.active?endProc(clock.elapsedTime):startProc()};

/* ---------- 每幀更新 ---------- */
function updateLife(dt,t){
 if(!proc.active&&t>proc.next)startProc();
 // 車
 for(const v of vehicles){const hide=proc.active&&(v.road==='se'||v.road==='shrine');v.g.visible=!hide;if(hide)continue;
  v.s+=v.v*dt;if(v.s>v.path.len)v.s-=v.path.len;pathAt(v.path,v.s,_o);v.g.position.set(_o.x,v.bob!=null?Math.abs(Math.sin(t*9+v.bob))*.03:0,_o.z);v.g.rotation.y=Math.atan2(_o.dx,_o.dz)}
 // 人
 for(let i=0;i<NW;i++){const w=walkers[i];w.s+=w.v*w.dir*dt;
  if(w.pong){if(w.s>w.path.len){w.s=w.path.len;w.dir=-1}else if(w.s<0){w.s=0;w.dir=1}}
  pathAt(w.path,w.s,_o);const yaw=Math.atan2(_o.dx*w.dir,_o.dz*w.dir);const f=w.run?10:6.5;const ph=t*f+w.ph;const bob=Math.abs(Math.sin(ph))*(w.run?.07:.03)*PS;
  const lat=w.run?((i%3)-1)*1.25:0;_p.set(_o.x-_o.dz*lat,bob,_o.z+_o.dx*lat);_q.setFromAxisAngle(_up,yaw);_s.setScalar(PS);_m.compose(_p,_q,_s);
  if(w.run){_lean.makeRotationX(.2);_m.multiply(_lean)}
  const sw=Math.sin(ph)*(w.run?.8:.42);
  hTorso.setMatrixAt(i,_m);hHead.setMatrixAt(i,_m);hHair.setMatrixAt(i,_m);hBag.setMatrixAt(i,w.bag?_m:_zero);
  limb(hLegL,i,-.095,.86,sw,0);limb(hLegR,i,.095,.86,-sw,0);limb(hArmL,i,-.215,1.37,-sw*.85,-.07);limb(hArmR,i,.215,1.37,sw*.85,.07)}
 for(const m of HPARTS)m.instanceMatrix.needsUpdate=true;
 // 遶境
 if(proc.active){proc.s+=proc.v*dt;
  for(const mb of proc.members){const s=proc.s-mb.off;const g=mb.g;const vis=s>=0&&s<=procRoute.len;g.visible=vis;if(g.userData.label)g.userData.label.visible=vis;if(!vis)continue;pathAt(procRoute,s,_o);
   g.position.set(_o.x-_o.dz*mb.lat,0,_o.z+_o.dx*mb.lat);g.rotation.y=Math.atan2(_o.dx,_o.dz);
   if(g.userData.giant){g.rotation.z=Math.sin(t*2.2+mb.ph)*.08;g.position.y=Math.abs(Math.sin(t*2.2+mb.ph))*.25}
   else if(g.userData.bob){g.position.y=Math.abs(Math.sin(t*3))*.15;g.rotation.z=Math.sin(t*1.5)*.04}
   else g.position.y=Math.abs(Math.sin(t*7+mb.ph))*.1;
   if(g.userData.spin)g.userData.spin.rotation.y+=dt*2.5}
  for(const r of rigs){const a=Math.sin(t*6+r.userData.ph)*.38;for(const [p,k] of r.userData.limbs)p.rotation.x=a*k}
  burstT-=dt;if(burstT<=0&&proc.s<procRoute.len){burstT=1.6+Math.random()*1.4;pathAt(procRoute,proc.s+6,_o);burst(_o.x,_o.z)}
  if(proc.s-proc.tail>procRoute.len)endProc(t)}
 let any=false;for(let i=0;i<sparkN;i++){if(sparkLife[i]>0){any=true;sparkLife[i]-=dt;sparkVel[i*3+1]-=9.8*dt;sparkPos[i*3]+=sparkVel[i*3]*dt;sparkPos[i*3+1]=Math.max(.1,sparkPos[i*3+1]+sparkVel[i*3+1]*dt);sparkPos[i*3+2]+=sparkVel[i*3+2]*dt;if(sparkLife[i]<=0)sparkPos[i*3+1]=-50}}
 if(any)sparkGeo.attributes.position.needsUpdate=true;
 for(const s of smokes){if(s.life>0){s.life-=dt;s.sp.position.y+=dt*1.6;const k=1-s.life/2.4;s.sp.scale.setScalar(4+k*9);s.sp.material.opacity=Math.max(0,.55*(1-k))}else s.sp.material.opacity=0}
}

/* ---------- 天空、雲、太陽、光塵 ---------- */
const skyU={top:{value:new THREE.Color()},hor:{value:new THREE.Color()},warm:{value:new THREE.Color()},sunDir:{value:new THREE.Vector3(0,1,0)},sunGlow:{value:0}};
const sky=new THREE.Mesh(new THREE.SphereGeometry(2800,32,16),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:skyU,
 vertexShader:`varying vec3 vW;void main(){vW=normalize((modelMatrix*vec4(position,1.)).xyz);gl_Position=projectionMatrix*viewMatrix*modelMatrix*vec4(position,1.);}`,
 fragmentShader:`uniform vec3 top,hor,warm,sunDir;uniform float sunGlow;varying vec3 vW;
 void main(){float h=clamp(vW.y,-.2,1.);vec3 c=mix(hor,top,pow(max(h,0.),.38));
  float sd=max(dot(normalize(vW),normalize(sunDir)),0.);c=mix(c,warm,(pow(sd,10.)*.85+pow(1.-max(h,0.),8.)*.3*pow(sd,.6))*sunGlow);
  c+=vec3(1.,.85,.6)*pow(sd,180.)*2.5*sunGlow;c=mix(c,hor*.92,smoothstep(0.,-.2,vW.y));gl_FragColor=vec4(c,1.);}`}));
scene.add(sky);
function cloudTexture(seed){const c=document.createElement('canvas');c.width=c.height=256;const g=c.getContext('2d');const r=rng(seed);
 for(let i=0;i<26;i++){const x=40+r()*176,y=90+r()*110-(i<8?40:0),rad=24+r()*48;const gr=g.createRadialGradient(x,y-rad*.3,rad*.1,x,y,rad);
  gr.addColorStop(0,'rgba(255,255,255,1)');gr.addColorStop(.55,'rgba(250,246,248,.85)');gr.addColorStop(1,'rgba(220,226,245,0)');g.fillStyle=gr;g.beginPath();g.arc(x,y,rad,0,7);g.fill()}
 g.globalCompositeOperation='source-atop';const sh=g.createLinearGradient(0,60,0,256);sh.addColorStop(0,'rgba(255,240,220,0)');sh.addColorStop(.6,'rgba(150,165,215,.35)');sh.addColorStop(1,'rgba(110,120,190,.6)');g.fillStyle=sh;g.fillRect(0,0,256,256);
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t}
const clouds=new THREE.Group();scene.add(clouds);
{const r=rng(77);const texs=[cloudTexture(1),cloudTexture(2),cloudTexture(3),cloudTexture(4)];
 for(let i=0;i<30;i++){const a=r()*Math.PI*2,d=1500+r()*800;const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:texs[i%4],transparent:true,depthWrite:false,fog:false}));
  const s=280+r()*420;sp.scale.set(s*1.3,s*.85,1);sp.position.set(Math.cos(a)*d,s*.3+r()*180,Math.sin(a)*d);sp.userData.drift=(r()-.5)*.02;clouds.add(sp)}}
const sunSprite=new THREE.Sprite(new THREE.SpriteMaterial({map:(()=>{const c=document.createElement('canvas');c.width=c.height=128;const g=c.getContext('2d');const gr=g.createRadialGradient(64,64,0,64,64,64);gr.addColorStop(0,'rgba(255,255,240,1)');gr.addColorStop(.18,'rgba(255,240,200,.9)');gr.addColorStop(.45,'rgba(255,200,140,.25)');gr.addColorStop(1,'rgba(255,180,120,0)');g.fillStyle=gr;g.fillRect(0,0,128,128);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t})(),transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,fog:false}));
sunSprite.scale.set(380,380,1);scene.add(sunSprite);
const moteN=520;const moteGeo=new THREE.BufferGeometry();{const r=rng(5);const a=new Float32Array(moteN*3);for(let i=0;i<moteN;i++){a[i*3]=(r()-.5)*W;a[i*3+1]=2+r()*50;a[i*3+2]=(r()-.5)*D}moteGeo.setAttribute('position',new THREE.BufferAttribute(a,3))}
const motes=new THREE.Points(moteGeo,new THREE.PointsMaterial({color:0xffe2b0,size:.5,transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false}));scene.add(motes);

/* ---------- 光源 ---------- */
const hemi=new THREE.HemisphereLight(0xffffff,0x888888,1);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);
const scm=sun.shadow.camera;scm.left=-220;scm.right=220;scm.top=220;scm.bottom=-220;scm.near=10;scm.far=1000;sun.shadow.bias=-.0004;sun.shadow.normalBias=.6;
scene.add(sun,sun.target);
scene.fog=new THREE.Fog(0xffffff,300,1000);

/* ---------- 後製：光暈＋調色＋移軸＋鏡頭光暈 ---------- */
const composer=new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
const bloom=new UnrealBloomPass(new THREE.Vector2(VW(),VH()),.2,.6,.82);composer.addPass(bloom);
composer.addPass(new OutputPass());
const grade=new ShaderPass({uniforms:{tDiffuse:{value:null},uRes:{value:new THREE.Vector2(VW(),VH())},uSat:{value:1},uWarm:{value:0},uCon:{value:1},uVig:{value:.3},uGrain:{value:0},uTilt:{value:1},uTime:{value:0},
  uSun:{value:new THREE.Vector2(-1,-1)},uFlare:{value:0},uShadow:{value:new THREE.Color(0,0,0)},uHigh:{value:new THREE.Color(0,0,0)}},
 vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
 fragmentShader:`uniform sampler2D tDiffuse;uniform vec2 uRes,uSun;uniform float uSat,uWarm,uCon,uVig,uGrain,uTilt,uTime,uFlare;uniform vec3 uShadow,uHigh;varying vec2 vUv;
 float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
 void main(){
  float band=smoothstep(.2,.55,abs(vUv.y-.42))*uTilt;vec3 c;
  if(band>.01){vec3 a=vec3(0.);float t=0.;float r=band*3.2;for(int i=-3;i<=3;i++)for(int j=-3;j<=3;j++){vec2 o=vec2(float(i),float(j))*r/uRes;float w=exp(-float(i*i+j*j)/7.);a+=texture2D(tDiffuse,vUv+o).rgb*w;t+=w;}c=a/t;}
  else c=texture2D(tDiffuse,vUv).rgb;
  float l=dot(c,vec3(.299,.587,.114));c=mix(vec3(l),c,uSat);
  c=(c-.5)*uCon+.5;c+=vec3(uWarm,uWarm*.35,-uWarm*.6);
  c+=uShadow*(1.-smoothstep(0.,.55,l))+uHigh*smoothstep(.45,1.,l);
  if(uFlare>0.){vec2 asp=vec2(uRes.x/uRes.y,1.);vec2 d=(vUv-uSun)*asp;float g=exp(-dot(d,d)*7.);c+=vec3(1.,.78,.5)*g*.35*uFlare;
   c+=vec3(1.,.8,.55)*exp(-abs(d.y)*90.)*exp(-abs(d.x)*1.6)*.25*uFlare;
   for(int k=1;k<5;k++){float f=float(k)*.27;vec2 gp=mix(uSun,vec2(1.)-uSun,f);vec2 gd=(vUv-gp)*asp;float rr=.02+.025*float(k);float ring=smoothstep(rr,rr*.6,length(gd));c+=mix(vec3(.5,.8,1.),vec3(1.,.6,.8),f)*ring*.07*uFlare;}}
  vec2 q=vUv-.5;c*=1.-uVig*dot(q,q)*1.6;
  c+=(h(vUv*uRes+uTime)-.5)*uGrain;
  gl_FragColor=vec4(clamp(c,0.,1.),1.);}`});
composer.addPass(grade);

/* ---------- 年代切換 ---------- */
let current=null,lookT=null,tiltOn=true;
const cur={sat:1,warm:0,con:1,vig:.3,grain:0,tilt:1,bloom:.15,clouds:.3,sunGlow:0,flare:0,motes:0};
function applyLook(e,instant){
 const L=e.look;const sunDir=new THREE.Vector3(...L.sun).normalize();
 sun.position.copy(sunDir).multiplyScalar(450);sun.target.position.set(0,0,0);sun.color.set(L.sunCol);sun.intensity=L.sunI;
 hemi.color.set(L.hemiSky);hemi.groundColor.set(L.hemiGnd);hemi.intensity=L.hemiI;
 skyU.top.value.set(L.sky[0]);skyU.hor.value.set(L.sky[1]);skyU.warm.value.set(L.sky[2]);skyU.sunDir.value.copy(sunDir);
 scene.fog.color.set(L.fog);scene.fog.near=L.fogD[0];scene.fog.far=L.fogD[1];
 sunSprite.position.copy(sunDir).multiplyScalar(2200);sunSprite.visible=!!e.sk;
 lookT={sat:L.sat,warm:L.warm,con:L.con,vig:L.vig,grain:L.grain,tilt:L.tilt*(tiltOn?1:0),bloom:L.bloom,clouds:L.clouds,sunGlow:e.sk?1:.25,flare:e.sk?1:0,motes:e.sk?.85:0};
 grade.uniforms.uShadow.value.set(e.sk?0x0c1a3a:0x000000).multiplyScalar(e.sk?1:0);
 grade.uniforms.uHigh.value.set(e.sk?0x2a1606:0x000000);
 renderer.toneMappingExposure=e.sk?1.08:1.0;
 if(instant)Object.assign(cur,lookT);
}
function setEra(i,instant){
 const e=ERAS[i];if(current===i)return;current=i;
 document.querySelectorAll('.era').forEach((b,k)=>b.setAttribute('aria-pressed',String(k===i)));
 const doSwap=()=>{
  const t=getTex(e.tex);groundMat.map=t;groundMat.needsUpdate=true;setProjTex(e.tex);
  buildBuildings(e);buildFixtures(e);layoutTown(e);
  treeGrowTarget=e.look.grow;treeMode=e.sk?2:(e.y===2011?1:0);layoutTrees(instant?e.look.grow:treeGrow,treeMode);if(instant)treeGrow=e.look.grow;
  drawPlate(e);applyLook(e,instant);
  eraText(e);
  selected=null;showInfo(null);
 };
 if(instant){doSwap();return}
 const fl=document.getElementById('flash');document.getElementById('flashYear').textContent=e.y<=2003?'≤2003':e.y;document.getElementById('flashSub').textContent=T_(e.dateZh,e.dateEn);
 fl.classList.add('on');setTimeout(()=>{doSwap();setTimeout(()=>fl.classList.remove('on'),260)},matchMedia('(prefers-reduced-motion: reduce)').matches?0:330);
}

/* ---------- UI ---------- */
const erasEl=document.getElementById('eras');
ERAS.forEach((e,i)=>{const b=document.createElement('button');b.className='era'+(e.sk?' sk':'');b.setAttribute('aria-pressed','false');b.innerHTML=`<b>${e.y<=2003?'≤2003':e.y}</b><span data-zh="${e.tagZh||'　'}" data-en="${e.tagEn||'　'}">${T_(e.tagZh,e.tagEn)||'　'}</span>`;b.onclick=()=>setEra(i);erasEl.appendChild(b)});
const rail=document.getElementById('rail');const y0=2002,y1=2027;const pos=y=>((y-y0)/(y1-y0)*100).toFixed(3)+'%';
for(let y=2004;y<=2020;y+=4){const s=document.createElement('span');s.className='yr';s.style.left=pos(y);s.textContent=y;rail.appendChild(s)}
const keyY=new Set(ERAS.map(e=>e.y));
SAMPLED.forEach(y=>{const t=document.createElement('span');t.className='tick'+(keyY.has(y)?' key':'');t.style.left=pos(y+.95);t.dataset.zh=keyY.has(y)?`${y} 年底：新影像`:`${y} 年底：沿用前期影像`;t.dataset.en=keyY.has(y)?`Late ${y}: new image`:`Late ${y}: earlier image still shown`;t.title=T_(t.dataset.zh,t.dataset.en);rail.appendChild(t)});
const capEl=document.createElement('span');capEl.className='cap';capEl.dataset.zh=`逐年查看 ${SAMPLED.length} 次 · ${ERAS.length} 期不同影像`;capEl.dataset.en=`${SAMPLED.length} yearly checks · ${ERAS.length} different images`;capEl.textContent=T_(capEl.dataset.zh,capEl.dataset.en);document.getElementById('railcap').appendChild(capEl);

const btn=id=>document.getElementById(id);
btn('tLabels').onclick=()=>{showLabels=!showLabels;btn('tLabels').setAttribute('aria-pressed',showLabels);document.querySelectorAll('.lbl').forEach(l=>l.classList.toggle('hide',!showLabels))};
btn('tSpin').onclick=()=>{controls.autoRotate=!controls.autoRotate;btn('tSpin').setAttribute('aria-pressed',controls.autoRotate)};
btn('sideToggle').onclick=()=>{const s=btn('side');const o=!s.classList.contains('open');s.classList.toggle('open',o);btn('sideToggle').setAttribute('aria-pressed',o)};
const VIEWS={vBird:[[210,150,300],[0,6,0]],vTop:[[0,600,1],[0,0,0]],vGate:[[36,16,150],[-14,6,72]],vTrack:[[-170,48,-40],[0,2,-50]],vStage:[[4,16,-78],[2,5,0]]};
let camAnim=null;
const fitK=()=>{const a=VW()/VH();return a<1?Math.min(2.1,1/a*.95):1};
function viewPose(id){const [p,t]=VIEWS[id];const Tg=new THREE.Vector3(...t),P=new THREE.Vector3(...p);if(id!=='vTop')P.sub(Tg).multiplyScalar(fitK()).add(Tg);else P.y*=fitK();return[P,Tg]}
{const [P,Tg]=viewPose('vBird');camera.position.copy(P);controls.target.copy(Tg)}
for(const id in VIEWS){btn(id).onclick=()=>{for(const k in VIEWS)btn(k).setAttribute('aria-pressed',k===id);const [P,Tg]=viewPose(id);camAnim={p0:camera.position.clone(),t0:controls.target.clone(),p1:P,t1:Tg,k:0}}}

/* 點選建物 */
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();let selected=null;let downAt=null;
renderer.domElement.addEventListener('pointerdown',ev=>{downAt=[ev.clientX,ev.clientY]});
renderer.domElement.addEventListener('pointerup',ev=>{if(!downAt||Math.hypot(ev.clientX-downAt[0],ev.clientY-downAt[1])>5)return;
 {const r=renderer.domElement.getBoundingClientRect();mouse.set((ev.clientX-r.left)/r.width*2-1,-(ev.clientY-r.top)/r.height*2+1)};ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(pickables,false)[0];
 if(hit){selected=hit.object.userData.grp;showInfo(selected.userData.b)}else{selected=null;showInfo(null)}});
function bName(b){return LANG==='en'?((L10N.B[b.id]||{}).en||b.name):b.name}
function area(p){let a=0;for(let i=0;i<p.length;i++){const q=p[i],r=p[(i+1)%p.length];a+=q[0]*r[1]-r[0]*q[1]}return Math.abs(a/2)}
function showInfo(b){
 const el=document.getElementById('bInfo');
 if(!b){el.innerHTML=`<div class="note">${T_('點一下模型上的建物，可查看量測尺寸與推估樓層。','Tap a building to see its measured size and estimated number of floors.')}</div>`;highlight(null);return}
 const E=edgeList(b.p);const L=Math.max(...E.map(x=>x.len)),S=Math.min(...E.map(x=>x.len));
 const B=L10N.B[b.id]||{};const alt=LANG==='en'?b.name:(B.en||'');
 el.innerHTML=`<div class="bname">${bName(b)}</div>${alt?`<div class="balt">${alt}${LANG==='en'&&B.mean?` · “${B.mean}”`:''}</div>`:''}<dl>`+
  (LANG==='en'?`<dt>Footprint</dt><dd>about ${L.toFixed(0)} × ${S.toFixed(0)} m</dd><dt>Area</dt><dd>about ${area(b.p).toFixed(0)} m²</dd><dt>Height</dt><dd>about ${b.h} m · ${B.fl||b.fl}</dd>${b.from?`<dt>First seen</dt><dd>${b.from} image</dd>`:''}`
  :`<dt>平面</dt><dd>約 ${L.toFixed(0)} × ${S.toFixed(0)} m</dd><dt>面積</dt><dd>約 ${area(b.p).toFixed(0)} m²</dd><dt>高度</dt><dd>約 ${b.h} m · ${b.fl}</dd>${b.from?`<dt>出現</dt><dd>${b.from} 年影像起</dd>`:''}`)+`</dl>`;
 highlight(selected);
 if(innerWidth<=820){btn('side').classList.add('open');btn('sideToggle').setAttribute('aria-pressed','true')}
}
function highlight(grp){bldGroup.traverse(o=>{if(o.isMesh){const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>{if(m.emissive&&!projMats.includes(m))m.emissive.set(0x000000)})}});
 if(grp)grp.traverse(o=>{if(o.isMesh){const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>{if(m.emissive&&!projMats.includes(m))m.emissive.set(0x3a2410)})}})}

function eraText(e){
 document.getElementById('sYear').textContent=e.y<=2003?'≤2003':e.y;document.getElementById('sTag').textContent=T_(e.tagZh,e.tagEn);
 document.getElementById('sDate').textContent=T_(e.dateZh,e.dateEn);document.getElementById('sText').textContent=T_(e.textZh,e.textEn);
}
window.addEventListener('langchange',ev=>{
 LANG=ev.detail;
 document.querySelectorAll('[data-zh][data-en]').forEach(n=>{const v=LANG==='en'?n.dataset.en:n.dataset.zh;if(n.classList.contains('tick'))n.title=v;else n.textContent=v});
 if(current!=null){const e=ERAS[current];eraText(e);buildBuildings(e);
  if(selected){const id=selected.userData.b.id;selected=bldGroup.children.find(g=>g.userData.b&&g.userData.b.id===id)||null;showInfo(selected&&selected.userData.b)}else showInfo(null)}
});
/* 標籤互相重疊時，只留較大的建物 */
let declutterN=0;
function declutter(){
 const L=[...document.querySelectorAll('#labels .lbl')].filter(l=>!l.classList.contains('hide')&&l.style.display!=='none');
 L.forEach(l=>l.classList.remove('clash'));
 const R=L.map(l=>({l,r:l.getBoundingClientRect(),p:+l.dataset.pri||0})).filter(o=>o.r.width>0).sort((a,b)=>b.p-a.p);
 const kept=[];
 for(const o of R){const hit=kept.some(k=>o.r.left<k.r.right+2&&o.r.right>k.r.left-2&&o.r.top<k.r.bottom+2&&o.r.bottom>k.r.top-2);if(hit)o.l.classList.add('clash');else kept.push(o)}
}

/* ---------- 迴圈 ---------- */
new ResizeObserver(()=>window.dispatchEvent(new Event('vresize'))).observe(VIEW);
addEventListener('vresize',()=>{camera.aspect=VW()/VH();camera.updateProjectionMatrix();renderer.setSize(VW(),VH());composer.setSize(VW(),VH());labelRenderer.setSize(VW(),VH());grade.uniforms.uRes.value.set(VW(),VH())});
const clock=new THREE.Clock();const tmpV=new THREE.Vector3();
const lerp=(a,b,t)=>a+(b-a)*t;
function tick(){
 const dt=Math.min(clock.getDelta(),.05),t=clock.elapsedTime;
 if(camAnim){camAnim.k=Math.min(1,camAnim.k+dt/1.4);const k=camAnim.k<.5?4*camAnim.k**3:1-(-2*camAnim.k+2)**3/2;camera.position.lerpVectors(camAnim.p0,camAnim.p1,k);controls.target.lerpVectors(camAnim.t0,camAnim.t1,k);if(camAnim.k>=1)camAnim=null}
 controls.update();
 updateLife(dt,t);
 if(lookT){const f=1-Math.exp(-dt*4);for(const k in lookT)cur[k]=lerp(cur[k],lookT[k],f)}
 if(Math.abs(treeGrow-treeGrowTarget)>.002){treeGrow=lerp(treeGrow,treeGrowTarget,1-Math.exp(-dt*3));layoutTrees(treeGrow,treeMode)}
 const G=grade.uniforms;G.uSat.value=cur.sat;G.uWarm.value=cur.warm;G.uCon.value=cur.con;G.uVig.value=cur.vig;G.uGrain.value=cur.grain;G.uTilt.value=cur.tilt;G.uTime.value=t%100;
 bloom.strength=cur.bloom;skyU.sunGlow.value=cur.sunGlow;
 clouds.children.forEach(c=>{c.material.opacity=cur.clouds*.95;c.position.applyAxisAngle(THREE.Object3D.DEFAULT_UP,c.userData.drift*dt)});
 motes.material.opacity=cur.motes;if(cur.motes>.01){const a=moteGeo.attributes.position;for(let i=0;i<moteN;i++){a.array[i*3+1]+=Math.sin(t*.7+i)*.01;a.array[i*3]+=.015;if(a.array[i*3]>W/2)a.array[i*3]-=W}a.needsUpdate=true}
 tmpV.copy(sunSprite.position).project(camera);const onScreen=tmpV.z<1&&Math.abs(tmpV.x)<1.3&&Math.abs(tmpV.y)<1.3;
 G.uSun.value.set(tmpV.x*.5+.5,tmpV.y*.5+.5);G.uFlare.value=onScreen?cur.flare:0;
 composer.render();labelRenderer.render(scene,camera);if((++declutterN%6)===0)declutter();
 requestAnimationFrame(tick);
}
document.fonts&&document.fonts.ready.then(()=>{if(current!=null)drawPlate(ERAS[current])});
setEra(ERAS.length-1,true);
tick();
setTimeout(()=>document.getElementById('loading').classList.add('done'),300);
window.dispatchEvent(new CustomEvent('langchange',{detail:LANG}));
