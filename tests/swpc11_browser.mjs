// DR-LAB-SWPC-1.1 · the M-checks that need the real screen 24, run in a throw-away headless Chrome.
//
//     node tests/swpc11_browser.mjs                 every M-check scenario (the server must run: start-dr-lab.cmd -NoBrowser)
//     node tests/swpc11_browser.mjs m14 m16         only these
//     node tests/swpc11_browser.mjs same            base and candidate render identically on a random sample of scenes
//     SWPC_SERVE=<git ref> …                        the same checks on the build committed at that ref (lab/dist/24)
//     node tests/swpc11_browser.mjs plan <dir> [seed]          the H01–H12 session: unfamiliar scenes, plan and key
//     node tests/swpc11_browser.mjs session-open <dir>         a visible throw-away Chrome window for the session
//     node tests/swpc11_browser.mjs show <dir> <pass> <step>   present one step there (variant, faults, settings)
//     node tests/swpc11_browser.mjs session-close <dir>
//
// Isolation (SWPC §8.1: fault and alert checks in an isolated instance, never on the working registry, server or the
// operator's settings): a new temporary browser profile per run (its own empty localStorage, deleted at the end); the
// page is the real built page (lab/dist/24), unchanged; faults are injected only between the page and the server — a
// wrapper of window.fetch installed before the page's script (delayed, failed or tampered responses), plus counting
// stand-ins for sound (AudioContext) and system notifications (Notification), so nothing is played or shown outside the
// profile. A synthetic «live» session replays a history day through the same wrapper. Nothing is written in the repo.
// The checks test what the screen shows (its passports, panel, inspector, toolbar, drawn geometry and canvas text), not
// how the code is arranged. Exit code 0 = every check passed; each line names its M-id of SWPC-1.1 §8.1.
import { execFileSync, spawn } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BASE = process.env.DR_LAB_URL || 'http://127.0.0.1:8767/24/';
const BASE_REF = process.env.SWPC_BASE_REF || '4526d30';     // the base of comparison of SWPC-1.1 (§8.3: main@4526d30)
const CAND_REF = process.env.SWPC_CAND_REF || null;          // null = the build in the working tree (lab/dist/24)

// a build of screen 24: { ref } = the files committed at a git ref, { dir } = a folder, null = what the server serves
const REF_CACHE = new Map();
function buildFiles(src) {
  const key = src.ref || src.dir;
  if (!REF_CACHE.has(key)) {
    const read = f => src.dir ? fs.readFileSync(path.join(src.dir, f)) : execFileSync('git', ['show', `${src.ref}:lab/dist/24/${f}`], { cwd: ROOT, maxBuffer: 64 << 20 });
    REF_CACHE.set(key, { 'index.html': read('index.html'), 'd24.js': read('d24.js') });
  }
  return REF_CACHE.get(key);
}
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const SERVE0 = process.env.SWPC_SERVE ? { ref: process.env.SWPC_SERVE } : process.env.SWPC_BASE ? { dir: process.env.SWPC_BASE } : null;
const CAND = () => CAND_REF ? { ref: CAND_REF } : null, BASEB = () => ({ ref: BASE_REF });
const CHROMES = [process.env.CHROME, 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', '/usr/bin/google-chrome', '/usr/bin/chromium'].filter(Boolean);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const DAY = '#date=2025-12-17&inst=NQ&session=RDR';          // an ordinary family (N 156)
const BRK = '#date=2025-12-10&inst=NQ&session=RDR&at=14:30';  // today's DR broken: the break family and the original

// the routes of SWPC-1.1 §9, read from the document itself (its only source): every estimand / fact form → its bindings;
// «{R,X}» is exactly two ids (§9), never a mask
function swpcRoutes() {
  const doc = fs.readFileSync(path.join(ROOT, 'spec', 'DR-LAB-SWPC-1.1.md'), 'utf8').replace(/\r\n/g, '\n');
  const sec = doc.split(/^## 9\. /m)[1].split(/^## 10\. /m)[0], routes = {};
  const span = s => s.split(',').flatMap(t => {
    const m = t.trim().match(/^B(\d\d)(?:[–-]B(\d\d))?$/);
    if (!m) return [];
    const a = +m[1], b = m[2] ? +m[2] : a;
    return Array.from({ length: b - a + 1 }, (_, i) => 'B' + String(a + i).padStart(2, '0'));
  });
  for (const m of sec.matchAll(/^\| `((?:EST|FF):[A-Z0-9-]+?)(-\{R,X\})?` \| ([^|]+) \|$/gm))
    for (const id of m[2] ? [m[1] + '-R', m[1] + '-X'] : [m[1]]) routes[id] = span(m[3]);
  return routes;
}

// ---------------------------------------------------------------- the browser (Chrome DevTools Protocol, no dependencies)
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

// a Chrome with a throw-away profile; headed = a visible window (the H-session), detached = it outlives this process
async function startChrome({ headed = false, prof = null, size = [1600, 900], detached = false } = {}) {
  const exe = CHROMES.find(p => fs.existsSync(p));
  if (!exe) throw new Error('no Chrome or Edge found (set CHROME)');
  prof = prof || fs.mkdtempSync(path.join(os.tmpdir(), 'swpc11-'));
  fs.mkdirSync(prof, { recursive: true });
  try { fs.rmSync(path.join(prof, 'DevToolsActivePort')); } catch (e) { /* none */ }
  const args = (headed ? ['--window-size=' + size.join(','), '--window-position=0,0'] : ['--headless=new', '--disable-gpu', '--hide-scrollbars'])
    .concat(['--force-device-scale-factor=1', '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, 'about:blank']);
  const proc = spawn(exe, args, { stdio: 'ignore', detached });
  if (detached) proc.unref();
  let port = null;
  for (let i = 0; i < 150 && !port; i++) {
    try { port = fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim() || null; } catch (e) { /* not yet */ }
    if (!port) await sleep(100);
  }
  if (!port) { proc.kill(); throw new Error('Chrome did not open its debugging port'); }
  return { proc, prof, port };
}

// attach to the page of a running Chrome; stubs = the configuration of the page's stand-ins (see STUBS), installed before
// the page's own script on every new document of this connection; serve = the build of screen 24 to give the page
async function attach(port, stubs = {}, serve = SERVE0) {
  const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const cdp = await connect(list.find(t => t.type === 'page').webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  const B = { cdp, errors: [], serve, stubs, script: null };
  cdp.on(m => { if (m.method === 'Runtime.exceptionThrown') B.errors.push((m.params.exceptionDetails.exception || {}).description || m.params.exceptionDetails.text); });
  B.setStubs = async cfg => {
    if (B.script) await cdp.send('Page.removeScriptToEvaluateOnNewDocument', { identifier: B.script });
    B.stubs = cfg;
    B.script = (await cdp.send('Page.addScriptToEvaluateOnNewDocument', { source: `(${STUBS})(${JSON.stringify(cfg)})` })).identifier;
  };
  await B.setStubs(stubs);
  // the page's own two files come from the chosen build (a git ref, a folder) or, by default, from the server
  await cdp.send('Fetch.enable', { patterns: [{ urlPattern: '*/24/d24.js*' }, { urlPattern: '*/24/' }, { urlPattern: '*/24/index.html*' }] });
  cdp.on(async m => {
    if (m.method !== 'Fetch.requestPaused') return;
    if (!B.serve) return cdp.send('Fetch.continueRequest', { requestId: m.params.requestId }).catch(() => {});
    const file = /d24\.js/.test(m.params.request.url) ? 'd24.js' : 'index.html';
    await cdp.send('Fetch.fulfillRequest', { requestId: m.params.requestId, responseCode: 200, body: buildFiles(B.serve)[file].toString('base64'),
      responseHeaders: [{ name: 'Content-Type', value: file === 'd24.js' ? 'application/javascript; charset=utf-8' : 'text/html; charset=utf-8' }, { name: 'Cache-Control', value: 'no-store' }] }).catch(() => {});
  });
  return B;
}

async function launch() {
  const c = await startChrome();
  const B = await attach(c.port);
  B.close = async () => {
    B.cdp.close(); c.proc.kill();
    for (let i = 0; i < 20; i++) { try { fs.rmSync(c.prof, { recursive: true, force: true }); break; } catch (e) { await sleep(250); } }
  };
  return B;
}

// installed before the page's own script on every document: the network seam and the counting stand-ins.
// cfg: { settings: {localStorage key: value} copied into this throw-away profile; faults: preset names (below);
//        live: {date, now, inst} a synthetic live session replaying a history day; realAudio: true lets the alert sound }
const STUBS = function (cfg) {
  cfg = cfg || {};
  const T = window.__swpcTest = { rules: [], log: [], chimes: 0, notes: 0, texts: new Map(), flag: {}, live: null };
  if (cfg.settings) try { for (const [k, v] of Object.entries(cfg.settings)) localStorage.setItem(k, v); } catch (e) { /* no storage */ }
  const realFetch = window.fetch.bind(window);
  // a rule: { match: substring, when?: url => bool, url?: url => url, delay?: ms, fail?: true, tamper?: (body, url, init) => body, once?: true }
  window.fetch = async (input, init) => {
    let url = String(input && input.url ? input.url : input);
    const rule = T.rules.find(r => url.includes(r.match) && (!r.when || r.when(url)) && !(r.once && r.used));
    if (!rule) return realFetch(input, init);
    rule.used = true;
    T.log.push([rule.name || rule.match, url]);
    if (rule.delay) await new Promise(r => setTimeout(r, rule.delay));
    if (rule.fail) throw new TypeError('swpc11: the network is down for this request');
    if (rule.url) url = rule.url(url);
    const resp = await realFetch(url, init);
    if (!rule.tamper) return resp;
    const body = rule.tamper(await resp.json(), url, init);
    return new Response(JSON.stringify(body), { status: resp.status, headers: { 'Content-Type': 'application/json' } });
  };
  // the faults of the H-session: the same as in the M-checks, worded exactly as the system words them (no test label)
  const PRESET = {
    zonesR: { name: 'zones R', match: '/api/d24/family', tamper: b => { if (b.zones && b.zones.R && b.zones.R.zones.length) b.zones.R.zones[0].n_zone += 1; return b; } },
    refZone: { name: 'reference', match: '/api/d24/verify', tamper: (body, url, init) => {
      const z = JSON.parse(init.body).passports.find(p => p.estimand === 'EST:B-ZONE-R');
      if (z && !T.flag.z) {
        T.flag.z = z;
        (body.mismatches = body.mismatches || []).push({ id: z.id, estimand: z.estimand, params: z.params, error: `page (${z.yes_count}, ${z.unknown_count}, ${z.no_event_count}) != reference (${z.yes_count - 1}, ${z.unknown_count}, ${z.no_event_count})` });
      }
      return body;
    } },
    nowDown: { name: 'NOW down', match: '/api/d24/now', fail: true }
  };
  for (const f of cfg.faults || []) if (PRESET[f]) T.rules.push(PRESET[f]);
  if (cfg.live) {
    const L = T.live = Object.assign({ bump: 0, high: null }, cfg.live);
    T.rules.push({ name: 'live day', match: '/api/d24/day', when: u => !u.includes('date='), url: u => u.replace('&refresh=1', '') + '&date=' + L.date,
      tamper: b => {
        if (b.status !== 'ok') return b;
        Object.assign(b, { source: 'live', fetched_at: new Date().toISOString(), now: L.now, feed: 'CME_MINI:' + (L.inst || 'NQ') + '1!' });
        b.bars = b.bars.filter(x => x[0] <= Math.floor(L.now / 5) * 5);
        const f = b.bars[b.bars.length - 1];
        if (L.bump) { f[4] = +(f[4] + L.bump).toFixed(2); f[2] = Math.max(f[2], f[4]); f[3] = Math.min(f[3], f[4]); }
        if (L.high != null) f[2] = Math.max(f[2], L.high);
        return b;
      } });
    T.rules.push({ name: 'live family', match: '/api/d24/family', when: u => !u.includes('date='), url: u => u + '&date=' + L.date });
    T.rules.push({ name: 'live now', match: '/api/d24/now', when: u => !u.includes('date='), url: u => u + '&date=' + L.date });
  }
  // sound is counted and silent, unless the session lets the alert be heard; system notifications are only counted
  class FakeAudio {
    constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }
    resume() { return Promise.resolve(); }
    createOscillator() { T.chimes++; return { type: 'sine', frequency: { value: 0 }, connect() {}, start() {}, stop() {} }; }
    createGain() { const g = { setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {} }; return { gain: g, connect() {} }; }
  }
  if (!cfg.realAudio) { window.AudioContext = FakeAudio; window.webkitAudioContext = FakeAudio; }
  const N = function () { T.notes++; };
  N.permission = 'granted'; N.requestPermission = () => Promise.resolve('granted');
  window.Notification = N;
  // every text drawn on the canvas (the census of M04)
  const fill = CanvasRenderingContext2D.prototype.fillText;
  CanvasRenderingContext2D.prototype.fillText = function (t, x, y, w) {
    const s = String(t);
    if (T.texts.size < 20000) T.texts.set(s, (T.texts.get(s) || 0) + 1);
    return fill.call(this, t, x, y, w);
  };
};

// helpers inside the page (window.__h), installed after every load
const HELPERS = function () {
  const D = window.__d24, T = window.__swpcTest, wait = ms => new Promise(r => setTimeout(r, ms)), panel = document.getElementById('panel');
  const fam = c => ['confirmed', 'broken', 'done'].includes(c.s.status);
  const H = window.__h = {
    D, T, wait, panel,
    // render until the family of the chosen session is on screen (or will not come), «Сейчас» answered, passports checked
    async settle(maxMs = 20000) {
      const t0 = Date.now();
      for (;;) {
        D.render(true);
        const c = D.cur(), idle = D.A.pending.size === 0 && D.A.nowPending.size === 0 && !D.A.busy;
        if (idle && (c.F || !fam(c)) && Date.now() - t0 > 250) break;
        if (idle && !c.F && fam(c) && Date.now() - t0 > 1500) break;
        if (Date.now() - t0 > maxMs) break;
        await wait(100);
      }
      for (let i = 0; i < 25 && D.contract().unchecked; i++) { await D.verify(); await wait(80); }
      D.render(true);
      return H.state();
    },
    state() { const c = D.cur(), F = c.F; return { status: c.s.status, F: !!F, view: F && F.view, snapshot: F && F.r.snapshot_id, N: F && F.N, slice: c.obs, live: c.live }; },
    pps(F) { return D.passports().filter(p => !F || p.snapshot_id === F.r.snapshot_id).map(p => ({ id: p.id, key: p.key, est: p.estimand, params: p.params, yes: p.yes_count, unk: p.unknown_count, no: p.no_event_count, N: p.N, cf: p.claim_form, sid: p.snapshot_id, fid: p.family_id, req: !!p.req, v: p.violation || null })); },
    base(F) { return JSON.stringify([F.N, F.r.snapshot_id, ...['R', 'X'].map(ev => [...F.ev[ev].cells.values()].map(q => [q.k, q.b, q.list.length].join(',')).sort().join(';')),
      ...['R', 'X'].map(ev => F.zones[ev] ? F.zones[ev].zones.map(z => z.zone_id + ':' + z.n_zone).join(',') : '-'), JSON.stringify(F.out || null)]); },
    zoneRows() { return [...panel.querySelectorAll('.p21-link[class*="zst-"]')].map(e => e.innerText.replace(/\s+/g, ' ').trim()); },
    heads() { return [...panel.querySelectorAll('.p21-h')].map(e => (e.firstChild && e.firstChild.textContent || e.innerText).split(/\s·\s|\n/)[0].trim().replace(/\d\d:\d\d/g, 'ЧЧ:ММ')); },
    notice() { const n = panel.querySelector('.p24-sc'); return n ? n.innerText : null; },
    nowBlock() { const n = panel.querySelector('.p24-nowblk'); return n ? n.innerText : null; },
    toggle() { const t = document.getElementById('panel21toggle'); return { alert: t.classList.contains('sc-alert'), title: t.title, aria: t.getAttribute('aria-label'), badge: getComputedStyle(t, '::after').content, hidden: document.getElementById('dr21-root').classList.contains('panel21closed') }; },
    // the toolbar: the controls left of its spacer keep their places; right of it they keep their widths (the clock's
    // text decides where the right group starts, by design)
    toolbarGeo() { const out = []; let right = false; for (const e of document.querySelectorAll('#tb > *')) { if (!e.offsetParent) continue; if (e.classList.contains('sp')) { right = true; continue; } const r = e.getBoundingClientRect(), id = e.id || e.className; if (/^(clock|apibar)$/.test(id)) continue; out.push(id + (right ? ' w' + Math.round(r.width) : ' @' + Math.round(r.left) + ' w' + Math.round(r.width))); } return out; },
    hide(on) { const root = document.getElementById('dr21-root'); if (root.classList.contains('panel21closed') !== on) document.getElementById('panel21toggle').click(); D.render(true); },
    async refresh() { document.getElementById('refresh21').click(); await wait(200); return H.settle(); },
    dataPP() { const byId = new Map(D.passports().map(p => [p.id, p])); return [...panel.querySelectorAll('[data-pp]')].map(el => { const p = byId.get(+el.dataset.pp); return { sid: p && p.snapshot_id, text: el.innerText.split('\n')[0], b: (el.querySelector('b') || {}).innerText || '' }; }); }
  };
  return true;
};

async function evaluate(cdp, fn, ...args) {
  const r = await cdp.send('Runtime.evaluate', { expression: `(${fn})(...${JSON.stringify(args)})`, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception || {}).description || r.exceptionDetails.text);
  return r.result.value;
}

async function open(B, hash, size = [1600, 900]) {
  await B.cdp.send('Emulation.setDeviceMetricsOverride', { width: size[0], height: size[1], deviceScaleFactor: 1, mobile: false });
  await B.cdp.send('Page.navigate', { url: 'about:blank' });
  await sleep(80);
  await B.cdp.send('Page.navigate', { url: BASE + hash });
  for (let i = 0; i < 100; i++) {
    if (await evaluate(B.cdp, () => !!(window.__d24 && document.readyState === 'complete')).catch(() => false)) break;
    await sleep(100);
  }
  await evaluate(B.cdp, HELPERS);
  return evaluate(B.cdp, () => window.__h.settle());
}

// a synthetic live session (inside the page): today's requests without a date are answered with a history day, the day
// cut at `now` (its forming M5 included) and marked live; `bump` / `high` move the forming candle as a tick would
const LIVE = async (date, now) => {
  const H = window.__h, { D, T } = H;
  T.live = { date, now, bump: 0, high: null };
  T.rules = T.rules.filter(r => !r.live);
  T.rules.push({ live: true, name: 'live day', match: '/api/d24/day', when: u => !u.includes('date='), url: u => u.replace('&refresh=1', '') + '&date=' + date,
    tamper: b => {
      if (b.status !== 'ok') return b;
      const L = T.live;
      Object.assign(b, { source: 'live', fetched_at: new Date().toISOString(), now: L.now, feed: 'CME_MINI:NQ1!' });
      b.bars = b.bars.filter(x => x[0] <= Math.floor(L.now / 5) * 5);
      const f = b.bars[b.bars.length - 1];
      if (L.bump) { f[4] = +(f[4] + L.bump).toFixed(2); f[2] = Math.max(f[2], f[4]); f[3] = Math.min(f[3], f[4]); }
      if (L.high != null) f[2] = Math.max(f[2], L.high);
      return b;
    } });
  T.rules.push({ live: true, name: 'live family', match: '/api/d24/family', when: u => !u.includes('date='), url: u => u + '&date=' + date });
  T.rules.push({ live: true, name: 'live now', match: '/api/d24/now', when: u => !u.includes('date='), url: u => u + '&date=' + date });
  D.A.auto = false; clearTimeout(D.A.timer);
  D.openLive();
  return H.settle();
};

// ---------------------------------------------------------------- report
const results = [];
function check(id, cond, msg, detail) {
  results.push({ id, ok: !!cond, msg });
  console.log((cond ? '  ok   ' : '  FAIL ') + id + ' ' + msg + (cond || detail === undefined ? '' : ' :: ' + JSON.stringify(detail).slice(0, 700)));
}

// ---------------------------------------------------------------- the checks of SWPC-1.1 §8.1
const S = {
  // M01: every number made by the screen in a sweep of its states is a passport of a real estimand with its claim form,
  // its family context, and a binding of §9 found by its exact id (no similar name gets a presentation)
  async m01(B) {
    const routes = swpcRoutes();
    check('M01', Object.keys(routes).filter(k => k.startsWith('EST:')).length === 53 && Object.keys(routes).filter(k => k.startsWith('FF:')).length === 8,
      '§9 of the document routes 53 estimands and 8 fact forms (read from the document)', Object.keys(routes).length);
    await open(B, DAY + '&at=11:40');
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, F0 = D.cur().F, z = (D.zonesOf(F0, 'R') || { zones: [] }).zones;
      const touch = async (h, extra) => { Object.assign(D.st, { hover: h }, extra || {}); D.render(true); await H.wait(30); };
      await touch({ k: 'zone', ev: 'R', i: 0 });
      await touch({ k: 'pcell', ev: 'X', k0: 3, k1: 4, src: 'proj' });
      await touch({ k: 'tcell', b0: 2, b1: 3, src: 'strip' });
      await touch({ k: 'pt', ev: 'R', i: 3 });
      await touch({ k: 'unk', src: 'strip' });
      await touch({ k: 'evrow', ev: 'X' });
      await touch({ k: 'out', cat: 'held' });
      await touch(null, { area: { k0: 2, k1: 5, b0: 2, b1: 5, ev: 'R' } });
      await touch({ k: 'area', part: 'band' });
      D.st.area = null; D.st.hover = null; D.st.pinLvl = 'u2'; D.render(true);
      D.st.detPin = true; D.render(true); await H.wait(50);
      D.st.hover = { k: 'zone', ev: 'X', i: 0 }; D.render(true);
      D.st.mode = 'path'; D.st.hover = null; D.render(true);
      const film = D.filmOf(D.cur().F), j = Math.floor(film.length / 2), k = [...film[j].cells.keys()][0];
      await touch({ k: 'fcell', j, kk: k, src: 'proj' });
      await touch({ k: 'col', j });
      D.st.mode = 'bounds'; D.st.hover = null; D.st.pin = null; D.st.detPin = false; D.render(true);
      await H.settle();
      return { pps: H.pps(), snap: D.cur().F.r.snapshot_id, zones: z.length };
    });
    const bad = r.pps.filter(p => !routes[p.est] || !p.cf || !p.sid || !p.fid || !p.req || p.N <= 0);
    check('M01', r.pps.length > 80 && !bad.length, `every passport of a sweep of states (${r.pps.length}) has its estimand routed in §9 by its exact id, a claim form and its family context`, bad.slice(0, 4));
    const ests = [...new Set(r.pps.map(p => p.est))].sort();
    check('M01', ests.length >= 20, `the sweep reached ${ests.length} distinct estimands (bindings exercised: ${[...new Set(ests.flatMap(e => routes[e] || []))].sort().join(' ')})`, ests);
  },

  // M02: no frame shows the numbers of one family under the name or scale of another, and a late answer of another
  // scene never replaces the scene on screen (family, day)
  async m02(B) {
    await open(B, BRK);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T, panel } = H, frames = [];
      const frame = () => {
        D.render(true);
        const c = D.cur(), F = c.F, head = (panel.querySelector('.p21-h span') || {}).innerText || '', pp = H.dataPP();
        const names = [...document.querySelectorAll('#ev .evc span')].map(e => e.innerText.trim());
        frames.push({ F: !!F, brk: F && F.brk, head: head.split(' · ')[0], nums: pp.filter(x => /\d/.test(x.b)).length, foreign: F ? pp.filter(x => x.sid !== F.r.snapshot_id).length : pp.filter(x => /\d/.test(x.b)).length,
          names: names.join('|'), fnames: F ? ['R', 'X'].map(e => F.names[e].toLowerCase()).join('|') : null });
      };
      frame();
      const brkSnap = D.cur().F && D.cur().F.r.snapshot_id;
      T.rules.push({ name: 'slow original family', match: '/api/d24/family', when: u => /view=conf/.test(u), delay: 1500, once: true });
      panel.querySelector('[data-view="conf"]').click();
      for (let i = 0; i < 22; i++) { frame(); await H.wait(100); }
      await H.settle(); frame();
      const confSnap = D.cur().F && D.cur().F.r.snapshot_id;
      panel.querySelector('[data-view="auto"]').click();
      await H.settle(); frame();
      return { frames, brkSnap, confSnap, back: D.cur().F && D.cur().F.r.snapshot_id };
    });
    const bad = r.frames.filter(f => f.foreign || (f.F && (f.brk !== /слома/.test(f.head) || f.names !== f.fnames)));
    check('M02', r.brkSnap && r.confSnap && r.brkSnap !== r.confSnap && r.back === r.brkSnap && !bad.length,
      `break family ↔ original over ${r.frames.length} frames (the original delayed 1,5 s): every number shown belongs to the family named in the header and the toolbar; none while loading`, bad.slice(0, 3));
    check('M02', r.frames.some(f => !f.F && f.nums === 0), 'while the original family loads, the panel shows no number of the break family under its name');
    await open(B, DAY);
    const s = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.rules.push({ name: 'late family A', match: '/api/d24/family', when: u => u.includes('date=2025-12-16'), delay: 2000, once: true });
      T.rules.push({ name: 'late day A', match: '/api/d24/day', when: u => u.includes('date=2025-12-16'), delay: 2600, once: true });
      D.openHist('2025-12-16'); await H.wait(150);
      D.openHist('2025-12-18'); await H.settle();
      const b = { snap: D.cur().F && D.cur().F.r.snapshot_id, date: D.A.day && D.A.day.date, label: document.getElementById('date').innerText };
      await H.wait(3000); await H.settle();
      const a = { snap: D.cur().F && D.cur().F.r.snapshot_id, date: D.A.day && D.A.day.date, label: document.getElementById('date').innerText, asked: D.A.date, foreign: H.dataPP().filter(x => x.sid !== b.snap).length };
      return { b, a };
    });
    check('M02', s.b.snap && s.a.snap === s.b.snap && s.a.date === '2025-12-18' && s.a.asked === '2025-12-18' && /18 дек/.test(s.a.label) && !s.a.foreign,
      'a late answer (day and family) of the previously opened day is dropped: the day asked last stays, with its own family', s);
  },

  // M03: a live tick and the per-second timer do not touch the closed-M5 statistics; replay never uses the shown future
  async m03(B) {
    await open(B, DAY + '&at=11:40');
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, panel } = H, c0 = D.cur(), F = c0.F, sl = c0.obs;
      // the statistics on screen: the zone rows, «Сейчас», today's statuses and the value of every passport already made
      // (the frame follows the candles shown, so new frame-dependent labels may appear; their values are not compared)
      const sig = () => { const c = D.cur(); return { text: JSON.stringify([H.zoneRows(), H.nowBlock(), D.zoneStatus(c.F, c, 'R'), D.zoneStatus(c.F, c, 'X')]), pp: new Map(H.pps(c.F).map(p => [p.key, p.yes + '/' + p.unk + '/' + p.no])) }; };
      const a = sig();
      // every candle after the slice is replaced (the day's cached bars; the session cache dropped so it is recomputed)
      for (const b of D.A.D.bars) if (b.t + 5 > sl) { b.h *= 1.03; b.l *= 0.97; b.c *= 1.01; }
      D.A.D.S = {}; D.render(true); await H.wait(50); D.render(true);
      const b = sig(), changed = [...a.pp].filter(([k, v]) => b.pp.get(k) !== v).map(([k]) => k);
      return { same: a.text === b.text && !changed.length, changed: changed.slice(0, 3), slice: sl, F: !!F, text: panel.innerText.length };
    });
    check('M03', r.F && r.same, 'replay: replacing every candle after the slice changes no share, status, passport or «Сейчас» (the future is shown, never used)', r);
    await open(B, DAY);
    const l = await evaluate(B.cdp, LIVE, '2025-12-17', 702.5);      // 11:42:30 ET: the M5 11:40-11:45 is forming
    const t = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      const sig = () => { const c = D.cur(); return JSON.stringify([H.zoneRows(), (H.nowBlock() || '').replace(/\s+/g, ' '), D.zoneStatus(c.F, c, 'R'), D.zoneStatus(c.F, c, 'X'), H.pps(c.F).map(p => p.key + '=' + p.yes)]); };
      const p0 = D.cur().s.priceNow, a = sig(), slice0 = D.cur().obs;
      await H.wait(2300);                       // the per-second timer redraws the live screen twice
      const a2 = sig();
      T.live.bump = 7.5;                        // a tick inside the same M5: only the forming candle moves
      const st = await H.refresh();
      const p1 = D.cur().s.priceNow, b = sig();
      return { live: st.live, F: st.F, slice0, slice1: D.cur().obs, moved: p1 !== p0, p0, p1, timer: a === a2, tick: a === b };
    });
    check('M03', l.F && l.live && t.F && t.timer, 'live: the per-second timer leaves every statistic as it was', t);
    check('M03', t.moved && t.slice0 === t.slice1 && t.tick, 'live: a tick inside the forming M5 moves the price, not the cut, a share, a status, a passport or «Сейчас»', t);
  },

  // M04: no frequency produces a sound, a notification, a toast, an animation, a forecast / decision word or an arrow:
  // sweep the states, count the stand-ins, compare idle canvas frames, read every drawn and written text
  async m04(B) {
    const hashes = [DAY + '&at=11:00', DAY + '&at=13:30', BRK, '#date=2025-12-19&inst=NQ&session=ODR', '#date=2025-12-09&inst=NQ&session=RDR&at=11:00'];
    const texts = new Map(), dom = [];
    let snd = 0, notes = 0, toast = false, still = true;
    for (const h of hashes) {
      await open(B, h);
      const r = await evaluate(B.cdp, async () => {
        const H = window.__h, { D, T, panel } = H, F = D.cur().F;
        if (F) for (const ev of ['R', 'X']) for (let i = 0; i < ((D.zonesOf(F, ev) || { zones: [] }).zones.length); i++) { D.st.hover = { k: 'zone', ev, i }; D.render(true); }
        D.st.hover = { k: 'now', ev: 'R' }; D.render(true); D.st.hover = { k: 'now', ev: 'X' }; D.render(true);
        D.st.hover = null; D.st.detPin = true; D.render(true); await H.wait(60);
        D.st.mode = 'path'; D.render(true); D.st.mode = 'bounds'; D.st.detPin = false; D.render(true);
        const cv = document.getElementById('cv'); D.render(true); await H.wait(200);
        const a = cv.toDataURL(); await H.wait(1600); const b = cv.toDataURL();
        const el = document.getElementById('alToast');
        return { snd: T.chimes, notes: T.notes, toast: !!(el && !el.hidden), still: a === b, texts: [...T.texts.keys()],
          dom: [panel.innerText, document.getElementById('insp').innerText, document.getElementById('det').innerText, document.getElementById('tb').innerText].join('\n') };
      });
      snd += r.snd; notes += r.notes; toast = toast || r.toast; still = still && r.still;
      for (const t of r.texts) texts.set(t, (texts.get(t) || 0) + 1);
      dom.push(r.dom);
    }
    check('M04', snd === 0 && notes === 0 && !toast, 'across 5 days and every zone / NOW hover no sound, no system notification and no toast happened', { snd, notes, toast });
    check('M04', still, 'an idle history screen does not change between frames 1,6 s apart (no pulse, no animation)');
    const arrows = [...texts.keys()].filter(t => /[↑↓▲▼←→⬆⬇]/.test(t));
    const known = t => /^[↑↓] \d\d:\d\d$/.test(t) || /^Слом DR [↑↓] \d\d:\d\d$/.test(t) || /^[↑↓] [+−]\d+,\d · [\d\s\u00a0\u202f]+(,\d+)?$/.test(t) || /^[▲▼]$/.test(t) || /^[▲▼] (\d+(,\d+)?%|—)$/.test(t);
    check('M04', arrows.every(known), `every arrow drawn comes from an observation or the frame (confirmation / break pill, the next STD beyond the frame, a column's out-of-frame mark and share): ${arrows.length} kinds`, arrows.filter(t => !known(t)));
    const all = [...texts.keys(), ...dom].join('\n');
    const future = all.match(/углуб[ия]тся|пойд[её]т|(?<![а-яё])будет|если да/gi) || [];
    const decide = all.match(/(?<!не )(?<![а-яё])(вход[а-яё]*|стоп|тейк|цел[ьи]|сигнал[а-яё]*|прогноз[а-яё]*|вероятност[а-яё]*|шанс[а-яё]*|покупа[а-яё]*|прода[вж][а-яё]*)(?![а-яё])/gi) || [];
    check('M04', !future.length && !decide.length, 'no forecast grammar about today and no trade / probability word anywhere on the screen (negations such as «не шанс», «не сделка» allowed)', { future, decide: decide.slice(0, 8) });
  },

  // M05: across cuts the BASE stays: the exact events, the masks, N and every share; a zoom of the frame changes none
  async m05(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, F = D.cur().F, sigs = [], pp = [];
      // the value of every BASE passport already made (a new frame may add frame-dependent labels; values are compared)
      const keep = () => new Map(H.pps(D.cur().F).filter(p => /^EST:B-(ZONE|RX|DR|ORDER)/.test(p.est)).map(p => [p.key, p.yes + '/' + p.unk + '/' + p.no]));
      const same = (a, b) => [...a].every(([k, v]) => !b.has(k) || b.get(k) === v);
      for (const dt of [5, 30, 90, 180, 330]) {
        const t = F.act0 + dt; if (t > F.end) break;
        D.st.rp = t; await H.settle(); const c = D.cur();
        sigs.push(H.base(c.F)); pp.push(keep());
      }
      const before = keep(), rows0 = H.zoneRows().map(x => x.replace(/ (держится|возможна|невозможна|неизвестно: нет свечи M5|—) /, ' ')).join('|'), p0 = D.V.p0;
      D.st.auto = false; D.st.p0 = D.V.p0 + (D.V.p1 - D.V.p0) * 0.3; D.st.p1 = D.V.p1 - (D.V.p1 - D.V.p0) * 0.3; await H.settle();
      const zoomed = keep(), rows1 = H.zoneRows().map(x => x.replace(/ (держится|возможна|невозможна|неизвестно: нет свечи M5|—) /, ' ')).join('|'), p1 = D.V.p0;
      return { n: sigs.length, base: new Set(sigs).size === 1, cuts: pp.every(m => same(pp[0], m) && same(m, pp[0])), zoomedSame: same(before, zoomed) && rows0 === rows1, kept: [...before.keys()].filter(k => zoomed.has(k)).length, framed: p0 !== p1 };
    });
    check('M05', r.n >= 4 && r.base && r.cuts, `at ${r.n} cuts the snapshot, the R / X tables, the zone masks with their n, N, the DR outcome and every BASE passport are the same`, r);
    check('M05', r.zoomedSame && r.framed && r.kept > 20, `a manual zoom of the frame changes no BASE passport (${r.kept} compared) and no zone row`, r);
  },

  // M06: R and X keep separate hundreds; the full bar of a band keeps its length when today makes it impossible
  async m06(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, F = D.cur().F, len = () => new Map((D.V.projBars || []).map(q => [q.ev + q.k, Math.round((q.x1 - q.x0) * 100) / 100]));
      D.st.rp = F.act0 + 5; D.st.auto = false; await H.settle();
      D.st.p0 = D.V.p0; D.st.p1 = D.V.p1;               // the same frame at both cuts
      const a = len();
      D.st.rp = F.end; await H.settle();
      const c = D.cur(), Rch = D.reachOf(c.F, c), b = len();
      const dead = [...b.keys()].filter(k => !Rch.okK(k[0], +k.slice(1)));
      const diff = [...a.keys()].filter(k => b.has(k) && a.get(k) !== b.get(k));
      D.st.hover = { k: 'pcell', ev: 'R', k0: -3, k1: -2, src: 'proj' }; D.render(true);
      const insp = document.getElementById('insp').innerText;
      const parts = [D.lbl('EST:B-RX-DIFF', 'k_parts'), D.lbl('EST:B-RX-DIFF', 'k_sum')];
      return { bars: a.size, dead: dead.length, deadSame: dead.filter(k => a.has(k)).every(k => a.get(k) === b.get(k)), diff, twoRows: /R ·/.test(insp) && /X ·/.test(insp), noSum: parts.some(p => insp.includes(p)) };
    });
    check('M06', r.bars > 10 && r.dead > 0 && r.deadSame && !r.diff.length, `the same frame at the first cut and at the block end: ${r.bars} bars keep their length, ${r.dead} of them impossible today`, r);
    check('M06', r.twoRows && r.noSum, 'a band\'s inspector shows R and X as two shares of N with the note that they do not add up', r);
  },

  // M07: two axes: a zone possible today with no history ahead is quiet, not impossible; a zone holding today's extreme
  // after its window passed still holds; the band of today's extreme stays reachable
  async m07(B) {
    const found = { quiet: null, holdsPast: null, edge: 0, bad: [] };
    for (const h of [DAY, '#date=2025-12-09&inst=NQ&session=RDR', '#date=2025-12-18&inst=NQ&session=RDR', '#date=2025-12-19&inst=NQ&session=ODR']) {
      await open(B, h);
      const r = await evaluate(B.cdp, async () => {
        const H = window.__h, { D } = H, F = D.cur().F, out = { quiet: null, holdsPast: null, edge: 0, bad: [] };
        if (!F) return out;
        for (let t = F.act0 + 5; t <= F.end; t += 10) {
          D.st.rp = t; D.render(true);
          const c = D.cur();
          if (!c.F) continue;                        // after today's break the break family is still on its way
          const Rch = D.reachOf(c.F, c);
          for (const ev of ['R', 'X']) {
            const Zm = D.zonesOf(c.F, ev); if (!Zm) continue;
            const S = D.zoneStatus(c.F, c, ev), K = D.zoneClock(c.F, c, ev), L = D.zoneLook(c.F, c, ev);
            Zm.zones.forEach((z, i) => {
              if (S[i] === 'POSSIBLE' && K[i] === 'FUTURE_EMPTY') { if (L[i] !== 'QUIET') out.bad.push('look ' + L[i]); else if (!out.quiet) out.quiet = { t, ev, label: z.label }; }
              if (S[i] === 'HOLDS' && c.F.f + 15 * (Math.max(...z.cell_mask.map(q => q[1])) + 1) <= t && !out.holdsPast) out.holdsPast = { t, ev, label: z.label };
              if (L[i] === 'IMPOSSIBLE' && S[i] !== 'IMPOSSIBLE') out.bad.push('drawn impossible while ' + S[i]);
            });
            const q = Rch.cur && Rch.cur[ev];
            if (Rch.known && q) { if (!Rch.okK(ev, q.k) || !Rch.okCell(ev, q.k, q.b)) out.bad.push('today band not reachable ' + ev + ' ' + t); else out.edge++; }
          }
        }
        return out;
      });
      found.quiet = found.quiet || r.quiet; found.holdsPast = found.holdsPast || r.holdsPast; found.edge += r.edge; found.bad.push(...r.bad);
    }
    check('M07', found.quiet && !found.bad.length, 'POSSIBLE with no family event ahead (FUTURE_EMPTY) is drawn quiet, never impossible', found);
    check('M07', found.holdsPast, 'a zone holding today\'s extreme after its window passed is still HOLDS', found.holdsPast);
    check('M07', found.edge > 50 && !found.bad.length, `the band and cell of today's extreme are reachable at every cut (${found.edge} cases)`, found.bad.slice(0, 3));
  },

  // M08: UNKNOWN, NO_PERIOD, a known zero and no family stay distinguishable; «Сейчас» unavailable is not «no data»
  async m08(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, panel } = H, F = D.cur().F, txt = panel.innerText;
      const und = ['R', 'X'].map(ev => (F.ev[ev].unknown + F.ev[ev].none > 0) === txt.includes(D.lbl('EST:B-RX-UNDETERMINED-' + ev, 'row', { ev })));
      const out = (panel.querySelector('.p24-out') || {}).innerText || '';
      const held = out.includes(D.lbl('EST:B-DR', 'held')) && out.includes(D.lbl('EST:B-DR', 'broken'));
      const zero = ['unknown', 'none'].every(k => (F.out[k] > 0) === out.includes(D.lbl('EST:B-DR', k)));
      D.st.detPin = true; D.render(true); await H.wait(50);
      const det = document.getElementById('det').innerText, np = F.M.filter(m => m.order === 'no_period').length;
      const order = (np > 0) === det.includes(D.lbl('EST:B-ORDER', 'no_period'));
      D.st.detPin = false; D.render(true);
      return { und, held, zero, order, np };
    });
    check('M08', r.und.every(Boolean) && r.held && r.zero && r.order, 'the undetermined row of R / X, the DR categories (held and broken always, unknown / no period only when present) and the order\'s «нет периода» follow their own counts', r);
    const pre = await open(B, '#date=2025-12-17&inst=NQ&session=RDR&at=10:20');
    const p = await evaluate(B.cdp, () => ({ text: window.__h.panel.innerText, status: window.__d24.cur().s.status }));
    check('M08', !pre.F && /семьи ещё нет/.test(p.text) && !/%/.test(p.text.replace(/Сейчас[\s\S]*/, '')), 'before the confirmation the panel says there is no family yet and shows no percentage', p);
    await open(B, DAY + '&at=11:40');
    const u = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.rules.push({ name: 'NOW down', match: '/api/d24/now', fail: true });
      D.st.rp = D.cur().obs + 5; await H.settle();
      return { block: H.nowBlock(), base: H.zoneRows().length };
    });
    check('M08', /Локальный сервер не ответил/.test(u.block || '') && !/нет данных/.test(u.block || '') && !/\d%/.test(u.block || '') && u.base > 0,
      '«Сейчас» that did not arrive says the server did not answer (not «нет данных», no number); the base map stays', u);
    await open(B, '#date=2025-11-05&inst=ES&session=ADR&at=23:20');
    const s = await evaluate(B.cdp, () => ({ block: window.__h.nowBlock(), rows: window.__h.zoneRows().length, N: window.__d24.cur().F && window.__d24.cur().F.N }));
    check('M08', s.N && s.N < 20 && s.block && !/Локальный сервер/.test(s.block) && s.rows >= 0, `a family of ${s.N}: «Сейчас» names its own support limit, distinct from an unavailable server; the base stays`, s);
  },

  // M09: at every cut «Сейчас» speaks the history (K33), names its mode and support, keeps its parts apart; the NOW of an
  // earlier cut never stands under a new one; BASE is untouched by it
  async m09(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H, F = D.cur().F, rows = [];
      const clk = m => String(Math.floor(((m % 1440) + 1440) % 1440 / 60)).padStart(2, '0') + ':' + String(((m % 60) + 60) % 60).padStart(2, '0');
      const base = H.base(F);
      for (const dt of [10, 40, 90, 150, 240]) {
        const t = F.act0 + dt; if (t >= F.end) break;
        D.st.rp = t; await H.settle();
        const b = H.nowBlock() || '';
        rows.push({ t: clk(t), cut: b.includes(clk(t)), mode: /по времени|похожий путь/.test(b), support: /опора|из \d+/.test(b), k33: !/углуб[ия]тся|пойд[её]т|будет|если да/.test(b), hist: b.includes('В истории'), base: H.base(D.cur().F) === base });
      }
      // the next cut's NOW delayed: its place says it is being counted, with no number, never the previous cut's
      const t1 = D.cur().obs + 5;
      T.rules.push({ name: 'slow NOW', match: '/api/d24/now', when: u => u.includes('at=' + t1), delay: 1500, once: true });
      D.st.rp = t1; D.render(true); await H.wait(300); D.render(true);
      const waiting = H.nowBlock() || '';
      await H.settle();
      const after = H.nowBlock() || '';
      return { rows, waiting, after, t1: clk(t1) };
    });
    check('M09', r.rows.length >= 4 && r.rows.every(x => x.cut && x.mode && x.support && x.k33 && x.hist && x.base), `at ${r.rows.length} cuts «Сейчас» carries its own cut, mode, support and historical words; BASE unchanged`, r.rows);
    check('M09', /считаю/.test(r.waiting) && !/\d%/.test(r.waiting) && r.after.includes(r.t1) && /\d%/.test(r.after), 'while the new cut\'s «Сейчас» is on its way the block says «считаю…» without a number, then shows the new cut', { waiting: r.waiting, after: r.after.slice(0, 80) });
  },

  // M10: switching layers off or framing the price leaves every count; the residual and the events out of the frame are
  // kept and recoverable
  async m10(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, F = D.cur().F;
      const keep = () => H.pps(D.cur().F).filter(p => /^EST:B-(ZONE|RX-UNDETERMINED|DR)/.test(p.est)).map(p => p.key + '=' + p.yes).sort().join(';');
      const a = keep(), rowsA = H.zoneRows().join('|');
      Object.assign(D.st.L, { pts: false, zones: false, proj: false, strip: false }); await H.settle();
      const b = keep(), rowsB = H.zoneRows().join('|');
      Object.assign(D.st.L, { pts: true, zones: true, proj: true, strip: true });
      const seen = new Set(D.passports().map(p => p.id));
      D.st.auto = false; const span = D.V.p1 - D.V.p0; D.st.p0 = D.V.p0 + span * 0.35; D.st.p1 = D.V.p1 - span * 0.35; await H.settle();
      // what the column names beyond this frame: the new out-of-frame passports made for it (their sides and counts)
      const sums = ['R', 'X'].map(ev => {
        const inFrame = (D.V.projBars || []).filter(q => q.ev === ev).reduce((t, q) => t + (F.ev[ev].P.get(q.k) || 0), 0);
        const named = D.passports().filter(p => !seen.has(p.id) && p.estimand === 'EST:B-RX-OUTFRAME-' + ev);
        const side = s => named.filter(p => p.params.side === s).reduce((t, p) => t + p.yes_count, 0);
        return { ev, inFrame, above: side('ABOVE'), below: side('BELOW'), known: F.ev[ev].known, named: true };
      });
      return { layers: a === b && rowsA === rowsB && rowsA.length > 0, sums };
    });
    check('M10', r.layers, 'with points, constellations, the price column and the time band switched off every count and every zone row stays', r);
    check('M10', r.sums.every(s => s.above + s.below > 0 && s.inFrame + s.above + s.below === s.known && s.named),
      'framed tight: the bars in the frame plus the shares named above and below it (▲ / ▼, each its own passport) are every known event; nothing dropped', r.sums);
  },

  // M11: «Путь семьи»: an M5 column, the range field and the final events stay apart; a band's profile uses M5 closes
  async m11(B) {
    await open(B, DAY + '&at=11:40');
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, before = new Set(D.passports().map(p => p.id));
      D.st.mode = 'path'; D.render(true);
      const F = D.cur().F, film = D.filmOf(F), j = film.findIndex(cd => cd.T > D.cur().obs), k = [...film[Math.max(0, j)].cells.keys()][0];
      D.st.hover = { k: 'fcell', j: Math.max(0, j), kk: k, src: 'proj' }; D.render(true);
      const lk = D.V.lk, row = lk && lk.row ? lk.row.every(q => q.n === (film[q.j].cells.get(k) || []).length) : false;
      D.st.hover = { k: 'fcell', j: Math.max(0, j), kk: k }; D.render(true);
      const insp = document.getElementById('insp').innerText;
      await H.settle();
      const made = D.passports().filter(p => !before.has(p.id)).map(p => p.estimand);
      D.st.mode = 'bounds'; D.st.hover = null; D.render(true);
      return { row, m5: lk && lk.t1 - lk.t0 === 5 && lk.ev === 'path', made: [...new Set(made)], insp: insp.length > 0 };
    });
    check('M11', r.row && r.m5, 'a band hovered in «Путь семьи» draws its profile from the M5 closes of the family (each M5 its own n), pointing at an M5', r);
    check('M11', r.made.length && r.made.every(e => /^EST:B-(CLOSE|CLOSE-MISSING|CLOSE-PREACT|RANGE)$/.test(e)), 'the numbers made in «Путь семьи» are closes, missing closes and the range field — no R / X share under this field', r.made);
  },

  // M12: hover / pin: a zone → its whole window; a price band → its peak 15 minutes; a band of «Путь семьи» → its M5
  // profile; «Сейчас» → the remaining movement from today's extreme; leaving restores the pinned subject or the snapshot
  async m12(B) {
    await open(B, DAY + '&at=11:40');
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, F = D.cur().F, insp = () => document.getElementById('insp').innerText;
      const z = D.zonesOf(F, 'R').zones[0], bs = z.cell_mask.map(q => q[1]);
      D.st.hover = { k: 'zone', ev: 'R', i: 0 }; D.render(true);
      const zone = D.V.lk && D.V.lk.src === 'zone' && D.V.win.t0 === F.f + 15 * Math.min(...bs) && D.V.win.t1 === F.f + 15 * (Math.max(...bs) + 1);
      const k = [...F.ev.X.P.keys()].sort((a, b) => F.ev.X.P.get(b) - F.ev.X.P.get(a))[0];
      D.st.hover = { k: 'pcell', ev: 'X', k0: k, k1: k + 1, src: 'proj' }; D.render(true);
      const band = D.V.lk && D.V.lk.src === 'pcell' && D.V.win.t1 - D.V.win.t0 === 15;
      D.st.hover = { k: 'now', ev: 'R' }; D.render(true);
      const now = !!(D.V.win && D.V.win.pA != null && D.V.win.t0 == null);
      D.st.hover = null; D.st.pin = { k: 'zone', ev: 'X', i: 0 }; D.render(true);
      const pinned = insp(), zx = D.zonesOf(F, 'X').zones[0].label;
      D.st.hover = { k: 'tcell', b0: 3, b1: 4, src: 'strip' }; D.render(true); const over = insp();
      D.st.hover = null; D.render(true); const back = insp();
      D.st.pin = null; D.render(true); const snap = insp();
      return { zone, band, now, pinned: pinned.includes(zx), over: !over.includes(zx), back: back.includes(zx), snap: /Слепок семьи/.test(snap), pinKept: true };
    });
    check('M12', r.zone && r.band && r.now, 'zone → its whole window; price band → its peak 15 minutes; «Сейчас» → the band of the remaining movement from today\'s extreme', r);
    check('M12', r.pinned && r.over && r.back && r.snap, 'a hover replaces the inspector only while it lasts; leaving restores the pinned zone, then the snapshot', r);
    await open(B, DAY + '&at=11:40&mode=path');
    const p = await evaluate(B.cdp, async () => {
      const { D } = window.__h, F = D.cur().F, film = D.filmOf(F), j = film.findIndex(cd => cd.T > D.cur().obs), k = [...film[Math.max(0, j)].cells.keys()][0];
      D.st.hover = { k: 'fcell', j, kk: k, src: 'proj' }; D.render(true);
      return { row: !!(D.V.lk && D.V.lk.row), m5: D.V.win && D.V.win.t1 - D.V.win.t0 === 5 };
    });
    check('M12', p.row && p.m5, 'a band of «Путь семьи» → its M5 profile (the axis window is one M5)', p);
  },

  // M13: one session's points, path, order, outcome and passport belong to that session; SAME_M5 gets no invented order
  async m13(B) {
    let same = null;
    // NQ ODR 2025-12-09: its family (N 186) holds one session whose first R and X fell in one M5
    for (const h of ['#date=2025-12-09&inst=NQ&session=ODR', DAY]) {
      await open(B, h);
      const r = await evaluate(B.cdp, async () => {
        const H = window.__h, { D, panel } = H, F = D.cur().F;
        if (!F) return null;
        const i = F.M.findIndex(m => m.R.s === 'known' && m.X.s === 'known'), m = F.M[i];
        D.st.pin = { k: 'pt', ev: 'R', i }; D.st.detPin = true; D.render(true); await H.wait(60);
        const sd = v => (Math.abs(v) < 1e-9 ? '0' : (v > 0 ? '+' : '−') + Math.abs(v).toLocaleString('ru-RU', { maximumFractionDigits: 2, minimumFractionDigits: Math.abs(v * 10 - Math.round(v * 10)) < 1e-9 ? 1 : 2 }));
        const ptxt = panel.innerText, det = document.getElementById('det').innerText, date = m.date.split('-').reverse().join('.');
        const own = ptxt.includes(date) && ptxt.includes(sd(m.R.v / m.w)) && ptxt.includes(sd(m.X.v / m.w)) && det.includes(date);
        const k = F.M.findIndex(x => x.order === 'same_M5');
        let s = null;
        if (k >= 0) { D.st.pin = { k: 'pt', ev: 'R', i: k }; D.render(true); s = document.getElementById('panel').innerText.includes(D.lbl('FF:MEMBER', 'order_same')); }
        D.st.pin = null; D.st.detPin = false; D.render(true);
        return { own, same: s };
      });
      if (r) { check('M13', r.own, 'the pinned session: its date, its own R and X, its window — one case in the panel and the six windows', h); if (r.same != null) same = r.same; }
      if (same != null) break;
    }
    check('M13', same === true, 'a session whose R and X fell in one M5 says its order inside the candle is unknown (no invented order)', same);
  },

  // M14: a faulty component loses its number and its dependent drawing; healthy independent components stay
  async m14(B) {
    // (a) the page's tables of a family disagree with the server's bundles → the whole family withheld; candles stay
    await open(B, DAY);
    const a = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.rules.push({ name: 'table', match: '/api/d24/family', when: u => u.includes('date=2025-12-17'), tamper: b => { if (b.counts) b.counts.R.unknown += 1; return b; } });
      D.openHist('2025-12-17'); await H.settle();
      const c = D.cur();
      return { F: !!c.F, text: H.panel.innerText, notice: H.notice(), bars: c.D.bars.length, box: c.s.drH != null };
    });
    check('M14', !a.F && /Числа не публикуются: счёт страницы не совпал с пакетом сервера/.test(a.text) && a.notice && a.bars > 50 && a.box,
      'the family\'s R table disagrees with the server\'s bundle: no number and no drawing of this family; the reason stands; candles and DR / IDR stay', { F: a.F, notice: a.notice, text: a.text.slice(0, 160) });
    // (b) one event's zone map disagrees → zones of that event withheld; the other event, the tables, DR outcome, NOW stay
    await open(B, DAY + '&at=11:40');
    const b = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H, zx = D.zonesOf(D.cur().F, 'X').zones.length, rows0 = H.zoneRows().length;
      T.rules.push({ name: 'zones R', match: '/api/d24/family', tamper: b => { if (b.zones && b.zones.R) b.zones.R.zones[0].n_zone += 1; return b; } });
      D.openHist('2025-12-17'); D.st.rpWanted = 700; await H.wait(50); await H.settle();
      const F = D.cur().F;
      return { F: !!F, R: !!D.zonesOf(F, 'R'), X: (D.zonesOf(F, 'X') || { zones: [] }).zones.length, zx, drawnR: (D.V.zoneHit || []).filter(z => z.ev === 'R').length, capsR: (D.V.caps || []).filter(z => z.ev === 'R').length,
        drawnX: (D.V.zoneHit || []).filter(z => z.ev === 'X').length, rows: H.zoneRows(), rows0, dr: H.pps(F).filter(p => p.est === 'EST:B-DR').every(p => !p.v), now: /\d%/.test(H.nowBlock() || ''), notice: H.notice() };
    });
    check('M14', b.F && !b.R && b.drawnR === 0 && b.capsR === 0 && b.X === b.zx && b.drawnX === b.zx && b.rows.every(t => !/ R\d /.test(' ' + t)) && b.dr && b.now && b.notice,
      'a zone of R disagrees: every R zone (constellations, capsules, rows) withheld; X zones, the DR outcome and «Сейчас» keep their numbers; the reason stands', b);
    // (c) today's zone status disagrees → statuses withheld («—», no state look); every share stays
    await open(B, DAY + '&at=11:40');
    const c = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H, rows0 = H.zoneRows();
      T.rules.push({ name: 'status', match: '/api/d24/family', tamper: b => { const z = b.today && b.today.zones && b.today.zones.R; if (z && z.status && z.status.length) z.status[0] = z.status[0] === 'HOLDS' ? 'IMPOSSIBLE' : 'HOLDS'; return b; } });
      D.st.rpWanted = 700; D.openHist('2025-12-17'); await H.settle();
      const F = D.cur().F, rows = H.zoneRows(), pct = s => (s.match(/\d+(,\d+)?%/) || [''])[0];
      return { F: !!F, rows, rows0, statuses: ['R', 'X'].map(ev => D.zoneStatus(F, D.cur(), ev)), shares: rows.map(pct).join('|') === rows0.map(pct).join('|'), notice: H.notice() };
    });
    check('M14', c.F && c.statuses.flat().every(s => s === 'WITHHELD') && c.rows.every(t => / — /.test(t)) && c.shares && c.notice,
      'today\'s zone status disagrees: every status withheld («—», no state look, today\'s reachability open); every share stays', c);
    // (d) the reference recomputes one zone and one band differently → exactly those numbers and their drawing withheld
    // (another day first: the passports of a snapshot are verified once, so the faulty reference must meet them new)
    await open(B, '#date=2025-12-18&inst=NQ&session=RDR');
    const d = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.flag = {};
      T.rules.push({ name: 'reference', match: '/api/d24/verify', tamper: (body, url, init) => {
        const req = JSON.parse(init.body), z = req.passports.find(p => p.estimand === 'EST:B-ZONE-R'), k = req.passports.find(p => p.estimand === 'EST:B-RX-BAND-X');
        body.mismatches = body.mismatches || [];
        for (const p of [z, k]) if (p && !T.flag[p.estimand]) { T.flag[p.estimand] = p; body.mismatches.push({ id: p.id, estimand: p.estimand, params: p.params, error: `page (${p.yes_count}, ${p.unknown_count}, ${p.no_event_count}) != reference (${p.yes_count - 1}, ${p.unknown_count}, ${p.no_event_count})` }); }
        return body;
      } });
      D.st.rpWanted = 700; D.openHist('2025-12-17'); await H.settle();
      const F = D.cur().F, Z = D.zonesOf(F, 'R').zones, iz = Z.findIndex(z => z.zone_id === T.flag['EST:B-ZONE-R'].params.zone_id), kb = T.flag['EST:B-RX-BAND-X'].params.k0;
      return { iz, kb, nZ: Z.length, caps: (D.V.caps || []).filter(q => q.ev === 'R').map(q => q.i), hills: (D.V.hills || []).filter(q => q.ev === 'R').map(q => q.i), labels: (D.V.zoneHit || []).filter(q => q.ev === 'R').map(q => q.i),
        bar: (D.V.projBars || []).some(q => q.ev === 'X' && q.k === kb), bars: (D.V.projBars || []).filter(q => q.ev === 'X').length,
        row: H.zoneRows().find(t => t.includes(' ' + Z[iz].label + ' ')) || null, others: H.zoneRows().filter(t => !t.includes(' ' + Z[iz].label + ' ')).every(t => /\d%/.test(t)), notice: H.notice() };
    });
    check('M14', d.iz >= 0 && !d.caps.includes(d.iz) && !d.hills.includes(d.iz) && d.labels.includes(d.iz) && / —$/.test(d.row || '') && d.caps.length === d.nZ - 1 && d.others && d.notice,
      'one zone withheld by the reference: its capsule and hill are gone, its name stays with «—»; every other zone keeps its number and drawing', d);
    check('M14', !d.bar && d.bars > 5, 'one band share withheld by the reference: its bar in the price column is gone, the other bars stay', { kb: d.kb, bars: d.bars });
    // (e) one NOW number without its published bundle → that row «—», the other event's row and BASE stay
    await open(B, DAY + '&at=11:40');
    const e = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.rules.push({ name: 'NOW bundle', match: '/api/d24/now', tamper: b => { if (b.contract && b.contract.bundles) b.contract.bundles = b.contract.bundles.filter(x => x.estimand !== 'EST:N-NEW-R'); return b; } });
      D.st.rp = D.cur().obs + 5; await H.settle();
      const rows = [...H.panel.querySelectorAll('.p24-nowblk .p21-link')].map(x => x.innerText.replace(/\s+/g, ' '));
      return { rows, base: H.zoneRows().every(t => /\d%/.test(t)), notice: H.notice() };
    });
    check('M14', e.rows.length === 2 && /—$/.test(e.rows[0]) && /\d%$/.test(e.rows[1]) && e.base && e.notice,
      '«Сейчас» R without its bundle shows «—»; «Сейчас» X and every BASE number stay', e);
  },

  // M15: with the summary hidden, a violation of the scene is reachable from its own button: a steady «!», an outline, the
  // reason in its name; no layer setting hides it; nothing opens, moves or takes the focus
  async m15(B) {
    await open(B, DAY + '&at=11:40');
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      H.hide(true); const clean = H.toggle(), geo0 = H.toolbarGeo(), focus0 = document.activeElement && document.activeElement.id;
      T.rules.push({ name: 'zones R', match: '/api/d24/family', tamper: b => { if (b.zones && b.zones.R) b.zones.R.zones[0].n_zone += 1; return b; } });
      D.st.rpWanted = 700; D.openHist('2025-12-17'); await H.settle();
      const alert = H.toggle(), geo1 = H.toolbarGeo(), focus1 = document.activeElement && document.activeElement.id;
      Object.keys(D.st.L).forEach(k => { D.st.L[k] = false; }); D.render(true);
      const layersOff = H.toggle();
      Object.keys(D.st.L).forEach(k => { D.st.L[k] = true; }); D.render(true);
      H.hide(false); const open_ = { toggle: H.toggle(), notice: H.notice() };
      return { clean, alert, layersOff, open: open_, sameGeo: JSON.stringify(geo0) === JSON.stringify(geo1), focus: focus0 === focus1 };
    });
    check('M15', !r.clean.alert && r.alert.alert && r.alert.hidden && /"!"/.test(r.alert.badge) && /Контракт SC-1\.1/.test(r.alert.aria) && /откройте «Сводку»/.test(r.alert.aria),
      'hidden summary + a violation: «Сводка» carries a steady «!» and an outline, its name gives the reason and where it stands', r.alert);
    check('M15', r.layersOff.alert && r.open.notice && !r.open.toggle.alert, 'no layer setting hides it; opened by the operator, the notice stands at the top and the button is plain again', { layersOff: r.layersOff.alert, notice: r.open.notice });
    check('M15', r.sameGeo && r.focus, 'the sign moves no button of the toolbar and takes no focus (the summary stays hidden until the operator opens it)', r);
    await open(B, DAY);
    const s = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.rules.push({ name: 'server refusal', match: '/api/d24/family', tamper: b => ({ status: 'contract_violation', message: 'нарушение контракта SC-1.1: today\'s confirmation / break differ from the re-derivation', session: b.session, today: b.today, view: b.view, key: b.key, contract: Object.assign({}, b.contract, { status: 'VIOLATION', bundles: undefined }) }) });
      H.hide(true); D.openHist('2025-12-17'); await H.settle();
      return H.toggle();
    });
    check('M15', s.alert && /re-derivation/.test(s.aria), 'the server\'s refusal of the family is reachable the same way', s);
    await open(B, '#date=2025-12-17&inst=NQ&session=RDR&at=10:20');
    const n = await evaluate(B.cdp, async () => { const H = window.__h; H.hide(true); return H.toggle(); });
    check('M15', !n.alert && /семьи ещё нет/.test(n.aria), 'with no violation the hidden summary\'s name says why there are no numbers, without the sign', n);
  },

  // M16: a correction without a verified result does not bring a number back; after verification no prohibition of
  // another scene remains
  async m16(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H, look = () => ({ F: !!D.cur().F, notice: H.notice(), v: D.contract().violations.length, toggle: H.toggle().alert });
      const rule = { name: 'table A', match: '/api/d24/family', when: u => u.includes('date=2025-12-17'), tamper: b => { if (b.counts) b.counts.R.unknown += 1; return b; } };
      T.rules.push(rule);
      D.openHist('2025-12-17'); await H.settle(); const a = look();
      D.render(true); await H.wait(300); D.render(true); const a2 = look();           // nothing new arrived: still withheld
      H.hide(true);
      D.openHist('2025-12-18'); await H.settle(); const b = look();
      rule.when = u => false;                                                              // the server is right again
      D.openHist('2025-12-17'); await H.settle(); const c = look();
      // the same disagreement on two days is reported on each (one context does not swallow the other's)
      T.rules.push({ name: 'table both', match: '/api/d24/family', tamper: x => { if (x.counts) x.counts.X.unknown += 1; return x; } });
      D.openHist('2025-12-18'); await H.settle(); const d1 = look();
      D.openHist('2025-12-16'); await H.settle(); const d2 = look();
      return { a, a2, b, c, d1, d2 };
    });
    check('M16', !r.a.F && r.a.notice && !r.a2.F && r.a2.notice, 'a withheld family stays withheld while no new verified result arrived', r);
    check('M16', r.b.F && !r.b.notice && !r.b.v && !r.b.toggle, 'another day: no notice, no sign, no violation of the previous day', r.b);
    check('M16', r.c.F && !r.c.notice && !r.c.v, 'the same day answered right again: the family returns, verified, with no stale prohibition', r.c);
    check('M16', !r.d1.F && r.d1.v && !r.d2.F && r.d2.v, 'the same disagreement on two days is reported on each of them', { d1: r.d1, d2: r.d2 });
  },

  // M17: only a line the operator set (or moved) gives its alert; one-shot; replay and history stage nothing; a share or
  // «Сейчас» never sets a line
  async m17(B) {
    await open(B, DAY);
    const l = await evaluate(B.cdp, LIVE, '2025-12-17', 700.5);
    const r0 = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.live.high = D.cur().s.priceNow + 40;                 // the price runs far: with no line nothing may fire
      await H.refresh();
      const el = document.getElementById('alToast');
      return { chimes: T.chimes, toast: !!(el && !el.hidden), lines: (D.alerts().NQ || []).length };
    });
    check('M17', l.live && r0.chimes === 0 && !r0.toast && r0.lines === 0, 'no line set: the price may run anywhere, no alert', r0);
    // the operator's gesture: the «+» at the price scale, a little above the forming candle
    const g = await evaluate(B.cdp, () => {
      const { D } = window.__h, cv = document.getElementById('cv').getBoundingClientRect(), s = D.cur().s, p = Math.ceil((D.cur().D.bars.slice(-1)[0].h + 2) / 0.25) * 0.25;
      return { x: cv.left + D.V.plot.w - 10, y: cv.top + D.V.Y(p), p, pxPrice: (D.V.p1 - D.V.p0) / D.V.plot.h };
    });
    await B.cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: g.x, y: g.y });
    await sleep(150);
    await evaluate(B.cdp, () => window.__d24.render(true));
    await B.cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: g.x, y: g.y, button: 'left', clickCount: 1 });
    await B.cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: g.x, y: g.y, button: 'left', clickCount: 1 });
    await sleep(100);
    const r1 = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H, a = (D.alerts().NQ || [])[0];
      if (!a) return { set: false };
      T.live.high = a.p + 0.25;                              // the forming candle crosses the line
      document.getElementById('refresh21').click(); await H.wait(200); await H.settle();
      const el = document.getElementById('alToast'), first = { chimes: T.chimes, toast: !!(el && !el.hidden), text: el ? el.textContent : '', fired: !!a.fired };
      T.live.high = a.p + 1;                                 // crossing again: one-shot
      document.getElementById('refresh21').click(); await H.wait(200); await H.settle();
      return { set: true, p: a.p, first, again: T.chimes };
    });
    check('M17', r1.set && Math.abs(r1.p - g.p) <= 2 * g.pxPrice + 0.25, 'the «+» gesture at the price scale sets one line at that price (within two pixels of the scale)', { set: r1.set, p: r1.p, want: g.p, pxPrice: g.pxPrice });
    check('M17', r1.first && r1.first.fired && r1.first.chimes === 6 && r1.first.toast && /Цена дошла до линии/.test(r1.first.text) && r1.again === 6,
      'the crossing of that line chimes once and shows its note; crossing again stays silent (one-shot)', r1);
    // moving the line re-arms it
    const m = await evaluate(B.cdp, () => { const { D } = window.__h, a = D.alerts().NQ[0], cv = document.getElementById('cv').getBoundingClientRect(); return { x: cv.left + D.V.plot.w * 0.5, y: cv.top + D.V.Y(a.p), y2: cv.top + D.V.Y(a.p + 3) }; });
    await B.cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: m.x, y: m.y }); await sleep(80);
    await evaluate(B.cdp, () => window.__d24.render(true));
    await B.cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: m.x, y: m.y, button: 'left', clickCount: 1 });
    for (let i = 1; i <= 5; i++) { await B.cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: m.x, y: m.y + (m.y2 - m.y) * i / 5, button: 'left' }); await sleep(30); }
    await B.cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: m.x, y: m.y2, button: 'left', clickCount: 1 });
    const r2 = await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H, a = D.alerts().NQ[0], armed = !a.fired, before = T.chimes;
      T.live.high = a.p + 0.25;
      document.getElementById('refresh21').click(); await H.wait(200); await H.settle();
      const fired = T.chimes - before;
      // replay back and forth and a history day: nothing is staged as live
      const c0 = T.chimes;
      D.st.rp = D.cur().obs - 30; D.render(true); D.st.rp = null; D.render(true);
      D.openHist('2025-12-17'); await H.settle(); D.alCheck(); D.st.rp = 700; D.render(true); D.st.rp = 760; D.render(true);
      return { armed, fired, staged: T.chimes - c0, lines: (D.alerts().NQ || []).length, all: Object.values(D.alerts()).flat().length };
    });
    check('M17', r2.armed && r2.fired === 6, 'a moved line is armed again and alerts once on its new price', r2);
    check('M17', r2.staged === 0 && r2.lines === 1 && r2.all === 1, 'replay and a history day stage no alert; the only line is the one the operator set (no share or «Сейчас» set one)', r2);
  },

  // M18: no rearrangement by a share or a state; the anchors, the auto / manual scale and the settings keep their rules
  async m18(B) {
    await open(B, DAY);
    const r = await evaluate(B.cdp, async () => {
      const H = window.__h, { D } = H, F = D.cur().F, heads = [], order = [], geo = [];
      for (const dt of [5, 45, 120, 240, 330]) {
        const t = F.act0 + dt; if (t > F.end) break;
        D.st.rp = t; await H.settle();
        heads.push(H.heads().join(' > ')); order.push(H.zoneRows().map(x => (x.match(/ ([RX]\d+) /) || [])[1]).join(',')); geo.push(H.toolbarGeo().filter(g => !/^clock|^apibar|^dayb/.test(g)).join(';'));
      }
      D.st.auto = true; D.render(true); const p0 = [D.V.p0, D.V.p1];
      D.st.auto = false; D.st.p0 = p0[0] - 50; D.st.p1 = p0[1] + 50; D.st.rp = F.act0 + 60; await H.settle(); const manual = D.V.p0 === p0[0] - 50 && D.V.p1 === p0[1] + 50;
      document.querySelector('#nav [data-z="0"]').click(); D.render(true); const reset = D.st.auto === true;
      return { heads: [...new Set(heads)], order: [...new Set(order)], geo: [...new Set(geo)].length, manual, reset };
    });
    check('M18', r.heads.length === 1 && r.order.length === 1, 'across cuts the panel keeps its order of blocks and the zones their order by time (no rearrangement by share or status)', r);
    check('M18', r.geo === 1, 'the toolbar keeps its places across cuts', r.geo);
    check('M18', r.manual && r.reset, 'a manual scale turns «Авто» off and stays; «↺» restores it', r);
  },

  // A1 (SWPC §3.3, W01): the scene's context — instrument, session, date, mode, the clock with the cut and its controls —
  // is wholly inside the window at both working sizes, in history and on a break day
  async a1(B) {
    for (const size of [[1600, 900], [1920, 1000]]) for (const h of [DAY + '&at=11:40', BRK, '#date=2025-11-05&inst=ES&session=ADR']) {
      await open(B, h, size);
      const r = await evaluate(B.cdp, () => {
        const W = innerWidth, out = [], pill = document.querySelector('#clock .pill');
        // the known exception of AGENTS.md / SWPC §8.4: the last control of the toolbar up to 11 px beyond 1600 in history
        for (const id of ['inst', 'sess', 'date', 'mode', 'ev', 'areab', 'dayb', 'step21', 'panel21toggle', 'lay', 'cfgb', 'clock']) {
          const e = document.getElementById(id);
          if (!e || !e.offsetParent) continue;
          const r = e.getBoundingClientRect();
          if (r.right > W + (id === 'clock' ? 11.5 : 0.5) || r.left < -0.5) out.push(id + ' ' + Math.round(r.left) + '…' + Math.round(r.right));
        }
        const pr = pill.getBoundingClientRect();
        if (pr.right > W + 0.5) out.push('the cut «' + pill.innerText + '» ' + Math.round(pr.left) + '…' + Math.round(pr.right));
        return { W, out, clock: document.getElementById('clock').innerText.replace(/\s+/g, ' ') };
      });
      check('A1', !r.out.length, `${size.join('×')} ${h}: the scene's context and the cut are inside the window (clock «${r.clock}»)`, r.out);
    }
  },

  // the pictures for the operator's comparison (SWPC §8.3): the states where the candidate differs from the base, shot in
  // this isolated instance; only when named (node tests/swpc11_browser.mjs shots; SWPC_SERVE=<base ref> for the base)
  async shots(B) {
    const dir = process.env.SWPC_SHOTS || path.join(ROOT, 'spec', 'ekran-24', 'img', 'swpc'), tag = SERVE0 ? 'baza' : 'kandidat';
    fs.mkdirSync(dir, { recursive: true });
    const shoot = async name => {
      await sleep(400);
      const r = await B.cdp.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(path.join(dir, `${name}-${tag}.png`), Buffer.from(r.data, 'base64'));
      console.log('  ..   ' + path.relative(ROOT, path.join(dir, `${name}-${tag}.png`)));
    };
    // 1 · a zone map of R the page cannot reconcile, the summary hidden by the operator
    await open(B, DAY + '&at=11:40', [1600, 900]);
    await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.rules.push({ name: 'zones R', match: '/api/d24/family', tamper: b => { if (b.zones && b.zones.R) b.zones.R.zones[0].n_zone += 1; return b; } });
      H.hide(true); D.st.rpWanted = 700; D.openHist('2025-12-17'); await H.settle();
    });
    await shoot('1-svodka-skryta');
    // 2 · one zone recomputed differently by the reference, the summary open
    await open(B, '#date=2025-12-18&inst=NQ&session=RDR', [1600, 900]);
    await evaluate(B.cdp, async () => {
      const H = window.__h, { D, T } = H;
      T.flag = {};
      T.rules.push({ name: 'reference', match: '/api/d24/verify', tamper: (body, url, init) => {
        const z = JSON.parse(init.body).passports.find(p => p.estimand === 'EST:B-ZONE-R');
        if (z && !T.flag.z) { T.flag.z = z; (body.mismatches = body.mismatches || []).push({ id: z.id, estimand: z.estimand, params: z.params, error: `page (${z.yes_count}, ${z.unknown_count}, ${z.no_event_count}) != reference (${z.yes_count - 1}, ${z.unknown_count}, ${z.no_event_count})` }); }
        return body;
      } });
      D.st.rpWanted = 700; D.openHist('2025-12-17'); await H.settle();
    });
    await shoot('2-zona-snyata');
    // 3 · a break day at 1600 px: the toolbar and the cut
    await open(B, BRK, [1600, 900]);
    await shoot('3-slom-1600');
    // 4 · «Сейчас» that did not arrive
    await open(B, DAY + '&at=11:40', [1600, 900]);
    await evaluate(B.cdp, async () => { const H = window.__h, { D, T } = H; T.rules.push({ name: 'NOW down', match: '/api/d24/now', fail: true }); D.st.rp = D.cur().obs + 5; await H.settle(); });
    await shoot('4-sejchas-nedostupno');
  },

  // the screen's own check (tests/ui_check24.js) in this isolated instance, at both sizes of AGENTS.md, on several states
  async ui24(B) {
    const code = fs.readFileSync(path.join(ROOT, 'tests', 'ui_check24.js'), 'utf8');
    const states = [DAY, BRK, '#date=2025-12-19&inst=NQ&session=ODR', '#date=2025-12-17&inst=NQ&session=ADR', '#date=2025-11-05&inst=ES&session=ADR'];
    for (const size of [[1600, 900], [1920, 1000]]) for (const h of states) {
      await open(B, h, size);
      const r = await B.cdp.send('Runtime.evaluate', { expression: code, awaitPromise: true, returnByValue: true });
      const v = r.result.value || { problems: ['ui_check24 did not run: ' + JSON.stringify(r.exceptionDetails || r.result).slice(0, 200)] };
      const known = v.problems.filter(p => size[0] === 1600 && /^toolbar overflows: (\d+) > (\d+)$/.test(p) && (+p.match(/(\d+) > (\d+)/)[1] - +p.match(/(\d+) > (\d+)/)[2]) <= 11);
      const rest = v.problems.filter(p => !known.includes(p));
      check('UI24', !rest.length, `tests/ui_check24.js ${size.join('×')} ${h}: ${rest.length ? 'problems' : 'no problems'}${known.length ? ' (the known toolbar exception: ' + known[0] + ')' : ''}`, rest);
    }
  }
};

// ---------------------------------------------------------------- scenes the operator has not worked with
const SERVER = BASE.replace(/\/24\/$/, '');
const api = async p => (await fetch(SERVER + p)).json();
// a seeded generator (mulberry32): the same seed gives the same scenes, recorded in every plan
function rng(seed) { let a = seed >>> 0; return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
// the days used in this repository's documents, tests and reviews, and all of December 2025, are left out
const FAMILIAR = d => d >= '2025-12-01' || ['2025-11-05'].includes(d);
const WIN = { ADR: [-270, -210, 120], ODR: [180, 240, 510], RDR: [570, 630, 960] };
const hm = m => { const x = ((Math.round(m) % 1440) + 1440) % 1440; return String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); };
async function* candidates(R) {
  const pools = {};
  for (const inst of ['NQ', 'ES', 'YM']) pools[inst] = ((await api('/api/d24/dates?instrument=' + inst)).dates || []).filter(([d]) => d >= '2024-01-01' && !FAMILIAR(d));
  for (let i = 0; i < 400; i++) {
    const inst = ['NQ', 'ES', 'YM'][Math.floor(R() * 3)], pool = pools[inst], [date, letters] = pool[Math.floor(R() * pool.length)];
    const session = { A: 'ADR', O: 'ODR', R: 'RDR' }[letters[Math.floor(R() * letters.length)]];
    yield { inst, date, session };
  }
}
// the family of a scene at a cut (the server's own answer, also its today's zone status and clock at that cut)
async function famAt(sc, at, view = 'conf') { return api(`/api/d24/family?instrument=${sc.inst}&session=${sc.session}&at=${at}&date=${sc.date}&view=${view}`); }
const hashOf = (sc, at, extra = '') => `#date=${sc.date}&inst=${sc.inst}&session=${sc.session}` + (at != null ? '&at=' + hm(at) : '') + extra;

// ---------------------------------------------------------------- base = candidate where SWPC-1.1 changed nothing (§8.3)
// on a seeded sample of unfamiliar scenes, in the states the H-tasks use, the base build and the candidate give the same
// pixels and words; the only expected difference is the toolbar where the cut would leave the window (meaning/13 № 51).
// Where the stimuli are identical a human A/B pair can only measure the person, not the screen; where they differ the
// H-session pairs them. A full render costs about the same.
S.same = async B0 => {
  const seed = +(process.env.SWPC_SEED || 20261007), R = rng(seed), scenes = [];
  for await (const sc of candidates(R)) {
    const f = await famAt(sc, WIN[sc.session][2]);
    if (f.status !== 'ok' || !f.N || !f.today || f.today.c0 == null) continue;
    sc.at = Math.floor(Math.min(WIN[sc.session][2] - 10, f.today.c0 + 20 + Math.floor(R() * 120)) / 5) * 5;   // an M5 close, as the screen allows
    scenes.push(sc);
    if (scenes.length >= 6) break;
  }
  scenes.push({ inst: 'NQ', date: '2025-12-10', session: 'RDR', at: 870, brk: true });   // a break day: the fold expected at 1600
  const STATES = ['initial', 'zone', 'band', 'tcell', 'member', 'path', 'hidden', 'zoom'];
  const apply = async st => {
    const H = window.__h, { D } = H, c = D.cur(), F = c.F;
    Object.assign(D.st, { hover: null, pin: null, detPin: false, mode: 'bounds', auto: true, p0: null, p1: null });
    H.hide(false);
    if (F && st === 'zone') { const ev = (D.zonesOf(F, 'R') || { zones: [] }).zones.length ? 'R' : 'X'; if ((D.zonesOf(F, ev) || { zones: [] }).zones.length) D.st.hover = { k: 'zone', ev, i: 0 }; }
    if (F && st === 'band') { const k = [...F.ev.X.P.keys()].sort((a, b) => F.ev.X.P.get(b) - F.ev.X.P.get(a))[0]; if (k != null) D.st.hover = { k: 'pcell', ev: 'X', k0: k, k1: k + 1, src: 'proj' }; }
    if (F && st === 'tcell') D.st.hover = { k: 'tcell', b0: 3, b1: 4, src: 'strip' };
    if (F && st === 'member') { const i = F.M.findIndex(m => m.R.s === 'known' && m.X.s === 'known'); if (i >= 0) { D.st.pin = { k: 'pt', ev: 'R', i }; D.st.detPin = true; } }
    if (F && st === 'path') { D.st.mode = 'path'; const film = D.filmOf(F), j = Math.min(film.length - 1, Math.floor(film.length / 2)), k = [...film[j].cells.keys()][0]; if (k != null) D.st.hover = { k: 'fcell', j, kk: k, src: 'proj' }; }
    if (st === 'hidden') H.hide(true);
    if (st === 'zoom') { D.render(true); const sp = D.V.p1 - D.V.p0; Object.assign(D.st, { auto: false, p0: D.V.p0 + sp * 0.3, p1: D.V.p1 - sp * 0.3 }); }
    D.render(true); await H.wait(150);
    // the reference check of the numbers this state made runs before the picture (it may withhold one of them)
    for (let i = 0; i < 25 && D.contract().unchecked; i++) { await D.verify(); await H.wait(80); }
    D.render(true); await H.wait(60); D.render(true);
    const pill = document.querySelector('#clock .pill'), kc = D.contract();
    return { texts: ['panel', 'insp', 'det', 'tb'].map(id => document.getElementById(id).innerText).join('\n§\n'), fold: !!(pill && pill.getBoundingClientRect().right > innerWidth), violations: kc.all || kc.violations || [] };
  };
  const shot = async () => (await B0.cdp.send('Page.captureScreenshot', { format: 'png' })).data;
  const diff = async (a, b) => evaluate(B0.cdp, async (a, b) => {
    const img = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'data:image/png;base64,' + src; });
    const [x, y] = await Promise.all([img(a), img(b)]), w = x.width, h = x.height, cv = new OffscreenCanvas(w, h), c = cv.getContext('2d');
    c.drawImage(x, 0, 0); const p = c.getImageData(0, 0, w, h).data; c.clearRect(0, 0, w, h); c.drawImage(y, 0, 0); const q = c.getImageData(0, 0, w, h).data;
    let n = 0, x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (let i = 0; i < p.length; i += 4) if (p[i] !== q[i] || p[i + 1] !== q[i + 1] || p[i + 2] !== q[i + 2]) { n++; const k = i / 4, px = k % w, py = Math.floor(k / w); x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py); }
    return { n, box: n ? [x0, y0, x1, y1] : null };
  }, a, b);
  let same = 0, expected = 0;
  const unexpected = [], perf = [], findings = [];
  for (const size of [[1600, 900], [1920, 1000]]) for (const sc of scenes) {
    const got = {};
    for (const which of ['base', 'cand']) {
      B0.serve = which === 'base' ? BASEB() : CAND();
      await open(B0, hashOf(sc, sc.at), size);
      got[which] = {};
      for (const st of STATES) { const r = await evaluate(B0.cdp, apply, st); got[which][st] = { png: await shot(), texts: r.texts, fold: r.fold }; got[which].violations = r.violations; }
      got[which].ms = await evaluate(B0.cdp, () => { const D = window.__d24, t = []; for (let i = 0; i < 25; i++) { const a = performance.now(); D.render(true); t.push(performance.now() - a); } t.sort((a, b) => a - b); return t[12]; });
    }
    perf.push({ scene: sc.inst + ' ' + sc.date + ' ' + sc.session, size: size.join('×'), base: +got.base.ms.toFixed(2), cand: +got.cand.ms.toFixed(2) });
    // a scene with a contract violation is not a scene where nothing changed: there the candidate withholds and signs by
    // design (M14, M15); it is reported as a finding, not compared
    const viol = [...new Set([...got.base.violations, ...got.cand.violations])];
    if (viol.length) { findings.push({ scene: hashOf(sc, sc.at), size: size.join('×'), violations: viol.slice(0, 3) }); continue; }
    for (const st of STATES) {
      const a = got.base[st], b = got.cand[st];
      if (a.png === b.png && a.texts === b.texts) { same++; continue; }
      const d = a.png === b.png ? { n: 0, box: null } : await diff(a.png, b.png);
      // expected: the base's cut would leave the window, the candidate folds the event names — a toolbar-only change
      if (a.fold && !b.fold && (!d.box || d.box[3] < 40)) { expected++; continue; }
      unexpected.push({ scene: hashOf(sc, sc.at), size: size.join('×'), state: st, pixels: d.n, box: d.box, texts: a.texts === b.texts ? 'same' : 'differ' });
    }
  }
  B0.serve = SERVE0;
  check('SAME', !unexpected.length && same > 60, `seed ${seed}: ${scenes.length} scenes × ${STATES.length} states × 2 sizes — ${same} pixel- and text-identical, ${expected} differ only by the toolbar fold where the base hides the cut`, unexpected.slice(0, 6));
  check('SAME', !findings.length, `no scene of the sample carries a contract violation (one that does is compared by M14 / M15, not here)${findings.length ? ': ' + findings.length + ' found' : ''}`, findings);
  const slow = perf.filter(p => p.cand > p.base * 1.25 + 1.5);
  check('SAME', !slow.length, `a full render costs the same (median of 25, ms; base → candidate): ${perf.map(p => p.base + '→' + p.cand).join(', ')}`, slow);
};

// ---------------------------------------------------------------- the H01–H12 session (SWPC §8.2, §8.3)
// plan: unfamiliar scenes (seeded), two passes with different scenes, A/B pairs only where base and candidate differ, a
// no-fault control among the fault scenes; the key (what the screen shows in each step) is read from the screen itself
async function findScene(R, test, tries = 60) {
  for await (const sc of candidates(R)) {
    if (tries-- <= 0) return null;
    const f0 = await famAt(sc, WIN[sc.session][2]);
    if (f0.status !== 'ok' || !f0.today || f0.today.c0 == null) continue;
    const r = await test(sc, f0);
    if (r) return Object.assign(sc, r);
  }
  return null;
}
const cutIn = (R, f0, sc, lo = 25, hi = 150) => Math.floor(Math.min(WIN[sc.session][2] - 10, f0.today.c0 + lo + Math.floor(R() * (hi - lo))) / 5) * 5;
async function general(R) {
  return findScene(R, async (sc, f0) => {
    const at = cutIn(R, f0, sc), f = await famAt(sc, at);
    if (f.status !== 'ok' || f.N < 60 || !f.zones || !f.zones.R || !f.zones.X || !f.zones.R.zones.length || !f.zones.X.zones.length) return null;
    if (![...f.zones.R.zones, ...f.zones.X.zones].some(z => z.p_snapshot >= 0.12)) return null;
    const n = await api(`/api/d24/now?instrument=${sc.inst}&session=${sc.session}&at=${at}&date=${sc.date}&view=conf`);
    if (n.status !== 'OK' || !n.R || !n.R.continuation || !n.X || !n.X.continuation) return null;
    return { at, N: f.N, unknown: f.counts.R.unknown + f.counts.R.none + f.counts.X.unknown + f.counts.X.none };
  });
}
async function planSession(dir, seed) {
  if (!dir) throw new Error('plan <dir> [seed]');
  fs.mkdirSync(dir, { recursive: true });
  const R = rng(seed), passes = [];
  const B = await launch();
  try {
    for (const pass of [1, 2]) {
      const g = [];
      for (let i = 0; i < 5; i++) g.push(await general(R));
      const brk = await findScene(R, async (sc, f0) => f0.today.brk != null && f0.today.brk < WIN[sc.session][2] - 20 ? { at: Math.min(WIN[sc.session][2] - 10, f0.today.brk + 20) } : null);
      const pre = await findScene(R, async (sc, f0) => f0.today.c0 - WIN[sc.session][1] >= 15 ? { at: WIN[sc.session][1] + 5 } : null);
      const small = await findScene(R, async (sc, f0) => {
        if (f0.N >= 40) return null;
        const at = cutIn(R, f0, sc, 20, 90), n = await api(`/api/d24/now?instrument=${sc.inst}&session=${sc.session}&at=${at}&date=${sc.date}&view=conf`);
        return n.R && n.R.mode === 'INSUFFICIENT_SUPPORT' ? { at } : null;
      }, 120);
      const nozone = await findScene(R, async (sc, f0) => {
        const at = cutIn(R, f0, sc, 20, 90), f = await famAt(sc, at);
        return f.status === 'ok' && f.zones && ['R', 'X'].some(ev => f.zones[ev] && !f.zones[ev].zones.length) ? { at } : null;
      }, 120);
      const same5 = await findScene(R, async (sc, f0) => { const i = (f0.members || []).findIndex(m => m.order === 'same_M5'); return i >= 0 ? { at: f0.today.c0, pt: i } : null; }, 150);
      // the two states of the history clock and reachability are found on the screen itself, scanning the cuts of a day
      let quiet = null, holds = null;
      for (let i = 0; i < 12 && !(quiet && holds); i++) {
        const sc = g[i % g.length] && Object.assign({}, g[i % g.length]);
        if (!sc) break;
        const alt = i < g.length ? sc : await general(R);
        if (!alt) continue;
        await open(B, hashOf(alt, null));
        const r = await evaluate(B.cdp, () => {
          const { D } = window.__h, F = D.cur().F, out = { quiet: null, holds: null };
          if (!F) return out;
          for (let t = F.act0 + 5; t <= F.end; t += 5) {
            D.st.rp = t; D.render(true); const c = D.cur(); if (!c.F) continue;
            for (const ev of ['R', 'X']) {
              const Zm = D.zonesOf(c.F, ev); if (!Zm) continue;
              const S = D.zoneStatus(c.F, c, ev), K = D.zoneClock(c.F, c, ev);
              Zm.zones.forEach((z, k) => {
                if (!out.quiet && S[k] === 'POSSIBLE' && K[k] === 'FUTURE_EMPTY') out.quiet = { t, ev, label: z.label };
                if (!out.holds && S[k] === 'HOLDS' && c.F.f + 15 * (Math.max(...z.cell_mask.map(q => q[1])) + 1) <= t) out.holds = { t, ev, label: z.label };
              });
            }
          }
          return out;
        });
        if (!quiet && r.quiet) quiet = Object.assign({}, alt, { at: r.quiet.t, zone: r.quiet.label });
        if (!holds && r.holds) holds = Object.assign({}, alt, { at: r.holds.t, zone: r.holds.label });
      }
      const odd = n => n % 2 === 1;                       // §8.3: odd tasks base → candidate, even tasks candidate → base
      const pair = (task, step) => odd(+task.slice(1)) ? [Object.assign({}, step, { variant: 'base' }), Object.assign({}, step, { variant: 'cand' })] : [Object.assign({}, step, { variant: 'cand' }), Object.assign({}, step, { variant: 'base' })];
      const S1 = (task, part, sc, extra = {}) => sc ? Object.assign({ task, part, hash: hashOf(sc, sc.at, extra.suffix || ''), variant: 'cand', faults: [], hide: false }, extra) : { task, part, missing: true };
      const steps = [
        S1('H01', 'а', g[0], { distract: true }),
        ...(brk ? pair('H01', S1('H01', 'б', brk, { distract: true })) : [S1('H01', 'б', null)]),
        S1('H02', '', g[1]),
        S1('H03', '', g[1], { spontaneous: true }),
        S1('H04', 'а', quiet, { point: quiet && quiet.zone }), S1('H04', 'б', holds, { point: holds && holds.zone }),
        S1('H05', '', g[2]),
        S1('H06', 'а', g.find(s => s && s.unknown) || g[2]), S1('H06', 'б', nozone), S1('H06', 'в', small),
        ...pair('H06', S1('H06', 'г', g[4], { faults: ['nowDown'] })),
        ...pair('H06', S1('H06', 'д', g[4], { faults: ['refZone'] })),
        S1('H06', 'е', pre),
        S1('H07', '', g[2]),
        S1('H08', 'а', g[3], { suffix: '&mode=path' }), S1('H08', 'б', same5, { suffix: same5 ? '&pt=' + same5.pt : '' }),
        S1('H09', '', g[3], { distract: true }),
        ...(() => { const [a, b] = pair('H10', S1('H10', 'сбой', g[4], { faults: ['zonesR'], hide: true })); return [a, S1('H10', 'контроль', g[0], { hide: true }), b]; })(),
        S1('H11', '', g[3] && Object.assign({}, g[3], { at: null }), { live: g[3] ? { date: g[3].date, now: g[3].at + 2.5, inst: g[3].inst } : null, realAudio: true }),
        S1('H12', '', g[0])
      ];
      steps.forEach((s, i) => { s.n = i + 1; });
      // the key: what the screen shows in each step, read from it (candidate or base as presented)
      for (const s of steps) {
        if (s.missing) continue;
        B.serve = s.variant === 'base' ? BASEB() : CAND();
        await B.setStubs({ faults: s.faults, live: s.live || undefined });
        await open(B, s.live ? '' : s.hash);
        s.key = await evaluate(B.cdp, async (hide, point) => {
          const H = window.__h, { D, panel } = H, F = D.cur().F;
          if (hide) H.hide(true);
          const k = { header: (panel.querySelector('.p21-h') || {}).innerText || null, date: document.getElementById('date').innerText, clock: document.getElementById('clock').innerText.replace(/\s+/g, ' '),
            rows: H.zoneRows(), now: H.nowBlock(), notes: [...panel.querySelectorAll('.p21-note,.p21-empty')].map(e => e.innerText), notice: H.notice(), toggle: H.toggle() };
          if (F && point) { const ev = point[0], i = (D.zonesOf(F, ev) || { zones: [] }).zones.findIndex(z => z.label === point); if (i >= 0) { D.st.hover = { k: 'zone', ev, i }; D.render(true); k.inspector = document.getElementById('insp').innerText; D.st.hover = null; } }
          if (F && !point) { const both = [...F.ev.R.P.keys()].filter(q => F.ev.X.P.get(q)).sort((a, b) => (F.ev.R.P.get(b) + F.ev.X.P.get(b)) - (F.ev.R.P.get(a) + F.ev.X.P.get(a)))[0]; if (both != null) { D.st.hover = { k: 'pcell', ev: 'R', k0: both, k1: both + 1, src: 'proj' }; D.render(true); k.band = document.getElementById('insp').innerText; D.st.hover = null; } }
          D.render(true);
          return k;
        }, !!s.hide, s.point || null);
        await B.setStubs({});
      }
      passes.push({ pass, steps });
    }
  } finally { B.serve = SERVE0; await B.close(); }
  const cand = buildFiles(CAND() || { dir: path.join(ROOT, 'lab', 'dist', '24') }), base = buildFiles(BASEB());
  const plan = { seed, created: new Date().toISOString(), base_ref: BASE_REF, cand_ref: CAND_REF || 'working tree', size: [1600, 900],
    builds: { cand: { 'd24.js': sha(cand['d24.js']), 'index.html': sha(cand['index.html']) }, base: { 'd24.js': sha(base['d24.js']), 'index.html': sha(base['index.html']) } }, passes };
  fs.writeFileSync(path.join(dir, 'plan.json'), JSON.stringify(plan, null, 1));
  const L = ['# Ключ оценщика · сеанс ' + seed, '', 'Только для оценщика: оператор видит ключ после обоих проходов. Сцены — дни, с которыми оператор не работал (seed ' + seed + ').', ''];
  for (const p of passes) {
    L.push('## Проход ' + p.pass, '');
    for (const s of p.steps) {
      L.push(`### ${s.n} · ${s.task}${s.part ? ' ' + s.part : ''}${s.variant === 'base' ? ' · база' : ''}`);
      if (s.missing) { L.push('', 'сцена не найдена за отведённое число попыток — задача в этом проходе не проводится', ''); continue; }
      L.push('', '`' + (s.live ? 'синтетический live ' + JSON.stringify(s.live) : s.hash) + '`' + (s.faults.length ? ' · сбой: ' + s.faults.join(', ') : '') + (s.hide ? ' · «Сводка» скрыта' : '') + (s.distract ? ' · с отвлечением' : '') + (s.spontaneous ? ' · сначала свободное описание' : ''), '');
      const k = s.key || {};
      for (const [name, v] of [['заголовок', k.header], ['дата', k.date], ['часы', k.clock], ['зоны', (k.rows || []).join(' | ')], ['«Сейчас»', k.now], ['строки', (k.notes || []).join(' | ')], ['строка контракта', k.notice], ['кнопка «Сводка»', k.toggle && (k.toggle.alert ? '«!» · ' : '') + (k.toggle.aria || '')], ['инспектор зоны', k.inspector], ['инспектор полосы', k.band]])
        if (v) L.push('- ' + name + ': ' + String(v).replace(/\n/g, ' · '));
      L.push('');
    }
  }
  fs.writeFileSync(path.join(dir, 'key.md'), L.join('\n'));
  const rec = ['# Запись сеанса · ' + seed, '', 'Обстановка: монитор …, разрешение …, масштаб Windows …, браузера …, дистанция …, освещение … (неизвестное — «неизвестно»). Настройки: копия оператора / по умолчанию.', '',
    '| Проход | Шаг | Задача | Вариант (метка) | Ответ | Свободное описание (H03) | Крит. ошибка | Ошибка взаимодействия | Ложная тревога | Время до верного ответа | Помощь | Заметили разницу? |', '|---|---|---|---|---|---|---|---|---|---|---|---|'];
  for (const p of passes) for (const s of p.steps) rec.push(`| ${p.pass} | ${s.n} | ${s.task}${s.part ? ' ' + s.part : ''} | ${s.variant === 'base' ? 'база' : 'кандидат'} |  |  |  |  |  |  |  |  |`);
  fs.writeFileSync(path.join(dir, 'record.md'), rec.join('\n') + '\n');
  console.log('plan, key and record written to ' + dir);
  for (const p of passes) console.log('pass ' + p.pass + ': ' + p.steps.map(s => s.n + ' ' + s.task + (s.part ? s.part : '') + (s.variant === 'base' ? '(база)' : '') + (s.missing ? '(нет сцены)' : '')).join(', '));
}

async function sessionOpen(dir) {
  const plan = JSON.parse(fs.readFileSync(path.join(dir, 'plan.json'), 'utf8'));
  const c = await startChrome({ headed: !process.env.SWPC_HEADLESS, prof: path.join(dir, 'profile'), size: plan.size, detached: true });
  fs.writeFileSync(path.join(dir, 'session.json'), JSON.stringify({ port: c.port, pid: c.proc.pid, prof: c.prof }));
  console.log('the session window is open (port ' + c.port + ')');
}
async function sessionShow(dir, pass, n) {
  const plan = JSON.parse(fs.readFileSync(path.join(dir, 'plan.json'), 'utf8')), ses = JSON.parse(fs.readFileSync(path.join(dir, 'session.json'), 'utf8'));
  const s = plan.passes.find(p => p.pass === pass).steps.find(x => x.n === n);
  if (!s || s.missing) throw new Error('no such step or no scene for it');
  let settings;
  try { settings = JSON.parse(fs.readFileSync(path.join(dir, 'settings.json'), 'utf8')); } catch (e) { settings = undefined; }
  const B = await attach(ses.port, { faults: s.faults, live: s.live || undefined, realAudio: !!s.realAudio, settings }, s.variant === 'base' ? BASEB() : CAND());
  await B.cdp.send('Page.navigate', { url: 'about:blank' });
  await sleep(80);
  await B.cdp.send('Page.navigate', { url: BASE + (s.live ? '' : s.hash) });
  for (let i = 0; i < 100; i++) { if (await evaluate(B.cdp, () => !!(window.__d24 && document.readyState === 'complete')).catch(() => false)) break; await sleep(100); }
  await evaluate(B.cdp, HELPERS);
  await evaluate(B.cdp, async hide => { await window.__h.settle(); if (hide) window.__h.hide(true); }, !!s.hide);
  await B.cdp.send('Fetch.disable');
  B.cdp.close();
  fs.appendFileSync(path.join(dir, 'log.jsonl'), JSON.stringify({ pass, n, task: s.task, part: s.part, variant: s.variant, shown: new Date().toISOString() }) + '\n');
  console.log(`shown: pass ${pass} step ${n} · ${s.task} ${s.part || ''} · ${s.variant === 'base' ? 'база' : 'кандидат'}${s.faults.length ? ' · ' + s.faults.join(',') : ''}`);
}
async function sessionTick(dir, high) {
  const ses = JSON.parse(fs.readFileSync(path.join(dir, 'session.json'), 'utf8')), B = await attach(ses.port, {}, null);
  await evaluate(B.cdp, async h => { const T = window.__swpcTest; if (!T || !T.live) return; T.live.high = h === 'line' ? (window.__d24.alerts()[window.__d24.A.inst] || [{}])[0].p + 0.25 : +h; document.getElementById('refresh21').click(); }, high);
  await B.cdp.send('Fetch.disable'); B.cdp.close();
  fs.appendFileSync(path.join(dir, 'log.jsonl'), JSON.stringify({ tick: high, at: new Date().toISOString() }) + '\n');
}
async function sessionClose(dir) {
  const ses = JSON.parse(fs.readFileSync(path.join(dir, 'session.json'), 'utf8'));
  try { process.kill(ses.pid); } catch (e) { /* closed */ }
  await sleep(800);
  for (let i = 0; i < 20; i++) { try { fs.rmSync(ses.prof, { recursive: true, force: true }); break; } catch (e) { await sleep(250); } }
  fs.rmSync(path.join(dir, 'session.json'), { force: true });
  console.log('the session window is closed and its profile removed');
}

// ---------------------------------------------------------------- main
const [cmd, ...rest] = process.argv.slice(2);
if (cmd === 'plan') { await planSession(rest[0], +rest[1] || (Date.now() % 1000000)); process.exit(0); }
if (cmd === 'session-open') { await sessionOpen(rest[0]); process.exit(0); }
if (cmd === 'show') { await sessionShow(rest[0], +rest[1], +rest[2]); process.exit(0); }
if (cmd === 'tick') { await sessionTick(rest[0], rest[1]); process.exit(0); }
if (cmd === 'session-close') { await sessionClose(rest[0]); process.exit(0); }
const want = process.argv.slice(2);
const B = await launch();
try {
  for (const [name, fn] of Object.entries(S)) {
    if (want.length ? !want.includes(name) : ['shots', 'same'].includes(name)) continue;
    console.log('— ' + name);
    try { await fn(B); } catch (e) { check(name.toUpperCase(), false, 'the scenario failed to run', String(e.stack || e).slice(0, 900)); }
  }
} finally {
  await B.close();
}
if (B.errors.length) console.log('page exceptions:', B.errors.slice(0, 5));
const bad = results.filter(r => !r.ok);
console.log(bad.length ? bad.length + ' FAILED' : 'ALL GOOD (' + results.length + ' checks)');
process.exit(bad.length ? 1 : 0);
