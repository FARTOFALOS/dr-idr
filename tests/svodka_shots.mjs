// Screen 24 · full-size snapshots of scenes in a throw-away headless Chrome (the «Сводка» candidate, 13.10.2026).
//
//     node tests/svodka_shots.mjs --base http://127.0.0.1:<port>/24/ --dir <folder> [--w 1600 --h 900] "<name>=<fragment>[|hover=<k>]" ...
//
// For each scene the page is opened fresh, the script waits until the family, «Сейчас» and «Отсюда» are answered and
// every passport is checked by the server's reference (or, before the confirmation, until the summary has its answer),
// optionally hovers one row of the summary (k = the link kind: cmp, now, arrive, fact, phase, zone …; the first such
// row), and saves <name>.png and <name>.json (the contract state and whether the scene was complete). These are images
// of the instrument, not of the tape; nothing is written but the output folder. Exit code 0 = every scene saved.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const argv = process.argv.slice(2);
const opt = (name, dflt) => { const i = argv.indexOf(name); if (i < 0) return dflt; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const BASE = opt('--base', 'http://127.0.0.1:8774/24/');
const DIR = opt('--dir', null);
const W = +opt('--w', '1600'), H = +opt('--h', '900');
const SCENES = argv;
const CHROMES = [process.env.CHROME, 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', '/usr/bin/google-chrome', '/usr/bin/chromium'].filter(Boolean);
const sleep = ms => new Promise(r => setTimeout(r, ms));

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url), pend = new Map();
    let id = 0;
    ws.onopen = () => resolve({
      send(method, params = {}) { const i = ++id; ws.send(JSON.stringify({ id: i, method, params })); return new Promise((ok, no) => pend.set(i, { ok, no, method })); },
      close() { try { ws.close(); } catch (e) { /* closed */ } }
    });
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.id) { const p = pend.get(m.id); pend.delete(m.id); if (p) m.error ? p.no(new Error(p.method + ': ' + JSON.stringify(m.error))) : p.ok(m.result); }
    };
    ws.onerror = e => reject(new Error('CDP: ' + (e.message || 'socket error')));
  });
}

async function startChrome() {
  const exe = CHROMES.find(p => fs.existsSync(p));
  if (!exe) throw new Error('no Chrome or Edge found (set CHROME)');
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'drlab-shots-'));
  const proc = spawn(exe, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1', '--no-first-run',
    '--no-default-browser-check', '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, 'about:blank'], { stdio: 'ignore' });
  let port = null;
  for (let i = 0; i < 150 && !port; i++) {
    try { port = fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim() || null; } catch (e) { /* not yet */ }
    if (!port) await sleep(100);
  }
  if (!port) { proc.kill(); throw new Error('Chrome did not open its debugging port'); }
  const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const cdp = await connect(list.find(t => t.type === 'page').webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  return { cdp, close: async () => { cdp.close(); proc.kill(); for (let i = 0; i < 20; i++) { try { fs.rmSync(prof, { recursive: true, force: true }); break; } catch (e) { await sleep(250); } } } };
}

const evaluate = async (cdp, fn, arg) => {
  const r = await cdp.send('Runtime.evaluate', { expression: '(' + fn + ')(' + JSON.stringify(arg === undefined ? null : arg) + ')', returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error('page: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text));
  return r.result.value;
};

// in the page: what is still missing before the scene is complete
const READY = function () {
  const d = window.__d24;
  if (!d || !d.V || !d.V.ctx) return 'page state';
  d.render(true);
  const ctx = d.V.ctx, C = d.contract(), panel = document.getElementById('panel'), txt = panel ? panel.innerText : '';
  if (/Загружаю|Собираю семью|Подбираю похожие|считаю…/.test(txt)) return 'panel loading';
  if (!ctx.F) return ['confirmed', 'broken', 'done'].includes(ctx.s.status) ? 'family' : 'ok';
  const n = d.nowOf(ctx), r = d.arriveOf(ctx);
  if (!n || !n.status) return 'now';
  if (!r || !r.status) return 'arrive';
  if (C.unchecked) { d.verify(); return 'unchecked passports ' + C.unchecked; }
  return 'ok';
};
const HOVER = function (k) {
  const d = window.__d24, L = d.links(), els = [...document.querySelectorAll('#panel [data-l21]')];
  const [kind, key] = k.split(':');
  const el = els.find(e => { const h = L[+e.dataset.l21] || {}; return h.k === kind && (!key || (kind === 'now' ? h.ev : h.id) === key); });
  if (!el) return false;
  el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
  d.render(false);
  return true;
};
const STATE = function () {
  const d = window.__d24, C = d.contract(), p = document.getElementById('panel');
  const rect = el => { if (!el) return null; const r = el.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; };
  const cv = document.getElementById('cv').getBoundingClientRect(), V = d.V, P = (x, y) => [cv.x + x, cv.y + y];
  const queries = [...p.querySelectorAll('.p24-q')].map(el => ({ text: el.innerText.split('\n')[0], r: rect(el) }));
  const geometry = { W: innerWidth, H: innerHeight, dom: { mode: rect(document.getElementById('mode')), frequencies: rect(document.getElementById('pathfreq21')), insp: rect(document.getElementById('insp')) },
    panel: { queries }, chart: { current: V.currentClose ? P(V.X(V.currentClose.t), V.Y(V.currentClose.p)) : null,
      place: V.graphEvidence && V.graphEvidence.price != null ? P(V.plot.w + V.axisW / 2, V.Y(V.graphEvidence.price)) : null,
      time: V.win && V.win.t0 != null ? P(V.X((V.win.t0 + V.win.t1) / 2), V.taxisY + 14) : null } };
  return { contract: { registry_hash: C.registry_hash, violations: C.violations, unchecked: C.unchecked }, panel_scroll: [p.scrollHeight, p.clientHeight], geometry };
};

async function main() {
  if (!DIR || !SCENES.length) throw new Error('usage: --dir <folder> "<name>=<fragment>[|hover=<k>]" ...');
  fs.mkdirSync(DIR, { recursive: true });
  const B = await startChrome();
  try {
    for (const spec of SCENES) {
      const eq = spec.indexOf('='), name = spec.slice(0, eq), [frag, ...mods] = spec.slice(eq + 1).split('|');
      const hover = (mods.find(m => m.startsWith('hover=')) || '').slice(6) || null;
      await B.cdp.send('Page.navigate', { url: 'about:blank' });
      await sleep(200);
      await B.cdp.send('Page.navigate', { url: BASE + frag });
      let why = 'start', t0 = Date.now();
      while (Date.now() - t0 < 90000) {
        await sleep(500);
        try { why = await evaluate(B.cdp, READY); } catch (e) { why = String(e.message); }
        if (why === 'ok') break;
      }
      await sleep(600);
      let hovered = null;
      if (hover) { hovered = await evaluate(B.cdp, HOVER, hover); await sleep(400); }
      const shot = await B.cdp.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(path.join(DIR, name + '.png'), Buffer.from(shot.data, 'base64'));
      const state = await evaluate(B.cdp, STATE);
      fs.writeFileSync(path.join(DIR, name + '.json'), JSON.stringify(Object.assign({ name, fragment: frag, hover, hovered, complete: why === 'ok', waiting_for: why === 'ok' ? null : why }, state), null, 1));
      console.log(name, why === 'ok' ? 'ok' : 'INCOMPLETE: ' + why, hover ? 'hover ' + hover + ':' + hovered : '');
    }
  } finally { await B.close(); }
}
main().then(() => process.exit(0), e => { console.error(e.message); process.exit(1); });
