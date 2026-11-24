  // ---------- «Слой от Anthropic»: the candidate DR-LAB-ANT-0.1 over 23.5 (meaning/28-sloj-ot-anthropic.md) ----------
  // Operator 22.11.2026: «сделай рядом, где у меня сверху область и R … слева еще одну … назови его слой от антропика …
  // если я буду нажимать на эту плашку … я буду видеть, что показывают именно твои предложенные изменения». Off — 23.5
  // exactly as TP-2.0; on — over the same drawing, Claude's proposal of 22.11 (PROPOSED, not accepted; its estimands live in
  // the candidate edition DR-LAB-CANDIDATES-1, integration/candidates/registry/97-ant-layer.yaml):
  // - «дошли после {cut}»: of the family's sessions that at today's last closed M5 were like today (CS:ANT-LIKE-NOW-1: own
  //   activation before it, every M5 up to it, the DR whole up to it, the first M5 of the deepest low so far in the window
  //   of T's clock that holds today's, the top so far within a quarter of the IDR width of today's — the tolerance of
  //   «Сейчас»), those that after it got to the level (an M5 high at its 0.1-SD cell or further) before their own DR broke
  //   (EST:ANT-REACH-AHEAD); the farthest levels that 70 % and 50 % of them reached are lines on the price column and over
  //   the hours ahead (only with as many of them as a place needs, TP-2.0 §3), a ladder in the panel;
  // - the window's levels «дошли 70 % / 50 %» (TP-2.0 Ч12) stay, dimmer, named by their condition («если true · W1»),
  //   «пройден» once today's top is at them; the panel says how many of the same sessions ended so (DR held, the pullback
  //   before the top in today's window; EST:ANT-COND-WINDOW).
  // Every number is a passport the server re-derives through the candidate gate (lab/server.py → lab/contract.py::
  // ref_ant_like_now); every word is a registered label of CF:ANT-*. The page's one pass per session (antAhead) is the
  // reference outcome level by level (tests/ant235.py). Never name a variable here after a shared one (tp235.js rule 6).
  const ANT = { on: /(?:^|[#&])ant=1(?:&|$)/.test(location.hash) };
  const ANT_C = '#CDEB6B';
  const antAvail = () => TP.on && !!REVIEW && !!REVIEW.estimands && !!REVIEW.estimands['EST:ANT-REACH-AHEAD'];
  const antOn = () => ANT.on && antAvail();
  const antPct = (p, n) => p.pct == null || !n ? '—' : pct(100 * p.yes_count / n);
  // one member after the cut: the farthest 0.1-SD cell its M5 highs reached before the first hole and before the M5 that
  // closed beyond its own opposite DR (that M5 not counted), and whether a hole came first. For a level k: top >= k — got
  // there; else a hole — unknown (a break could hide in it); else no (the DR broke first or the block ended).
  function antAhead(Fb, m, cut) {
    let top = null, gap = false;
    for (let j = 0; j < Fb.grid.length; j++) {
      const T = Fb.grid[j];
      if (T <= cut || T > Fb.end) continue;
      const q = m.path[j];
      if (q == null) { gap = true; continue; }
      if (q[2] < m.oppv) break;
      if (!gap) { const k = fdiv(10 * q[1], m.w); if (top == null || k > top) top = k; }
    }
    return { top, gap };
  }
  // the state of the layer at today's cut on the family of the screen (P.A), or why there is none
  function antNow(F) {
    const P = F._tp, Fb = P && P.A, today = P && P.today;
    if (!Fb || !Fb.grid || !Fb.r.today) return { why: 'none' };
    const key = Fb.r.snapshot_id + '|' + P.T.r.snapshot_id + '|' + (today ? today.sl + ':' + today.lo + ':' + today.rows.length : '-');
    if (P._ant && P._ant.key === key) return P._ant;
    const out = { key, why: null };
    P._ant = out;
    if (!today) { out.why = 'wait'; return out; }
    const sl = today.sl, wt = Fb.w0t, rows = today.rows, opp = Fb.side === 1 ? Fb.r.today.drL : Fb.r.today.drH;
    const oppv = Fb.d0 * (tk(opp) - Fb.e0t), xt = Math.max(...rows.map(r => r.hi));
    Object.assign(out, { cut: sl, xt, wt, kt: fdiv(10 * xt, wt) });
    if (sl >= Fb.end) { out.why = 'ended'; return out; }
    if (rows.some(r => r.cl < oppv)) { out.why = 'broken'; return out; }
    const W = today.w && P.clock.windows[today.w];
    if (!W) { out.why = 'nowin'; return out; }
    const [b0, b1] = W, set = [];
    for (const m of Fb.M) {
      const pre = [], at = [];
      for (let j = 0; j < Fb.grid.length; j++) if (Fb.grid[j] > m.act && Fb.grid[j] <= sl) { pre.push(m.path[j]); at.push(j); }
      if (!pre.length || pre.some(q => q == null) || pre.some(q => q[2] < m.oppv)) continue;
      let i = 0;
      for (let a = 1; a < pre.length; a++) if (pre[a][0] < pre[i][0]) i = a;
      const b = Math.floor((Fb.grid[at[i]] - 5 - Fb.f) / 15);
      if (b < b0 || b >= b1) continue;
      const xm = Math.max(...pre.map(q => q[1]));
      if (4 * Math.abs(xm * wt - xt * m.w) > m.w * wt) continue;          // the top so far within ¼ of today's (NOW-1.0 M1X)
      set.push(Object.assign({ m }, antAhead(Fb, m, sl)));
    }
    const n = set.length, need = tpNeed(Fb.N), tops = set.map(q => q.top).filter(v => v != null).sort((a, b) => b - a);
    const params = { cut: sl, b0, b1 };
    const reach = k => {
      const yes = set.filter(q => q.top != null && q.top >= k).length, unk = set.filter(q => !(q.top != null && q.top >= k) && q.gap).length;
      return pp(Fb, { estimand: 'EST:ANT-REACH-AHEAD', case_set: 'CS:ANT-LIKE-NOW-1', params: Object.assign({}, params, { k }), event_id: 'X', region_kind: 'level',
        exact_price_bounds: [k, 100000], time_bounds: [sl, Fb.end], start_rule: 'после ' + clk(sl), end_rule: 'до ' + clk(Fb.end), yes_count: yes, unknown_count: unk, no_event_count: n - yes - unk,
        display_scope: 'panel', phrase: lbl('EST:ANT-REACH-AHEAD', 'row', { lvl: sd(k / 10) }), horizon: lbl('FF:PASSPORT-VIEW', 'horizon_after', { t: clk(sl), end: clk(Fb.end) }) });
    };
    // L_q: the farthest cell above today's top that at least ceil(q n / 100) of them reached (the need-th highest top)
    const lvlOf = q => { const k = Math.ceil(q * n / 100); return n && tops.length >= k && tops[k - 1] > out.kt ? tops[k - 1] : null; };
    const L70 = lvlOf(70), L50 = lvlOf(50);
    const yes = set.filter(q => q.m.outcome === 'held' && q.m.R.s === 'known' && Math.floor((q.m.R.t - Fb.f) / 15) >= b0 && Math.floor((q.m.R.t - Fb.f) / 15) < b1).length;
    const unk = set.filter(q => q.m.outcome === 'unknown' || (q.m.outcome === 'held' && q.m.R.s === 'unknown')).length;
    const cond = n ? pp(Fb, { estimand: 'EST:ANT-COND-WINDOW', case_set: 'CS:ANT-LIKE-NOW-1', params, event_id: 'R', region_kind: 'time_band', exact_price_bounds: null,
      time_bounds: [Fb.f + 15 * b0, Fb.f + 15 * b1], start_rule: Fb.from, end_rule: 'до ' + clk(Fb.end), yes_count: yes, unknown_count: unk, no_event_count: n - yes - unk, display_scope: 'panel',
      phrase: lbl('EST:ANT-COND-WINDOW', 'row', { w: TP_NAME[today.w] }), horizon: hzOf(Fb) }) : null;
    // the ladder: every 0.1 SD from the cell above today's top to the farthest one that at least a tenth of them reached,
    // at most 12 rows (a wider step then, the lines' levels always in)
    const tenth = Math.max(1, Math.ceil(n / 10)), kEnd = n && tops.length >= tenth ? Math.max(out.kt + 1, tops[tenth - 1]) : out.kt + 1, step = Math.max(1, Math.ceil((kEnd - out.kt) / 12));
    const ks = [];
    for (let k = out.kt + 1; k <= kEnd; k += step) ks.push(k);
    for (const k of [L70, L50]) if (k != null && !ks.includes(k)) ks.push(k);
    ks.sort((a, b) => a - b);
    Object.assign(out, { b0, b1, w: today.w, n, need, step, cond, ladder: n ? ks.map(k => ({ k, p: reach(k) })) : [],
      lines: n >= need ? [[70, L70], [50, L50]].filter(([, k]) => k != null).map(([q, k]) => ({ q, k, p: reach(k) })) : [], L70, L50 });
    return out;
  }
  // the price column (app.js::drawProjRX), instead of tpReachMarks while the layer is on: the window's levels named by their
  // condition and dimmer, «пройден» once today's top is at them; then the layer's own lines
  function antMarks(c, F, A_, top0, bot0) {
    const s = antNow(F), w = F._tp.w, used = [];
    // a pair of labels never covers another: the line stays at its level, its words move to the nearest free place
    const place = y => {
      for (const dy of [0, 24, -24, 48, -48, 72, -72]) {
        const m = y + dy, a = m - 13, b = m + 12;
        if (a < top0 - 30 || b > bot0 + 14 || used.some(([u0, u1]) => a < u1 && b > u0)) continue;
        used.push([a, b]); return m;
      }
      return y;
    };
    const two = (y0, a, b, col, aa, ab) => {
      const y = place(y0);
      c.font = '700 9.5px ' + FONT; c.textBaseline = 'bottom'; c.fillStyle = rgba(col, aa);
      c.fillText(a, A_.x + A_.w - c.measureText(a).width - 6, y - 1);
      c.font = '600 8.5px ' + FONT; c.textBaseline = 'top'; c.fillStyle = rgba(col, ab);
      c.fillText(b, A_.x + A_.w - c.measureText(b).width - 6, y + 1);
    };
    for (const L of tpLevels(F)) {
      const y = Math.round(V.Y(F.u2p(L.k / 10))) + 0.5;
      if (y < top0 || y > bot0) continue;
      const passed = s.xt != null && 10 * s.xt >= L.k * s.wt;
      c.save(); c.strokeStyle = rgba(cfg.X, passed ? 0.3 : 0.5); c.lineWidth = 1; c.setLineDash(L.q === 70 ? [] : [3, 3]);
      c.beginPath(); c.moveTo(A_.x + 2, y); c.lineTo(A_.x + A_.w - 2, y); c.stroke(); c.restore();
      const cond = lbl('EST:ANT-COND-WINDOW', 'cond', { w: TP_NAME[w] || '' });
      two(y, 'дошли ' + L.q + ' % · ' + sd(L.k / 10), passed ? lbl('EST:ANT-COND-WINDOW', 'passed') + ' · ' + cond : cond, cfg.X, passed ? 0.45 : 0.7, passed ? 0.4 : 0.6);
    }
    for (const L of s.lines || []) {
      if (L.p.pct == null) continue;                                     // a withheld number draws no line
      const y = Math.round(V.Y(F.u2p(L.k / 10))) + 0.5;
      if (y < top0 || y > bot0) continue;
      c.save(); c.strokeStyle = rgba(ANT_C, 0.9); c.lineWidth = 1.3; c.setLineDash(L.q === 70 ? [] : [4, 3]);
      c.beginPath(); c.moveTo(A_.x + 2, y); c.lineTo(A_.x + A_.w - 2, y); c.stroke(); c.restore();
      two(y, lbl('EST:ANT-REACH-AHEAD', 'line_q', { q: L.q, lvl: sd(L.k / 10) }), lbl('EST:ANT-REACH-AHEAD', 'line_when', { cut: clk(s.cut) }), ANT_C, 1, 0.8);
    }
  }
  // over the hours ahead: the layer's lines from the cut to the block end, quiet, with their share at the cut
  function antChart(c, ctx) {
    const F = ctx.F, s = antNow(F);
    if (!s.lines || !s.lines.length) return;
    const x0 = Math.max(0, Math.round(V.X(s.cut))), x1 = Math.min(V.plot.w, Math.round(V.X(F._tp.A.end)));
    if (x1 <= x0) return;
    for (const L of s.lines) {
      if (L.p.pct == null) continue;
      const y = Math.round(V.Y(F.u2p(L.k / 10))) + 0.5;
      if (y < 0 || y > V.plot.h) continue;
      c.save(); c.strokeStyle = rgba(ANT_C, 0.55); c.lineWidth = 1; c.setLineDash(L.q === 70 ? [6, 4] : [2, 4]);
      c.beginPath(); c.moveTo(x0, y); c.lineTo(x1, y); c.stroke(); c.restore();
      c.font = '700 9px ' + FONT; c.textBaseline = 'bottom'; c.fillStyle = rgba(ANT_C, 0.85);
      c.fillText(L.q + ' %', x0 + 4, y - 1);
    }
  }
  // the panel: first under the DR outcome while the layer is on (panel.js)
  function antPanel(F, ctx) {
    const s = antNow(F), out = [], E = 'EST:ANT-REACH-AHEAD', CW = 'EST:ANT-COND-WINDOW', cut = s.cut != null ? clk(s.cut) : clk(sliceOf(ctx));
    out.push('<div class="p21-h second"><span title="' + esc(lbl(E, 'head_title', { cut })) + '" style="color:' + ANT_C + '">' + lbl(E, 'head', { cut }) + '</span><span>' + lbl(E, 'head_r') + '</span></div>');
    if (s.why) return out.join('') + '<div class="p21-note">' + lbl(E, s.why === 'none' ? 'wait' : s.why) + '</div>';
    if (!s.n) return out.join('') + '<div class="p21-note">' + lbl(E, 'none', { cut }) + '</div>';
    const W = F._tp.clock.windows[s.w];
    out.push('<div class="p21-note">' + lbl(E, 'like', { cut, n: s.n, w: TP_NAME[s.w], t0: clk(F.f + 15 * W[0]), t1: clk(F.f + 15 * W[1]), top: sd(Math.round(100 * s.xt / s.wt) / 100) }) +
      (s.n < 20 ? ' · ' + lbl(E, 'few', { n: s.n }) : '') + (s.step > 1 ? ' · ' + lbl(E, 'step', { step: num(s.step / 10, 1) }) : '') + '</div>');
    for (const r of s.ladder) {
      const p = r.p, line = s.lines.find(L => L.k === r.k), tt = lbl(E, 'row_title', { n: s.n, cut, lvl: sd(r.k / 10), yes: p.yes_count, no: p.no_event_count, unknown: p.unknown_count });
      out.push('<div class="p21-link mc" style="cursor:default" title="' + esc(tt) + '">' + prow('<span>' + lbl(E, 'row', { lvl: sd(r.k / 10) }) + (line ? ' <i style="color:' + ANT_C + '">· ' + line.q + ' %</i>' : '') + '</span>',
        line ? '<span style="color:' + ANT_C + '">' + antPct(p, s.n) + '</span>' : antPct(p, s.n)) + '</div>');
    }
    const lv = q => { const k = q === 70 ? s.L70 : s.L50; return k != null ? lbl(E, 'level', { q, lvl: sd(k / 10) }) : lbl(E, 'level_none', { q }); };
    out.push('<div class="p21-note">' + lv(70) + ' · ' + lv(50) + (s.n < s.need ? ' · ' + lbl(E, 'thin', { need: s.need }) : '') + '</div>');
    // the window's own levels (Ч12) and how often days like today ended as those levels assume
    const lvls = tpLevels(F), name = TP_NAME[F._tp.w] || '';
    out.push('<div class="p21-note">' + (lvls.length ? lbl(CW, 'note', { w: name, levels: lvls.map(L => L.q + ' % ' + sd(L.k / 10)).join(' · ') }) : lbl(CW, 'note_none', { w: name })) + '</div>');
    if (s.cond) {
      const p = s.cond;
      out.push('<div class="p21-link mc" style="cursor:default" title="' + esc(lbl(CW, 'row_title', { w: TP_NAME[s.w], n: s.n, cut, yes: p.yes_count, no: p.no_event_count, unknown: p.unknown_count })) + '">' +
        prow('<span>' + lbl(CW, 'row', { w: TP_NAME[s.w] }) + '</span>', antPct(p, s.n)) + '</div>');
    }
    out.push('<div class="p21-note" style="opacity:.8">' + lbl(E, 'check') + '</div>');
    return out.join('');
  }
  // tests/ant235_page.mjs
  function antState(F) {
    const s = F && F._tp && antOn() ? antNow(F) : null;          // nothing is counted while the layer is off
    return { avail: antAvail(), on: antOn(), why: s ? s.why : antOn() ? 'no-tp' : 'off', cut: s && s.cut, n: s && s.n, need: s && s.need, w: s && s.w, kt: s && s.kt,
      L70: s && s.L70, L50: s && s.L50, lines: s && s.lines ? s.lines.map(L => ({ q: L.q, k: L.k, yes: L.p.yes_count, unknown: L.p.unknown_count, no: L.p.no_event_count, held: L.p.pct == null })) : [],
      ladder: s && s.ladder ? s.ladder.map(r => ({ k: r.k, yes: r.p.yes_count, unknown: r.p.unknown_count, no: r.p.no_event_count })) : [],
      cond: s && s.cond ? { yes: s.cond.yes_count, unknown: s.cond.unknown_count, no: s.cond.no_event_count } : null };
  }
