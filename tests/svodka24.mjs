// The «Сводка» candidate of screen 24 on real scenes, in a throw-away headless Chrome (branch svodka-24, 13.10.2026).
//
//     node tests/svodka24.mjs [--base http://127.0.0.1:<port>/24/]
//
// For each declared scene (three sequences of one real day M5 by M5 and the edge states) the page is opened fresh at
// 1600 × 900, waited for (family, «Сейчас», «Отсюда», the reference check of every passport), and two in-page checks are
// evaluated: tests/ui_check24.js (the accepted screen's invariants) and tests/svodka24_check.js (the candidate's
// distinctions, C1–C12). A scene passes when both return no problem and the contract has no violation. Nothing is written.
// The server of this checkout must run on the given base (never the operator's 8767 / 8771 / 8772).
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (name, dflt) => { const i = argv.indexOf(name); if (i < 0) return dflt; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const BASE = opt('--base', 'http://127.0.0.1:8774/24/');
const UI_PATH = opt('--ui', null);          // another copy of ui_check24.js (the accepted line's, to tell an old problem from a new one)
const ONLY_UI = argv.includes('--ui-only');
const ES = '#date=2024-03-04&inst=ES&session=RDR&at=';
// the sequences of the brief §8 on one real day (ES RDR 04.03.2024: long; +0,5, a pullback through the IDR edge, its
// middle and −0,7, then a new high) and the edge states
const SCENES = [
  ['S1 откат после расширения', ['10:45', '10:55', '11:10', '11:20', '11:25', '11:35', '11:40'].map(t => ES + t)],
  ['S3 время после окна отката', ['12:00', '12:15', '12:25', '12:45'].map(t => ES + t)],
  ['E1 до подтверждения', ['#date=2025-02-27&inst=NQ&session=RDR&at=10:55']],
  ['E2 после слома DR, малая семья', ['#date=2025-03-07&inst=NQ&session=RDR&at=14:35']],
  ['E3 мало сессий у «Отсюда»; шорт', ['#date=2025-12-17&inst=NQ&session=RDR&at=11:10', '#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all']],
  ['E4 пропуск M5 в сегодняшнем пути', ['#date=2024-08-02&inst=ES&session=RDR&at=12:05']],
];
// problems the accepted line (PR #8, served by its own checkout) shows on the same scenes with its own ui_check24.js
// (run of 13.10.2026): not regressions of the candidate, reported apart and not counted
const KNOWN = [/^ui_check24 toolbar overflows: 16\d\d > 1600$/, /^ui_check24 panel shows session counts$/];
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
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'drlab-svodka-'));
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
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
  return { cdp, close: async () => { cdp.close(); proc.kill(); for (let i = 0; i < 20; i++) { try { fs.rmSync(prof, { recursive: true, force: true }); break; } catch (e) { await sleep(250); } } } };
}
const run = async (cdp, expression) => {
  const r = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error('page: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text));
  return r.result.value;
};
const READY = `(() => { const d = window.__d24; if (!d || !d.V || !d.V.ctx) return 'page'; d.render(true); const c = d.V.ctx, C = d.contract(), t = (document.getElementById('panel') || {}).innerText || '';
  if (/Загружаю|Собираю семью|Подбираю похожие|считаю…/.test(t)) return 'panel';
  if (!c.F) return ['confirmed', 'broken', 'done'].includes(c.s.status) ? 'family' : 'ok';
  if (!d.nowOf(c) || !d.arriveOf(c)) return 'answers'; if (C.unchecked) { d.verify(); return 'unchecked'; } return 'ok'; })()`;

async function main() {
  const UI = fs.readFileSync(UI_PATH || path.join(HERE, 'ui_check24.js'), 'utf8'), SV = fs.readFileSync(path.join(HERE, 'svodka24_check.js'), 'utf8');
  const B = await startChrome();
  let bad = 0, n = 0;
  try {
    for (const [name, frags] of SCENES) {
      console.log(name);
      for (const f of frags) {
        await B.cdp.send('Page.navigate', { url: 'about:blank' }); await sleep(150);
        await B.cdp.send('Page.navigate', { url: BASE + f });
        let why = 'start';
        for (let t0 = Date.now(); Date.now() - t0 < 90000;) { await sleep(400); try { why = await run(B.cdp, READY); } catch (e) { why = e.message; } if (why === 'ok') break; }
        const sv = ONLY_UI ? { problems: [], info: {} } : await run(B.cdp, SV), ui = await run(B.cdp, UI), k = await run(B.cdp, 'window.__d24.contract()');
        const all = [].concat(why === 'ok' ? [] : ['not complete: ' + why], sv.problems.map(p => 'svodka ' + p), (ui.problems || []).map(p => 'ui_check24 ' + p), k.violations.map(v => 'SC-1.1 ' + v));
        const probs = all.filter(p => !KNOWN.some(re => re.test(p))), known = all.filter(p => KNOWN.some(re => re.test(p)));
        n++; if (probs.length) bad++;
        console.log('  ' + (probs.length ? 'FAIL' : 'ok  ') + ' ' + f.replace(/^#/, '') + (sv.info && sv.info.change ? ' · ' + sv.info.change : '') + (probs.length ? '\n      ' + probs.join('\n      ') : '') + (known.length ? '\n      known on the accepted line: ' + known.join(' | ') : ''));
      }
    }
  } finally { await B.close(); }
  console.log(bad ? `${bad} of ${n} scenes FAIL` : `ALL GOOD (${n} scenes)`);
  process.exit(bad ? 1 : 0);
}
main().catch(e => { console.error(e.message); process.exit(1); });
