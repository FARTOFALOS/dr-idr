  // ---------- DR-LAB-TP-1.1 on 23.5: the semantic core of 03.11.2026 on the same drawing ----------
  // The core: the project «dr», document «DR-LAB-TP-1.1 · Смысловое ядро созвездий» (docs/DR-LAB-23-5-TP.md here). The
  // family of the screen F (all its sessions, the scene's family) keeps only the DR outcome, one 100 %. Everything else
  // is built from T, the family's sessions whose DR held (the author's «only true scenarios»; lab/tp11.py, flag ':held'):
  // - the band (time): the clock of T's pullbacks R before the top (per 15 minutes, share of |T|), every bunch drawn
  //   brighter with its share, the lines of the median and of the 70 % mark, and in the place of the zone capsules the
  //   windows: W1 (first bunch → median), W2 (median → 70 %), «позже» after 70 % and «до окна» before W1; X is the selected
  //   window's sessions in the same manner (operator 04.11: «так же самое можно и X показывать»): its bunches brighter with
  //   their shares and its median and 70 % lines (the median is the author's «max extension median time»), its last 15
  //   minutes apart («ход не кончился до закрытия», never a place);
  // - the price column and the constellations: the sessions of one window T_W (flag ':held:tw=W1'), its price bands as
  //   the places of R, the price bands of all their tops over 0.2-SD cells as the places of X (the author's «cluster of
  //   extension… next big cluster»; zone rule TP_BANDS, tp-bands-3; core 1.4), under the mouse «дошли до» its lower edge;
  //   at rest W1, a window under the mouse on the band shows its sessions, a click fixes it.
  // - the other windows' places of R (operator 05.11), always on the chart in their own hours, quieter and named by their
  //   window («W2 · R1»), each its share of its own window; a window under the mouse marks its peak 15 minutes and says
  //   when inside it (tpWinPeak, tpWinTip).
  // The drawing and the colours of 23.5 stay as they were (operator 03.11: «все ценовые, все цветовые, как у нас были»).
  // «Сейчас» (NOW-1.0) stays on the whole family F: its move to T is a separate task (core §6).
  // DR-LAB-TP-2.0 (operator 10.11: «реализуй спецификацию (на все шесть вопросов — ответ — да»; meaning/25-tp-2-0-specifikaciya.md):
  // - one measure per colour: an amber number (a bunch, a window, a place of R, the rows «без отката до вершины» and «вне
  //   мест») is the share of the WHOLE family F (EST:TP-MASS-R on the family of the screen: DR held and R before the top in
  //   the region); the share inside the window is in the inspector (C1); a blue number is «дошли до» among the window's
  //   sessions (EST:B-RX-BAND-X from the place's near edge), «кончили здесь» in the inspector;
  // - only mass: a bunch or a place needs max(4, ceil(0.05 N)) sessions, N of the whole family (server and page alike);
  // - the price column marks the levels 70 % and 50 % of the window's sessions reached (tpReachMarks);
  // - the window on screen follows today: a pinned window, else the window of today's deepest point so far (tpToday),
  //   else W1;
  // - the summary says how the DR ended for the family's sessions that by this clock had gone as deep (tpDepthRow,
  //   EST:TP-DR-AT-DEPTH on CS:TP-DEPTH-AT-CUT-1).
  // T and T_W are named as what they are (CS:TP-TRUE-1, CS:TP-WINDOW-1: subgroups chosen by their future; C1 words).
  // '#tp=0' in the address shows the previous meaning (the table of 30.10) for comparison, and so does '#cells=1' (the layer
  // «Клетки» of 30.10 is a view of that table: its shortcut «DR Lab 23.5 · клетки» keeps opening it); '#tpw=W2' fixes a window.
  const TP = { on: !/(?:^|[#&])(?:tp=0|cells=1)(?:&|$)/.test(location.hash), pin: (/(?:^|[#&])tpw=(BEFORE|W1|W2|LATE)(?:&|$)/.exec(location.hash) || [])[1] || null, last: null };
  const TP_WINDOWS = ['BEFORE', 'W1', 'W2', 'LATE'];
  const TP_NAME = { BEFORE: 'до окна', W1: 'W1', W2: 'W2', LATE: 'позже' };
  const tpOn = () => TP.on;
  const tpFlags = w => ':rpre:held' + (w ? ':tw=' + w : '');
  const tpKey = (D, s, w) => famKey(D, s, 'conf') + '|tp|' + (w || 'T');
  function tpRequest(fk, s, w) {
    if (A.pending.has(fk)) return;
    A.pending.add(fk);
    const at = s.live ? Math.floor(NOW / 5) * 5 : s.obs;
    fetch('/api/d24/family?instrument=' + A.inst + '&session=' + s.k + '&at=' + at + (A.src === 'hist' ? '&date=' + A.date : '') + '&view=conf' + (st.scope === 'all' ? ':all' : '') + tpFlags(w))
      .then(r => r.json()).then(r => { r._fk = fk; r._ctx = 'tp|' + (A.respSeq = (A.respSeq || 0) + 1); A.fams.set(fk, r); if (A.fams.size > 64) A.fams.delete(A.fams.keys().next().value); })
      .catch(() => A.fams.set(fk, { status: 'error', message: 'Локальный сервер не ответил' }))
      .finally(() => { A.pending.delete(fk); redraw(true); });
  }
  // the rule of lab/tp11.py, written again on the page: the page counts T's clock from the members it received (the server
  // keeps its own to select T_W; the same definitions twice: a window family whose sessions are not the page's window is
  // withheld, tpCheck)
  const tpNeed = n => Math.max(4, Math.ceil(n / 20));
  function tpRegions(c) {
    const n = c.length, higher = (j, i) => c[j] > c[i] || (c[j] === c[i] && j < i), keep = [], out = [];
    const apex = [];
    for (let i = 0; i < n; i++) if (c[i] > 0 && (i === 0 || c[i] >= c[i - 1]) && (i === n - 1 || c[i] >= c[i + 1]) && !(i > 0 && c[i - 1] === c[i])) apex.push(i);
    for (const i of apex) {
      const base = [];
      for (const step of [-1, 1]) {
        let j = i + step, low = c[i];
        while (j >= 0 && j < n && !higher(j, i)) { low = Math.min(low, c[j]); j += step; }
        base.push(j >= 0 && j < n ? low : 0);
      }
      if (2 * (c[i] - Math.max(...base)) >= c[i]) keep.push(i);
    }
    const lowest = (a, b) => { let m = a; for (let j = a; j <= b; j++) if (c[j] < c[m]) m = j; return m; };
    keep.forEach((i, a) => {
      const left = a === 0 ? 0 : lowest(keep[a - 1], i) + 1, right = a === keep.length - 1 ? n - 1 : lowest(i, keep[a + 1]) - 1;
      let lo = i, hi = i;
      while (lo - 1 >= left && 2 * c[lo - 1] >= c[i]) lo--;
      while (hi + 1 <= right && 2 * c[hi + 1] >= c[i]) hi++;
      out.push([lo, hi, i]);
    });
    return out;
  }
  const tpQuant = (ts, a, b) => { const K = ts.length; if (!K) return null; const k = Math.floor((a * K + b - 1) / b); return { t: ts[k - 1], k, K }; };
  function tpMarks(M, ev, f) {
    const ts = M.filter(m => m[ev].s === 'known').map(m => m[ev].t).sort((a, b) => a - b), cells = new Map();
    for (const t of ts) { const b = Math.floor((t - f) / 15); cells.set(b, (cells.get(b) || 0) + 1); }
    return { ts, cells: [...cells.entries()].sort((a, b) => a[0] - b[0]), unknown: M.filter(m => m[ev].s === 'unknown').length, none: M.filter(m => m[ev].s === 'none').length };
  }
  function tpClock(F, NB) {
    const f = F.f, win = Math.floor((F.r.key.window[0] - f) / 15), bLo = win, bHi = Math.floor((F.end - 5 - f) / 15), N = F.N, m = tpMarks(F.M, 'R', f);
    const at = new Map(m.cells), c = [];
    for (let b = bLo; b <= bHi; b++) c.push(at.get(b) || 0);
    const bunches = [];
    for (const [lo, hi, top] of tpRegions(c)) { let n = 0; for (let j = lo; j <= hi; j++) n += c[j]; if (n >= tpNeed(NB)) bunches.push({ b0: bLo + lo, b1: bLo + hi + 1, n, peak: bLo + top }); }
    const median = tpQuant(m.ts, 1, 2), p70 = tpQuant(m.ts, 7, 10), W = { BEFORE: null, W1: null, W2: null, LATE: null };
    if (median) {
      const bm = Math.floor((median.t - f) / 15), bp = Math.floor((p70.t - f) / 15), first = bunches.find(u => u.b0 <= bm), s0 = first ? first.b0 : bLo;
      W.W1 = [s0, bm + 1];
      if (s0 > bLo) W.BEFORE = [bLo, s0];
      if (bp > bm) W.W2 = [bm + 1, bp + 1];
      if (bp < bHi) W.LATE = [bp + 1, bHi + 1];
    }
    return { version: 'tp-2.0', N, known: m.ts.length, unknown: m.unknown, none: m.none, cells: m.cells, bunches, median, p70, windows: W, need: tpNeed(NB), n_base: NB, step: 15, range: [bLo, bHi + 1] };
  }
  // the family of a window: every member's R in the window that the page counted on T, as many as T has there; its own X
  // marks counted here (the response publishes no clock, lab/scene24.py: its numbers have no declared meaning in SC-1.1)
  function tpCheck(G, w, T) {
    if (!w) return null;
    const W = T.tpc.windows[w];
    if (!W || G.M.some(q => q.R.s !== 'known' || Math.floor((q.R.t - G.f) / 15) < W[0] || Math.floor((q.R.t - G.f) / 15) >= W[1])) return 'сессии окна ' + TP_NAME[w];
    if (G.N !== tpCount(T.tpc, W[0], W[1])) return 'число сессий окна ' + TP_NAME[w];
    return null;
  }
  // the clock of the window's tops X (the bunch rule of lab/tp11.py): bunches over the block without its last 15 minutes,
  // the median, the tops of the last 15 minutes apart (a move cut by the close: never a bunch, never a place)
  function tpXClock(G, NB) {
    const f = G.f, bLo = Math.floor((G.r.key.window[0] - f) / 15), bHi = Math.floor((G.end - 5 - f) / 15), m = tpMarks(G.M, 'X', f), at = new Map(m.cells), c = [];
    for (let b = bLo; b < bHi; b++) c.push(at.get(b) || 0);
    const bunches = [];
    for (const [lo, hi, top] of tpRegions(c)) { let n = 0; for (let j = lo; j <= hi; j++) n += c[j]; if (n >= tpNeed(NB)) bunches.push({ b0: bLo + lo, b1: bLo + hi + 1, n, peak: bLo + top }); }
    return { cells: m.cells, bunches, median: tpQuant(m.ts, 1, 2), close: at.get(bHi) || 0, bLo, bHi, need: tpNeed(NB) };
  }
  // every place of X is a price band of the window's tops on the 0.2-SD grid (lab/tp11.py::xbands) and never holds a top
  // of the last 15 minutes; the contract re-derives the bands themselves (ref_tp_xbands)
  function tpXCheck(G) {
    const xc = G.tpxc, Z = (G.zones.X || { zones: [] }).zones;
    for (const z of Z)
      if (z.cell_mask.some(q => q[1] >= xc.bHi || q[0] < z.price_low || q[0] >= z.price_high) || z.price_low % 2 || z.price_high % 2) return 'места вершины ' + z.label;
    return null;
  }
  function tpXMarks(G) { const m = tpMarks(G.M, 'X', G.f); return { median: tpQuant(m.ts, 1, 2), p70: tpQuant(m.ts, 7, 10), known: m.ts.length, unknown: m.unknown, none: m.none, cells: m.cells }; }
  // one family of TP: its response checked like the family of the screen (snapOf), then built by the same buildSnap
  const TP_KEY = ['instrument', 'session', 'weekday', 'direction', 'event', 'window', 'cutoff', 'scope'];
  function tpSnap(D, s, w, T, Fb) {          // Fb: the family of the screen (never name it A: A is the page's state)
    const fk = tpKey(D, s, w), r = A.fams.get(fk);
    if (!r) { tpRequest(fk, s, w); return null; }
    if (r.status !== 'ok' || r.view !== 'conf' || (r.key.scope || 'weekday') !== st.scope || r.key.r_event !== 'R_BEFORE_X' || r.key.cohort !== 'HELD' ||
      r.key.zone_rule !== (w ? 'TP_BANDS' : 'TP_NONE') || (r.key.tp_window || null) !== (w || null) || !r.today || r.today.c0 !== s.conf || r.today.side !== s.side) return null;
    if (r._refused === undefined) {
      r._refused = regFault(r.contract) || (!r.contract.bundles ? 'конверт контракта без опубликованных чисел' : null);
      if (r._refused) kViolate(r._refused, null, r._ctx);
      else if (r.contract.status !== 'CONFORMANT') kViolate('сервер: ' + ((r.contract.violations || []).map(v => v.message).join('; ') || r.contract.status), null, r._ctx);
    }
    if (r._refused) return null;
    if (w && !T) return null;
    if (!w && !Fb) return null;                                  // T's threshold is counted from N of the whole family
    if (!r._F) {
      const B = w ? T : Fb;
      if (TP_KEY.some(k => JSON.stringify(r.key[k]) !== JSON.stringify(B.r.key[k]))) { r._refused = 'набор не из той же семьи'; kViolate(r._refused, null, r._ctx); return null; }
      const G = buildSnap(r, s, 'conf');
      G.req.view = 'conf' + (r.key.scope === 'all' ? ':all' : '') + tpFlags(w);
      G.tpw = w || null;
      const NB = w ? T.tpc.n_base : Fb.N;                      // TP-2.0 §3: the mass threshold from N of the whole family
      if (w) { G.tpx = tpXMarks(G); G.tpxc = tpXClock(G, NB); } else G.tpc = tpClock(G, NB);   // T: its clock; T_W: the clock of its tops
      const bad = G.held.has('family') ? 'счёт страницы не совпал с пакетом сервера (' + G.mismatch.join(', ') + ')' : tpCheck(G, w, T) || (w ? tpXCheck(G) : null);
      if (bad) { r._refused = G.held.has('family') ? bad : 'страница пересчитала другое: ' + bad; kViolate(r._refused, null, r._ctx); return null; }
      r._F = G;
    }
    return r._F;
  }
  // the view of the screen: the window family T_W with T and F at hand. A window under the mouse on the band (or its row in
  // the panel is clicked) shows its sessions; at rest the fixed window, else W1
  function tpView(D, s, F0, cx) {
    if (!F0) return null;
    const T = tpSnap(D, s, null, null, F0);
    if (!T) return null;
    const tp = T.tpc, h = st.hover, has = w => !!(w && tp.windows[w]);
    for (const w of TP_WINDOWS) if (has(w)) tpSnap(D, s, w, T);            // every window's family at once: a hover switches without waiting
    // TP-2.0 §6.3: a pinned window; else the window of today's deepest point so far (it becomes the pullback before the
    // top if the move makes a new top); else W1
    const today = tpToday(F0, Object.assign({ D }, cx || {}), tp), rest = has(TP.pin) ? TP.pin : today && has(today.w) ? today.w : has('W1') ? 'W1' : TP_WINDOWS.find(has) || null;
    const want = h && h.k === 'tpwin' && h.src === 'strip' && has(h.id) ? h.id : rest;
    let w = want, G = w ? tpSnap(D, s, w, T) : T;
    if (!G && w !== rest) { w = rest; G = w ? tpSnap(D, s, w, T) : T; }
    if (!G) return null;
    if (TP.last !== w) { TP.last = w; if (st.pin && ['pt', 'zone', 'mcell'].includes(st.pin.k)) st.pin = null; }
    const why = has(TP.pin) && w === TP.pin ? 'pin' : today && w === today.w ? 'today' : 'none';
    const key = G.r.snapshot_id + '|' + T.r.snapshot_id + '|' + F0.r.snapshot_id + '|' + why + '|' + (today ? today.T + ':' + today.lo : '');
    if (G._tpv && G._tpv._tpKey === key) return G._tpv;
    return (G._tpv = Object.assign({}, G, { _tp: { T, A: F0, clock: tp, w, x: w ? G.tpx : null, xc: w ? G.tpxc : null, today, why }, _tpKey: key }));
  }
  // today's deepest point against the activation so far, from today's closed M5 after it (TP-2.0 §2.6, point D): its
  // level u, the open of the first M5 that reached it and the window of T's clock it falls in; none while the prefix is
  // incomplete or before the first M5 after the activation
  function tpToday(F0, ctx, tp) {
    if (!ctx.D || ctx.obs == null) return null;
    const rows = todayRows(F0, ctx), sl = sliceOf(ctx);
    if (!rows.length || rows.length !== Math.max(0, (sl - F0.act0) / 5)) return null;
    let j = 0;
    for (let i = 1; i < rows.length; i++) if (rows[i].lo < rows[j].lo) j = i;
    const t = rows[j].T - 5, b = Math.floor((t - F0.f) / 15), w = tp ? TP_WINDOWS.find(k => tp.windows[k] && b >= tp.windows[k][0] && b < tp.windows[k][1]) || null : null;
    return { lo: rows[j].lo, T: rows[j].T, t, u: rows[j].lo / F0.w0t, w, sl, rows };
  }
  // what the panel says while a TP family is missing or refused
  function tpStatus(ctx) {
    const s = ctx.s, rT = A.fams.get(tpKey(ctx.D, s, null));
    if (!rT) return 'Собираю true-сессии семьи…';
    if (rT.status !== 'ok') return (rT.message || rT.status) + '';
    if (rT._refused) return 'Числа не публикуются: ' + rT._refused;
    const w = TP.last || 'W1', rW = A.fams.get(tpKey(ctx.D, s, w));
    if (!rW) return 'Собираю сессии окна ' + TP_NAME[w] + '…';
    if (rW.status !== 'ok') return (rW.message || rW.status) + '';
    if (rW._refused) return 'Числа не публикуются: ' + rW._refused;
    return 'Собираю семью…';
  }
  const tpWinT = (F, w) => { const W = F._tp.clock.windows[w]; return W ? [F.f + 15 * W[0], F.f + 15 * W[1]] : null; };
  const tpCount = (tp, b0, b1) => tp.cells.filter(([b]) => b >= b0 && b < b1).reduce((s, q) => s + q[1], 0);
  // ---------- TP-2.0: the mass of the whole family (EST:TP-MASS-R on the family of the screen F, its N) ----------
  // the family's sessions whose DR held and whose R before the top lies in the region (cells; null = open); part NO_R: DR
  // held, R before the top not determined. Verified by the server (lab/contract.py::ref_tp_mass) like any passport.
  function tpMass(F, o) {
    const Fb = F._tp && F._tp.A;
    if (!Fb) return { pct: null, N: 0, yes_count: 0, unknown_count: 0 };
    const inb = (x, lo, hi) => (lo == null || x >= lo) && (hi == null || x < hi), nb = o.not_bands || [];
    const part = o.part || 'KNOWN', params = { k0: o.k0 == null ? null : o.k0, k1: o.k1 == null ? null : o.k1, b0: o.b0 == null ? null : o.b0, b1: o.b1 == null ? null : o.b1, part, not_bands: nb };
    const n = part === 'NO_R' ? Fb.M.filter(m => m.outcome === 'held' && m.R.s !== 'known').length
      : Fb.ev.R.pts.filter(q => q.m.outcome === 'held' && inb(q.k, params.k0, params.k1) && inb(q.b, params.b0, params.b1) && !nb.some(z => q.k >= z[0] && q.k < z[1])).length;
    const where = part === 'NO_R' ? '' : (params.b0 != null ? 'в ' + clk(Fb.f + 15 * params.b0) + '–' + clk(Fb.f + 15 * params.b1) : '') + (params.k0 != null ? ' · ' + band(params.k0, params.k1) + ' SD' : '') + (nb.length ? ' · вне мест' : '');
    return pp(Fb, { estimand: 'EST:TP-MASS-R', params, event_id: 'R', region_kind: part === 'NO_R' ? 'unknown' : params.k0 != null ? 'joint' : 'time_band',
      exact_price_bounds: params.k0 != null ? [params.k0, params.k1] : null, time_bounds: params.b0 != null ? [Fb.f + 15 * params.b0, Fb.f + 15 * params.b1] : null,
      start_rule: Fb.from, end_rule: 'до ' + clk(Fb.end), yes_count: n, display_scope: 'tp',
      phrase: lbl('EST:TP-MASS-R', part === 'NO_R' ? 'phrase_none' : 'phrase', { where }), horizon: hzOf(Fb) });
  }
  // the share of a stretch of T's clock: the family's sessions whose DR held and whose R before the top was in it (TP-2.0
  // Ч2, Ч3); the same count as T's clock or the number is withheld
  function tpShare(F, b0, b1) {
    const p = tpMass(F, { b0, b1 });
    if (p.pct != null && p.yes_count !== tpCount(F._tp.clock, b0, b1)) kViolate('the family mass of ' + clk(F.f + 15 * b0) + '–' + clk(F.f + 15 * b1) + ' is not T\'s count', p);
    return p;
  }
  // a place of R of window w: its share of the whole family (TP-2.0 Ч4); the same sessions as the place or withheld
  function tpMassPlace(F, w, z) {
    const W = F._tp.clock.windows[w];
    if (!W) return { pct: null, N: 0, yes_count: 0, unknown_count: 0 };
    const p = tpMass(F, { k0: z.price_low, k1: z.price_high, b0: W[0], b1: W[1] });
    if (p.pct != null && p.yes_count !== z.n_zone) kViolate('the family mass of the place ' + z.label + ' is not its sessions', p);
    return p;
  }
  // the reach of a place of X: of the window's sessions, those whose top got to its near edge or further (EST:B-RX-BAND-X
  // from the edge up; a top of the last 15 minutes reached its level too)
  function tpReachPass(F, z) {
    const D = F.ev.X, n = D.pts.filter(q => q.k >= z.price_low).length;
    return pp(F, { estimand: 'EST:B-RX-BAND-X', params: { k0: z.price_low, k1: 100000 }, event_id: 'X', region_kind: 'price_band', exact_price_bounds: [z.price_low, 100000], time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: n, unknown_count: D.unknown, no_event_count: D.none, display_scope: 'inspector', phrase: lbl('EST:B-RX-BAND-X', 'phrase', { name: F.names.X.toLowerCase(), ev: 'X', what: F.what.X, band: '≥ ' + sd(z.price_low / 10) }), horizon: hzOf(F) });
  }
  // the number and the name a place carries on the chart (app.js::zoneMark): R — the family share; X — «дошли»
  function tpMarkPass(F, ev, z) {
    if (ev === 'R') return { p: tpMassPlace(F, F._tp.w, z), name: z.label };
    return { p: tpReachPass(F, z), name: z.label + ' · дошли' };
  }
  // the inspector's head of a place (app.js::zoneTip): F is the family on screen (or another window's, tagged _tpg)
  function tpZoneHead(F, ev, z, pw) {
    const S = F._tp ? F : F._tpg.F, w = F._tp ? S._tp.w : F._tpg.w, W = S._tp.clock.windows[w], nw = F.N;
    const win = W ? clk(S.f + 15 * W[0]) + '–' + clk(S.f + 15 * W[1]) : '', inW = 'из ' + nw + ' сессий с откатом в ' + win + ' (DR устоял)';
    if (ev === 'R') {
      const p = tpMassPlace(S, w, z);
      return '<div class="ibig" style="color:#F0F5FF">' + ppTxt(p) + '<span>семьи</span></div>' +
        '<div class="is">' + lbl('EST:TP-MASS-R', 'place', { n: p.yes_count, N: p.N, pct: ppTxt(p), t0: win.split('–')[0], t1: win.split('–')[1], band: band(z.price_low, z.price_high) }) + '</div>' +
        '<div class="ir">' + inW + ' — в этой полосе ' + z.n_zone + '<b>' + ppTxt(pw) + '</b></div>';
    }
    const r = tpReachPass(F, z);
    return '<div class="ibig" style="color:#F0F5FF">' + ppTxt(r) + '<span>дошли до ' + sd(z.price_low / 10) + ' SD</span></div>' +
      '<div class="is" style="color:' + cfg.X + '">дошли до ' + sd(z.price_low / 10) + ' SD: ' + r.yes_count + ' ' + inW + '</div>' +
      '<div class="ir">ход кончился в этой полосе: ' + z.n_zone + ' из ' + nw + '<b>' + ppTxt(pw) + '</b></div>';
  }
  // ---------- TP-2.0 Ч12: the levels the window's sessions reached, 70 % and 50 % ----------
  // L_q: the highest level of the 0.1-SD grid that at least ceil(q |T_W|) of the window's sessions reached (their top at it
  // or further; EST:B-RX-BAND-X from L up)
  function tpLevels(F) {
    const N = F.N, ks = F.ev.X.pts.map(q => q.k).sort((a, b) => b - a), out = [];
    if (!N) return out;
    for (const [q, den] of [[70, 100], [50, 100]]) {
      const need = Math.ceil(q * N / den);
      if (ks.length < need) continue;
      const k = ks[need - 1];                                      // the need-th highest cell: that many tops at k or above
      out.push({ q, k, p: tpReachPass(F, { price_low: k }) });
    }
    return out;
  }
  function tpReachMarks(c, F, A_, top0, bot0) {
    for (const L of tpLevels(F)) {
      const y = Math.round(V.Y(F.u2p(L.k / 10))) + 0.5;
      if (y < top0 || y > bot0) continue;
      c.save(); c.strokeStyle = rgba(cfg.X, 0.8); c.lineWidth = 1; c.setLineDash(L.q === 70 ? [] : [3, 3]);
      c.beginPath(); c.moveTo(A_.x + 2, y); c.lineTo(A_.x + A_.w - 2, y); c.stroke(); c.restore();
      c.font = '700 9.5px ' + FONT; c.textBaseline = 'bottom'; c.fillStyle = rgba(cfg.X, 0.95);
      const t = 'дошли ' + L.q + ' % · ' + sd(L.k / 10);
      c.fillText(t, A_.x + A_.w - c.measureText(t).width - 6, y - 1);
    }
  }
  // ---------- TP-2.0 Ч13: how the DR ended for the family's sessions that by this clock had gone as deep ----------
  // CS:TP-DEPTH-AT-CUT-1: eligible at the cut as in «Сейчас» (own activation before it, a complete prefix, the DR still
  // whole) and their deepest point against the activation up to the cut at today's or deeper (exact, integers);
  // EST:TP-DR-AT-DEPTH, one passport per category, re-derived by the server (lab/contract.py::ref_tp_depth_set)
  function tpDepth(F, ctx) {
    const Fb = F._tp.A, today = F._tp.today;
    if (!Fb || !today || !Fb.grid) return null;
    const sl = today.sl, rt = today.lo, wt = Fb.w0t, set = [];
    for (const m of Fb.M) {
      const pre = [];
      for (let j = 0; j < Fb.grid.length; j++) if (Fb.grid[j] > m.act && Fb.grid[j] <= sl) pre.push(m.path[j]);
      if (!pre.length || pre.some(q => q == null) || pre.some(q => q[2] < m.oppv)) continue;
      if (Math.min(...pre.map(q => q[0])) * wt <= rt * m.w) set.push(m);
    }
    const cnt = { HELD: set.filter(m => m.outcome === 'held').length, BROKEN: set.filter(m => m.outcome === 'broken').length, UNKNOWN: set.filter(m => m.outcome === 'unknown').length, ALL: set.length };
    const pass = {};
    for (const cat of ['ALL', 'HELD', 'BROKEN', 'UNKNOWN'])
      pass[cat] = pp(Fb, { estimand: 'EST:TP-DR-AT-DEPTH', case_set: 'CS:TP-DEPTH-AT-CUT-1', params: { cut: sl, category: cat }, event_id: 'DR', region_kind: 'category', start_rule: Fb.from, end_rule: 'до ' + clk(Fb.end),
        yes_count: cnt[cat], display_scope: 'panel', phrase: '', horizon: hzOf(Fb) });
    return { cut: sl, u: today.u, D: cnt.ALL, held: cnt.HELD, broken: cnt.BROKEN, unknown: cnt.UNKNOWN, pass };
  }
  function tpDepthRow(F, ctx) {
    const d = tpDepth(F, ctx);
    if (!d) return '';
    const held = ['ALL', 'HELD', 'BROKEN', 'UNKNOWN'].some(k => d.pass[k].violation) ? '—' : null, cut = clk(d.cut);
    if (!d.D) return '<div class="p21-note" title="' + esc(lbl('EST:TP-DR-AT-DEPTH', 'title')) + '">' + lbl('EST:TP-DR-AT-DEPTH', 'none', { cut }) + '</div>';
    const txt = held || lbl('EST:TP-DR-AT-DEPTH', 'row', { cut, u: sd(Math.round(100 * d.u) / 100), D: d.D, held: d.held, broken: d.broken }) + (d.unknown ? lbl('EST:TP-DR-AT-DEPTH', 'row_unknown', { unknown: d.unknown }) : '');
    const hp = held ? '—' : pct(100 * d.held / d.D);
    return '<div class="p21-h second"><span title="' + esc(lbl('EST:TP-DR-AT-DEPTH', 'title')) + '">' + txt + (d.D < 20 ? ' · ' + lbl('EST:TP-DR-AT-DEPTH', 'few', { n: d.D }) : '') + '</span><span>устоял ' + hp + '</span></div>';
  }
  // the share of a stretch of the window's tops: EST:B-RX-WINDOW-X on the window family (its N = |T_W|)
  const tpXShare = (F, b0, b1) => { let n = 0; for (const [b, k] of F.ev.X.T) if (b >= b0 && b < b1) n += k; return evPass(F, 'X', 'time_band', null, [F.f + 15 * b0, F.f + 15 * b1], n); };
  // a line of the clock: by the close of its M5 the half (70 %) of the set's known events had happened; its number is the
  // E4 clock of the same family (EST:B-CLOCK, all prices, part EARLIER, cut = that close)
  function tpLines(F) {
    const out = [], P = F._tp;
    for (const [ev, G, mk] of [['R', P.T, P.clock], ['X', F, P.x]]) {
      if (!mk) continue;
      for (const id of ['median', 'p70']) {
        const q = mk[id];
        if (!q) continue;
        const cut = q.t + 5, n = G.ev[ev].pts.filter(p => p.t + 5 <= cut).length;
        out.push({ ev, id, t: q.t, cut, k: q.k, K: q.K, G, p: clockPass(G, ev, { k0: -100000, k1: 100000 }, 'EARLIER', cut, n) });
      }
    }
    return out;
  }
  // ---------- the band of TP (drawBand's place and manner: the same strip, columns, capsules and colours) ----------
  function tpBand(c, ctx) {
    const F = ctx.F, P = F._tp, T = P.T, tp = P.clock, B0 = V.band, h = hv(), sl = sliceOf(ctx), lk = V.lk, dir = F.d0 > 0 ? { X: -1, R: 1 } : { X: 1, R: -1 };
    const ov = V.bandOv = bandOverlay(ctx), B = { x: B0.x, y: B0.y - ov, w: B0.w, h: B0.h + ov };
    // one lane of capsules on R's side (where the zone capsules stood): the windows
    const LH = 15, lane = { R: 1, X: 0 }, upEv = dir.X < 0 ? 'X' : 'R', dnEv = upEv === 'X' ? 'R' : 'X';
    const top = B.y + 3 + lane[upEv] * (LH + 2) + 2, bot = B.y + B.h - 3 - lane[dnEv] * (LH + 2) - 2;
    const cy = Math.round((top + bot) / 2) + 0.5, half = (bot - top) / 2 - 2;
    c.save(); c.beginPath(); c.rect(B.x, B.y, B.w, B.h); c.clip();
    c.fillStyle = '#0A0B0F'; c.fillRect(B0.x, B0.y, B0.w, B0.h);
    if (ov > 0) { const gr = c.createLinearGradient(0, B.y, 0, B0.y); gr.addColorStop(0, 'rgba(10,11,15,0)'); gr.addColorStop(1, 'rgba(10,11,15,.72)'); c.fillStyle = gr; c.fillRect(B.x, B.y, B.w, ov); }
    c.fillStyle = C.grid; c.fillRect(B0.x, B0.y, B0.w, 1);
    drawMidnight(c, B0.y, B0.y + B0.h);
    // TP-2.0: R — T's clock as a share of the whole family (N); X — the window's sessions, share of |T_W|. One scale per
    // colour (rule 3): each half has its own maximum, the halves are never compared by height.
    const nR = new Map(tp.cells), nX = F.ev.X.T, NR = (P.A && P.A.N) || T.N, NX = F.N;
    const mxE = { R: 1e-9, X: 1e-9 };
    for (const n of nR.values()) mxE.R = Math.max(mxE.R, n / NR);
    for (const n of nX.values()) mxE.X = Math.max(mxE.X, n / NX);
    const mx = Math.max(mxE.R, mxE.X), yOf = (ev, s) => cy + dir[ev] * (1 + half * Math.min(1, Math.max(0, s) / mxE[ev]));
    const bunchOf = b => tp.bunches.find(u => b >= u.b0 && b < u.b1), xc = P.xc, xBunchOf = b => xc && xc.bunches.find(u => b >= u.b0 && b < u.b1);
    const Wsel = P.w && tp.windows[P.w];
    V.bandCols = []; V.bandVals = []; V.caps = []; V.hills = []; V.tpCaps = []; V.tpLines = [];
    const labels = [];
    for (let b = 0; b < F.nb; b++) {
      const t0 = F.f + 15 * b, x0 = V.X(t0) + 1, x1 = V.X(t0 + 15) - 1;
      if (x1 < B.x || x0 > B.x + B.w) continue;
      V.bandCols.push({ b, x0, x1 });
      const past = t0 + 15 <= sl, lit = !!(h && h.k === 'tcell' && b >= h.b0 && b < h.b1) || !!(lk && (lk.b === b || (lk.ties && lk.ties.includes(b))));
      for (const ev of ['X', 'R']) {
        const n = ev === 'R' ? nR.get(b) || 0 : nX.get(b) || 0, share = n / (ev === 'R' ? NR : NX), G = ev === 'R' ? T : F;
        if (!n) continue;
        // a withheld share (its passport «—», SWPC-1.1 M14) draws no column; its place stays empty
        if (ppHeld(G, 'EST:B-RX-WINDOW-' + ev, { b0: b, b1: b + 1 })) { if (lit) labels.push({ x: (x0 + x1) / 2, y: cy + dir[ev] * 9, t: '—', col: cfg[ev] }); continue; }
        const inW = ev === 'R' ? !!(Wsel && b >= Wsel[0] && b < Wsel[1]) : true, bu = ev === 'R' ? bunchOf(b) : xBunchOf(b), closeX = ev === 'X' && xc && b === xc.bHi;
        let a = 0.12 + 0.26 * Math.pow(share / mxE[ev], 0.7);
        if (past) a *= 0.5;
        if (!inW) a *= 0.6;                                   // outside the selected window: quieter, never hidden
        if (closeX) a *= 0.55;                                // the tops of the last 15 minutes: a move not ended before the close
        if (lit) a = Math.max(a, 0.5);
        if (bu) a = Math.max(a, (past ? 0.3 : 0.5) + 0.45 * share / mxE[ev]);   // a bunch: brighter (the author's darker time mode)
        c.fillStyle = rgba(cfg[ev], Math.min(1, a * cfg.stripA / 80));
        const y = yOf(ev, share);
        c.fillRect(x0, Math.min(cy + dir[ev], y), x1 - x0, Math.abs(y - cy) - 1);
        if (closeX && Math.abs(y - cy) > 3) { c.save(); c.strokeStyle = rgba(cfg.X, 0.55); c.lineWidth = 1; c.setLineDash([2, 2]); c.strokeRect(Math.round(x0) + 0.5, Math.round(Math.min(cy + dir.X, y)) + 0.5, Math.max(1, Math.round(x1 - x0) - 1), Math.max(1, Math.round(Math.abs(y - cy) - 1) - 1)); c.restore(); }
        if (lit) labels.push({ x: (x0 + x1) / 2, y: dir[ev] < 0 ? y - 7 : y + 8, t: ppTxt(ev === 'R' ? tpShare(F, b, b + 1) : evPass(G, ev, 'time_cell', null, [t0, t0 + 15], n)).replace('%', ''), col: cfg[ev] });
      }
    }
    // each bunch's share of T at its apex column, always (core §4.2: every bunch with its share)
    for (const u of tp.bunches) {
      const p = tpShare(F, u.b0, u.b1);
      if (p.pct == null) continue;
      // beyond the apex column's end, or inside it when the column fills its half (the window lane stays clear)
      const n = nR.get(u.peak) || 0, x = (V.X(F.f + 15 * u.peak) + V.X(F.f + 15 * u.peak + 15)) / 2, y = yOf('R', n / NR), inside = Math.abs(y - cy) > half - 10;
      labels.push({ x, y: y + dir.R * (inside ? -8 : 9), t: ppTxt(p), col: inside ? '#F4F1EC' : mixW(cfg.R, 0.25), big: true });
    }
    // the same for the window's tops X (their share of T_W)
    if (xc) for (const u of xc.bunches) {
      const p = tpXShare(F, u.b0, u.b1);
      if (p.pct == null) continue;
      const n = nX.get(u.peak) || 0, x = (V.X(F.f + 15 * u.peak) + V.X(F.f + 15 * u.peak + 15)) / 2, y = yOf('X', n / NX), inside = Math.abs(y - cy) > half - 10;
      labels.push({ x, y: y + dir.X * (inside ? -8 : 9), t: ppTxt(p), col: inside ? '#EEF5FF' : mixW(cfg.X, 0.25), big: true });
    }
    // the lines of the clock: the median solid, the 70 % mark dashed, each in its event's half
    for (const L of tpLines(F)) {
      const x = Math.round(V.X(L.cut)) + 0.5;
      if (x < B.x || x > B.x + B.w) continue;
      const y0 = cy + dir[L.ev], y1 = cy + dir[L.ev] * (half + 1), on = !!(h && h.k === 'tpline' && h.ev === L.ev && h.id === L.id), held = L.p.pct == null;
      c.save(); c.strokeStyle = rgba(cfg[L.ev], held ? 0.25 : on ? 1 : 0.85); c.lineWidth = on ? 2 : 1.3; c.setLineDash(L.id === 'p70' ? [4, 3] : []);
      c.beginPath(); c.moveTo(x, y0); c.lineTo(x, y1); c.stroke(); c.restore();
      // a short mark at the outer end, the median one row further out than the 70 % mark, so close lines stay readable
      c.font = '700 9.5px ' + FONT; c.textBaseline = 'middle'; c.fillStyle = rgba(cfg[L.ev], held ? 0.4 : 0.95);
      c.fillText(L.id === 'median' ? '½' : '70%', x + 3, cy + dir[L.ev] * (half - (L.id === 'median' ? 4 : 15)));
      V.tpLines.push({ ev: L.ev, id: L.id, x, y0: Math.min(y0, y1), y1: Math.max(y0, y1) });
    }
    for (const L of labels) { c.font = (L.big ? '700 10.5px ' : '700 10.5px ') + FONT; c.fillStyle = L.col; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(L.t, L.x, Math.max(B.y + 7, Math.min(B.y + B.h - 7, L.y))); c.textAlign = 'left'; }
    // the windows in the place of the zone capsules: the selected one outlined, the others a soft fill; «до окна» and «позже»
    // quieter. Each carries its name and its share of T (core §7: «у W % true-сессий откат до вершины был в этом окне»).
    const shares = TP_WINDOWS.filter(w => tp.windows[w]).map(w => ({ w, W: tp.windows[w], p: tpShare(F, tp.windows[w][0], tp.windows[w][1]) }));
    const capMax = Math.max(1e-9, ...shares.map(q => q.p.pct || 0));
    for (const { w, W, p } of shares) {
      const x0 = V.X(F.f + 15 * W[0]) + 1, x1 = V.X(F.f + 15 * W[1]) - 1, wd = x1 - x0, y0 = dir.R < 0 ? B.y + 3 : B.y + B.h - 3 - LH + 2;
      if (x1 < B.x || x0 > B.x + B.w || wd < 4) continue;
      const on = w === P.w, hov = !!(h && (h.k === 'tpwin' || h.k === 'tpzone') && h.id === w), side = w === 'BEFORE' || w === 'LATE', r = Math.pow((p.pct || 0) / capMax, 0.7);
      c.save(); c.globalAlpha = on || hov ? 1 : 0.8;
      c.fillStyle = rgba(cfg.R, Math.min(1, ((on ? 0.3 : 0.1 + 0.16 * r) * (side ? 0.6 : 1) + (hov ? 0.08 : 0)) * cfg.capA / 100)); roundRect(c, x0, y0, wd, LH, LH / 2); c.fill();
      if (on || hov) { c.strokeStyle = rgba(cfg.R, on ? 0.75 : 0.5); c.lineWidth = 1; roundRect(c, x0 + 0.5, y0 + 0.5, wd - 1, LH - 1, LH / 2); c.stroke(); }
      c.beginPath(); c.rect(x0 + 2, y0, wd - 4, LH); c.clip();
      c.textBaseline = 'middle';
      let x = x0 + 9;
      c.font = '700 10.5px ' + FONT;
      const nw = c.measureText(TP_NAME[w]).width, pw = pctW(c, ppTxt(p), '700 ', 10.5 + (on ? 1 : 0));
      c.font = '700 10.5px ' + FONT; c.fillStyle = rgba(side ? '#B8BEC9' : mixW(cfg.R, 0.2), Math.min(1, (on ? 1 : 0.85) * cfg.capTxt / 100));
      if (wd >= nw + 14) { c.fillText(TP_NAME[w], x, y0 + LH / 2 + 0.5); x += nw + 6; }
      // a narrow window keeps its name; its share is then in its title and in the panel
      if (wd >= nw + pw + 20) pctDraw(c, ppTxt(p), x, y0 + LH / 2 + 0.5, '700 ', 10.5 + (on ? 1 : 0), rgba(mixW(cfg.R, 0.35), Math.min(1, (on ? 1 : 0.8) * cfg.capTxt / 100)));
      c.restore();
      V.tpCaps.push({ id: w, box: [x0, y0, wd, LH] });
    }
    // the centre line, the slice, the names of the halves, the unknown mass (R of T, X of the window), as drawBand
    const xF = V.X(F.f), xE = V.X(F.end);
    c.fillStyle = 'rgba(209,212,220,.14)'; c.fillRect(Math.max(B.x, xF), cy, Math.min(B.x + B.w, xE) - Math.max(B.x, xF), 1);
    const xs = Math.round(V.X(sl)) + 0.5;
    if (xs > B.x && xs < B.x + B.w) { c.strokeStyle = 'rgba(209,212,220,.35)'; c.setLineDash([3, 4]); c.beginPath(); c.moveTo(xs, B.y + 1); c.lineTo(xs, B.y + B.h); c.stroke(); c.setLineDash([]); }
    c.textBaseline = 'middle';
    if (xF - 60 > B.x) {
      c.font = '700 10px ' + FONT;
      c.fillStyle = cfg.X; c.fillText('X ' + F.names.X.toLowerCase() + ' · ' + TP_NAME[P.w || 'W1'], Math.max(B.x + 6, xF - 150), cy + dir.X * 9);
      c.fillStyle = cfg.R; c.fillText('R ' + F.names.R.toLowerCase() + ' · доля семьи', Math.max(B.x + 6, xF - 150), cy + dir.R * 9);
    }
    V.stripUnk = null;
    const uX = F.ev.X.unknown + F.ev.X.none, uR = T.ev.R.unknown + T.ev.R.none;
    if (uX + uR) {
      const x0 = Math.min(xE + 6, B.x + B.w - 40), w = 14;
      c.fillStyle = 'rgba(160,168,180,.45)';
      for (const [ev, u, n] of [['X', uX, NX], ['R', uR, NR]]) { if (!u) continue; const y = yOf(ev, u / n); c.fillRect(x0, Math.min(y, cy + dir[ev]), w, Math.abs(y - cy) - 1); }
      c.fillStyle = C.text2; c.font = '600 10.5px ' + FONT; c.fillText('?', x0 + w + 4, cy);
      V.stripUnk = [x0, top, w + 14, bot - top];
    }
    c.restore();
    V.bandCy = cy;
    c.fillStyle = C.axis; c.fillRect(V.plot.w, B0.y, V.W - V.plot.w, B0.h);
    c.fillStyle = C.grid; c.fillRect(V.plot.w, B0.y, V.W - V.plot.w, 1); c.fillRect(V.plot.w, B0.y, 1, B0.h);
  }
  function tpHit(x, y) {
    const inBox = a => x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3];
    const w = (V.tpCaps || []).find(inBox);
    if (w) return { k: 'tpwin', id: w.id, src: 'strip' };
    const L = (V.tpLines || []).find(q => Math.abs(x - q.x) <= 3 && y >= q.y0 - 2 && y <= q.y1 + 2);
    if (L) return { k: 'tpline', ev: L.ev, id: L.id, src: 'strip' };
    return null;
  }
  // a click on a window (on the band or its row in the panel) fixes it; a second click lets go (back to W1)
  function tpPinWindow(w) { TP.pin = TP.pin === w ? null : w; st.pin = null; st.hover = null; tip.hidden = true; render(true); }
  // the window's peak 15 minutes: the cell of T's clock inside the window that holds most of its pullbacks (the earliest of
  // equal ones), the time the trader reads off the window (operator 05.11: «в какое время будет этот максимальный откат…
  // не просто как позже, а более уточнённый»)
  function tpWinPeak(F, w) {
    const tp = F._tp.clock, W = tp.windows[w];
    if (!W) return null;
    let best = null;
    for (const [b, n] of tp.cells) if (b >= W[0] && b < W[1] && (!best || n > best.n)) best = { b, n };
    return best && { b: best.b, n: best.n, t0: F.f + 15 * best.b, t1: F.f + 15 * best.b + 15 };
  }
  // ---------- the pullback places of the other windows, always on the chart (operator 05.11) ----------
  // «Почему… на откат R я вижу только одно созвездие в W1… сделай так, чтобы я видел позже созвездие, тоже откаты, а не
  // так, чтобы я на них наводил мышку… может быть, в другом оформлении». The windows split T's pullbacks by time, so the
  // places of every window lie in its own hours: drawn together they are the whole map of T's pullbacks. The window on
  // screen keeps the full drawing (and its X); every other window's places of R are drawn quieter — a lighter haze, smaller
  // stars, the window's name before the place's — each with its share of ITS window's sessions (EST:B-ZONE-R on that
  // window family, verified like the rest). Under the mouse: the place's words and its hours; a click puts the window on
  // screen. X stays the window's on screen: its tops are the continuation of those sessions only.
  const TPG = { haze: 0.85, thread: 0.8, star: 0.85, starA: 0.85, label: 0.95, size: 0.85 };
  function tpOthers(ctx) {
    const F = ctx.F, P = F && F._tp, out = [];
    if (!P) return out;
    for (const w of TP_WINDOWS) {
      if (w === P.w || !P.clock.windows[w]) continue;
      const G = tpSnap(ctx.D, ctx.s, w, P.T);
      if (G) G._tpg = { F, w };                                        // TP-2.0: its places read the family share of the screen's F
      if (G && G.zones.R && G.zones.R.zones.length) out.push({ w, G });
    }
    return out;
  }
  // phase 'under' (before the candles): haze, threads and names; phase 'over' (after the candles): the stars and, under the
  // mouse, the place's outline
  function tpGhosts(c, ctx, phase) {
    if (phase === 'under') V.tpGhostHit = [];
    if (!ctx.F || !ctx.F._tp || !st.L.zones || st.mode !== 'bounds') return;
    const h = hv(), env = V.zoneEnv, sl = sliceOf(ctx), R0 = 1.7 * cfg.ptSize / 100;
    for (const { w, G } of tpOthers(ctx)) {
      const CL = cloudsOf(G), S = zoneLook(G, ctx, 'R'), wl = !!(h && h.k === 'tpwin' && h.id === w);
      CL.R.forEach((g, i) => {
        if (!g || zoneHeld(G, 'R', i)) return;           // a withheld place's share is «—»: no haze asserts it
        const on = !!(h && h.k === 'tpzone' && h.id === w && h.i === i), k = on || wl ? 1.5 : h && h.k !== 'stripBg' ? 0.6 : 1;
        const col = stateCol(cfg.R, S[i]), imp = expiredLook(S[i]), dim = imp ? 0.6 * cfg.spentA / 100 : S[i] === 'QUIET' ? 0.7 : S[i] === 'HOLDS' ? 1.15 : 1;
        if (phase === 'under') {
          const fa = cfg.cloudA / 100 * TPG.haze, ta = cfg.threadA / 100 * TPG.thread;
          c.save();
          c.filter = 'blur(14px)'; c.fillStyle = rgba(col, 0.5 * Math.min(0.5, 0.17 * k * dim * fa)); loopsPath(c, g.g1); c.fill();
          c.filter = 'blur(7px)'; c.fillStyle = rgba(col, 0.5 * Math.min(0.45, 0.13 * k * dim * fa)); loopsPath(c, g.g2); c.fill();
          c.filter = 'none';
          c.strokeStyle = rgba(col, Math.min(0.35, 0.13 * k * dim * ta)); c.lineWidth = 0.5;
          c.beginPath(); for (const s of g.mst) { c.moveTo(s[0], s[1]); c.lineTo(s[2], s[3]); } c.stroke();
          c.restore();
          // the name «W2 · R1» and the share of the window's sessions, as the window on screen names its places (zoneMark),
          // smaller and quieter; off the candles it moves up or down in its own hours, never left into the past ('stay')
          if (env) zoneMark(c, ctx, G, 'R', i, g, g.z, S[i], col, h, env, { name: TP_NAME[w] + ' · ' + g.z.label, pass: tpMassPlace(ctx.F, w, g.z), size: TPG.size, alpha: TPG.label, k, stay: true, hit: box => V.tpGhostHit.push({ box, w, i, loops: g.hit }) });
          else V.tpGhostHit.push({ box: [0, 0, 0, 0], w, i, loops: g.hit });
          return;
        }
        if (!st.L.pts) return;
        c.save();
        for (const q of G.ev.R.pts) {
          if (pointZone(G, q) !== i) continue;
          const x = V.X(q.t + 2.5), y = V.Y(q.p);
          if (x < -4 || x > V.plot.w + 4 || y < -4 || y > V.plot.h + 4) continue;
          const a = ((q.t + 5 <= sl ? cfg.pastA : cfg.ptA) / 100) * 1.1 * TPG.starA * (on ? 1.6 : k < 1 ? 0.6 : 1) * dim;
          c.fillStyle = rgba(col, Math.min(1, a)); c.beginPath(); c.arc(x, y, R0 * TPG.star, 0, 6.2832); c.fill();
        }
        if (on) { c.strokeStyle = rgba(col, 0.55); c.lineWidth = 1; loopsPath(c, g.ln); c.stroke(); }
        c.restore();
      });
    }
  }
  // the place of another window under the mouse: its name first, then inside its haze (as the window on screen)
  function tpGhostAt(x, y, inside) {
    for (const q of V.tpGhostHit || []) {
      const ok = inside ? inLoops(q.loops, x, y) : x >= q.box[0] && x <= q.box[0] + q.box[2] && y >= q.box[1] && y <= q.box[1] + q.box[3];
      if (ok) return { k: 'tpzone', ev: 'R', id: q.w, i: q.i };
    }
    return null;
  }
  // under the mouse its whole time window over its prices, as a place of the window on screen (linkOf, 'zone')
  function tpGhostLink(ctx, h) {
    const g = tpOthers(ctx).find(q => q.w === h.id), G = g && g.G, z = G && G.zones.R.zones[h.i];
    if (!z || zoneHeld(G, 'R', h.i)) return;
    const bs = z.cell_mask.map(q => q[1]), ks = z.cell_mask.map(q => q[0]), t0 = G.f + 15 * Math.min(...bs), t1 = G.f + 15 * (Math.max(...bs) + 1);
    const look = zoneStatus(G, ctx, 'R')[h.i], spent = expiredLook(look);
    V.lk = { ev: 'R', src: 'zone', t0, t1, k0: Math.min(...ks), k1: Math.max(...ks) + 1, sl: sliceOf(ctx), spent, hold: look === 'HOLDS', marker: targetMarker(G, ctx, 'R', z) };
    V.win = Object.assign({ pA: null, pB: null }, V.win || {}, { t0, t1, col: spent ? stateCol(cfg.R, 'spent') : cfg.R });
  }
  // a click on such a place puts its window on screen and keeps the place under the inspector
  function tpPinGhost(h) { TP.pin = h.id; st.ev = 'R'; st.pin = null; st.pinZone = h.i + 1; st.hover = null; tip.hidden = true; render(true); }
  // ---------- the words under the mouse ----------
  // the window under the mouse: its share of T, then WHEN inside it (operator 05.11): its peak 15 minutes and by when half
  // of its sessions had their pullback, both over the window's sessions (EST:B-RX-WINDOW-R, EST:B-CLOCK-R on the window
  // family), and its places of R with their shares
  function tpWinTip(F, h, ctx) {
    const P = F._tp, tp = P.clock, W = tp.windows[h.id];
    if (!W) return '';
    const p = tpShare(F, W[0], W[1]), on = P.w === h.id, G = ctx ? tpSnap(ctx.D, ctx.s, h.id, P.T) : null, set = 'сессий окна ' + TP_NAME[h.id];
    let when = '';
    const pk = tpWinPeak(F, h.id);
    if (G && pk) {
      const n = G.ev.R.T.get(pk.b) || 0, pP = evPass(G, 'R', 'time_cell', null, [pk.t0, pk.t1], n);
      when += '<div class="il" style="color:' + cfg.R + '">Чаще всего откат в истории окна — ' + clk(pk.t0) + '–' + clk(pk.t1) + '</div>' +
        '<div class="ir">в эти 15 минут — у ' + set + '<b>' + ppTxt(pP) + '</b></div>';
      const m = tpMarks(G.M, 'R', G.f), q = tpQuant(m.ts, 1, 2);
      if (q) {
        const cut = q.t + 5, pM = clockPass(G, 'R', { k0: -100000, k1: 100000 }, 'EARLIER', cut, G.ev.R.pts.filter(r => r.t + 5 <= cut).length);
        when += '<div class="ir" title="' + esc(lbl('EST:B-CLOCK-R', 'title')) + '">к ' + clk(cut) + ' (медиана окна) откат уже был — у ' + set + '<b>' + ppTxt(pM) + '</b></div>';
      }
      // its places of R (where in price), each its share of the window's sessions; their hours under the mouse at the place
      (G.zones.R || { zones: [] }).zones.forEach((z, i) => {
        if (!zoneHeld(G, 'R', i)) when += '<div class="ir">место <span style="color:' + cfg.R + '">' + z.label + '</span> ' + band(z.price_low, z.price_high) + ' SD · семьи<b>' + ppTxt(tpMassPlace(F, h.id, z)) + '</b></div>';
      });
    }
    return '<div class="ih">' + TP_NAME[h.id] + ' · ' + clk(F.f + 15 * W[0]) + '–' + clk(F.f + 15 * W[1]) + '</div>' + sentence(p) + when +
      '<div class="if">' + (on ? 'Колонка цены и созвездия — сессии этого окна.' : h.src === 'strip' ? 'Наведено: колонка цены и созвездия — сессии этого окна; щелчок закрепляет.' : 'Щелчок — сессии этого окна на экране.') + ' Доля окна — от всей семьи (DR устоял до ' + clk(F.end) + ', откат до вершины в окне).</div>';
  }
  // a place of another window under the mouse: the place's own words on its window family, which window, and the click
  function tpGhostTip(F, ctx, h) {
    const g = tpOthers(ctx).find(q => q.w === h.id), W = F._tp.clock.windows[h.id];
    if (!g || !W) return '';
    const z = g.G.zones.R.zones[h.i], head = '<div class="ih"><span style="color:' + cfg.R + '">';
    return zoneTip(g.G, ctx, { k: 'zone', ev: 'R', i: h.i }).replace(head + (z ? z.label : '') + '</span>', head + TP_NAME[h.id] + ' · ' + (z ? z.label : '') + '</span>') +
      '<div class="if">Место окна ' + TP_NAME[h.id] + ' (' + clk(F.f + 15 * W[0]) + '–' + clk(F.f + 15 * W[1]) + '): крупное число — доля всей семьи; в строке ниже — доля среди сессий окна. Щелчок — окно ' + TP_NAME[h.id] + ' на экране целиком (колонка цены и места вершины его сессий).</div>';
  }
  function tpLineTip(F, h) {
    const L = tpLines(F).find(q => q.ev === h.ev && q.id === h.id);
    if (!L) return '';
    const what = h.ev === 'R' ? 'откат до вершины' : 'вершина хода', set = h.ev === 'R' ? 'true-сессий' : 'сессий окна ' + TP_NAME[F._tp.w];
    const und = h.ev === 'R' && L.G.ev.R.none ? '<div class="ir">' + lbl('EST:B-RX-UNDETERMINED-R', 'row', { ev: 'R' }) + '<b>' + ppTxt(undPass(L.G, 'R', 'BOTH')) + '</b></div>' : '';
    return '<div class="ih">' + (h.id === 'median' ? 'Медиана' : 'Отметка 70 %') + ' · ' + clk(L.cut) + '</div>' +
      '<div class="is">К закрытию M5 ' + clk(L.t) + '–' + clk(L.cut) + ' ' + what + ' был у ' + (h.id === 'median' ? 'половины' : '70 %') + ' ' + set + ' с известным событием.</div>' +
      '<div class="ir" title="' + esc(lbl('EST:B-CLOCK-' + h.ev, 'title')) + '">' + lbl('EST:B-CLOCK-' + h.ev, 'earlier', { t: clk(L.cut) }) + '<b>' + ppTxt(L.p) + '</b></div>' + und + ifoot(L.G);
  }
  function tpCellTip(F, ctx, h) {
    const P = F._tp, T = P.T, b = h.b0, b1 = h.b1 || b + 1, t0 = F.f + 15 * b, t1 = F.f + 15 * b1, nR = tpCount(P.clock, b, b1);
    let nX = 0;
    for (const [q, n] of F.ev.X.T) if (q >= b && q < b1) nX += n;
    const pR = evPass(T, 'R', 'time_cell', null, [t0, t1], nR), pX = evPass(F, 'X', 'time_cell', null, [t0, t1], nX);
    const u = P.clock.bunches.find(q => b >= q.b0 && b < q.b1), w = TP_WINDOWS.find(k => P.clock.windows[k] && b >= P.clock.windows[k][0] && b < P.clock.windows[k][1]);
    const xu = P.xc && P.xc.bunches.find(q => b >= q.b0 && b < q.b1), close = P.xc && b1 > P.xc.bHi;
    const row = (ev, p, set) => '<div class="ib"><i style="color:' + cfg[ev] + '">' + lbl(p.estimand, 'two_row', { ev, name: (ev === 'R' ? T : F).names[ev].toLowerCase() }) + '</i><span class="k"> ' + set + ' </span><b>' + ppTxt(p) + '</b></div>';
    return '<div class="ih">' + clk(t0) + '–' + clk(t1) + (w ? ' · ' + TP_NAME[w] : '') + (u ? ' · пучок ' + clk(F.f + 15 * u.b0) + '–' + clk(F.f + 15 * u.b1) : '') + '</div>' +
      '<div class="iq">' + lbl('FF:R-BEFORE-X', 'q_window') + '</div>' + row('R', pR, 'true') + row('X', pX, TP_NAME[P.w || 'W1']) +
      (xu ? '<div class="is" style="color:' + cfg.X + '">пучок вершин ' + clk(F.f + 15 * xu.b0) + '–' + clk(F.f + 15 * xu.b1) + '</div>' : '') +
      (close ? '<div class="is">Вершина в последние 15 минут сессии: ход не кончился до закрытия — это не место вершины.</div>' : '') + ifoot(T, lbl('FF:SHARE-STEP', 'foot_time'));
  }
  // the R-side depth under the mouse in the price column (operator 03.11: not drawn, only a number when asked): of the
  // window's sessions, those whose pullback went deeper than this band's lower edge (EST:B-RX-BAND-R over the deeper cells)
  function tpDepthLine(F, h) {
    if (!F._tp || (h.ev || st.ev) !== 'R') return '';
    const n = F.ev.R.pts.filter(q => q.k < h.k0).length, D = F.ev.R;
    const p = pp(F, { estimand: 'EST:B-RX-BAND-R', params: { k0: -100000, k1: h.k0 }, event_id: 'R', region_kind: 'price_band', exact_price_bounds: [-100000, h.k0], time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: n, unknown_count: D.unknown, no_event_count: D.none, display_scope: 'inspector', phrase: lbl('EST:B-RX-BAND-R', 'phrase', { name: F.names.R.toLowerCase(), ev: 'R', what: F.what.R, band: '< ' + sd(h.k0 / 10) }), horizon: hzOf(F) });
    return '<div class="ir">глубже ' + sd(h.k0 / 10) + ' SD у сессий окна ' + TP_NAME[F._tp.w || 'W1'] + '<b>' + ppTxt(p) + '</b></div>';
  }
  // the X-side ladder at a place of tops (core 1.4, the author's «targets»): of the window's sessions, those whose top
  // reached this band's lower edge or went further (EST:B-RX-BAND-X from the edge up; a top of the last 15 minutes
  // reached its level too, so it counts here though it is never a place)
  function tpReachLine(F, z) {
    if (!F._tp || !z) return '';
    return '<div class="ir" style="color:' + cfg.X + '">дошли до ' + sd(z.price_low / 10) + ' SD у сессий окна ' + TP_NAME[F._tp.w || 'W1'] + '<b>' + ppTxt(tpReachPass(F, z)) + '</b></div>';
  }
  // ---------- the panel: the clock of T, the windows (a row fixes its window), then the places of the window ----------
  function tpPanel(F, ctx) {
    const P = F._tp, T = P.T, tp = P.clock, out = [];
    out.push(tpDepthRow(F, ctx));                                       // TP-2.0 Ч13: the frame by today's depth
    // TP-2.0: every amber number here is a share of the whole family (EST:TP-MASS-R); windows + «без отката до вершины» =
    // the share «устоял»
    out.push('<div class="p21-h second"><span title="' + esc(lbl('EST:TP-MASS-R', 'head_title')) + '">' + lbl('EST:TP-MASS-R', 'head') + '</span><span>' + lbl('EST:TP-MASS-R', 'head_r') + '</span></div>');
    for (const u of tp.bunches) {
      const p = tpShare(F, u.b0, u.b1);
      out.push(link({ k: 'tcell', b0: u.b0, b1: u.b1, src: 'tp' }, prow(lbl('EST:TP-MASS-R', 'bunch', { t0: clk(F.f + 15 * u.b0), t1: clk(F.f + 15 * u.b1) }), ppTxt(p)), 'mc', p, plainTitle(p)));
    }
    if (!tp.bunches.length) out.push('<div class="p21-note">' + lbl('EST:TP-MASS-R', 'none', { need: tp.need }) + '</div>');
    const lines = tpLines(F).filter(L => L.ev === 'R');
    if (lines.length) out.push('<div class="p21-note">' + lines.map(L => '<span title="' + esc(lbl('EST:B-CLOCK-R', 'earlier', { t: clk(L.cut) }) + ': ' + ppTxt(L.p) + ' (из устоявших)') + '">' + (L.id === 'median' ? 'медиана' : '70 %') + ' <b style="color:' + cfg.R + '">' + clk(L.cut) + '</b></span>').join(' · ') + '</div>');
    for (const w of TP_WINDOWS) {
      const W = tp.windows[w];
      if (!W) continue;
      const p = tpShare(F, W[0], W[1]), on = P.w === w;
      out.push(link({ k: 'tpwin', id: w }, '<span class="t"><span><span class="zt">' + clk(F.f + 15 * W[0]) + '–' + clk(F.f + 15 * W[1]) + '</span> <i class="zn" style="color:' + (w === 'BEFORE' || w === 'LATE' ? '#B8BEC9' : cfg.R) + '">' + TP_NAME[w] + '</i>' + (on ? ' <span class="p21-sub">на экране' + (P.why === 'today' ? ' · сегодняшний откат' : P.why === 'pin' ? ' · закреплено' : '') + '</span>' : '') + '</span></span><b>' + ppTxt(p) + '</b>', 'mc' + (on ? ' pinned' : ''), p, plainTitle(p)));
      if (on && F.zones.R) {
        // «вне мест»: the window's sessions whose pullback lies outside its places, a share of the family too
        const nb = F.zones.R.zones.filter((z, i) => !zoneHeld(F, 'R', i)).map(z => [z.price_low, z.price_high]), q = tpMass(F, { b0: W[0], b1: W[1], not_bands: nb });
        out.push('<div class="mc dim" title="' + esc(plainTitle(q)) + '"><span class="t"><span>&nbsp;&nbsp;' + lbl('EST:TP-MASS-R', 'outside') + '</span></span><b>' + ppTxt(q) + '</b></div>');
      }
    }
    const nr = tpMass(F, { part: 'NO_R' });
    if (nr.yes_count) out.push(link({ k: 'evrow', ev: 'R' }, prow(lbl('EST:TP-MASS-R', 'no_r'), ppTxt(nr)), 'dim', nr, plainTitle(nr)));
    // the continuation of the window's sessions: the time lines of their own top X (the ladder is on today's levels)
    const xl = tpLines(F).filter(L => L.ev === 'X'), xc = P.xc;
    if (P.w) {
      const W = tp.windows[P.w], why = P.why === 'today' && P.today ? 'сегодня самая глубокая точка — ' + sd(Math.round(100 * P.today.u) / 100) + ' SD в ' + clk(P.today.t) : P.why === 'pin' ? 'закреплено' : 'отката ещё не было';
      out.push('<div class="p21-h second"><span title="Продолжение сессий с откатом ' + (W ? clk(F.f + 15 * W[0]) + '–' + clk(F.f + 15 * W[1]) : '') + ' (' + why + '): пучки времени вершин, их медиана и 70 %; на графике места вершины — подпись «дошли»: сколько сессий окна дошли до ближнего края; на колонке цены — уровни, до которых дошли 70 % и 50 %.">Продолжение · ' + TP_NAME[P.w] + ' · из сессий окна</span><span>доля окна</span></div>');
      out.push('<div class="p21-note">Продолжение сессий с откатом ' + (W ? clk(F.f + 15 * W[0]) + '–' + clk(F.f + 15 * W[1]) : '') + ' · ' + why + (F.N < 20 ? ' · мало сессий: n=' + F.N : '') + '</div>');
      if (xc) for (const u of xc.bunches) { const p = tpXShare(F, u.b0, u.b1); out.push(link({ k: 'tcell', ev: 'X', b0: u.b0, b1: u.b1, src: 'tpx' }, prow('пучок вершин ' + clk(F.f + 15 * u.b0) + '–' + clk(F.f + 15 * u.b1), ppTxt(p)), 'mc', p, plainTitle(p))); }
      if (xc && !xc.bunches.length) out.push('<div class="p21-note">Пучков вершин нет: ни один отрезок времени не набрал ' + xc.need + ' сессий (5 % семьи, не меньше 4).</div>');
      for (const L of tpLevels(F)) out.push('<div class="mc" title="' + esc(plainTitle(L.p)) + '"><span class="t"><span>дошли до <b style="color:' + cfg.X + '">' + sd(L.k / 10) + ' SD</b> — ' + L.q + ' % окна</span></span><b>' + ppTxt(L.p) + '</b></div>');
      if (xl.length) out.push('<div class="p21-note">' + xl.map(L => '<span title="' + esc(lbl('EST:B-CLOCK-X', 'earlier', { t: clk(L.cut) }) + ': ' + ppTxt(L.p)) + '">' + (L.id === 'median' ? 'медиана вершины' : '70 % вершин') + ' <b style="color:' + cfg.X + '">' + clk(L.cut) + '</b></span>').join(' · ') + '</div>');
      if (xc && xc.close) { const p = tpXShare(F, xc.bHi, xc.bHi + 1); out.push(link({ k: 'tcell', ev: 'X', b0: xc.bHi, b1: xc.bHi + 1, src: 'tpx' }, prow('ход не кончился до закрытия', ppTxt(p)), 'dim', p, plainTitle(p))); }
      if (F.ev.X.unknown + F.ev.X.none) { const u = undPass(F, 'X', 'BOTH'); out.push(link({ k: 'evrow', ev: 'X' }, prow(lbl('EST:B-RX-UNDETERMINED-X', 'row', { ev: '<i style="color:' + cfg.X + '">X</i>' }), ppTxt(u)), 'dim', u, plainTitle(u))); }
    }
    return out.join('');
  }
  // the places of R of the other windows (operator 05.11), each its share of its own window; a row is the place on the chart
  // and a click puts its window on screen
  function tpGhostPanel(F, ctx) {
    const gs = tpOthers(ctx), out = [];
    if (!gs.length) return '';
    out.push('<div class="p21-h second"><span title="' + esc(lbl('EST:TP-MASS-R', 'others_title')) + '">' + lbl('EST:TP-MASS-R', 'others') + '</span><span>' + lbl('EST:TP-MASS-R', 'head_r') + '</span></div>');
    for (const { w, G } of gs) {
      const S = zoneStatus(G, ctx, 'R');
      G.zones.R.zones.forEach((z, i) => {
        if (zoneHeld(G, 'R', i)) return;
        const p = tpMassPlace(F, w, z);
        out.push(link({ k: 'tpzone', ev: 'R', id: w, i }, '<span class="t"><span><span class="zt">' + clk(z.time_start) + '–' + clk(z.time_end) + '</span> <i class="zn" style="color:' + cfg.R + '">' + TP_NAME[w] + ' · ' + z.label + '</i></span>' +
          '<span class="p21-sub">' + lbl('EST:B-ZONE-R', 'sub', { band: band(z.price_low, z.price_high), status: zstOf(G, ctx, z, S[i]) }) + '</span></span><b class="zp">' + ppTxt(p) + '</b>', 'mc zst-' + S[i], p, plainTitle(p)));
      });
    }
    return out.join('');
  }
