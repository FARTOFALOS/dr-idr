  // ---------- «От этой свечи» (MVP v3, operator 25.11.2026; not a contract estimand, nothing is sent to /verify) ----------
  // Operator 25.11: «нажимаю и вижу … пятиминутные кластеры … вместо всех вот этих боксов»; then «примени тот же смысл,
  // что в DR-сессии, только в меньшем масштабе … вверх расширение и вниз расширение только считаем … не лесенка».
  // The DR rules of TP-2.0 (meaning/25 §2.4–2.5, lab/tp11.py) on a smaller frame:
  // - the box is the anchor M5 (the last closed one; in replay the chosen one): its high and low play the DR;
  // - the family: every historical session of the same instrument, session and side (all weekdays, the base lab/.runtime
  //   via lab/anchor235_build.py, dates before today) that at the SAME clock M5 was confirmed, had its DR whole and closed
  //   as far from its IDR edge in SD as today (±0,25 SD; ±0,5 when fewer than ANC_MIN) — M of them, one vote each;
  // - two facts per session over the horizon: the extension up (its farthest high beyond the anchor's high, the first M5
  //   reaching it) and the extension down (its farthest low beyond the anchor's low); no extension on a side is its own
  //   row, never a zero; an extreme in the horizon's last M5 is a move cut by the horizon («ещё шли»), not a place;
  // - time: counts of the extremes' M5 → bunches by the TP rule (tpRegions), marks ½ and 70 %;
  // - price: counts per ANC_STEP SD beyond the anchor → places by the same rule; a bunch or a place needs tpNeed(M);
  // - every number is a share of M. History of similar moments, not a forecast.
  // - on the chart (operator 25.11 evening: «не нужно показывать звезды … самый максимальный кластер … его границы
  //   протягивались на весь экран налево»): each place a quiet dashed box over the middle half of its ends' hours; its ONE
  //   cluster, the 5 min × 0,1 SD cell with the most ends, bright, its two SD bounds carried translucent to the left edge
  //   with the name. The rules for agents: spec/ekran-24/19-ot-etoj-svechi-23-5.md.
  const ANC = { on: /(?:^|[#&])anc=1(?:&|$)/.test(location.hash), lib: {}, load: {}, Hs: [6, 12, 0], hi: 1, memo: null };
  const ANC_MIN = 20, ANC_STEP = 0.1;   // the price cell: 0,1 SD of the DR grid, as TP-2.0 (operator 25.11: «уровни, которые относятся к DR»)
  window.__anc = ANC;   // for checks from the console
  const ancOn = () => ANC.on;
  const ancPct = v => (Math.round(v * 1000) / 10).toFixed(1).replace('.', ',').replace(/,0$/, '');
  const ancSd = r => (r > 0 ? '+' : r < 0 ? '−' : '') + Math.abs(r).toFixed(1).replace('.', ',');
  const ancHName = () => ANC.Hs[ANC.hi] ? ANC.Hs[ANC.hi] * 5 + ' мин' : 'до конца блока';
  function ancLib(key) {
    if (ANC.lib[key]) return ANC.lib[key];
    if (!ANC.load[key]) ANC.load[key] = fetch('anchor/' + key + '.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null)
      .then(j => { ANC.lib[key] = j || { err: 1 }; ANC.memo = null; render(true); }).catch(() => { ANC.lib[key] = { err: 1 }; render(true); });
    return null;
  }
  function ancNow(ctx) {
    const F = ctx.F;
    if (!F || !ctx.s.conf) return { why: 'Нет подтверждения — не от чего считать' };
    if (ctx.s.failed) return { why: 'DR сегодня сломан — этот режим считает только для целого DR' };
    const lib = ancLib(A.inst + '_' + ctx.s.k);
    if (!lib) return { why: 'Загружаю историю сессий…' };
    if (lib.err) return { why: 'Нет файла истории: запустите python -B lab/anchor235_build.py' };
    const T = sliceOf(ctx), j = lib.grid.indexOf(T), b = ctx.D.bars.find(q => q.t + 5 === T);
    if (j < 0 || !b) return { why: 'Срез вне часов сессии' };
    const dir = p => F.d0 * (tk(p) - F.e0t), c0 = dir(b.c), h0 = Math.max(dir(b.h), dir(b.l)), l0 = Math.min(dir(b.h), dir(b.l));
    const u0 = c0 / F.w0t, iso = ctx.D.iso || '9999', H = ANC.Hs[ANC.hi];
    const key = [A.inst, ctx.s.k, T, c0, h0, l0, iso, H, F.d0].join('|');
    if (ANC.memo && ANC.memo.key === key) return ANC.memo;
    const g1 = H ? Math.min(lib.grid.length - 1, j + H) : lib.grid.length - 1, L = g1 - j, cand = [];
    if (L < 2) return { why: 'До конца блока меньше двух M5' };
    for (const s of lib.sessions) {
      if (s.s !== F.d0 || s.d >= iso || s.c > T) continue;
      const pj = s.p[j];
      if (!pj) continue;
      let broke = false;
      for (let g = 0; g <= j && !broke; g++) { const q = s.p[g]; if (q && lib.grid[g] > s.c && q[2] < s.o) broke = true; }
      if (broke) continue;
      cand.push({ s, dist: Math.abs(pj[2] / s.w - u0) });
    }
    let tol = 0.25, MS = cand.filter(q => q.dist <= tol);
    if (MS.length < ANC_MIN) { tol = 0.5; MS = cand.filter(q => q.dist <= tol); }
    const ev = { X: { pts: [], none: 0, open: 0, unk: 0 }, R: { pts: [], none: 0, open: 0, unk: 0 } };
    for (const { s } of MS) {
      const aH = s.p[j][1], aL = s.p[j][0];
      let hi = null, lo = null, gH = 0, gL = 0, gap = false;
      for (let g = j + 1; g <= g1; g++) {
        const q = s.p[g];
        if (!q) { gap = true; continue; }
        if (hi == null || q[1] > hi) { hi = q[1]; gH = g; }
        if (lo == null || q[0] < lo) { lo = q[0]; gL = g; }
      }
      if (hi == null || gap) { ev.X.unk++; ev.R.unk++; continue; }      // a missing M5 could hold the extreme: unknown
      for (const [e, ext, u, g] of [['X', hi - aH, hi / s.w, gH], ['R', aL - lo, lo / s.w, gL]]) {
        if (ext <= 0) { ev[e].none++; continue; }                        // never beyond the anchor on this side
        if (g === g1) { ev[e].open++; continue; }                        // still going when the horizon ended
        // the end on the session's OWN DR grid (u from its IDR edge in its IDR widths), as the screen's SD levels
        ev[e].pts.push({ u, k: Math.floor(u / ANC_STEP + 1e-9), c: g - j - 1, t: lib.grid[g] - 5, d: s.d });
      }
    }
    const M = MS.length, need = tpNeed(M);
    for (const e of ['X', 'R']) {
      const E = ev[e], tc = new Array(L).fill(0);
      for (const p of E.pts) tc[p.c]++;
      E.tc = tc;
      E.bunches = tpRegions(tc).map(([lo, hi, ap]) => ({ c0: lo, c1: hi + 1, ap, n: tc.slice(lo, hi + 1).reduce((x, y) => x + y, 0) })).filter(u => u.n >= need);
      const ts = E.pts.map(p => p.t).sort((x, y) => x - y);
      E.half = tpQuant(ts, 1, 2); E.p70 = tpQuant(ts, 7, 10);
      const kmin = E.pts.reduce((m, p) => Math.min(m, p.k), Infinity), kmax = E.pts.reduce((m, p) => Math.max(m, p.k), -Infinity);
      const pc = E.pts.length ? new Array(kmax - kmin + 1).fill(0) : [];
      for (const p of E.pts) pc[p.k - kmin]++;
      E.pc = pc; E.kmin = E.pts.length ? kmin : 0;
      E.places = tpRegions(pc).map(([lo, hi, ap]) => {
        const mem = E.pts.filter(p => p.k - E.kmin >= lo && p.k - E.kmin <= hi), ts2 = mem.map(p => p.t).sort((x, y) => x - y);
        // the box's hours: the middle half of its sessions' ends (first and third quarter), so the accent shows
        const q1 = tpQuant(ts2, 1, 4), q3 = tpQuant(ts2, 3, 4);
        // the place's own cluster (operator 25.11 «один самый максимальный кластер»): its 5 min × 0,1 SD cell with the most
        // ends; ties — the earlier time, then the cell nearer the place's apex row
        const occ = new Map();
        for (const p of mem) { const kk = p.t + '|' + p.k; occ.set(kk, (occ.get(kk) || 0) + 1); }
        let top = null;
        for (const [kk, n] of occ) {
          const [t, k] = kk.split('|').map(Number), cand = { t, k, n };
          if (!top || n > top.n || (n === top.n && (t < top.t || (t === top.t && Math.abs(k - E.kmin - ap) < Math.abs(top.k - E.kmin - ap))))) top = cand;
        }
        return { k0: E.kmin + lo, k1: E.kmin + hi + 1, ap: E.kmin + ap, n: mem.length, t0: q1.t, t1: q3.t + 5, tq: tpQuant(ts2, 1, 2), top };
      }).filter(z => z.n >= need).sort((a, b2) => a.k0 - b2.k0);
      E.places.forEach((z, i) => { z.name = e + (i + 1); });
      E.out = E.pts.length - E.places.reduce((x, z) => x + z.n, 0);
    }
    ANC.memo = { key, T, j, g1, L, c0, h0, l0, u0, tol, M, need, pool: cand.length, ev, t1: lib.grid[g1], H };
    return ANC.memo;
  }
  // a level u of the DR grid (directed SD from today's IDR edge) on today's chart
  const ancY = (F, u) => V.Y(F.u2p(u));
  // the nearest free height for a label [x0, x1] around y (half height hh, step dy), alternating up and down, inside the
  // chart below its header line
  const ancFree = (placed, x0, x1, y, hh, dy) => {
    for (const off of [0, -1, 1, -2, 2, -3, 3, -4, 4]) {
      const yy = y + off * dy;
      if (yy < 54 || yy > V.plot.h - 10) continue;
      if (!placed.some(q => x0 < q[2] && x1 > q[0] && yy - hh < q[3] && yy + hh > q[1])) return yy;
    }
    return y;
  };
  const ancWord = (F, e) => (e === 'X') === (F.d0 > 0) ? 'вверх' : 'вниз';
  function ancChart(c, ctx) {
    const F = ctx.F, a = ancNow(ctx);
    V.ancHdr = null;
    c.save();
    c.font = '600 11px ' + FONT; c.textBaseline = 'top'; c.textAlign = 'left';
    const head = a.why || ('От свечи ' + clk(a.T - 5) + '–' + clk(a.T) + ' · похожих ' + a.M + ' · все дни · DR цел · ±' + String(a.tol).replace('.', ',') +
      ' SD · ' + ancHName() + ' ▾' + (a.M < ANC_MIN ? ' · мало сессий' : ''));
    const hw = c.measureText(head).width;
    c.fillStyle = 'rgba(8,9,12,.9)'; c.fillRect(8, 26, hw + 12, 18);
    c.fillStyle = a.why ? '#A3A8B3' : '#E6EAF0'; c.fillText(head, 14, 29);
    V.ancHdr = [8, 26, 20 + hw, 44];
    if (a.why || !a.M) { c.restore(); return; }
    const xA = V.X(a.T), xB = V.X(a.t1);
    // the anchor M5 as the small box: its high and low over the horizon, the line of the anchor
    c.strokeStyle = 'rgba(230,234,240,.45)'; c.setLineDash([2, 3]); c.lineWidth = 1;
    c.beginPath(); c.moveTo(Math.round(xA) + 0.5, 0); c.lineTo(Math.round(xA) + 0.5, V.plot.h); c.stroke();
    for (const u of [a.h0 / F.w0t, a.l0 / F.w0t]) { const y = Math.round(V.Y(F.u2p(u))) + 0.5; c.beginPath(); c.moveTo(V.X(a.T - 5), y); c.lineTo(xB, y); c.stroke(); }
    c.setLineDash([]);
    const placedL = [];
    for (const e of ['R', 'X']) {
      const E = a.ev[e];
      // the places: the band of the extensions' ends × the hours they came, the share of M
      for (const z of E.places) {
        // the place itself quiet (the operator reads the block himself); its one cluster bright, carried to the left
        const ya = ancY(F, z.k0 * ANC_STEP), yb = ancY(F, z.k1 * ANC_STEP), y0 = Math.min(ya, yb), hh = Math.max(3, Math.abs(yb - ya));
        const x0 = V.X(z.t0), x1 = Math.max(x0 + 4, V.X(z.t1));
        c.fillStyle = rgba(cfg[e], 0.06); c.fillRect(x0, y0, x1 - x0, hh);
        c.strokeStyle = rgba(cfg[e], 0.35); c.lineWidth = 1; c.setLineDash([3, 3]);
        c.strokeRect(Math.round(x0) + 0.5, Math.round(y0) + 0.5, Math.round(x1 - x0) - 1, Math.round(hh) - 1); c.setLineDash([]);
        const T0 = z.top;
        if (!T0) continue;
        const ca = ancY(F, T0.k * ANC_STEP), cb = ancY(F, (T0.k + 1) * ANC_STEP), cy0 = Math.min(ca, cb), ch = Math.max(3, Math.abs(cb - ca));
        const cx0 = V.X(T0.t), cx1 = Math.max(cx0 + 4, V.X(T0.t + 5));
        // its SD bounds to the left edge, translucent, with the name at the edge
        c.strokeStyle = rgba(cfg[e], 0.6); c.lineWidth = 1; c.setLineDash([6, 4]);
        for (const y of [Math.round(cy0) + 0.5, Math.round(cy0 + ch) - 0.5]) { c.beginPath(); c.moveTo(0, y); c.lineTo(cx0, y); c.stroke(); }
        c.setLineDash([]);
        c.fillStyle = rgba(cfg[e], 0.05); c.fillRect(0, cy0, cx0, ch);
        c.fillStyle = rgba(cfg[e], 0.6); c.fillRect(cx0, cy0, cx1 - cx0, ch);
        c.strokeStyle = mixW(cfg[e], 0.4); c.lineWidth = 1.5; c.strokeRect(Math.round(cx0) + 0.5, Math.round(cy0) + 0.5, Math.round(cx1 - cx0) - 1, Math.round(ch) - 1);
        const rng = ancSd(T0.k / 10) + '…' + ancSd((T0.k + 1) / 10).replace(/^[+−]/, '');
        c.font = '600 10px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'left';
        const lt = z.name + ' ' + rng, lw = c.measureText(lt).width, lym = clamp(cy0 + ch / 2, 54, V.plot.h - 8);
        const ly0 = ancFree(placedL, 6, 12 + lw, lym, 7, 15);
        placedL.push([6, ly0 - 7, 12 + lw, ly0 + 7]);
        c.fillStyle = 'rgba(8,9,12,.8)'; c.fillRect(6, ly0 - 7, lw + 6, 14); c.fillStyle = rgba(cfg[e], 0.95); c.fillText(lt, 9, ly0);
        // its words next to the cell: the name, the SD, the 5 minutes and its share of M
        const t = z.name + ' · ' + rng + ' · ' + clk(T0.t) + ' · ' + ancPct(T0.n / a.M) + '%';
        c.font = '700 11.5px ' + FONT;
        const tw = c.measureText(t).width;
        // to the right of the cell; when that runs into the price scale, to its left
        const lx = cx1 + 11 + tw <= V.plot.w ? cx1 + 5 : Math.max(0, cx0 - 11 - tw), ly = ancFree(placedL, lx, lx + tw + 6, clamp(cy0 + ch / 2, 54, V.plot.h - 10), 8, 17);
        placedL.push([lx, ly - 8, lx + tw + 6, ly + 8]);
        c.fillStyle = 'rgba(8,9,12,.88)'; c.fillRect(lx, ly - 8, tw + 6, 16); c.fillStyle = mixW(cfg[e], 0.2); c.fillText(t, lx + 3, ly);
      }
    }
    c.restore();
  }
  // the time band in 5-minute columns: when the extensions up (X half) and down (R half) ended; bunches framed with their
  // share of M, the marks ½ and 70 %
  function ancBand(c, ctx) {
    const F = ctx.F, a = ancNow(ctx), B = V.band, dir = F.d0 > 0 ? { X: -1, R: 1 } : { X: 1, R: -1 };
    V.bandOv = 0;
    c.save(); c.beginPath(); c.rect(B.x, B.y, B.w, B.h); c.clip();
    c.fillStyle = '#0A0B0F'; c.fillRect(B.x, B.y, B.w, B.h); c.fillStyle = C.grid; c.fillRect(B.x, B.y, B.w, 1);
    const cy = Math.round(B.y + B.h / 2) + 0.5, half = B.h / 2 - 4;
    c.fillStyle = C.grid; c.fillRect(B.x, cy, B.w, 1);
    c.font = '600 10px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'left';
    for (const e of ['X', 'R']) { c.fillStyle = rgba(cfg[e], 0.9); c.fillText((e === 'X' ? 'X ' : 'R ') + ancWord(F, e) + ' · когда кончилось расширение', B.x + 6, cy + dir[e] * (half - 4)); }
    if (!a.why && a.M) {
      const mx = Math.max(1, ...a.ev.X.tc, ...a.ev.R.tc), cx = i => V.X(lib5(a, i));
      const placedB = [];
      for (const e of ['X', 'R']) {
        const E = a.ev[e], inB = i => E.bunches.some(u => i >= u.c0 && i < u.c1);
        E.tc.forEach((n, i) => {
          if (!n) return;
          const x0 = cx(i) + 1, x1 = cx(i + 1) - 1, hh = Math.max(2, (half - 14) * n / mx), y = dir[e] < 0 ? cy - hh : cy + 1;
          c.fillStyle = rgba(cfg[e], (inB(i) ? 0.55 : 0.22) + 0.35 * n / mx); c.fillRect(x0, y, Math.max(1, x1 - x0), hh);
        });
        for (const u of E.bunches) {
          const x0 = cx(u.c0) + 0.5, x1 = cx(u.c1) - 0.5, yy = dir[e] < 0 ? cy - half + 10 : cy + 2, hh = half - 12;
          c.strokeStyle = rgba(cfg[e], 0.9); c.lineWidth = 1; c.strokeRect(Math.round(x0) + 0.5, Math.round(yy) + 0.5, Math.round(x1 - x0), Math.round(hh));
          c.font = '700 11px ' + FONT; c.textAlign = 'center'; c.fillStyle = mixW(cfg[e], 0.25);
          const lt = ancPct(u.n / a.M) + '%', lw = c.measureText(lt).width, lx = (x0 + x1) / 2, ly = dir[e] < 0 ? yy + 5 : yy + hh - 6;
          if (placedB.some(q => q[2] === e && Math.abs(q[0] - lx) < (q[1] + lw) / 2 + 3)) continue;   // no number over another
          placedB.push([lx, lw, e]); c.fillText(lt, lx, ly);
        }
        for (const [q, nm] of [[E.half, '½'], [E.p70, '70%']]) {
          if (!q) continue;
          const x = Math.round(V.X(q.t + 5)) + 0.5;
          c.strokeStyle = rgba(cfg[e], 0.9); c.setLineDash(nm === '½' ? [] : [4, 3]); c.beginPath(); c.moveTo(x, cy + dir[e]); c.lineTo(x, cy + dir[e] * (half + 2)); c.stroke(); c.setLineDash([]);
          c.font = '700 9.5px ' + FONT; c.textAlign = 'left'; c.fillStyle = rgba(cfg[e], 0.95); c.fillText(nm, x + 3, cy + dir[e] * (nm === '½' ? 8 : 18));
        }
      }
    }
    c.restore();
  }
  const lib5 = (a, i) => a.T + 5 * i;   // the open minute of the i-th M5 after the anchor
  // the price column: where the extensions ended, per ANC_STEP SD beyond the anchor (a density, not «хотя бы до»); the
  // rows of a place brighter, its name and share at its apex row
  function ancProj(c, ctx0) {
    const ctx = V.ctx || ctx0, F = ctx.F, a = ancNow(ctx), A_ = V.proj;
    c.fillStyle = C.axis; c.fillRect(A_.x, 0, A_.w, A_.h); c.fillStyle = C.grid; c.fillRect(A_.x, 0, 1, A_.h);
    V.projBars = [];
    c.save(); c.beginPath(); c.rect(A_.x, 0, A_.w, A_.h); c.clip();
    if (!a.why && a.M) {
      const x0 = A_.x + 46, blen = A_.w - 46 - 50;
      for (const e of ['X', 'R']) {
        const E = a.ev[e], mx = Math.max(1, ...E.pc), yE = Math.round(ancY(F, e === 'X' ? a.h0 / F.w0t : a.l0 / F.w0t)) + 0.5;
        c.strokeStyle = 'rgba(230,234,240,.5)'; c.beginPath(); c.moveTo(A_.x, yE); c.lineTo(A_.x + A_.w, yE); c.stroke();
        E.pc.forEach((n, i) => {
          if (!n) return;
          const k = E.kmin + i, ya = ancY(F, k * ANC_STEP), yb = ancY(F, (k + 1) * ANC_STEP), y0 = Math.min(ya, yb), hh = Math.max(1, Math.abs(yb - ya) - 1);
          if (y0 > A_.h - 38 || y0 + hh < 0) return;
          const z = E.places.find(q => k >= q.k0 && k < q.k1);
          c.fillStyle = rgba(cfg[e], z ? 0.85 : 0.3); c.fillRect(x0, y0, Math.max(1, blen * n / mx), hh);
          if (z && k === z.ap) {
            c.font = '700 10px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'left'; c.fillStyle = mixW(cfg[e], 0.2);
            c.fillText(z.name + ' ' + ancPct(z.n / a.M) + '%', x0 + blen * n / mx + 3, y0 + hh / 2);
          }
          if (hh >= 9 && (z || n / mx >= 0.5)) { c.font = '500 9px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'right'; c.fillStyle = '#8D93A0'; c.fillText(ancSd(k / 10), A_.x + 42, y0 + hh / 2); }
        });
      }
    }
    // the footer: the count, the horizon (a click changes it) and the rows that are not places
    c.fillStyle = 'rgba(10,11,15,.96)'; c.fillRect(A_.x + 1, A_.h - 52, A_.w - 1, 52);
    c.textBaseline = 'bottom'; c.textAlign = 'left'; c.font = '700 10px ' + FONT; c.fillStyle = '#C9CED8';
    c.fillText(a.why ? 'От этой свечи' : 'От ' + clk(a.T) + ' · похожих ' + a.M, A_.x + 6, A_.h - 36);
    c.font = '500 9.5px ' + FONT; c.fillStyle = '#8D93A0'; c.fillText('горизонт: ' + ancHName() + ' ▾', A_.x + 6, A_.h - 22);
    if (!a.why && a.M) {
      const r = e => { const E = a.ev[e]; return e + ': нет ' + ancPct(E.none / a.M) + '% · ещё шли ' + ancPct(E.open / a.M) + '%'; };
      c.fillText(r('X') + ' · ' + r('R'), A_.x + 6, A_.h - 8);
    }
    V.ancFoot = [A_.x, A_.h - 52, A_.x + A_.w, A_.h];
    c.restore();
  }
  // a click on the chart's header or the column's footer: the next horizon (30 / 60 min / to the block end)
  function ancClick(x, y) {
    const inR = r => r && x >= r[0] && x <= r[2] && y >= r[1] && y <= r[3];
    if (!inR(V.ancHdr) && !inR(V.ancFoot)) return false;
    ANC.hi = (ANC.hi + 1) % ANC.Hs.length; ANC.memo = null; render(true);
    return true;
  }
