  // ================= 23.5 · «Съёмы лоу» — the local layer (operator 2026-10-26) =================
  // An overlay over the main map of final R / X, switched by «Слои ▾ → Съёмы лоу». It never changes the main map, its
  // zones, N or percentages. Definition SW-0.1 (docs/DR-LAB-23-5-SWEEPS.md), in the operator's words of 26.10:
  //   the low = the session's deepest point after its confirmation at that moment (for a short, its highest point), that
  //   held at least one M5 (the next M5's low is higher): the low under which a trader keeps his stop;
  //   a sweep = a later M5 goes below that low by at least one tick (a wick counts);
  //   a continuation = after the sweep the session makes a new high (above its high so far), before its block ends.
  // One star = the bottom of the sweep (the deepest point between the sweep and the new high), at the open of its first
  // M5; a thin thread goes to the last held low it took. One session can have several stars; in a constellation it has
  // one vote. The constellations use the zone rule of screen 24 (0.1 SD x 15 minutes, 3 x 3 neighbourhood, half the
  // height of its own peak, support max(4, ceil(N/20))) over unique sessions, as the pullback candidate PB-0.1 does.
  // The data are the family on screen (the same F, N, own IDR scale, M5 paths the server publishes and the page checks);
  // the page computes, lab/sweeps235_ref.py recomputes for the checks. A session with a missing M5 after its
  // activation is unknown, as for R / X; so is one with an M5 that makes both a new low and a new high (no known order, no M1, operator
  // 21.10).
  const SWC = '#B89CFF', SW = { key: null, model: null };
  function swSession(F, m) {
    const bars = [];
    for (let j = 0; j < F.grid.length; j++) {
      const T = F.grid[j];
      if (T <= m.act) continue;
      const q = m.path[j];
      if (!q) return { status: 'UNKNOWN', events: [] };
      bars.push({ T, lo: q[0], hi: q[1] });
    }
    if (!bars.length) return { status: 'NONE', events: [] };
    let HS = -Infinity, LS = Infinity, held = null, pend = null, prevNewLow = null, ambiguous = false;
    const events = [];
    for (let i = 0; i < bars.length; i++) {
      const b = bars[i], newHigh = b.hi > HS, newLow = b.lo < LS;
      // the low that held: the previous M5 made a new session low and this one did not go below it
      if (prevNewLow && b.lo >= prevNewLow.lo) held = { v: prevNewLow.lo, t: prevNewLow.T - 5 };
      const sweeps = newLow && held && b.lo < held.v;
      if (pend && newHigh) {
        if (newLow) ambiguous = true;              // the new low and the new high in one M5: order unknown
        else { events.push({ ...pend, cont: b.T - 5 }); pend = null; }
      }
      if (sweeps && newHigh && !pend && HS > -Infinity) ambiguous = true;
      if (sweeps) {
        if (!pend) pend = { swing: held, bottom: { v: b.lo, t: b.T - 5 } };
        else { pend.swing = held; pend.bottom = { v: b.lo, t: b.T - 5 }; }
      } else if (newLow && pend) pend.bottom = { v: b.lo, t: b.T - 5 };
      prevNewLow = newLow ? b : null;
      if (newLow) LS = b.lo;
      if (newHigh) HS = b.hi;
    }
    if (pend) events.push({ ...pend, cont: null });
    if (ambiguous) return { status: 'UNKNOWN', events: [] };   // an M5 whose order decides the result, as a missing M5
    return { status: 'KNOWN', events };
  }
  function swRegions(byCase, bLo, bHi) {
    let kMin = Infinity, kMax = -Infinity;
    for (const cells of byCase.values()) for (const c of cells) { const k = +c.split('|')[0]; kMin = Math.min(kMin, k); kMax = Math.max(kMax, k); }
    if (!isFinite(kMin) || bHi < bLo) return [];
    const kLo = kMin - 1, nk = kMax + 1 - kLo + 1, nb = bHi - bLo + 1, D = new Int32Array(nk * nb), at = (i, j) => i * nb + j;
    for (const cells of byCase.values()) {
      const dil = new Uint8Array(nk * nb);
      for (const c of cells) {
        const [k, b] = c.split('|').map(Number);
        if (b < bLo || b > bHi) continue;
        for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) {
          const i = k - kLo + di, j = b - bLo + dj;
          if (i >= 0 && i < nk && j >= 0 && j < nb) dil[at(i, j)] = 1;
        }
      }
      for (let x = 0; x < D.length; x++) D[x] += dil[x];
    }
    const peak = [];
    for (let i = 0; i < nk; i++) for (let j = 0; j < nb; j++) {
      const v = D[at(i, j)];
      if (v <= 0) continue;
      let top = true;
      for (let di = -1; di <= 1 && top; di++) for (let dj = -1; dj <= 1; dj++) {
        const a = i + di, c = j + dj;
        if (a >= 0 && a < nk && c >= 0 && c < nb && D[at(a, c)] > v) { top = false; break; }
      }
      if (top) peak.push([i, j, v]);
    }
    const out = [], seen = new Set();
    for (const lam of [...new Set(peak.map(p => p[2] / 2))].sort((a, b) => b - a)) {
      const lab = new Int32Array(nk * nb).fill(-1);
      let n = 0;
      for (let s = 0; s < D.length; s++) {
        if (lab[s] >= 0 || D[s] < lam) continue;
        const stack = [s]; lab[s] = n;
        while (stack.length) {
          const x = stack.pop(), i = Math.floor(x / nb), j = x % nb;
          for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) {
            const a = i + di, c = j + dj;
            if (a < 0 || a >= nk || c < 0 || c >= nb) continue;
            const y = at(a, c);
            if (lab[y] < 0 && D[y] >= lam) { lab[y] = n; stack.push(y); }
          }
        }
        n++;
      }
      for (const [i, j, v] of peak) {
        if (v !== 2 * lam) continue;
        const L = lab[at(i, j)], key = lam + '|' + L;
        if (seen.has(key)) continue;
        seen.add(key);
        let mx = 0; const cells = [];
        for (let s = 0; s < D.length; s++) if (lab[s] === L) { mx = Math.max(mx, D[s]); cells.push([Math.floor(s / nb) + kLo, s % nb + bLo]); }
        if (mx !== v) continue;
        out.push({ cells, top: v });
      }
    }
    return out;
  }
  function swModel(F) {
    const key = F && F.r && F.r.snapshot_id + '|' + F.view + '|' + F.N;
    if (!key) return null;
    if (SW.key === key) return SW.model;
    const cats = { CONT: 0, NOCONT: 0, NONE: 0, UNKNOWN: 0 }, stars = [], byCase = new Map(), w0 = F.r.key && F.r.key.window;
    F.M.forEach((m, mi) => {
      const s = swSession(F, m);
      if (s.status !== 'KNOWN') { cats[s.status]++; return; }
      const cont = s.events.filter(e => e.cont != null);
      cats[cont.length ? 'CONT' : s.events.length ? 'NOCONT' : 'NONE']++;
      for (const e of cont) {
        const k = Math.floor(10 * e.bottom.v / m.w), b = Math.floor((e.bottom.t - F.f) / 15);
        stars.push({ m, mi, e, k, b, u: e.bottom.v / m.w, us: e.swing.v / m.w, t: e.bottom.t, ts: e.swing.t, brk: m.brk != null && m.brk <= e.bottom.t + 5 });
        if (!byCase.has(m.id)) byCase.set(m.id, new Set());
        byCase.get(m.id).add(k + '|' + b);
      }
    });
    const need = Math.max(4, Math.ceil(F.N / 20)), bLo = w0 ? Math.floor((w0[0] - F.f) / 15) : 0, bHi = Math.floor((F.end - 5 - F.f) / 15);
    const zones = [];
    for (const { cells, top } of swRegions(byCase, bLo, bHi)) {
      const cs = new Set(cells.map(c => c[0] + '|' + c[1])), members = [...byCase].filter(([, s]) => [...s].some(c => cs.has(c))).map(([id]) => id);
      if (members.length < need) continue;
      const kk = cells.map(c => c[0]), bb = cells.map(c => c[1]), inside = stars.filter(q => cs.has(q.k + '|' + q.b) && members.includes(q.m.id));
      const depth = inside.map(q => q.us - q.u).sort((a, b) => a - b);
      zones.push({ cells: cs, top, members, n: members.length, k0: Math.min(...kk), k1: Math.max(...kk) + 1,
        t0: F.f + 15 * Math.min(...bb), t1: F.f + 15 * (Math.max(...bb) + 1), stars: inside, depth: depth[Math.floor((depth.length - 1) / 2)] });
    }
    zones.sort((a, b) => a.t0 - b.t0 || b.n - a.n);
    zones.forEach((z, i) => { z.label = 'С' + (i + 1); });
    const used = new Set(zones.flatMap(z => z.members));
    SW.key = key; SW.model = { cats, stars, zones, need, inZones: used.size, N: F.N };
    return SW.model;
  }
  // the words follow the side: for a short the stop is above the session's high and the continuation is a new low
  const swW = F => F.d0 > 0 ? { low: 'лоу', high: 'хай' } : { low: 'хай', high: 'лой' };
  const swOn = ctx => st.L.sweep && st.mode === 'bounds' && ctx.F && ctx.F.N && !ctx.F.brk;
  function drawSweeps(c, ctx) {
    if (!swOn(ctx)) { V.sw = null; return; }
    const F = ctx.F, M = swModel(F), cut = sliceOf(ctx), geo = [];
    if (!M) return;
    const P = u => V.Y(F.u2p(u)), Xt = t => V.X(t + 2.5), past = q => q.t + 5 <= cut;
    c.save();
    for (const z of M.zones) for (const q of z.stars) {          // the haze of a constellation: its own stars only
      const x = Xt(q.t), y = P(q.u), g = c.createRadialGradient(x, y, 0, x, y, 16);
      g.addColorStop(0, rgba(SWC, past(q) ? 0.05 : 0.12)); g.addColorStop(1, rgba(SWC, 0));
      c.fillStyle = g; c.fillRect(x - 16, y - 16, 32, 32);
    }
    // only the stars of a constellation, as on the main map since the operator's edit of 16.10 (a lone star is noise)
    for (const q of M.zones.flatMap(z => z.stars)) {
      const x = Xt(q.t), y = P(q.u), xs = Xt(q.ts), ys = P(q.us), a = past(q) ? 0.35 : 1;
      c.strokeStyle = rgba(SWC, 0.28 * a); c.lineWidth = 0.8; c.beginPath(); c.moveTo(xs, ys); c.lineTo(x, y); c.stroke();
      c.fillStyle = rgba(SWC, 0.85 * a); c.beginPath(); c.arc(x, y, 1.8, 0, 2 * Math.PI); c.fill();
      if (q.brk) { c.strokeStyle = rgba(SWC, 0.8 * a); c.beginPath(); c.arc(x, y, 3.4, 0, 2 * Math.PI); c.stroke(); }
      geo.push({ x, y, q });
    }
    const lbl_ = [];
    c.font = '600 11px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle';
    M.zones.forEach((z, i) => {
      const xs = z.stars.map(q => Xt(q.t)), ys = z.stars.map(q => P(q.u));
      const x = xs.reduce((a, b) => a + b, 0) / xs.length, y = ys.reduce((a, b) => a + b, 0) / ys.length;
      const t = z.label + ' ' + pct(100 * z.n / M.N), w = c.measureText(t).width;
      c.fillStyle = rgba(SWC, z.t1 <= cut ? 0.35 : 0.7); c.fillText(t, x, y);
      lbl_.push({ i, box: [x - w / 2 - 3, y - 8, w + 6, 16] });
    });
    c.restore();
    V.sw = { geo, lbl: lbl_ };
  }
  function swHit(x, y) {
    if (!V || !V.sw) return null;
    let best = null, bd = 5;
    for (const o of V.sw.geo) { const d = Math.hypot(o.x - x, o.y - y); if (d < bd) { bd = d; best = o; } }
    if (best) return { k: 'sw', mi: best.q.mi, t: best.q.t };
    for (const L of V.sw.lbl) if (x >= L.box[0] && x <= L.box[0] + L.box[2] && y >= L.box[1] && y <= L.box[1] + L.box[3]) return { k: 'swzone', i: L.i };
    return null;
  }
  function swInspector(ctx, h) {
    const F = ctx.F, M = F && swModel(F);
    if (!M) return '';
    const P = u => px(F.u2p(u)), W = swW(F);
    if (h.k === 'swzone') {
      const z = M.zones[h.i];
      if (!z) return '';
      return '<div class="ih" style="color:' + SWC + '">' + z.label + ' · съёмы ' + W.low + ' · ' + pct(100 * z.n / M.N) + '</div>' +
        '<div class="is">' + clk(z.t0) + '–' + clk(z.t1) + ' · ' + band(z.k0, z.k1) + ' SD</div>' +
        '<div class="is">У ' + z.n + ' из ' + M.N + ' сессий семьи здесь кончался съём ' + W.low + ', после которого был новый ' + W.high + ' сессии.</div>' +
        '<div class="is">Обычно дальше снятого ' + W.low + ' на ' + sd(z.depth).replace('+', '') + ' SD (медиана).</div>' +
        '<div class="ifoot">История семьи, не прогноз. Локальный слой 23.5, кандидат.</div>';
    }
    const m = F.M[h.mi], q = M.stars.find(s => s.mi === h.mi && s.t === h.t);
    if (!m || !q) return '';
    return '<div class="ih" style="color:' + SWC + '">Съём ' + W.low + ' · ' + esc(m.date) + '</div>' +
      '<div class="is">' + (W.low === 'лоу' ? 'Лоу' : 'Хай') + ' держался: ' + sd(q.us) + ' SD · ' + P(q.us) + ' · ' + clk(q.ts) + '</div>' +
      '<div class="is">Сняли до: ' + sd(q.u) + ' SD · ' + P(q.u) + ' · ' + clk(q.t) + ' · дальше на ' + sd(q.us - q.u).replace('+', '') + ' SD</div>' +
      '<div class="is">Новый ' + W.high + ' сессии: ' + clk(q.e.cont) + (q.brk ? ' · DR к этому моменту сломан' : '') + '</div>' +
      '<div class="ifoot">Точка и нить — эта историческая сессия. Цены — в сегодняшней шкале.</div>';
  }
  function swPanel(F, ctx) {
    if (!swOn(ctx)) return '';
    const M = swModel(F);
    if (!M) return '';
    const W = swW(F), row = (t, n) => '<div class="r"><span class="t"><span>' + t + '</span></span><b>' + pct(100 * n / M.N) + '</b></div>';
    const cut = sliceOf(ctx);
    return '<div class="p24-sweeps"><div class="p21-h second"><span style="color:' + SWC + '">Съёмы ' + W.low + ' · локальный слой' + candTag() + '</span></div>' +
      '<div class="p21-note">' + W.low + ' сессии, который держался, сняли хотя бы на тик — доля всей семьи</div>' +
      row('сняли и потом новый ' + W.high + ' сессии', M.cats.CONT) + row('сняли, нового ' + (W.high === 'хай' ? 'хая' : 'лоя') + ' не было', M.cats.NOCONT) +
      row(W.low + ' не снимали', M.cats.NONE) + row('неизвестно · нет свечи M5', M.cats.UNKNOWN) +
      M.zones.map(z => '<div class="r" style="opacity:' + (z.t1 <= cut ? .55 : 1) + '"><span class="t"><span>' + clk(z.t0) + '–' + clk(z.t1) + ' <i style="color:' + SWC + '">' + z.label + '</i><br><span class="p21-sub">' + band(z.k0, z.k1) + ' SD · обычно дальше ' + W.low + ' на ' + sd(z.depth).replace('+', '') + ' SD</span></span></span><b>' + pct(100 * z.n / M.N) + '</b></div>').join('') +
      (M.zones.length ? '' : '<div class="p21-note">сгущений съёмов нет по правилу зон</div>') + '</div>';
  }
  // for the checks (tests/sweeps235_page.mjs, the browser): the model of the family on screen
  window.__sw235 = () => { const c = cur(); return c.F ? swModel(c.F) : null; };
