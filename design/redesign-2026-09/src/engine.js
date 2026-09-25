  // ================= shared engine (identical in the three variants) =================
  // Synthetic day for the mockup only: M5 bars [open minute, o, h, l, c] of 2026-09-24, minutes of the trading day (ET),
  // the evening of 09-23 negative. Not market data.
  _D() {
    if (this.__D) return this.__D;
    const raw = __BARS__;
    const bars = raw.map(b => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4] }));
    const SESS = {
      ADR: { k: 'ADR', start: -270, formed: -210, end: 120 },
      ODR: { k: 'ODR', start: 180, formed: 240, end: 510 },
      RDR: { k: 'RDR', start: 570, formed: 630, end: 960 }
    };
    this.__D = { bars, SESS, ORDER: ['ADR', 'ODR', 'RDR'], NOW: 788, DAY0: -360, DAY1: 1020 };
    return this.__D;
  }
  _C() {
    return Object.assign({
      bg: '#0B0D10', panel: '#0F1216', raised: '#161A21', hover: '#1B2029', line: '#1E232B', line2: '#2B313C',
      text: '#D1D4DC', text2: '#B2B5BE', text3: '#8F939E', up: '#089981', dn: '#F23645',
      retr: '#3D9BFF', ext: '#B07CFF', replay: '#F7C948', white: '#F8FAFC', brk: '#8B1E1E'
    }, this._palX ? this._palX() : {});
  }
  _st() {
    const s = this.state || {};
    return {
      session: s.session || 'RDR', rp: s.rp || null, scrub: s.scrub || null,
      v0: s.v0 != null ? s.v0 : 545, v1: s.v1 != null ? s.v1 : 970, yz: s.yz || 1,
      hover: s.hover || null, pick: s.pick || null,
      layers: s.layers || { rclust: true, eclust: false, fan: true, ladder: true },
      mx: s.mx != null ? s.mx : null, my: s.my != null ? s.my : null, drag: !!s.drag
    };
  }
  // ---------- small helpers ----------
  _hash(str) { let h = 2166136261; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  _rng(seed) {
    let a = seed >>> 0;
    return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  _gauss(r) { let u = 0; while (u === 0) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r()); }
  _q(sorted, p) { if (!sorted.length) return 0; const i = (sorted.length - 1) * p, a = Math.floor(i), b = Math.ceil(i); return sorted[a] + (sorted[b] - sorted[a]) * (i - a); }
  _clk(m) { const x = ((Math.round(m) % 1440) + 1440) % 1440; return String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); }
  _num(v, d) { return Number(v).toLocaleString('ru-RU', { minimumFractionDigits: d, maximumFractionDigits: d }); }
  _px(v) { return this._num(Math.round(v / 0.25) * 0.25, 2); }
  _sg(v, d) { const dd = d == null ? 1 : d, r = Math.round(v * Math.pow(10, dd)) / Math.pow(10, dd); return r > 0 ? '+' + this._num(r, dd) : r < 0 ? '−' + this._num(-r, dd) : this._num(0, dd); }
  _pct(v) { return this._num(v, v >= 10 || v === 0 ? 0 : 1) + '%'; }
  _a(hex, a) { const n = parseInt(hex.slice(1), 16); return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + a + ')'; }
  _dashH(col, a, b) { return 'repeating-linear-gradient(90deg,' + col + ' 0px ' + a + 'px,transparent ' + a + 'px ' + (a + b) + 'px)'; }
  _dashDotH(col) { return 'repeating-linear-gradient(90deg,' + col + ' 0px 10px,transparent 10px 14px,' + col + ' 14px 16px,transparent 16px 20px)'; }
  _dashV(col, a, b) { return 'repeating-linear-gradient(180deg,' + col + ' 0px ' + a + 'px,transparent ' + a + 'px ' + (a + b) + 'px)'; }
  // TradingView's candle body width for a bar spacing (lightweight-charts optimalCandlestickWidth, 1 px wick parity)
  _bodyW(S) {
    if (S >= 2.5 && S <= 4) return 3;
    const coeff = 1 - 0.2 * Math.atan(Math.max(4, S) - 4) / (Math.PI * 0.5);
    let w = Math.max(1, Math.min(Math.floor(S * coeff), Math.floor(S)));
    if (w >= 2 && w % 2 === 0) w -= 1;
    return w;
  }
  // ---------- one session at an observed minute (the same rules as lab/live.py) ----------
  _sess(k, obs, live) {
    const D = this._D(), S = D.SESS[k], key = k + '|' + obs + '|' + (live ? 1 : 0);
    this.__S = this.__S || {};
    if (this.__S[key]) return this.__S[key];
    const closedBy = live ? D.NOW : obs;
    const closed = D.bars.filter(b => b.t + 5 <= closedBy), known = live ? D.bars : closed;
    const res = { k, start: S.start, formed: S.formed, end: S.end, obs, live };
    const winAll = known.filter(b => b.t >= S.start && b.t < S.formed);
    if (!winAll.length || obs < S.start) { res.status = 'before'; return (this.__S[key] = res); }
    res.open = winAll[0].o;
    res.drH = Math.max(...winAll.map(b => b.h)); res.drL = Math.min(...winAll.map(b => b.l));
    res.idrH = Math.max(...winAll.map(b => Math.max(b.o, b.c))); res.idrL = Math.min(...winAll.map(b => Math.min(b.o, b.c)));
    res.winEnd = Math.min(S.formed, winAll[winAll.length - 1].t + 5);
    res.complete = closed.filter(b => b.t >= S.start && b.t < S.formed).length === (S.formed - S.start) / 5;
    if (!res.complete) { res.status = 'forming'; return (this.__S[key] = res); }
    const lim = Math.min(obs, S.end);
    let conf = null;
    for (const b of closed) {
      if (b.t < S.formed || b.t + 5 > lim) continue;
      if (b.c > res.drH) { conf = { t: b.t + 5, side: 1 }; break; }
      if (b.c < res.drL) { conf = { t: b.t + 5, side: -1 }; break; }
    }
    if (!conf) { res.status = obs >= S.end ? 'noconf' : 'waiting'; return (this.__S[key] = res); }
    const side = conf.side, w = res.idrH - res.idrL;
    Object.assign(res, { conf: conf.t, side, dir: side === 1 ? 'long' : 'short', edge: side === 1 ? res.idrH : res.idrL, width: w, opp: side === 1 ? res.drL : res.drH });
    res.coord = v => side * (v - res.edge) / w;
    res.price = c => res.edge + side * c * w;
    for (const b of closed) if (b.t + 5 > conf.t && b.t + 5 <= lim && side * (b.c - res.opp) < 0) { res.failed = b.t + 5; break; }
    const inSess = known.filter(b => b.t >= S.formed && b.t < lim);
    const last = inSess[inSess.length - 1];
    res.priceNow = last.c; res.nowCoord = res.coord(last.c); res.lastT = last.t;
    let rs = Infinity, rst = null, es = -Infinity, est = null;
    for (const b of inSess) {
      if (b.t + 5 <= conf.t) continue;
      const lo = res.coord(side === 1 ? b.l : b.h), hi = res.coord(side === 1 ? b.h : b.l);
      if (lo < rs) { rs = lo; rst = b.t + 5; }
      if (hi > es) { es = hi; est = b.t + 5; }
    }
    if (rst != null) Object.assign(res, { retrSoFar: rs, retrT: rst, extSoFar: es, extT: est });
    res.status = obs >= S.end ? 'done' : 'confirmed';
    if (res.status === 'confirmed') res.ov = this._ov(k, obs, res);
    return (this.__S[key] = res);
  }
  // ---------- similar sessions (synthetic stand-in for the history cohort, deterministic per session and minute) ----------
  _ov(k, obs, s) {
    const key = k + '|' + obs;
    this.__O = this.__O || {};
    if (this.__O[key]) return this.__O[key];
    const r = this._rng(this._hash('ov|' + key)), g = () => this._gauss(r);
    const end = s.end, x0 = s.nowCoord, oppC = s.coord(s.opp);
    const n = 70 + Math.floor(r() * 50), extra = 30 + Math.floor(r() * 40);
    const grid = []; for (let t = obs + 5; t <= end; t += 5) grid.push(t);
    const P = [];
    for (let i = 0; i < n + extra; i++) {
      const co = i < n, xs = x0 + (co ? 0.1 : 0.5) * g();
      const rev = r() < 0.1, mu = rev ? -(0.010 + 0.008 * r()) : 0.0017 + 0.0022 * g(), pull = 0.004 + 0.006 * Math.abs(g()), tau = 16 + 30 * r(), sig = 0.044 * (0.7 + 0.6 * r());
      let x = xs, mn = Infinity, tmn = obs + 1, mx = -Infinity, tmx = obs + 1, broken = false, gi = 0;
      const fan = new Array(grid.length);
      for (let m = obs + 1; m <= end; m++) {
        x += mu - pull * Math.exp(-(m - obs) / tau) + sig * g();
        const lo = x - Math.abs(g()) * sig * 0.9, hi = x + Math.abs(g()) * sig * 0.9;
        if (lo < mn) { mn = lo; tmn = m; }
        if (hi > mx) { mx = hi; tmx = m; }
        if (m % 5 === 0 && x < oppC) broken = true;
        if (gi < grid.length && m === grid[gi]) { fan[gi] = x - xs; gi++; }
      }
      P.push({ co, mn, tmn, mx, tmx, broken, fan });
    }
    const C = P.filter(p => p.co), N = C.length;
    const binLo = (v, st) => Math.round(Math.floor(v / st + 1e-9) * st * 10) / 10, binT = (t, st) => Math.floor((t - 1) / st) * st;
    const cellsOf = (vk, tk) => {
      const m = new Map();
      for (const p of C) { const lo = binLo(p[vk], 0.1), t = binT(p[tk], 15), kk = lo.toFixed(1) + '|' + t, e = m.get(kk); if (e) e.n++; else m.set(kk, { lo, t, n: 1 }); }
      return [...m.values()];
    };
    const zonesOf = (vk, tk) => {
      const m = new Map();
      for (const p of C) { const lo = binLo(p[vk], 0.2), t = binT(p[tk], 30), kk = lo.toFixed(1) + '|' + t, e = m.get(kk); if (e) e.n++; else m.set(kk, { lo, t, n: 1 }); }
      return [...m.values()].sort((a, b) => b.n - a.n || a.t - b.t).slice(0, 3)
        .map((z, i) => ({ rank: i + 1, lo: z.lo, hi: Math.round((z.lo + 0.2) * 10) / 10, t: z.t, t_hi: z.t + 30, n: z.n, pct: Math.round(1000 * z.n / N) / 10 }));
    };
    const disp = cells => {
      const srt = cells.filter(c => c.n >= 2 && c.t + 15 > obs).sort((a, b) => b.n - a.n || a.t - b.t), out = [];
      let acc = 0; for (const c of srt) { if (acc >= 0.4 * N) break; out.push(c); acc += c.n; }
      return out;
    };
    const LV = []; for (let v = -1.5; v <= 3.0001; v += 0.25) LV.push(Math.round(v * 100) / 100);
    const touch = LV.map(L => ({ L, pct: 100 * C.filter(p => (L >= x0 ? p.mx >= L : p.mn <= L)).length / N }));
    const fan = [];
    grid.forEach((t, j) => {
      const v = C.map(p => p.fan[j]).filter(Number.isFinite).sort((a, b) => a - b);
      if (v.length >= 10) fan.push({ t, lo: x0 + this._q(v, 0.2), mid: x0 + this._q(v, 0.5), hi: x0 + this._q(v, 0.8) });
    });
    const rHi = Math.max(0.5, Math.ceil((x0 + 0.15) * 10) / 10), eLo = Math.min(-1, Math.floor((x0 - 0.15) * 10) / 10), t0 = Math.floor(obs / 15) * 15;
    const hist = (arr, vk, lo, nb, st, isT) => {
      const b = new Array(nb).fill(0);
      for (const p of arr) { const i = Math.floor(((isT ? p[vk] - 1 : p[vk]) - lo) / st + 1e-9); if (i >= 0 && i < nb) b[i]++; }
      return b;
    };
    const nt = Math.max(1, Math.ceil((end - t0) / 15));
    const H = {
      retr: { lo: Math.round((rHi - 3.1) * 10) / 10, st: 0.1, nb: 31, co: hist(C, 'mn', rHi - 3.1, 31, 0.1), ref: hist(P, 'mn', rHi - 3.1, 31, 0.1) },
      ext: { lo: eLo, st: 0.1, nb: 46, co: hist(C, 'mx', eLo, 46, 0.1), ref: hist(P, 'mx', eLo, 46, 0.1) },
      rtime: { lo: t0, st: 15, nb: nt, co: hist(C, 'tmn', t0, nt, 15, true), ref: hist(P, 'tmn', t0, nt, 15, true), time: true },
      etime: { lo: t0, st: 15, nb: nt, co: hist(C, 'tmx', t0, nt, 15, true), ref: hist(P, 'tmx', t0, nt, 15, true), time: true }
    };
    const srtMn = C.map(p => p.mn).sort((a, b) => a - b), srtMx = C.map(p => p.mx).sort((a, b) => a - b);
    const cellsMin = cellsOf('mn', 'tmn'), cellsMax = cellsOf('mx', 'tmx');
    const res = {
      n: N, pool: P.length, band: 0.25, t0, end, x0,
      drTrue: Math.round(1000 * C.filter(p => !p.broken).length / N) / 10,
      touch, fan, cellsMin, cellsMax, dispMin: disp(cellsMin), dispMax: disp(cellsMax),
      zonesMin: zonesOf('mn', 'tmn'), zonesMax: zonesOf('mx', 'tmx'), H,
      medRetr: this._q(srtMn, 0.5), medExt: this._q(srtMx, 0.5),
      ptsMin: C.map(p => [p.tmn, p.mn]), ptsMax: C.map(p => [p.tmx, p.mx])
    };
    return (this.__O[key] = res);
  }
  // ---------- interaction ----------
  _suppressed() { return Date.now() - (this.__sup || 0) < 250; }
  _hv(key) {
    this.__hv = this.__hv || {};
    if (this.__hv[key]) return this.__hv[key];
    return (this.__hv[key] = {
      enter: () => this.setState({ hover: key }),
      leave: () => { if ((this.state || {}).hover === key) this.setState({ hover: null }); },
      click: e => { if (e && e.stopPropagation) e.stopPropagation(); if (this._suppressed()) return; const p = (this.state || {}).pick; this.setState({ pick: p === key ? null : key }); }
    });
  }
  _fit(k) { const S = this._D().SESS[k]; return { v0: S.start - 25, v1: S.end + 10 }; }
  _selSession(k) { this.setState(Object.assign({ session: k, rp: null, pick: null, hover: null, yz: 1 }, this._fit(k))); }
  _sessIn(t) { const D = this._D(); return D.ORDER.find(k => t > D.SESS[k].start && t <= D.SESS[k].end) || null; }
  _barClick(t) {
    if (this._suppressed()) return;
    const at = t + 5, k = this._sessIn(at);
    if (!k) return;
    const st = this._st();
    if (st.rp && st.rp.at === at) { this.setState({ rp: null, pick: null }); return; }
    const up = { rp: { sess: k, at }, session: k, pick: null, hover: null };
    if (k !== st.session) Object.assign(up, this._fit(k));
    this.setState(up);
  }
  _live() { this.setState({ rp: null, pick: null }); }
  _toggleLayer(k) { const L = Object.assign({}, this._st().layers); L[k] = !L[k]; this.setState({ layers: L }); }
  _zoomAt(delta, px) {
    const st = this._st(), D = this._D(), PW = this._cfg().PW, span = st.v1 - st.v0;
    const f = Math.min(Math.max(px / PW, 0), 1), ta = st.v0 + f * span;
    const ns = Math.min(Math.max(span * Math.exp(delta * 0.0016), 40), D.DAY1 - D.DAY0 + 60);
    let v0 = ta - f * ns; v0 = Math.min(Math.max(v0, D.DAY0 - 30), D.DAY1 + 30 - ns);
    this.setState({ v0, v1: v0 + ns });
  }
  _panBy(dxPx) {
    const st = this._st(), D = this._D(), PW = this._cfg().PW, span = st.v1 - st.v0;
    let v0 = st.v0 - dxPx / PW * span; v0 = Math.min(Math.max(v0, D.DAY0 - 30), D.DAY1 + 30 - span);
    this.setState({ v0, v1: v0 + span });
  }
  _zoomBtn(dir) { this._zoomAt(dir * 260, this._cfg().PW * 0.62); }
  _reset() { this.setState(Object.assign({ yz: 1 }, this._fit(this._st().session))); }
  _local(e) {
    const el = this.__el || e.currentTarget, rc = el.getBoundingClientRect(), sc = rc.width / this._cfg().W || 1;
    return { x: (e.clientX - rc.left) / sc, y: (e.clientY - rc.top) / sc, sc };
  }
  _wheel(e) {
    const p = this._local(e), cfg = this._cfg();
    const dx = e.deltaX || 0, dy = e.deltaY || 0;
    this.__acc = this.__acc || { z: 0, p: 0, y: 0 };
    if (p.x > cfg.PW && p.y < cfg.PH) this.__acc.y += dy;
    else if (Math.abs(dx) > Math.abs(dy) || e.shiftKey) this.__acc.p += (Math.abs(dx) > Math.abs(dy) ? dx : dy);
    else this.__acc.z += dy;
    this.__acc.x = p.x;
    if (this.__wraf) return;
    this.__wraf = requestAnimationFrame(() => {
      this.__wraf = null;
      const a = this.__acc; this.__acc = { z: 0, p: 0, y: 0 };
      if (a.y) { const yz = Math.min(Math.max(this._st().yz * Math.exp(-a.y * 0.0015), 0.35), 6); this.setState({ yz }); }
      if (a.p) this._panBy(-a.p);
      if (a.z) this._zoomAt(a.z, a.x);
    });
  }
  _refCb() {
    if (this.__cref) return this.__cref;
    return (this.__cref = el => {
      if (this.__el === el) return;
      if (this.__el && this.__wh) this.__el.removeEventListener('wheel', this.__wh);
      this.__el = el;
      if (el) { this.__wh = e => { e.preventDefault(); e.stopPropagation(); this._wheel(e); }; el.addEventListener('wheel', this.__wh, { passive: false }); this.__native = true; }
    });
  }
  _mouse() {
    if (this.__mh) return this.__mh;
    const move = e => {
      const p = this._local(e);
      if (this.__drag && (e.buttons & 1)) {
        const dx = p.x - this.__drag.x;
        if (!this.__drag.moved && Math.abs(dx) > 3) { this.__drag.moved = true; this.setState({ drag: true }); }
        if (this.__drag.moved) { this.__drag.x = p.x; this._panBy(dx); return; }
      }
      this.__mm = p;
      if (this.__mraf) return;
      this.__mraf = requestAnimationFrame(() => { this.__mraf = null; const q = this.__mm; if (q) this.setState({ mx: q.x, my: q.y }); });
    };
    return (this.__mh = {
      down: e => { if (e.button !== 0) return; const p = this._local(e); this.__drag = { x: p.x, moved: false }; },
      move,
      up: () => { if (this.__drag && this.__drag.moved) { this.__sup = Date.now(); this.setState({ drag: false }); } this.__drag = null; },
      leave: () => { if (this.__drag && this.__drag.moved) this.__sup = Date.now(); this.__drag = null; this.__mm = null; this.setState({ mx: null, my: null, drag: false }); },
      wheel: e => { if (!this.__native) this._wheel(e); },
      bg: () => { if (this._suppressed()) return; if ((this.state || {}).pick) this.setState({ pick: null }); }
    });
  }
  // ---------- the session chart: everything in chart pixels ----------
  _scene(cfg, st) {
    const D = this._D(), K = this._C();
    const rpx = st.scrub || st.rp, live = !rpx, act = rpx ? rpx.sess : st.session, obs = rpx ? rpx.at : D.NOW;
    const S = {}; for (const k of D.ORDER) S[k] = k === act ? this._sess(k, obs, live) : this._sess(k, D.NOW, true);
    const A = S[act], ov = A.ov || null;
    const PW = cfg.PW, PH = cfg.PH, v0 = st.v0, v1 = st.v1, span = v1 - v0;
    const X = t => (t - v0) / span * PW;
    const sp = 5 * PW / span, bw = this._bodyW(sp);
    const vis = D.bars.filter(b => b.t + 5 > v0 && b.t < v1);
    const hk = st.hover || st.pick || null, hp = hk ? hk.split('|') : [];
    const L = st.layers;
    // --- price range: visible bars, the active DR, what the overlay draws in view
    let lo = Infinity, hi = -Infinity, olo = Infinity, ohi = -Infinity;
    for (const b of vis) { if (b.l < lo) lo = b.l; if (b.h > hi) hi = b.h; }
    if (A.drH != null && A.end > v0 && A.start < v1) { lo = Math.min(lo, A.drL); hi = Math.max(hi, A.drH); }
    const addP = p => { if (p < olo) olo = p; if (p > ohi) ohi = p; };
    if (ov) {
      const inT = (t, d) => t + d > v0 && t < v1;
      if (L.rclust) for (const z of ov.zonesMin) if (inT(z.t, 30)) { addP(A.price(z.lo)); addP(A.price(z.hi)); }
      if (L.eclust) for (const z of ov.zonesMax) if (inT(z.t, 30)) { addP(A.price(z.lo)); addP(A.price(z.hi)); }
      if (L.fan) for (const f of ov.fan) if (f.t > v0 && f.t < v1) { addP(A.price(f.lo)); addP(A.price(f.hi)); }
      if (!isFinite(lo) && isFinite(olo)) { lo = A.price(ov.x0) - 1; hi = lo + 2; }
    }
    if (isFinite(lo) && isFinite(olo)) {           // the forecast may widen the scale by a third at most: candles stay large
      const bs = Math.max(hi - lo, 20);
      lo = Math.min(lo, Math.max(olo, lo - 0.33 * bs)); hi = Math.max(hi, Math.min(ohi, hi + 0.33 * bs));
    }
    if (!isFinite(lo)) { lo = 24400; hi = 24800; }
    if (hi - lo < 20) { const m = (hi + lo) / 2; lo = m - 10; hi = m + 10; }
    const pad = (hi - lo) * 0.07; lo -= pad; hi += pad;
    if (st.yz !== 1) { const m = (lo + hi) / 2, half = (hi - lo) / 2 / st.yz; lo = m - half; hi = m + half; }
    const Y = p => (hi - p) / (hi - lo) * PH;
    const inY = yy => yy > -1 && yy < PH + 1;
    const out = { S, A, ov, act, obs, live, X, Y, lo, hi, sp, bw, hk, hp, K, PW, PH };
    const after = t => !live && t > obs;             // replay: drawn later than the moment
    // --- session boxes (DR window), the 0.1..0.9 IDR grid of the active one, session labels
    out.boxes = []; out.grid = []; out.gridT = []; out.slabels = [];
    for (const k of D.ORDER) {
      const s = S[k]; if (s.drH == null) continue;
      const xa = X(s.start), xb = X(s.status === 'forming' ? s.winEnd : s.formed);
      const active = k === act, sessHl = hk === 'sess|' + k;
      if (xb > 0 && xa < PW) {
        const ya = Y(s.drH), yb = Y(s.drL);
        out.boxes.push({ x: Math.round(xa), y: Math.round(ya), w: Math.max(1, Math.round(xb - xa)), h: Math.max(1, Math.round(yb - ya)), bg: active ? 'rgba(255,255,255,0.055)' : sessHl ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.03)', op: after(s.start) ? 0.4 : 1 });
        if (active && s.complete) {
          const wI = s.idrH - s.idrL, fromLow = s.dir === 'short';
          for (let j = 1; j <= 9; j++) {
            const v = fromLow ? s.idrL + j * wI / 10 : s.idrH - j * wI / 10, yy = Math.round(Y(v));
            out.grid.push({ x: Math.round(xa), y: yy, w: Math.max(1, Math.round(xb - xa)), h: 1, bg: 'rgba(203,213,225,0.34)' });
            if (j !== 5 && xa > 22 && xb - xa >= 90) out.gridT.push({ x: Math.round(xa) - 5, y: yy - 7, t: this._num(j / 10, 1) });
          }
        }
      }
      const lx = Math.max(X(s.start), 0);
      if (X(s.end) > 8 && lx < PW - 40) {
        const hv = this._hv('sess|' + k);
        out.slabels.push({
          x: Math.round(lx) + 6, t: k, active, c: active ? K.text : K.text3, fw: active ? 700 : 600,
          sub: s.status === 'confirmed' ? (live ? 'идёт' : '') : s.status === 'done' ? (s.failed ? 'DR сломан' : 'DR удержался') : s.status === 'waiting' ? 'ждёт подтверждения' : s.status === 'forming' ? 'формируется' : '',
          dot: k === 'RDR' && live && s.status === 'confirmed' ? 'inline-block' : 'none',
          click: () => { if (this._suppressed()) return; if (k !== this._st().session || this._st().rp) this._selSession(k); },
          enter: hv.enter, leave: hv.leave, bg: sessHl ? K.hover : 'transparent'
        });
      }
    }
    // --- levels (Pine DR/IDR V1.5 lines) with their tags on the price scale
    out.lines = []; out.lhits = []; out.tags = [];
    const hlLevel = hp[0] === 'lvl' ? hp[1] + '|' + hp[2] : null;
    const lvlMatch = (k, id) => hlLevel && (hlLevel === k + '|' + id || hlLevel === k + '|' + id.replace(/[HL]$/, ''));
    const touchP = hp[0] === 'touch' && ov ? A.price(+hp[1]) : null;
    for (const k of D.ORDER) {
      const s = S[k]; if (s.drH == null) continue;
      const active = k === act, sessHl = hk === 'sess|' + k;
      const xa = Math.max(0, X(s.start)), xb = Math.min(PW, X(s.status === 'forming' ? s.winEnd : s.end));
      if (xb - xa < 2) continue;
      const Ls = [{ id: 'drH', p: s.drH, kind: 'dr', name: 'DR' }, { id: 'drL', p: s.drL, kind: 'dr', name: 'DR' },
        { id: 'idrH', p: s.idrH, kind: 'idr', name: 'IDR' }, { id: 'idrL', p: s.idrL, kind: 'idr', name: 'IDR' }];
      if (s.complete) {
        Ls.push({ id: 'mid', p: (s.idrH + s.idrL) / 2, kind: 'mid', name: 'mid' }, { id: 'open', p: s.open, kind: 'open', name: 'open' });
        const step = (s.idrH - s.idrL) / 2;
        for (let j = 1; j <= 10; j++) {
          Ls.push({ id: 'u' + j, p: s.idrH + j * step, kind: 'std', name: this._num(j * 0.5, 1), c: s.side === 1 ? j * 0.5 : -1 - j * 0.5 });
          Ls.push({ id: 'd' + j, p: s.idrL - j * step, kind: 'std', name: '−' + this._num(j * 0.5, 1), c: s.side === 1 ? -1 - j * 0.5 : j * 0.5 });
        }
      }
      const anyLvl = !!hlLevel && hlLevel.startsWith(k + '|');
      for (const l of Ls) {
        if (!active && !sessHl && !(l.kind === 'dr' || l.kind === 'idr')) continue;
        const yy = Y(l.p); if (!inY(yy)) continue;
        const on = lvlMatch(k, l.id) || (touchP != null && active && Math.abs(l.p - touchP) < 0.2);
        let th = 1, bg, op = 1;
        if (l.kind === 'dr') { th = 2; bg = K.white; op = 0.92; }
        else if (l.kind === 'idr') { th = 2; bg = this._dashH('#F1F5F9', 9, 4); op = 0.86; }
        else if (l.kind === 'open') { bg = K.up; op = 0.85; }
        else { bg = this._dashDotH('#E2E8F0'); op = l.kind === 'mid' ? 0.8 : 0.62; }
        if (!active) op *= sessHl ? 0.85 : 0.36;
        if (anyLvl && active && !on) op *= 0.45;
        if (on) { th += 1; op = 1; }
        if (active && after(s.start)) op *= 0.4;
        const y0 = Math.round(yy) - Math.floor(th / 2);
        out.lines.push({ x: Math.round(xa), y: y0, w: Math.round(xb - xa), h: th, bg, op: Math.round(op * 100) / 100, sh: on ? '0 0 8px ' + this._a('#FFFFFF', 0.55) : 'none' });
        if (active || sessHl) {
          const lk = 'lvl|' + k + '|' + l.id, hv = this._hv(lk);
          if (active) out.lhits.push({ x: Math.round(xa), y: Math.round(yy) - 4, w: Math.round(xb - xa), h: 9, enter: hv.enter, leave: hv.leave, click: hv.click });
          out.tags.push({ y: yy, h: 20, kind: l.kind, name: l.name, price: this._px(l.p), on, key: lk, c: l.c, pri: l.kind === 'dr' || l.kind === 'idr' ? 1 : 0, sess: k });
        }
      }
    }
    // --- current / replay price
    const lastBar = D.bars[D.bars.length - 1];
    if (live) {
      const upb = lastBar.c >= lastBar.o, yy = Y(lastBar.c);
      if (inY(yy)) out.tags.push({ y: yy, h: 34, kind: 'price', name: '', price: this._px(lastBar.c), sub: '01:52', col: upb ? K.up : K.dn, on: hk === 'price', key: 'price', pri: 2 });
      const xl = X(lastBar.t + 2.5) + bw / 2 + 3;
      if (inY(yy) && xl < PW) out.priceLine = { x: Math.round(Math.max(0, xl)), y: Math.round(yy), w: Math.max(0, Math.round(PW - Math.max(0, xl))), h: 1, bg: this._dashH(upb ? K.up : K.dn, 3, 3), op: hk === 'price' ? 1 : 0.55 };
    } else if (A.priceNow != null) {
      const yy = Y(A.priceNow);
      if (inY(yy)) out.tags.push({ y: yy, h: 20, kind: 'rprice', name: '', price: this._px(A.priceNow), col: K.replay, on: hk === 'price', key: 'price', pri: 2 });
    }
    // --- overlay of the active session: clusters, zones, fan, ladder
    out.cells = []; out.zones = []; out.badges = []; out.picks = []; out.ladder = []; out.ladderT = []; out.fan = null; out.guide = null;
    const cellRect = (lo_, lo2, t, t2) => {
      const a = Y(A.price(lo_)), b = Y(A.price(lo2)), xa = X(Math.max(t, obs)), xb = X(t2);
      return { x0: xa, x1: xb, y0: Math.min(a, b), y1: Math.max(a, b) };
    };
    if (ov) {
      const zoneOf = (kind, c) => (kind === 'min' ? ov.zonesMin : ov.zonesMax).find(z => c.lo >= z.lo - 1e-9 && c.lo < z.hi - 1e-9 && c.t >= z.t && c.t < z.t_hi);
      for (const kind of ['min', 'max']) {
        const layerOn = kind === 'min' ? L.rclust : L.eclust;
        if (!layerOn && !(hp[0] === 'zone' && hp[1] === kind)) continue;
        const hue = kind === 'min' ? K.retr : K.ext, list = kind === 'min' ? ov.dispMin : ov.dispMax, mxn = Math.max(1, ...list.map(c => c.n));
        const kindHl = (hp[0] === 'cell' || hp[0] === 'zone') && hp[1] === kind;
        for (const c of layerOn ? list : []) {
          const R = cellRect(c.lo, c.lo + 0.1, c.t, c.t + 15);
          if (R.x1 <= 0 || R.x0 >= PW || R.x1 - R.x0 < 1 || R.y1 < 0 || R.y0 > PH) continue;
          const key = 'cell|' + kind + '|' + c.lo.toFixed(1) + '|' + c.t, on = hk === key, z = zoneOf(kind, c);
          const inZ = hp[0] === 'zone' && hp[1] === kind && z && z.rank === +hp[2];
          const f = c.n / mxn, hv = this._hv(key);
          let a = 0.16 + 0.52 * f;
          if (kindHl && !on && !inZ) a *= 0.45;
          if (on || inZ) a = Math.min(0.9, a + 0.25);
          out.cells.push({ x: Math.round(R.x0) + 1, y: Math.round(R.y0) + 1, w: Math.max(1, Math.round(R.x1 - R.x0) - 1), h: Math.max(1, Math.round(R.y1 - R.y0) - 1), bg: this._a(hue, Math.round(a * 100) / 100), bd: on ? '1.5px solid #FFFFFF' : 'none', key, kind, c, z, f, enter: hv.enter, leave: hv.leave, click: hv.click, R });
          if (on) out.guide = { R, hue, kind, what: kind === 'min' ? 'Откат закончится' : 'Экстремум', t0: Math.max(c.t, obs), t1: c.t + 15, lo: c.lo, hi: c.lo + 0.1, n: c.n, pct: 100 * c.n / ov.n, key, zone: z };
        }
        const zs = kind === 'min' ? ov.zonesMin : ov.zonesMax;
        for (const zz of zs) {
          if (!layerOn && hk !== 'zone|' + kind + '|' + zz.rank) continue;
          const R = cellRect(zz.lo, zz.hi, zz.t, zz.t_hi);
          if (R.x1 <= 0 || R.x0 >= PW || R.x1 - R.x0 < 2) continue;
          const key = 'zone|' + kind + '|' + zz.rank, on = hk === key, hv = this._hv(key);
          out.zones.push({ x: Math.round(R.x0), y: Math.round(R.y0), w: Math.max(2, Math.round(R.x1 - R.x0)), h: Math.max(2, Math.round(R.y1 - R.y0)), bd: (on ? 2 : zz.rank === 1 ? 1.5 : 1) + 'px ' + (zz.rank === 1 || on ? 'solid ' : 'dashed ') + this._a(hue, on ? 1 : zz.rank === 1 ? 0.95 : 0.7), bg: on ? this._a(hue, 0.18) : 'transparent', key, kind, z: zz, hue, R, enter: hv.enter, leave: hv.leave, click: hv.click });
          out.badges.push({ x: Math.round(R.x0) - 9, y: Math.round(R.y0) - 9, t: String(zz.rank), bg: hue, bd: on ? '1px solid #FFFFFF' : '1px solid ' + hue, on, key, kind, enter: hv.enter, leave: hv.leave, click: hv.click });
          if (on) out.guide = { R, hue, kind, what: kind === 'min' ? 'Откат закончится' : 'Экстремум', t0: Math.max(zz.t, obs), t1: zz.t_hi, lo: zz.lo, hi: zz.hi, n: zz.n, pct: zz.pct, key, zone: zz, rank: zz.rank };
        }
      }
      // badges must not overlap each other
      out.badges.sort((a, b) => a.y - b.y || a.x - b.x);
      for (let i = 1; i < out.badges.length; i++) for (let j = 0; j < i; j++) {
        const a = out.badges[j], b = out.badges[i];
        if (Math.abs(a.x - b.x) < 20 && Math.abs(a.y - b.y) < 20) b.x = a.x + 20;
      }
      // picks from the history charts: time x price cells (rule 16)
      if (hp[0] === 'bin' || hp[0] === 'hcell') {
        const kind = hp[0] === 'hcell' || hp[1] === 'retr' || hp[1] === 'rtime' ? 'min' : 'max', hue = kind === 'min' ? K.retr : K.ext;
        const src = kind === 'min' ? ov.cellsMin : ov.cellsMax, mxn = Math.max(1, ...src.map(c => c.n));
        for (const c of src) {
          const hit = hp[0] === 'hcell' ? Math.abs(c.lo - +hp[1]) < 1e-6 && c.t === +hp[2]
            : (hp[1] === 'retr' || hp[1] === 'ext') ? Math.abs(c.lo - +hp[2]) < 1e-6 : c.t === +hp[2];
          if (!hit || c.t + 15 <= obs) continue;
          const R = cellRect(c.lo, c.lo + 0.1, c.t, c.t + 15);
          if (R.x1 <= 0 || R.x0 >= PW) continue;
          out.picks.push({ x: Math.round(R.x0), y: Math.round(R.y0), w: Math.max(2, Math.round(R.x1 - R.x0)), h: Math.max(2, Math.round(R.y1 - R.y0)), bg: this._a(hue, 0.3 + 0.55 * c.n / mxn), bd: '1px solid ' + this._a('#FFFFFF', 0.85), kind, f: c.n / mxn });
        }
        if (out.picks.length) {
          const x0 = Math.min(...out.picks.map(p => p.x)), x1 = Math.max(...out.picks.map(p => p.x + p.w)), y0 = Math.min(...out.picks.map(p => p.y)), y1 = Math.max(...out.picks.map(p => p.y + p.h));
          const lo2 = A.coord(hi - y1 / PH * (hi - lo)), hi2 = A.coord(hi - y0 / PH * (hi - lo));
          out.guide = { R: { x0, x1, y0, y1 }, hue, kind, pick: true, t0: v0 + x0 / PW * span, t1: v0 + x1 / PW * span, lo: Math.min(lo2, hi2), hi: Math.max(lo2, hi2) };
        }
      }
      if (hp[0] === 'col') {
        const tc = +hp[1];
        for (const kind of ['min', 'max']) {
          if (kind === 'min' ? !L.rclust : !L.eclust) continue;
          const hue = kind === 'min' ? K.retr : K.ext, src = kind === 'min' ? ov.cellsMin : ov.cellsMax, mxn = Math.max(1, ...src.map(c => c.n));
          for (const c of src) {
            if (c.t !== tc || c.t + 15 <= obs) continue;
            const R = cellRect(c.lo, c.lo + 0.1, c.t, c.t + 15);
            if (R.x1 <= 0 || R.x0 >= PW) continue;
            out.picks.push({ x: Math.round(R.x0), y: Math.round(R.y0), w: Math.max(2, Math.round(R.x1 - R.x0)), h: Math.max(2, Math.round(R.y1 - R.y0)), bg: this._a(hue, 0.3 + 0.55 * c.n / mxn), bd: '1px solid ' + this._a('#FFFFFF', 0.85), kind, f: c.n / mxn });
          }
        }
        const x0 = X(Math.max(tc, obs)), x1 = X(tc + 15);
        if (x1 > 0 && x0 < PW) {
          const ys = out.picks.map(p => p.y), ye = out.picks.map(p => p.y + p.h);
          const y0 = ys.length ? Math.min(...ys) : PH, y1 = ye.length ? Math.max(...ye) : PH;
          const cr = ov.H.rtime, ce = ov.H.etime, ir = Math.floor((tc - cr.lo) / 15), ie = Math.floor((tc - ce.lo) / 15);
          out.guide = { R: { x0, x1, y0, y1 }, hue: '#D1D4DC', kind: 'col', col: true, pick: false, t0: Math.max(tc, obs), t1: tc + 15,
            lo: ys.length ? A.coord(hi - y1 / PH * (hi - lo)) : 0, hi: ys.length ? A.coord(hi - y0 / PH * (hi - lo)) : 0, noPrice: !ys.length,
            nr: ir >= 0 && ir < cr.nb ? cr.co[ir] : 0, ne: ie >= 0 && ie < ce.nb ? ce.co[ie] : 0 };
          if (A.side === -1 && out.guide.lo > out.guide.hi) { const q = out.guide.lo; out.guide.lo = out.guide.hi; out.guide.hi = q; }
        }
      }
      if (L.fan && ov.fan.length) {
        const pts = ov.fan.filter(f => f.t > v0 - 10 && f.t < v1 + 10);
        if (pts.length) {
          const sx = X(obs), sy = Y(A.price(ov.x0)), P2 = (t, c) => X(t).toFixed(1) + ',' + Y(A.price(c)).toFixed(1);
          out.fan = {
            area: 'M' + sx.toFixed(1) + ',' + sy.toFixed(1) + ' ' + pts.map(f => 'L' + P2(f.t, f.hi)).join(' ') + ' ' + pts.slice().reverse().map(f => 'L' + P2(f.t, f.lo)).join(' ') + ' Z',
            mid: 'M' + sx.toFixed(1) + ',' + sy.toFixed(1) + ' ' + pts.map(f => 'L' + P2(f.t, f.mid)).join(' ')
          };
        }
      }
      if (L.ladder && cfg.ladderW && !cfg.noLadder) {
        const x0 = PW + 6, bwMax = cfg.ladderW - 44;
        let lastT = -99;
        const rows = ov.touch.map(tc => ({ tc, yy: Y(A.price(tc.L)) })).filter(q => q.yy > 4 && q.yy < PH - 4).sort((a, b) => a.yy - b.yy);
        for (const { tc, yy } of rows) {
          if (tc.pct < 1) continue;
          const key = 'touch|' + tc.L, on = hk === key, hv = this._hv(key), hue = tc.L >= ov.x0 ? K.ext : K.retr;
          const barW = Math.max(2, Math.round(bwMax * tc.pct / 100));
          out.ladder.push({ lx: 42 + bwMax - barW, w: barW, bg: this._a(hue, on ? 1 : 0.78), hit: { x: PW, y: Math.round(yy) - 6, w: cfg.ladderW, h: 12 }, enter: hv.enter, leave: hv.leave, click: hv.click, on });
          const half = Math.abs(tc.L * 2 - Math.round(tc.L * 2)) < 1e-6;
          if ((half || on) && yy - lastT >= 15) { out.ladderT.push({ x: x0, y: Math.round(yy) - 8, t: Math.round(tc.pct) + '%', c: on ? '#FFFFFF' : hue, fw: on ? 700 : 500 }); lastT = yy; }
        }
      }
      if (touchP != null) {
        const yy = Y(touchP), tc = ov.touch.find(q => Math.abs(q.L - +hp[1]) < 1e-6), hue = +hp[1] >= ov.x0 ? K.ext : K.retr;
        if (inY(yy)) {
          out.touchLine = { x: Math.round(X(obs)), y: Math.round(yy) - 1, w: Math.max(0, Math.round(PW - X(obs))), h: 2, bg: this._dashH(hue, 6, 4) };
          out.tags.push({ y: yy, h: 20, kind: 'guide', name: this._sg(+hp[1], 2), price: this._px(touchP) + ' · ' + Math.round(tc.pct) + '%', col: hue, on: true, key: 'touch', pri: 3, guide: true });
        }
      }
    }
    // guides from the highlighted cluster to the axes (rule 18)
    out.glines = []; out.ttags = [];
    if (out.guide) {
      const G = out.guide, R = G.R, col = this._a(G.hue, 0.75), gx = cfg.PW + (cfg.ladderW || 0);
      const xa = Math.max(0, R.x0), xb = Math.min(PW, R.x1);
      out.glines.push({ x: Math.round(xa), y: Math.round(R.y1), w: 1, h: Math.max(0, PH - Math.round(R.y1)), bg: this._dashV(col, 3, 3) });
      out.glines.push({ x: Math.round(xb), y: Math.round(R.y1), w: 1, h: Math.max(0, PH - Math.round(R.y1)), bg: this._dashV(col, 3, 3) });
      if (!G.noPrice) {
        out.glines.push({ x: Math.round(xb), y: Math.round(R.y0), w: Math.max(0, gx - Math.round(xb)), h: 1, bg: this._dashH(col, 3, 3) });
        out.glines.push({ x: Math.round(xb), y: Math.round(R.y1), w: Math.max(0, gx - Math.round(xb)), h: 1, bg: this._dashH(col, 3, 3) });
        const pTop = Math.max(A.price(G.lo), A.price(G.hi)), pBot = Math.min(A.price(G.lo), A.price(G.hi));
        out.tags.push({ y: R.y0, h: 20, kind: 'guide', name: '', price: this._px(pTop), col: G.hue, on: true, pri: 3, guide: true });
        out.tags.push({ y: R.y1, h: 20, kind: 'guide', name: '', price: this._px(pBot), col: G.hue, on: true, pri: 3, guide: true });
      }
      out.ttags.push({ x: xa, t: this._clk(G.t0), col: G.hue, fg: '#0B0D10', pri: 3 }, { x: xb, t: this._clk(G.t1), col: G.hue, fg: '#0B0D10', pri: 3 });
    }
    // --- candles in TradingView geometry
    out.wicks = []; out.bodies = []; out.chits = [];
    const replayT = rpx ? rpx.at - 5 : null;
    for (const b of vis) {
      const xc = Math.round(X(b.t + 2.5)), upb = b.c >= b.o, col = upb ? K.up : K.dn;
      const yH = Math.round(Y(b.h)), yL = Math.round(Y(b.l)), top = Math.round(Y(Math.max(b.o, b.c))), bot = Math.round(Y(Math.min(b.o, b.c)));
      const op = after(b.t + 5) ? 0.3 : 1, sel = replayT === b.t;
      out.wicks.push({ x: xc, y: yH, w: 1, h: Math.max(1, yL - yH), bg: sel ? K.replay : col, op });
      out.bodies.push({ x: xc - (bw - 1) / 2, y: top, w: bw, h: Math.max(1, bot - top), bg: col, op, bd: sel ? '1px solid ' + K.replay : 'none' });
      const t = b.t;
      out.chits.push({ x: Math.round(xc - sp / 2), y: yH - 6, w: Math.max(3, Math.round(sp)), h: Math.max(8, yL - yH + 12), click: () => this._barClick(t) });
    }
    // confirmation and DR-break pills of every session (rule 12)
    out.pills = [];
    for (const k of D.ORDER) {
      const s = S[k]; if (!s.conf) continue;
      const mk = (minute, bg, below, key) => {
        const b = D.bars.find(q => q.t + 5 === minute); if (!b || b.t + 5 <= v0 || b.t >= v1) return;
        const xc = X(b.t + 2.5), yy = below ? Y(b.l) + 6 : Y(b.h) - 24, hv = this._hv(key), on = hk === key;
        out.pills.push({ x: Math.round(xc - 21), y: Math.round(yy), t: this._clk(minute), bg, op: (k === act ? 1 : 0.62) * (after(minute) ? 0.45 : 1), bd: on ? '1px solid #FFFFFF' : '1px solid ' + this._a('#FFFFFF', 0.18), enter: hv.enter, leave: hv.leave, click: hv.click });
      };
      mk(s.conf, s.side === 1 ? K.up : K.dn, s.side === -1, 'conf|' + k);
      if (s.failed) mk(s.failed, K.brk, s.side === 1, 'fail|' + k);
    }
    // current minute (rule 11) and the replay moment
    out.vlines = [];
    const xn = X(D.NOW);
    if (xn > 0 && xn < PW) { out.vlines.push({ x: Math.round(xn), y: 0, w: 1, h: PH, bg: this._dashV(this._a('#D1D4DC', 0.34), 6, 4), op: 1 }); out.ttags.push({ x: xn, t: this._clk(D.NOW), col: '#2A2E39', fg: '#FFFFFF', pri: 1 }); }
    if (!live) { const xm = X(obs); if (xm > 0 && xm < PW) { out.vlines.push({ x: Math.round(xm), y: 0, w: 1, h: PH, bg: K.replay, op: 0.9 }); out.ttags.push({ x: xm, t: 'момент ' + this._clk(obs), col: K.replay, fg: '#0B0D10', pri: 2 }); } }
    // crosshair
    out.xh = []; out.hoverBar = null;
    if (st.mx != null && !st.drag && st.mx >= 0 && st.mx < PW && st.my >= 0 && st.my < PH) {
      const tm = v0 + st.mx / PW * span, tb = Math.floor(tm / 5) * 5, xc = Math.round(X(tb + 2.5));
      out.xh.push({ x: xc, y: 0, w: 1, h: PH, bg: this._dashV(this._a('#9598A1', 0.6), 5, 4) }, { x: 0, y: Math.round(st.my), w: PW + (cfg.ladderW || 0), h: 1, bg: this._dashH(this._a('#9598A1', 0.6), 5, 4) });
      out.tags.push({ y: st.my, h: 20, kind: 'cross', name: '', price: this._px(hi - st.my / PH * (hi - lo)), col: '#363A45', on: true, pri: 4, guide: true });
      out.ttags.push({ x: xc, t: this._clk(tb), col: '#363A45', fg: '#FFFFFF', pri: 4 });
      out.hoverBar = D.bars.find(b => b.t === tb) || null;
    }
    // --- price scale: tag layout (no tag overlaps another; guides push the others aside) and round-number ticks
    const guides = out.tags.filter(t => t.guide);
    let rest = out.tags.filter(t => !t.guide && !guides.some(gt => Math.abs(gt.y - t.y) < (gt.h + t.h) / 2 + 1));
    rest.sort((a, b) => a.y - b.y);
    for (let i = 0; i < rest.length; i++) rest[i].ty = i ? Math.max(rest[i].y, rest[i - 1].ty + (rest[i - 1].h + rest[i].h) / 2 + 2) : Math.max(rest[i].y, rest[i].h / 2);
    for (let i = rest.length - 1; i >= 0; i--) { const lim = i === rest.length - 1 ? PH - rest[i].h / 2 : rest[i + 1].ty - (rest[i + 1].h + rest[i].h) / 2 - 2; if (rest[i].ty > lim) rest[i].ty = lim; }
    for (const g of guides) g.ty = Math.min(Math.max(g.y, g.h / 2), PH - g.h / 2);
    out.tags = rest.concat(guides);
    const steps = [0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 100, 250, 500, 1000];
    const pstep = steps.find(s2 => s2 / (hi - lo) * PH >= 44) || 1000;
    out.ticks = [];
    for (let p = Math.ceil(lo / pstep) * pstep; p <= hi; p += pstep) {
      const yy = Y(p); if (yy < 8 || yy > PH - 8) continue;
      if (out.tags.some(t => Math.abs(t.ty - yy) < t.h / 2 + 8)) continue;
      out.ticks.push({ y: Math.round(yy) - 8, t: this._num(p, pstep < 1 ? 2 : 0) });
    }
    // --- time axis
    const tsteps = [5, 10, 15, 30, 60, 120, 180, 240, 360];
    const tstep = tsteps.find(s2 => s2 / span * PW >= 76) || 360;
    out.tlabels = [];
    const tt = out.ttags;
    for (let t = Math.ceil(v0 / tstep) * tstep; t <= v1; t += tstep) {
      const xx = X(t); if (xx < 18 || xx > PW - 18) continue;
      if (tt.some(q => Math.abs(q.x - xx) < 52)) continue;
      out.tlabels.push({ x: Math.round(xx), t: ((t % 1440) + 1440) % 1440 === 0 ? (t < 720 ? '24 сен' : '25 сен') : this._clk(t) });
    }
    tt.sort((a, b) => b.pri - a.pri);
    const keep = [];
    for (const q of tt) if (!keep.some(k2 => Math.abs(k2.x - q.x) < 26 + (q.t.length + k2.t.length) * 3.4)) keep.push(q);
    out.ttags = keep.map(q => ({ x: Math.round(q.x), t: q.t, col: q.col, fg: q.fg }));
    // --- legend: OHLC of the bar under the crosshair, else the last one (TradingView style)
    const lb = out.hoverBar || (!live && D.bars.find(b => b.t + 5 === obs)) || lastBar, ch = lb.c - lb.o;
    out.legend = { o: this._px(lb.o), h: this._px(lb.h), l: this._px(lb.l), c: this._px(lb.c), ch: (ch >= 0 ? '+' : '−') + this._px(Math.abs(ch)), col: ch >= 0 ? K.up : K.dn, when: this._clk(lb.t) };
    return out;
  }
  // tags -> styled boxes for the price scale (x = scale left)
  _tagBoxes(sc, xs, withPct) {
    const K = this._C(), A = sc.A, ov = sc.ov;
    return sc.tags.map(t => {
      let bg = '#1B1F27', fg = K.text, bd = '1px solid #3A404C', fw = 500;
      if (t.kind === 'dr') { bg = K.white; fg = '#0B0D10'; bd = '1px solid ' + K.white; fw = 600; }
      else if (t.kind === 'idr') { bg = '#0B0D10'; fg = '#F1F5F9'; bd = '1px solid #F1F5F9'; }
      else if (t.kind === 'open') { bg = '#0B0D10'; fg = K.up; bd = '1px solid ' + K.up; }
      else if (t.kind === 'price') { bg = t.col; fg = '#FFFFFF'; bd = '1px solid ' + t.col; fw = 600; }
      else if (t.kind === 'rprice') { bg = '#0B0D10'; fg = K.replay; bd = '1px solid ' + K.replay; fw = 600; }
      else if (t.kind === 'guide' || t.kind === 'cross') { bg = t.col; fg = t.kind === 'cross' ? '#FFFFFF' : '#0B0D10'; bd = '1px solid ' + t.col; fw = 600; }
      if (t.on && (t.kind === 'std' || t.kind === 'mid')) { bg = '#E2E8F0'; fg = '#0B0D10'; bd = '1px solid #E2E8F0'; }
      if (t.on && t.kind === 'idr') { bg = '#F1F5F9'; fg = '#0B0D10'; }
      if (t.on && t.kind === 'open') { bg = K.up; fg = '#FFFFFF'; }
      let pct = '', pcol = 'transparent', pdisp = 'none';
      if (withPct && ov && t.kind === 'std' && t.sess === sc.act && t.c != null) {
        const tc = ov.touch.find(q => Math.abs(q.L - t.c) < 1e-6);
        if (tc) { pct = Math.round(tc.pct) + '%'; pcol = withPct === 'muted' ? '#8F939E' : t.c >= ov.x0 ? K.ext : K.retr; pdisp = 'inline'; }
      }
      const hv = t.key ? this._hv(t.key) : {};
      return {
        x: xs + 1, y: Math.round(t.ty - t.h / 2), h: t.h, bg, fg, bd, fw, name: t.name, nd: t.name ? 'inline' : 'none', price: t.price,
        sub: t.sub || '', sd: t.sub ? 'block' : 'none', pct, pcol, pdisp,
        anc: Math.abs(t.ty - t.y) > 1.5 ? 'block' : 'none', ay: Math.round(t.y - t.ty + t.h / 2) - 1, acol: t.kind === 'dr' ? K.white : t.kind === 'price' ? t.col : '#9BA1AC',
        enter: hv.enter, leave: hv.leave, click: hv.click
      };
    });
  }
  // ---------- the six history charts of the same cohort (rule 3), flattened for the markup ----------
  _bottom(sc, W, H) {
    const K = this._C(), ov = sc.ov, A = sc.A, hk = sc.hk, hp = sc.hp;
    const res = { frames: [], titles: [], bars: [], cells: [], texts: [], fanArea: 'M0,0', fanMid: 'M0,0', fanZero: 'M0,0', show: !!ov, fx: 0, fy: 0, fw: 0, fh: 0, empty: ov ? 'none' : 'flex' };
    const gap = 8, cw = (W - gap * 7) / 6, ch = H - gap * 2;
    const names = ['Путь', 'Глубина × время', 'Откат', 'Расширение', 'Время отката', 'Время экстремума'];
    if (!ov) {
      for (let i = 0; i < 6; i++) { const x = gap + i * (cw + gap); res.frames.push({ x: Math.round(x), y: gap, w: Math.round(cw), h: ch }); res.titles.push({ x: Math.round(x) + 10, y: gap + 6, t: names[i] }); }
      return res;
    }
    const G = sc.guide;
    const hlBin = (chart, lo, st) => {
      if (hp[0] === 'bin' && hp[1] === chart) return Math.abs(+hp[2] - lo) < 1e-6 ? 2 : 0;
      if (!G) return 0;
      if (G.col) return (chart === 'rtime' || chart === 'etime') && lo + st > G.t0 && lo < G.t1 ? 1 : 0;
      const kindOk = (chart === 'retr' || chart === 'rtime') ? G.kind === 'min' : G.kind === 'max';
      if (!kindOk) return 0;
      if (chart === 'retr' || chart === 'ext') return lo + st > G.lo + 1e-6 && lo < G.hi - 1e-6 ? 1 : 0;
      return lo + st > G.t0 && lo < G.t1 ? 1 : 0;
    };
    for (let i = 0; i < 6; i++) {
      const x = gap + i * (cw + gap), y = gap;
      res.frames.push({ x: Math.round(x), y, w: Math.round(cw), h: ch });
      res.titles.push({ x: Math.round(x) + 10, y: y + 6, t: names[i] });
      const px0 = x + 30, py0 = y + 26, pw = cw - 40, ph = ch - 26 - 20;
      if (i === 0) {                                   // path: median and 20-80 % of closes, IDR scale
        const f = ov.fan; if (!f.length) continue;
        const vmin = Math.min(...f.map(q => q.lo), ov.x0) - 0.1, vmax = Math.max(...f.map(q => q.hi), ov.x0) + 0.1;
        const fx = t => (t - sc.obs) / (ov.end - sc.obs) * pw, fy = v => (vmax - v) / (vmax - vmin) * ph;
        res.fx = Math.round(px0); res.fy = Math.round(py0); res.fw = Math.round(pw); res.fh = Math.round(ph);
        res.fanArea = 'M0,' + fy(ov.x0).toFixed(1) + ' ' + f.map(q => 'L' + fx(q.t).toFixed(1) + ',' + fy(q.hi).toFixed(1)).join(' ') + ' ' + f.slice().reverse().map(q => 'L' + fx(q.t).toFixed(1) + ',' + fy(q.lo).toFixed(1)).join(' ') + ' Z';
        res.fanMid = 'M0,' + fy(ov.x0).toFixed(1) + ' ' + f.map(q => 'L' + fx(q.t).toFixed(1) + ',' + fy(q.mid).toFixed(1)).join(' ');
        if (0 > vmin && 0 < vmax) res.fanZero = 'M0,' + fy(0).toFixed(1) + ' L' + pw.toFixed(1) + ',' + fy(0).toFixed(1);
        for (const v of [Math.ceil(vmin * 2) / 2, Math.floor(vmax * 2) / 2]) res.texts.push({ x: Math.round(px0) - 6, y: Math.round(py0 + fy(v)) - 7, t: this._sg(v, 1), al: 'translateX(-100%)' });
        res.texts.push({ x: Math.round(px0), y: Math.round(py0 + ph) + 3, t: this._clk(sc.obs), al: 'none' }, { x: Math.round(px0 + pw), y: Math.round(py0 + ph) + 3, t: this._clk(ov.end), al: 'translateX(-100%)' });
        continue;
      }
      if (i === 1) {                                   // depth x time of the final retracement
        const rows = [], los = ov.cellsMin.map(c => c.lo), top = Math.min(3, Math.max(...los) + 0.1), bottomR = Math.max(-2.5, Math.min(...los) - 0.1);
        for (let rr = Math.round(top * 10); rr >= Math.round(bottomR * 10); rr--) rows.push(rr / 10);
        const cols = []; for (let t = ov.t0; t < ov.end; t += 15) cols.push(t);
        const cwid = pw / cols.length, rh = ph / rows.length, mxn = Math.max(1, ...ov.cellsMin.map(c => c.n));
        const map = new Map(ov.cellsMin.map(c => [c.lo.toFixed(1) + '|' + c.t, c.n]));
        rows.forEach((rv, ri) => cols.forEach((t, ci) => {
          const n = map.get(rv.toFixed(1) + '|' + t) || 0; if (!n) return;
          const key = 'hcell|' + rv.toFixed(1) + '|' + t, hv = this._hv(key);
          const on = hk === key || (G && G.kind === 'min' && rv >= G.lo - 1e-6 && rv < G.hi - 1e-6 && t >= Math.floor(G.t0 / 15) * 15 && t < G.t1);
          res.cells.push({ x: Math.round(px0 + ci * cwid), y: Math.round(py0 + ri * rh), w: Math.max(1, Math.round(cwid) - 1), h: Math.max(1, Math.round(rh) - 1), bg: this._a(K.retr, Math.round((0.22 + 0.73 * n / mxn) * 100) / 100), bd: on ? '1px solid #FFFFFF' : 'none', enter: hv.enter, leave: hv.leave, click: hv.click });
        }));
        for (const rv of rows) if (Math.round(rv * 10) % 5 === 0) res.texts.push({ x: Math.round(px0) - 6, y: Math.round(py0 + rows.indexOf(rv) * rh + rh / 2) - 7, t: this._sg(rv, 1), al: 'translateX(-100%)' });
        res.texts.push({ x: Math.round(px0), y: Math.round(py0 + ph) + 3, t: this._clk(ov.t0), al: 'none' }, { x: Math.round(px0 + pw), y: Math.round(py0 + ph) + 3, t: this._clk(ov.end), al: 'translateX(-100%)' });
        continue;
      }
      const chartKey = ['retr', 'ext', 'rtime', 'etime'][i - 2], Hh = ov.H[chartKey], hue = chartKey === 'retr' || chartKey === 'rtime' ? K.retr : K.ext;
      const mx = Math.max(1, ...Hh.co, ...Hh.ref), bwid = pw / Hh.nb;
      const anyHl = Hh.co.some((_, j) => hlBin(chartKey, Math.round((Hh.lo + j * Hh.st) * 10) / 10, Hh.st));
      for (let j = 0; j < Hh.nb; j++) {
        const lo2 = Hh.time ? Hh.lo + j * Hh.st : Math.round((Hh.lo + j * Hh.st) * 10) / 10;
        const xx = px0 + j * bwid, hr = Hh.ref[j] / mx * ph, hc = Hh.co[j] / mx * ph;
        if (hr > 0) res.bars.push({ x: Math.round(xx) + 1, y: Math.round(py0 + ph - hr), w: Math.max(1, Math.round(bwid) - 2), h: Math.max(1, Math.round(hr)), bg: '#262B35', bd: 'none' });
        const lvl = hlBin(chartKey, lo2, Hh.st), key = 'bin|' + chartKey + '|' + (Hh.time ? lo2 : lo2.toFixed(1)), hv = this._hv(key);
        if (hc > 0) res.bars.push({ x: Math.round(xx) + 1, y: Math.round(py0 + ph - hc), w: Math.max(1, Math.round(bwid) - 2), h: Math.max(2, Math.round(hc)), bg: lvl ? this._a(hue, 1) : this._a(hue, anyHl ? 0.35 : 0.8), bd: lvl === 2 || hk === key ? '1px solid #FFFFFF' : 'none', enter: hv.enter, leave: hv.leave, click: hv.click });
        else res.bars.push({ x: Math.round(xx), y: Math.round(py0), w: Math.max(1, Math.round(bwid)), h: Math.round(ph), bg: 'transparent', bd: 'none', enter: hv.enter, leave: hv.leave, click: hv.click });
      }
      const every = Math.max(1, Math.ceil(Hh.nb / (Hh.time ? 4 : 5)));
      for (let j = 0; j < Hh.nb; j += every) {
        const lo2 = Hh.lo + j * Hh.st;
        res.texts.push({ x: Math.round(px0 + j * bwid + bwid / 2), y: Math.round(py0 + ph) + 3, t: Hh.time ? this._clk(lo2) : this._sg(lo2, 1), al: 'translateX(-50%)' });
      }
      res.texts.push({ x: Math.round(px0) - 6, y: Math.round(py0) - 6, t: String(mx), al: 'translateX(-100%)' });
    }
    return res;
  }
