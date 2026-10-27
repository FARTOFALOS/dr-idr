// 23.5 after the semantic reset of 27.10 (meaning/22-time-price-constellation-reset.md, docs/DR-LAB-23-5-MATRIX.md):
// the base map is one table time × SD of the family's final R / X; zone-map-3 is not read. What this proves on real
// families (a running 23.5 server with --integration) and on built fixtures:
//   1. the table = the server's joint cells, and its cells add up to the known final R / X (N − undetermined);
//   2. the price column at rest = each row's strongest cell (its window kept), the band at rest = each window's
//      strongest cell (its row kept); every number is that cell's own passport, checked by the server's reference;
//   3. a row of one event hovered = exactly that row of the table in the band, a window of one event = exactly that
//      column in the price column; the other event stays at rest; an opened profile never outgrows its resting bar;
//   4. the drawn witnesses (one per M5 × 0.1 SD, another pick, all sessions) never change a number, a passport or the panel;
//   5. the slice moves today's facts only: the table, its numbers and the haze's sessions after the slice stay;
//   6. without the server's zones in the packet every number, passport and the panel are the same;
//   7. fixtures: a spread row against a peaked row, all cells single, 1000 sessions in one M5 cell, the order of points.
// node tests/matrix235_page.mjs [http://127.0.0.1:8735]
import fs from 'node:fs';
import { startChrome, evaluate } from './trace_page.mjs';
const base = process.argv[2] || 'http://127.0.0.1:8735', b = await startChrome(), errors = [], out = 'lab/.runtime/matrix235-page';
fs.mkdirSync(out, { recursive: true });
let n = 0;
const pause = ms => new Promise(r => setTimeout(r, ms));
const ck = (ok, name) => { if (!ok) throw Error(name); n++; console.log('PASS ' + name); };
b.cdp.on('Runtime.exceptionThrown', e => errors.push(e.exceptionDetails.exception?.description || e.exceptionDetails.text));
const scenes = [['NQ', 'RDR', '2025-12-17', '11:10'], ['ES', 'RDR', '2025-11-12', '11:00'], ['YM', 'ODR', '2025-10-20', '04:30'], ['YM', 'RDR', '2025-12-18', '11:00']];
async function ready() {
  for (let i = 0; i < 400; i++) {
    const s = await evaluate(b.cdp, () => { const d = window.__d24, c = d?.cur(); return { ready: !!(c?.F?.N && c.F._mx && d.V?.plot && !d.contract().unchecked) }; });
    if (s.ready) return;
    await pause(150);
  }
  throw Error('23.5 did not settle');
}
// everything a number of the map is made of, at rest: the column, the band, their passports, the panel
const SIG = () => {
  const d = window.__d24, V = d.V, pp = d.passports();
  d.st.hover = null; d.st.pin = null; d.render(true);
  const pass = (ev, k, b) => { const p = pp.find(p => p.estimand === 'EST:B-RX-REGION-' + ev && p.params.k0 === k && p.params.k1 === k + 1 && p.params.b0 === b && p.params.b1 === b + 1); return p ? [p.yes_count, p.N, p.pct] : null; };
  return JSON.stringify({ bars: d.V.projBars.map(q => [q.ev, q.k, q.b, q.n, pass(q.ev, q.k, q.b)]), band: d.V.bandVals.map(q => [q.ev, q.b, q.k, q.n, pass(q.ev, q.k, q.b)]),
    panel: document.getElementById('panel').innerText });
};
try {
  await b.cdp.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const [inst, sess, date, at] of scenes) {
    const tag = `${inst} ${sess} ${date} ${at}`;
    await b.cdp.send('Page.navigate', { url: 'about:blank' });
    await b.cdp.send('Page.navigate', { url: `${base}/23-5/#date=${date}&inst=${inst}&session=${sess}&at=${at}` });
    await ready();
    const s = await evaluate(b.cdp, async SIGsrc => {
      const SIG = eval('(' + SIGsrc + ')');
      const d = window.__d24, c = d.cur(), F = c.F, T = F._mx;
      const q = new URLSearchParams({ instrument: d.A.inst, session: c.s.k, at: Math.floor(d.st.rp / 5) * 5, view: 'conf', scope: d.st.scope, trials: '', date: d.A.date });
      const api = (await (await fetch('/api/integration/scene?' + q)).json()).family, r = {};
      for (const ev of ['R', 'X']) {
        const cells = api.counts[ev].cells, sum = cells.reduce((a, x) => a + x[2], 0), at_ = new Map(cells.map(x => [x[0] + '|' + x[1], x[2]]));
        const page = T[ev].cells.map(x => [x.k, x.b, x.n].join(',')).sort().join(';'), srv = cells.map(x => x.join(',')).sort().join(';');
        // the resting projections recomputed here from the server's cells
        const rowPk = new Map(), colPk = new Map(), edge = k => Math.abs(2 * k + 1);
        for (const [k, bb, nn] of cells) {
          const a = rowPk.get(k); if (!a || nn > a[2] || (nn === a[2] && bb < a[1])) rowPk.set(k, [k, bb, nn]);
          const o = colPk.get(bb); if (!o || nn > o[2] || (nn === o[2] && (edge(k) < edge(o[0]) || (edge(k) === edge(o[0]) && k < o[0])))) colPk.set(bb, [k, bb, nn]);
        }
        d.st.hover = null; d.st.pin = null; d.render(true);
        const bars = d.V.projBars.filter(x => x.ev === ev), band = d.V.bandVals.filter(x => x.ev === ev);
        const restCol = bars.every(x => { const p = rowPk.get(x.k); return p && p[1] === x.b && p[2] === x.n && x.ans; });
        const restBand = band.length > 0 && band.every(x => { const p = colPk.get(x.b); return p && p[0] === x.k && p[2] === x.n && x.ans; }) && band.length === [...colPk.keys()].filter(bb => bb >= 0 && bb < F.nb).length;
        const lbls = d.V.projLbl.filter(x => x.ev === ev), pass = lbls.length > 0 && lbls.every(x => x.est === 'EST:B-RX-REGION-' + ev && x.yes === x.n && x.N === F.N && bars.some(y => y.k === x.k && y.b === x.b && y.n === x.n));
        // a row of this event opened: the band shows that row, the other event at rest
        const topRow = [...rowPk.values()].sort((a, b) => b[2] - a[2] || a[0] - b[0])[0], k0 = topRow[0];
        d.st.hover = { k: 'pcell', ev, k0, k1: k0 + 1, src: 'proj' }; d.render(true);
        const row = cells.filter(x => x[0] === k0).map(x => x[1] + ':' + x[2]).sort().join(','), shown = d.V.bandVals.filter(x => x.ev === ev).map(x => x.b + ':' + x.n).sort().join(',');
        const otherRest = d.V.bandVals.filter(x => x.ev !== ev).every(x => !x.ans && colPk && x.n > 0);
        const rowMax = Math.max(...d.V.bandVals.filter(x => x.ev === ev).map(x => x.n)) === topRow[2];
        const tipRow = document.getElementById('insp')?.innerText || '';
        // a window of this event opened: the price column shows that column (the rows in the frame)
        const topCol = [...colPk.values()].sort((a, b) => b[2] - a[2] || a[1] - b[1])[0], b0 = topCol[1];
        d.st.hover = { k: 'tcell', ev, b0, b1: b0 + 1, src: 'strip' }; d.render(true);
        const inFrame = new Set(d.V.projBars.map(x => x.k)), colShown = d.V.projBars.filter(x => x.ev === ev).map(x => x.k + ':' + x.n).sort().join(',');
        const col = cells.filter(x => x[1] === b0 && inFrame.has(x[0])).map(x => x[0] + ':' + x[2]).sort().join(',');
        const notOver = d.V.projBars.filter(x => x.ev === ev).every(x => x.n <= rowPk.get(x.k)[2]) && d.V.projBars.filter(x => x.ev !== ev).every(x => !x.ans);
        d.st.hover = null; d.render(true);
        r[ev] = { same: page === srv, sum, known: T[ev].known, und: api.counts[ev].unknown + api.counts[ev].none, restCol, restBand, pass, bars: bars.length,
          row: row === shown, rowMax, otherRest, col: col === colShown, notOver, tipRow: /%/.test(tipRow) };
      }
      const panel = document.getElementById('panel').innerText;
      return { N: F.N, r, zones: JSON.stringify(F.zones), apiZones: (api.zones.R?.zones.length || 0) + (api.zones.X?.zones.length || 0),
        caps: (d.V.caps || []).length, hills: (d.V.hills || []).length, zoneHit: (d.V.zoneHit || []).length, noZoneList: !/Зоны по времени/.test(panel) && /Время × SD/.test(panel),
        sig: SIG(), slice: d.st.rp, snap: F.r.snapshot_id };
    }, SIG.toString());
    for (const ev of ['R', 'X']) {
      const r = s.r[ev];
      ck(r.same, `${tag} ${ev}: the page's table = the server's joint cells`);
      ck(r.sum === r.known && r.sum + r.und === s.N, `${tag} ${ev}: the cells add up to the known final ${ev} (${r.sum} + ${r.und} undetermined = N ${s.N})`);
      ck(r.restCol && r.bars > 0, `${tag} ${ev}: the price column at rest = each row's strongest cell, its window kept (${r.bars} rows)`);
      ck(r.restBand, `${tag} ${ev}: the band at rest = each window's strongest cell, its row kept`);
      ck(r.pass, `${tag} ${ev}: every number at rest is its cell's own passport (B-RX-REGION, n of N) and names its bar`);
      ck(r.row && r.rowMax, `${tag} ${ev}: a row opened = exactly that row of the table in the band, its tallest = the resting bar`);
      ck(r.otherRest, `${tag} ${ev}: with a row of ${ev} open the other event stays at rest`);
      ck(r.col && r.notOver, `${tag} ${ev}: a window opened = exactly that column in the price column, never above a resting bar; the other event at rest`);
      ck(r.tipRow, `${tag} ${ev}: the inspector of a row names its strongest cell`);
    }
    ck(s.zones === '{}' && s.apiZones >= 0 && !s.caps && !s.hills && !s.zoneHit && s.noZoneList, `${tag}: zone-map-3 is not read (server still publishes ${s.apiZones} zones): no capsules, hills, zone names or list`);
    // 4. the witnesses never move a number
    const w = await evaluate(b.cdp, async SIGsrc => {
      const SIG = eval('(' + SIGsrc + ')'), d = window.__d24, m = window.__mx235, s0 = SIG(), n0 = d.V.stars.length;
      m.set({ all: true }); const s1 = SIG(), n1 = d.V.stars.length;
      m.set({ all: false, pick: 'last' }); const s2 = SIG();
      m.set({ all: false, pick: 'mean' }); const s3 = SIG();
      return { same: s0 === s1 && s0 === s2 && s0 === s3, n0, n1 };
    }, SIG.toString());
    ck(w.same && w.n1 >= w.n0, `${tag}: the drawn witnesses (one per M5 × 0.1 SD: ${w.n0} stars; all sessions: ${w.n1}; another pick) change no number, passport or panel`);
    // 5. the slice: today's facts move, the table and the history after the slice stay
    const sl = await evaluate(b.cdp, async (SIGsrc, s0) => {
      const SIG = eval('(' + SIGsrc + ')'), d = window.__d24, F0 = d.cur().F, before = JSON.parse(SIG());
      d.st.rp = Math.min(F0.end - 5, d.st.rp + 60); d.render(true);
      for (let i = 0; i < 100 && (!d.cur().F || d.contract().unchecked); i++) await new Promise(r => setTimeout(r, 100));
      const F = d.cur().F, after = JSON.parse(SIG()), cells = ev => F._mx[ev].cells.map(x => [x.k, x.b, x.n].join(',')).sort().join(';');
      const tableSame = F.r.snapshot_id === s0 && ['R', 'X'].every(ev => cells(ev) === F0._mx[ev].cells.map(x => [x.k, x.b, x.n].join(',')).sort().join(';'));
      // the rows in both frames (the frame follows today's candles) carry the same cells
      const both = (A, B) => A.filter(x => B.some(y => y[0] === x[0] && y[1] === x[1])).map(x => x.slice(0, 4).join(',')).sort().join(';');
      const nums = both(after.bars, before.bars) === both(before.bars, after.bars) && both(after.bars, before.bars).length > 0;
      const later = d.V.bandVals.filter(x => F.f + 15 * x.b >= d.st.rp).length, haze = ['R', 'X'].every(ev => d.V.mxHaze[ev].n === F._mx[ev].known);
      d.st.rp -= 60; d.render(true);
      return { tableSame, nums, later, haze };
    }, SIG.toString(), s.snap);
    ck(sl.tableSame && sl.nums, `${tag}: a later slice keeps the family's table and every resting number`);
    ck(sl.later > 0 && sl.haze, `${tag}: the history after the slice stays drawn (band windows ahead: ${sl.later}; haze from all sessions)`);
    // 6. without the server's zones the map is the same
    const z = await evaluate(b.cdp, async SIGsrc => {
      const SIG = eval('(' + SIGsrc + ')'), d = window.__d24, s0 = SIG(), F0 = d.cur().F;
      const r = [...d.A.fams.values()].find(x => x && x._F && (x._F === F0 || x._F._mxv === F0));
      if (!r) return { found: false };
      const keep = r.zones; r.zones = undefined; r._F = null; d.render(true);
      for (let i = 0; i < 50 && !d.cur().F; i++) await new Promise(q => setTimeout(q, 100));
      const s1 = SIG(), viol = d.contract().violations.length;
      // and the switch is real: the screen of zones shows other numbers
      r.zones = keep; r._F = null; window.__mx235.set({ on: false }); await new Promise(q => setTimeout(q, 200));
      d.st.hover = null; d.render(true); const zbars = d.V.projBars.map(q => q.n).join(','), mbars = JSON.parse(s0).bars.map(q => q[3]).join(',');
      window.__mx235.set({ on: true }); r._F = null; d.render(true);
      return { found: true, same: s0 === s1, viol, differs: zbars !== mbars };
    }, SIG.toString());
    ck(z.found && z.same && !z.viol, `${tag}: with the server's zones removed from the packet every number, passport and the panel are the same`);
    ck(z.differs, `${tag}: (control) the zone screen, switched back on, shows other numbers — the check can see a difference`);
    ck(await evaluate(b.cdp, () => !window.__d24.contract().violations.length), `${tag}: no contract violation (every passport checked by the server's reference)`);
  }
  // 7. fixtures: the table's rules on built families (no market data)
  const fx = await evaluate(b.cdp, () => {
    const m = window.__mx235, mk = list => {      // list: [ev, k, b, minuteInWindow, u]
      const F = { f: 600, ev: {} };
      for (const ev of ['R', 'X']) {
        const cells = new Map(), pts = [];
        list.filter(x => x[0] === ev).forEach(([, k, b, mm, u], i) => {
          const key = k + '|' + b; if (!cells.has(key)) cells.set(key, { k, b, list: [] }); cells.get(key).list.push(i);
          pts.push({ i, ev, k, b, t: 600 + 15 * b + mm, u, p: u, m: { date: '2000-01-' + String(1 + i % 28).padStart(2, '0') } });
        });
        F.ev[ev] = { cells, pts, known: pts.length };
      }
      return F;
    };
    const sig = T => JSON.stringify(['R', 'X'].map(ev => [T[ev].cells.map(c => [c.k, c.b, c.n]).sort(), [...T[ev].row.values()].map(c => [c.k, c.b, c.n]).sort(), [...T[ev].col.values()].map(c => [c.k, c.b, c.n]).sort()]));
    // a: a row spread thinly over eight windows against a row with one strong window
    const spread = [...Array(8)].map((_, b) => ['R', -3, b, 5, -0.25]), peak = [['R', -5, 2, 5, -0.45], ['R', -5, 2, 5, -0.46], ['R', -5, 2, 10, -0.47], ['R', -5, 2, 0, -0.45], ['R', -5, 7, 5, -0.45]];
    const A = m.table(mk([...spread, ...peak]));
    // b: every cell single
    const B = m.table(mk([...Array(30)].map((_, i) => ['X', i % 6, Math.floor(i / 6), 5, (i % 6) / 10 + 0.05])));
    // c: 1000 sessions in one M5 × 0.1 SD cell
    const C = m.table(mk([...Array(1000)].map((_, i) => ['X', 4, 3, 5, 0.42 + i * 1e-5])));
    // d: the order of the points
    const list = [...spread, ...peak, ['X', 1, 2, 5, 0.15], ['X', 1, 2, 10, 0.16], ['X', 3, 5, 0, 0.33]];
    const D1 = m.table(mk(list)), D2 = m.table(mk(list.slice().reverse()));
    return { spread: A.R.row.get(-3).n, peak: A.R.row.get(-5).n, peakB: A.R.row.get(-5).b,
      single: [...B.X.row.values(), ...B.X.col.values()].every(c => c.n === 1) && B.X.max === 1,
      oneCell: C.X.wit.length === 1 && C.X.cells[0].n === 1000 && C.X.wit[0].same.length === 1000, order: sig(D1) === sig(D2) };
  });
  ck(fx.peak === 4 && fx.peakB === 2 && fx.spread === 1, 'fixture: a row with one strong window (4 in one cell) stands above a row spread over eight windows (1 each), though its sum is smaller (5 < 8)');
  ck(fx.single, 'fixture: when every cell holds one session, every resting bar is the same (nothing stands out)');
  ck(fx.oneCell, 'fixture: 1000 sessions in one M5 × 0.1 SD cell are one witness, and the cell holds all 1000');
  ck(fx.order, 'fixture: the order of the points changes no cell, no resting projection');
  const shot = await b.cdp.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out + '/last.png', Buffer.from(shot.data, 'base64'));
  ck(!errors.length, 'no page exceptions');
  console.log('ALL GOOD · ' + n + ' checks');
} catch (e) {
  console.log('FAIL ' + e.message); if (errors.length) console.log(errors.join('\n')); process.exitCode = 1;
} finally { await b.close?.(); }
