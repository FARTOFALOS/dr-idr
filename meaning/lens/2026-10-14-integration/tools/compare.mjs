// Uses the existing trace Chrome/CDP harness; no second browser engine or product server.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startChrome, evaluate } from '../../../../tests/trace_page.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const pkg=path.join(root,'meaning/lens/2026-10-14-integration');
const local=path.join(root,'lab/.runtime/integration-spec');
const args=process.argv.slice(2), baseA=args[0], baseB=args[1];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const scenes=[
 ['FOCUS','2025-12-17','11:10','all','bounds',null,null,'hidden'],
 ['WAIT','2025-12-17','10:35','weekday','bounds',null],
 ['CONF','2025-12-17','10:40','weekday','bounds',null],
 ['OPEN','2025-12-17','11:10','all','bounds','arrive:-1/2'],
 ['FEW','2025-12-17','11:10','weekday','bounds','arrive:-1/2'],
 ['PULL','2025-12-10','11:15','all','bounds','now:R'],
 ['REACHED','2025-12-10','11:20','all','bounds','arrive:-1/2'],
 ['BREAK','2025-12-10','14:30','weekday','bounds',null],
 ['ORIGINAL','2025-12-10','14:30','weekday','bounds',null,'conf'],
 ['PATHS','2025-12-17','11:10','all','path','arrive:-1/2']
];

async function ready(B,scene){
 let reason=''; const until=Date.now()+100000;
 while(Date.now()<until){
  try { reason=await evaluate(B.cdp,(date,at)=>{
   const D=window.__d24;if(!D||!D.V||!D.cur)return 'page';const c=D.cur(),C=D.contract();
   if(!D.A.day||D.A.day.status!=='ok'||c.D.iso!==date)return 'day';
   if(c.obs!==at)return 'cut '+c.obs;
   if(!c.F&&['waiting','forming','before','noconf'].includes(c.s.status))return 'ok';
   if(!c.F)return 'family';if(C.unchecked)return 'unchecked';
   const n=D.nowOf(c);if(!n||!n.status)return 'now';return 'ok';
  },scene[1],+scene[2].split(':')[0]*60+(+scene[2].split(':')[1]));}catch(e){reason=e.message;}
  if(reason==='ok'){await sleep(1000);return;} await sleep(250);
 }
 throw new Error(scene[0]+' did not settle: '+reason);
}

const read=async (B,base,scene,viewport)=>{
 const data=await evaluate(B.cdp,async(base,selection,view,hide)=>{
  const D=window.__d24;D.st.mode=view;D.st.detPin=view==='path';D.st.detTab=5;
  const root=document.getElementById('dr21-root');root.classList.toggle('panel21closed',hide);
  D.render(true); await new Promise(r=>setTimeout(r,400));
  if(selection){const [kind,id]=selection.split(':');const link=D.links().find(l=>l.k===kind&&(kind==='now'?l.ev===id:String(l.id)===id));if(link){D.st.pin=link;D.st.hover=null;D.render(true);}}
  await new Promise(r=>setTimeout(r,900));
  const until=Date.now()+20000;
  while(D.contract().unchecked && Date.now()<until)await new Promise(r=>setTimeout(r,200));
  if(D.contract().unchecked)throw new Error('new view passports did not verify');
  const c=D.cur(),F=c.F,C=D.contract(),panel=document.getElementById('panel'),P=D.passports();
  const clip=(a,b)=>a.top<b.top||a.right>b.right||a.bottom>b.bottom||a.left<b.left;
  const viewport={top:0,left:0,right:innerWidth,bottom:innerHeight};
  const toolbar=document.getElementById('tb');
  const figures=F?{family_id:F.r.family_id,snapshot_id:F.r.snapshot_id,N:F.N,view:F.view,
    cells:Object.fromEntries(['R','X'].map(ev=>[ev,[...F.ev[ev].cells.values()].map(v=>[v.k,v.b,v.list.length]).sort((a,b)=>a[0]-b[0]||a[1]-b[1])])),
    members:F.M.map(m=>({id:m.id,w:m.w,R:m.R,X:m.X})).sort((a,b)=>a.id.localeCompare(b.id)),counts:F.r.counts}:null;
  const n=F&&D.nowOf(c); const arr=F&&D.arriveOf?D.arriveOf(c):null;
  const observed=c.D.bars.filter(b=>b.t+5<=c.obs).map(b=>[b.t,b.o,b.h,b.l,b.c]);
  const counters=[...panel.querySelectorAll('.p24-frame>span,.qmeta,.p21-sub')].filter(el=>el.getClientRects().length&&getComputedStyle(el).display!=='none')
    .map(el=>el.textContent).filter(t=>/(?:\bn\s*=|\bN\s*=|\d+\s+сессий|\d+\s+из\s+\d+)/.test(t)&&!/мало|неизвестно/i.test(t));
  return {scene:{date:c.D.iso,cut:c.obs,status:c.s.status,side:c.s.side,failed:c.s.failed},base:figures,observed,
    now:n&&{status:n.status,cut:n.cut,base:n.base,R:n.R,X:n.X},arrive:arr,
    contract:{registry:C.registry_hash,violations:C.violations,unchecked:C.unchecked},
    passports:P.map(p=>({estimand:p.estimand,params:p.params,yes:p.yes_count,unknown:p.unknown_count,N:p.N,checked:p.checked,violation:p.violation})),
    geometry:{width:innerWidth,height:innerHeight,no_page_scroll:document.documentElement.scrollHeight<=innerHeight+1,
     toolbar_visible:toolbar?!clip(toolbar.getBoundingClientRect(),viewport):null,
     canvas:document.querySelector('canvas')?.getBoundingClientRect().toJSON()},
    panel_counters:counters,panel_text:panel.innerText,inspector:document.getElementById('insp')?.innerText,
    graphEvidence:D.graphEvidence||null,pathEvidence:D.pathEvidence||null,
    selection:selection||null,summary_hidden:root.classList.contains('panel21closed'),has_frame:F!=null};
 },base,scene[5],scene[4],scene[7]==='hidden');
 const img=await B.cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
 const label=scene[0].toLowerCase()+'-'+viewport[0];
 fs.mkdirSync(path.join(pkg,'comparison/img'),{recursive:true});
 fs.writeFileSync(path.join(pkg,'comparison/img',label+'.'+(base===baseA?'A':'B')+'.png'),Buffer.from(img.data,'base64'));
 return data;
};

async function main(){
 if(!baseA||!baseB)throw new Error('two isolated backend URLs required');
 fs.mkdirSync(local,{recursive:true});
 const B=await startChrome(),rows=[];
 try{
  for(const size of [[1600,900],[1920,1000]]){
   await B.cdp.send('Emulation.setDeviceMetricsOverride',{width:size[0],height:size[1],deviceScaleFactor:1,mobile:false});
   for(const scene of scenes){
    const pair={id:scene[0],viewport:size};
    for(const [tag,base] of [['A',baseA],['B',baseB]]){
     const hash='#date='+scene[1]+'&inst=NQ&session=RDR&at='+scene[2]+(scene[3]==='all'?'&scope=all':'');
     await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(120);
     await B.cdp.send('Page.navigate',{url:base+'/24/'+hash});await ready(B,scene);
     if(scene[6]){await evaluate(B.cdp,()=>{const D=window.__d24;D.st.view='conf';D.render(true);});await sleep(1500);}
     pair[tag]=await read(B,base,scene,size);
    }
    rows.push(pair);console.log('COMPARED '+scene[0]+' '+size.join('x'));
   }
  }
 }finally{await B.close();}
 fs.writeFileSync(path.join(local,'comparison.raw.local.json'),JSON.stringify(rows));
}
export { ready, scenes };
if(path.resolve(process.argv[1]||'')===fileURLToPath(import.meta.url))main().catch(e=>{console.error(e.stack||e);process.exit(1);});
