// DR Lab 23.5 · the semantic core DR-LAB-TP-1.1 on the page (design/sozvezdiya-23-5/src/tp235.js, operator 03.11.2026).
//
//     node tests/tp235_page.mjs http://127.0.0.1:<port>          (a server of this working copy with --integration)
//
// For a few history scenes: the confirmation family shows T (the sessions whose DR held) and one window's sessions T_W;
// the DR outcome is the whole family's; every number on screen is a passport the server's reference re-derived (no
// violation, none unchecked); the windows partition T's known pullbacks; the places of X are 0.2-SD price bands of the
// window's tops, never in the last 15 minutes, and tell «дошли до» under the mouse; a window under the mouse
// switches the view and a click fixes it; the places of R of every other window are on the chart without the mouse, a
// window under the mouse marks its peak 15 minutes and says when inside it, a place of another window under the mouse
// shows its words and a click puts that window on screen (operator 05.11); '#tp=0' shows the table of 30.10 again.
// Exit code 0 = every check passed.
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
    // X (core 1.4): its places are price bands of the window's tops on the 0.2-SD grid, never in the last 15 minutes
    const xc = r.t.xc, xin = z => z.cells.every(([k, b]) => b < xc.bHi && k >= z.price[0] && k < z.price[1]) && z.price[0] % 2 === 0 && z.price[1] % 2 === 0;
    ck(!!xc && r.t.xzones.every(xin), 'every place of X is a 0.2-SD band of tops, none in the last 15 minutes (' + r.t.xzones.length + ' places, ' + (xc ? xc.bunches.length : 0) + ' bunches of tops)');
    ck(!r.caps.some(q => q.id === 'XBOX'), 'no capsule «вершина» on the band (core 1.4: the median line of the tops is the author\'s time)');
    // a place of X under the mouse tells how many of the window's sessions got as far as its lower edge (EST:B-RX-BAND-X)
    const xl = await evaluate(B.cdp, function () { const z = (window.__d24.V.zoneHit || []).find(q => q.ev === 'X'); return z ? z.box : null; });
    if (xl) {
      await hover(B.cdp, r.cv[0] + xl[0] + xl[2] / 2, r.cv[1] + xl[1] + xl[3] / 2); await sleep(300); await settle(B.cdp);
      const tt = await evaluate(B.cdp, function () { const t = document.getElementById('insp'); return { shown: !!t && window.__d24.st.hover && window.__d24.st.hover.k === 'zone', text: t ? t.innerText : '', c: window.__d24.contract() }; });
      ck(tt.shown && /дошли до [+−-]?\d,\d SD у сессий окна/.test(tt.text) && !tt.c.all.length && !tt.c.unchecked, 'a place of X under the mouse shows «дошли до» its lower edge, verified (' + (tt.c.all[0] || tt.c.unchecked || '') + ')');
      await hover(B.cdp, 200, 200); await sleep(200);
    }
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
    // 05.11: the pullback places of every other window are on the chart without the mouse, quieter, named by their window
    const g = await evaluate(B.cdp, function () { return window.__d24.tp(); });
    const want = g.others.reduce((a, q) => a + q.places, 0);
    ck(g.ghosts.length === want && !g.ghosts.some(q => q.w === g.w), 'the places of R of the other windows are drawn (' + g.ghosts.length + ' of ' + want + '; on screen ' + g.w + ')');
    // each window's peak 15 minutes is the cell of T's clock in it holding most pullbacks
    const peakOk = g.peaks.every(({ W, pk }) => { const inW = g.clock.cells.filter(([b]) => b >= W[0] && b < W[1]); if (!inW.length) return !pk; const mx = Math.max(...inW.map(q => q[1])); return pk && pk.n === mx && pk.b === inW.find(q => q[1] === mx)[0]; });
    ck(peakOk, 'every window has its peak 15 minutes (' + g.peaks.map(q => q.w + ' ' + (q.pk ? q.pk.b : '-')).join(', ') + ')');
    const lateCap = (await evaluate(B.cdp, function () { return (window.__d24.V.tpCaps || []).map(q => ({ id: q.id, box: q.box })); })).find(q => q.id !== g.w);
    if (lateCap) {
      await hover(B.cdp, r.cv[0] + lateCap.box[0] + lateCap.box[2] / 2, r.cv[1] + lateCap.box[1] + lateCap.box[3] / 2); await sleep(300); await settle(B.cdp);
      const t = await evaluate(B.cdp, function () { const d = window.__d24; return { win: d.V.win, text: document.getElementById('insp').innerText, c: d.contract() }; });
      const pk = g.peaks.find(q => q.w === lateCap.id).pk;
      ck(!!pk && !!t.win && !!t.win.peak && t.win.peak[0] === pk.t0 && t.win.peak[1] === pk.t1, 'a window under the mouse marks its peak 15 minutes on the time axis (' + lateCap.id + ' ' + (t.win && t.win.peak) + ')');
      ck(/Чаще всего откат в истории окна — \d\d:\d\d–\d\d:\d\d/.test(t.text) && /медиана окна/.test(t.text) && !t.c.all.length && !t.c.unchecked, 'its inspector says when inside it, verified (' + (t.c.all[0] || t.c.unchecked || '') + ')');
      await hover(B.cdp, 200, 200); await sleep(300);
    }
    const gb = (await evaluate(B.cdp, function () { return window.__d24.tp().ghosts; })).find(q => q.box[2] > 0);
    if (gb) {
      const x = r.cv[0] + gb.box[0] + gb.box[2] / 2, y = r.cv[1] + gb.box[1] + gb.box[3] / 2;
      await hover(B.cdp, x, y); await sleep(300); await settle(B.cdp);
      const t = await evaluate(B.cdp, function () { const d = window.__d24; return { h: d.st.hover, lk: d.V.lk && d.V.lk.src, w: d.tp().w, text: document.getElementById('insp').innerText, c: d.contract() }; });
      ck(t.h && t.h.k === 'tpzone' && t.h.id === gb.w && t.lk === 'zone' && t.w !== gb.w, 'a place of ' + gb.w + ' under the mouse: its hours over its prices, the window on screen stays (' + t.w + ')');
      ck(new RegExp('^' + ({ BEFORE: 'до окна', W1: 'W1', W2: 'W2', LATE: 'позже' })[gb.w] + ' · R\\d').test(t.text) && /Место окна/.test(t.text) && !t.c.all.length && !t.c.unchecked, 'its inspector names the window, verified (' + (t.c.all[0] || t.c.unchecked || '') + ')');
      await click(B.cdp, x, y); await hover(B.cdp, 200, 200); await sleep(300); await settle(B.cdp);
      const t2 = await evaluate(B.cdp, function () { const d = window.__d24; return { tp: d.tp(), pin: d.st.pin, c: d.contract() }; });
      ck(t2.tp.w === gb.w && t2.tp.pin === gb.w && t2.pin && t2.pin.k === 'zone' && t2.pin.i === gb.i && !t2.tp.ghosts.some(q => q.w === gb.w), 'a click puts ' + gb.w + ' on screen with that place pinned');
      ck(!t2.c.all.length && !t2.c.unchecked, 'and it is verified (' + (t2.c.all[0] || t2.c.unchecked || '') + ')');
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
