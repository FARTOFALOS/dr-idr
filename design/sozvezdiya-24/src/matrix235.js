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
  //   which stars form a constellation: since 30.10 the server's table-cells-1, cells of this table with 2+ sessions
  //   (lab/zonemap24.py::table_map, the flag ':tcells' in RBX), the drawing unchanged; never a number;
  // - a row of one event hovered opens that event's whole row in the band, a window of one event opens its whole column
  //   in the price column; the other event stays at rest, dimmed. One scale: an opened profile never outgrows its rest;
  // - equal maxima are co-maxima: the number is the same, every tied cell is lit, none stands for another.
  const MX = { on: true };
  const mxOn = () => MX.on && !pullbackMode();
  const mxN = (T, k, b) => { const c = T.at.get(k + '|' + b); return c ? c.n : 0; };
  const MX_KEY_MIN = 3;                      // the layer «Клетки»: fewer sessions than this are not a place to pick
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
    // the key cells: the strongest of their row and of their window at once, so the rectangle at the price and the rectangle
    // under the time stand for this very cell (computed from the table, never by crossing two separate clusters)
    const key = cells.filter(c => c.n >= MX_KEY_MIN && row.get(c.k).n === c.n && col.get(c.b).n === c.n).sort((a, z) => z.n - a.n || a.b - z.b);
    return { cells, at, row, col, rowTies, colTies, key, keySet: new Set(key.map(c => c.k + '|' + c.b)), max: Math.max(1, ...cells.map(c => c.n)), known: D.known };
  }
  // the view of the family the page reads: the same members, counts and zones (the drawing), plus the table
  function mxView(F) {
    if (!F || !mxOn()) return F;
    const key = mxCellsOn() ? 'cells' : 'zones';
    if (F._mxv && F._mxv._mxKey === key) return F._mxv;
    const T = { R: mxTable(F, 'R'), X: mxTable(F, 'X') };
    T.max = Math.max(T.R.max, T.X.max);
    const V_ = Object.assign({}, F, { _mx: T, _mxKey: key, _cl: null, _mxv: null });
    // the layer «Клетки»: zone-map-3 is not read, the view's zones are empty (its haze, threads, stars, capsules, hills
    // and list do not exist); the table is drawn as it is (drawMxCells)
    if (key === 'cells') {
      V_.zones = {};
      for (const ev of ['R', 'X']) if (F.zones && F.zones[ev]) V_.zones[ev] = Object.assign({}, F.zones[ev], { zones: [] });
      V_.zcell = { R: new Map(), X: new Map() };
    }
    return (F._mxv = V_);
  }
  // what the hover opens: a window of one event (axis 'price': the price column shows its column) or a row of one event
  // (axis 'time': the band shows its row); else null, the rest
  function mxSection(h, axis) {
    if (!h || !h.ev) return null;
    if (axis === 'price' && h.k === 'tcell' && h.b1 === h.b0 + 1) return { ev: h.ev, b: h.b0 };
    if (axis === 'time' && h.k === 'pcell' && h.k1 === h.k0 + 1) return { ev: h.ev, k: h.k0 };
    if (h.k === 'mcell') return axis === 'price' ? { ev: h.ev, b: h.b0 } : { ev: h.ev, k: h.k0 };   // a cell opens its window and its row
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
  // ---------- the layer «Клетки» (operator 30.10): the table itself on the chart, readable at a glance ----------
  // Every 15-minute × 0.1-SD cell where an R or a final X of the family's sessions lies is a rectangle exactly over its time
  // and its price; empty cells stay empty; nothing is smoothed or joined, no zone is read. After the operator's first look
  // («какую мне клетку выбрать, если они одинаковые?»):
  // - the fill follows the cell's share of the family with a strong contrast, one fixed scale for R and X, any day: the same
  //   share always looks the same, a cell with 3.5 % of the family (at least 4 sessions) is nearly solid, a single session
  //   is barely there (a star alone is noise, operator 20.10), so no outlier dims the rest;
  // - a key cell (the strongest of its row and of its window, 3+ sessions) has an outline, its share written in it (the same
  //   number and passport as the rectangles) and dotted threads to the price column and down to the time band; the
  //   rectangles of its row and window stand out there too, as the clusters did with zones;
  // - today's path filters as everywhere: a cell whose time is gone or that today's R / X can no longer take turns grey and
  //   loses its thread, the history under it does not change; the cell holding today's event so far is outlined bright;
  // - a hovered cell opens its row in the band and its window in the column (one event), the rest of the chart dims; a
  //   hovered rectangle of the column or the band lights its row or window of cells the same way.
  // A cell holding both events is split: R on its left half, X on its right. Off by default; «#cells=1» turns it on (the
  // shortcut «DR Lab 23.5 · клетки»).
  function mxCellsOn() { return mxOn() && !!st.L.cells; }
  // the counts are skewed (13 in the first window, 3–6 elsewhere): a logarithmic scale keeps 3 against 6 apart; on a full
  // cell of 7 sessions (N 185): 1 ≈ 0.035, 2 ≈ 0.22, 3 ≈ 0.40, 5 ≈ 0.68, 7 = 0.9, 8+ solid
  const mxFull = N => Math.max(4, Math.ceil(0.035 * N));
  const mxAlpha = (n, full) => Math.min(1, 0.035 + 0.865 * Math.pow(Math.log(n) / Math.log(full), 1.5));
  function mxCellState(Rch, ev, k, b) {
    const q = Rch.known && Rch.cur[ev];
    return q && q.k === k && q.b === b ? 'HOLDS' : Rch.okCell(ev, k, b) ? 'POSSIBLE' : 'IMPOSSIBLE';
  }
  const mxInFocus = (h, ev, k, b) => !h ? true : h.k === 'mcell' ? ev === h.ev && (k === h.k0 || b === h.b0) : h.k === 'pcell' && h.ev ? ev === h.ev && k >= h.k0 && k < h.k1 : h.k === 'tcell' ? (!h.ev || h.ev === ev) && b >= h.b0 && b < h.b1 : true;
  function drawMxCells(c, ctx) {
    const F = ctx.F;
    V.mxCells = [];
    if (!F || !F._mx || !mxCellsOn()) return;
    const T = F._mx, h = hv(), Rch = reachOf(F, ctx), focusing = !!(h && (h.k === 'mcell' || h.k === 'pcell' || h.k === 'tcell')), rect = [], X1 = V.plot.x + V.plot.w, Y1 = V.plot.y + V.plot.h;
    const full = mxFull(F.N);
    for (const key of new Set([...T.R.at.keys(), ...T.X.at.keys()])) {
      const [k, b] = key.split('|').map(Number), r = T.R.at.get(key), x = T.X.at.get(key);
      const x0 = V.X(F.f + 15 * b), x1 = V.X(F.f + 15 * b + 15), ya = V.Y(F.u2p(k / 10)), yb = V.Y(F.u2p((k + 1) / 10));
      const y0 = Math.min(ya, yb), y1 = Math.max(ya, yb);
      if (x1 < 0 || x0 > X1 || y1 < 0 || y0 > Y1) continue;
      const parts = (r && x ? [['R', r, x0, (x0 + x1) / 2], ['X', x, (x0 + x1) / 2, x1]] : [[r ? 'R' : 'X', r || x, x0, x1]]).map(([ev, cell, a, z]) => {
        const state = mxCellState(Rch, ev, k, b), focus = mxInFocus(h, ev, k, b);
        let alpha = mxAlpha(cell.n, full);
        if (state === 'IMPOSSIBLE') alpha *= 0.55;
        if (focusing) alpha = focus ? Math.max(alpha, 0.34) : alpha * 0.3;
        c.fillStyle = rgba(state === 'IMPOSSIBLE' ? stateCol(cfg[ev], 'spent') : cfg[ev], alpha);
        c.fillRect(Math.round(a) + 0.5, Math.round(y0) + 0.5, Math.max(1, Math.round(z - a) - 1), Math.max(1, Math.round(y1 - y0) - 1));
        return { ev, n: cell.n, a, z, alpha, state, key: T[ev].keySet.has(key), focus };
      });
      rect.push({ k, b, x0, x1, y0, y1, parts });
    }
    // the key cells over the fill: threads first, then the outline and the number
    for (const q of rect) for (const P of q.parts) {
      if (!P.key || P.state === 'IMPOSSIBLE' || (focusing && !P.focus)) continue;
      const ym = (q.y0 + q.y1) / 2, xm = (P.a + P.z) / 2;
      c.save(); c.setLineDash([2, 4]); c.lineWidth = 1; c.strokeStyle = rgba(cfg[P.ev], 0.5);
      c.beginPath(); c.moveTo(q.x1, Math.round(ym) + 0.5); c.lineTo(X1, Math.round(ym) + 0.5); c.moveTo(Math.round(xm) + 0.5, q.y1); c.lineTo(Math.round(xm) + 0.5, Y1); c.stroke(); c.restore();
    }
    c.textAlign = 'center'; c.textBaseline = 'middle';
    for (const q of rect) for (const P of q.parts) {
      const on = h && h.k === 'mcell' && h.k0 === q.k && h.b0 === q.b && h.ev === P.ev;
      if (P.key || (P.state === 'HOLDS' && P.n >= MX_KEY_MIN) || on) {
        c.lineWidth = on || P.state === 'HOLDS' ? 2 : 1;
        c.strokeStyle = on ? '#F0F5FF' : P.state === 'IMPOSSIBLE' ? rgba(stateCol(cfg[P.ev], 'spent'), 0.5) : P.state === 'HOLDS' ? mixW(cfg[P.ev], 0.6) : rgba(mixW(cfg[P.ev], 0.35), 0.9);
        c.strokeRect(Math.round(P.a) + 0.5, Math.round(q.y0) + 0.5, Math.max(1, Math.round(P.z - P.a) - 1), Math.max(1, Math.round(q.y1 - q.y0) - 1));
      }
      if (P.key && !(focusing && !P.focus)) {
        const t = ppTxt(mxCellPass(F, P.ev, { k: q.k, b: q.b, n: P.n })).replace('%', ''), fs = Math.min(13, Math.max(9.5, (q.y1 - q.y0) * 0.55));
        c.font = '700 ' + fs + 'px ' + FONT;
        c.fillStyle = P.state === 'IMPOSSIBLE' ? 'rgba(210,214,222,.8)' : P.alpha >= 0.42 ? '#0A0B0F' : mixW(cfg[P.ev], 0.55);
        c.fillText(t, (P.a + P.z) / 2, (q.y0 + q.y1) / 2 + 0.5);
      }
    }
    c.textAlign = 'left';
    V.mxCells = rect; V.mxFull = full;
  }
  // the cell under the pointer when the table holds R or X there (the half under it when both)
  function mxCellHit(F, x, y) {
    if (!F || !F._mx || !mxCellsOn()) return null;
    const b = Math.floor((V.T(x) - F.f) / 15), k = F.cellOfP(V.P(y)), key = k + '|' + b, r = F._mx.R.at.has(key), q = F._mx.X.at.has(key);
    if (!r && !q) return null;
    return { k: 'mcell', ev: r && q ? (x < (V.X(F.f + 15 * b) + V.X(F.f + 15 * b + 15)) / 2 ? 'R' : 'X') : r ? 'R' : 'X', k0: k, b0: b };
  }
  // its inspector: the cell's time and price, each event's sentence of its own passport (n / N of F, B-RX-REGION)
  function mxCellTip(F, h) {
    const t0 = F.f + 15 * h.b0, p0 = F.u2p(h.k0 / 10), p1 = F.u2p((h.k0 + 1) / 10), key = h.k0 + '|' + h.b0;
    const line = ev => { const c = F._mx[ev].at.get(key); return c ? '<div class="is" style="color:' + cfg[ev] + '">' + ev + ' · ' + sentence(mxCellPass(F, ev, { k: h.k0, b: h.b0, n: c.n })) + (F._mx[ev].keySet.has(key) ? ' — сильнейшая и в своей строке SD, и в своём окне' : '') + '</div>' : ''; };
    return '<div class="ih">' + band(h.k0, h.k0 + 1) + ' SD × ' + clk(t0) + '–' + clk(t0 + 15) + '</div><div class="is">' + px(Math.min(p0, p1)) + '–' + px(Math.max(p0, p1)) + '</div>' + line('X') + line('R');
  }
  // the panel with the layer on: the key cells by time, where the zone list stood; the family switch and the undetermined stay
  zonesHtml = (prev => function (F, ctx) {
    if (!F || !F._mx || !mxCellsOn()) return prev(F, ctx);
    const out = ['<div class="p21-h second">Главные клетки по времени' + scopeSwitch() + '</div>'], sl = sliceOf(ctx), Rch = reachOf(F, ctx), rows = [];
    for (const ev of ['R', 'X']) for (const q of F._mx[ev].key) rows.push({ ev, q, s: mxCellState(Rch, ev, q.k, q.b) });
    rows.sort((a, z) => a.q.b - z.q.b || z.q.n - a.q.n);
    if (!rows.length) out.push('<div class="p21-note">Ни одна клетка не выделяется: нет клетки из ' + MX_KEY_MIN + '+ сессий, сильнейшей и в строке, и в окне</div>');
    let sep = false;
    const nowLine = () => '<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>';
    for (const r of rows) {
      const t0 = F.f + 15 * r.q.b, p = mxCellPass(F, r.ev, r.q), top = r.q.n === F._mx[r.ev].max;
      if (!sep && t0 + 15 > sl) { sep = true; out.push(nowLine()); }
      out.push(link({ k: 'mcell', ev: r.ev, k0: r.q.k, b0: r.q.b }, '<span class="t"><span><span class="zt">' + clk(t0) + '–' + clk(t0 + 15) + '</span> <i class="zn" style="color:' + cfg[r.ev] + '">' + r.ev + '</i></span>' +
        '<span class="p21-sub">' + lbl('EST:B-ZONE-' + r.ev, 'sub', { band: band(r.q.k, r.q.k + 1), status: zst(r.s) }) + '</span></span><b class="zp' + (top ? ' big' : '') + '" style="color:' + (r.s === 'IMPOSSIBLE' ? 'rgba(140,146,157,.8)' : cfg[r.ev]) + ';opacity:1">' + ppTxt(p) + '</b>', 'mc zst-' + r.s, p, plainTitle(p)));
    }
    if (!sep) out.push(nowLine());
    for (const ev of ['X', 'R']) {
      const D = F.ev[ev], tag = '<i style="color:' + cfg[ev] + '">' + ev + '</i>';
      if (D.unknown + D.none) { const u = undPass(F, ev, 'BOTH'); out.push(link({ k: 'evrow', ev }, prow(lbl('EST:B-RX-UNDETERMINED-' + ev, 'row', { ev: tag }), ppTxt(u)), 'dim', u, plainTitle(u))); }
    }
    return out.join('');
  })(zonesHtml);
  // for the checks (tests/matrix235_page.mjs): the switch and the table of any family
  window.__mx235 = { set: o => { Object.assign(MX, o); render(true); }, state: () => Object.assign({}, MX), table: F => ({ R: mxTable(F, 'R'), X: mxTable(F, 'X') }), zoneCell: mxZoneCell,
    cells: on => { if (on != null) { st.L.cells = !!on; render(true); } return mxCellsOn(); }, drawnCells: () => (V && V.mxCells || []).map(q => [q.k, q.b]), alpha: mxAlpha, keyMin: MX_KEY_MIN };
