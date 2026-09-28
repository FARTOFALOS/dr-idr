// DR Lab: one-process fetch of M5 bars from TradingView Desktop (read-only chart data), restoring the user's chart.
// Usage: node tv_fetch.mjs <TV symbol> [count]  -> prints {success, symbol, feed, bars:[[time,open,high,low,close],...]}
// Readiness is judged by the chart itself: symbol and resolution switched, bar series non-empty and stable.
import { pathToFileURL } from 'node:url';
import { homedir } from 'node:os';
import { join } from 'node:path';

const base = join(process.env.TV_MCP_DIR || join(homedir(), 'Claude', 'tradingview-mcp'), 'src');   // local tradingview-mcp checkout
const conn = await import(pathToFileURL(join(base, 'connection.js')).href);
const { evaluate, KNOWN_PATHS } = conn;
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const BARS = KNOWN_PATHS.mainSeriesBars;
const [symbol, countArg] = process.argv.slice(2);
const count = Math.min(Number(countArg || 500), 1000);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const q = s => JSON.stringify(s);

const probe = () => evaluate(`(function(){ try { var c = ${CHART}; var ms = c._chartWidget.model().mainSeries(); var b = ms.bars();
  var si = ms.symbolInfo && ms.symbolInfo(); var n = b && typeof b.size === 'function' ? b.size() : 0;
  var last = n ? b.valueAt(b.lastIndex()) : null;
  return { symbol: c.symbol(), res: String(c.resolution()), loading: !!(ms.isLoading && ms.isLoading()),
           series: si ? String(si.pro_name || si.full_name || si.ticker || si.name) : '', n: n, last: last ? last[0] : null };
  } catch (e) { return null; } })()`);
const setChart = (sym, res) => evaluate(`(function(){ var c = ${CHART};
  ${sym ? `c.setSymbol(${q(sym)}, {});` : ''} ${res ? `c.setResolution(${q(res)}, {});` : ''} return true; })()`);

// First choice: a pane of the user's layout that already shows this symbol on 5 minutes -> read it, switch nothing.
const tailSym = symbol.split(':')[1];
const passive = await evaluate(`(function(){ try { var ws = window.TradingViewApi._chartWidgetCollection.getAll();
  var order = ['5', '1'];
  for (var o = 0; o < order.length; o++) for (var k = 0; k < ws.length; k++) { var ms = ws[k].model().mainSeries(); var si = ms.symbolInfo(); var b = ms.bars();
    if (!si || String(ms.interval()) !== order[o] || ms.isLoading() || b.size() < 50) continue;
    var name = String(si.pro_name || si.full_name || ''); if (name.slice(-${tailSym.length}) !== ${q(tailSym)}) continue;
    var out = []; var end = b.lastIndex();
    for (var i = Math.max(b.firstIndex(), end - ${count} + 1); i <= end; i++) { var v = b.valueAt(i); if (v) out.push([v[0], v[1], v[2], v[3], v[4]]); }
    return { feed: name, bars: out, pane: k, interval: order[o] }; } } catch (e) {} return null; })()`);
if (passive && passive.bars && passive.bars.length && !(process.argv[4] === 'need5' && passive.interval !== '5')) {
  console.log(JSON.stringify({ success: true, symbol, feed: passive.feed, pane: passive.pane, interval: passive.interval, switched: false, bars: passive.bars }));
  process.exit(0);
}

let prev = null;
try {
  prev = await probe();
  if (!prev) throw new Error('TradingView chart is not available');
  await setChart(symbol, '5');
  const tail = symbol.split(':')[1];
  let stable = 0, lastSig = '', data = null;
  for (let i = 0; i < 120 && !data; i++) {
    await sleep(250);
    const p = await probe();
    if (!p || p.loading || p.res !== '5' || !p.series.endsWith(tail) || p.n < 50) { stable = 0; continue; }
    const sig = `${p.n}:${p.last}`;
    stable = sig === lastSig ? stable + 1 : 0; lastSig = sig;
    if (stable >= 2) {
      data = await evaluate(`(function(){ var b = ${BARS}; var out = []; var end = b.lastIndex();
        for (var i = Math.max(b.firstIndex(), end - ${count} + 1); i <= end; i++) { var v = b.valueAt(i);
          if (v) out.push([v[0], v[1], v[2], v[3], v[4]]); } return out; })()`);
    }
  }
  if (!data || !data.length) throw new Error('chart did not return bars for ' + symbol);
  const feed = (await probe() || {}).series || null;
  console.log(JSON.stringify({ success: true, symbol, feed, interval: '5', switched: true, bars: data }));
} catch (e) {
  console.log(JSON.stringify({ success: false, error: String((e && e.message) || e) }));
} finally {
  try { if (prev) await setChart(prev.symbol !== symbol ? prev.symbol : null, prev.res !== '5' ? prev.res : null); } catch { /* leave chart */ }
  process.exit(0);
}
