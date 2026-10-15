// Execute the existing accepted screen's in-page checks at both required viewport sizes.
import fs from 'node:fs';
import {startChrome,evaluate} from './trace_page.mjs';
const base=process.argv[2]||'http://127.0.0.1:8773',B=await startChrome(),results=[];
const sleep=ms=>new Promise(ok=>setTimeout(ok,ms));
try{
 for(const [width,height] of [[1600,900],[1920,1000]]){
  await B.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  await B.cdp.send('Page.navigate',{url:'about:blank'});await sleep(100);
  await B.cdp.send('Page.navigate',{url:base+'/24/#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all'});
  for(let n=0;n<300;n++){
   if(await evaluate(B.cdp,()=>!!window.__d24?.cur().F&&!window.__d24.contract().unchecked))break;
   if(n===299)throw Error('base page not ready');await sleep(150);
  }
  const check=await evaluate(B.cdp,code=>(0,eval)(code),fs.readFileSync('tests/ui_check24.js','utf8'));
  if(check.problems.length)throw Error(width+': '+JSON.stringify(check));
  results.push({viewport:[width,height],...check});console.log('PASS ui_check24 '+width+'x'+height+' problems: []');
 }
 fs.mkdirSync('lab/.runtime/final-checks',{recursive:true});
 fs.writeFileSync('lab/.runtime/final-checks/base24-page.json',JSON.stringify({base,results},null,2)+'\n');
 console.log('ALL GOOD');
}finally{await B.close();}
