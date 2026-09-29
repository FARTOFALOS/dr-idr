  // Design 22: the right panel of design 21 (percentages only, every line a link to the chart), changed by the audit of
  // 2026-09-29 (meaning/04-dizajn-22.md): a match mark says how today's price was matched in the history and, when it
  // was not, no percentage is shown (a dash is «no fitting history», not zero); every row names its event, horizon and
  // match on hover; a place's time is when its sessions first came there; before a confirmation «до DR high / low»
  // counts each session's own DR; «тенью за DR» beside «DR удержится»; no «пусто». Same synthetic data as design 21.
  const P21 = { get compare() { return !!st.L.snap21; }, snapshots: new Map(), links: [] };

  function p21Key(h) {
    if (!h) return '';
    return [h.k, h.role, h.id, h.slice, h.pLo, h.pHi, h.t0, h.t1, h.T, h.i, h.t, h.p, h.hot].join('|');
  }
  function p21Pin(h) {
    if (!h) return;
    st.pin = p21Key(st.pin) === p21Key(h) ? null : h;
    st.hover = null;
    render(true);
  }
  // the screen at the confirmation (grey contours on the chart; «Слои» → «Контуры на момент подтверждения»)
  function p21Snapshot(ctx) {
    if (ctx.s.conf == null || ctx.s.conf > ctx.obs) return null;
    const key = ctx.D.d + '|' + ctx.s.k + '|' + ctx.s.conf;
    if (!P21.snapshots.has(key)) {
      const s = sess(ctx.D, ctx.s.k, ctx.s.conf, false), ov = overlay(ctx.D, s);
      if (!ov) return null;
      P21.snapshots.set(key, { D: ctx.D, s, ov, obs: s.conf, live: false });
    }
    return P21.snapshots.get(key);
  }

  // ---------- what a link shows ----------
  // the densest spot of a place: its densest price step (0.1 IDR) and, in it, the densest time window of the extremes
  function hotOf(ov, R, k) {
    if (!k.all || !k.all.length) return null;
    const cnt = new Map();
    for (const q of k.all) { const b = Math.floor(q.u / 0.1 + 1e-9); cnt.set(b, (cnt.get(b) || 0) + 1); }
    let best = null;
    for (const [b, n] of cnt) if (!best || n > best[1]) best = [b, n];
    const pb = R.pb.find(q => q.b === best[0]);
    if (!pb) return null;
    const tc = timeCluster(ov, R, pb.pLo, pb.pHi);
    return tc && { pLo: pb.pLo, pHi: pb.pHi, p: (pb.pLo + pb.pHi) / 2, binPct: pb.pct, tc };
  }
  // when similar sessions first reached a price after the moment (5-minute bars), and the densest window of it;
  // own = 'H' | 'L': each session's own DR high / low instead of today's price (design 22, before a confirmation)
  function firstTouch(ov, p, own) {
    const u = ov.p2u(p), up = own ? own === 'H' : u >= ov.u0, bins = new Map();
    let n = 0;
    for (const q of ov.sims) {
      const lv = own ? (own === 'H' ? q.uH : q.uL) : u;
      if (lv == null) continue;
      for (let j = 0; j < ov.grid.length; j++) {
        const v = up ? q.hi[j] : q.lo[j];
        if (v != null && (up ? v >= lv : v <= lv)) { const T = ov.grid[j] - 5; bins.set(T, (bins.get(T) || 0) + 1); n++; break; }
      }
    }
    if (!n) return null;
    let pk = null;
    for (const [b, c] of bins) if (!pk || c > pk[1]) pk = [b, c];
    let t0 = pk[0], t1 = pk[0] + 5, m = pk[1];
    while ((bins.get(t0 - 5) || 0) >= 0.6 * pk[1]) { t0 -= 5; m += bins.get(t0); }
    while ((bins.get(t1) || 0) >= 0.6 * pk[1]) { m += bins.get(t1); t1 += 5; }
    return { bins: [...bins].sort((a, b) => a[0] - b[0]), peak: pk[1], t0, t1, pct: 100 * m / ov.N, all: 100 * n / ov.N };
  }
  // before the stars are drawn: resolve the link under the mouse into a window for the axes, the strip and the stars
  function prep21(ctx) {
    V.h21 = null;
    const h = hv(), ov = ctx.ov;
    if (!h || !ov) return;
    if (h.k === 'place') {
      const R = ov.roles.find(r => r.id === h.role), k = R && R.cons.find(q => q.id === h.id);
      if (!k) return;
      const en = k.entry && !k.entry.now ? k.entry : null;
      V.h21 = { k: 'place', R, zone: k, en };
      if (en) { const p = ov.u2p(en.edge); V.win = { t0: en.t0, t1: en.t1, pA: p, pB: p, col: R.col }; }
    } else if (h.k === 'times' || h.k === 'zone') {
      V.h21 = h;
    } else if (h.k === 'step') {
      const ft = ov.match === 'none' ? null : firstTouch(ov, h.p, h.own);
      V.h21 = { k: 'step', p: h.p, name: h.name, ft };
      if (ft) V.win = { t0: ft.t0, t1: ft.t1, pA: h.p, pB: h.p, col: '#E9EEF5' };
    }
  }
  function drawTC21(c, col, tc, pLo, pHi, xFrom, xTo) {
    const y0 = V.Y(pHi), y1 = V.Y(pLo), mid = (y0 + y1) / 2, hh = Math.max(16, y1 - y0), top = mid - hh / 2;
    c.fillStyle = rgba(col, 0.09); c.fillRect(xFrom, top, xTo - xFrom, hh);
    for (const [b, n] of tc.bins) {
      const x0 = V.X(b) + 0.5, x1 = V.X(b + 5) - 0.5, bh = Math.max(1.5, hh * n / tc.peak), inW = b >= tc.t0 && b < tc.t1;
      c.fillStyle = rgba(col, inW ? 0.95 : 0.35); c.fillRect(x0, top + hh - bh, Math.max(1, x1 - x0), bh);
    }
    const xa = Math.round(V.X(tc.t0)) + 0.5, xb = Math.round(V.X(tc.t1)) + 0.5;
    c.strokeStyle = rgba(col, 1); c.lineWidth = 1.5; c.strokeRect(xa, Math.round(top) + 0.5, xb - xa, Math.round(hh));
    c.fillStyle = rgba(col, 0.1); c.fillRect(xa, top + hh, xb - xa, V.plot.h - top - hh);
    c.strokeStyle = rgba(col, 0.6); c.lineWidth = 1; c.setLineDash([3, 3]);
    c.beginPath(); c.moveTo(xa, top + hh); c.lineTo(xa, V.plot.h); c.moveTo(xb, top + hh); c.lineTo(xb, V.plot.h); c.stroke(); c.setLineDash([]);
  }
  function brightLine(c, p, text, xl) {
    const y = Math.round(V.Y(p)) + 0.5;
    c.strokeStyle = 'rgba(246,248,252,.95)'; c.lineWidth = 2; c.setLineDash([]);
    c.beginPath(); c.moveTo(0, y); c.lineTo(V.plot.w, y); c.stroke();
    if (text) {
      c.font = '700 12px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'right';
      const w = c.measureText(text).width + 10;
      const xr = xl != null ? xl + w : V.plot.w - 8;
      c.fillStyle = '#F4F6FA'; roundRect(c, xr - w, y - 9, w, 18, 3); c.fill();
      c.fillStyle = '#0B0C10'; c.fillText(text, xr - 5, y + 0.5); c.textAlign = 'left';
    }
  }
  // after the levels: the lit link (a place: its borders and when its sessions first came there; a step: the line and
  // when it was usually first reached; a level: the line)
  function drawReference21(c, ctx) {
    const h = hv(), ov = ctx.ov;
    if (!h) return;
    if (h.k === 'lvl' || h.k === 'prev') {
      const p = h.k === 'lvl' ? h.l && h.l.p : h.p;
      if (Number.isFinite(p)) brightLine(c, p, h.k === 'lvl' && h.l ? (h.l.type === 'std' ? h.l.name : h.l.full) : null);
      return;
    }
    const H = V.h21;
    if (!H || !ov) return;
    if (H.k === 'place') {
      const k = H.zone, s = ctx.s;
      for (const u of [k.lo, k.hi]) {
        if (!isFinite(u)) continue;
        const p = ov.u2p(u), l = levels(s).find(q => Math.abs(q.p - p) < 1e-6);
        brightLine(c, p, (l ? (l.type === 'std' ? l.name : l.full) + ' · ' : 'граница места · ') + px(p), V.X(ov.obs) + 10);
      }
      if (H.en) { const p = ov.u2p(H.en.edge), d = (V.p1 - V.p0) * 0.004; drawTC21(c, H.R.col, H.en, p - d, p + d, V.X(ov.obs), V.X(ov.end)); }
    } else if (H.k === 'times') {
      if (H.from != null) { const xa = V.X(H.from), xb = V.X(H.ts[0].t); c.fillStyle = 'rgba(246,248,252,.05)'; c.fillRect(Math.min(xa, xb), 0, Math.abs(xb - xa), V.plot.h); }
      for (const q of H.ts) {
        const x = Math.round(V.X(q.t)) + 0.5;
        c.strokeStyle = 'rgba(246,248,252,.9)'; c.lineWidth = 1.5; c.setLineDash([5, 4]);
        c.beginPath(); c.moveTo(x, 0); c.lineTo(x, V.plot.h); c.stroke(); c.setLineDash([]);
        c.font = '700 11.5px ' + FONT; c.textBaseline = 'top';
        const w = c.measureText(q.label).width + 10;
        c.fillStyle = '#F4F6FA'; roundRect(c, x - w / 2, 96, w, 18, 3); c.fill();
        c.fillStyle = '#0B0C10'; c.textAlign = 'center'; c.fillText(q.label, x, 99); c.textAlign = 'left';
      }
    } else if (H.k === 'zone') {
      const ya = V.Y(Math.max(H.pA, H.pB)), yb = V.Y(Math.min(H.pA, H.pB));
      c.fillStyle = rgba(H.col || '#F4F6FA', 0.13); c.fillRect(0, ya, V.plot.w, Math.max(2, yb - ya));
      brightLine(c, H.pA, H.name + ' · ' + px(H.pA), V.X(ov.obs) + 10);
      if (Math.abs(H.pB - H.pA) > 1e-9) brightLine(c, H.pB, px(H.pB), V.X(ov.obs) + 10);
    } else if (H.k === 'step') {
      brightLine(c, H.p, H.name);
      if (H.ft) drawTC21(c, '#E9EEF5', H.ft, H.p - (V.p1 - V.p0) * 0.004, H.p + (V.p1 - V.p0) * 0.004, V.X(ov.obs), V.X(ov.end));
    }
  }
  function drawSnapshot21(c, ctx) {
    const snap = P21.compare && p21Snapshot(ctx);
    if (!snap) return;
    c.save(); c.setLineDash([4, 5]);
    for (const R of snap.ov.roles) for (const k of R.cons) {
      const g = k.g;
      if (!g || !g.segs) continue;
      c.strokeStyle = 'rgba(171,180,194,.35)'; c.lineWidth = 1;
      c.beginPath();
      for (let i = 0; i < g.segs.length; i += 5) {
        if (g.segs[i + 4] !== g.coreId) continue;
        c.moveTo(V.X(g.t0 + g.segs[i] * g.dt), V.Y(snap.ov.u2p(g.u0 + g.segs[i + 1] * g.du)));
        c.lineTo(V.X(g.t0 + g.segs[i + 2] * g.dt), V.Y(snap.ov.u2p(g.u0 + g.segs[i + 3] * g.du)));
      }
      c.stroke();
    }
    c.setLineDash([]); c.font = '12px ' + FONT; c.fillStyle = '#AAB5C4'; c.fillText('Серые контуры · как было на подтверждении ' + clk(snap.obs), 10, 76); c.restore();
  }

  // ---------- the panel ----------
  // a link row; `mean` = its meaning on hover (event · horizon · match), plain text
  function link(h, html, cls, mean) { const i = P21.links.push(h) - 1; return '<div class="p21-link' + (cls ? ' ' + cls : '') + '" data-l21="' + i + '"' + (mean ? ' title="' + esc(mean) + '"' : '') + '>' + html + '</div>'; }
  function lvlObj(s, id) { return levels(s).find(l => l.id === id); }
  // targets ahead in the direction of the side in play (the next STD steps not yet taken, the session extreme, past
  // sessions' DR, the nearest open VIB)
  function targets21(ctx) {
    const s = ctx.s, ov = ctx.ov, side = ov.mode === 'brk' ? s.nside : s.side, w = s.idrH - s.idrL, out = [];
    const ahead = p => side === 1 ? p > s.priceNow + 1e-9 : p < s.priceNow - 1e-9;
    const edge = ov.mode === 'brk' ? s.nedge : s.edge, done = (ov.mode === 'brk' ? s.takenN : s.taken) || [];
    for (let j = 1; j <= 6; j++) { const p = edge + side * j * w / 2; if (ahead(p) && !done.some(q => q.j === j && q.t)) out.push({ p, name: stepName(j, side === 1) }); }
    const bars = ctx.D.bars.filter(b => b.t >= s.start && b.t < Math.min(ctx.obs, s.end) && (ctx.live || b.t + 5 <= ctx.obs));
    if (bars.length) { const e = side === 1 ? Math.max(...bars.map(b => b.h)) : Math.min(...bars.map(b => b.l)); if (ahead(e)) out.push({ p: e, name: side === 1 ? 'максимум сессии' : 'минимум сессии' }); }
    for (const P of prevList(ctx)) { const p = side === 1 ? P.s.drH : P.s.drL; if (ahead(p)) out.push({ p, name: P.name + (side === 1 ? ' DR high' : ' DR low') }); }
    for (const v of vibsKnown(ctx)) if (v.fill == null) { const p = side === 1 ? v.lo : v.hi; if (ahead(p)) out.push({ p, name: 'VIB' }); }
    out.sort((a, b) => Math.abs(a.p - s.priceNow) - Math.abs(b.p - s.priceNow));
    const res = [], kind = q => q.name === 'VIB' ? 'vib' : /^[+−]\d/.test(q.name) ? 'std' : 'lvl', cap = { vib: 1, std: 2, lvl: 3 }, used = { vib: 0, std: 0, lvl: 0 };
    for (const q of out) {
      if (res.some(r => Math.abs(r.p - q.p) < 0.06 * w) || used[kind(q)] >= cap[kind(q)]) continue;
      used[kind(q)]++; res.push(q);
      if (res.length === 4) break;
    }
    return res.sort((a, b) => Math.abs(a.p - s.priceNow) - Math.abs(b.p - s.priceNow));
  }
  function quant(a, f) { const v = a.slice().sort((x, y) => x - y); return v.length ? v[Math.min(v.length - 1, Math.round(f * (v.length - 1)))] : null; }
  function panelHtml(ctx) {
    const s = ctx.s, ov = ctx.ov;
    P21.links = [];
    if (!ov) {
      const msg = API && (!A.day || A.day.status !== 'ok') ? (A.day && A.day.message) || 'Загружаю свечи…' :
        s.status === 'forming' ? 'Коробка ещё формируется' : s.status === 'before' ? 'Сессия ещё не началась' :
        ['confirmed', 'broken', 'waiting'].includes(s.status) ? (API && A.cohorts.size ? 'Похожих сессий нет' : 'Ищу похожие сессии…') : s.status === 'noconf' ? 'Сессия закончилась без подтверждения' : 'Сессия закончилась';
      panel.innerHTML = '<div class="p21-empty">' + esc(msg) + '</div>';
      return;
    }
    const side = ov.mode === 'brk' ? s.nside : s.side, out = [], none = ov.match === 'none';
    const P = v => none || v == null ? '—' : pct(v);                     // a dash = no fitting history, not zero
    const hor = 'после ' + clk(ctx.obs) + ' до ' + clk(ov.end), m = MATCH[ov.match];
    const M = ev => ev + ' · ' + hor + ' · ' + m;                          // the meaning of a row, on hover
    const row = (text, val) => '<span class="t">' + text + '</span><b>' + val + '</b>';
    const mark = { p25: '●', p50: '◐', none: '○' }[ov.match];
    out.push('<div class="p21-h"><span title="' + esc(m + ' · ' + (ov.cond || '')) + '">Дальше по похожим <i class="p22-match m-' + ov.match + '">' + mark + '</i></span><span>после ' + clk(ctx.obs) + '</span></div>');
    if (none) out.push('<div class="p21-note" title="' + esc('Похожих, у которых цена была там же, где сегодня, в истории не набралось. Такие проценты на новых днях были не лучше постоянной оценки (цели — хуже), поэтому их нет. Прочерк — это отсутствие подходящей истории, а не ноль.') + '">цена не сопоставлена · процентов нет</div>');
    if (ov.mode === 'wait') {
      out.push('<div class="p21-dir"><span class="lb" title="' + esc(M('первое подтверждение позже (закрытие M5 за своим DR); «нет» — не было до конца сессии')) + '">Подтверждение</span>' +
        link({ k: 'lvl', id: 'drH', l: lvlObj(s, 'drH') }, '↑ <b>' + P(ov.dir.up) + '</b>', 'in') +
        link({ k: 'lvl', id: 'drL', l: lvlObj(s, 'drL') }, '↓ <b>' + P(ov.dir.dn) + '</b>', 'in') +
        '<span class="p21-no">нет <b>' + P(ov.dir.none) + '</b></span></div>');
      if (ov.ownH != null) {
        out.push(link({ k: 'step', p: s.drH, name: 'DR high', own: 'H' }, row('до своего DR high', P(ov.ownH)), '', M('цена похожей сессии хотя бы раз дошла до собственного DR high (как и ↑)')));
        out.push(link({ k: 'step', p: s.drL, name: 'DR low', own: 'L' }, row('до своего DR low', P(ov.ownL)), '', M('цена похожей сессии хотя бы раз дошла до собственного DR low (как и ↓)')));
      }
    }
    for (const R of ov.roles) {
      const k = R.cons.slice().sort((a, b) => b.pct - a.pct)[0];
      const ev = (R.id === 'pull' || R.id === 'dn' ? 'окончательный минимум' : 'окончательный максимум') + ' попал в полосу места';
      if (k && k.n) out.push(link({ k: 'place', role: R.id, id: k.id }, row('<i style="color:' + R.col + '">' + R.name.toLowerCase() + '</i> чаще всего ' + k.name, P(k.pct)), '', M(ev)));
    }
    out.push(link({ k: 'col', t0: ctx.obs, t1: ctx.obs + ov.near }, row('в первые ' + ov.near + ' минут', ov.roles.map(R => '<i style="color:' + R.col + '">' + P(R.nearPct) + '</i>').join(' · ')), 'dim', M('окончательный экстремум случился в первые минуты')));
    // the three places per side: share of the band, the densest price in it, and when its sessions first came there
    out.push('<div class="p21-h second">Места <span>цена · впервые здесь</span></div>');
    const mx = Math.max(1, ...ov.roles.flatMap(r => r.cons.map(k => k.pct)));
    for (const R of ov.roles) {
      const arrow = ov.mode === 'wait' ? '' : ((R.id === 'cont' ? side : -side) === 1 ? ' ↑' : ' ↓');
      out.push('<div class="p21-g"><i style="background:' + R.col + '"></i>' + R.name + arrow + '</div>');
      for (const k of R.cons.slice().sort((a, b) => b.sortP - a.sortP)) {
        const hot = k.n ? hotOf(ov, R, k) : null, en = k.entry;
        const when = !k.n ? '' : en && en.now ? 'сейчас' : en && !none ? clk(en.t0) + '–' + clk(en.t1) : '';
        const ev = (R.id === 'pull' || R.id === 'dn' ? 'окончательный минимум' : 'окончательный максимум') + ' попал в полосу «' + k.name + '» (вся полоса, не только ядро); «впервые» — когда эти сессии первый раз дошли до полосы';
        out.push(link({ k: 'place', role: R.id, id: k.id },
          '<span class="bar" style="width:' + (none ? 0 : 100 * k.pct / mx).toFixed(1) + '%;background:' + R.col + '"></span><b style="color:' + R.col + '">' + P(k.pct) + '</b><span class="z">' + k.short + '</span><span class="pr">' + (hot && !none ? px(hot.p) : '—') + '</span><span class="tm">' + when + '</span>', 'place', M(ev)));
      }
    }
    if (ov.mode !== 'wait') {
      // targets ahead: the share of similar sessions that got there, and when they usually first did
      const T = targets21(ctx);
      if (T.length) {
        out.push('<div class="p21-h second">Цели <span>обычно к · дошли</span></div>');
        for (const q of T) {
          const ft = none ? null : firstTouch(ov, q.p);
          out.push(link({ k: 'step', p: q.p, name: q.name }, '<span class="t">' + esc(q.name) + ' · ' + px(q.p) + '</span><span class="tm2">' + (ft ? clk(ft.t0) : '') + '</span><b>' + P(none ? null : ov.touch(q.p)) + '</b>', 'tgt', M('цена хотя бы раз дошла до уровня; «обычно к» — самое частое окно первого касания')));
        }
      }
    }
    // time: by when half (and 70 %) of the final extremes had been reached
    out.push('<div class="p21-h second">Время экстремума <span>половина достигнута к</span></div>');
    for (const R of ov.roles) {
      const ts = R.stars.map(q => q.t), t50 = quant(ts, 0.5), t70 = quant(ts, 0.7);
      if (t50 == null) continue;
      const deep = R.id === 'pull' || R.id === 'dn';
      const text = '<i style="color:' + R.col + '">' + R.name.toLowerCase() + '</i>: ' + (none ? '—' : clk(t50) + (deep ? ' · 70% к ' + clk(t70) : ''));
      const ts2 = none ? [] : [{ t: t50, label: '50% · ' + clk(t50) }].concat(deep ? [{ t: t70, label: '70% · ' + clk(t70) }] : []);
      out.push(link({ k: 'times', from: ctx.obs, ts: ts2.length ? ts2 : [{ t: ctx.obs, label: clk(ctx.obs) }] }, '<span class="t">' + text + '</span>' + (!none && t50 <= ctx.obs ? '<span class="p21-past">прошло</span>' : ''), 'time',
        M('момент, когда был достигнут окончательный экстремум; окончательным он стал только к концу сессии')));
    }
    if (ov.mode === 'conf') {
      // the opposite side: the DR rule by M5 close, the wick beyond the DR, and the deep pullback (retirement −0,75)
      out.push('<div class="p21-h second">Противоположная сторона</div>');
      out.push(link({ k: 'lvl', id: side === 1 ? 'drL' : 'drH', l: lvlObj(s, side === 1 ? 'drL' : 'drH') }, row('DR удержится до ' + clk(s.end), P(ov.holds)), '', M('ни одно закрытие M5 не ушло за противоположный край своего DR')));
      if (ov.wick != null) out.push(link({ k: 'lvl', id: side === 1 ? 'drL' : 'drH', l: lvlObj(s, side === 1 ? 'drL' : 'drH') }, row('тенью за DR заходили', P(ov.wick)), 'dim', M('цена хотя бы тенью (low / high) зашла за противоположный край своего DR — так задевается стоп прямо за DR; сюда входят и сломы DR закрытием')));
      const pR = ov.u2p(-0.75), deep = ov.sims.filter(q => q.mn <= -0.75), heldAfter = deep.length >= 10 ? 100 * deep.filter(q => q.held).length / deep.length : null;
      const pull = ov.roles.find(r => r.id === 'pull');
      if (ov.u0 > -0.75) out.push(link({ k: 'zone', pA: pR, pB: s.opp, name: 'retirement −0,75', col: pull.col }, row('retirement −0,75 · ' + px(pR) + (heldAfter != null && !none ? '<br><span class="p21-sub">после касания DR держался ' + pct(heldAfter) + '</span>' : ''), P(none ? null : ov.touch(pR))), '',
        M('цена хотя бы раз дошла до −0,75 IDR; «после касания» — доля удержавших DR среди дошедших')));
      else out.push('<div class="p21-note">цена уже в зоне retirement</div>');
    }
    panel.innerHTML = out.join('');
    panelMarks();
  }
  function panelMarks() {
    const h = hv();
    for (const el of panel.querySelectorAll('[data-l21]')) {
      const L = P21.links[+el.dataset.l21];
      let on = p21Key(L) === p21Key(h);
      if (!on && h && L && L.k === 'place' && h.k === 'con') on = h.role === L.role && h.id === L.id;
      el.classList.toggle('on', !!on);
      el.classList.toggle('pinned', !!(st.pin && p21Key(L) === p21Key(st.pin)));
    }
  }
  function initPanel21() {
    panel.addEventListener('mouseover', e => { const el = e.target.closest('[data-l21]'); if (!el) return; st.hover = P21.links[+el.dataset.l21]; animStrip(); redraw(); });
    panel.addEventListener('mouseout', e => { const el = e.target.closest('[data-l21]'); if (!el || el.contains(e.relatedTarget)) return; st.hover = null; animStrip(); redraw(); });
    panel.addEventListener('click', e => { const el = e.target.closest('[data-l21]'); if (el) p21Pin(P21.links[+el.dataset.l21]); });
    dom('step21').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; const t = (st.rp ?? Math.floor(NOW / 5) * 5) + Number(b.dataset.step); if (t >= NOW) backLive(); else replayAt(t); });
    dom('panel21toggle').addEventListener('click', () => { const closed = dom('dr21-root').classList.toggle('panel21closed'); dom('panel21toggle').setAttribute('aria-pressed', String(!closed)); render(true); });
    new ResizeObserver(() => redraw(true)).observe(cv);
  }
