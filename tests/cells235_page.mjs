// 23.5 · the layer «Клетки» (operator 30.10, his reviewer's semantic baseline; design/sozvezdiya-23-5/src/matrix235.js):
// the chart shows the family's joint table time × SD itself, no zone. What this proves on real families (a running 23.5
// server with --integration):
//   1. with «#cells=1» the view reads no zone (R and X zone lists empty) and the contract finds nothing to object to;
//   2. every drawn rectangle is a cell of the table that holds sessions (an empty cell is never painted), and every cell
//      of the table whose rectangle lies on the chart is drawn, once, exactly over its 15 minutes and its 0.1 SD;
//   3. a cell under the pointer names its time and price and each event's own passport (n / N of the same F, the
//      registered region estimand, its count = the table's), checked by the server's reference;
//   4. the layer off: the zones of the family come back as they were;
//   5. no page exceptions.
// node tests/cells235_page.mjs [http://127.0.0.1:8735]
import { startChrome, evaluate } from './trace_page.mjs';
const base = process.argv[2] || 'http://127.0.0.1:8735', b = await startChrome(), errors = [];
let n = 0;
const pause = ms => new Promise(r => setTimeout(r, ms));
const ck = (ok, name) => { if (!ok) throw Error(name); n++; console.log('PASS ' + name); };
b.cdp.on('Runtime.exceptionThrown', e => errors.push(e.exceptionDetails.exception?.description || e.exceptionDetails.text));
const scenes = [['NQ', 'RDR', '2025-12-17', '11:10'], ['ES', 'RDR', '2025-12-18', '11:30'], ['YM', 'ODR', '2025-10-20', '04:30'], ['YM', 'RDR', '2025-12-18', '11:00']];
async function ready() {
  for (let i = 0; i < 400; i++) {
    const s = await evaluate(b.cdp, () => { const d = window.__d24, c = d?.cur(); return { ready: !!(c?.F?.N && c.F._mx && d.V?.plot && !d.contract().unchecked) }; });
    if (s.ready) return;
    await pause(150);
  }
  throw Error('23.5 did not settle');
}
try {
  await b.cdp.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const [inst, sess, date, at] of scenes) {
    const tag = `${inst} ${sess} ${date} ${at}`;
    await b.cdp.send('Page.navigate', { url: 'about:blank' });
    await b.cdp.send('Page.navigate', { url: `${base}/23-5/#date=${date}&inst=${inst}&session=${sess}&at=${at}&cells=1` });
    await ready();
    const s = await evaluate(b.cdp, () => {
      const d = window.__d24, m = window.__mx235, F = d.cur().F, V = d.V, T = F._mx;
      d.st.hover = null; d.st.pin = null; d.render(true);
      const drawn = d.V.mxCells.map(q => q.k + '|' + q.b), on = (k, bb) => {
        const x0 = V.X(F.f + 15 * bb), x1 = V.X(F.f + 15 * bb + 15), ya = V.Y(F.u2p(k / 10)), yb = V.Y(F.u2p((k + 1) / 10));
        return !(x1 < 0 || x0 > V.plot.x + V.plot.w || Math.max(ya, yb) < 0 || Math.min(ya, yb) > V.plot.y + V.plot.h);
      };
      const table = [...new Set([...T.R.at.keys(), ...T.X.at.keys()])], held = new Set(table);
      const visible = table.filter(key => { const [k, bb] = key.split('|').map(Number); return on(k, bb); });
      const exact = d.V.mxCells.every(q => Math.abs(q.x0 - V.X(F.f + 15 * q.b)) < 0.01 && Math.abs(q.x1 - V.X(F.f + 15 * q.b + 15)) < 0.01 &&
        Math.abs(Math.min(q.y0, q.y1) - Math.min(V.Y(F.u2p(q.k / 10)), V.Y(F.u2p((q.k + 1) / 10)))) < 0.01);
      // the strongest cell of the two tables, hovered: the inspector and its passports
      const best = [...T.R.cells.map(c => ['R', c]), ...T.X.cells.map(c => ['X', c])].sort((a, z) => z[1].n - a[1].n)[0][1];
      d.st.hover = { k: 'mcell', k0: best.k, b0: best.b }; d.render(false);
      const pp = d.passports(), want = ['R', 'X'].map(ev => { const c = T[ev].at.get(best.k + '|' + best.b); return c ? [ev, c.n] : null; }).filter(Boolean);
      const passOk = want.every(([ev, nn]) => pp.some(p => p.estimand === 'EST:B-RX-REGION-' + ev && p.params.k0 === best.k && p.params.k1 === best.k + 1 && p.params.b0 === best.b && p.params.b1 === best.b + 1 && p.yes_count === nn && p.N === F.N));
      const tipText = (document.getElementById('tip') || document.body).innerText;
      d.st.hover = null; d.render(true);
      return { zones: ['R', 'X'].map(ev => (d.zonesOf(F, ev) || { zones: [] }).zones.length), cellsOn: m.cells(), drawn: drawn.length, unique: new Set(drawn).size,
        allHeld: drawn.every(key => held.has(key)), missing: visible.filter(key => !drawn.includes(key)).length, visible: visible.length, table: table.length, exact,
        passOk, want, best: [best.k, best.b, best.n], N: F.N, hit: !!d.hit, violations: d.contract().violations, unchecked: d.contract().unchecked };
    });
    ck(s.cellsOn && s.zones[0] === 0 && s.zones[1] === 0, `${tag}: the layer «Клетки» reads no zone (R ${s.zones[0]}, X ${s.zones[1]})`);
    ck(s.drawn > 0 && s.drawn === s.unique && s.allHeld, `${tag}: ${s.drawn} rectangles, each once, each a cell of the table that holds sessions (no empty cell painted)`);
    ck(s.missing === 0 && s.drawn === s.visible, `${tag}: every cell of the table on the chart is drawn (${s.visible} of ${s.table}; the rest lie outside the visible prices or times)`);
    ck(s.exact, `${tag}: every rectangle stands exactly over its 15 minutes and its 0.1 SD`);
    ck(s.passOk, `${tag}: the strongest cell (${s.best.join(' · ')} of ${s.N}) hovered names each event's own passport, its count the table's (${s.want.map(w => w.join(' ')).join(', ')})`);
    // what the eye reads at rest: the fill by sessions on one scale for R and X, the key cells tied to the column and the band
    const r = await evaluate(b.cdp, () => {
      const d = window.__d24, F = d.cur().F, T = F._mx, m = window.__mx235;
      d.st.hover = null; d.st.pin = null; d.render(true);
      const parts = d.V.mxCells.flatMap(q => q.parts.map(P => ({ k: q.k, b: q.b, ...P }))), live = parts.filter(P => P.state !== 'IMPOSSIBLE'), full = d.V.mxFull;
      const keys = ['R', 'X'].flatMap(ev => T[ev].key.map(q => ({ ev, k: q.k, b: q.b, n: q.n })));
      const onChart = keys.filter(q => d.V.mxCells.some(c => c.k === q.k && c.b === q.b));
      return { full, fullOk: full === Math.max(4, Math.ceil(0.035 * F.N)), oneScale: live.every(P => Math.abs(P.alpha - m.alpha(P.n, full)) < 1e-9), order: live.every(a => live.every(z => a.n < z.n || a.alpha >= z.alpha)),
        single: parts.filter(P => P.n === 1).every(P => P.alpha < 0.05), singles: parts.filter(P => P.n === 1).length, strong: live.filter(P => P.n >= full), strongOk: live.filter(P => P.n >= full).every(P => P.alpha >= 0.89),
        keyOk: keys.every(q => q.n >= m.keyMin && T[q.ev].row.get(q.k).n === q.n && T[q.ev].col.get(q.b).n === q.n), keys: keys.length,
        keysDrawn: onChart.every(q => d.V.mxCells.find(c => c.k === q.k && c.b === q.b).parts.some(P => P.ev === q.ev && P.key)),
        linked: onChart.every(q => { const pr = d.V.projBars.find(B => B.ev === q.ev && B.k === q.k), bd = d.V.bandVals.find(B => B.ev === q.ev && B.b === q.b); return (!pr || (pr.n === q.n && T[q.ev].rowTies(q.k).includes(q.b))) && !!bd && bd.n === q.n && T[q.ev].colTies(q.b).includes(q.k); }),      // equal maxima are co-maxima
        passports: onChart.every(q => d.passports().some(p => p.estimand === 'EST:B-RX-REGION-' + q.ev && p.params.k0 === q.k && p.params.b0 === q.b && p.yes_count === q.n)) };
    });
    ck(r.fullOk && r.oneScale && r.order, `${tag}: the fill grows with the sessions on one fixed scale for R and X (full from ${r.full} sessions, 3.5 % of the family)`);
    ck(r.single && r.singles > 0, `${tag}: a single session is barely there (${r.singles} such cells, fill < 0.05)`);
    ck(r.strongOk, `${tag}: every live cell from that share is nearly solid (${r.strong.length} such cells)`);
    ck(r.keys > 0 && r.keyOk && r.keysDrawn, `${tag}: ${r.keys} key cells, each the strongest of its row and of its window with ${3}+ sessions, each drawn as key`);
    ck(r.linked, `${tag}: a key cell is the very cell its rectangles at the price and under the time show (same row, window and sessions)`);
    ck(r.passports, `${tag}: the number on a key cell is its own passport`);
    // a real pointer: a cell opens its row and window; a rectangle of the column or the band lights its row or window of cells
    const moved = async (x, y) => { await b.cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y }); await pause(250); };
    const spot = await evaluate(b.cdp, () => {
      const d = window.__d24, cv = document.querySelector('canvas').getBoundingClientRect(), F = d.cur().F;
      const cands = d.V.mxCells.flatMap(q => q.parts.filter(P => P.key && P.state !== 'IMPOSSIBLE').map(P => ({ q, P }))).sort((a, z) => z.P.n - a.P.n);
      const free = cands.map(({ q, P }) => ({ x: (P.a + P.z) / 2, y: (q.y0 + q.y1) / 2, ev: P.ev, k: q.k, b: q.b, n: P.n })).filter(o => { const h = d.hit(o.x, o.y); return h && h.k === 'mcell' && h.ev === o.ev && h.k0 === o.k && h.b0 === o.b; })[0];
      return free ? Object.assign(free, { X: cv.left + free.x, Y: cv.top + free.y, left: cv.left, top: cv.top }) : null;
    });
    if (spot) {
      await moved(spot.X, spot.Y);
      const a = await evaluate(b.cdp, () => { const d = window.__d24, h = d.st.hover; return { h, column: d.V.projBars.filter(B => B.ev === h.ev && B.ans).map(B => B.b), band: d.V.bandVals.filter(B => B.ev === h.ev && B.ans).map(B => B.k), focus: d.V.mxCells.flatMap(q => q.parts.map(P => [q.k, q.b, P.ev, P.focus])) }; });
      ck(a.h && a.h.k === 'mcell' && a.h.ev === spot.ev && a.h.k0 === spot.k && a.h.b0 === spot.b, `${tag}: the pointer over the key cell ${spot.ev} ${spot.k} × ${spot.b} is that cell`);
      ck(a.column.length > 0 && a.column.every(v => v === spot.b), `${tag}: the column opens that cell's window (${a.column.length} rows)`);
      ck(a.band.length > 0 && a.band.every(v => v === spot.k), `${tag}: the band opens that cell's row (${a.band.length} windows)`);
      ck(a.focus.every(([k, bb, ev, f]) => f === (ev === spot.ev && (k === spot.k || bb === spot.b))), `${tag}: on the chart only that row and window of the event stay lit`);
      const bar = await evaluate(b.cdp, s0 => { const d = window.__d24; d.st.hover = null; d.render(false); const B = d.V.projBars.find(q => q.ev === s0.ev && q.k === s0.k); return B ? { x: (B.x0 + B.x1) / 2, y: (B.top + B.bot) / 2 } : null; }, spot);
      if (bar) {
        await moved(spot.left + bar.x, spot.top + bar.y);
        const p = await evaluate(b.cdp, () => { const d = window.__d24, h = d.st.hover; return { h, focus: d.V.mxCells.flatMap(q => q.parts.map(P => [q.k, P.ev, P.focus])) }; });
        ck(p.h && p.h.k === 'pcell' && p.h.ev === spot.ev && p.h.k0 === spot.k, `${tag}: the pointer on the rectangle at the price is that row of that event`);
        ck(p.focus.every(([k, ev, f]) => f === (ev === spot.ev && k === spot.k)), `${tag}: the rectangle at the price lights exactly its row of cells on the chart`);
      }
      const col = await evaluate(b.cdp, s0 => { const d = window.__d24, q = d.V.bandCols.find(c => c.b === s0.b), F = d.cur().F, up = (s0.ev === 'X') === (F.d0 > 0); return q ? { x: (q.x0 + q.x1) / 2, y: d.V.bandCy + (up ? -5 : 5) } : null; }, spot);
      if (col) {
        await moved(spot.left + col.x, spot.top + col.y);
        const t = await evaluate(b.cdp, () => { const d = window.__d24, h = d.st.hover; return { h, focus: d.V.mxCells.flatMap(q => q.parts.map(P => [q.b, P.ev, P.focus])) }; });
        ck(t.h && t.h.k === 'tcell' && t.h.ev === spot.ev && t.h.b0 === spot.b, `${tag}: the pointer on the rectangle under the time is that window of that event`);
        ck(t.focus.every(([bb, ev, f]) => f === (ev === spot.ev && bb === spot.b)), `${tag}: the rectangle under the time lights exactly its window of cells on the chart`);
      }
      await moved(3, 3);
    }
    await pause(1200);
    const v = await evaluate(b.cdp, () => ({ violations: window.__d24.contract().violations, unchecked: window.__d24.contract().unchecked }));
    ck(!v.violations.length && !v.unchecked, `${tag}: the server's reference checked every passport of the layer, no violation (${v.violations.join('; ') || 'none'})`);
    const off = await evaluate(b.cdp, () => {
      const d = window.__d24, m = window.__mx235;
      m.cells(false);
      const F = d.cur().F, out = { zones: ['R', 'X'].map(ev => (d.zonesOf(F, ev) || { zones: [] }).zones.length),
        server: ['R', 'X'].map(ev => (F.r && F.r.zones && F.r.zones[ev] ? F.r.zones[ev].zones.length : 0)), drawn: (d.V.mxCells || []).length };
      m.cells(true);
      return out;
    });
    ck(off.drawn === 0 && off.zones.join() === off.server.join(), `${tag}: the layer off: no rectangle, the server's zones of the family as they were (R ${off.zones[0]}, X ${off.zones[1]})`);
  }
  ck(!errors.length, 'no page exceptions');
  console.log('ALL GOOD · ' + n + ' checks');
} catch (e) {
  console.log('FAIL ' + e.message); if (errors.length) console.log(errors.join('\n')); process.exitCode = 1;
} finally { await b.close?.(); }
