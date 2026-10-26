// Installed 23.5: a new event reaches its constellation, its scale-bound witness and the desktop launch.
// node tests/pullbacks235_page.mjs http://127.0.0.1:8735 http://127.0.0.1:8767
import fs from 'node:fs';
import {startChrome, evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8735', baseline=process.argv[3]||'http://127.0.0.1:8767';
const B=await startChrome(), errors=[], results=[], coverage=[];
const sleep=ms=>new Promise(ok=>setTimeout(ok,ms));
const out='lab/.runtime/final-checks/pullbacks235', shots='spec/ekran-23-5/img/bounds';
fs.mkdirSync(out,{recursive:true}); fs.mkdirSync(shots,{recursive:true});
B.cdp.on('Runtime.exceptionThrown',ev=>errors.push(ev.exceptionDetails.exception?.description||ev.exceptionDetails.text));
const ck=(ok,name)=>{if(!ok)throw Error(name);results.push(name);console.log('PASS '+name);};
async function ready(){
 for(let n=0;n<320;n++){
  const s=await evaluate(B.cdp,()=>{const d=window.__d24,p=d?.pullbacks();const zones=p?.packet?.proof.maps[String(p.scale)].zones||[];return {ready:!!p?.packet&&p.mode&&!p.pending&&(!zones.length||d.V.zoneHit?.some(z=>z.ev==='R')),error:p?.error};});
  if(s.error)throw Error(s.error); if(s.ready)return; await sleep(150);
 }
 throw Error('pullback page did not settle');
}
async function open(fragment){
 await B.cdp.send('Page.navigate',{url:'about:blank'}); await sleep(100);
 await B.cdp.send('Page.navigate',{url:base+(process.env.DR_LAB_VIEW_PATH||'/23-5/')+fragment}); await ready();
}
async function shot(name){
 const s=await B.cdp.send('Page.captureScreenshot',{format:'png'});
 fs.writeFileSync(shots+'/'+name+'.png',Buffer.from(s.data,'base64'));
}
const fragment='#date=2025-12-17&inst=NQ&session=RDR&at=11:10&mode=pullbacks&pbscale=1';
try{
 const launcher=fs.readFileSync('start-dr-lab-23-5.ps1','utf8');
 ck(launcher.includes("$Page = '23-5/#trial=pullbacks&pbscale=1'"),'desktop launcher opens the chosen scale-1 pullback view');
 for(const [width,height] of [[1600,900],[1920,1000]]){
  await B.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await open(fragment);
  const state=await evaluate(B.cdp,()=>{
   const d=window.__d24, r=d.pullbacks().packet, p=r.proof, v=d.V;
   const zones=p.maps['1'].zones;
   return {mode:d.pullbacks().mode,scale:d.pullbacks().scale,N:p.context.N,family:p.context.family_id,
    zones:zones.map(z=>({id:z.zone_id,n:z.n_known,cells:z.cell_mask})),knownPoints:p.points.length,
    drawn:d.pbGeom().zones.reduce((s,z)=>s+z.pts.length,0),bound:d.cur().F.zones.R.zones.map(z=>({n:z.n,cells:z.cell_mask})),layout:{mode:d.st.mode,price:d.V.projW,band:d.V.bandH,events:[...new Set(d.V.zoneHit.map(z=>z.ev))],caps:[...new Set(d.V.caps.map(z=>z.ev))],rows:[...new Set(d.V.projBars.map(z=>z.ev))],extraButton:!document.querySelector('[data-m="pullbacks"]').hidden},
    bundles:r.contract.bundles.length,errors:d.contract().violations,integrity:d.contract().integrity,
    title:document.title,panel:document.getElementById('panel').innerText,compare:document.querySelector('[data-compare24]')?.href,
    toolbarOverflow:document.getElementById('tb').scrollWidth-document.getElementById('tb').clientWidth,
    canvas:[v.W,v.H],frame:[v.plot.w,v.plot.h]};
  });
  ck(state.mode&&state.scale===1&&state.title.includes('23.5'),width+': named 23.5 pullback view and chosen scale are active');
  const compare=new URL(state.compare), cq=new URLSearchParams(compare.hash.slice(1));
  ck(compare.port==='8767'&&cq.get('inst')==='NQ'&&cq.get('session')==='RDR'&&cq.get('date')==='2025-12-17'&&cq.get('at')==='11:10'&&cq.get('scope')==='weekday',
     width+': comparison link opens 24 with the same instrument, date, block, closed M5 and family scope');
  ck(state.bundles>0&&state.errors.length===0&&state.integrity.length===0,width+': published numbers pass the page contract');
  ck(state.layout.mode==='bounds'&&state.layout.price===176&&state.layout.band>0&&!state.layout.extraButton&&['R','X'].every(ev=>state.layout.events.includes(ev)&&state.layout.caps.includes(ev)&&state.layout.rows.includes(ev)),width+': shared bounds view keeps both constellations, bottom capsules and price columns');
  ck(state.drawn>0&&state.zones.length>0,width+': the new historical bottoms are actually drawn');
  ck(JSON.stringify(state.zones.map(z=>[z.n,z.cells]))!==JSON.stringify(state.bound.map(z=>[z.n,z.cells])),width+': the local-cycle map differs from final R in its counts or location');
  ck(state.toolbarOverflow<=11,width+': date and cut stay within the toolbar');
  ck(!state.panel.includes('завершённого отката здесь нет'),width+': unestablished completion is not stated as absence');
  const unions=await evaluate(B.cdp,()=>{
   const d=window.__d24,p=d.pullbacks().packet.proof,s=d.pullbacks().scale,pts=p.points.filter(q=>q.kt>=s),F=d.mapContext().F,sl=p.context.cut;
   const price=[...F.ev.R.P].every(([k,n])=>new Set(pts.filter(q=>q.k===k).map(q=>q.case)).size===n);
   const time=[...F.ev.R.T].every(([b,n])=>new Set(pts.filter(q=>q.b===b).map(q=>q.case)).size===n);
   const clock=d.V.projBars.filter(q=>q.ev==='R').every(v=>{const qs=pts.filter(q=>q.k===v.k),yes=new Set(qs.map(q=>q.case)),later=new Set(qs.filter(q=>q.open+5>sl).map(q=>q.case));return v.n===yes.size&&v.earlier===yes.size-later.size&&v.later===later.size;});
   const noFinalRule=d.zoneStatus(F,d.cur(),'R').every(s=>s!=='IMPOSSIBLE'&&s!=='HOLDS');
   const labels=d.V.projLabels.every(q=>q.box[0]>=d.V.proj.x&&q.box[0]+q.box[2]<=d.V.proj.x+d.V.proj.w);
   return {price,time,clock,noFinalRule,labels,multiple:pts.length>new Set(pts.map(q=>q.case)).size};
  });
  ck(Object.values(unions).every(Boolean),width+': new price/time shares deduplicate sessions, clock colours use new bottoms, labels fit, and final-R constraints do not leak into L');
  for(const mode of ['path','continuations','bounds']){
   await B.cdp.send('Runtime.evaluate',{expression:`document.querySelector('[data-m="${mode}"]').click()`});
   if(mode==='bounds')await ready();
  }
  ck(await evaluate(B.cdp,()=>{const d=window.__d24;return d.pullbacks().mode&&d.V.caps.some(z=>z.ev==='R')&&d.V.caps.some(z=>z.ev==='X');}),width+': return from path and continuation tabs preserves both constellation layers');
  const cell=await evaluate(B.cdp,()=>{const d=window.__d24,v=d.V.projBars.find(v=>v.ev==='R'&&v.n>10);const r=document.getElementById('cv').getBoundingClientRect();return {x:r.x+(v.x0+v.x1)/2,y:r.y+(v.top+v.bot)/2,k:v.k};});
  for(const type of ['mouseMoved','mousePressed','mouseReleased'])await B.cdp.send('Input.dispatchMouseEvent',{type,x:cell.x,y:cell.y,button:type==='mouseMoved'?'none':'left',clickCount:type==='mouseMoved'?0:1});
  await ready();
  const area=await evaluate(B.cdp,()=>{const d=window.__d24,p=d.pullbacks().packet.proof,a=d.st.area;return {a,r:a&&p.marginals[String(d.pullbacks().scale)].find(v=>v.k0===a.k0&&v.k1===a.k1&&v.b0===null&&v.b1===null),N:p.context.N};});
  ck(area.a?.k0===cell.k&&area.r?.members.length===area.r?.n_known,width+': the original price-column click selects the new typed region with verified unique-session counts');
  await B.cdp.send('Runtime.evaluate',{expression:`document.querySelector('[data-clear="area"]').click()`});await ready();
  await shot(width+'-nq-rdr');

  const pin=await evaluate(B.cdp,()=>{
   const d=window.__d24,p=d.pullbacks().packet.proof,E=new Map(p.episodes.map(e=>[e.id,e]));
   const visible=d.pbGeom().zones.flatMap(z=>z.pts.map(x=>x.q));
   const q=visible.find(q=>q.episodes.some(id=>E.get(id).kt<1))||visible[0];
   d.st.hover=null;d.st.pin={k:'pbpt',id:q.id,same:1};d.render(true);
   const actual=[...document.querySelectorAll('#insp [data-pb-episode]')].map(el=>el.dataset.pbEpisode);
   const expected=q.episodes.filter(id=>E.get(id).kt>=1);
   const drLinks=[...document.querySelectorAll('#insp [data-pb-dr-for]')].map(el=>el.dataset.pbDrFor);
   return {actual,expected,drLinks,excluded:q.episodes.length-expected.length,text:document.getElementById('insp').innerText};
  });
  ck(JSON.stringify(pin.actual)===JSON.stringify(pin.expected),width+': hover exposes only vertices established at this scale');
  ck(JSON.stringify(pin.drLinks)===JSON.stringify(pin.expected),width+': DR order is shown separately for every displayed H/B link');
  ck(pin.text.includes('между M5 дна и обновления'),width+': M5-label spacing is named without exact intrabar duration');
  await shot(width+'-nq-witness');

  const before=await evaluate(B.cdp,()=>{
   const p=window.__d24.pullbacks().packet.proof;
   return JSON.stringify([p.context.family_id,p.points,p.maps]);
  });
  await B.cdp.send('Runtime.evaluate',{expression:"document.querySelector('[data-step=\"5\"]').click()"});await ready();
  const after=await evaluate(B.cdp,()=>{
   const d=window.__d24,p=d.pullbacks().packet.proof;
   return {history:JSON.stringify([p.context.family_id,p.points,p.maps]),cut:p.context.cut,pinned:d.st.pin?.k};
  });
  ck(before===after.history&&after.cut===675&&after.pinned==='pbpt',width+': next M5 keeps the same historical map and pinned witness');

  for(const scale of [2,3,6]){
   await B.cdp.send('Runtime.evaluate',{expression:`document.querySelector('[data-pbscale="${scale}"]').click()`});
   const check=await evaluate(B.cdp,()=>{
    const d=window.__d24,p=d.pullbacks().packet.proof,s=d.pullbacks().scale,E=new Map(p.episodes.map(e=>[e.id,e]));
    const visible=d.pbGeom().zones.flatMap(z=>z.pts.map(x=>x.q));
    const q=visible.find(q=>q.episodes.some(id=>E.get(id).kt<s))||visible[0];
    if(!q)return {scale:s,empty:true,expected:[],actual:[],excluded:0};
    d.st.pin={k:'pbpt',id:q.id,same:1};d.st.hover=null;d.render(true);
    const expected=q.episodes.filter(id=>E.get(id).kt>=s);
    return {scale:s,expected,actual:[...document.querySelectorAll('#insp [data-pb-episode]')].map(el=>el.dataset.pbEpisode),excluded:q.episodes.length-expected.length};
   });
   ck(check.scale===scale&&JSON.stringify(check.actual)===JSON.stringify(check.expected),width+': scale '+scale+' changes point witnesses together with selection');
   if(check.excluded)coverage.push({width,scale,excluded_links:check.excluded});
  }
 }
 ck(coverage.length>0,'real shared-bottom counterexample exercises the scale-filter repair');
 for(const scene of [
  ['ES','ODR','2025-11-12','05:00'],['YM','ADR','2025-10-08','22:00'],['NQ','RDR','2025-12-10','14:30']]){
  const [inst,session,date,at]=scene;
  await open(`#inst=${inst}&session=${session}&date=${date}&at=${at}&mode=pullbacks&pbscale=1`);
  const check=await evaluate(B.cdp,()=>{
   const d=window.__d24,p=d.pullbacks().packet.proof;
   return {N:p.context.N,frame:p.context.view,violations:d.contract().violations,error:d.pullbacks().error};
  });
  ck(check.N>0&&!check.error&&!check.violations.length,scene.join(' ')+': own instrument, block and frame produce a checked view');
 }
 await open('#inst=NQ&session=RDR&date=2025-12-17&at=15:55&mode=pullbacks&pbscale=1');
 const last=await evaluate(B.cdp,()=>{
  const p=window.__d24.pullbacks().packet.proof;
  return {known:p.today.episodes.filter(e=>e.status==='KNOWN'&&e.kt>=1).length,text:document.getElementById('ev').innerText};
 });
 ck(last.known>0&&last.text.includes('R')&&last.text.includes('X')&&!last.text.includes('L'),
    'completed episodes remain in the proof while the original R/X header is preserved');
 const query='/api/d24/family?instrument=NQ&session=RDR&date=2025-12-17&at=670';
 const [old,current]=await Promise.all([baseline,base].map(async x=>(await fetch(x+query)).json()));
 ck(JSON.stringify([old.family_id,old.snapshot_id,old.N,old.counts,old.members,old.zones])===
    JSON.stringify([current.family_id,current.snapshot_id,current.N,current.counts,current.members,current.zones]),
   '24 and 23.5 retain identical accepted family, final R/X and their zones for the comparison scene');
 ck(await evaluate(B.cdp,()=>{const c=window.__d24.cfg;return c.shading24_235&&c.projA===90&&c.passedA===30;}),'screen 24 shading preset replaces the superseded flat-contrast preset');
 ck(errors.length===0,'no browser exceptions throughout both sizes, scales, instruments and frames');
 fs.writeFileSync(out+'/browser.json',JSON.stringify({base,baseline,results,coverage,errors},null,2)+'\n');
 console.log('ALL GOOD '+results.length+' checks');
}finally{await B.close();}
