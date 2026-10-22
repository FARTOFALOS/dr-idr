// Observable shading and its semantic inputs. Throws on wrong counts, hidden-data loss, fake past or wrong time hills.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8735',view=process.env.DR_LAB_VIEW_PATH||'/23-5/';
const b=await startChrome(),errors=[],checks=[],out='lab/.runtime/shading235';
fs.mkdirSync(out,{recursive:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const ck=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);console.log('PASS '+name);};
b.cdp.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
await b.cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__fills=[];const f=CanvasRenderingContext2D.prototype.fillRect;CanvasRenderingContext2D.prototype.fillRect=function(...a){if(this.canvas.id==='cv')window.__fills.push({a,fill:this.fillStyle,alpha:this.globalAlpha});return f.apply(this,a);};`});
async function open(at){
 await b.cdp.send('Page.navigate',{url:'about:blank'});
 await b.cdp.send('Page.navigate',{url:base+view+'#date=2025-12-17&inst=NQ&session=RDR&at='+at+'&trial=pullbacks&pbscale=1'});
 for(let i=0;i<300;i++){const s=await evaluate(b.cdp,()=>{const d=window.__d24,p=d?.pullbacks();return {ok:!!p?.packet&&d.V.bandBars?.length&&d.V.projBars?.some(q=>q.ev==='R'),error:p?.error};});if(s.error)throw Error(s.error);if(s.ok)return;await pause(200);}
 throw Error('screen did not settle');
}
async function shot(name){const s=await b.cdp.send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(out+'/'+name+'.png',Buffer.from(s.data,'base64'));}
try{
 for(const [width,height]of [[1600,900],[1920,1000]]){
  await b.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await open('11:10');
  const r=await evaluate(b.cdp,()=>{
   const d=window.__d24,p=d.pullbacks().packet.proof,F=d.mapContext().F,cut=p.context.cut,pts=p.points.filter(q=>q.kt>=d.pullbacks().scale);
   window.__fills=[];d.render(true);
   const raw=d.V.projBars,labels=d.V.projLabels,need=Math.max(4,Math.ceil(F.N/20));
   const correct=raw.filter(q=>q.ev==='R').every(q=>{const use=pts.filter(v=>v.k===q.k),all=new Set(use.map(v=>v.case)),later=new Set(use.filter(v=>v.open+5>cut).map(v=>v.case));return q.n===all.size&&q.later===later.size&&q.earlier===all.size-later.size;});
   const hidden=raw.filter(q=>!q.visible),visible=raw.filter(q=>q.visible);
   const noHiddenPaint=hidden.every(q=>!window.__fills.some(f=>f.a[2]>0.1&&Math.abs(f.a[0]-q.x0)<0.1&&Math.abs(f.a[1]-(q.top+0.5))<0.1));
   const noSmallLabels=labels.every(l=>{const q=raw.find(q=>q.ev===l.ev&&q.k===l.k);return q?.substantial;});
   const hills=d.timeHills().R,curve=[];
   for(const h of hills.filter(Boolean)){
    const cells=new Set(h.z.cell_mask.map(c=>c.join('|'))),qs=pts.filter(q=>cells.has(q.k+'|'+q.b));
    for(const [t,actual]of [h.pts[0],h.pts[Math.floor(h.pts.length/2)],h.pts.at(-1)]){
     const by=new Map();for(const q of qs){const v=Math.exp(-((t-(q.open+2.5))**2)/(2*7**2));by.set(q.case,Math.max(by.get(q.case)||0,v));}
     curve.push(Math.abs([...by.values()].reduce((a,b)=>a+b,0)-actual)<1e-9);
    }
    curve.push(h.cases===new Set(qs.map(q=>q.case)).size,h.cases===h.z.n_known,h.pk<=h.cases+1e-9,h.pts.at(-1)[0]>=Math.max(...qs.map(q=>q.open+2.5))+20);
   }
   const invisibleTime=d.V.bandBars.filter(q=>q.n&&!q.visible),shownTime=d.V.bandBars.filter(q=>q.n&&q.visible);
   return {cfg:{projA:d.cfg.projA,passedA:d.cfg.passedA,R:d.cfg.R,projR:d.cfg.projR,X:d.cfg.X,projX:d.cfg.projX},correct,noHiddenPaint,noSmallLabels,curve:curve.every(Boolean),hidden:hidden.length,visible:visible.length,labels:labels.length,alphas:[...new Set(visible.map(q=>Math.round(q.futureA*1000)))].length,invisibleTime:invisibleTime.length,shownTime:shownTime.length,N:F.N,need,contract:d.contract().violations,hiddenCell:hidden.find(q=>q.ev==='R')};
  });
  ck(r.cfg.projA===90&&r.cfg.passedA===30&&r.cfg.projR===r.cfg.R&&r.cfg.projX===r.cfg.X,width+': screen 24 shading and palette installed');
  ck(r.correct&&r.contract.length===0,width+': historical case counts and clock parts retained');
  ck(r.hidden>0&&r.visible>0&&r.labels<r.visible&&r.noHiddenPaint&&r.noSmallLabels,width+': small rows are absent, supported peaks have a quiet label hierarchy');
  ck(r.alphas>2,width+': actual bars have graded shading, not a flat full-opacity fill');
  ck(r.curve,width+': time hills use every zone witness and at most one vote per session');
  ck(r.invisibleTime>0&&r.shownTime>0,width+': time strip focuses on zones and retains residual bins in data');
  await shot(width+'-bounds');
  const h=r.hiddenCell;
  const hover=await evaluate(b.cdp,h=>{const d=window.__d24;d.st.hover={k:'pbpcell',ev:'R',k0:h.k,k1:h.k+1,src:'proj'};d.render(true);return {row:d.V.projBars.find(v=>v.ev==='R'&&v.k===h.k),label:d.V.projLabels.some(v=>v.ev==='R'&&v.k===h.k),N:d.mapContext().F.N,text:document.getElementById('insp').innerText};},h);
  ck(hover.row.visible&&hover.label&&hover.row.n===h.n&&hover.N===r.N&&hover.text.includes('откаты'),width+': hidden row can be inspected without changing the denominator');
  await shot(width+'-hover');
  await open('15:55');
  const past=await evaluate(b.cdp,()=>{const d=window.__d24,c=d.cur(),F=d.mapContext().F;return {look:d.zoneLook(F,c,'R'),states:d.zoneStatus(F,c,'R'),hills:d.V.hills.filter(h=>h.ev==='R').map(h=>({dashed:h.dashed,alpha:h.alpha,look:h.look})),N:F.N};});
  ck(past.N===r.N&&past.look.every(v=>v==='PAST')&&past.states.every(v=>v!=='IMPOSSIBLE'&&v!=='HOLDS')&&past.hills.every(h=>h.dashed&&h.alpha<0.1),width+': expired window is dim/dashed without inventing a final-R price restriction');
  await shot(width+'-past');
 }
 ck(errors.length===0,'no browser exceptions');
 fs.writeFileSync(out+'/RESULT.json',JSON.stringify({base,view,checks,errors,outcome:'PASS'},null,2)+'\n');
 console.log('ALL GOOD '+checks.length);
}finally{await b.close();}
