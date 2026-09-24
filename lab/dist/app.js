'use strict';
const $ = id => document.getElementById(id);
const defaults = {instrument:'NQ',session:'RDR',direction:'long',weekday:'all',from:630,to:660,status:'all',mode:'history',observed:690,target:.8};
let state={...defaults}, data=null, currentView='dashboard', requestId=0, activeScene=null, sceneTf=5;
try{const saved=JSON.parse(sessionStorage.getItem('dr-lab-view')||'null');if(saved&&saved.version===1)state={...defaults,...saved.state};}catch{/* Optional device-local view preference only. */}
const sessionTimes={RDR:[630,960],ODR:[240,510],ADR:[1230,1560]};
const weekdays=['Понедельник','Вторник','Среда','Четверг','Пятница'];
const number=(n,d=0)=>n==null?'—':Number(n).toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d});
const signed=(n,d=1)=>n==null?'—':(n>0?'+':'')+number(n,d);
const time=m=>m==null?'—':`${String(Math.floor(m/60)%24).padStart(2,'0')}:${String(Math.floor(m)%60).padStart(2,'0')}`+(m>=1440?' +1':'');
const asMinute=s=>{const [h,m]=s.split(':').map(Number);return h*60+m;};
const xml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const svg=(w,h,body,label)=>`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${xml(label)}">${body}</svg>`;
const help={
  path:['Распределение путей','Линия — медиана закрытий выбранных завершённых сессий в каждый момент. Область — 20-й и 80-й процентили. Это срез распределения в каждый момент, а не одна реально существовавшая траектория и не вероятность удержания цены внутри полосы до конца сессии.','Для направленной шкалы начало — граница IDR по направлению подтверждения. Шорты зеркально переведены в ту же систему координат.'],
  heat:['Один случай — одна ячейка','Каждая завершённая сессия даёт пару: глубина окончательного максимального отката и время его первого достижения. По цене шаг 0,1 IDR, по времени — 15 минут.','Цвет отражает число сессий в ячейке. Подсказка показывает количество и долю от всей завершённой выборки. Это карта экстремумов, а не карта всех касаний. Щелчок выделяет оба условия и пересчитывает остальные графики.'],
  retr:['Максимальный откат','Минимальная направленная координата цены после закрытия подтверждающей свечи до конца наблюдения. Для лонга используется low, для шорта — high.','0 — ближняя граница IDR; −1 — противоположная. Положительный минимум означает, что цена не вернулась внутрь IDR. В режиме «На момент» измерение начинается строго после среза. Оборванные сессии не подменяются завершёнными.'],
  ext:['Максимальное расширение','Максимальная направленная координата после подтверждения. В режиме «На момент» — только после выбранного времени.','Частота попадания максимума в столбец и вероятность достижения его нижней границы — разные числа. Для вероятности достижения суммируются все исходы, достигшие цели или ушедшие дальше.'],
  rtime:['Время максимального отката','Нью-йоркское время первого достижения окончательного экстремума. На полной истории оно известно после окончания сессии.','Выбор временного столбца — исследовательский отбор по будущему исходу. В режиме «На момент» этот отбор отключён: в текущую минуту нельзя знать, что следующий минимум не станет глубже.'],
  etime:['Время максимального расширения','Время первого достижения наибольшего расширения внутри наблюдаемого интервала. Это не время первого касания каждой промежуточной цели.','Если экстремум повторяется, здесь учитывается первое достижение. Полный свечной путь сохраняется для отдельного расчёта последовательности касаний.'],
  true:['Что означает DR true','После первого подтверждения ни одно последующее закрытие M5 не пересекло противоположную внешнюю границу DR. Тени могут её пересекать.','DR true не означает прибыльную сделку. До конца наблюдения итог true неизвестен; false становится известен на закрытии первого противоположного подтверждения.'],
  sample:['Какие случаи посчитаны','Единица — одна сессия выбранного инструмента. Число выбранных сессий, полностью наблюдаемых сессий и недосмотренных случаев показаны отдельно.','В режиме ленты свечи — минутная лента NQ 2006–2025 (2026 скрыт); в демо-режиме — искусственные. Числа описывают историю выбранной группы, а не прогноз и не сделку.']
};

function showHelp(key){
  const h=help[key]||help.sample;
  $('help-content').innerHTML=`<div class="eyebrow">СМЫСЛ ПОКАЗАТЕЛЯ</div><h2>${h[0]}</h2>${h.slice(1).map(x=>`<p>${x}</p>`).join('')}`;
  $('help-dialog').showModal();
}
function tip(event,text){const box=$('tooltip');box.textContent=text;box.classList.remove('hidden');box.style.left=Math.max(8,Math.min(event.clientX+12,window.innerWidth-290))+'px';box.style.top=Math.max(8,Math.min(event.clientY+16,window.innerHeight-box.offsetHeight-12))+'px';}
function hideTip(){$('tooltip').classList.add('hidden');}
function params(){return new URLSearchParams(Object.entries(state).filter(([,v])=>v!==null&&v!==undefined&&v!==''));}
async function load(){
  const rid=++requestId;
  $('error').classList.add('hidden');
  $('context-line').setAttribute('aria-busy','true');
  try{
    const response=await fetch('/api/query?'+params());
    const value=await response.json();
    if(!response.ok)throw new Error(value.error||'Расчёт недоступен');
    if(rid!==requestId)return;
    data=value;document.body.classList.remove('data-stale');render();if(window.liveOnQuery)window.liveOnQuery();
    try{sessionStorage.setItem('dr-lab-view',JSON.stringify({version:1,state}));}catch{}
  }catch(error){if(rid===requestId){$('error').textContent=error.message+' · Показана последняя рассчитанная выборка.';$('error').classList.remove('hidden');document.body.classList.add('data-stale');}}
  finally{if(rid===requestId)$('context-line').setAttribute('aria-busy','false');}
}
function sync(){
  for(const key of ['direction','weekday','status','target'])$(key).value=String(state[key]);
  $('from').value=time(state.from).slice(0,5);$('to').value=time(state.to).slice(0,5);
  document.querySelectorAll('[data-session]').forEach(b=>b.classList.toggle('active',b.dataset.session===state.session));document.querySelectorAll('[data-instrument]').forEach(b=>b.classList.toggle('active',b.dataset.instrument===(state.instrument||'NQ')));if($('crumb-instrument'))$('crumb-instrument').textContent=state.instrument||'NQ';
  document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===state.mode));
  $('status').disabled=state.mode==='prefix';
  $('prefix-panel').classList.toggle('hidden',state.mode!=='prefix');
  $('observed').min=sessionTimes[state.session][0]+5;$('observed').max=sessionTimes[state.session][1]-5;$('observed').value=state.observed;
  $('observed-label').textContent=time(state.observed)+' ET';
}
function clearChartFilters(){for(const k of ['retr','ext','rtime','etime']){delete state[k];delete state[k+'_hi'];}}
function selectBin(key,lo,extend=false){
  if(state.mode==='prefix')return;
  const step=key.includes('time')?15:.1;
  if(extend&&state[key]!=null){const previous=state[key];state[key]=Math.min(previous,lo);state[key+'_hi']=Math.max(state[key+'_hi']||previous+step,lo+step);}
  else if(state[key]===lo&&state[key+'_hi']==null){delete state[key];}
  else{state[key]=lo;delete state[key+'_hi'];}
  load();
}
function kpi(label,value,meta,accent='',key=''){return `<div class="kpi ${accent}"><div class="kpi-label">${label}${key?` <button class="info-button" data-help="${key}" aria-label="Объяснение: ${label}">i</button>`:''}</div><div class="kpi-value">${value}</div><div class="kpi-meta">${meta}</div></div>`;}
function render(){
  const d=data,dir=state.direction==='long'?'↑ Long':state.direction==='short'?'↓ Short':'Long + Short';
  $('context-line').textContent=`${state.instrument||'NQ'} · ${state.session} · ${dir} · ${state.weekday==='all'?'все дни':weekdays[+state.weekday]} · ${time(state.from)}–${time(state.to)} ET`;
  $('kpis').innerHTML=[
    kpi('Сессий в выборке',number(d.n),`из ${number(d.base_n)} по контексту`,'accent','sample'),
    kpi('DR true',number(d.true.pct,1)+'<small>%</small>',`${d.true.k} / ${d.true.n} известных исходов`,'','true'),
    kpi('Медианный откат',signed(d.median_retr,2)+'<small>IDR</small>',`завершено: ${d.complete_n}`),
    kpi('Медианное расширение',signed(d.median_ext,2)+'<small>IDR</small>','от ближней границы IDR'),
    kpi('Время отката',d.median_rtime||'—','медиана · New York'),
    kpi('Достижение цели',number(d.target.pct,1)+'<small>%</small>',`${d.target.k} / ${d.target.n} · цель ${signed(+state.target)}${d.target.unknown?` · неизв. ${d.target.unknown}`:''}`,'accent')
  ].join('');
  let chips=[];
  const names={retr:'Откат',ext:'Расширение',rtime:'Время отката',etime:'Время расширения'};
  for(const key of Object.keys(names)){if(state[key]!=null){const temporal=key.includes('time');const end=state[key+'_hi']??(+state[key]+(temporal?15:.1));chips.push(`<span class="chip">${names[key]} ${temporal?time(+state[key]):signed(+state[key])}…${temporal?time(end):signed(end)}<button data-clear="${key}" aria-label="Удалить фильтр ${names[key]}">×</button></span>`);}}
  if(state.status!=='all')chips.unshift('<span class="xray-label">ОТБОР ПО БУДУЩЕМУ ИТОГУ · X-RAY</span>');
  $('selection-chips').innerHTML=chips.join('')||`<span class="muted">${state.mode==='prefix'?`На ${time(state.observed)}: исключено ${d.prefix_excluded} уже неактуальных или недоступных случаев`:'Вся выбранная группа · нажмите на столбец или ячейку, чтобы уточнить'}</span>`;
  $('clear-charts').classList.toggle('hidden',!['retr','ext','rtime','etime'].some(k=>state[k]!=null));
  if(!(window.liveOwnsCharts&&window.liveOwnsCharts())){drawPath(d);drawHeat(d);for(const key of ['retr','ext','rtime','etime'])drawHist(key,d.charts[key]);}
  $('target-result').innerHTML=`${number(d.target.pct,1)}%<small>${d.target.k} из ${d.target.n} известных исходов · неизвестно ${d.target.unknown}${d.target.unknown?`<br>Границы для всех случаев: ${number(d.target.bounds[0],1)}–${number(d.target.bounds[1],1)}%`:''}</small>`;
  const market=d.data_kind==='MARKET';$('provenance').textContent=market?`${d.version} · ${d.provenance}`:`${d.version} · SYNTHETIC · без Volume`;document.querySelector('.demo-badge').textContent=market?`ЛЕНТА ${d.instrument} · 2006–2025`:'ДЕМО · СИНТЕТИЧЕСКИЕ ДАННЫЕ';document.querySelector('.demo-note').innerHTML=market?`Реальная лента ${d.instrument}: <b>${number(d.total)} сессий с подтверждением</b> (ADR, ODR, RDR), 2006–2025; 2026 скрыт. Числа — описание истории, не прогноз и не сделка.`:'Макет на <b>2 160 искусственных сессиях</b>. Числа показывают работу интерфейса и расчётов, а не свойства рынка NQ.';
  renderScenes();if(activeScene)drawScene(activeScene);
  if(window.liveRedraw)window.liveRedraw();
}
function drawPath(d){
  const host=$('path-chart'),w=Math.max(320,host.clientWidth-16),h=Math.max(150,host.clientHeight-4),p={l:42,r:14,t:8,b:24};
  const lows=d.curve.map(v=>v.low),highs=d.curve.map(v=>v.high);
  const vlo=Math.min(0,...lows)-.12,vhi=Math.max(.3,...highs)+.12,span=vhi-vlo,stepY=span>3?1:span>1.4?.5:.25;
  const ys=[];for(let v=Math.ceil(vlo/stepY)*stepY;v<=vhi+1e-9;v+=stepY)ys.push(Math.round(v*100)/100);
  const x=t=>p.l+(t-d.formed)/(d.end-d.formed)*(w-p.l-p.r),y=v=>p.t+(vhi-v)/span*(h-p.t-p.b);
  let g=ys.map(v=>`<line x1="${p.l}" y1="${y(v)}" x2="${w-p.r}" y2="${y(v)}" class="${v===0?'zero-line':'grid-line'}"/><text x="${p.l-8}" y="${y(v)+4}" text-anchor="end" class="axis-text">${signed(v)}</text>`).join('');
  for(let t=d.formed;t<=d.end;t+=(w<430?90:60))g+=`<text x="${x(t)}" y="${h-5}" text-anchor="middle" class="axis-text">${time(t)}</text>`;
  if(d.curve.length){
    const path=(field,points=d.curve)=>points.map((v,i)=>`${i?'L':'M'}${x(v.t).toFixed(1)},${y(v[field]).toFixed(1)}`).join(' ');
    const reverse=[...d.curve].reverse();
    g+=`<defs><linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#27bda6" stop-opacity=".28"/><stop offset="1" stop-color="#27bda6" stop-opacity=".05"/></linearGradient><clipPath id="path-clip"><rect x="${p.l}" y="${p.t}" width="${w-p.l-p.r}" height="${h-p.t-p.b}"/></clipPath></defs><g clip-path="url(#path-clip)"><path d="${path('high')} ${path('low',reverse).replace('M','L')} Z" fill="url(#band)"/><path d="${path('mid')}" fill="none" stroke="#3edac3" stroke-width="2.2"/>`;
    if(state.mode==='prefix')g+=`<line x1="${x(state.observed)}" x2="${x(state.observed)}" y1="${p.t}" y2="${h-p.b}" stroke="#8bc7ff" stroke-dasharray="4 3"/>`;
    g+='</g>';
    for(const v of d.curve)g+=`<rect x="${x(v.t)-3}" y="${p.t}" width="7" height="${h-p.t-p.b}" fill="transparent" data-tip="${time(v.t)} ET · медиана ${signed(v.mid,2)} IDR · n=${v.n}"/>`;
  } else g+=`<text x="310" y="120" text-anchor="middle" class="axis-text">Нет завершённых сессий для этого отбора</text>`;
  $('path-chart').innerHTML=svg(w,h,g,'Распределение направленных траекторий выбранных сессий');
}
function drawHist(key,chart,src=data){
  const host=$(key+'-chart');host.classList.toggle('blue',key==='ext'||key==='etime');
  const w=Math.max(220,host.clientWidth-16),h=Math.max(100,host.clientHeight-2),p={l:29,r:8,t:10,b:22},temporal=key.includes('time'),bins=chart.bins;
  if(!bins.length){host.innerHTML='<div class="empty">Нет наблюдений</div>';return;}
  const max=Math.max(1,...bins.map(b=>b.n),...chart.reference.map(b=>b.n));
  const bw=(w-p.l-p.r)/bins.length,y=n=>h-p.b-n/max*(h-p.t-p.b);
  let g='';
  for(const frac of [0,.5,1])g+=`<line x1="${p.l}" y1="${y(max*frac)}" x2="${w-p.r}" y2="${y(max*frac)}" class="grid-line"/><text x="${p.l-6}" y="${y(max*frac)+3}" text-anchor="end" class="axis-text">${number(max*frac)}</text>`;
  bins.forEach((b,i)=>{
    const x=p.l+i*bw+2,ref=chart.reference[i]?.n||0;
    g+=`<rect x="${x}" y="${y(ref)}" width="${Math.max(2,bw-4)}" height="${h-p.b-y(ref)}" class="bar-reference"/>`;
    const label=temporal?`${time(b.lo)}–${time(b.hi)}`:`${signed(b.lo)}…${signed(b.hi)} IDR`;
    const tipText=`${label} · ${b.n} / ${chart.n} сессий · ${number(chart.n?100*b.n/chart.n:0,1)}%`;
    const selected=state[key]!=null&&b.lo>=state[key]-1e-8&&b.lo<(state[key+'_hi']??(state[key]+(temporal?15:.1)))-1e-8;
    g+=`<rect role="button" tabindex="${state.mode==='history'?0:-1}" aria-disabled="${state.mode==='prefix'}" aria-label="${xml(tipText)}" data-bin="${key}" data-lo="${b.lo}" data-tip="${xml(tipText)}" x="${x}" y="${y(b.n)}" width="${Math.max(2,bw-4)}" height="${Math.max(3,h-p.b-y(b.n))}" class="bar ${selected?'selected':''}"/>`;
    const step=Math.ceil(bins.length/Math.max(4,Math.floor(w/(temporal?68:50))));
    if(i%step===0)g+=`<text x="${x+bw/2}" y="${h-6}" text-anchor="middle" class="axis-text">${temporal?time(b.lo):signed(b.lo)}</text>`;
  });
  const median=key==='retr'?src.median_retr:key==='ext'?src.median_ext:null;
  if(median!=null&&median>=bins[0].lo&&median<bins.at(-1).hi){const x=p.l+(median-bins[0].lo)/(bins.at(-1).hi-bins[0].lo)*(w-p.l-p.r);g+=`<line x1="${x}" x2="${x}" y1="${p.t-4}" y2="${h-p.b}" class="median-line"/>`;}
  host.innerHTML=svg(w,h,g,`Распределение ${key}; знаменатель ${chart.n} завершённых сессий`);
  $(key+'-foot').innerHTML=`<span>n = ${chart.n} · ${temporal?'шаг 15 минут':'шаг 0,1 IDR'}${chart.underflow+chart.overflow?' · вне шкалы: '+(chart.underflow+chart.overflow):''}</span><span>${state.mode==='history'?'Shift+щелчок — диапазон':'после среза'}</span>`;
}
function drawHeat(d){
  const times=[];for(let t=d.formed;t<d.end;t+=15)times.push(t);
  const top=Math.min(30,Math.max(3,...d.heat.map(c=>Math.round(c.r*10))));const rows=[];for(let r=top;r>=-25;r--)rows.push(r/10);
  const lookup=new Map(d.heat.map(c=>[`${c.r.toFixed(1)}:${c.t}`,c.n]));
  const max=Math.max(1,...d.heat.map(c=>c.n));
  const hh=$('heatmap').clientHeight,ch=(matchMedia('(min-width:1001px) and (min-height:600px)').matches&&hh>80)?Math.max(5,Math.floor((hh-22)/rows.length)-2):15;
  let html=`<div class="heatmap-grid" style="--cell-h:${ch}px;grid-template-columns:31px repeat(${times.length}, minmax(6px, 1fr))">`;
  for(const [i,r] of rows.entries()){
    html+=`<span class="heat-y">${Math.round(r*10)%5===0?signed(r):''}</span>`;
    for(const t of times){const n=lookup.get(`${r.toFixed(1)}:${t}`)||0,alpha=n?.22+.78*n/max:.035;
      const txt=`${signed(r)}…${signed(r+.1)} IDR · ${time(t)}–${time(t+15)} ET · ${n} / ${d.complete_n} сессий (${number(d.complete_n?n/d.complete_n*100:0,1)}%)`;
      html+=`<button ${state.mode==='prefix'?'disabled':''} data-heat-r="${r}" data-heat-t="${t}" data-tip="${xml(txt)}" aria-label="${xml(txt)}" class="heatmap-cell ${state.retr===r&&state.rtime===t?'selected':''}" style="background:rgba(53,203,176,${alpha})"></button>`;
    }
  }
  html+='<span></span>'+times.map((t,i)=>`<span class="heat-x">${i%4===0?time(t):''}</span>`).join('')+'</div>';
  $('heatmap').innerHTML=html;
  const visible=d.heat.filter(c=>c.r>=-2.5&&c.r<.4&&c.t>=d.formed&&c.t<d.end).reduce((s,c)=>s+c.n,0);
  $('heat-count').textContent=`n = ${d.complete_n} · ${d.complete_n-visible} вне видимой ценовой шкалы`;
}
function renderScenes(){
  if(!data)return;
  const rows=data.scenes;
  $('scenes-table').innerHTML=rows.length?`<table><thead><tr><th>${data.data_kind==='MARKET'?'Дата':'Синтетическая дата'}</th><th>Сессия</th><th>Подтверждение</th><th>Итог</th><th>Откат</th><th>Время</th><th>Расширение</th></tr></thead><tbody>${rows.map(e=>`<tr data-scene="${e.id}" tabindex="0" role="button" aria-label="Открыть сцену ${e.id}"><td>${e.date}</td><td>${state.session}</td><td>${time(e.confirmation)} ${e.direction==='long'?'↑':'↓'}</td><td class="${e.dr_true===true?'status-true':e.dr_true===false?'status-false':'muted'}">${e.dr_true===null?'неизвестно':e.dr_true?'DR true':'DR false'}${!e.complete?' · обрыв':''}</td><td>${signed(e.retracement,2)}</td><td>${time(e.retracement_time)}</td><td>${signed(e.extension,2)}</td></tr>`).join('')}</tbody></table><div class="panel-foot">Показано ${rows.length} из ${data.n} · ${data.data_kind==='MARKET'?'даты и свечи — лента NQ':'даты и свечи сгенерированы для макета'}</div>`:'<div class="empty">Для этих условий сцен нет.<br>Расширьте окно подтверждения или снимите фильтр.</div>';
}
async function openScene(id){
  const r=await fetch('/api/scene?id='+encodeURIComponent(id)),e=await r.json();
  if(!r.ok)return;
  activeScene=e;drawScene(e);$('scene-detail').scrollIntoView({behavior:'smooth',block:'nearest'});
}
function drawScene(e){
  const s=e.direction==='long'?1:-1,w=Math.max(360,$('scenes-view').clientWidth-36),h=315,p={l:50,r:30,t:22,b:32};
  const minuteBars=e.bars.filter(b=>state.mode==='history'||b[0]<=state.observed);
  const grouped=new Map();
  for(const b of minuteBars){const key=Math.ceil(b[0]/sceneTf)*sceneTf;if(!grouped.has(key))grouped.set(key,{bar:[key,b[1],b[2],b[3],b[4]],count:1});else{const a=grouped.get(key);a.bar[2]=Math.max(a.bar[2],b[2]);a.bar[3]=Math.min(a.bar[3],b[3]);a.bar[4]=b[4];a.count++;}}
  const points=[...grouped.values()].filter(x=>x.count===sceneTf).map(x=>x.bar);
  const normalized=points.map(b=>({t:b[0],o:s*(b[1]-e.edge)/e.width,h:s*((s===1?b[2]:b[3])-e.edge)/e.width,l:s*((s===1?b[3]:b[2])-e.edge)/e.width,c:s*(b[4]-e.edge)/e.width}));
  const lo=Math.min(-1.2,...normalized.map(b=>b.l))-.15,hi=Math.max(.5,...normalized.map(b=>b.h))+.2;
  const x=t=>p.l+(t-e.confirmation)/(e.end-e.confirmation)*(w-p.l-p.r),y=v=>p.t+(hi-v)/(hi-lo)*(h-p.t-p.b);
  let g='';for(const v of [-1,-.8,-.5,0,.5,1,1.5,2,3]){if(v>hi||v<lo)continue;g+=`<line x1="${p.l}" x2="${w-p.r}" y1="${y(v)}" y2="${y(v)}" class="${v===0||v===-1?'zero-line':'grid-line'}"/><text x="${p.l-8}" y="${y(v)+4}" class="axis-text" text-anchor="end">${signed(v)}</text>`;}
  const candleW=Math.max(.8,Math.min(7,(w-p.l-p.r)/(e.end-e.confirmation)*sceneTf*.7));
  for(const b of normalized){const color=b.c>=b.o?'#49d6b6':'#ee8b96';g+=`<line x1="${x(b.t)}" x2="${x(b.t)}" y1="${y(b.h)}" y2="${y(b.l)}" stroke="${color}"/><rect x="${x(b.t)-candleW/2}" y="${y(Math.max(b.o,b.c))}" width="${candleW}" height="${Math.max(1,Math.abs(y(b.o)-y(b.c)))}" fill="${color}" data-tip="${time(b.t)} · O ${signed(b.o,2)} H ${signed(b.h,2)} L ${signed(b.l,2)} C ${signed(b.c,2)} IDR"/>`;}
  for(let t=Math.ceil(e.confirmation/60)*60;t<=e.end;t+=60)g+=`<text x="${x(t)}" y="${h-7}" text-anchor="middle" class="axis-text">${time(t)}</text>`;
  if(state.mode==='prefix')g+=`<line x1="${x(state.observed)}" x2="${x(state.observed)}" y1="${p.t}" y2="${h-p.b}" stroke="#85caff" stroke-dasharray="4 4"/>`;
  $('scene-detail').innerHTML=`<div class="scene-toolbar"><div><h2>${e.id} · ${e.direction==='long'?'Long':'Short'}</h2><span class="muted">${data&&data.data_kind==='MARKET'?`OHLC ${e.instrument||'NQ'}`:'Синтетические OHLC'} · ${state.mode==='history'?'полная история':'свечи до '+time(state.observed)} · направленная шкала IDR</span></div><div class="scene-actions"><div class="segmented"><button data-tf="1" class="${sceneTf===1?'active':''}">M1</button><button data-tf="5" class="${sceneTf===5?'active':''}">M5</button></div><button class="text-button" id="close-scene">Закрыть ×</button></div></div><div class="scene-chart">${svg(w,h,g,'Свечной путь выбранной синтетической сцены, только закрытые бары')}</div><div class="panel-foot">${state.mode==='prefix'?'Будущие свечи скрыты':e.complete?'Наблюдение завершено':'Лента оборвана: итоговые экстремумы не подтверждены'} · 1 IDR = ${number(e.width*(e.tick||.25),2)} пункта · подтверждение ${time(e.confirmation)} ET</div>`;
}
async function changeView(view){
  currentView=view;
  for(const v of ['dashboard','scenes','model'])$(v+'-view').classList.toggle('hidden',v!==view);
  document.querySelectorAll('.main-nav [data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  $('page-title').textContent=({dashboard:'Время. Цена. Вероятность.',scenes:'За каждым числом — сцена.',model:'Смысл системы.'})[view];
  if(view==='model'){
    try{const r=await fetch('/api/spec'),d=await r.json();$('model-content').innerHTML=markdown(d.text);}catch{$('model-content').textContent='Спецификация временно недоступна.';}
  }
}
function markdown(text){
  let result='',code=false,list=false;
  for(const raw of text.split('\n')){
    if(raw.startsWith('```')){if(list){result+='</ul>';list=false;}result+=code?'</pre>':'<pre>';code=!code;continue;}
    if(code){result+=xml(raw)+'\n';continue;}
    let line=xml(raw).replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g,'<a href="$2" target="_blank" rel="noreferrer">$1</a>');
    if(/^[-*] /.test(raw)){if(!list){result+='<ul>';list=true;}result+='<li>'+line.slice(2)+'</li>';continue;}
    if(list){result+='</ul>';list=false;}
    if(raw.startsWith('# '))result+='<h2>'+line.slice(2)+'</h2>';
    else if(raw.startsWith('## '))result+='<h2>'+line.slice(3)+'</h2>';
    else if(raw.startsWith('### '))result+='<h3>'+line.slice(4)+'</h3>';
    else if(raw.trim())result+='<p>'+line+'</p>';
  }
  return result+(list?'</ul>':'');
}
document.addEventListener('click',event=>{
  const b=event.target.closest('button,[data-bin],[data-scene]');if(!b)return;
  if(b.dataset.help)showHelp(b.dataset.help);
  if(b.dataset.view)changeView(b.dataset.view);
  if(b.dataset.instrument){state.instrument=b.dataset.instrument;clearChartFilters();activeScene=null;sync();load();}
  if(b.dataset.session){state.session=b.dataset.session;state.from=sessionTimes[state.session][0];state.to=state.from+30;state.observed=state.from+60;clearChartFilters();activeScene=null;sync();load();}
  if(b.dataset.mode){state.mode=b.dataset.mode;if(state.mode==='prefix'){state.status='all';clearChartFilters();}sync();load();}
  if(b.dataset.bin)selectBin(b.dataset.bin,+b.dataset.lo,event.shiftKey);
  if(b.dataset.clear){delete state[b.dataset.clear];delete state[b.dataset.clear+'_hi'];load();}
  if(b.dataset.heatR!==undefined&&state.mode==='history'){const r=+b.dataset.heatR,t=+b.dataset.heatT;delete state.retr_hi;delete state.rtime_hi;if(state.retr===r&&state.rtime===t){delete state.retr;delete state.rtime;}else{state.retr=r;state.rtime=t;}load();}
  if(b.dataset.scene)openScene(b.dataset.scene);
  if(b.id==='close-scene'){activeScene=null;$('scene-detail').innerHTML='';}
  if(b.dataset.tf){sceneTf=+b.dataset.tf;if(activeScene)drawScene(activeScene);}
});
document.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&(e.target.hasAttribute('data-bin')||e.target.hasAttribute('data-scene'))){e.preventDefault();e.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
document.addEventListener('pointermove',e=>{const t=e.target.closest('[data-tip]');if(t)tip(e,t.dataset.tip);else hideTip();});
document.addEventListener('focusin',e=>{if(e.target.dataset.tip){const r=e.target.getBoundingClientRect();tip({clientX:r.left,clientY:r.bottom},e.target.dataset.tip);}});
document.addEventListener('focusout',hideTip);window.addEventListener('scroll',hideTip,true);
$('filters').addEventListener('submit',e=>e.preventDefault());
for(const key of ['direction','weekday','status','target'])$(key).addEventListener('change',()=>{state[key]=$(key).value;load();});
for(const key of ['from','to'])$(key).addEventListener('change',()=>{let value=asMinute($(key).value);if(state.session==='ADR'&&value<720)value+=1440;state[key]=value;load();});
$('observed').addEventListener('input',()=>{$('observed-label').textContent=time(+$('observed').value)+' ET';});
$('observed').addEventListener('change',()=>{state.observed=+$('observed').value;load();});
$('clear-charts').addEventListener('click',()=>{clearChartFilters();load();});
$('mobile-filters').addEventListener('click',()=>{const open=document.querySelector('.sidebar').classList.toggle('filters-open');$('mobile-filters').setAttribute('aria-expanded',String(open));$('mobile-filters').textContent=open?'Свернуть параметры ⌃':'Настроить выборку ⌄';});
$('reset').addEventListener('click',()=>{state={...defaults};sync();load();});
$('help-dialog').querySelector('.dialog-close').addEventListener('click',()=>$('help-dialog').close());
$('help-dialog').addEventListener('click',e=>{if(e.target===$('help-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
$('export').addEventListener('click',()=>{if(!data)return;const payload={kind:data.data_kind==='MARKET'?'DR_LAB_MARKET_QUERY':'DR_LAB_DEMO_QUERY',warning:data.data_kind==='MARKET'?data.instrument+' 2006-2025 history; description, not a forecast':'SYNTHETIC DATA — NOT NQ RESEARCH',version:data.version,seed:data.seed,query:state,counts:{base:data.base_n,selected:data.n,complete:data.complete_n,unknown:data.unknown_n},scene_ids:data.scenes.map(e=>e.id),scene_ids_truncated:data.n>data.scenes.length};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=data.data_kind==='MARKET'?`dr-lab-${data.instrument.toLowerCase()}-selection.json`:'dr-lab-demo-selection.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(data)render();},160);});
if(document.modelContext?.registerTool){
  const lifecycle=new AbortController();window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
  const tool={name:'read_dr_lab_selection',title:'Прочитать выборку DR Lab',description:'Returns the current visible cohort, filters and denominators (data_kind says whether it is the NQ tape or the synthetic demo). It does not run a market forecast or alter the page.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:false},execute(input){if(input&&Object.keys(input).length)throw new Error('This tool takes no parameters');if(!data)throw new Error('No completed query');return {data_kind:data.data_kind,query:data.query,selected:data.n,complete:data.complete_n,unknown:data.unknown_n,target:data.target};}};
  try{Promise.resolve(document.modelContext.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch{}
}
sync();load();
