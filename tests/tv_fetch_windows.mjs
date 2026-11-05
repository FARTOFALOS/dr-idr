// DR Lab · lab/tv_fetch.mjs reads live bars from any TradingView window and never switches a chart unless asked.
//
//     node tests/tv_fetch_windows.mjs            (Chrome or Edge; set CHROME=<path> if it is elsewhere)
//
// A throw-away headless Chrome plays TradingView Desktop: two pages whose addresses look like TradingView charts, each
// with a fake window.TradingViewApi (the chart-widget paths tv_fetch.mjs reads), laid out as the operator's two windows
// of 30.10: the first holds ES on 1 minute and YM on 15 minutes, the second NQ on 5 and on 1 minute. tv_fetch.mjs is run
// against this Chrome's DevTools port, as against TradingView's 9222. Checked:
//   - NQ is read from the 5-minute pane of the second window, nothing switched (the old code switched the first
//     window's chart to NQ and back: operator 30.10, 05.11);
//   - ES is read from its 1-minute pane; the forming bar is the pane's last bar;
//   - YM, on no 1- or 5-minute pane, is NO_PANE and no chart is touched (the minute refresh);
//   - YM with «switch» (the «⟳ Обновить» button) switches the first window's active chart and restores it;
//   - «need5» takes only a 5-minute pane.
// Nothing is written; the browser profile is temporary. Exit code 0 = every check passed.
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FETCH = path.join(HERE, '..', 'lab', 'tv_fetch.mjs');
const CHROMES = [process.env.CHROME, 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', '/usr/bin/google-chrome', '/usr/bin/chromium', '/opt/pw-browsers/chromium'].filter(Boolean);
const sleep = ms => new Promise(r => setTimeout(r, ms));
let bad = 0;
const ck = (ok, what) => { if (!ok) bad++; console.log((ok ? '  ok   ' : '  FAIL ') + what); };

// one fake TradingView window: panes = [[symbol, interval], ...]; the first pane is the active chart
const PAGE = panes => `<!doctype html><title>TradingView</title><script>
(function () {
  var T0 = 1793800800, log = window.__log = [];
  function series(sym, iv) {
    var st = { sym: sym, iv: String(iv), bars: [] };
    function fill() { var step = st.iv === '1' ? 60 : st.iv === '5' ? 300 : 900, n = 400; st.bars = [];
      for (var i = 0; i < n; i++) { var t = T0 + (i - n + 1) * step, o = 100 + i; st.bars.push([t, o, o + 2, o - 1, o + 1]); } }
    fill();
    return { st: st, fill: fill, symbolInfo: function () { return { pro_name: st.sym }; }, interval: function () { return st.iv; },
      isLoading: function () { return false; },
      bars: function () { return { size: function () { return st.bars.length; }, firstIndex: function () { return 0; },
        lastIndex: function () { return st.bars.length - 1; }, valueAt: function (i) { return st.bars[i]; } }; } };
  }
  var widgets = ${JSON.stringify(panes)}.map(function (p) { var s = series(p[0], p[1]); return { s: s, model: function () { return { mainSeries: function () { return s; } }; } }; });
  var active = widgets[0];
  var api = { _chartWidget: active, symbol: function () { return active.s.st.sym; }, resolution: function () { return active.s.st.iv; },
    setSymbol: function (x) { log.push('symbol ' + x); active.s.st.sym = x; active.s.fill(); },
    setResolution: function (x) { log.push('resolution ' + x); active.s.st.iv = String(x); active.s.fill(); } };
  window.TradingViewApi = { _chartWidgetCollection: { getAll: function () { return widgets; } }, _activeChartWidgetWV: { value: function () { return api; } } };
  window.__state = function () { return widgets.map(function (w) { return w.s.st.sym + '@' + w.s.st.iv; }); };
})();
</script>`;
const LAYOUT = { one: [['CME_MINI:ES1!', '1'], ['CBOT_MINI:YM1!', '15']], two: [['CME_MINI:NQ1!', '5'], ['CME_MINI:NQ1!', '1']] };

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url), pend = new Map();
    let id = 0;
    ws.onopen = () => resolve({
      send(method, params = {}) { const i = ++id; ws.send(JSON.stringify({ id: i, method, params })); return new Promise((ok, no) => pend.set(i, { ok, no })); },
      close() { try { ws.close(); } catch (e) { /* closed */ } }
    });
    ws.onmessage = ev => { const m = JSON.parse(ev.data); const p = m.id && pend.get(m.id); if (p) { pend.delete(m.id); m.error ? p.no(new Error(JSON.stringify(m.error))) : p.ok(m.result); } };
    ws.onerror = () => reject(new Error('CDP socket error'));
  });
}
const value = async (port, urlPart, expression) => {
  const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const t = list.find(x => x.type === 'page' && x.url.includes(urlPart));
  const c = await connect(t.webSocketDebuggerUrl);
  try { return (await c.send('Runtime.evaluate', { expression, returnByValue: true })).result.value; } finally { c.close(); }
};
const run = (port, symbol, ...flags) => {
  const outp = execFileSync(process.execPath, [FETCH, symbol, '600', ...flags], { env: { ...process.env, TV_CDP_PORT: String(port), TV_MCP_DIR: path.join(os.tmpdir(), 'no-tradingview-mcp') }, encoding: 'utf8', timeout: 90000 });
  return JSON.parse(outp.trim().split('\n').pop());
};

const exe = CHROMES.find(p => fs.existsSync(p));
if (!exe) { console.log('no Chrome or Edge found (set CHROME)'); process.exit(1); }
const server = http.createServer((req, res) => { const k = req.url.split('/').pop(); res.writeHead(LAYOUT[k] ? 200 : 404, { 'content-type': 'text/html; charset=utf-8' }); res.end(LAYOUT[k] ? PAGE(LAYOUT[k]) : ''); });
await new Promise(r => server.listen(0, '127.0.0.1', r));
const site = `http://127.0.0.1:${server.address().port}/tradingview.com/chart`;
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'drlab-tvfetch-'));
const proc = spawn(exe, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--no-sandbox',
  '--remote-debugging-port=0', '--user-data-dir=' + prof, site + '/one'], { stdio: 'ignore' });
try {
  let port = null;
  for (let i = 0; i < 150 && !port; i++) {
    try { port = fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim() || null; } catch (e) { /* not yet */ }
    if (!port) await sleep(100);
  }
  if (!port) throw new Error('Chrome did not open its debugging port');
  await fetch(`http://127.0.0.1:${port}/json/new?${site}/two`, { method: 'PUT' });   // headless Chrome opens one page at start
  for (let i = 0; i < 100; i++) {
    const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    if (list.filter(t => t.type === 'page' && /tradingview\.com\/chart/.test(t.url)).length === 2) break;
    await sleep(100);
  }
  const before = [await value(port, '/one', 'JSON.stringify(window.__state())'), await value(port, '/two', 'JSON.stringify(window.__state())')];
  const untouched = async () => (await value(port, '/one', 'window.__log.length')) === 0 && (await value(port, '/two', 'window.__log.length')) === 0;

  console.log('NQ: on 5 and 1 minutes in the second window only');
  const nq = run(port, 'CME_MINI:NQ1!');
  ck(nq.success && nq.switched === false, 'read without switching (' + (nq.error || '') + ')');
  ck(/\/two$/.test(nq.window_url || '') && nq.interval === '5' && nq.feed === 'CME_MINI:NQ1!', 'from the second window\'s 5-minute pane (' + nq.window_url + ', ' + nq.interval + ' min)');
  ck(nq.bars && nq.bars.length === 400 && nq.bars[399][0] === 1793800800, 'all bars up to the forming one (' + (nq.bars || []).length + ')');
  ck(await untouched(), 'no chart of either window was switched');

  console.log('ES: on 1 minute in the first window');
  const es = run(port, 'CME_MINI:ES1!');
  ck(es.success && es.switched === false && /\/one$/.test(es.window_url || '') && es.interval === '1', 'read from the first window\'s 1-minute pane, nothing switched');
  ck(await untouched(), 'no chart of either window was switched');

  console.log('YM: only on 15 minutes — the minute refresh');
  const ym = run(port, 'CBOT_MINI:YM1!');
  ck(!ym.success && ym.code === 'NO_PANE' && /YM1! нет на 1 или 5 мин/.test(ym.error), 'NO_PANE with its reason (' + ym.error + ')');
  ck(await untouched(), 'no chart of either window was switched');

  console.log('NQ with need5 (the once-a-day backfill)');
  const n5 = run(port, 'CME_MINI:NQ1!', 'need5');
  ck(n5.success && n5.interval === '5' && n5.switched === false, 'a 5-minute pane only, nothing switched');

  console.log('YM with «switch» — the «⟳ Обновить» button');
  // the switch happens in the window DevTools lists first, as the old single-window read did; the other one is untouched
  const listed = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).filter(t => t.type === 'page' && /tradingview\.com\/chart/.test(t.url));
  const first = /\/one$/.test(listed[0].url) ? '/one' : '/two', other = first === '/one' ? '/two' : '/one';
  const yms = run(port, 'CBOT_MINI:YM1!', 'switch');
  ck(yms.success && yms.switched === true && yms.interval === '5' && (yms.window_url || '').endsWith(first), 'read by switching the active chart of the first listed window, ' + first + ' (' + (yms.error || '') + ')');
  const logF = await value(port, first, 'JSON.stringify(window.__log)'), logO = await value(port, other, 'JSON.stringify(window.__log)');
  const back = first === '/one' ? ['symbol CME_MINI:ES1!', 'resolution 1'] : ['symbol CME_MINI:NQ1!'];
  ck(logF === JSON.stringify(['symbol CBOT_MINI:YM1!', 'resolution 5', ...back]) && logO === '[]', 'switched to YM on 5 minutes and back, the other window untouched (' + logF + ' / ' + logO + ')');
  const after = [await value(port, '/one', 'JSON.stringify(window.__state())'), await value(port, '/two', 'JSON.stringify(window.__state())')];
  ck(JSON.stringify(after) === JSON.stringify(before), 'both windows as they were (' + after.join(' ') + ')');
} catch (e) {
  bad++; console.log('  FAIL ' + e.message);
} finally {
  proc.kill(); server.close();
  for (let i = 0; i < 20; i++) { try { fs.rmSync(prof, { recursive: true, force: true }); break; } catch (e) { await sleep(250); } }
}
console.log(bad ? `${bad} check(s) failed` : 'ALL GOOD');
process.exit(bad ? 1 : 0);
