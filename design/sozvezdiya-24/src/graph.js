  // The operator's approved plan, 13.10.2026: the SAME question in two views. No estimator, matching rule, result or
  // historical coordinate is changed here. A historical line joins observed M5 closes; a hole breaks it. It is not
  // an intrabar path. The heatmap remains the registered CLOSE-M5 frequency layer, unchanged.
  const GRAPH_FF = 'FF:GRAPH-QUESTIONS';
  const graphQueryKind = h => !!(h && ['now', 'arrive', 'past', 'drctx', 'fact', 'phase'].includes(h.k));
  const graphContextKey = ctx => [A.inst, ctx.D.iso, ctx.s.k, st.scope, ctx.F && ctx.F.r.family_id].join('|');

  function familyCloseSegments(F, m) {
    const segments = []; let segment = null, last = null;
    for (let j = 0; j < F.grid.length; j++) {
      const row = m.path && m.path[j], t = F.grid[j];
      if (!row || !Number.isFinite(row[2]) || !m.w) { segment = null; last = null; continue; }
      const k = fdiv(10 * row[2], m.w);
      if (ppHeld(F, 'EST:B-CLOSE', { j, k0: k, k1: k + 1 })) { segment = null; last = null; continue; }
      const p = { j, t, u: row[2] / m.w, p: F.u2p(row[2] / m.w), lo: F.u2p(row[0] / m.w), hi: F.u2p(row[1] / m.w), pre: t <= m.act };
      if (!segment || !last || t - last.t !== 5) { segment = []; segments.push(segment); }
      segment.push(p); last = p;
    }
    return segments;
  }

  function graphQuestion(ctx, h) {
    h = h || hv();
    const F = ctx.F;
    if (!F || !graphQueryKind(h) || (h.context && h.context !== graphContextKey(ctx))) return null;
    const q = { kind: h.k, ev: h.ev, id: h.id, family: F.r.family_id, snapshot: F.r.snapshot_id, cut: sliceOf(ctx), ready: false };
    if (h.k === 'now') {
      const n = nowOf(ctx), E = n && n[h.ev];
      q.response = n; q.event = E;
      q.cut = n && n.cut ? n.cut.cut : q.cut;
      if (!Number.isFinite(q.cut) && n && n.cut) q.cut = clockMinute(n.cut.cut_clock_et);
      if (!E || !E.state || !E.continuation || !['OK', 'FROZEN_AT_BREAK'].includes(n.status)) return q;
      q.ready = !!nowBundle(n, 'EST:N-NEW-' + h.ev, 'MAIN', E.continuation);
      q.amount = q.ready && nowBundle(n, 'EST:N-IF-NEW-' + h.ev, 'MAIN');
      q.time = q.ready && nowBundle(n, 'EST:N-TIME-' + h.ev, 'MAIN');
      return q;
    }
    if (h.k === 'arrive') {
      const r = arriveOf(ctx), P = arrPlace(r, h.id);
      q.response = r; q.place = P;
      if (!P || !r || r.status !== 'OK') return q;
      q.price = P.withheld ? null : arrPrice(ctx, P); q.resolved = !P.withheld && P.state.status === 'RESOLVED';
      q.ready = !P.withheld && P.state.status === 'OPEN' && P.publication === 'PUBLISHED' && !!arriveBundle(r, P.level, P);
      q.members = q.ready ? P.members : [];
      return q;
    }
    q.ready = !F.held.has('family');
    return q;
  }

  const clockMinute = v => { const a = String(v || '').split(':').map(Number); return a.length === 2 && a.every(Number.isFinite) ? a[0] * 60 + a[1] : null; };

  function drawHistoricalPath(c, F, m, opts) {
    const segs = familyCloseSegments(F, m), cut = opts.cut;
    c.save(); c.lineWidth = opts.width || 1;
    for (const points of segs) {
      let stage = null, open = false;
      for (let i = 1; i < points.length; i++) {
        const a = points[i - 1], b = points[i];
        if (opts.futureOnly && b.t <= cut) continue;
        const before = b.t <= cut, pre = b.pre;
        const next = [before, pre].join('|');
        if (next !== stage) {
          if (open) c.stroke();
          stage = next; open = true;
          c.strokeStyle = rgba(opts.color, opts.alpha * (before ? 0.38 : 1) * (pre ? 0.45 : 1));
          c.lineWidth = opts.width || 1; c.setLineDash(opts.unknown ? [3, 4] : pre ? [2, 3] : []);
          c.beginPath(); c.moveTo(V.X(a.t), V.Y(a.p));
        }
        c.lineTo(V.X(b.t), V.Y(b.p));
      }
      if (open) c.stroke();
      if (points.length === 1 && (!opts.futureOnly || points[0].t > cut)) { const p = points[0]; c.fillStyle = rgba(opts.color, opts.alpha); c.fillRect(V.X(p.t) - 0.5, V.Y(p.p) - 0.5, 1, 1); }
      // Only the highlighted, prefix-matched historical cases carry their observed M5 ranges. This makes a wick-only
      // reach visible without inventing a first-arrival point or the order inside an M5.
      if (opts.ranges) for (const p of points) {
        if (p.t <= cut) continue;
        c.strokeStyle = rgba(opts.color, opts.alpha * 0.36); c.lineWidth = 0.65; c.setLineDash([]);
        c.beginPath(); c.moveTo(V.X(p.t), V.Y(p.lo)); c.lineTo(V.X(p.t), V.Y(p.hi)); c.stroke();
      }
    }
    c.restore();
    return segs;
  }

  function drawFamilyPaths(c, ctx) {
    const F = ctx.F, cut = sliceOf(ctx);
    V.pathEvidence = { family: F.r.family_id, snapshot: F.r.snapshot_id, cut, ids: [], segments: [], frequencies: st.pathFreq };
    if (F.held.has('family')) return;
    const q = graphQuestion(ctx), active = !!(q && q.kind === 'arrive' && q.ready);
    const alpha = clamp(10 / F.N, 0.018, 0.16) * (st.pathFreq ? 0.38 : 1) * (active ? 0.42 : 1);
    for (const m of F.M) {
      const segs = drawHistoricalPath(c, F, m, { cut, color: cfg.path, alpha });
      V.pathEvidence.ids.push(m.id);
      V.pathEvidence.segments.push({ id: m.id, points: segs.map(s => s.map(p => [p.j, p.t, p.u, p.p])) });
    }
    if (active) for (const [id, label] of q.members) {
      const m = F.M.find(x => x.id === id);
      if (!m) continue;
      drawHistoricalPath(c, F, m, { cut, color: label === 'YES' ? cfg.R : label === 'NO' ? cfg.path : '#A6AFBC', alpha: label === 'YES' ? 0.34 : 0.19, width: label === 'YES' ? 1.15 : 0.9, futureOnly: true, ranges: true, unknown: label === 'UNKNOWN' });
    }
  }

  function drawCurrentClose(c, ctx) {
    const F = ctx.F, cut = sliceOf(ctx), bar = ctx.D.bars.find(p => p.t + 5 === cut);
    V.currentClose = null;
    if (!bar) return;
    const p = bar.c, x = V.X(cut), y = V.Y(p);
    V.currentClose = { t: cut, p, u: F ? F.p2u(p) : null };
    c.save();
    c.strokeStyle = rgba(C.hist, 0.7); c.lineWidth = 1.25; c.setLineDash([4, 4]);
    c.beginPath(); c.moveTo(x, y); c.lineTo(x, V.plot.h); c.stroke(); c.setLineDash([]);
    c.fillStyle = C.bg; c.strokeStyle = '#F7C948'; c.lineWidth = 2.2;
    c.beginPath(); c.arc(x, y, 6, 0, Math.PI * 2); c.fill(); c.stroke();
    c.fillStyle = '#F7C948'; c.beginPath(); c.arc(x, y, 2.3, 0, Math.PI * 2); c.fill();
    c.restore();
  }

  function drawQuestionOverlay(c, ctx) {
    const F = ctx.F, h = hv(), q = graphQuestion(ctx, h);
    V.graphEvidence = q ? { kind: q.kind, ev: q.ev, id: q.id, family: q.family, cut: q.cut, ready: q.ready, members: q.members || [], price: q.price, priceRange: null, firstTimeRange: null, resolved: !!q.resolved } : null;
    if (!q) return;
    if (q.kind === 'now') {
      const E = q.event;
      if (!q.ready || !E || !E.state) return;
      const sign = q.ev === 'R' ? -1 : 1, u = q.ev === 'R' ? E.state.r_seen : E.state.x_seen, col = cfg[q.ev], anchor = F.u2p(u);
      const x0 = clamp(V.X(q.cut), 0, V.plot.w), x1 = V.plot.w - 3, y0 = V.Y(anchor);
      c.save(); c.strokeStyle = col; c.lineWidth = 1.65; c.setLineDash([5, 4]);
      c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y0); c.stroke(); c.setLineDash([]);
      c.fillStyle = C.bg; c.beginPath(); c.arc(x0, y0, 4, 0, Math.PI * 2); c.fill(); c.stroke();
      const a = E.continuation.delta_if_new || {}, t = E.continuation.time_to_new || {};
      if (q.amount && a.q25 != null && a.q75 != null) {
        const pA = F.u2p(u + sign * a.q25), pB = F.u2p(u + sign * a.q75), pM = F.u2p(u + sign * a.q50);
        const ya = V.Y(pA), yb = V.Y(pB), ym = V.Y(pM), w = Math.min(82, Math.max(40, V.plot.w * 0.07)), xx = V.plot.w - w;
        c.fillStyle = rgba(col, 0.22); c.fillRect(xx, Math.min(ya, yb), w, Math.max(2, Math.abs(ya - yb)));
        c.strokeStyle = rgba(col, 0.95); c.lineWidth = 1.2; c.strokeRect(xx, Math.min(ya, yb), w, Math.max(2, Math.abs(ya - yb)));
        c.beginPath(); c.moveTo(xx, ym); c.lineTo(V.plot.w, ym); c.stroke();
        V.win = { pA, pB, t0: null, t1: null, col };
        V.graphEvidence.priceRange = [pA, pB];
      }
      // FIRST update time and FINAL additional depth are separate marginal quantities. Never make their combination
      // a price×time target, a straight forecast line, or the endpoint of a synthetic path.
      if (q.time && t.q25_min != null && t.q75_min != null) {
        const ta = Math.min(F.end, q.cut + t.q25_min), tb = Math.min(F.end, q.cut + t.q75_min);
        const xa = clamp(V.X(ta), 0, V.plot.w), xb = clamp(V.X(tb), 0, V.plot.w);
        c.fillStyle = rgba(col, 0.22); c.fillRect(xa, V.plot.h - 7, Math.max(2, xb - xa), 7);
        c.strokeStyle = col; c.lineWidth = 1.4; c.beginPath(); c.moveTo(xa, V.plot.h - 10); c.lineTo(xa, V.plot.h); c.moveTo(xb, V.plot.h - 10); c.lineTo(xb, V.plot.h); c.stroke();
        if (t.q50_min != null) { const xm = V.X(Math.min(F.end, q.cut + t.q50_min)); c.beginPath(); c.moveTo(xm, V.plot.h - 14); c.lineTo(xm, V.plot.h); c.stroke(); }
        V.win = Object.assign(V.win || { pA: null, pB: null, col }, { t0: ta, t1: tb, timeLabel: lbl(GRAPH_FF, 'first_time', { ev: q.ev }) });
        V.graphEvidence.firstTimeRange = [ta, tb];
      }
      c.restore(); return;
    }
    if (q.kind === 'arrive') {
      if (q.price == null) return;
      const x = V.X(sliceOf(ctx)), y = V.Y(q.price), col = q.resolved ? stateCol(cfg.R, 'spent') : cfg.R;
      c.save(); c.lineWidth = 1.6; c.strokeStyle = col; c.setLineDash(q.resolved ? [2, 4] : []);
      c.beginPath(); c.moveTo(0, y); c.lineTo(V.plot.w, y); c.stroke(); c.setLineDash([]);
      V.win = { pA: q.price, pB: q.price, t0: null, t1: null, col };
      if (q.ready && q.place.state && q.place.state.w) {
        const state = q.place.state, center = state.close_v / state.w, a = F.u2p(center - 0.25), b = F.u2p(center + 0.25), ya = V.Y(a), yb = V.Y(b);
        c.fillStyle = rgba(cfg.path, 0.18); c.fillRect(x - 5, Math.min(ya, yb), 10, Math.abs(ya - yb));
        c.strokeStyle = cfg.path; c.lineWidth = 1.5; c.strokeRect(x - 5, Math.min(ya, yb), 10, Math.abs(ya - yb));
      }
      if (q.resolved) {
        const t = clockMinute(q.place.state.time), bar = ctx.D.bars.find(b => b.t + 5 === t);
        if (bar) {
          const xa = V.X(bar.t), xb = V.X(bar.t + 5), ya = V.Y(bar.h), yb = V.Y(bar.l);
          c.strokeStyle = cfg.R; c.lineWidth = 1.7; c.strokeRect(xa, ya - 3, Math.max(3, xb - xa), Math.max(6, yb - ya + 6));
          V.win.t0 = bar.t; V.win.t1 = bar.t + 5;
          V.graphEvidence.observedM5 = [bar.t, bar.t + 5];
        }
      }
      c.restore(); return;
    }
    if (q.kind === 'past') {
      const rows = todayRows(F, ctx);
      const activation = ctx.D.bars.find(b => b.t + 5 === F.act0);
      if (activation) {
        c.save(); c.strokeStyle = '#F7C948'; c.fillStyle = C.bg; c.lineWidth = 2;
        c.beginPath(); c.arc(V.X(F.act0), V.Y(activation.c), 5, 0, Math.PI * 2); c.fill(); c.stroke(); c.restore();
      }
      c.save(); c.strokeStyle = '#F7C948'; c.lineWidth = 2.5;
      c.beginPath(); let prev = null;
      for (const row of rows) {
        const x = V.X(row.T), y = V.Y(F.u2p(row.cl / F.w0t));
        if (!prev || row.T - prev.T !== 5) c.moveTo(x, y); else c.lineTo(x, y);
        prev = row;
      }
      c.stroke(); c.restore();
      for (const ev of ['R', 'X']) drawFactLine(c, ctx, ev);
      for (const level of levels(ctx.s)) {
        const L = levelRat(F, level.p), fact = todayReach(F, ctx, L, levelUp(F, ctx, L));
        if (fact.t == null) continue;
        const bar = ctx.D.bars.find(b => b.t === fact.t);
        if (!bar) continue;
        c.save(); c.fillStyle = C.bg; c.strokeStyle = '#F7C948'; c.lineWidth = 1.25;
        c.beginPath(); c.arc(V.X(bar.t + 2.5), V.Y(level.p), 3.2, 0, Math.PI * 2); c.fill(); c.stroke(); c.restore();
      }
      return;
    }
    if (q.kind === 'drctx' && ctx.s.opp != null) {
      c.save(); c.strokeStyle = ctx.s.failed ? C.brk : cfg.dr; c.lineWidth = 2.2;
      c.beginPath(); c.moveTo(V.X(F.act0), V.Y(ctx.s.opp)); c.lineTo(V.plot.w, V.Y(ctx.s.opp)); c.stroke(); c.restore();
      V.win = { pA: ctx.s.opp, pB: ctx.s.opp, t0: null, t1: null, col: ctx.s.failed ? C.brk : cfg.dr };
    }
  }

  function graphQuestionTip(ctx, h) {
    const F = ctx.F, q = graphQuestion(ctx, h);
    if (!F || !q) return '';
    if (h.k === 'past') {
      const out = '<div class="ih">' + lbl(GRAPH_FF, 'past') + '</div>' + todayHtml(F, ctx).replace(lbl('FF:TODAY-PREFIX', 'chg_none', { cut: clk(sliceOf(ctx)) }), lbl(GRAPH_FF, 'no_event', { cut: clk(sliceOf(ctx)) }));
      return out + '<div class="is">' + lbl(GRAPH_FF, 'past_title') + '</div>';
    }
    if (h.k === 'drctx') {
      const known = new Set(todayRows(F, ctx).map(b => b.T)); let hole = null;
      for (let t = F.act0 + 5; t <= sliceOf(ctx); t += 5) if (!known.has(t)) { hole = t; break; }
      return '<div class="ih">' + lbl(GRAPH_FF, 'dr') + '</div><div class="il">' + lbl('FF:TODAY-PREFIX', ctx.s.failed ? 'dr_broken' : 'dr_held', ctx.s.failed ? { t: clk(ctx.s.failed - 5) } : { opp: px(ctx.s.opp) }) + (hole == null ? '' : lbl('FF:TODAY-PREFIX', 'hole_short', { t: clk(hole - 5) })) + '</div>' + (F.out ? outcomeHtml(F, true) : '') + '<div class="is">' + lbl(GRAPH_FF, 'dr_title') + '</div>';
    }
    return '';
  }

  function graphNowTip(ctx, h) {
    const F = ctx.F, q = graphQuestion(ctx, h), E = q && q.event, n = q && q.response;
    const head = '<div class="ih" style="color:' + cfg[h.ev] + '">' + lbl(GRAPH_FF, h.ev === 'R' ? 'pullback' : 'extension') + '</div>';
    if (!q || !q.ready || !E || !E.continuation) return head + '<div class="is">' + esc(E && E.note || n && (n.note || n.message) || lbl(GRAPH_FF, 'unavailable')) + '</div>';
    const Cn = E.continuation, k = Cn.support, ev = h.ev, NE = 'EST:N-NEW-' + ev, b = Cn.p_new_bounds || [];
    const value = k.N_match_unknown ? pct(100 * b[0]) + '–' + pct(100 * b[1]) : pct(100 * Cn.p_new_extreme);
    const u = ev === 'R' ? E.state.r_seen : E.state.x_seen, sign = ev === 'R' ? -1 : 1, a = Cn.delta_if_new || {}, t = Cn.time_to_new || {};
    const price = v => px(F.u2p(u + sign * v));
    let out = head + '<div class="is">' + lbl(GRAPH_FF, 'anchor', { ev, price: price(0), cut: n.cut.cut_clock_et }) + '</div>';
    out += '<div class="ir"><span>' + lbl(NE, 'row', { ev }, VW(F)) + '</span><b>' + value + '</b></div>';
    out += '<div class="is">' + lbl(GRAPH_FF, 'new_counts', { yes: k.N_new_yes, n: k.N_match_total, unknown: k.N_match_unknown }) + ' · ' + lbl(GRAPH_FF, E.mode === 'PATH_CONDITIONED' ? 'by_path' : 'by_time') + '</div>';
    if (q.amount && a.q50 != null) out += '<div class="iq">' + lbl(GRAPH_FF, 'amount_head') + '</div><div class="il">' + lbl(GRAPH_FF, 'amount_value', { mid: price(a.q50), lo: px(Math.min(F.u2p(u + sign * a.q25), F.u2p(u + sign * a.q75))), hi: px(Math.max(F.u2p(u + sign * a.q25), F.u2p(u + sign * a.q75))), n: a.n }) + '</div>';
    if (q.time && t.q50_min != null) out += '<div class="iq">' + lbl(GRAPH_FF, 'time_head') + '</div><div class="il">' + lbl(GRAPH_FF, 'time_value', { min: Math.round(t.q50_min), n: t.n }) + '</div>';
    return out + '<div class="if">' + lbl(GRAPH_FF, 'own_anchor') + '</div>';
  }
