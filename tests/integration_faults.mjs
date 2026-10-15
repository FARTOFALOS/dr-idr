import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8773';
const B=await startChrome(),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const checks=[];const check=(ok,t)=>{if(!ok)throw new Error(t);checks.push(t);console.log('PASS '+t);};
try{
 await B.cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:`const realFetch=window.fetch;window.fetch=async(...args)=>{const response=await realFetch(...args);if(String(args[0]).includes('/api/integration/scene')){const value=await response.json();const bundle=value.candidates?.arrive?.contract?.bundles?.find(b=>b.estimand==='EST:K-ARRIVE'&&JSON.parse(b.parameters||'{}').level==='-1/2');if(bundle){const p=bundle.estimates.find(e=>e.value_kind==='POINT');p.numerator++;}return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});}return response;};`});
 await B.cdp.send('Page.navigate',{url:base+'/24/#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all&trial=arrive,paths&det=1'});
 for(let i=0;i<150;i++){if(await evaluate(B.cdp,()=>!!window.__d24?.integration().packet))break;await sleep(200);}
 const r=await evaluate(B.cdp,()=>{const d=window.__d24,h=d.links().find(h=>h.k==='arrive'&&h.id==='-1/2');if(!h)return{};
   const el=document.querySelector('[data-l21="'+d.links().indexOf(h)+'"]');el.click();d.render(true);
   return {text:el.textContent,F:!!d.cur().F,N:d.cur().F?.N,selection:d.integration().selection,paths:d.integration().pathEvidence,tip:document.getElementById('insp').innerText,violations:d.contract().violations};});
 check(r.F&&r.N>0&&r.text.includes('—')&&r.tip.includes('не опубликовано'),'tampered candidate bundle withholds its percentage with a visible reason; BASE remains');
 check(!r.selection&&!r.paths,'withheld candidate cannot retain a target line or conditional paths');
 // Simulate an unavailable live channel in the test browser only; do not restart or operate TradingView.
 await evaluate(B.cdp,()=>{const previous=window.fetch;window.fetch=async(...args)=>{const url=new URL(String(args[0]),location.href);if(url.pathname==='/api/d24/day'&&!url.searchParams.has('date'))return new Response(JSON.stringify({status:'no_data',message:'Тест: канал TradingView недоступен'}),{headers:{'Content-Type':'application/json'}});return previous(...args);};document.getElementById('dayb').click();document.getElementById('dlive').click();});
 await sleep(900);
 const live=await evaluate(B.cdp,()=>{const d=window.__d24;return {source:d.A.src,pin:d.st.pin,packet:d.integration().packet,text:document.getElementById('panel').innerText,selection:d.integration().selection};});
 check(live.source==='live'&&!live.pin&&!live.packet&&!live.selection&&!live.text.includes('37,8%'),'return to unavailable live cannot reuse a historical answer or selection');
 const guarded=await evaluate(B.cdp,()=>window.__d24.lbl('EST:N-NEW-R','title_mark',{today:'0',cut:'11:10',pct:'50%',yes:1,D:2,n:2,N:2}));
 check(guarded==='','candidate labels cannot extend the accepted NOW vocabulary');
 fs.writeFileSync('lab/.runtime/integration-checks/faults.local.json',JSON.stringify({status:'PASS',checks,scope:'controlled browser faults; fresh live feed not tested'},null,1));
 console.log('ALL GOOD');
}finally{await B.close();}
