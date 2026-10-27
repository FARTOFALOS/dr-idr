// Live page verification of the approved time-first plan. The image must be driven by the same registered joint
// cells, peak targets, core memberships and post-L witnesses, including interactions and failure withdrawal.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8795',b=await startChrome(),checks=[],errors=[],out='lab/.runtime/time-sd235-page';
fs.mkdirSync(out,{recursive:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const ck=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);console.log('PASS '+name);};
b.cdp.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
await b.cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__arcs=[];const original=CanvasRenderingContext2D.prototype.arc;CanvasRenderingContext2D.prototype.arc=function(...p){if(this.canvas.id==='cv')window.__arcs.push(p);return original.apply(this,p);};`});
const fragment='#date=2025-12-17&inst=NQ&session=RDR&at=11:10';
async function ready(){
 for(let i=0;i<400;i++){
  const s=await evaluate(b.cdp,()=>{const d=window.__d24,p=d?.pullbacks?.();return {ready:!!d?.timeSd?.().data&&p&&!p.pending&&d.V.projBars?.length&&!d.contract().unchecked,error:p?.error};});
  if(s.error)throw Error(s.error);if(s.ready)return;await pause(150);
 }
 throw Error('time-SD page did not settle');
}
async function open(url){await b.cdp.send('Page.navigate',{url:'about:blank'});await b.cdp.send('Page.navigate',{url});await ready();}
async function shot(name){const s=await b.cdp.send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(out+'/'+name+'.png',Buffer.from(s.data,'base64'));}
const signature=()=>{const d=window.__d24,F=d.cur().F;return JSON.stringify([F.r.family_id,F.r.snapshot_id,F.N,F.r.members,F.r.zones]);};
try{
 for(const [width,height]of [[1600,900],[1920,1000]]){
  await b.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await open(base+'/23-5/'+fragment);
  const state=await evaluate(b.cdp,()=>{
   const d=window.__d24,F=d.mapContext().F,t=d.timeSd().data,p=d.pullbacks().packet;
   window.__arcs=[];d.render(true);
   const all=['R','X'];
   const counts=all.every(ev=>[...F.ev[ev].P].every(([k,n])=>n===t.maps[ev].price_peaks.find(v=>v.index===k)?.n_known)&&[...F.ev[ev].T].every(([k,n])=>n===t.maps[ev].time_peaks.find(v=>v.index===k)?.n_known));
   const differs=t.maps.R.price_peaks.some(v=>{const old=p.proof.marginals[String(t.scale)].find(q=>q.k0===v.k0&&q.k1===v.k1&&q.b0==null&&q.b1==null);return old?.n_known>v.n_known;});
   const cores=all.every(ev=>t.maps[ev].cores.every(z=>z.time_end-z.time_start===15&&z.price_high-z.price_low===3&&new Set(z.members).size===z.n_known));
   const drawn=d.V.stars||[],nodes=Object.fromEntries(all.map(ev=>[ev,drawn.filter(q=>q.ev===ev).length]));
   const everyCore=all.every(ev=>t.maps[ev].cores.every(z=>{const raw=t.maps[ev].points.filter(q=>q.k>=z.k0&&q.k<z.k1&&q.b===z.b0);const visible=raw.some(q=>d.V.X(q.open+2.5)>=0&&d.V.X(q.open+2.5)<=d.V.plot.w&&d.V.Y(F.u2p(q.v/p.proof.sessions.find(w=>w.id===q.case).w))>=0&&d.V.Y(F.u2p(q.v/p.proof.sessions.find(w=>w.id===q.case).w))<=d.V.plot.h);return !visible||drawn.some(s=>s.ev===ev&&s.q.k>=z.k0&&s.q.k<z.k1&&s.q.b===z.b0);}));
   const glyphLimit=all.every(ev=>t.maps[ev].cores.every(z=>drawn.filter(s=>s.ev===ev&&s.q.k>=z.k0&&s.q.k<z.k1&&s.q.b===z.b0).length<=9));
   const arcs=drawn.every(s=>window.__arcs.some(a=>Math.abs(a[0]-s.x)<1e-7&&Math.abs(a[1]-s.y)<1e-7));
   const clocks=d.V.projBars.every(q=>{const v=t.maps[q.ev].price_peaks.find(v=>v.index===q.k);return q.n===v.n_known&&q.earlier===v.earlier&&q.later===v.later;});
   const trace=d.timeSd().trace;
   const own=trace.every(q=>q.estimand.startsWith('EST:TS-')&&q.N===F.N&&p.contract.bundles.some(x=>x.id===q.bundle&&x.estimand===q.estimand));
   return {counts,clocks,differs,cores,everyCore,glyphLimit,arcs,nodes,own,trace:trace.length,N:F.N,pw:d.V.projW,mode:d.st.mode,phase:d.phaseOf(F,d.cur()),violations:d.contract().violations,header:document.querySelector('.p24-nowblk .p21-h')?.innerText,title:document.title};
  });
  ck(state.mode==='bounds'&&state.title.includes('23.5')&&state.pw===116,width+': existing bounds layout and 116px price column retained');
  ck(state.counts&&state.differs,width+': displayed projections use peaks of joint cells, not the retired whole-session PB marginals');
  ck(state.clocks,width+': price-bar early and late masses match the selected joint cell even when today makes FINAL-X impossible');
  ck(state.cores,width+': every constellation has exactly its declared local time and SD extent');
  ck(state.everyCore&&state.glyphLimit&&state.arcs&&state.nodes.R>1&&state.nodes.X>1,width+': real canvas draws compact witnessed constellations, at most nine M5/SD representatives per core');
  ck(state.own&&state.trace>20&&!state.violations.length,width+': visible numbers use their own TS passports and preserve the full N');
  ck(state.phase===null&&state.header.includes('итоговые R/X'),width+': final-extreme context is named and its phase cannot control the PB map');
  await shot(width+'-bounds');
  const baseSignature=await evaluate(b.cdp,signature);
  for(const ev of ['R','X']){
   const hover=await evaluate(b.cdp,ev=>{
    const d=window.__d24,F=d.mapContext().F,m=d.timeSd().data.maps[ev];
    const peak=m.price_peaks.find(v=>d.V.projBars.some(q=>q.ev===ev&&q.k===v.index));
    d.st.pin=null;d.st.hover={k:'pbpcell',ev,k0:peak.index,k1:peak.index+1,src:'proj'};d.render(true);
    const exact=['R','X'].every(e=>F.ev[e].pts.every(q=>d.emphOf(q,{k:'pcell',ev,k0:peak.index,k1:peak.index+1},F,d.cur())===(e===ev&&q.k===peak.k0&&q.b===peak.b0)));
    return {peak,exact,link:d.V.lk,text:document.getElementById('insp').innerText,est:document.querySelector('#insp [data-ts-est]')?.dataset.tsEst};
   },ev);
   ck(hover.exact&&hover.link?.b===hover.peak.b0&&hover.link.k0===hover.peak.k0&&hover.est==='EST:TS-PEAK-'+ev,width+': '+ev+' price hover lights only the same exact joint cell as its number');
   const timeHover=await evaluate(b.cdp,ev=>{const d=window.__d24,p=d.timeSd().data.maps[ev].time_peaks[0];d.st.hover={k:'pbtcell',ev,b0:p.index,b1:p.index+1,src:'strip'};d.render(true);return {peak:p,link:d.V.lk,est:document.querySelector('#insp [data-ts-est]')?.dataset.tsEst};},ev);
   ck(timeHover.link?.k0===timeHover.peak.k0&&timeHover.link.b===timeHover.peak.b0&&timeHover.est==='EST:TS-PEAK-'+ev,width+': '+ev+' time hover identifies the same exact SD cell as its number');
   const core=await evaluate(b.cdp,ev=>{const d=window.__d24;d.st.hover=null;d.st.pin={k:'pbzone',ev,i:0};d.st.detPin=true;d.render(true);return {cards:document.querySelectorAll('#detg .dcard').length,body:document.querySelector('#detg .dbody')?.innerText,est:document.querySelector('#insp [data-ts-est]')?.dataset.tsEst,errors:d.contract().violations};},ev);
   ck(core.cards===6&&core.body?.length>0&&core.est==='EST:TS-CORE-'+ev&&!core.errors.length,width+': '+ev+' core pins into the existing inspector and six detail windows');
  }
  const point=await evaluate(b.cdp,()=>{const d=window.__d24,s=d.V.stars.find(s=>s.ev==='R');d.st.pin={k:'pbpt',id:s.q.pbid,same:1};d.st.hover=null;d.render(true);return {id:s.q.pbid,text:document.getElementById('insp').innerText,episodes:document.querySelectorAll('#insp [data-pb-episode]').length,body:document.querySelector('#detg .dbody')?.innerText};});
  ck(point.episodes>0&&point.text.includes('M5')&&point.body?.length>0,width+': compact star still opens its actual H/L/B episode witnesses');
  await shot(width+'-witness');
  const finalContext=await evaluate(b.cdp,()=>{const d=window.__d24,s=d.V.stars.find(s=>s.ev==='X');d.st.pin={k:'pt',ev:'X',i:s.q.i,q:s.q};d.render(true);return document.getElementById('insp').innerText;});
  ck(finalContext.includes('Окончательный откат')&&finalContext.includes('Окончательное расширение'),width+': X witness names its paired final R explicitly, without presenting it as local PB');
  await evaluate(b.cdp,()=>{const d=window.__d24;d.st.detPin=false;d.st.pin=d.st.hover=null;d.st.area={ev:'X',k0:1,k1:4,b0:0,b1:2};d.render(true);});await ready();
  const area=await evaluate(b.cdp,()=>{const d=window.__d24,p=d.pullbacks().packet.proof,t=p.time_sd,F=d.mapContext().F;const v=t.maps.X.regions.find(v=>v.k0===1&&v.k1===4&&v.b0===0&&v.b1===2);return {n:v?.n_known,want:new Set(t.maps.X.points.filter(q=>q.k>=1&&q.k<4&&q.b>=0&&q.b<2).map(q=>q.case)).size,N:F.N,violations:d.contract().violations};});
  ck(area.n===area.want&&area.N===state.N&&!area.violations.length,width+': selected X area reaches its own TS region calculation');
  await evaluate(b.cdp,()=>{const d=window.__d24;d.st.area=null;d.st.pin={k:'pbzone',ev:'R',i:0};d.st.hover=null;d.render(true);});await ready();
  const before=await evaluate(b.cdp,()=>{const d=window.__d24,t=d.timeSd().data;return JSON.stringify(['R','X'].map(e=>t.maps[e].cores.map(z=>[z.zone_id,z.members,z.cell_mask])));});
  await b.cdp.send('Runtime.evaluate',{expression:"document.querySelector('[data-step=\"5\"]').click()"});await ready();
  const after=await evaluate(b.cdp,()=>{const d=window.__d24,t=d.timeSd().data;return {map:JSON.stringify(['R','X'].map(e=>t.maps[e].cores.map(z=>[z.zone_id,z.members,z.cell_mask]))),pin:d.st.pin?.k,cut:d.pullbacks().packet.proof.context.cut};});
  ck(before===after.map&&after.pin==='pbzone'&&after.cut===675,width+': next closed M5 preserves core identities and the pin');
  // Other modes still use their original, named questions; they do not turn final extrema into PB episodes.
  for(const mode of ['path','continuations','bounds']){await b.cdp.send('Runtime.evaluate',{expression:`document.querySelector('[data-m="${mode}"]').click()`});if(mode==='bounds')await ready();}
  ck((await evaluate(b.cdp,signature))===baseSignature,width+': family/BASE labels survive mode changes unchanged');
  const errs=await evaluate(b.cdp,()=>window.__d24.contract().violations);ck(!errs.length,width+': no accepted-contract mismatch after interactions');
 }
 for(const scene of [['ES','ODR','2025-11-12','05:00'],['YM','ADR','2025-10-08','22:00'],['NQ','RDR','2025-12-10','14:30'],['NQ','RDR','2025-12-17','11:10','all']]){
  const [inst,session,date,at,scope='weekday']=scene;await open(base+`/23-5/#inst=${inst}&session=${session}&date=${date}&at=${at}&scope=${scope}`);
  const s=await evaluate(b.cdp,()=>{const d=window.__d24,t=d.timeSd().data;return {ok:['R','X'].every(e=>t.maps[e].cores.every(z=>z.b1-z.b0===1&&z.k1-z.k0===3)),error:d.pullbacks().error,violations:d.contract().violations};});
  ck(s.ok&&!s.error&&!s.violations.length,scene.join(' ')+': same finite geometry and contract in another frame');
 }
 // Corrupt only this disposable browser's response, after a valid release was visible.
 await open(base+'/23-5/'+fragment);
 await evaluate(b.cdp,()=>{const original=window.fetch;window.fetch=async function(...args){const r=await original(...args);if(!String(args[0]).includes('/api/integration/time-sd?'))return r;const p=await r.json();p.proof.time_sd.maps.R.cores[0].n_known++;return new Response(JSON.stringify(p),{status:200,headers:{'Content-Type':'application/json'}});};document.querySelector('[data-step="5"]').click();});
 let withdrawn;
 for(let i=0;i<400;i++){withdrawn=await evaluate(b.cdp,()=>{const d=window.__d24,p=d.pullbacks(),F=d.mapContext().F;return {error:p.error,pending:p.pending,packet:!!p.packet,cores:F.zones.R.zones.length+F.zones.X.zones.length,projection:F.ev.R.P.size+F.ev.X.P.size,baseN:d.cur().F.N,drawn:d.V.stars?.length||0,candles:!!d.cur().D.bars?.length};});if(withdrawn.error&&!withdrawn.pending)break;await pause(150);}
 ck(!!withdrawn.error&&!withdrawn.packet&&!withdrawn.cores&&!withdrawn.projection&&!withdrawn.drawn&&withdrawn.baseN>0,'corrupt response withdraws the new map and projections together, without substituting the old 24 map');
 await shot('fault-withdrawal');
 ck(!errors.length,'no browser exceptions throughout both sizes, instruments, frames and interactions');
 fs.writeFileSync(out+'/RESULT.json',JSON.stringify({status:'PASS',checks,errors,base},null,2)+'\n');
 console.log('ALL GOOD '+checks.length);
}finally{await b.close();}
