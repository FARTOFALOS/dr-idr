// 23.5: observed visits of exact zone cells are separate from final R/X and the family's clock.
// node tests/visit_states_page.mjs http://127.0.0.1:8735 [--today]
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8735', today=process.argv.includes('--today');
const B=await startChrome(), results=[];
await B.cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('drlab.d235.trials',JSON.stringify({pullbacks:false}));`});
const sleep=ms=>new Promise(ok=>setTimeout(ok,ms));
const out='lab/.runtime/release-checks/visit-states-shots';
async function open(fragment){
 await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(100);
 await B.cdp.send('Page.navigate',{url:base+'/23-5/'+fragment});
 for(let n=0;n<300;n++){
  if(await evaluate(B.cdp,()=>!!window.__d24?.cur().F && !!window.__d24.visitState && !window.__d24.contract().unchecked))return;
  await sleep(150);
 }
 throw Error('screen not ready: '+fragment);
}
async function shot(name){
 const s=await B.cdp.send('Page.captureScreenshot',{format:'png'});
 fs.mkdirSync(out,{recursive:true}); fs.writeFileSync(out+'/'+name+'.png',Buffer.from(s.data,'base64'));
}
try{
 for(const [width,height] of [[1600,900],[1920,1000]]){
  await B.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await open('#date=2025-12-17&inst=NQ&session=RDR&at=11:10');
  const check=await evaluate(B.cdp,()=>{
   const d=window.__d24, F=d.cur().F, done=[];
   const ck=(ok,name)=>{if(!ok)throw Error(name);done.push(name);};
   const z={zone_id:'test',cell_mask:[[1,0]],time_start:300,time_end:315};
   const frame={act0:300,end:360,f:300,w0t:40,e0t:0,d0:1,held:new Set()};
   const bar=(t,hit)=>({t,o:hit?1:4,h:hit?2:5,l:hit?1:4,c:hit?1.5:4.5});
   const ctx=(cut,bars)=>({live:false,obs:cut,D:{bars}});
   const state=(cut,bars,target=z,fr=frame)=>d.visitState(fr,ctx(cut,bars),null,null,target);
   ck(state(300,[bar(300,true)]).state==='PENDING','forming M5 is not a visit');
   const hit=state(305,[bar(300,true)]);
   ck(hit.state==='VISITED'&&hit.t===305,'visit becomes known at its M5 close');
   ck(state(305,[bar(300,true)],z,{...frame,act0:305}).state==='PENDING','activation candle is excluded');
   ck(state(315,[bar(300,true)],z,{...frame,act0:315}).state==='NO_PERIOD','window ending before eligible M5 is not a missed visit');
   const other=[bar(300,false),bar(305,false),bar(310,false),bar(315,true),bar(320,false),bar(325,false)];
   ck(state(330,other).state==='MISSED','same price after the zone window gets no check');
   const future={...z,cell_mask:[[1,1]],time_start:315,time_end:330};
   ck(state(310,[bar(300,true),bar(305,false)],future).state==='PENDING','same price before the window gets no check');
   const mask={...z,cell_mask:[[1,0],[10,1]],time_end:330};
   ck(state(330,other,mask).state==='MISSED','bounding rectangle cannot replace the zone mask');
   ck(state(315,[bar(300,false),bar(305,false),bar(310,false)]).state==='MISSED','complete ended window without visit');
   ck(state(310,[bar(305,false)]).state==='UNKNOWN','missing M5 cannot become nonvisit');
   const known=state(310,[bar(305,true)]);
   ck(known.state==='VISITED'&&known.t===310,'observed visit survives another missing M5');
   ck(state(305,[bar(300,true)],z,{...frame,held:new Set(['today.zones'])}).state==='WITHHELD','withheld status has no substitute fact');
   const real=F.zones.X.zones[0];
   const markerYes=d.targetMarker(frame,ctx(305,[bar(300,true)]),'X',z);
   const markerNo=d.targetMarker(frame,ctx(330,other),'X',z);
   const markerFuture=d.targetMarker(frame,ctx(310,[bar(300,true),bar(305,false)]),'X',future);
   const markerUnknown=d.targetMarker(frame,ctx(310,[bar(305,false)]),'X',z);
   ck(markerYes.paint.color===d.cfg.visitC&&markerYes.paint.mark==='✓','same exact visit gives a green check and green circle');
   ck(markerNo.paint.color===d.cfg.visitMissC&&markerNo.paint.mark==='×','known nonvisit of an ended exact window gives a red cross and circle');
   ck(markerFuture.paint.color===d.cfg.X&&!markerFuture.paint.mark,'a prior visit cannot color a different future window green');
   ck(markerUnknown.paint.dashed&&!['✓','×'].includes(markerUnknown.paint.mark),'unknown visit cannot get a success or failure color');
   ck(markerYes.time===302.5&&markerYes.u>=.1&&markerYes.u<.2,'green circle is inside the witnessing M5 and its own price cell');
   ck(markerYes.targetKey!==markerFuture.targetKey,'same price with a different window is a different fact target');
   ck(markerYes.targetKey!==d.targetMarker({...frame,e0t:100},ctx(305,[bar(300,true)]),'X',z).targetKey&&markerYes.targetKey===d.targetMarker(frame,ctx(310,[bar(300,true),bar(305,false)]),'X',z).targetKey,'target identity changes with its physical price frame and stays fixed across cuts of that same target');
   ck(d.bandPaint('X',true,true).fill===d.cfg.projX&&!d.bandPaint('X',true,true).mark,'full-horizon band keeps its X role and never inherits a narrow visit badge');
   ck(d.bandPaint('X',false,true).state==='IMPOSSIBLE'&&d.bandPaint('X',false,true).fill!==d.cfg.projX,'gray band is reserved for its own impossible final extreme');
   ck(d.bandPaint('X',true,false).state==='UNKNOWN'&&d.bandPaint('X',true,false).fill===d.cfg.projX,'unknown reachability is not asserted impossible');
   ck(d.colorBindings.version==='23.5-color-1'&&d.colorBindings.marker.scope==='exact_price_time_target','rendering exposes its versioned semantic ownership map');
   const futurePaint=d.visitPaint('X',{state:'PENDING',start:330},5,true,320);
   const openPaint=d.visitPaint('X',{state:'PENDING',start:330},5,true,335);
   const pastPaint=d.visitPaint('X',{state:'UNMARKED'},0,true,420);
   const visitedPaint=d.visitPaint('X',{state:'VISITED'},0,false,420);
   const missedPaint=d.visitPaint('X',{state:'MISSED'},0,true,420);
   ck(futurePaint.state==='FUTURE'&&futurePaint.mark==='○'&&openPaint.state==='OPEN'&&openPaint.mark==='●','future and open windows differ without moving their boundaries');
   ck(pastPaint.state==='PAST'&&pastPaint.mark!=='✓','a clock-only zone annotation is not a successful visit');
   ck(visitedPaint.mark==='✓'&&visitedPaint.markColor===d.cfg.visitC&&visitedPaint.text!==d.cfg.visitC,'green visit check is separate from readable historical percentage');
   ck(missedPaint.mark==='×'&&!missedPaint.active,'an expired unvisited window never gets a success check');
   ck(d.visitPaint('X',{state:'UNMARKED'},5,true,320).mark==='','a band without one named window has no open-window symbol');
   if(real){
    const passport=d.passports().find(p=>p.estimand==='EST:B-ZONE-X'&&p.params.zone_id===real.zone_id);
    const cell=real.cell_mask.find(([,b])=>F.f+15*b+15>F.act0);
    if(!passport||!cell)throw Error('missing discriminating zone witness');
    const [k,b]=cell,T=Math.max(F.act0+5,F.f+15*b+5),price=F.u2p((k+.5)/10);
    const hitCtx={...d.cur(),live:false,obs:T,D:{...d.cur().D,bars:[{t:T-5,o:price,h:price,l:price,c:price}]}};
    const known=d.visitState(F,hitCtx,null,null,real);let blocked;
    const prior=passport.violation;
    try{passport.violation='test withheld zone';blocked=d.visitState(F,hitCtx,null,null,real);}finally{passport.violation=prior;}
    ck(known.state==='VISITED'&&blocked.state==='WITHHELD','an observed contact cannot certify a zone whose own passport was withheld');
   }
   const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
   const lum=a=>a.map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
   const contrast=(fg,bg,alpha=1)=>{const b=rgb(bg),l=lum(rgb(fg).map((x,i)=>x*alpha+b[i]*(1-alpha))),r=lum(b);return (Math.max(l,r)+.05)/(Math.min(l,r)+.05);};
   const paints=[futurePaint,openPaint,pastPaint,visitedPaint,missedPaint];
   ck(paints.every(p=>contrast(p.text,'#0B0C10')>=4.5&&contrast(p.markColor,'#0B0C10')>=4.5),'all status numbers and symbols meet 4.5:1 on the column background');
   ck(d.cfg.projA===90&&d.cfg.passedA===30&&new Set(d.V.projBars.filter(p=>p.visible).map(p=>Math.round(p.futureA*1000))).size>1,'screen 24 graded ambient shading replaces the former universal 3:1 ambient-fill rule (operator 22.10)');
   const labels=d.V.projLabels, col=d.V.proj;
   ck(d.V.projBars.every(p=>p.earlier+p.later===p.n&&!p.paint.mark),'whole band mass is preserved and no narrower fact is attached to its percentage');
   ck(d.V.projBars.filter(p=>p.ev==='R').every(r=>{const x=d.V.projBars.find(p=>p.ev==='X'&&p.k===r.k);return !x||x.x0-r.x1>=5.99;}),'R and X have a visible gap and independently owned percentages');
   ck(labels.length>0&&labels.every(l=>l.fs>=8&&l.box[0]>=col.x&&l.box[0]+l.box[2]<=col.x+col.w),'screen 24 quiet numbers fit the column; exact values remain available on hover');
   ck(labels.every((l,i)=>labels.slice(i+1).filter(q=>q.ev===l.ev).every(q=>Math.abs((l.box[1]+l.box[3]/2)-(q.box[1]+q.box[3]/2))>=(l.box[3]+q.box[3])/2)),'column numbers do not overlap on either event side');
   ck(!d.contract().violations.length,'no contract violations');
   return done;
  });
  const ui=await evaluate(B.cdp,code=>(0,eval)(code),fs.readFileSync('tests/ui_check24.js','utf8'));
  if(ui.problems.length)throw Error(JSON.stringify(ui.problems));
  results.push({viewport:[width,height],checks:check.length,ui_problems:ui.problems});
  console.log('PASS visit facets '+width+'x'+height+' '+check.length+' checks; ui_check24 problems: []');
  if(today){
   let identity=null;
   for(const [cut,expected,name] of [['05:05','PENDING','before'],['05:10','VISITED','visited'],['07:30','VISITED','active-window'],['08:00','VISITED','three-states']]){
    await open('#inst=NQ&session=ODR&at='+cut);
    const scene=await evaluate(B.cdp,({expected,cut})=>{
     const d=window.__d24, c=d.cur(), F=c.F, z=F.zones.X.zones.find(z=>z.label==='X1');
     if(d.A.day.date!=='2026-10-20'||!z)throw Error('the optional live witness is specifically 20.10.2026');
     const v=d.visitState(F,c,null,null,z);
     if(v.state!==expected||expected==='VISITED'&&v.t!==310)throw Error('today X1: '+JSON.stringify(v));
     if(cut==='08:00'){
      const x2=F.zones.X.zones.find(z=>z.label==='X2'),r2=F.zones.R.zones.find(z=>z.label==='R2');
      if(d.visitState(F,c,null,null,x2).state!=='MISSED'||d.visitState(F,c,null,null,r2).state!=='PENDING')throw Error('three distinct visit states');
     }
     d.st.panel=true;d.st.hover={k:'zone',ev:'X',i:F.zones.X.zones.indexOf(z)};d.render(true);
     if(expected==='VISITED'&&(d.V.lk.marker.visit.state!=='VISITED'||d.V.lk.marker.paint.color!==d.cfg.visitC))throw Error('zone check and circle must share the visit target');
     return {state:v.state,t:v.t,N:F.N,identity:JSON.stringify([F.r.family_id,F.r.snapshot_id,F.r.counts,F.r.zones])};
    },{expected,cut});
    if(identity&&identity!==scene.identity)throw Error('a visit or clock changed the baseline family');identity=scene.identity;
    await shot(width+'-'+name);
    console.log('PASS today '+cut+' X1 '+scene.state+' N='+scene.N);
   }
   await evaluate(B.cdp,()=>{
    const d=window.__d24,F=d.cur().F,i=F.zones.X.zones.findIndex(z=>z.label==='X2');
    d.st.hover={k:'zone',ev:'X',i};d.render(true);
    if(d.V.lk.marker.visit.state!=='MISSED'||d.V.lk.marker.paint.color!==d.cfg.visitMissC)throw Error('missed zone check and circle do not share the red outcome');
    const z=F.zones.X.zones[i],visible=z.cell_mask.some(([k,b])=>{const x=d.V.X(F.f+15*b+7.5),y=d.V.Y(F.u2p((k+.5)/10));return x>=8&&x<=d.V.plot.w-8&&y>=48&&y<=d.V.plot.h-8;});
    let y=d.V.Y(F.u2p(d.V.lk.marker.u));
    if(visible&&(y<48||y>d.V.plot.h-8))throw Error('a missed zone with visible own cells hides its red marker outside the frame');
    const prices=z.cell_mask.flatMap(([k])=>[F.u2p(k/10),F.u2p((k+1)/10)]),pad=(d.V.p1-d.V.p0)*.1;
    d.st.auto=false;d.st.p0=Math.min(d.V.p0,...prices)-pad;d.st.p1=Math.max(d.V.p1,...prices)+pad;d.render(true);
    y=d.V.Y(F.u2p(d.V.lk.marker.u));
    if(y<48||y>d.V.plot.h-8||d.V.lk.marker.paint.color!==d.cfg.visitMissC)throw Error('red marker is not visible when the exact missed target is in view');
   });
   await shot(width+'-missed-window');
   await open('#inst=YM&session=RDR&at=11:35');
   const ym=await evaluate(B.cdp,()=>{
    const d=window.__d24,F=d.cur().F;
    d.st.hover={k:'pcell',ev:'X',k0:4,k1:5,src:'proj'};d.render(true);
    const p=d.V.projBars.find(p=>p.ev==='X'&&p.k===4),r=d.V.projBars.find(p=>p.ev==='R'&&p.k===4),lk=d.V.lk;
    if(F.N!==157||p.n!==14||p.earlier!==4||p.later!==10||p.paint.fill!==d.cfg.projX||p.paint.mark)throw Error('YM 8.9% inherited an unrelated early window');
    if(lk.b!==9||lk.n!==2||lk.marker.visit.state!=='PENDING'||lk.marker.paint.color!==d.cfg.X)throw Error('12:45 peak marker does not own its future window');
    if(!r||r.n!==1||p.x0-r.x1<5.99)throw Error('YM R 0.6 and X 8.9 are not visibly separated');
    const inspector=document.querySelector('#insp').textContent;
    if(!inspector.includes('12:45–13:00')||inspector.includes('эта полоса внутри X1'))throw Error('inspector still binds to another target');
    return {N:F.N,n:p.n,earlier:p.earlier,later:p.later,peakN:lk.n};
   });
   await shot(width+'-ym-8-9');
   console.log('PASS YM 8.9% exact scope '+JSON.stringify(ym));
   await evaluate(B.cdp,()=>{const d=window.__d24;d.st.hover={k:'zone',ev:'X',i:0};d.render(true);if(d.V.lk.marker.paint.color!==d.cfg.visitC)throw Error('YM visited constellation circle is not green');});
   await shot(width+'-ym-visited');
  }
 }
 fs.mkdirSync('lab/.runtime/final-checks',{recursive:true});
 fs.writeFileSync('lab/.runtime/final-checks/visit-states.json',JSON.stringify({base,results},null,2)+'\n');
 console.log('ALL GOOD');
}finally{await B.close();}
