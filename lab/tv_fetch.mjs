// DR Lab: M5 bars of one instrument from TradingView Desktop (read-only chart data).
// Usage: node tv_fetch.mjs <TV symbol> [count] [need5] [switch]
//   -> prints one JSON line {success, symbol, feed, interval, switched, window, pane, bars:[[time,open,high,low,close],...]}
//      or {success:false, code, error}
//
// Every TradingView window is searched (each window is its own page in the Chrome DevTools list on port 9222) for a pane
// that already shows the symbol on 5 or 1 minutes. Such a pane is read and nothing on the user's charts changes; a 5-minute
// pane is preferred (it holds the previous day), a 1-minute pane is aggregated to clock M5 by lab/live.py. The forming M5
// is the pane's last bar, so a read every minute shows the forming candle growing minute by minute.
// Only with «switch» (the «⟳ Обновить» button, never the minute refresh) may the active chart of the first window be
// switched to the symbol on 5 minutes for 2–4 s and restored. Without a pane and without «switch» nothing is touched:
// {success:false, code:'NO_PANE'} and the screen keeps its last bars.
// Why (operator 30.10 and 05.11): with two TradingView windows (ES and YM in the first, NQ on 5 and 1 minutes in the
// second) the old code looked only into the first window, found no NQ there and switched the operator's ES chart to NQ
// and back every 5 minutes; after such a switch the page also dropped from a refresh every minute to one every 5 minutes.
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { join } from 'node:path';

const MCP = process.env.TV_MCP_DIR || join(homedir(), 'Claude', 'tradingview-mcp');   // local tradingview-mcp checkout (fallbacks only)
const HOST = process.env.TV_CDP_HOST || process.env.CDP_HOST || '127.0.0.1';
const PORT = Number(process.env.TV_CDP_PORT || process.env.CDP_PORT) || 9222;
const [symbol, countArg, ...flags] = process.argv.slice(2);
const count = Math.min(Number(countArg || 500), 3000);
const NEED5 = flags.includes('need5'), SWITCH = flags.includes('switch');
const tail = String(symbol || '').split(':').pop();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const q = s => JSON.stringify(s);
// on Windows a write to a pipe is asynchronous: the process exits only after the line is out
const say = o => new Promise(r => process.stdout.write(JSON.stringify(o) + '\n', () => r()));
const watchdog = setTimeout(() => { say({ success: false, code: 'TIMEOUT', error: 'TradingView не ответил за 60 с' }).then(() => process.exit(0)); }, 60000);

// ---------- one CDP session per TradingView window ----------
function wsSession(url) {                       // Node 22+: the built-in WebSocket (as tests/trace_page.mjs)
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url), wait = new Map();
    let id = 0;
    ws.onmessage = ev => {
      const m = JSON.parse(typeof ev.data === 'string' ? ev.data : String(ev.data)), w = wait.get(m.id);
      if (!w) return;
      wait.delete(m.id);
      if (m.error) w.no(new Error(m.error.message || 'CDP error'));
      else if (m.result && m.result.exceptionDetails) w.no(new Error(m.result.exceptionDetails.text || 'evaluation error'));
      else w.ok(m.result && m.result.result ? m.result.result.value : undefined);
    };
    ws.onerror = () => reject(new Error('CDP: socket error'));
    ws.onopen = () => resolve({
      evaluate: expression => new Promise((ok, no) => { const k = ++id; wait.set(k, { ok, no }); ws.send(JSON.stringify({ id: k, method: 'Runtime.evaluate', params: { expression, returnByValue: true } })); }),
      close: () => { try { ws.close(); } catch { /* closed */ } }
    });
  });
}
let CRI = null;                                  // older Node: chrome-remote-interface from the tradingview-mcp checkout
if (typeof WebSocket !== 'function') { try { CRI = createRequire(join(MCP, 'package.json'))('chrome-remote-interface'); } catch { CRI = null; } }
async function criSession(target) {
  const c = await CRI({ host: HOST, port: PORT, target: target.id });
  return {
    evaluate: async expression => { const r = await c.Runtime.evaluate({ expression, returnByValue: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.text || 'evaluation error'); return r.result && r.result.value; },
    close: () => { try { c.close(); } catch { /* closed */ } }
  };
}
// the windows, the ones that show a chart first, in the order DevTools lists them (the first is the one the old code read)
async function windows() {
  let list;
  try { list = await (await fetch(`http://${HOST}:${PORT}/json/list`)).json(); } catch { return null; }
  const pages = list.filter(t => t.type === 'page' && /tradingview/i.test(t.url || ''));
  const chart = t => /tradingview\.com\/chart/i.test(t.url || '');
  const out = [];
  for (const t of [...pages.filter(chart), ...pages.filter(t => !chart(t))]) {
    // a page another DevTools client holds may be listed without its socket address: it is the standard one
    const url = t.webSocketDebuggerUrl || `ws://${HOST}:${PORT}/devtools/page/${t.id}`;
    try { out.push(Object.assign(await (typeof WebSocket === 'function' ? wsSession(url) : CRI ? criSession(t) : Promise.reject(new Error('no CDP client'))), { title: t.title || '', url: t.url || '' })); } catch { /* skip this window */ }
  }
  return out;
}
// last resort: the tradingview-mcp connection (it sees only the first window, as before)
async function legacyWindow() {
  try {
    const conn = await import(pathToFileURL(join(MCP, 'src', 'connection.js')).href);
    return [{ evaluate: e => conn.evaluate(e), close: () => {}, title: '', url: '' }];
  } catch { return []; }
}

// ---------- what is read in a window ----------
// every pane of the window that shows the symbol on 5 or 1 minutes and has its bars loaded
const FIND = `(function(){ try { var ws = window.TradingViewApi._chartWidgetCollection.getAll(), out = [];
  for (var k = 0; k < ws.length; k++) { var ms = ws[k].model().mainSeries(), si = ms.symbolInfo(), b = ms.bars(), iv = String(ms.interval());
    if (!si || (iv !== '5' && iv !== '1') || ms.isLoading() || b.size() < 50) continue;
    var name = String(si.pro_name || si.full_name || ''); if (name.slice(-${tail.length}) !== ${q(tail)}) continue;
    out.push({ pane: k, interval: iv, n: b.size(), feed: name }); }
  return out; } catch (e) { return []; } })()`;
// the bars of one pane, if it still shows the symbol on that interval (the user may have changed it in between)
const READ = (pane, iv) => `(function(){ try { var ms = window.TradingViewApi._chartWidgetCollection.getAll()[${pane}].model().mainSeries();
  var si = ms.symbolInfo(), name = String(si && (si.pro_name || si.full_name) || '');
  if (String(ms.interval()) !== ${q(iv)} || name.slice(-${tail.length}) !== ${q(tail)}) return null;
  var b = ms.bars(), out = [], end = b.lastIndex();
  for (var i = Math.max(b.firstIndex(), end - ${count} + 1); i <= end; i++) { var v = b.valueAt(i); if (v) out.push([v[0], v[1], v[2], v[3], v[4]]); }
  return out; } catch (e) { return null; } })()`;
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const PROBE = `(function(){ try { var c = ${CHART}; var ms = c._chartWidget.model().mainSeries(); var b = ms.bars();
  var si = ms.symbolInfo && ms.symbolInfo(); var n = b && typeof b.size === 'function' ? b.size() : 0;
  var last = n ? b.valueAt(b.lastIndex()) : null;
  return { symbol: c.symbol(), res: String(c.resolution()), loading: !!(ms.isLoading && ms.isLoading()),
           series: si ? String(si.pro_name || si.full_name || si.ticker || si.name) : '', n: n, last: last ? last[0] : null };
  } catch (e) { return null; } })()`;
const SET = (sym, res) => `(function(){ var c = ${CHART}; ${sym ? `c.setSymbol(${q(sym)}, {});` : ''} ${res ? `c.setResolution(${q(res)}, {});` : ''} return true; })()`;
const ACTIVE_BARS = `(function(){ var b = ${CHART}._chartWidget.model().mainSeries().bars(); var out = []; var end = b.lastIndex();
  for (var i = Math.max(b.firstIndex(), end - ${count} + 1); i <= end; i++) { var v = b.valueAt(i); if (v) out.push([v[0], v[1], v[2], v[3], v[4]]); } return out; })()`;

// the old way, only on «⟳ Обновить»: switch the active chart of the first window to the symbol on 5 minutes, read, restore
async function switched(win) {
  let prev = null;
  try {
    prev = await win.evaluate(PROBE);
    if (!prev) throw new Error('TradingView chart is not available');
    await win.evaluate(SET(symbol, '5'));
    let stable = 0, lastSig = '', data = null;
    for (let i = 0; i < 120 && !data; i++) {
      await sleep(250);
      const p = await win.evaluate(PROBE);
      if (!p || p.loading || p.res !== '5' || !p.series.endsWith(tail) || p.n < 50) { stable = 0; continue; }
      const sig = `${p.n}:${p.last}`;
      stable = sig === lastSig ? stable + 1 : 0; lastSig = sig;
      if (stable >= 2) data = await win.evaluate(ACTIVE_BARS);
    }
    if (!data || !data.length) throw new Error('chart did not return bars for ' + symbol);
    const feed = (await win.evaluate(PROBE) || {}).series || null;
    return { success: true, symbol, feed, interval: '5', switched: true, window: 0, window_url: win.url, bars: data };
  } catch (e) {
    return { success: false, code: 'SWITCH_FAILED', error: String((e && e.message) || e) };
  } finally {
    try { if (prev) await win.evaluate(SET(prev.symbol !== symbol ? prev.symbol : null, prev.res !== '5' ? prev.res : null)); } catch { /* leave chart */ }
  }
}

let wins = [];
try {
  wins = (await windows()) || [];
  if (!wins.length) wins = await legacyWindow();
  if (!wins.length) { await say({ success: false, code: 'NO_TRADINGVIEW', error: 'TradingView chart is not available (port ' + PORT + ')' }); }
  else {
    // every window's panes with the symbol; a 5-minute pane first (it reaches back to the previous day), then a 1-minute one
    const found = [];
    for (let w = 0; w < wins.length; w++) {
      let panes = [];
      try { panes = (await wins[w].evaluate(FIND)) || []; } catch { panes = []; }
      for (const p of panes) found.push(Object.assign({ window: w }, p));
    }
    const order = NEED5 ? ['5'] : ['5', '1'];
    let result = null;
    for (const iv of order) {
      for (const f of found.filter(x => x.interval === iv)) {
        let bars = null;
        try { bars = await wins[f.window].evaluate(READ(f.pane, iv)); } catch { bars = null; }
        if (bars && bars.length) { result = { success: true, symbol, feed: f.feed, window: f.window, window_url: wins[f.window].url, pane: f.pane, interval: iv, switched: false, bars }; break; }
      }
      if (result) break;
    }
    if (!result && SWITCH) result = await switched(wins[0]);
    if (!result) result = { success: false, code: 'NO_PANE', windows: wins.length,
      error: tail + ' нет на ' + (NEED5 ? '5' : '1 или 5') + ' мин ни в одном окне TradingView (окон: ' + wins.length + '); график не трогаю' };
    await say(result);
  }
} catch (e) {
  await say({ success: false, code: 'ERROR', error: String((e && e.message) || e) });
} finally {
  for (const w of wins) { try { w.close(); } catch { /* closed */ } }
  clearTimeout(watchdog);
  process.exit(0);
}
