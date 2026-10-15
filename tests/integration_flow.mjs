// User journeys in one page, through real DOM controls. Faults affect only this throw-away browser.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8773';
const out='spec/ekran-24/img/integration-first';fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const B=await startChrome(),errors=[],results=[];
B.cdp.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
const check=(ok,text)=>{if(!ok)throw new Error(text);results.push(text);console.log('PASS '+text);};
async function ready(cut,view=null){
 for(let i=0;i<240;i++){
  const r=await evaluate(B.cdp,()=>{const d=window.__d24;if(!d)return null;const c=d.cur(),x=d.integration();return {cut:c.obs,error:x.error,packet:x.packet?.context.cut,view:c.F?.view,checks:d.contract().unchecked};});
  if(r?.error)throw new Error(r.error);
  if(r?.cut===cut&&r.packet===cut&&(!view||r.view===view)&&!r.checks){await sleep(150);return;}
  if(i===239)throw new Error('scene timeout '+cut+': '+JSON.stringify(r));await sleep(200);
 }
}
async function go(date,at,scope='all',trials='pre,arrive,paths'){
 await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(100);
 await B.cdp.send('Page.navigate',{url:base+'/24/#date='+date+'&inst=NQ&session=RDR&at='+at+'&scope='+scope+'&trial='+trials});
 await ready(+at.split(':')[0]*60+(+at.split(':')[1]));
}
async function step(){await evaluate(B.cdp,()=>document.querySelector('#step21 [data-step="5"]').click());}
async function pick(){return evaluate(B.cdp,()=>{
 const d=window.__d24,h=d.links().find(x=>x.k==='arrive'&&x.id==='-1/2');if(!h)return false;
 const i=d.links().indexOf(h),el=document.querySelector('[data-l21="'+i+'"]');
 el.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));el.click();return true;
});}
async function shot(name,width){
 const p=await B.cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(out+'/'+name+'-'+width+'.png',Buffer.from(p.data,'base64'));
}
async function state(){return evaluate(B.cdp,()=>{
 const d=window.__d24,c=d.cur(),i=d.integration(),a=d.arriveOf(c),p=a?.places?.find(x=>x.level==='-1/2');
 const h=d.st.pin,sel=d.candidateSelection(c,h),lit=c.F&&h&&sel?.ready?c.F.ev.R.pts.filter(q=>sel.ids.has(q.m.id)).length:null;
 return {cut:c.obs,context:i.packet?.context.id,family:c.F?.r.family_id,snapshot:c.F?.r.snapshot_id,N:c.F?.N,
  view:c.F?.view,pin:h?.k,pinId:h?.id,arrive:a?.status,place:p?.state.status,publication:p?.publication,
  bundle:!!(p&&d.arriveBundle(a,p.level,p)),n:p?.counts?.n_match,lit,
  selection:i.selection,pathIds:i.pathEvidence?.ids,now:i.packet?.now?.status,nowCut:i.packet?.now?.cut?.cut,
  facts:i.packet?.target_facts,violations:d.contract().violations,discarded:i.discarded,
  scroll:document.documentElement.scrollHeight>innerHeight+2,summaryClosed:document.getElementById('dr21-root').classList.contains('panel21closed'),
  rows:d.links().filter(x=>x.k==='arrive').length};
});}
try{
 for(const width of [1600,1920]){
  await B.cdp.send('Emulation.setDeviceMetricsOverride',{width,height:width===1600?900:1000,deviceScaleFactor:1,mobile:false});
  await go('2025-12-17','10:35');
  check(await evaluate(B.cdp,()=>!!document.querySelector('.p24-pre')&&!window.__d24.cur().F),'PRE before confirmation '+width);await shot('pre',width);
  await step();await ready(640);
  check(await evaluate(B.cdp,()=>!document.querySelector('.p24-pre')&&window.__d24.arriveOf(window.__d24.cur())?.status==='NO_PREFIX'),'confirmation replaces PRE without using activating M5 '+width);
  for(let k=0;k<6;k++){await step();await ready(645+k*5);}
  check(await pick(),'select middle IDR through actual panel click '+width);
  await evaluate(B.cdp,()=>document.getElementById('deth').click());await sleep(250);
  let a=await state();check(a.pin==='arrive'&&a.bundle&&a.selection&&a.selection.ids.length===a.n,'selected answer links its exact matched set '+width);
  check(a.pathIds&&a.pathIds.length===a.n&&!a.scroll,'linked paths use the answer support in the existing tray '+width);await shot('selected',width);
  await step();await ready(675);let b=await state();
  check(a.family===b.family&&a.snapshot===b.snapshot&&a.N===b.N&&b.pinId==='-1/2'&&a.context!==b.context,'new M5 keeps BASE and selected target, replaces answer context '+width);
  await evaluate(B.cdp,()=>document.getElementById('panel21toggle').click());await sleep(200);
  check((await state()).summaryClosed,'summary remains optional '+width);await shot('focus',width);
  await go('2025-12-10','11:10');await pick();
  await evaluate(B.cdp,()=>{
   const old=window.fetch;window.fetch=async(...args)=>{const r=await old(...args);if(String(args[0]).includes('/api/integration/scene')&&new URL(String(args[0]),location.href).searchParams.get('at')==='675')await new Promise(ok=>setTimeout(ok,1800));return r;};
  });
  await step();await sleep(70);await step();await ready(680);await sleep(2200);
  b=await state();check(b.place==='RESOLVED'&&b.pinId==='-1/2'&&!b.bundle&&b.discarded>0,'late earlier reply cannot restore a reached target percentage '+width);await shot('reached',width);
  // Advance on the very same page to the DR break, keeping native replay controls.
  for(let k=0;k<38;k++){await step();await ready(685+k*5);}
  b=await state();check(b.view==='brk'&&b.arrive==='DR_BROKEN','break switches the family and withdraws intact-DR Q1 '+width);
  await evaluate(B.cdp,()=>document.querySelector('[data-scope="weekday"]').click());await ready(870,'brk');
  b=await state();check(b.N>0&&b.N<20,'explicit weekday scope keeps a small BASE family '+width);await shot('break',width);
  await evaluate(B.cdp,()=>document.querySelector('[data-view="conf"]').click());await ready(870,'conf');
  b=await state();check(b.now==='FROZEN_AT_BREAK'&&b.nowCut===845&&b.arrive==='DR_BROKEN'&&b.facts['-1/2'].reached==='YES','return original: frozen NOW and observed fact, no Q1 revival '+width);await shot('original',width);
  await go('2025-12-17','11:10','weekday');b=await state();
  check(b.publication==='WITHHELD_FEW_SESSIONS'&&!b.bundle,'few sessions withhold ARRIVE without widening '+width);await shot('few',width);
  await go('2025-12-17','11:10');await pick();
  await evaluate(B.cdp,()=>{document.getElementById('cfgb').click();const box=document.querySelector('[data-trial="arrive"]');box.closest('details').open=true;box.checked=false;box.dispatchEvent(new Event('input',{bubbles:true}));});await ready(670);
  check((await state()).rows===0,'candidate switch removes only its answers '+width);
 }
 check(errors.length===0,'no browser exceptions');
 fs.writeFileSync('lab/.runtime/integration-checks/flow.local.json',JSON.stringify({results,errors},null,1));
 console.log('ALL GOOD '+results.length+' journey checks; two viewports');
}catch(e){console.error(e.stack||e);const shot=await B.cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync('lab/.runtime/integration-checks/failure.png',Buffer.from(shot.data,'base64'));process.exitCode=1;}
finally{await B.close();}
