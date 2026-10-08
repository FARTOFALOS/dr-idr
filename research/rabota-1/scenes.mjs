// research/rabota-1 · the working screen 24 as it is, on real history states at different stages of a session, each as
// the live screen at its cut (no candle after it). For the reconstruction of the trader's work (meaning/17).
//
//     node research/rabota-1/scenes.mjs
//
// The machinery is research/now-1/shots.mjs (fail-closed provenance, control check, live-at-cut interception), with the
// variant always A and the real build only.
//
// Each scene is the live screen at its cut: inside that browser only, the page's requests for «today» are answered with
// the history day cut at the cut (no candle after it, no forming candle), so the trader sees what he would have seen
// then, not what came later. The page is served by the running local server; for B and C only its two files
// (index.html, d24.js) are replaced by the research build (research/now-1/dist) between the browser and the server.
//
// Fail closed: a shot is kept only if its provenance is the scene's — the day on screen is the scene's date cut at its
// cut and marked as the synthetic live day; instrument, session, slice, family snapshot and the «Сейчас» answer the page
// used are those the server gives directly for that date and cut (asked by this script, not through the page); no
// contract violation; B and C used exactly A's «Сейчас» answer. The control is checked first: the build the server
// serves is lab/dist/24 on disk and the build of the candidate passport, and the research copy in the variant A renders
// it pixel for pixel (the page's clock frozen). Any failure stops the run and writes no image.
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '..', '..');
const NOW1 = path.join(ROOT, 'research', 'now-1');
const SERVER = 'http://127.0.0.1:8767', BASE = SERVER + '/24/';
const DIST = path.join(NOW1, 'dist'), IMG = path.join(HERE, 'img');
// chosen by fixed rules (README): id, instrument, feed, session, date, cut (ET minutes), stage
const SCENES = [
  ['pre', 'NQ', 'CME_MINI:NQ1!', 'RDR', '2025-02-27', 655, 'коробка сформирована, подтверждения ещё нет'],
  ['r1', 'ES', 'CME_MINI:ES1!', 'RDR', '2024-03-04', 695, 'после подтверждения: цена откатила к сегодняшнему дну отката'],
  ['r2', 'YM', 'CBOT_MINI:YM1!', 'ODR', '2024-01-19', 305, 'после подтверждения: откат от максимума идёт, цена далеко над дном отката'],
  ['brk', 'NQ', 'CME_MINI:NQ1!', 'RDR', '2025-03-07', 875, 'DR сломан: семья слома'],
  ['late', 'NQ', 'CME_MINI:NQ1!', 'ODR', '2025-06-25', 420, 'поздний срез'],
];
const CHROMES = [process.env.CHROME, 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'].filter(Boolean);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const lf = b => Buffer.from(b.toString('utf8').replace(/\r\n/g, '\n'), 'utf8');
const sha = b => crypto.createHash('sha256').update(lf(b)).digest('hex');
const fail = msg => { throw new Error('NOT VALID: ' + msg); };

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url), pend = new Map(), handlers = [];
    let id = 0;
    ws.onopen = () => resolve({
      send(method, params = {}) { const i = ++id; ws.send(JSON.stringify({ id: i, method, params })); return new Promise((ok, no) => pend.set(i, { ok, no, method })); },
      on(fn) { handlers.push(fn); },
      close() { try { ws.close(); } catch (e) { /* closed */ } }
    });
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.id) { const p = pend.get(m.id); pend.delete(m.id); if (p) m.error ? p.no(new Error(p.method + ': ' + JSON.stringify(m.error))) : p.ok(m.result); }
      else handlers.forEach(h => h(m));
    };
    ws.onerror = e => reject(new Error('CDP: ' + (e.message || 'socket error')));
  });
}

// ---- the control, before anything is shot: what the server serves is the working build on disk and the passport's
const served = { 'index.html': Buffer.from(await (await fetch(BASE)).arrayBuffer()), 'd24.js': Buffer.from(await (await fetch(BASE + 'd24.js')).arrayBuffer()) };
const research = { 'index.html': fs.readFileSync(path.join(DIST, 'index.html')), 'd24.js': fs.readFileSync(path.join(DIST, 'd24.js')) };
const passport = JSON.parse(fs.readFileSync(path.join(ROOT, 'spec', 'ekran-24', 'swpc-kandidat.json'), 'utf8'));
const build = {
  real: { d24_js: sha(served['d24.js']), index_html: sha(served['index.html']) },
  research: { d24_js: sha(research['d24.js']), index_html: sha(research['index.html']) },
};
for (const f of ['index.html', 'd24.js']) {
  const disk = sha(fs.readFileSync(path.join(ROOT, 'lab', 'dist', '24', f)));
  if (sha(served[f]) !== disk) fail(`the server serves a ${f} that is not lab/dist/24/${f} on disk`);
  if (passport.served_sha256[f] !== disk) fail(`lab/dist/24/${f} is not the build of the candidate passport (spec/ekran-24/swpc-kandidat.json)`);
}

const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'now1-'));
const exe = CHROMES.find(p => fs.existsSync(p));
const proc = spawn(exe, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, 'about:blank'], { stdio: 'ignore' });
let port = null;
for (let i = 0; i < 150 && !port; i++) { try { port = fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim() || null; } catch (e) { /* not yet */ } if (!port) await sleep(100); }
const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const cdp = await connect(list.find(t => t.type === 'page').webSocketDebuggerUrl);
await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
const errors = [];
cdp.on(m => { if (m.method === 'Runtime.exceptionThrown') errors.push((m.params.exceptionDetails.exception || {}).description || m.params.exceptionDetails.text); });

// which files the page gets: 'real' = the server's own build (untouched), 'research' = research/now-1/dist
let serve = 'real';
await cdp.send('Fetch.enable', { patterns: [{ urlPattern: '*/24/d24.js*' }, { urlPattern: '*/24/' }, { urlPattern: '*/24/index.html*' }] });
cdp.on(async m => {
  if (m.method !== 'Fetch.requestPaused') return;
  if (serve === 'real') return cdp.send('Fetch.continueRequest', { requestId: m.params.requestId }).catch(() => {});
  const f = /d24\.js/.test(m.params.request.url) ? 'd24.js' : 'index.html';
  cdp.send('Fetch.fulfillRequest', { requestId: m.params.requestId, responseCode: 200, body: research[f].toString('base64'),
    responseHeaders: [{ name: 'Content-Type', value: f === 'd24.js' ? 'application/javascript; charset=utf-8' : 'text/html; charset=utf-8' }, { name: 'Cache-Control', value: 'no-store' }] }).catch(() => {});
});
let script = null;
async function variant(v, sc) {
  if (script) await cdp.send('Page.removeScriptToEvaluateOnNewDocument', { identifier: script });
  const L = { date: sc[4], cut: sc[5], feed: sc[2] };
  // the variant; the page's clock frozen (only the countdown under the last price reads it in a cut scene); «today» =
  // the history day cut at the scene's cut; silent stand-ins for sound and system notifications
  script = (await cdp.send('Page.addScriptToEvaluateOnNewDocument', { source: `window.__NOWV=${JSON.stringify(v)};
    (() => { const RD = Date, T0 = 1791460800000; class FD extends RD { constructor(...a) { super(...(a.length ? a : [T0])); } static now() { return T0; } } window.Date = FD; })();
    try { localStorage.setItem('drlab.auto', '0'); } catch (e) {}
    (() => { const L = ${JSON.stringify(L)}, real = window.fetch.bind(window);
      window.fetch = async (input, init) => {
        let url = String(input && input.url ? input.url : input);
        if (!['/api/d24/day', '/api/d24/family', '/api/d24/now'].some(p => url.includes(p)) || url.includes('date=')) return real(input, init);
        url = url.replace('&refresh=1', '') + (url.includes('?') ? '&' : '?') + 'date=' + L.date;
        const resp = await real(url, init);
        if (!url.includes('/api/d24/day')) return resp;
        const b = await resp.json();
        if (b.status === 'ok') { Object.assign(b, { source: 'live', fetched_at: new Date().toISOString(), now: L.cut, feed: L.feed, __scene: L.date }); b.bars = b.bars.filter(x => x[0] < L.cut); }
        return new Response(JSON.stringify(b), { status: resp.status, headers: { 'Content-Type': 'application/json' } });
      }; })();
    window.Notification=function(){};window.Notification.permission='denied';window.Notification.requestPermission=()=>Promise.resolve('denied');
    window.AudioContext=window.webkitAudioContext=function(){return{createOscillator(){return{connect(){},start(){},stop(){},frequency:{setValueAtTime(){}},type:''}},createGain(){return{connect(){},gain:{setValueAtTime(){},exponentialRampToValueAtTime(){},linearRampToValueAtTime(){}}}},destination:{},currentTime:0,resume(){return Promise.resolve()},close(){}}};` })).identifier;
}
async function ev(fn, ...args) {
  const r = await cdp.send('Runtime.evaluate', { expression: `(${fn})(...${JSON.stringify(args)})`, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception || {}).description || r.exceptionDetails.text);
  return r.result.value;
}
async function open(sc, extra = '') {
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
  await cdp.send('Page.navigate', { url: 'about:blank' }); await sleep(80);
  await cdp.send('Page.navigate', { url: BASE + '#inst=' + sc[1] + extra });
  for (let i = 0; i < 100; i++) { if (await ev(() => !!(window.__d24 && document.readyState === 'complete')).catch(() => false)) break; await sleep(100); }
  // render until the family and «Сейчас» have answered and the passports are verified (as tests/swpc11_browser.mjs);
  // then report what is on screen and where it came from
  return ev(async () => {
    // performance.now, not Date: the page's Date is frozen for the pixel comparison
    const D = window.__d24, wait = ms => new Promise(r => setTimeout(r, ms)), t0 = performance.now();
    for (;;) {
      D.render(true);
      const c = D.cur(), idle = D.A.pending.size === 0 && D.A.nowPending.size === 0 && !D.A.busy, blk = document.querySelector('.p24-nowblk');
      if (idle && c.F && blk && !/считаю/.test(blk.innerText) && performance.now() - t0 > 400) break;
      if (idle && !c.F && !['confirmed', 'broken', 'done'].includes(c.s.status) && performance.now() - t0 > 1500) break;   // no family yet
      if (performance.now() - t0 > 20000) break;
      await wait(100);
    }
    for (let i = 0; i < 25 && D.contract().unchecked; i++) { await D.verify(); await wait(80); }
    D.render(true); await wait(150);
    const c = D.cur(), F = c.F, n = F ? D.nowOf(c) : null, day = D.A.day || {}, k = D.contract();
    const pick = E => E && E.continuation ? { mode: E.mode, p: E.continuation.p_new_extreme, b: E.continuation.p_new_bounds, support: E.continuation.support,
      q: E.continuation.delta_if_new, t: E.continuation.time_to_new, state: E.state } : null;
    const b = document.querySelector('.p24-nowblk'), sel = document.querySelector('.p24-sel');
    return {
      variant: window.__NOWV, text: b ? b.innerText : null, pinned: sel ? sel.parentElement.innerText.slice(0, 400) : null,
      day: { date: day.date || null, scene: day.__scene || null, source: day.source, now: day.now, feed: day.feed, last_bar: day.bars && day.bars.length ? day.bars[day.bars.length - 1][0] : null },
      inst: D.A.inst, src: D.A.src, session: c.s.k, live: c.live, slice: c.obs,
      family: F ? { snapshot: F.r.snapshot_id, family: F.r.family_id, N: F.N, view: F.view } : null,
      now: n ? { status: n.status, cut: n.cut.cut, snapshot: n.cut.snapshot_id, family: n.cut.family_id, R: pick(n.R), X: pick(n.X) } : null,
      contract: { violations: k.violations, unchecked: k.unchecked }
    };
  });
}
const shot = async () => Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png' })).data, 'base64');
async function hoverR() {
  const at = await ev(() => { const e = [...document.querySelectorAll('.p24-nowblk .p21-link')][0]; if (!e) return null; const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + 10]; });
  if (!at) fail('no «Сейчас» row to hover');
  await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: at[0], y: at[1] });
  await sleep(400); await ev(() => window.__d24.render(true)); await sleep(150);
}
const same = (x, y) => JSON.stringify(x) === JSON.stringify(y);
// the server asked directly (not through the page): the family and «Сейчас» of the scene's date and cut
async function direct(sc) {
  const [, inst, , session, date, cut] = sc, q = `instrument=${inst}&session=${session}&at=${cut}&date=${date}`;
  const fam = await (await fetch(`${SERVER}/api/d24/family?${q}&view=auto`)).json(), now = await (await fetch(`${SERVER}/api/d24/now?${q}&view=auto`)).json();
  const pick = E => E && E.continuation ? { mode: E.mode, p: E.continuation.p_new_extreme, b: E.continuation.p_new_bounds, support: E.continuation.support,
    q: E.continuation.delta_if_new, t: E.continuation.time_to_new, state: E.state } : null;
  return { snapshot: fam.snapshot_id, family: fam.family_id, now: { status: now.status, cut: now.cut && now.cut.cut, snapshot: now.cut && now.cut.snapshot_id, family: now.cut && now.cut.family_id, R: pick(now.R), X: pick(now.X) } };
}
function verify(sc, v, P, D) {
  const [id, inst, , session, date, cut] = sc, at = `${id} ${v}: `;
  if (P.variant !== v) fail(at + `the page ran the variant ${P.variant}`);
  if (P.day.scene !== date || P.day.date !== date) fail(at + `the day on screen is ${P.day.date} (scene ${date}): the interception did not work`);
  if (P.day.source !== 'live' || P.day.now !== cut || !(P.day.last_bar < cut)) fail(at + `the day is not cut at ${cut} (now ${P.day.now}, last candle ${P.day.last_bar})`);
  if (P.inst !== inst || P.session !== session || !P.live || P.slice !== cut) fail(at + `context ${P.inst} ${P.session} live=${P.live} slice ${P.slice}`);
  if (!P.family || P.family.snapshot !== D.snapshot || P.family.family !== D.family) fail(at + `family ${P.family && P.family.snapshot} != server ${D.snapshot}`);
  if (!P.now || !same(P.now, D.now)) fail(at + '«Сейчас» on the page is not the server\'s answer for this date and cut');
  if (P.now.status !== 'OK' || P.now.snapshot !== P.family.snapshot || P.now.cut !== cut) fail(at + `«Сейчас» ${P.now.status} on ${P.now.snapshot} at ${P.now.cut}`);
  if (P.contract.violations.length || P.contract.unchecked) fail(at + 'contract: ' + P.contract.violations.join('; ') + (P.contract.unchecked ? ' · unchecked ' + P.contract.unchecked : ''));
}


// the numbers the page itself shows on this scene: every passport of its snapshot (estimand, parameters, counts), the
// panel's text, the drawer «Окна семьи» opened (order, level ladder, family path) and the toolbar
const dump = () => ev(async () => {
  const D = window.__d24, c = D.cur(), F = c.F, wait = ms => new Promise(r => setTimeout(r, ms));
  const panel = document.getElementById('panel'), tb = document.getElementById('tb');
  const out = { toolbar: tb ? tb.innerText.replace(/\s+/g, ' ').trim() : null, panel: panel ? panel.innerText : null };
  if (F) {
    D.st.detPin = true; D.render(true); await wait(300); D.render(true);
    const g = document.getElementById('detg');
    out.drawer = g ? g.innerText : null;
    out.passports = D.passports().filter(p => p.snapshot_id === F.r.snapshot_id).map(p => ({ est: p.estimand, params: p.params, yes: p.yes_count, unk: p.unknown_count, no: p.no_event_count, N: p.N, pct: p.pct, pctHi: p.pctHi, phrase: p.phrase || null, v: p.violation || null }));
    out.family = { cond: F.cond || null, N: F.N, view: F.view, key: F.r.key, out: F.out || null };
  }
  return out;
});
const out = new Map(), meta = { build, scenes: {} }, report = [];
try {
  for (const sc of SCENES) {
    const [id, inst, , session, date, cut, what] = sc, D = await direct(sc), m = meta.scenes[id] = { inst, session, date, cut, what, server: D };
    serve = 'real'; await variant('A', sc);
    const a = await open(sc);
    if (id === 'pre') {
      // before the confirmation there is no family: the page must show none, and the server must publish none
      if (a.day.scene !== date || a.day.now !== cut || !(a.day.last_bar < cut) || a.inst !== inst || a.session !== session || !a.live || a.slice !== cut) fail(id + ': not the scene');
      if (a.family || D.snapshot) fail(id + ': a family exists before the confirmation');
    } else verify(sc, 'A', a, D);
    m.A = a; out.set(id + '.png', await shot());
    m.dump = await dump();
    if (m.dump.drawer) out.set(id + '-okna.png', await shot());
    report.push(`${id} ${inst} ${session} ${date} ${String(Math.floor(cut / 60)).padStart(2, '0')}:${String(cut % 60).padStart(2, '0')}: verified${D.snapshot ? ' · family ' + D.snapshot + ' (' + a.family.view + ')' : ' · no family'}`);
  }
} finally {
  cdp.close(); proc.kill(); await sleep(600);
  for (let i = 0; i < 20; i++) { try { fs.rmSync(prof, { recursive: true, force: true }); break; } catch (e) { await sleep(250); } }
}
fs.mkdirSync(IMG, { recursive: true });
for (const f of fs.readdirSync(IMG)) fs.rmSync(path.join(IMG, f));
for (const [f, b] of out) fs.writeFileSync(path.join(IMG, f), b);
fs.writeFileSync(path.join(HERE, 'scenes.json'), JSON.stringify(meta, null, 1));
console.log(`control: the server serves lab/dist/24 = the candidate passport's build (d24.js ${build.real.d24_js.slice(0, 12)})`);
console.log(report.join('\n'));
if (errors.length) console.log('page exceptions:', errors.slice(0, 5));
console.log('ALL VERIFIED: ' + out.size + ' shots');
