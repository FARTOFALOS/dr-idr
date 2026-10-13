// DR Lab semantic trace · the state screen 24 actually rendered, collected in a throw-away headless Chrome.
//
//     node tests/trace_page.mjs --base http://127.0.0.1:<port>/24/ --out <file> "<fragment>" ["<fragment>" ...]
//
// Normally started by `python -B lab/semtrace.py run --screens`, which runs this checkout's server on a free port (never
// 8767, 8771 or 8772) and stops it afterwards. For each fragment (a declared scene: a history day, a cut, a scope) the
// page is opened fresh at 1600 × 900, the script waits until the family, «Сейчас» and «Отсюда» are answered and every
// passport has been checked by the server's reference (POST /api/d24/verify), then reads, for every element of the panel
// that links to the chart (data-l21): where it stands, what it shows, what it is bound to — a passport of the page, a
// bundle the server published (the very object the page used), or a reason of absence — and whether its visible words
// are the registered labels the page's own lbl() renders with these values. Visible texts are returned raw; the Python
// side (lab/semtrace.py::ingest_screen) keeps only their digests (a row may hold a price). Nothing is written but the
// output file; the browser profile is temporary and deleted. Exit code 0 = every fragment collected.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const argv = process.argv.slice(2);
const opt = (name, dflt) => { const i = argv.indexOf(name); if (i < 0) return dflt; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const BASE = opt('--base', 'http://127.0.0.1:8767/24/');
const OUT = opt('--out', null);
const FRAGMENTS = argv;
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
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'drlab-trace-'));
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

const evaluate = async (cdp, fn) => {
  const r = await cdp.send('Runtime.evaluate', { expression: '(' + fn + ')()', returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error('page: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text));
  return r.result.value;
};

// in the page: what is still missing before the scene is complete (the family, «Сейчас», «Отсюда», the reference check)
const READY = function () {
  const d = window.__d24;
  if (!d || !d.V || !d.V.ctx) return 'page state';
  const ctx = d.V.ctx, C = d.contract();
  if (!d.passports().length) return 'passports';
  const n = d.nowOf(ctx), r = d.arriveOf(ctx);
  if (!n || !n.status) return 'now';
  if (!r || !r.status) return 'arrive';
  if (C.unchecked) return 'unchecked passports ' + C.unchecked;
  if (!document.querySelector('[data-l21]')) return 'panel';
  return 'ok';
};

// in the page: every element of the panel that links to the chart, with what it shows and what it is bound to
const COLLECT = function () {
  const d = window.__d24, ctx = d.V.ctx, C = d.contract();
  const P = new Map(d.passports().map(p => [String(p.id), p]));
  const L = d.links();
  const strip = s => String(s == null ? '' : s).replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  const n = d.nowOf(ctx), r = d.arriveOf(ctx);
  const par = b => { try { return JSON.parse(b.parameters || '{}'); } catch (e) { return {}; } };
  const els = [];
  for (const el of document.querySelectorAll('[data-l21]')) {
    const i = +el.dataset.l21, h = L[i] || {};
    const pp = el.dataset.pp ? P.get(el.dataset.pp) : null;
    const block = el.closest('.p24-nowblk') ? 'NOW' : el.closest('.p24-arrblk') ? 'ARRIVE' : el.closest('.p24-phase') ? 'PHASE'
      : h.k === 'zone' ? 'ZONES' : h.k === 'evrow' ? 'SUMMARY_FAMILY' : /^(dr|out)/.test(h.k || '') ? 'DR_OUTCOME' : 'OTHER';
    const b = el.querySelector('b');
    const rec = { l21: i, link: { k: h.k || null, ev: h.ev || null, id: h.id != null ? String(h.id) : null }, block,
      shown: b ? b.textContent : '', text: el.textContent, title: el.title || '', sub: [...el.querySelectorAll('.p21-sub')].map(x => x.textContent) };
    if (pp) {
      Object.assign(rec, { bound_kind: 'PASSPORT', estimand: pp.estimand, claim_form: pp.claim_form, parameters: pp.params,
        counts: { yes: pp.yes_count, unknown: pp.unknown_count, no_event: pp.no_event_count, N: pp.N, binary: !!pp.binary },
        passport: { checked: !!pp.checked, violation: pp.violation || null } });
      // the passport's phrase is made by lbl() from its registered form; a row whose title is not that phrase is not judged
      rec.label_ok = pp.phrase ? strip(rec.title).startsWith(strip(pp.phrase)) : null;
    } else if (h.k === 'now' && n) {
      const est = 'EST:N-NEW-' + h.ev, bun = n.contract && (n.contract.bundles || []).find(x => x.estimand === est && par(x).role === 'MAIN');
      const E = n[h.ev] || {}, sp = (E.continuation || {}).support || {};
      Object.assign(rec, { estimand: est, counts: { yes: sp.N_new_yes, no: sp.N_new_no, unknown: sp.N_match_unknown, n: sp.N_match_total, eligible: sp.N_eligible, N: n.base && n.base.N_base } });
      if (bun) Object.assign(rec, { bound_kind: 'BUNDLE', bundle: bun, claim_form: bun.claim_form, parameters: par(bun) });
      else rec.bound_kind = rec.shown && rec.shown !== '—' ? 'UNBOUND' : 'ABSENCE';
      if (h.ev === 'R') { const first = el.querySelector('.t > span'); rec.label_ok = !!first && strip(first.textContent).startsWith(strip(d.lbl(est, 'row_mark', { ev: 'R' }))); }
    } else if (h.k === 'arrive' && r) {
      const lvl = String(h.id), place = (r.places || []).find(p => p.level === lvl) || {};
      const bun = r.contract && (r.contract.bundles || []).find(x => x.estimand === 'EST:K-ARRIVE' && par(x).level === lvl);
      const k = place.counts || {}, stt = (place.state || {}).status;
      Object.assign(rec, { estimand: 'EST:K-ARRIVE', parameters: { level: lvl },
        counts: { yes: k.yes, no: k.no, unknown: k.unknown, n: k.n_match, eligible: k.N_eligible, not_yet: k.N_not_yet, N: k.N_parent } });
      if (bun) Object.assign(rec, { bound_kind: 'BUNDLE', bundle: bun, claim_form: bun.claim_form, parameters: par(bun) });
      else {
        rec.bound_kind = rec.shown && rec.shown !== '—' ? 'UNBOUND' : 'ABSENCE';
        rec.absence_reason = place.withheld ? 'CONTRACT_WITHHELD' : stt === 'RESOLVED' ? 'RESOLVED_TODAY' : place.publication === 'WITHHELD_FEW_SESSIONS' ? 'FEW_SESSIONS'
          : place.publication === 'NO_KNOWN_OUTCOME' ? 'NO_KNOWN_OUTCOME' : null;
      }
      // the words of the accepted block, or of the price ladder of the «Сводка» candidate (13.10): the place reached today by
      // the opening minute of its M5, the count with who they are
      const open5 = t => { const [h, m] = String(t).split(':').map(Number), x = ((h * 60 + m - 5) % 1440 + 1440) % 1440; return String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); };
      const wants = place.withheld ? [d.lbl('FF:K-TARGET', 'withheld')] : stt === 'RESOLVED' ? [d.lbl('FF:K-TARGET', 'RESOLVED', { time: place.state.time }), d.lbl('FF:K-TARGET', 'RESOLVED_rail', { time: open5(place.state.time) })]
        : place.publication === 'WITHHELD_FEW_SESSIONS' ? [d.lbl('FF:FEW-SESSIONS', 'few', { n: k.n_match })]
        : k.n_known ? [d.lbl('EST:K-ARRIVE', k.unknown ? 'sub_unknown' : 'sub', { yes: k.yes, n: k.n_match, unknown: k.unknown }), d.lbl('EST:K-ARRIVE', k.unknown ? 'rail_sub_unknown' : 'rail_sub', { yes: k.yes, n: k.n_match, unknown: k.unknown })] : [d.lbl('FF:K-TARGET', 'none_known')];
      rec.label_ok = rec.sub.some(s => wants.some(w => strip(s) === strip(w)));
    } else {
      rec.bound_kind = /\d\s*%/.test(rec.shown) ? 'UNBOUND' : 'FACT';
    }
    els.push(rec);
  }
  return { fragment: location.hash, viewport: innerWidth + 'x' + innerHeight, collected_at_utc: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    contract: { registry_hash: C.registry_hash, violations: C.violations, unchecked: C.unchecked }, elements: els };
};

async function main() {
  if (!FRAGMENTS.length) throw new Error('no fragment given');
  const B = await startChrome();
  const out = [];
  try {
    for (const f of FRAGMENTS) {
      await B.cdp.send('Page.navigate', { url: 'about:blank' });
      await sleep(200);
      await B.cdp.send('Page.navigate', { url: BASE + f });
      let state = '', t0 = Date.now();
      while (Date.now() - t0 < 120000) {
        try { state = await evaluate(B.cdp, READY); } catch (e) { state = String(e.message || e); }
        if (state === 'ok') break;
        await sleep(500);
      }
      if (state !== 'ok') throw new Error(`${f}: the scene did not complete (${state})`);
      await sleep(1500);                                  // passports made by the last render are verified too
      for (let i = 0; i < 40 && (await evaluate(B.cdp, READY)) !== 'ok'; i++) await sleep(500);
      out.push(await evaluate(B.cdp, COLLECT));
      console.log(`  ok   ${f}: ${out[out.length - 1].elements.length} elements`);
    }
  } finally {
    await B.close();
  }
  const text = JSON.stringify(out);
  if (OUT) fs.writeFileSync(OUT, text); else process.stdout.write(text);
}

main().catch(e => { console.error('  FAIL ' + (e.stack || e)); process.exit(1); });
