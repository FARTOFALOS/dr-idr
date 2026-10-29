  // ---------- semantic reset of 27.10 (meaning/22-time-price-constellation-reset.md): one table time × SD ----------
  // The base numbers of 23.5 come from ONE joint table per event: for the fixed family F every known session gives one
  // R and one final X (time, SD) and votes in exactly one 15-minute × 0.1-SD cell (since 29.10 R is the pullback before
  // the session's extreme, the deepest point before the first M5 of the final X: RBX in app.js); the mass of a cell is n / N of
  // the same F (EST:B-RX-REGION of SC-1.1). The drawing of 23.5 stays as it was (operator 27.10: «те же визуализации,
  // просто с новым смыслом»): constellations, their stars, haze and threads, capsules and hills, the colours of the
  // columns. What changes is what the numbers are:
  // - at rest the price column shows each SD row's strongest cell (max over time, its window kept) and the time band
  //   each window's strongest cell (max over SD, its row kept): the strongest local condensation, not the row sum;
  // - a constellation's percentage is its strongest cell, the same kind of number as the rectangle (operator 27.10);
  //   which stars form a constellation is the drawing of zone-map-3, never a number;
  // - a row of one event hovered opens that event's whole row in the band, a window of one event opens its whole column
  //   in the price column; the other event stays at rest, dimmed. One scale: an opened profile never outgrows its rest;
  // - equal maxima are co-maxima: the number is the same, every tied cell is lit, none stands for another.
  const MX = { on: true };
  const mxOn = () => MX.on && !pullbackMode();
  const mxN = (T, k, b) => { const c = T.at.get(k + '|' + b); return c ? c.n : 0; };
  // one event's table: its cells, and each row's and each window's strongest cell (the first of equal ones is only the
  // place its number is anchored; rowTies / colTies name all of them)
  function mxTable(F, ev) {
    const D = F.ev[ev], cells = [...D.cells.values()].map(c => ({ k: c.k, b: c.b, n: c.list.length, list: c.list }));
    const at = new Map(), row = new Map(), col = new Map(), edge = k => Math.abs(2 * k + 1);
    for (const c of cells) {
      at.set(c.k + '|' + c.b, c);
      const r = row.get(c.k);
      if (!r || c.n > r.n || (c.n === r.n && c.b < r.b)) row.set(c.k, c);
      const q = col.get(c.b);
      if (!q || c.n > q.n || (c.n === q.n && (edge(c.k) < edge(q.k) || (edge(c.k) === edge(q.k) && c.k < q.k)))) col.set(c.b, c);
    }
    const rowTies = k => { const r = row.get(k); return r ? cells.filter(c => c.k === k && c.n === r.n).map(c => c.b).sort((a, b) => a - b) : []; };
    const colTies = b => { const q = col.get(b); return q ? cells.filter(c => c.b === b && c.n === q.n).map(c => c.k).sort((a, z) => a - z) : []; };
    return { cells, at, row, col, rowTies, colTies, max: Math.max(1, ...cells.map(c => c.n)), known: D.known };
  }
  // the view of the family the page reads: the same members, counts and zones (the drawing), plus the table
  function mxView(F) {
    if (!F || !mxOn()) return F;
    if (F._mxv) return F._mxv;
    const T = { R: mxTable(F, 'R'), X: mxTable(F, 'X') };
    T.max = Math.max(T.R.max, T.X.max);
    return (F._mxv = Object.assign({}, F, { _mx: T, _cl: null, _mxv: null }));
  }
  // what the hover opens: a window of one event (axis 'price': the price column shows its column) or a row of one event
  // (axis 'time': the band shows its row); else null, the rest
  function mxSection(h, axis) {
    if (!h || !h.ev) return null;
    if (axis === 'price' && h.k === 'tcell' && h.b1 === h.b0 + 1) return { ev: h.ev, b: h.b0 };
    if (axis === 'time' && h.k === 'pcell' && h.k1 === h.k0 + 1) return { ev: h.ev, k: h.k0 };
    return null;
  }
  // the values of the price column per event, row k → { k, b, n, ans }: at rest the row's strongest cell; with a window
  // of this event open, that window's cell; the other event at rest with ans false
  function mxProjVals(F, sec) {
    const out = {};
    for (const ev of ['R', 'X']) {
      const T = F._mx[ev], m = new Map();
      if (sec && sec.ev === ev) { for (const c of T.cells) if (c.b === sec.b) m.set(c.k, { k: c.k, b: c.b, n: c.n, ans: true }); }
      else for (const [k, c] of T.row) m.set(k, { k, b: c.b, n: c.n, ans: !sec });
      out[ev] = m;
    }
    return out;
  }
  // the value a column of the band shows for one event: its window's strongest cell, or the opened row's cell
  function mxBandVal(F, ev, b, sec) {
    const T = F._mx[ev];
    if (sec && sec.ev === ev) return { k: sec.k, b, n: mxN(T, sec.k, b), ans: true };
    const c = T.col.get(b);
    return c ? { k: c.k, b, n: c.n, ans: !sec } : null;
  }
  const mxCellPass = (F, ev, v) => evPass(F, ev, 'price_time', [v.k, v.k + 1], [F.f + 15 * v.b, F.f + 15 * v.b + 15], v.n);
  // a constellation's number: its strongest cell among the cells of its drawing (n / N of that one cell)
  function mxZoneCell(F, ev, z) {
    const T = F._mx[ev];
    let best = null;
    for (const [k, b] of z.cell_mask) { const n = mxN(T, k, b); if (n && (!best || n > best.n || (n === best.n && (b < best.b || (b === best.b && k < best.k))))) best = { k, b, n }; }
    return best;
  }
  // the link of a hovered row: its strongest cell (the cell its resting number names) and every co-maximum of the row
  function mxLink(F, ctx, h) {
    const T = F._mx[h.ev], c = T.row.get(h.k0);
    if (!c || h.k1 !== h.k0 + 1) return;
    const Rch = reachOf(F, ctx), yc = (V.Y(F.u2p(h.k0 / 10)) + V.Y(F.u2p(h.k1 / 10))) / 2, past = F.f + 15 * (c.b + 1) <= Rch.sl || !Rch.okCell(h.ev, c.k, c.b);
    const target = { event_id: h.ev, cell_mask: [[c.k, c.b]], time_start: F.f + 15 * c.b, time_end: F.f + 15 * (c.b + 1) };
    V.lk = { ev: h.ev, x: V.X(F.f + 15 * c.b + 7.5), y: yc, b: c.b, n: c.n, past, k0: h.k0, k1: h.k1, src: 'pcell', mx: true, ties: T.rowTies(h.k0), marker: targetMarker(F, ctx, h.ev, target) };
  }
  // the inspector's first line for a row or a window: the strongest cell (every co-maximum), one sentence of its passport
  function mxTip(F, h) {
    const T = F._mx, line = (ev, k, b, n) => '<div class="is">' + sentence(mxCellPass(F, ev, { k, b, n })) + '</div>';
    if (h.k === 'pcell') { const ev = h.ev, c = ev && T[ev].row.get(h.k0); return c ? T[ev].rowTies(h.k0).map(b => line(ev, h.k0, b, c.n)).join('') : ''; }
    if (h.k === 'tcell') return (h.ev ? [h.ev] : ['X', 'R']).map(e => { const c = T[e].col.get(h.b0); return c ? T[e].colTies(h.b0).map(k => line(e, k, h.b0, c.n)).join('') : ''; }).join('');
    return '';
  }
  // for the checks (tests/matrix235_page.mjs): the switch and the table of any family
  window.__mx235 = { set: o => { Object.assign(MX, o); render(true); }, state: () => Object.assign({}, MX), table: F => ({ R: mxTable(F, 'R'), X: mxTable(F, 'X') }), zoneCell: mxZoneCell };
