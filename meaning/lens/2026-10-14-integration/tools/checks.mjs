// Run frozen branch checks, without rewriting them to make a new layout pass.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startChrome, evaluate } from '../../../../tests/trace_page.mjs';
import { ready, scenes } from './compare.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const local=path.join(root,'lab/.runtime/integration-spec');
const urls=process.argv.slice(2);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function main(){
 const B=await startChrome(),rows=[];
 try{
  for(const size of [[1600,900],[1920,1000]]){
   await B.cdp.send('Emulation.setDeviceMetricsOverride',{width:size[0],height:size[1],deviceScaleFactor:1,mobile:false});
   for(const name of ['WAIT','OPEN','BREAK','PATHS']){
    const scene=scenes.find(s=>s[0]===name);
    for(const [i,tag] of ['accepted','candidate'].entries()){
     await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(100);
     await B.cdp.send('Page.navigate',{url:urls[i]+'/24/#date='+scene[1]+'&inst=NQ&session=RDR&at='+scene[2]+(scene[3]==='all'?'&scope=all':'')});
     await ready(B,scene);
     await evaluate(B.cdp,(mode)=>{const D=window.__d24;D.st.mode=mode;D.st.detPin=mode==='path';document.getElementById('dr21-root').classList.remove('panel21closed');D.render(true);},scene[4]);
     for(const test of (tag==='candidate'?['ui_check24.js','family_path24_check.js']:['ui_check24.js'])){
      const code=fs.readFileSync(path.join(local,tag,'tests',test),'utf8');
      const res=await B.cdp.send('Runtime.evaluate',{expression:code,returnByValue:true,awaitPromise:true});
      if(res.exceptionDetails)throw new Error(tag+'/'+name+'/'+test+': '+JSON.stringify(res.exceptionDetails));
      rows.push({scene:name,viewport:size,variant:tag,test,result:res.result.value});
     }
     console.log('CHECKED '+tag+' '+name+' '+size.join('x'));
    }
   }
  }
 }finally{await B.close();}
 fs.writeFileSync(path.join(local,'branch-checks.raw.local.json'),JSON.stringify(rows));
}
main().catch(e=>{console.error(e.stack||e);process.exit(1);});
