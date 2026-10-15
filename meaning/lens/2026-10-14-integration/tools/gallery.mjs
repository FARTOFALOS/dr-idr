import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath,pathToFileURL } from 'node:url';
import { startChrome,evaluate } from '../../../../tests/trace_page.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const pkg=path.join(root,'meaning/lens/2026-10-14-integration');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const B=await startChrome();
try{
 await B.cdp.send('Page.navigate',{url:pathToFileURL(path.join(pkg,'comparison/index.html')).href});
 await sleep(1200);
 const result=await evaluate(B.cdp,async()=>{
  const problems=[],scene=document.getElementById('scene'),size=document.getElementById('size');
  let checked=0;
  for(const s of [...scene.options])for(const z of [...size.options])for(const b of ['both','a','b']){
   scene.value=s.value;size.value=z.value;document.getElementById(b).click();
   for(let k=0;k<100&&[...document.images].some(i=>!i.complete);k++)await new Promise(r=>setTimeout(r,20));
   if(document.images.length!==(b==='both'?2:1)||[...document.images].some(i=>!i.naturalWidth))problems.push(s.value+'/'+z.value+'/'+b);
   checked++;
  }
  scene.value='OPEN';size.value='1600';document.getElementById('both').click();
  return {checked,problems};
 });
 if(result.problems.length)throw new Error(JSON.stringify(result));
 fs.writeFileSync(path.join(pkg,'comparison/gallery-check.json'),JSON.stringify(result,null,1)+'\n');
 console.log('GALLERY',result.checked,'scene/size/display combinations; all screenshot resources load');
}finally{await B.close();}
