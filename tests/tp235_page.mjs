// DR Lab 23.5 · the semantic core DR-LAB-TP-1.1 on the page (design/sozvezdiya-23-5/src/tp235.js, operator 03.11.2026).
//
//     node tests/tp235_page.mjs http://127.0.0.1:<port>          (a server of this working copy with --integration)
//
// For a few history scenes: the confirmation family shows T (the sessions whose DR held) and one window's sessions T_W;
// the DR outcome is the whole family's; every number on screen is a passport the server's reference re-derived (no
// violation, none unchecked); the windows partition T's known pullbacks; the places of X lie in bunches of tops and never
// in the last 15 minutes; a window under the mouse
// switches the view and a click fixes it; '#tp=0' shows the table of 30.10 again. Exit code 0 = every check passed.
import { startChrome, evaluate } from './trace_page.mjs';

const base = (process.argv[2] || 'http://127.0.0.1:8735').replace(/\/$/, '');
const SCENES = [['NQ', 'RDR', '2025-12-17', '11:40'], ['ES', 'RDR', '2025-12-18', '12:30'], ['NQ', 'ODR', '2025-12-19', '06:00'], ['YM', 'ADR', '2025-12-16', '00:30']];
const sleep = ms => new Promise(r => setTimeout(r, ms));
let bad = 0;
const ck = (ok, what) => { if (!ok) bad++; console.log((ok ? '  ok   ' : '  FAIL ') + what); };

async function settle(cdp, want) {
  for (let i = 0; i < 120; i++) {
    const s = await evaluate(cdp, function () {
      const d = window.__d24;
      if (!d || !d.V || !d.V.ctx || !d.A.day || d.A.day.status !== 'ok') return 'page';
      const t = d.tp(), c = d.contract(), s = d.V.ctx.s;
      if (['before', 'forming', 'waiting', 'noconf'].includes(s.status)) return 'noconf';
      if (!s.conf) return 'page';
      if (t.on && !t.w) return 'tp';
      if (!d.passports().length) return 'passports';
      d.verify();
      return c.unchecked ? 'unchecked' : 'ok';
    });
    if (s === 'ok' || s === 'noconf' || (want && s === want)) return s;
    await sleep(250);
  }
  return 'timeout';
}
const hover = (cdp, x, y) => cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
const click = async (cdp, x, y) => { await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 }); await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }); };

const B = await startChrome();
try {
  for (const [inst, sess, date, at] of SCENES) {
    console.log(`${inst} ${sess} ${date} ${at}`);
    await B.cdp.send('Page.navigate', { url: `${base}/23-5/#date=${date}&inst=${inst}&session=${sess}&at=${at}` });
    await sleep(800);
    const st = await settle(B.cdp);
    if (st === 'noconf') { console.log('  (no confirmation in this scene: skipped)'); continue; }
    ck(st === 'ok', 'the scene settles with every passport checked (' + st + ')');
    const r = await evaluate(B.cdp, function () {
      const d = window.__d24, t = d.tp(), c = d.contract(), F = d.V.ctx.F, P = F && F._tp;
      const ps = d.passports(), byView = v => ps.filter(p => p.req && p.req.view === v);
      const T = P && P.T, sumW = P ? Object.values(P.clock.windows).filter(Boolean).reduce((s, W) => s + P.clock.cells.filter(([b]) => b >= W[0] && b < W[1]).reduce((a, q) => a + q[1], 0), 0) : null;
      return { t, viol: c.violations, all: c.all, unchecked: c.unchecked, mx: !!(F && F._mx), sumW, known: P ? P.clock.known : null,
        outN: P && P.A ? P.A.N : null, outSum: P && P.A && P.A.out ? Object.values(P.A.out).reduce((a, b) => a + b, 0) : null,
        heldAll: F ? F.M.every(m => m.outcome === 'held') : null, tN: T ? T.N : null, tHeld: P && P.A && P.A.out ? P.A.out.held : null,
        nT: P ? byView(T.req.view).every(p => p.N === T.N) : null, nW: P && P.w ? byView(F.req.view).every(p => p.N === F.N) : null,
        panel: document.getElementById('panel').innerText, caps: (d.V.tpCaps || []).map(q => ({ id: q.id, box: q.box })),
        cv: (r => [r.left, r.top])(document.querySelector('#dr21-root canvas').getBoundingClientRect()) };
    });
    ck(r.t.on && !r.mx, 'the core TP-1.1 is on and the table of 30.10 is off');
    ck(!r.viol.length && !r.all.length, 'no contract violation (' + (r.all[0] || '') + ')');
    ck(r.outN === r.outSum && r.outN > 0, 'the DR outcome is one 100 % of the whole family (N ' + r.outN + ')');
    ck(r.tN === r.tHeld, 'T is exactly the sessions whose DR held (' + r.tN + ' of ' + r.outN + ')');
    ck(r.heldAll, 'every session on screen held its DR');
    ck(r.sumW === r.known, 'the windows partition the known pullbacks of T (' + r.sumW + ' = ' + r.known + ')');
    // X (operator 04.11): its places lie inside a bunch of the window's tops and never in the last 15 minutes of the block
    const xc = r.t.xc, xin = z => z.cells.every(([, b]) => b < xc.bHi) && xc.bunches.some(u => z.cells.every(([, b]) => b >= u.b0 && b < u.b1));
    ck(!!xc && r.t.xzones.every(xin), 'every place of X lies in a bunch of tops, none in the last 15 minutes (' + r.t.xzones.length + ' places, ' + (xc ? xc.bunches.length : 0) + ' bunches)');
    ck(!xc || !xc.box || (xc.box[0] < xc.box[1] && r.t.caps.includes('XBOX')), 'the box «вершина» is drawn from the first bunch of tops to their median');
    ck(r.nT && (r.nW !== false), 'every passport of T counts over |T|, of the window over |T_W|');
    ck(/Время отката · true-сессии/.test(r.panel) && /Места отката/.test(r.panel), 'the panel shows the clock of T and the places of the window');
    ck(r.t.lines.includes('R:median'), 'the median line of T is drawn');
    // a window under the mouse switches the view; a click fixes it
    const other = r.caps.find(q => q.id !== r.t.w && q.id !== 'BEFORE');
    if (other) {
      const x = r.cv[0] + other.box[0] + other.box[2] / 2, y = r.cv[1] + other.box[1] + other.box[3] / 2;   // canvas → page
      await hover(B.cdp, x, y); await sleep(300); await settle(B.cdp);
      const w1 = await evaluate(B.cdp, function () { return window.__d24.tp().w; });
      ck(w1 === other.id, 'hovering ' + other.id + ' shows its sessions (' + w1 + ')');
      await click(B.cdp, x, y); await hover(B.cdp, 200, 200); await sleep(300); await settle(B.cdp);
      const w2 = await evaluate(B.cdp, function () { return window.__d24.tp(); });
      ck(w2.w === other.id && w2.pin === other.id, 'a click fixes ' + other.id + ' after the mouse leaves');
      const c2 = await evaluate(B.cdp, function () { return window.__d24.contract(); });
      ck(!c2.all.length && !c2.unchecked, 'the fixed window is verified too (' + (c2.all[0] || c2.unchecked) + ')');
    }
  }
  // the previous meaning stays reachable
  await B.cdp.send('Page.navigate', { url: `${base}/23-5/#date=2025-12-17&inst=NQ&session=RDR&at=11:40&tp=0` });
  await sleep(800);
  await settle(B.cdp);
  const o = await evaluate(B.cdp, function () { const d = window.__d24; return { t: d.tp(), mx: !!(d.V.ctx.F && d.V.ctx.F._mx), all: d.contract().all }; });
  ck(!o.t.on && o.mx && !o.all.length, "'#tp=0' shows the table of 30.10 without a violation");
} finally { await B.close(); }
console.log(bad ? bad + ' check(s) failed' : 'all checks passed');
process.exit(bad ? 1 : 0);
