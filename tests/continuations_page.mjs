// Real browser/real API. Only the throw-away browser is fault-injected.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8773';
const out='spec/ekran-24/img/continuations';fs.mkdirSync(out,{recursive:true});
const B=await startChrome(),results=[],errors=[],frames=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
B.cdp.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
function check(ok,name){if(!ok)throw Error(name);results.push(name);console.log('PASS '+name);}
async function ready(cut){
 for(let i=0;i<400;i++){
  const s=await evaluate(B.cdp,()=>{const d=window.__d24;if(!d)return null;const c=d.continuations();return {cut:d.cur().obs,error:c.error,packet:c.packet?.proof.context.cut,drawing:c.drawing?.release,release:c.packet?.release_id,pending:c.pending};});
  if(s?.error)throw Error(s.error);
  if(s?.cut===cut&&s.packet===cut&&s.drawing===s.release){await sleep(150);return;}
  if(i===399)throw Error('timeout '+JSON.stringify(s));await sleep(150);
 }
}
async function go(at='11:10',seed=true){
 await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(80);
 await B.cdp.send('Page.navigate',{url:base+'/24/#date=2025-12-17&inst=NQ&session=RDR&at='+at+'&scope=all&trial=continuations&mode=continuations'+(seed?'&cont=17,19,685,700,670':'')});
 if(seed)await ready(670);
 else for(let i=0;i<200;i++){if(await evaluate(B.cdp,()=>!!window.__d24?.cur().F)){await sleep(200);break;}await sleep(150);}
}
async function snap(name){
 const shot=await B.cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(out+'/'+name+'.png',Buffer.from(shot.data,'base64'));
}
async function state(){return evaluate(B.cdp,()=>{
 const d=window.__d24,c=d.continuations(),p=c.packet.proof;
 return {cut:p.context.cut,status:c.packet.status,target:JSON.stringify(p.target),question:p.question.id,release:c.packet.release_id,
         source:p.context.history_revision,counts:p.counts,support:p.support,ids:p.witnesses.map(w=>w.id),draw_ids:c.drawing.ids,
         draw_release:c.drawing.release,inspector:document.querySelector('#insp').innerText,
         family:JSON.stringify([d.cur().F.r.family_id,d.cur().F.r.snapshot_id,d.cur().F.r.members,d.cur().F.r.counts,d.cur().F.r.zones]),
         overflow:document.documentElement.scrollWidth>innerWidth+12};
 });}
try{
 for(const [width,height] of [[1600,900],[1920,1000]]){
  await B.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await go();const first=await state();frames.push({viewport:[width,height],cut:670,counts:first.counts,support:first.support,release:first.release});
  check(first.support.n_total===97&&first.counts.outside_F===60,'all 97 witnesses, including 60 outside F, '+width);
  check(JSON.stringify(first.ids)===JSON.stringify(first.draw_ids)&&first.draw_release===first.release,'drawing is bound to every exact case of the published release, '+width);
  check(!first.overflow,'toolbar fits '+width);
  await snap(width+'-initial');
  await evaluate(B.cdp,()=>document.querySelector('#deth').click());await sleep(200);
  const selected=await evaluate(B.cdp,()=>{
   const d=window.__d24,c=d.continuations(),F=new Set(d.cur().F.M.map(m=>m.id)),w=c.packet.proof.witnesses.find(w=>!F.has(w.id)),el=document.querySelector('#c24case');
   if(!el||!w)return null;el.value=w.id;el.dispatchEvent(new Event('change',{bubbles:true}));return w.id;
  });await sleep(100);
  check(!!selected&&await evaluate(B.cdp,id=>window.__d24.continuations().selected===id&&window.__d24.continuations().drawing.ids.includes(id),selected),
        'case inspector selects a real witness outside F / '+width);
  await snap(width+'-witness');
  await evaluate(B.cdp,()=>{const el=document.querySelector('#c24case');el.value='';el.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('#deth').click();});await sleep(150);
  for(const cut of [675,680,685,690,695,700]){
   await evaluate(B.cdp,()=>document.querySelector('#step21 [data-step="5"]').click());await ready(cut);
   const next=await state();frames.push({viewport:[width,height],cut,status:next.status,support:next.support,counts:next.counts,question:next.question,release:next.release});
   check(next.target===first.target,'physical area and absolute window remain pinned at '+cut+' / '+width);
   if(cut<690)check(next.question===first.question,'same future question before first window close '+cut+' / '+width);
   if(cut===690){
    check(next.question!==first.question&&next.support.n_total===39&&next.support.yes===20,'residual question explicitly has 39 cases of 81 position matches / '+width);
    check(/новый остаточный вопрос/.test(next.inspector)&&/остаток 11:30/.test(next.inspector),'visible residual meaning at 11:30 / '+width);
    await snap(width+'-residual');
   }
   if(cut>=695)check(next.status==='FACT_YES'&&!next.ids.length&&!next.draw_ids.length&&/11:35/.test(next.inspector),'fact replaces percentage and conditional drawing / '+width);
   if(cut===695)await snap(width+'-fact');
  }
  await evaluate(B.cdp,()=>document.querySelector('#mode [data-m="bounds"]').click());await sleep(250);
  const restored=await evaluate(B.cdp,()=>{const f=window.__d24.cur().F;return JSON.stringify([f.r.family_id,f.r.snapshot_id,f.r.members,f.r.counts,f.r.zones]);});
  check(restored===first.family,'original historical R/X snapshot restored identically / '+width);await snap(width+'-bounds');
  await evaluate(B.cdp,()=>document.querySelector('#mode [data-m="continuations"]').click());await ready(700);
  check((await state()).target===first.target,'target survives switching representations / '+width);
 }
 // Actual mouse selection, not a synthetic setter: close 11:30..11:40, same SD band.
 await go('11:10',false);
 await evaluate(B.cdp,()=>document.querySelector('#areab').click());
 const rect=await evaluate(B.cdp,()=>{const d=window.__d24,v=d.V,s=d.cur().s,e=s.side===1?s.idrH:s.idrL,w=s.idrH-s.idrL,r=document.querySelector('#cv').getBoundingClientRect();return {x:r.left+v.X(686),x1:r.left+v.X(699),y:r.top+v.Y(e+s.side*w*1.72),y1:r.top+v.Y(e+s.side*w*1.88)};});
 await B.cdp.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x,y:rect.y});
 await B.cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',x:rect.x,y:rect.y,button:'left',clickCount:1});
 await B.cdp.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x1,y:rect.y1,button:'left',buttons:1});
 await B.cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:rect.x1,y:rect.y1,button:'left',clickCount:1});await ready(670);
 check((await state()).support.n_total===97,'mouse brush creates the same physical target and exact window');
 // Corrupt a path while leaving the correct percentage untouched: no dependent drawing survives.
 for(const fault of ['missing_path','foreign_path','foreign_bundle']){
  await evaluate(B.cdp,fault=>{
   const original=window.fetch.bind(window);window.fetch=async(...args)=>{const r=await original(...args);if(!String(args[0]).includes('/api/integration/continuations'))return r;
    const x=await r.json();if(!x.proof?.witnesses.length)return new Response(JSON.stringify(x),{status:200});
    if(fault==='missing_path')x.proof.witnesses.pop();
    if(fault==='foreign_path')x.proof.witnesses[0].path[x.proof.witnesses[0].path.length-1]=[999,1000,999];
    if(fault==='foreign_bundle'){const p=JSON.parse(x.contract.bundles[0].parameters);p.release='foreign-release';x.contract.bundles[0].parameters=JSON.stringify(p);}
    return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}});
   };window.__d24.st.rp=675;window.__d24.render(true);
  },fault);
  let rejected=false;for(let i=0;i<300;i++){const s=await evaluate(B.cdp,()=>{const c=window.__d24.continuations();return {error:c.error,packet:!!c.packet,drawing:c.drawing};});if(s.error){rejected=!s.packet&&!s.drawing;break;}await sleep(150);}
  check(rejected,'correct number cannot keep a '+fault+' drawing');
  await go();
 }
 await evaluate(B.cdp,()=>{
  const original=window.fetch.bind(window);window.fetch=async(...args)=>{
   const r=await original(...args);
   if(String(args[0]).includes('/api/integration/continuations')&&JSON.parse(args[1].body).at===675)await new Promise(ok=>setTimeout(ok,2000));
   return r;
  };
  document.querySelector('#step21 [data-step="5"]').click();
 });await sleep(100);
 await evaluate(B.cdp,()=>document.querySelector('#step21 [data-step="5"]').click());await ready(680);await sleep(2400);
 check((await state()).cut===680&&await evaluate(B.cdp,()=>window.__d24.continuations().discarded>0),
       'a late prior release cannot replace the new M5 answer or drawing');
 const prior=await state();
 await evaluate(B.cdp,()=>{const d=window.__d24;d.st.rpWanted=680;d.openHist('2025-12-17');});await ready(680);
 const reopened=await state();
 check(reopened.release===prior.release&&reopened.target===prior.target&&reopened.family===prior.family,
       'reopening the same day restores a current scene and the identical pinned release');
 check(!errors.length,'no browser exceptions: '+errors.join('\n'));
 fs.writeFileSync('integration/continuations-browser-verification.json',JSON.stringify({status:'PASS',results,frames,limits:['machine checks, not operator perceptual acceptance','fixed/residual window calibration remains separate']},null,2)+'\n');
 console.log('ALL GOOD',results.length);
}finally{await B.close();}
