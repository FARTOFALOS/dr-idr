  // ================= «Откаты до обновления» · the candidate DR-LAB-PB-0.1 (operator 2026-10-21) =================
  // meaning/lens/2026-10-21-otkaty-do-obnovleniya/: the construction, its review, the definition and the answer. A view of
  // its own behind the trial «pullbacks» (⚙ → Испытание кандидатов): the accepted R / X map, its numbers and words stay.
  // One source-bound publication (GET /api/integration/pullbacks, lab/pullbacks24.py) for the family on screen (the same
  // F, N, frame): every member's episodes H -> L -> B with its witness bars, the merged bottoms, the constellations of
  // every scale and today's facts. Before anything is drawn the page checks the release hash, the scene and family, every
  // witness against the accepted family path, every star against its own bars (its vertex, the first update, nothing
  // deeper between, after the activation) and every constellation's members and share against its bundle; a failed check
  // withdraws the number and the drawing together. Stepping by M5 changes only today's facts: the map is the family's
  // history, fixed at its activation, and a pinned historical session stays pinned.
  const PBC = '#C3A6F2', PB_SCALES = [1, 2, 3, 6], PB_KEY = 'drlab.d24.pbscale';
  const PB = { key: null, packet: null, pending: null, error: null, seq: 0, scale: 1, cl: null, verified: 0 };
  try { const k = +localStorage.getItem(PB_KEY); if (PB_SCALES.includes(k)) PB.scale = k; } catch (e) { /* 1 */ }
  {
    const q = new URLSearchParams(location.hash.slice(1)), k = +q.get('pbscale');
    if (PB_SCALES.includes(k)) PB.scale = k;
    if (ICFG.enabled && q.get('mode') === 'pullbacks') { TRIAL.pullbacks = true; st.mode = 'pullbacks'; }
  }
  const pullbackMode = () => ICFG.enabled && TRIAL.pullbacks && st.mode === 'pullbacks';
  function pbRequest(ctx) {
    if (!ctx.F || !ctx.F.N || !ctx.s.conf) return null;
    const cut = sliceOf(ctx), view = st.view === 'conf' ? 'conf' : 'auto';
    return { cut, view, key: [IS.epoch, A.inst, ctx.D.iso, ctx.s.k, cut, view, st.scope, ctx.F.r.snapshot_id].join('|') };
  }
  function pbPacket(ctx) { const q = pbRequest(ctx); return q && PB.key === q.key ? PB.packet : null; }
  function requestPullbacks(ctx) {
    if (!pullbackMode()) return;
    const q = pbRequest(ctx);
    if (!q || (q.key === PB.key && (PB.packet || PB.error)) || PB.pending === q.key) return;
    const token = ++PB.seq, F = ctx.F;
    PB.key = q.key; PB.packet = null; PB.error = null; PB.pending = q.key; PB.cl = null;
    const args = new URLSearchParams({ instrument: A.inst, session: ctx.s.k, at: q.cut, view: q.view, scope: st.scope });
    if (A.src === 'hist') args.set('date', A.date);
    fetch('/api/integration/pullbacks?' + args).then(async res => {
      const r = await res.json();
      if (!res.ok) throw Error(r.message || r.error || 'Сервер не ответил');
      if (token !== PB.seq) return;
      if (r.status !== 'OK') throw Error(r.message || r.status);
      await pbVerify(r, q, ctx, F);
      if (token !== PB.seq) return;
      PB.packet = r; PB.verified++;
    }).catch(e => { if (token === PB.seq) { PB.error = e.message; PB.packet = null; } })
      .finally(() => { if (token === PB.seq) PB.pending = null; redraw(true); });
  }
  function pbBundle(r, est, pred) {
    const f = REVIEW && REVIEW.forms[est], b = (r.contract.bundles || []).find(x => x.estimand === est && pred(parOf(x)));
    if (!b || !f || b.claim_form !== f.id || b.claim.claim_class !== f.claim_class || !(b.admissible_claims || []).includes(f.claim_class)) return null;
    return b;
  }
  // a star and its own bars: the vertex (equal highs, kt neighbours on each side strictly lower), no update before B, the
  // update at B, nothing deeper between H and B, the bottom after the activation
  function pbWitness(pt, w, E) {
    const bars = w.bars, bl = bars[pt.i];
    if (!bl || bl[2] !== pt.v || pt.i <= w.act_i) return 'дно не на своей M5';
    for (const id of pt.episodes) {
      const e = E.get(id);
      if (!e || e.case !== pt.case || e.status !== 'KNOWN' || e.jl !== pt.i || e.L !== pt.v) return 'эпизод точки';
      for (let j = e.a; j <= e.b; j++) if (!bars[j] || bars[j][1] !== e.h) return 'вершина';
      for (let k = 1; k <= e.kt; k++) { const l = bars[e.a - k], r = bars[e.b + k]; if (!l || !r || l[1] >= e.h || r[1] >= e.h) return 'соседи вершины'; }
      for (let j = e.b + 1; j < e.jb; j++) if (!bars[j] || bars[j][1] > e.h) return 'обновление раньше B';
      if (!bars[e.jb] || bars[e.jb][1] <= e.h) return 'нет обновления на B';
      for (let j = e.a + 1; j < e.jb; j++) if (bars[j][2] < pt.v) return 'дно глубже';
      if (pt.i < e.a || pt.i > e.jb) return 'дно вне отрезка H–B';
    }
    return null;
  }
  function pbZoneCheck(r, s) {
    const p = r.proof, zm = p.maps[String(s)], N = p.context.N, pts = p.points.filter(q => q.kt >= s);
    for (const z of zm.zones) {
      const cells = new Set(z.cell_mask.map(c => c[0] + '|' + c[1]));
      const mem = [...new Set(pts.filter(q => cells.has(q.k + '|' + q.b)).map(q => q.case))].sort();
      if (JSON.stringify(mem) !== JSON.stringify(z.members) || z.n_known !== mem.length) return 'состав ' + z.label;
      const b = pbBundle(r, 'EST:PB-ZONE', x => x.zone_id === z.zone_id && x.scale === s);
      const pt = b && b.estimates.find(e => e.value_kind === 'POINT'), bd = b && b.estimates.find(e => e.value_kind === 'BOUNDS');
      if (!pt || pt.numerator !== z.n_known || pt.denominator !== N || (z.n_possible ? !bd || Math.abs(bd.upper - (z.n_known + z.n_possible) / N) > 1e-12 : !!bd)) return 'доля ' + z.label;
    }
    const sb = pbBundle(r, 'EST:PB-SESSIONS', x => x.scale === s), cats = sb && sb.estimates[0].categories;
    if (!cats || cats.reduce((t, c) => t + c.count, 0) !== N || cats.some(c => c.count !== zm.sessions[c.category])) return 'категории сессий';
    return null;
  }
  async function pbVerify(r, q, ctx, F) {
    const p = r.proof, c = p.context;
    if (!r.contract || r.contract.status !== 'CONFORMANT' || reviewFault(r)) throw Error(r.message || 'Нет проверенного выпуска');
    if (c.instrument !== A.inst || c.date !== ctx.D.iso || c.session !== ctx.s.k || c.cut !== q.cut || c.scope !== st.scope) throw Error('Ответ другого среза');
    if (!F || c.family_id !== F.r.family_id || c.snapshot_id !== F.r.snapshot_id || c.view !== F.view || c.N !== F.N) throw Error('Ответ другой семьи или рамки');
    if (c.base_registry_hash !== SC11.registry_hash || c.registry_hash !== REVIEW.registry_hash) throw Error('Другой реестр контракта');
    if (p.definition.version !== 'DR-LAB-PB-0.1' || JSON.stringify(p.definition.scales) !== JSON.stringify(PB_SCALES)) throw Error('Другая версия определения');
    if (await cHash(p) !== r.release_id) throw Error('Данные выпуска подменены');
    if (p.sessions.length !== F.M.length) throw Error('Свидетели — не члены семьи');
    p.sessions.forEach((w, i) => {
      const m = F.M[i];
      if (w.id !== m.id || w.w !== m.w || w.act !== m.act || p.grid[w.act_i] !== m.act) throw Error('Свидетель не совпадает с семьёй: ' + w.id);
      for (let j = 0; j < F.grid.length; j++) {
        const b = w.bars[p.first_i + j], f = m.path[j];
        if ((b == null) !== (f == null) || (b && (b[2] !== f[0] || b[1] !== f[1] || b[3] !== f[2]))) throw Error('Путь свидетеля не совпадает с путём семьи: ' + w.id);
      }
    });
    const W = new Map(p.sessions.map(w => [w.id, w])), E = new Map(p.episodes.map(e => [e.id, e]));
    for (const pt of p.points) { const bad = pbWitness(pt, W.get(pt.case), E); if (bad) throw Error('Точка не подтверждается своими свечами (' + bad + '): ' + pt.case); }
    for (const s of PB_SCALES) { const bad = pbZoneCheck(r, s); if (bad) throw Error('Созвездие не совпадает с публикацией: ' + bad + ' · масштаб ' + s); }
    // today: the published bars are the visible prefix of this page; every completed episode stands on them
    const T = p.today;
    if (JSON.stringify(todayDirected(ctx, p, T)) !== JSON.stringify(T.bars)) throw Error('Сегодняшние свечи ответа не совпадают с экраном');
    const tw = { bars: T.bars, act_i: p.grid.indexOf(T.act) };
    for (const e of T.episodes) if (e.status === 'KNOWN') {
      const bad = pbWitness({ i: e.jl, v: e.L, case: 'today', episodes: ['t'] }, tw, new Map([['t', Object.assign({}, e, { id: 't', case: 'today' })]]));
      if (bad) throw Error('Сегодняшний эпизод не стоит на свечах: ' + bad);
    }
    return r;
  }
  // today's closed M5 of the block up to the slice, in the frame of the answer (directed ticks)
  function todayDirected(ctx, p, T) {
    const tick = A.day.tick || 0.25, by = new Map(ctx.D.bars.map(b => [b.t + 5, b])), t = v => Math.round(v / tick), d = T.direction, e = T.edge_ticks, out = [];
    for (const Tm of p.grid) {
      if (Tm > T.cut) break;
      const b = by.get(Tm);
      out.push(!b ? null : d === 1 ? [t(b.o) - e, t(b.h) - e, t(b.l) - e, t(b.c) - e] : [e - t(b.o), e - t(b.l), e - t(b.h), e - t(b.c)]);
    }
    return out;
  }
  // ---------- geometry: haze and threads of each constellation over its stars (a binned, separable Gaussian: fast for many) ----------
  function pbKde(pts, sig) {
    const step = 4, xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    const x0 = Math.min(...xs) - 3 * sig, y0 = Math.min(...ys) - 3 * sig;
    const nx = Math.ceil((Math.max(...xs) + 3 * sig - x0) / step) + 1, ny = Math.ceil((Math.max(...ys) + 3 * sig - y0) / step) + 1;
    const A0 = new Float64Array(nx * ny), A1 = new Float64Array(nx * ny), gv = new Float64Array(nx * ny);
    for (const [x, y] of pts) { const ix = Math.round((x - x0) / step), iy = Math.round((y - y0) / step); if (ix >= 0 && ix < nx && iy >= 0 && iy < ny) A0[iy * nx + ix]++; }
    const R = Math.ceil(3 * sig / step), K = [];
    for (let d = -R; d <= R; d++) K.push(Math.exp(-(d * step) * (d * step) / (2 * sig * sig)));
    for (let iy = 0; iy < ny; iy++) for (let ix = 0; ix < nx; ix++) { let s = 0; for (let d = -R; d <= R; d++) { const j = ix + d; if (j >= 0 && j < nx) s += K[d + R] * A0[iy * nx + j]; } A1[iy * nx + ix] = s; }
    let mx = 0, mi = 0;
    for (let iy = 0; iy < ny; iy++) for (let ix = 0; ix < nx; ix++) {
      let s = 0; for (let d = -R; d <= R; d++) { const j = iy + d; if (j >= 0 && j < ny) s += K[d + R] * A1[j * nx + ix]; }
      gv[iy * nx + ix] = s; if (s > mx) { mx = s; mi = iy * nx + ix; }
    }
    return { step, x0, y0, nx, ny, gv, mx, spot: { x: x0 + (mi % nx) * step, y: y0 + Math.floor(mi / nx) * step } };
  }
  function pbMst(pts) {
    const n = pts.length, inT = new Uint8Array(n), best = new Float64Array(n).fill(Infinity), from = new Int32Array(n).fill(-1), segs = [];
    if (!n) return segs;
    best[0] = 0;
    for (let it = 0; it < n; it++) {
      let u = -1;
      for (let i = 0; i < n; i++) if (!inT[i] && (u < 0 || best[i] < best[u])) u = i;
      inT[u] = 1;
      if (from[u] >= 0) segs.push([pts[from[u]][0], pts[from[u]][1], pts[u][0], pts[u][1]]);
      for (let i = 0; i < n; i++) if (!inT[i]) { const d = Math.hypot(pts[u][0] - pts[i][0], pts[u][1] - pts[i][1]); if (d < best[i]) { best[i] = d; from[i] = u; } }
    }
    return segs;
  }
  function pbGeom(ctx, r) {
    const p = r.proof, s = PB.scale, F = ctx.F;
    const key = [V.plot.w, V.plot.h, st.v0, st.v1, V.p0, V.p1].map(v => Math.round(v * 100)).join('|') + '|' + s + '|' + r.release_id;
    if (PB.cl && PB.cl.key === key) return PB.cl;
    const W = new Map(p.sessions.map(w => [w.id, w])), E = new Map(p.episodes.map(e => [e.id, e])), P = new Map(p.points.map(q => [q.id, q]));
    const zones = p.maps[String(s)].zones.map((z, i) => {
      const cells = new Set(z.cell_mask.map(c => c[0] + '|' + c[1]));
      const pts = p.points.filter(q => q.kt >= s && cells.has(q.k + '|' + q.b)).map(q => ({ q, x: V.X(q.open + 2.5), y: V.Y(F.u2p(q.v / W.get(q.case).w)) }));
      const xy = pts.map(o => [o.x, o.y]), kd = xy.length ? pbKde(xy, 18) : null;
      return { z, i, pts, kd, g1: kd ? iso(kd, 0.22) : [], g2: kd ? iso(kd, 0.6) : [], hit: kd ? iso(kd, 0.2) : [], ln: kd ? iso(kd, 0.35) : [], mst: pbMst(xy) };
    });
    return (PB.cl = { key, zones, W, E, P });
  }
  const pbShare = (z, N) => z.n_possible ? pct(100 * z.n_known / N) + '–' + pct(100 * (z.n_known + z.n_possible) / N) : pct(100 * z.n_known / N);
  const pbRel = (r, i) => r.proof.today.zones[String(PB.scale)][i];
  function pbDraw(c, ctx, phase) {
    requestPullbacks(ctx);
    const r = pbPacket(ctx), F = ctx.F;
    if (phase === 'under') V.pbLbl = [];
    if (!r || !F) return;
    const G = pbGeom(ctx, r), h = hv(), N = r.proof.context.N, sl = sliceOf(ctx);
    if (phase === 'under') {
      for (const g of G.zones) {
        if (!g.kd) continue;
        const rel = pbRel(r, g.i), past = rel.clock === 'PAST', on = !!(h && h.k === 'pbzone' && h.i === g.i), k = !h ? 1 : on ? 1.5 : 0.6;
        const dim = past ? 0.6 * cfg.spentA / 100 : 1, col = past ? stateCol(PBC, 'spent') : PBC, fa = cfg.cloudA / 100, ta = cfg.threadA / 100;
        c.save();
        c.filter = 'blur(14px)'; c.fillStyle = rgba(col, 0.5 * Math.min(0.5, 0.17 * k * dim * fa)); loopsPath(c, g.g1); c.fill();
        c.filter = 'blur(7px)'; c.fillStyle = rgba(col, 0.5 * Math.min(0.45, 0.13 * k * dim * fa)); loopsPath(c, g.g2); c.fill();
        c.filter = 'none';
        c.strokeStyle = rgba(col, Math.min(0.35, 0.13 * k * dim * ta)); c.lineWidth = 0.5;
        c.beginPath(); for (const sg of g.mst) { c.moveTo(sg[0], sg[1]); c.lineTo(sg[2], sg[3]); } c.stroke();
        if (on) { c.strokeStyle = rgba(col, 0.6); c.lineWidth = 1; loopsPath(c, g.ln); c.stroke(); }
        // the name and share inside, translucent, under the candles, as the accepted constellations show theirs
        const zt = pbShare(g.z, N), fs = Math.round(clamp(12 + 0.45 * 100 * g.z.n_known / N, 15, 21) * cfg.zoneLbl / 100), nfs = Math.round(fs * 0.6);
        c.font = '700 ' + nfs + 'px ' + FONT;
        const wN = c.measureText(g.z.label).width, wT = wN + 4 + pctW(c, zt, '700 ', fs);
        const cx = g.pts.reduce((a, o) => a + o.x, 0) / g.pts.length, cy = g.pts.reduce((a, o) => a + o.y, 0) / g.pts.length;
        const lx = clamp(cx - wT / 2, 4, V.plot.w - 64 - wT), ly = clamp(cy - fs / 2, 30, V.plot.h - fs - 4), yb = ly + fs * 0.86;
        c.globalAlpha = (k < 1 ? 0.4 + 0.5 * k : 1) * (past ? cfg.zoneSpentA / 100 : 1);
        c.font = '700 ' + nfs + 'px ' + FONT; c.textBaseline = 'alphabetic'; c.fillStyle = rgba(col, cfg.zoneNameA / 100); c.fillText(g.z.label, lx, yb);
        pctDraw(c, zt, lx + wN + 4, yb, '700 ', fs, rgba(mixW(col, 0.35), cfg.zoneNumA / 100));
        c.restore();
        V.pbLbl.push({ box: [lx - 2, ly - 2, wT + 4, fs + 6], i: g.i });
      }
      return;
    }
    // over the candles: the stars of every constellation, then the path of the hovered or pinned historical session
    const R0 = 1.7 * cfg.ptSize / 100, sel = h && h.k === 'pbpt' ? G.P.get(h.id) : null;
    for (const g of G.zones) {
      const col = pbRel(r, g.i).clock === 'PAST' ? stateCol(PBC, 'spent') : PBC;
      for (const o of g.pts) {
        if (o.x < -4 || o.x > V.plot.w + 4 || o.y < -4 || o.y > V.plot.h + 4) continue;
        const lit = sel ? sel.case === o.q.case : h && h.k === 'pbzone' ? h.i === g.i : null;
        let a = (o.q.open + 5 <= sl ? cfg.pastA : cfg.ptA) / 100 * 1.1, rr = R0;
        if (lit === true) { a = Math.min(1, Math.max(a, 0.55) + 0.3); rr = R0 * 1.3; } else if (lit === false) a *= 0.28;
        c.fillStyle = rgba(col, Math.min(1, a)); c.beginPath(); c.arc(o.x, o.y, rr, 0, 6.2832); c.fill();
      }
    }
    if (sel) pbDrawPath(c, ctx, r, G, sel);
  }
  // the chosen historical session: its own M5 (ranges and closes in its IDR units carried to today's scale, its real
  // clock), the vertex H of every episode ending at this bottom with its level dashed to the update B (the first M5 above
  // it), the bottom L, its activation and its DR break; quiet, so today's candles stay first
  function pbDrawPath(c, ctx, r, G, pt) {
    const F = ctx.F, p = r.proof, w = G.W.get(pt.case), U = v => V.Y(F.u2p(v / w.w)), X = j => V.X(p.grid[j] - 2.5);
    c.save();
    c.beginPath(); let first = true;
    w.bars.forEach((b, j) => { if (!b || j < p.first_i) { first = true; return; } const x = X(j), y = U(b[3]); if (first) { c.moveTo(x, y); first = false; } else c.lineTo(x, y); });
    c.strokeStyle = rgba('#ECF0F6', Math.min(1, 0.4 * cfg.pathA / 100)); c.lineWidth = 1; c.stroke();
    w.bars.forEach((b, j) => {
      if (!b || j < p.first_i) return;
      const x = Math.round(X(j)) + 0.5;
      c.strokeStyle = rgba('#ECF0F6', Math.min(1, (j <= w.act_i ? 0.06 : 0.14) * cfg.pathA / 100)); c.beginPath(); c.moveTo(x, U(b[1])); c.lineTo(x, U(b[2])); c.stroke();
    });
    const mark = (x, y, t) => { c.font = '700 11px ' + FONT; c.fillStyle = PBC; c.textBaseline = 'middle'; c.fillText(t, x + 8, y + 0.5); };
    for (const id of pt.episodes) {
      const e = G.E.get(id), xa = X(e.a), xb = X(e.jb), yh = U(e.h);
      c.strokeStyle = rgba(PBC, 0.75); c.lineWidth = 1; c.setLineDash([4, 3]); c.beginPath(); c.moveTo(xa, yh); c.lineTo(xb, yh); c.stroke(); c.setLineDash([]);
      c.fillStyle = PBC; c.beginPath(); c.arc(xa, yh, 3, 0, 6.2832); c.fill(); mark(xa, yh - 9, 'H');
      c.strokeStyle = PBC; c.lineWidth = 1.6; c.beginPath(); c.moveTo(xb - 5, yh); c.lineTo(xb + 5, yh); c.stroke(); mark(xb, yh - 9, 'B');
    }
    const xl = X(pt.i), yl = U(pt.v);
    c.strokeStyle = PBC; c.lineWidth = 1.6; c.beginPath(); c.arc(xl, yl, 6, 0, 6.2832); c.stroke(); mark(xl, yl, 'L');
    const tag = (T, text, bg, y) => { const x = V.X(T - 2.5); c.font = '600 10.5px ' + FONT; const tw = c.measureText(text).width + 8; c.fillStyle = bg; roundRect(c, x - tw / 2, y, tw, 16, 3); c.fill(); c.fillStyle = '#0B0C10'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, x, y + 8.5); c.textAlign = 'left'; };
    tag(w.act, (F.brk ? 'слом ' : 'подтв. ') + clk(w.act), 'rgba(236,240,246,.85)', 70);
    if (!F.brk && w.brk != null) tag(w.brk, 'слом DR ' + clk(w.brk), 'rgba(242,54,69,.9)', 90);
    c.restore();
  }
  function pbHit(x, y) {
    if (!pullbackMode()) return null;
    const ctx = V.ctx, r = pbPacket(ctx);
    if (!r || !ctx.F) return null;
    const G = pbGeom(ctx, r);
    let best = null, bd = 5;
    for (const g of G.zones) for (const o of g.pts) { const d = Math.hypot(o.x - x, o.y - y); if (d < bd) { bd = d; best = o; } }
    if (best) {
      const same = new Set(G.zones.flatMap(g => g.pts).filter(o => Math.hypot(o.x - best.x, o.y - best.y) < 2.5).map(o => o.q.case));
      return { k: 'pbpt', id: best.q.id, same: same.size };
    }
    for (const L of V.pbLbl || []) if (x >= L.box[0] && x <= L.box[0] + L.box[2] && y >= L.box[1] && y <= L.box[1] + L.box[3]) return { k: 'pbzone', i: L.i };
    for (const g of G.zones) if (g.hit.length && inLoops(g.hit, x, y)) return { k: 'pbzone', i: g.i };
    return null;
  }
  // ---------- words: only the registered labels of the candidate edition (integration/candidates/registry/90-pullbacks.yaml) ----------
  const PZ = 'EST:PB-ZONE', PS = 'EST:PB-SESSIONS', PT = 'FF:PB-TODAY', PE = 'FF:PB-EPISODE';
  const pbStatus = ctx => !ctx.F || !ctx.F.N ? statusMsg(ctx) : PB.error || 'Собираю эпизоды семьи…';
  // the frame's own words: in a short (and in a break frame of a long) the vertex is a low and the pullback ends at a high
  const pbW = F => { const d = F && F.d0 === -1 ? 'down' : 'up'; return { top: lbl(PE, 'top_' + d), topg: lbl(PE, 'topg_' + d), topgp: lbl(PE, 'topgp_' + d), bot: lbl(PE, 'bot_' + d) }; };
  function pbRelWords(rel, F) {
    const v = rel.visit, cp = rel.completion, w = pbW(F);
    return { clock: lbl(PT, rel.clock), visit: v.state === 'VISITED' ? lbl(PT, 'VISITED', { t: clk(v.close) }) : lbl(PT, v.state === 'UNKNOWN' ? 'VISIT_UNKNOWN' : 'NOT_YET'),
      completion: cp.state === 'COMPLETED' ? lbl(PT, 'COMPLETED', { top: w.top, h: clk(cp.h_open), t: clk(cp.b_close) }) : cp.state === 'IN_ZONE_NOT_UPDATED' ? lbl(PT, 'IN_ZONE_NOT_UPDATED', { top: w.top, h: clk(cp.h_open) }) : lbl(PT, 'NONE') };
  }
  const pbWin = z => clk(z.time_start) + '–' + clk(z.time_end);
  const pbDate = id => id.slice(3, 7) + '-' + id.slice(7, 9) + '-' + id.slice(9, 11);
  const pbScaleSwitch = () => '<span class="p24-seg sm pbseg" title="' + esc(lbl(PZ, 'scale_title', { k: PB.scale })) + '"><span class="pbsl">' + lbl(PZ, 'scale') + '</span>' +
    PB_SCALES.map(k => '<button data-pbscale="' + k + '" class="' + (PB.scale === k ? 'on' : '') + '">' + k + '</button>').join('') + '</span>';
  function pbPanel(ctx) {
    requestPullbacks(ctx);
    const F = ctx.F, r = pbPacket(ctx), out = [];
    out.push('<div class="p21-h"><span title="' + esc(lbl(PZ, 'head_title')) + '">' + lbl(PZ, 'head') + '</span><span>' + (F ? lbl(PZ, 'frame', null, VW(F)) : '') + '</span></div>');
    if (F) out.push('<div class="p21-note">' + esc(F.cond) + '</div>');
    out.push('<div class="p21-h second pbctl">' + pbScaleSwitch() + scopeSwitch() + '</div>');
    if (!r) return out.join('') + '<div class="p21-note">' + esc(pbStatus(ctx)) + '</div>';
    const p = r.proof, zm = p.maps[String(PB.scale)], N = p.context.N, sl = sliceOf(ctx), now = () => '<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>';
    if (!zm.zones.length) out.push('<div class="p21-note">' + lbl(PZ, 'none', { need: zm.need }) + '</div>');
    let sep = false;
    zm.zones.forEach((z, i) => {
      if (!sep && z.time_end > sl) { sep = true; out.push(now()); }
      const wd = pbRelWords(pbRel(r, i), F), b = pbBundle(r, PZ, x => x.zone_id === z.zone_id && x.scale === PB.scale);
      const row = '<span class="t"><span><span class="zt">' + pbWin(z) + '</span> <i class="zn" style="color:' + PBC + '">' + z.label + '</i></span>' +
        '<span class="p21-sub">' + lbl(PZ, 'sub', { band: band(z.price_low, z.price_high), clock: wd.clock }) + '</span>' +
        '<span class="p21-sub">' + lbl(PT, 'row') + ': ' + esc(wd.visit) + ' · ' + esc(wd.completion) + '</span></span><b class="zp">' + (b ? pbShare(z, N) : '—') + '</b>';
      let html = link({ k: 'pbzone', i }, row, 'mc' + (pbRel(r, i).clock === 'PAST' ? ' zst-IMPOSSIBLE' : ''), null, b ? b.claim.statement_ru : '');
      if (b) html = html.replace('data-l21=', 'data-bundle="' + b.id + '" data-edition="' + REVIEW.edition + '" data-l21=');
      out.push(html);
    });
    if (!sep && zm.zones.length) out.push(now());
    const sb = pbBundle(r, PS, x => x.scale === PB.scale);
    if (sb) for (const cat of sb.estimates[0].categories) out.push('<div class="p21-link dim" data-bundle="' + sb.id + '" data-edition="' + REVIEW.edition + '" title="' + esc(sb.claim.statement_ru) + '">' + prow(lbl(PS, cat.category), pct(100 * cat.count / N)) + '</div>');
    out.push('<div class="p21-note">' + lbl(PZ, 'note') + '</div>');
    out.push(pbTodayHtml(r, F));
    return out.join('');
  }
  function pbTodayHtml(r, F) {
    const T = r.proof.today, s = PB.scale, u = v => sd(v / T.w), w = pbW(F);
    const done = T.episodes.filter(e => e.status === 'KNOWN' && e.kt >= s), wait = T.episodes.filter(e => e.status === 'NOT_YET' && e.kt >= s && e.L != null);
    const e1 = done.length ? done.reduce((a, b) => b.b_close > a.b_close ? b : a) : null, e2 = wait.length ? wait.reduce((a, b) => b.h_open > a.h_open ? b : a) : null;
    const s1 = e1 ? lbl(PT, 'today_done', { n: done.length, bot: w.bot, top: w.top, l: u(e1.L), lt: clk(e1.l_open), h: clk(e1.h_open), bt: clk(e1.b_close) }) : lbl(PT, 'today_none');
    const s2 = e2 ? lbl(PT, 'today_wait', { top: w.top, bot: w.bot, h: u(e2.h), ht: clk(e2.h_open), l: u(e2.L), lt: clk(e2.l_open) }) : '';
    return '<div class="p21-h second"><span title="' + esc(lbl(PT, 'k', { act: clk(T.act) })) + '">' + lbl(PT, 'today_head', { scale: s }) + '</span></div><div class="p21-note">' + esc(s1) + '</div>' + (s2 ? '<div class="p21-note">' + esc(s2) + '</div>' : '');
  }
  function pbInspector(ctx, h) {
    const r = pbPacket(ctx);
    if (!r) return '<div class="ih">' + lbl(PZ, 'head') + '</div><div class="is">' + esc(pbStatus(ctx)) + '</div>';
    const p = r.proof, N = p.context.N, G = pbGeom(ctx, r), F = ctx.F;
    if (h && h.k === 'pbzone') {
      const z = p.maps[String(PB.scale)].zones[h.i];
      if (!z) return '';
      const wd = pbRelWords(pbRel(r, h.i), F), ww = pbW(F);
      return '<div class="ih">' + lbl(PZ, 'zone_head', { label: z.label, window: pbWin(z), band: band(z.price_low, z.price_high) }) + '</div>' +
        '<div class="is"><b class="big">' + pbShare(z, N) + '</b> ' + lbl(PZ, 'zone_share', { yes: z.n_known, N, topg: ww.topg }) + '</div>' +
        (z.n_possible ? '<div class="is">' + lbl(PZ, 'zone_unknown', { unknown: z.n_possible }) + '</div>' : '') +
        '<div class="is">' + lbl(PZ, 'zone_more', { episodes: z.n_episodes, points: z.n_points, scale: PB.scale }) + '</div>' +
        '<div class="is">' + lbl(PT, 'row') + ': ' + esc(wd.clock) + ' · ' + esc(wd.visit) + ' · ' + esc(wd.completion) + '</div>' +
        '<div class="is k">' + lbl(PZ, 'zone_click') + '</div>';
    }
    if (h && h.k === 'pbpt') {
      const pt = G.P.get(h.id);
      if (!pt) return '';
      const w = G.W.get(pt.case), u = v => sd(v / w.w), e0 = G.E.get(pt.episodes[0]), ww = pbW(F);
      const lines = ['<b>' + lbl(PE, 'head', { date: w.date.split('-').reverse().join('.') }) + '</b>' + (h.same > 1 ? ' <span class="k">' + lbl(PE, 'same', { n: h.same - 1 }) + '</span>' : '')];
      lines.push(lbl(PE, 'L', { bot: ww.bot, sd: u(pt.v), t: clk(pt.open) + '–' + clk(pt.open + 5) }));
      for (const id of pt.episodes) {
        const e = G.E.get(id);
        lines.push('<span class="k">' + lbl(PE, 'H', { top: ww.top, sd: u(e.h), t: clk(e.h_open) + '–' + clk(e.h_open + 5) }) + '</span>');
        lines.push(lbl(PE, 'B', { topg: ww.topg, t: clk(e.b_close - 5) + '–' + clk(e.b_close), c: clk(e.b_close) }) + ' · <span class="k">' + lbl(PE, 'gap', { m: e.b_close - pt.open - 5 }) + '</span>');
      }
      if (pt.episodes.length > 1) lines.push('<span class="k">' + lbl(PE, 'links', { n: pt.episodes.length, topgp: ww.topgp }) + '</span>');
      lines.push('<span class="k">' + lbl(PE, 'scale', { top: ww.top, k: pt.kt }) + '</span>');
      lines.push(lbl(PE, 'dr_' + e0.dr, { t: w.brk != null ? clk(w.brk) : '' }));
      lines.push('<span class="k">' + lbl(PE, 'now', { t: clk(sliceOf(ctx)) }) + '</span>');
      return lines.join('<br>');
    }
    return '<div class="ih">' + lbl(PZ, 'head') + ' · ' + lbl(PZ, 'scale') + ' ' + PB.scale + '</div><div class="is">' + esc(F ? F.cond : '') + '</div><div class="is k">' + lbl(PZ, 'note') + '</div>';
  }
  // window 1: a constellation's sessions (each with its bottom and its update), or every episode of one session
  function pbDetail(ctx, o) {
    const r = pbPacket(ctx);
    if (!r) return { head: lbl(PZ, 'head'), body: '<div class="p21-note">' + esc(pbStatus(ctx)) + '</div>' };
    const p = r.proof, N = p.context.N, G = pbGeom(ctx, r);
    if (o && o.k === 'pbzone' && p.maps[String(PB.scale)].zones[o.i]) {
      const z = p.maps[String(PB.scale)].zones[o.i], cells = new Set(z.cell_mask.map(c => c[0] + '|' + c[1])), first = new Map();
      for (const q of p.points) if (q.kt >= PB.scale && cells.has(q.k + '|' + q.b) && !first.has(q.case)) first.set(q.case, q);
      const rows = z.members.map(id => { const q = first.get(id), e = G.E.get(q.episodes[0]); return '<div class="pbep pbrow" data-pbpt="' + esc(q.id) + '"><span>' + esc(pbDate(id)) + '</span><b>L ' + clk(q.open) + ' · B ' + clk(e.b_close) + '</b></div>'; }).join('');
      return { head: lbl(PZ, 'win_head', { label: z.label }), body: dRow(lbl(PZ, 'win_share'), pbShare(z, N)) + dRow(lbl(PZ, 'win_window'), pbWin(z) + ' · ' + band(z.price_low, z.price_high) + ' SD') +
        '<div class="p21-note">' + lbl(PZ, 'win_cells', { n: z.cell_mask.length }) + ' · ' + lbl(PZ, 'win_apex', { d: z.apex_D }) + '</div>' +
        '<div class="pblist"><div class="pbep k"><span>' + lbl(PZ, 'win_members') + '</span></div>' + rows +
        (z.possible.length ? '<div class="pbep k"><span>' + lbl(PZ, 'win_possible') + '</span></div><div class="p21-note">' + z.possible.map(id => esc(pbDate(id))).join(', ') + '</div>' : '') + '</div>' };
    }
    if (o && o.k === 'pbpt' && G.P.get(o.id)) {
      const pt = G.P.get(o.id), w = G.W.get(pt.case), u = v => sd(v / w.w), mine = new Set(pt.episodes);
      const dr = w.oppv == null ? lbl(PE, 'dr_NA') : w.brk != null ? lbl(PE, 'dr_broken', { t: clk(w.brk) }) : w.brk_known ? lbl(PE, 'dr_held', { end: clk(p.context.end) }) : lbl(PE, 'dr_unknown');
      const rows = p.episodes.filter(e => e.case === pt.case).map(e => '<div class="pbep' + (mine.has(e.id) ? ' on' : '') + '" title="' + esc('H ' + u(e.h) + (e.status === 'KNOWN' ? ' · L ' + u(e.L) : '') + ' SD') + '"><span>' +
        clk(e.h_open) + (e.status === 'KNOWN' ? ' → ' + clk(e.l_open) : '') + (e.b_close != null ? ' → ' + clk(e.b_close) : '') + '</span><b>' + lbl(PE, e.status) + ' · ' + lbl(PE, 'win_scale', { k: e.kt }) + '</b></div>').join('');
      return { head: lbl(PE, 'win_head', { date: w.date.split('-').reverse().join('.') }), body: '<div class="p21-note">' + lbl(PE, 'win_act', { t: clk(w.act), dr }) + '</div><div class="pblist"><div class="pbep k"><span>' + lbl(PE, 'win_cols') + '</span></div>' + rows + '</div>' };
    }
    return { head: lbl(PZ, 'head'), body: '<div class="p21-note">' + esc(lbl(PZ, 'head_title')) + '</div><div class="p21-note">' + esc(lbl(PZ, 'scale_title', { k: PB.scale })) + '</div>' + dRow('выпуск', r.release_id.slice(0, 12)) };
  }
  // window 2: the same episodes at every scale (the review: compare scales, the episodes keep their identity)
  function pbScalesHtml(r) {
    const p = r.proof, N = p.context.N;
    return '<div class="pblist">' + PB_SCALES.map(k => {
      const zm = p.maps[String(k)], top = zm.zones.reduce((a, z) => !a || z.n_known > a.n_known ? z : a, null), c = zm.sessions;
      return '<div class="pbsc' + (k === PB.scale ? ' on' : '') + '" data-pbscale="' + k + '">' + dRow(lbl(PS, 'scale_row', { k }), top ? top.label + ' ' + pbShare(top, N) : '—') +
        '<div class="p21-note">' + lbl(PS, 'scale_note', { n: zm.zones.length, in: pct(100 * c.IN_ZONES / N), unk: pct(100 * c.UNKNOWN / N), e: zm.episodes }) + '</div></div>';
    }).join('') + '</div>';
  }
  // window 3: the bottoms of this scale by cell (0,1 SD × 15 min, sessions per cell), the constellations outlined
  function pbHeat(id, ctx, r) {
    const K = cardCanvas(id);
    if (!K) return;
    const { c, W, H } = K, p = r.proof, F = ctx.F, s = PB.scale, L = 30, T = 4, B = 16, Rm = 4, cnt = new Map();
    for (const q of p.points) if (q.kt >= s) { const key = q.k + '|' + q.b; if (!cnt.has(key)) cnt.set(key, new Set()); cnt.get(key).add(q.case); }
    if (!cnt.size) return;
    const ks = [...cnt.keys()].map(k => +k.split('|')[0]).sort((a, b) => a - b);
    const k0 = ks[Math.floor(0.03 * (ks.length - 1))], k1 = ks[Math.ceil(0.97 * (ks.length - 1))] + 1, mx = Math.max(...[...cnt.values()].map(v => v.size));
    const cw = (W - L - Rm) / F.nb, rh = (H - T - B) / Math.max(1, k1 - k0), X = b => L + b * cw, Y = k => T + (k1 - 1 - k) * rh;
    for (const [key, set] of cnt) { const [k, b] = key.split('|').map(Number); if (k < k0 || k >= k1) continue; c.fillStyle = rgba(PBC, 0.18 + 0.82 * Math.pow(set.size / mx, 0.7)); c.fillRect(X(b) + 0.5, Y(k) + 0.25, Math.max(1, cw - 1), Math.max(1, rh - 0.5)); }
    for (const z of p.maps[String(s)].zones) {
      const set = new Set(z.cell_mask.map(([k, b]) => k + '|' + b));
      c.strokeStyle = rgba(PBC, 0.95); c.lineWidth = 1; c.beginPath();
      for (const [k, b] of z.cell_mask) {
        if (k < k0 || k >= k1) continue;
        const x0 = X(b), x1 = X(b + 1), y0 = Y(k), y1 = Y(k) + rh;
        if (!set.has((k + 1) + '|' + b)) { c.moveTo(x0, y0); c.lineTo(x1, y0); }
        if (!set.has((k - 1) + '|' + b)) { c.moveTo(x0, y1); c.lineTo(x1, y1); }
        if (!set.has(k + '|' + (b - 1))) { c.moveTo(x0, y0); c.lineTo(x0, y1); }
        if (!set.has(k + '|' + (b + 1))) { c.moveTo(x1, y0); c.lineTo(x1, y1); }
      }
      c.stroke();
    }
    const xs = X((sliceOf(ctx) - F.f) / 15);
    if (xs > L && xs < W - Rm) { c.strokeStyle = 'rgba(209,212,220,.5)'; c.setLineDash([3, 3]); c.beginPath(); c.moveTo(xs, T); c.lineTo(xs, H - B); c.stroke(); c.setLineDash([]); }
    c.font = '10px ' + FONT; c.fillStyle = C.text3; c.textBaseline = 'middle'; c.textAlign = 'right';
    c.fillText(sd(k1 / 10), L - 4, T + 4); c.fillText(sd(k0 / 10), L - 4, H - B - 4);
    c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText(clk(F.f), L, H - B + 3); c.textAlign = 'right'; c.fillText(clk(F.end), W - Rm, H - B + 3); c.textAlign = 'left';
  }
  // the «↺» frame: the candles, the box and the constellations whose window has not passed (as the accepted view does)
  function pbRange(ctx, lo, hi) {
    const r = pbPacket(ctx), F = ctx.F;
    if (!r || !F) return [lo, hi];
    r.proof.maps[String(PB.scale)].zones.forEach((z, i) => {
      if (pbRel(r, i).clock === 'PAST') return;
      const a = F.u2p(z.price_low / 10), b = F.u2p(z.price_high / 10); lo = Math.min(lo, a, b); hi = Math.max(hi, a, b);
    });
    return [lo, hi];
  }
  // the toolbar keeps its accepted width (SWPC-1.1 W01: the cut is never hidden): the view's own button stands only while the
  // view is open (the area button gives way to it); it is entered from its row in the panel or by switching the trial on
  function pbToolbar(F) {
    const b = dom('mode').querySelector('[data-m="pullbacks"]');
    if (b) b.hidden = !pullbackMode();
    dom('areab').hidden = pullbackMode();
    if (!pullbackMode()) return;
    dom('ev').innerHTML = '<span class="evc" title="' + esc(lbl(PZ, 'head_title')) + '"><i style="background:' + PBC + '"></i>L<span> ' + pbW(F).bot + '</span></span>';
  }
  root.addEventListener('click', e => {
    const b = e.target.closest('[data-pbscale]');
    if (!b || !pullbackMode()) return;
    PB.scale = +b.dataset.pbscale; PB.cl = null; st.pin = st.hover = null;
    try { localStorage.setItem(PB_KEY, String(PB.scale)); } catch (x) { /* not kept */ }
    dom('detg')._k = ''; render(true);
  });
  det.addEventListener('mouseover', e => { const el = e.target.closest('[data-pbpt]'); if (!el || !pullbackMode()) return; st.hover = { k: 'pbpt', id: el.dataset.pbpt, same: 1 }; st.fromDet = true; redraw(); });
  // windows 2 and 3 of the six (panel.js::details): the scales and the bottoms by cell; false = not this view
  function pbCards(g, ctx) {
    const pr = pullbackMode() && pbPacket(ctx);
    if (!pr) return false;
    const cards = g.querySelectorAll('.dcard');
    cards[1].innerHTML = '<div class="dt">' + lbl('EST:PB-SESSIONS', 'scales_head') + '</div>' + pbScalesHtml(pr);
    cards[2].innerHTML = '<div class="dt" style="color:' + PBC + '">L · цена × время</div><canvas id="dcL"></canvas>';
    pbHeat('dcL', ctx, pr);
    return true;
  }
  // the entry from the accepted view: one row of the candidates' place in the panel (integration.js::candidatePanel)
  function pbEntry() {
    if (!ICFG.enabled || !TRIAL.pullbacks || pullbackMode()) return '';
    return '<div class="p21-link pbentry" data-pbmode="1" title="' + esc(lbl(PZ, 'head_title')) + '">' + prow('<i class="zn" style="color:' + PBC + '">L</i> ' + lbl(PZ, 'head'), '›') + '</div>';
  }
  root.addEventListener('click', e => { if (!e.target.closest('[data-pbmode]')) return; st.mode = 'pullbacks'; st.hover = st.pin = null; st.tool = false; render(true); });
