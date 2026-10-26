// Regression of the operator's 22.10 comparison: stars were forcibly off, the anchor cropped the zone,
// and FINAL-X bars outside zone windows were hidden while PB-L received a misleading winner/loser contrast.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8735';
const b=await startChrome(),checks=[],errors=[],out='lab/.runtime/constellations235';
fs.mkdirSync(out,{recursive:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const ck=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);console.log('PASS '+name);};
b.cdp.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
await b.cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:`
 window.__arcs=[];window.__rects=[];
 const a=CanvasRenderingContext2D.prototype.arc,f=CanvasRenderingContext2D.prototype.fillRect;
 CanvasRenderingContext2D.prototype.arc=function(...p){if(this.canvas.id==='cv')window.__arcs.push(p);return a.apply(this,p);};
 CanvasRenderingContext2D.prototype.fillRect=function(...p){if(this.canvas.id==='cv')window.__rects.push({p,fill:this.fillStyle});return f.apply(this,p);};`});
async function open(fragment){
 await b.cdp.send('Page.navigate',{url:'about:blank'});
 await b.cdp.send('Page.navigate',{url:base+'/23-5/'+fragment});
 for(let i=0;i<320;i++){
  const s=await evaluate(b.cdp,()=>{const d=window.__d24,p=d?.pullbacks();return {ok:!!p?.packet&&!p.pending&&!!d.V.stars?.length&&!!d.V.bandBars?.length,error:p?.error};});
  if(s.error)throw Error(s.error);if(s.ok)return;await pause(150);
 }
 throw Error('page did not settle');
}
try{
 for(const [width,height]of [[1600,900],[1920,1000]]){
  await b.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await open('#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=weekday&trial=pullbacks&pbscale=1');
  const s=await evaluate(b.cdp,()=>{
   const d=window.__d24,F=d.mapContext().F,p=d.pullbacks().packet.proof;
   window.__arcs=[];window.__rects=[];d.render(true);
   const cloud=d.pullbacks().model.cloud,stars=d.V.stars,raw=F.ev.R.pts;
   const expected=new Set();
   for(const z of F.zones.R.zones){const mask=new Set(z.cell_mask.map(c=>c.join('|')));for(const q of raw)if(mask.has(q.k+'|'+q.b))expected.add(q.k+'|'+q.t);}
   const actual=new Set(cloud.ev.R.pts.map(q=>q.k+'|'+q.t));
   const sameCells=expected.size===actual.size&&[...expected].every(k=>actual.has(k));
   const actualWitnesses=cloud.ev.R.pts.every(q=>raw.some(v=>v.pbid===q.pbid&&v.t===q.t&&v.p===q.p));
   const allCells=F.zones.R.zones.map((z,i)=>({
    i,full:raw.filter(q=>F.zcell.R.get(q.k+'|'+q.b)===i).length,
    nodes:cloud.ev.R.pts.filter(q=>F.zcell.R.get(q.k+'|'+q.b)===i).length,
    outside:cloud.ev.R.pts.some(q=>F.zcell.R.get(q.k+'|'+q.b)===i&&(Math.abs(q.k-z.anchor[0])>1||Math.abs(q.b-z.anchor[1])>1))
   }));
   const arcs=stars.every(q=>window.__arcs.some(a=>Math.abs(a[0]-q.x)<1e-7&&Math.abs(a[1]-q.y)<1e-7));
   const bars=d.V.bandBars,counts=['R','X'].every(ev=>[...F.ev[ev].T].every(([b,n])=>bars.some(q=>q.ev===ev&&q.b===b&&q.n===n&&q.visible)));
   const painted=bars.filter(q=>q.n).every(q=>window.__rects.some(r=>Math.abs(r.p[0]-q.x0)<1e-7&&Math.abs(r.p[1]-Math.min(q.cy+(q.y>q.cy?1:-1),q.y))<1e-7&&r.p[2]>0&&r.p[3]>0));
   const outsideX=bars.filter(q=>q.ev==='X'&&q.n&&!F.zones.X.zones.some(z=>z.cell_mask.some(([,bb])=>bb===q.b)));
   return {layer:d.st.L.pts,roles:[...new Set(stars.map(q=>q.ev))],sameCells,actualWitnesses,allCells,arcs,
    compact:cloud.ev.R.pts.length<raw.length,counts,painted,outsideX:outsideX.length,outsideXVisible:outsideX.every(q=>q.visible),
    neutral:bars.every(q=>!q.comparable&&q.dom===0),
    linear:bars.filter(q=>q.n>0).every(q=>Math.abs((Math.abs(q.y-q.cy)-1)/q.n-(Math.abs(bars.find(v=>v.n>0).y-bars.find(v=>v.n>0).cy)-1)/bars.find(v=>v.n>0).n)<1e-9),
    xUnchanged:F.ev.X===d.cur().F.ev.X,N:F.N,expectedN:p.context.N,contract:d.contract().violations,
    stats:{points:raw.length,nodes:cloud.ev.R.pts.length,stars:stars.length,time:bars.filter(q=>q.n).map(q=>[q.ev,q.b,q.n])}};
  });
  ck(s.layer&&['R','X'].every(ev=>s.roles.includes(ev))&&s.arcs,width+': real canvas draws stars of both colours by default');
  ck(s.sameCells&&s.actualWitnesses&&s.compact,width+': one genuine witness per occupied M5/SD cell, not fabricated points or all episodes');
  ck(s.allCells.some(q=>q.nodes>1&&q.outside)&&s.allCells.every(q=>!q.full||q.nodes>0),width+': the full zone produces a constellation beyond its anchor');
  ck(s.counts&&s.painted&&s.outsideX>0&&s.outsideXVisible,width+': all window shares actually paint, including blue bins outside zones');
  ck(s.neutral&&s.linear,width+': no winner/loser contrast for unlike events; heights keep a common linear scale');
  ck(s.xUnchanged&&s.N===s.expectedN&&!s.contract.length,width+': X, full family N and typed semantic contracts are unchanged');
  const shot=await b.cdp.send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(out+'/'+width+'-bounds.png',Buffer.from(shot.data,'base64'));
  fs.writeFileSync(out+'/'+width+'-stats.json',JSON.stringify(s,null,2)+'\n');
  // With the candidate off, the original FINAL-R/X comparison retains its own legitimate presentation.
  const accepted=await evaluate(b.cdp,()=>{const d=window.__d24;d.setTrial('pullbacks',false);d.render(true);return {pb:d.pullbacks().mode,roles:[...new Set(d.V.stars.map(q=>q.ev))],comparable:d.V.bandBars.every(q=>q.comparable)};});
  ck(!accepted.pb&&accepted.comparable&&accepted.roles.includes('X'),width+': candidate-off restores accepted R/X without leaking PB presentation');
 }
 ck(!errors.length,'no browser exceptions');
 fs.writeFileSync(out+'/RESULT.json',JSON.stringify({checks,errors,outcome:'PASS'},null,2)+'\n');
 console.log('ALL GOOD '+checks.length);
}finally{await b.close();}
