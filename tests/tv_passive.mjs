import assert from 'node:assert/strict';
import vm from 'node:vm';
import {collectPassive} from '../lab/tv_passive.mjs';

const bars = Array.from({length:60}, (_,i)=>[1700000000+i*300,100,102,99,101]);
function widget(symbol, interval, loading=false) {
  return {model:()=>({mainSeries:()=>({symbolInfo:()=>({pro_name:symbol}), interval:()=>interval,
    isLoading:()=>loading, bars:()=>({size:()=>bars.length, firstIndex:()=>0,
      lastIndex:()=>bars.length-1, valueAt:i=>bars[i]})})})};
}
const windows = {one:[widget('CME_MINI:NQ1!', '1')], two:[widget('CME_MINI:NQ1!', '5'),widget('CBOT_MINI:YM1!', '5')],
  wrong:[widget('OTHER:NQ1!', '5'), widget('CME_MINI:ES1!', '5', true)]};
let selected, reads=0;
const conn = {reconnectTo:async id=>{selected=id;}, evaluate:async code=>{
  reads++;
  assert.doesNotMatch(code, /setSymbol|setResolution|activeChart|bringToFront/);
  return vm.runInNewContext(code,{window:{TradingViewApi:{_chartWidgetCollection:{getAll:()=>windows[selected]}}}});
}};
const targets=Object.keys(windows).map(id=>({id,type:'page',url:'https://www.tradingview.com/chart/abc/'}));
targets.push({id:'shell',type:'page',url:'https://www.tradingview.com/desktop/'});
let got=await collectPassive(conn,targets,'CME_MINI:NQ1!',10);
assert.equal(got.target,'two');assert.equal(got.interval,'5');assert.equal(got.bars.length,10);assert.equal(got.switched,false);
assert.equal(reads,3);
got=await collectPassive(conn,targets,'CME_MINI:ES1!',10);
assert.equal(got.success,false);assert.equal(got.switched,false);
got=await collectPassive(conn,targets.slice(0,1),'CME_MINI:NQ1!',10,true);
assert.equal(got.success,false);
console.log('PASS: all-window passive selection, M5 preference, exact feed, loading rejection, missing M5 and no chart mutations');
