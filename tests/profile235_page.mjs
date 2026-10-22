// Facet boundaries that would be lost by copying 23.5 over /24/ or by leaking FINAL-R's cells into PB-L.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8795',b=await startChrome(),checks=[],errors=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const fragment='#date=2025-12-17&inst=NQ&session=RDR&at=11:10';
const ck=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);console.log('PASS '+name);};
b.cdp.on('Runtime.exceptionThrown',e=>errors.push(e.exceptionDetails.exception?.description||e.exceptionDetails.text));
async function open(view){await b.cdp.send('Page.navigate',{url:'about:blank'});await b.cdp.send('Page.navigate',{url:base+view+fragment});await ready(view.includes('23-5'));}
async function ready(pb){for(let n=0;n<300;n++){const r=await evaluate(b.cdp,()=>{const d=window.__d24,p=d?.pullbacks?.();return {base:!!d?.cur().F&&!d.contract().unchecked,pb:!!p?.packet&&!p.pending,error:p?.error,rendered:d?.V.projBars?.some(q=>q.ev==='R')};});if(r.error)throw Error(r.error);if(r.base&&(!pb||r.pb&&r.rendered))return;await pause(200);}throw Error('view not ready');}
const signature=()=>{const d=window.__d24,F=d.cur().F;return JSON.stringify([F.r.family_id,F.r.snapshot_id,F.N,F.r.members,F.r.counts,F.r.zones]);};
try{
 await open('/24/');const before=await evaluate(b.cdp,signature);
 const kept=await evaluate(b.cdp,()=>Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith('drlab.d24.')).map(k=>[k,localStorage.getItem(k)])));
 await open('/23-5/');const candidate=await evaluate(b.cdp,signature);
 const after=await evaluate(b.cdp,()=>Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith('drlab.d24.')).map(k=>[k,localStorage.getItem(k)])));
 ck(before===candidate,'23.5 reuses exactly the accepted F and does not replace historical labels in the family');
 ck(JSON.stringify(kept)===JSON.stringify(after),'23.5 never writes screen 24 local settings or trial choices');
 const typed=await evaluate(b.cdp,()=>{const d=window.__d24,F=d.mapContext().F,p=d.pullbacks().packet.proof,pts=p.points.filter(q=>q.kt>=d.pullbacks().scale),cells=new Map();for(const q of pts){const k=q.k+'|'+q.b;if(!cells.has(k))cells.set(k,new Set());cells.get(k).add(q.case);}return F.ev.R.event_id==='PB_L'&&F.ev.R.cells.size===cells.size&&[...F.ev.R.cells].every(([key,c])=>JSON.stringify(c.list.map(i=>F.M[i].id).sort())===JSON.stringify([...cells.get(key)].sort()));});
 ck(typed,'PB adapter has its own typed cell table, never inherited FINAL-R cells');
 const unknown=await evaluate(b.cdp,()=>{const d=window.__d24,p=d.pullbacks().packet.proof;d.st.hover={k:'pbunk',src:'strip'};d.render(true);const labels=[...document.querySelectorAll('#insp [data-pb-category]')];return labels.length===2&&labels.some(x=>x.dataset.pbCategory==='UNKNOWN')&&labels.some(x=>x.dataset.pbCategory==='NONE')&&document.getElementById('insp').innerText.includes('X · не определено');});
 ck(unknown,'the mixed unknown glyph opens PB categories and final-X mass, never inherited final-R unknowns');
 await evaluate(b.cdp,()=>{const d=window.__d24;d.st.area={ev:'R',k0:-Infinity,k1:Infinity,b0:1,b1:3};d.render(true);});await ready(true);
 const time=await evaluate(b.cdp,()=>{const d=window.__d24,p=d.pullbacks().packet.proof,v=p.marginals['1'].find(v=>v.k0===null&&v.k1===null&&v.b0===1&&v.b1===3);return v&&v.n_known===new Set(p.points.filter(q=>q.kt>=1&&q.b>=1&&q.b<3).map(q=>q.case)).size&&d.contract().violations.length===0;});
 ck(time,'unbounded price on a time-only selection is normalized and returns the requested region');
 await evaluate(b.cdp,()=>{const d=window.__d24;d.st.area={ev:'R',k0:-2,k1:1,b0:0,b1:3};d.render(true);});await ready(true);
 const joint=await evaluate(b.cdp,()=>{const d=window.__d24,p=d.pullbacks().packet.proof,v=p.marginals['1'].find(v=>v.k0===-2&&v.k1===1&&v.b0===0&&v.b1===3);return v&&v.n_known===new Set(p.points.filter(q=>q.kt>=1&&q.k>=-2&&q.k<1&&q.b>=0&&q.b<3).map(q=>q.case)).size;});
 ck(joint,'price × time selection counts one case once even with multiple qualifying local episodes');
 await open('/24/');ck(await evaluate(b.cdp,signature)===before,'return to /24/ retains the original family and final R/X');
 ck(await evaluate(b.cdp,()=>!window.__d24.pullbacks().mode&&document.title.includes('24')),'default /24/ remains accepted bounds rather than the 23.5 candidate');
 ck(errors.length===0,'both surfaces have no browser exceptions');
 fs.mkdirSync('lab/.runtime/release-checks',{recursive:true});fs.writeFileSync('lab/.runtime/release-checks/profile235.json',JSON.stringify({base,checks,errors,outcome:'PASS'},null,2)+'\n');
 console.log('ALL GOOD '+checks.length);
}finally{await b.close();}
