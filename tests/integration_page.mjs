import fs from 'node:fs';
import path from 'node:path';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8773';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const B=await startChrome(), errors=[];
B.cdp.on('Runtime.exceptionThrown',ev=>errors.push(ev.exceptionDetails.exception?.description||ev.exceptionDetails.text));
try {
 await B.cdp.send('Page.navigate',{url:base+'/24/#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all&trial=pre,arrive,paths&det=1'});
 for(let i=0;i<180;i++){
  const state=await evaluate(B.cdp,()=>{const D=window.__d24;return D?{F:!!D.cur().F,i:D.integration().packet?.status,error:D.integration().error}:null});
  if(state?.F&&state.i==='OK')break;
  if(state?.error)throw new Error(state.error);
  if(i===179)throw new Error('page did not settle: '+JSON.stringify(state)+' '+JSON.stringify(errors));
  await sleep(250);
 }
 const state=await evaluate(B.cdp,()=>{
  const D=window.__d24,h=D.links().find(x=>x.k==='arrive'&&x.id==='-1/2');
  if(h){D.st.pin=h;D.st.hover=null;D.st.detPin=true;D.render(true);}
  return {family:!!D.cur().F,scene:D.integration().packet?.context,arrive:D.arriveOf(D.cur())?.status,
          rows:D.links().filter(h=>h.k==='arrive').length,contract:D.contract(),error:D.integration().error,
          selection:D.integration().selection,pathIds:D.integration().pathEvidence?.ids?.length,panel:document.getElementById('panel').innerText};
 });
 fs.mkdirSync('lab/.runtime/integration-checks',{recursive:true});
 fs.writeFileSync('lab/.runtime/integration-checks/page.local.json',JSON.stringify({state,errors},null,1));
 const png=await B.cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
 fs.writeFileSync('lab/.runtime/integration-checks/first.png',Buffer.from(png.data,'base64'));
 // FF:CANDIDATE-STATUS (operator 19.10): every candidate surface carries its standing where it is shown, an accepted
 // block never does; the accepted view at the same cut has no tag at all
 const tags=async(hash,wait)=>{
  await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(80);
  await B.cdp.send('Page.navigate',{url:base+'/24/'+hash});
  for(let i=0;i<240;i++){const s=await evaluate(B.cdp,w=>{const D=window.__d24;if(!D?.V?.ctx)return false;D.render(true);return !!document.querySelector(w);},wait).catch(()=>false);if(s)break;await sleep(250);}
  await sleep(300);
  return evaluate(B.cdp,()=>({pre:document.querySelectorAll('#panel .p24-pre .p21-h .p24-cand').length,arrive:document.querySelectorAll('#panel .p24-arrblk .p21-h .p24-cand').length,
   phase:document.querySelectorAll('#panel .p24-phase .p21-h .p24-cand').length,now:document.querySelectorAll('#panel .p24-nowblk .p24-cand').length,
   all:document.querySelectorAll('#panel .p24-cand').length,tab:document.querySelector('#mode [data-m="continuations"]').title}));
 };
 const day='#date=2025-12-17&inst=NQ&session=RDR';
 const tPre=await tags(day+'&at=10:30&trial=pre','.p24-pre .p21-link');
 const t0810=await tags(day+'&at=11:00&trial=phase,nowmarks','.p24-phase');
 const tArr=await tags(day+'&at=11:00&trial=arrive','.p24-arrblk');
 const tBase=await tags(day+'&at=11:00','.p24-nowblk .p21-link');
 const standing=tPre.pre===1&&t0810.phase===1&&t0810.now===1&&tArr.arrive===1&&tBase.all===0&&/кандидат/.test(tBase.tab);
 console.log(JSON.stringify({rows:state.rows,arrive:state.arrive,selected:!!state.selection,pathIds:state.pathIds,error:state.error,errors,standing:{pre:tPre,phase_nowmarks:t0810,arrive:tArr,accepted:tBase}}));
 if(errors.length||state.rows!==3||!state.selection||!standing)process.exitCode=1;
}finally{await B.close();}
