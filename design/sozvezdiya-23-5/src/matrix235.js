  // ---------- semantic reset of 27.10 (meaning/22-time-price-constellation-reset.md): one table time × SD ----------
  // The base constellations are ONE joint table per event. For the fixed family F every known session gives one final R
  // and one final X (time, SD) and votes in exactly one 15-minute × 0.1-SD cell; the mass of a cell is n / N of the same
  // F (EST:B-RX-REGION of SC-1.1). Every carrier of the map comes from that table:
  // - at rest the price column shows each SD row's strongest cell (max over time, its window kept) and the time band
  //   each window's strongest cell (max over SD, its row kept): operator 27.10, the eye goes to the strongest local
  //   condensation, not to a row spread thinly over the day (the row sum was the question of screen 24);
  // - a row of one event hovered opens that event's whole row in the band, a window of one event opens its whole column
  //   in the price column; the other event stays at rest, dimmed: one event answers. Both use the scale of the rest, so
  //   an opened profile never outgrows its resting bar and its tallest part equals it;
  // - the haze is the density of all the event's sessions (a Gaussian of 18 px, as screen 24), drawn in many thin levels
  //   of its own peak, so it grows continuously with the mass; the stars are real witnesses, one per M5 × 0.1 SD cell,
  //   as bright as their cell's mass; a thread joins a witness to its nearest witness in a neighbouring M5 × 0.1 SD
  //   cell. None of them makes a number: every number and the haze come from all sessions, whichever witness is drawn.
  //   The drawing is scaled per event (R's strongest place as bright as X's); the numbers stay on the one N;
  // - zone-map-3 is not read: the view's zones are empty, so its capsules, names, shares, list and hills do not exist.
  // Today's path stays a separate layer of fact: the slice limits today's candles, never the history after it.
  const MX = { on: true, pick: 'mean', all: false };
  const mxOn = () => MX.on && !pullbackMode();
  // the brightness of a star or a thread: one curve of the event's density there, relative to the event's own peak
  const mxMass = r => Math.pow(Math.max(0, Math.min(1, r)), 0.7);
  const MX_FLOOR = 0.035;          // below this opacity nothing is drawn (a drawing rule; no number depends on it)
  const mxN = (T, k, b) => { const c = T.at.get(k + '|' + b); return c ? c.n : 0; };
  // one event's table: its cells, each row's and each window's strongest cell, and its witnesses
  function mxTable(F, ev) {
    const D = F.ev[ev], cells = [...D.cells.values()].map(c => ({ k: c.k, b: c.b, n: c.list.length, list: c.list }));
    const at = new Map(), row = new Map(), col = new Map(), edge = k => Math.abs(2 * k + 1);
    for (const c of cells) {
      at.set(c.k + '|' + c.b, c);
      // ties: the earlier window for a row, the row nearer the edge of the IDR for a window (as the 23.10 projections)
      const r = row.get(c.k);
      if (!r || c.n > r.n || (c.n === r.n && c.b < r.b)) row.set(c.k, c);
      const q = col.get(c.b);
      if (!q || c.n > q.n || (c.n === q.n && (edge(c.k) < edge(q.k) || (edge(c.k) === edge(q.k) && c.k < q.k)))) col.set(c.b, c);
    }
    // witnesses: per M5 × 0.1 SD cell one real session, the one nearest that cell's mean price (MX.pick 'last' takes
    // another one, MX.all draws every session: both only for the check that the drawing never moves a number)
    const micro = new Map();
    for (const q of D.pts) { const key = q.k + '|' + Math.floor((q.t - F.f) / 5); if (!micro.has(key)) micro.set(key, []); micro.get(key).push(q); }
    const wit = [];
    for (const qs of micro.values()) {
      const u = qs.reduce((a, q) => a + q.u, 0) / qs.length, mt = Math.floor((qs[0].t - F.f) / 5);
      const ord = qs.slice().sort((a, b) => Math.abs(a.u - u) - Math.abs(b.u - u) || a.i - b.i);
      const same = qs.map(q => q.i);
      if (MX.all) for (const q of qs) wit.push(Object.assign({}, q, { same, mt }));
      else wit.push(Object.assign({}, MX.pick === 'last' ? ord[ord.length - 1] : ord[0], { same, mt }));
    }
    return { cells, at, row, col, wit, max: Math.max(1, ...cells.map(c => c.n)), known: D.known };
  }
  // the view of the family the whole page reads in this mode: the same members and counts, the table, no zones
  function mxView(F) {
    if (!F || !mxOn()) return F;
    if (F._mxv && F._mxv._mxKey === MX.pick + MX.all) return F._mxv;
    const T = { R: mxTable(F, 'R'), X: mxTable(F, 'X') };
    T.max = Math.max(T.R.max, T.X.max);
    // the scale of the price column: R's and X's strongest cells of a row stand side by side in one bar
    T.rowMax = Math.max(1, ...[...new Set([...T.R.row.keys(), ...T.X.row.keys()])].map(k => (T.R.row.get(k) || { n: 0 }).n + (T.X.row.get(k) || { n: 0 }).n));
    F._mxv = Object.assign({}, F, { zones: {}, zcell: { R: new Map(), X: new Map() }, _mx: T, _mxKey: MX.pick + MX.all, _cl: null, _mxv: null, _mxc: null });
    return F._mxv;
  }
  // what is opened by the hover: a window of one event (axis 'price': the price column shows its column) or a row of one
  // event (axis 'time': the band shows its row); else null, the rest
  function mxSection(h, axis) {
    if (!h || !h.ev) return null;
    if (axis === 'price' && h.k === 'tcell' && h.b1 === h.b0 + 1) return { ev: h.ev, b: h.b0 };
    if (axis === 'time' && h.k === 'pcell' && h.k1 === h.k0 + 1) return { ev: h.ev, k: h.k0 };
    return null;
  }
  // the value a column of the band shows for one event: its window's strongest cell, or the opened row's cell
  function mxBandVal(F, ev, b, sec) {
    const T = F._mx[ev];
    if (sec && sec.ev === ev) return { k: sec.k, b, n: mxN(T, sec.k, b), ans: true };
    const c = T.col.get(b);
    return c ? { k: c.k, b, n: c.n, ans: !sec } : null;
  }
  const mxCellPass = (F, ev, v) => evPass(F, ev, 'price_time', [v.k, v.k + 1], [F.f + 15 * v.b, F.f + 15 * v.b + 15], v.n);
  // the density of one event's sessions in screen space, all of them (never the witnesses): every session's point is
  // spread by a Gaussian of 18 px, as the constellations of screen 24 (kde); a separable blur on a 4-px grid, cached
  // until the view moves. Its levels are drawn as soft fills, many and thin, so the haze grows continuously with the mass
  function mxField(pts, W, H) {
    const step = 4, s = 18 / step, r = Math.ceil(3 * s), m = r + 2, nx = Math.ceil(W / step) + 2 * m + 1, ny = Math.ceil(H / step) + 2 * m + 1;
    const a = new Float64Array(nx * ny), b = new Float64Array(nx * ny), ker = [];
    for (let i = -r; i <= r; i++) ker.push(Math.exp(-(i * i) / (2 * s * s)));
    for (const [x, y] of pts) {
      const gx = Math.round(x / step) + m, gy = Math.round(y / step) + m;
      if (gx >= 0 && gx < nx && gy >= 0 && gy < ny) a[gy * nx + gx] += 1;
    }
    for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) { let v = 0; for (let i = -r; i <= r; i++) { const xx = x + i; if (xx >= 0 && xx < nx) v += a[y * nx + xx] * ker[i + r]; } b[y * nx + x] = v; }
    let mx = 0;
    for (let x = 0; x < nx; x++) for (let y = 0; y < ny; y++) { let v = 0; for (let i = -r; i <= r; i++) { const yy = y + i; if (yy >= 0 && yy < ny) v += b[yy * nx + x] * ker[i + r]; } a[y * nx + x] = v; if (v > mx) mx = v; }
    return { step, x0: -m * step, y0: -m * step, nx, ny, gv: a, mx };
  }
  const MX_LEVELS = [0.12, 0.24, 0.36, 0.48, 0.6, 0.72, 0.84];
  // the two densities of each event (still possible today / no longer), cached on the family until the view moves
  function mxFieldOf(full, ctx) {
    const Rch = reachOf(full, ctx), W = V.plot.w, H = V.plot.h, key = [W, H, st.v0, st.v1, V.p0, V.p1, Rch.sl].map(v => Math.round(v * 100)).join('|');
    if (full._mxf && full._mxf.key === key) return full._mxf;
    const fld = { key };
    for (const ev of ['R', 'X']) {
      const live = [], gone = [];
      for (const q of full.ev[ev].pts) (Rch.okCell(ev, q.k, q.b) ? live : gone).push([V.X(q.t + 2.5), V.Y(q.p)]);
      const L = mxField(live, W, H), G = mxField(gone, W, H);
      // the levels and the stars reach full brightness at 3/4 of the peak, so one tight spot does not dim the rest
      fld[ev] = { live: L, gone: G, peak: 0.75 * Math.max(L.mx, G.mx, 1e-9), n: live.length + gone.length, nGone: gone.length };
    }
    return (full._mxf = fld);
  }
  // the event's density at a screen point, as a share of its own peak
  function mxDens(fl, x, y) {
    const G = fl.live, ix = Math.round((x - G.x0) / G.step), iy = Math.round((y - G.y0) / G.step);
    if (ix < 0 || iy < 0 || ix >= G.nx || iy >= G.ny) return 0;
    return (G.gv[iy * G.nx + ix] + fl.gone.gv[iy * G.nx + ix]) / fl.peak;
  }
  // «дымка и нити» from the table: the density of all the event's sessions, split into those today's final event can
  // still take (the event's colour) and those it can no longer take (the spent shade), both on the event's own peak; the
  // threads. Hover dims the event that does not answer
  function mxClouds(c, ctx) {
    const F = ctx.F, full = F._full || F, T = F._mx, h = hv(), Rch = reachOf(full, ctx), fa = cfg.cloudA / 100, ta = cfg.threadA / 100;
    mxFieldOf(full, ctx);
    V.mxHaze = { R: { n: full._mxf.R.n, gone: full._mxf.R.nGone }, X: { n: full._mxf.X.n, gone: full._mxf.X.nGone } };
    for (const ev of ['R', 'X']) {
      const col0 = cfg[ev], spent = stateCol(col0, 'spent'), fl = full._mxf[ev];
      const k = !h ? 1 : (h.k === 'pcell' || h.k === 'tcell') && h.ev ? (h.ev === ev ? 1.1 : 0.45) : h.k === 'pt' ? 0.6 : 0.8;
      for (const [G, col, dim] of [[fl.live, col0, 1], [fl.gone, spent, 0.6 * cfg.spentA / 100]]) {
        if (!G.mx) continue;
        c.save(); c.filter = 'blur(9px)'; c.fillStyle = rgba(col, Math.min(0.12, 0.045 * k * dim * fa));
        // the levels at fractions of the event's own peak (both parts on one peak): a staircase under a blur, so continuous
        for (const f of MX_LEVELS) { if (f * fl.peak > G.mx) break; loopsPath(c, iso(Object.assign({}, G, { mx: fl.peak }), f)); c.fill(); }
        c.restore();
      }
      // the threads: each witness to its nearest witness in the eight neighbouring M5 × 0.1 SD cells, as thin as before;
      // a relation the table has (neighbouring cells), with no tree over the whole map and no length threshold
      const wit = T[ev].wit, by = new Map(wit.map(w => [w.k + '|' + w.mt, w])), done = new Set(), pos = w => [V.X(w.t + 2.5), V.Y(w.p)];
      c.save(); c.lineWidth = 0.5;
      for (const w of wit) {
        const [x, y] = pos(w);
        let best = null, bd = Infinity;
        for (const dk of [-1, 0, 1]) for (const dm of [-1, 0, 1]) {
          if (!dk && !dm) continue;
          const n = by.get((w.k + dk) + '|' + (w.mt + dm));
          if (!n) continue;
          const [nx, ny] = pos(n), d = Math.hypot(nx - x, ny - y);
          if (d < bd) { bd = d; best = n; }
        }
        if (!best) continue;
        const key = [w.k + '|' + w.mt, best.k + '|' + best.mt].sort().join('/');
        if (done.has(key)) continue;
        done.add(key);
        const r = Math.min(mxDens(fl, x, y), mxDens(fl, ...pos(best))), a = Math.min(0.35, 0.16 * ta * mxMass(r));
        if (a < 0.008) continue;
        const [nx, ny] = pos(best);
        c.strokeStyle = rgba(Rch.okCell(ev, w.k, w.b) ? col0 : spent, a * k);
        c.beginPath(); c.moveTo(x, y); c.lineTo(nx, ny); c.stroke();
      }
      c.restore();
    }
  }
  // «Границы хода», the price column from the table. One bar per SD row, R's segment then X's from the same edge, R's
  // percentage left of the bar, X's right of it (as screen 24). At rest a segment is the row's strongest cell of that
  // event, n / N of that one cell; a window of one event hovered: that event's cells of the window, the other event at
  // rest, dimmed. A cell whose window has passed by the clock is green, a cell today's final event can no longer take grey.
  function mxDrawProj(c, ctx) {
    const F = ctx.F, T = F._mx, A_ = V.proj, h = hv(), top0 = 40, bot0 = A_.h - 16, x0 = A_.x + 38, blen = A_.w - 38 - 36;
    c.fillStyle = C.axis; c.fillRect(A_.x, 0, A_.w, A_.h);
    c.fillStyle = C.grid; c.fillRect(A_.x, 0, 1, A_.h);
    V.projBars = []; V.projLbl = []; V.projCols = { X: [A_.x, A_.x + A_.w], R: [A_.x, A_.x + A_.w] }; V.projUnk = null; V.projEdge = null;
    c.save(); c.beginPath(); c.rect(A_.x, 0, A_.w, A_.h); c.clip();
    const sec = mxSection(h, 'price'), Rch = reachOf(F, ctx), sl = Rch.sl, labels = [], out = { X: [0, 0], R: [0, 0] }, outK = { X: [null, null], R: [null, null] };
    const valOf = (ev, k) => { if (sec && sec.ev === ev) { const n = mxN(T[ev], k, sec.b); return n ? { k, b: sec.b, n } : null; } return T[ev].row.get(k) || null; };
    const top1 = {};
    for (const ev of ['R', 'X']) { let best = null; for (const k of [...T[ev].row.keys()]) { const v = valOf(ev, k); if (v && (!best || v.n > best.n)) best = v; } top1[ev] = best && best.k; }
    for (const k of [...new Set([...T.R.row.keys(), ...T.X.row.keys()])]) {
      const [top, bot] = cellY(F, k, k + 1);
      if (bot < top0 || top > bot0) {
        for (const ev of ['R', 'X']) {
          if (sec && sec.ev !== ev) continue;
          const v = sec ? valOf(ev, k) : null, n = sec ? (v ? v.n : 0) : F.ev[ev].P.get(k) || 0, i = bot < top0 ? 0 : 1, r = outK[ev][i];
          if (!n) continue;
          out[ev][i] += n; outK[ev][i] = r ? [Math.min(r[0], k), Math.max(r[1], k)] : [k, k];
        }
        continue;
      }
      let x = x0;
      for (const ev of ['R', 'X']) {
        const v = valOf(ev, k);
        if (!v) continue;
        const ans = !sec || sec.ev === ev, on = !!(h && h.k === 'pcell' && h.ev === ev && k >= h.k0 && k < h.k1);
        const passed = F.f + 15 * (v.b + 1) <= sl, dead = !Rch.okCell(ev, k, v.b), r = Math.pow(v.n / T.max, 0.75);
        let a = 0.22 + 0.78 * r;
        if (!ans) a *= 0.3;
        if (on) a = 1;
        const len = Math.max(2, blen * v.n / T.rowMax), hh = Math.max(1, bot - top - 1);
        if (!ppHeld(F, 'EST:B-RX-REGION-' + ev, { k0: k, k1: k + 1, b0: v.b, b1: v.b + 1 })) {
          c.fillStyle = dead ? rgba(stateCol(cfg[ev], 'spent'), Math.min(1, a * cfg.projA / 90) * cfg.passedA / 100 * 1.8)
            : passed ? rgba(cfg.doneC, Math.min(1, Math.max(0.2, 0.75 * a * cfg.projA / 90 * cfg.passedA / 30)))
            : rgba(cfg[ev], Math.min(1, a * cfg.projA / 90));
          c.fillRect(x, top + 0.5, len, hh);
        }
        V.projBars.push({ ev, k, b: v.b, n: v.n, ans, top, bot, x0: x, x1: x + len });
        if (ans && (on || sec || 100 * v.n / F.N >= 2 || top1[ev] === k)) labels.push({ ev, v, k, y: (top + bot) / 2, xe: x + len, on, dead, passed, r, q: v.n / T.max });
        x += len;
      }
    }
    const used = { R: [], X: [] };
    for (const L of labels.sort((a, b) => (b.on - a.on) || (b.v.n - a.v.n))) {
      const fs = (L.on ? 13 : L.dead ? 8.5 : 8.5 + 5.5 * L.q) * cfg.colSize / 100;
      if (used[L.ev].some(u => Math.abs(u[0] - L.y) < (u[1] + fs) / 2 + 1)) continue;
      used[L.ev].push([L.y, fs]);
      const p = mxCellPass(F, L.ev, L.v), wt = L.on || (!L.dead && L.q > 0.7) ? '700 ' : !L.dead ? '600 ' : '', t = ppTxt(p), tw = pctW(c, t, wt, fs);
      V.projLbl.push({ ev: L.ev, k: L.k, b: L.v.b, n: L.v.n, est: p.estimand, yes: p.yes_count, N: p.N, txt: t });
      c.textBaseline = 'middle';
      pctDraw(c, t, L.ev === 'R' ? Math.max(A_.x + 3, x0 - 3 - tw) : Math.min(L.xe + 3, A_.x + A_.w - tw - 6), L.y + 0.5, wt, fs,
        L.on ? '#FFFFFF' : L.dead ? 'rgba(140,146,157,.5)' : L.passed ? rgba(cfg.doneC, 0.75) : rgba(mixW(cfg[L.ev], 0.45 * L.r), 0.5 + 0.5 * L.r));
    }
    c.textBaseline = 'top'; c.font = '700 10.5px ' + FONT;
    c.fillStyle = cfg.R; c.fillText('R откат', A_.x + 5, 3);
    const hx = 'X прод.';
    c.fillStyle = cfg.X; c.fillText(hx, A_.x + A_.w - c.measureText(hx).width - 5, 3);
    // beyond the frame: at rest the whole share beyond the visible prices (B-RX-OUTFRAME); with a window open, that
    // window's cells beyond them (B-RX-REGION)
    const share = (ev, i) => sec ? evPass(F, ev, 'price_time', [outK[ev][i][0], outK[ev][i][1] + 1], [F.f + 15 * sec.b, F.f + 15 * sec.b + 15], out[ev][i]) : outPass(F, ev, i, outK[ev][i], out[ev][i]);
    const shares = (i, y, base) => {
      c.font = '10px ' + FONT; c.textBaseline = base;
      c.fillStyle = C.text2; c.fillText(i ? '▼' : '▲', A_.x + A_.w / 2 - 4, y);
      if (out.R[i]) { c.fillStyle = cfg.R; c.fillText(ppTxt(share('R', i)), A_.x + 5, y); }
      if (out.X[i]) { const t = ppTxt(share('X', i)); c.fillStyle = cfg.X; c.fillText(t, A_.x + A_.w - c.measureText(t).width - 5, y); }
    };
    if (out.X[0] + out.R[0]) shares(0, 18, 'top');
    if (out.X[1] + out.R[1]) shares(1, A_.h - 3, 'bottom');
    c.restore();
  }
  // the prices the frame holds with the table: the middle 60 % of each event's sessions today's final event can still
  // take (a rule of the view only; the rest is named by ▲ / ▼ in the price column)
  function mxSpan(F, ctx) {
    const Rch = reachOf(F, ctx);
    let lo = Infinity, hi = -Infinity;
    for (const ev of ['R', 'X']) {
      const ps = F.ev[ev].pts.filter(q => Rch.okCell(ev, q.k, q.b)).map(q => q.p).sort((a, b) => a - b);
      if (ps.length < 5) continue;
      lo = Math.min(lo, ps[Math.floor(0.2 * (ps.length - 1))]); hi = Math.max(hi, ps[Math.ceil(0.8 * (ps.length - 1))]);
    }
    return isFinite(lo) ? [lo, hi] : null;
  }
  // the link of a hovered row: its strongest cell (the same cell its resting number names), a soft column down to the band
  function mxLink(F, ctx, h) {
    const c = F._mx[h.ev].row.get(h.k0);
    if (!c || h.k1 !== h.k0 + 1) return;
    const Rch = reachOf(F, ctx), yc = (V.Y(F.u2p(h.k0 / 10)) + V.Y(F.u2p(h.k1 / 10))) / 2, past = F.f + 15 * (c.b + 1) <= Rch.sl || !Rch.okCell(h.ev, c.k, c.b);
    const target = { event_id: h.ev, cell_mask: [[c.k, c.b]], time_start: F.f + 15 * c.b, time_end: F.f + 15 * (c.b + 1) };
    V.lk = { ev: h.ev, x: V.X(F.f + 15 * c.b + 7.5), y: yc, b: c.b, n: c.n, past, k0: h.k0, k1: h.k1, src: 'pcell', mx: true, marker: targetMarker(F, ctx, h.ev, target) };
  }
  // the inspector's first line for a row or a window: the strongest cell, as one sentence of its passport
  function mxTip(F, h) {
    const ev = h.ev, T = F._mx;
    if (h.k === 'pcell') { const c = ev && T[ev].row.get(h.k0); return c ? '<div class="is">' + sentence(mxCellPass(F, ev, c)) + '</div>' : ''; }
    if (h.k === 'tcell') return (ev ? [ev] : ['X', 'R']).map(e => { const c = T[e].col.get(h.b0); return c ? '<div class="is">' + sentence(mxCellPass(F, e, c)) + '</div>' : ''; }).join('');
    return '';
  }
  pbCloudContext = (prev => function (ctx) {
    const F = ctx.F;
    if (!F || !F._mx) return prev(ctx);
    if (!F._mxc) F._mxc = Object.assign({}, F, { _full: F, ev: { R: Object.assign({}, F.ev.R, { pts: F._mx.R.wit }), X: Object.assign({}, F.ev.X, { pts: F._mx.X.wit }) } });
    return Object.assign({}, ctx, { F: F._mxc });
  })(pbCloudContext);
  // the panel: no zone list; the family's scope and each event's undetermined share stay where they were
  zonesHtml = (prev => function (F, ctx) {
    if (!F || !F._mx) return prev(F, ctx);
    const out = ['<div class="p21-h second">Время × SD' + scopeSwitch() + '</div>'];
    for (const ev of ['X', 'R']) {
      const D = F.ev[ev], tag = '<i style="color:' + cfg[ev] + '">' + ev + '</i>';
      if (D.unknown + D.none) { const u = undPass(F, ev, 'BOTH'); out.push(link({ k: 'evrow', ev }, prow(lbl('EST:B-RX-UNDETERMINED-' + ev, 'row', { ev: tag }), ppTxt(u)), 'dim', u, plainTitle(u))); }
    }
    return out.join('');
  })(zonesHtml);
  // for the checks (tests/matrix235_page.mjs): the switch, the witness rule and the table of any family
  window.__mx235 = { set: o => { Object.assign(MX, o); render(true); }, state: () => Object.assign({}, MX), table: F => ({ R: mxTable(F, 'R'), X: mxTable(F, 'X') }), mass: mxMass, floor: MX_FLOOR };
