  // ================= DR Lab · cluster mockups, shared engine (identical in the three variants) =================
  // Synthetic days only (gen_days.py): M5 bars [open minute, o, h, l, c], minutes of the trading day (ET), the evening
  // before negative. The similar-session cohorts are simulated. Not market data, not the lab's numbers.
  _D() {
    const s = this.state || {}, day = s.scene === 'brk' ? 'B' : 'A';
    this.__DD = this.__DD || {};
    if (this.__DD[day]) return this.__DD[day];
    const raw = day === 'B' ? __BARS_B__ : __BARS_A__;
    const bars = raw.map(b => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4] }));
    const SESS = {
      ADR: { k: 'ADR', start: -270, formed: -210, end: 120 },
      ODR: { k: 'ODR', start: 180, formed: 240, end: 510 },
      RDR: { k: 'RDR', start: 570, formed: 630, end: 960 }
    };
    // yesterday's RDR box (synthetic): its levels run through the whole day as structure
    const PREV = { k: 'PREV', name: 'RDR 23.09', drH: 24518.5, drL: 24402.25, idrH: 24506, idrL: 24411.5 };
    return (this.__DD[day] = { day, bars, SESS, ORDER: ['ADR', 'ODR', 'RDR'], NOW: 788, DAY0: -360, DAY1: 1020, PREV, mid: day === 'B' ? ['25 сен', '26 сен'] : ['24 сен', '25 сен'], date: day === 'B' ? 'пт, 25 сен' : 'чт, 24 сен' });
  }
  _C() {
    return {
      bg: '#0B0D10', panel: '#0F1216', raised: '#161A21', hover: '#1B2029', line: '#1E232B', line2: '#2B313C',
      text: '#D1D4DC', text2: '#B2B5BE', text3: '#8F939E', up: '#089981', dn: '#F23645',
      pull: '#FF5A5F', cont: '#34D399', neu: '#B4C3D8', replay: '#F7C948', white: '#F8FAFC', brk: '#9F1D24'
    };
  }
  _st() {
    const s = this.state || {};
    return {
      scene: s.scene || 'conf', session: s.session || 'RDR', rp: s.rp || null, scrub: s.scrub || null,
      v0: s.v0 != null ? s.v0 : 545, v1: s.v1 != null ? s.v1 : 970, yz: s.yz || 1,
      hover: s.hover || null, pick: s.pick || null,
      layers: s.layers || { pull: true, cont: true, struct: true },
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
  _clk(m) { const x = ((Math.round(m) % 1440) + 1440) % 1440; return String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); }
  _dur(m) { const x = Math.max(0, Math.round(m)); return Math.floor(x / 60) + ':' + String(x % 60).padStart(2, '0'); }
  _num(v, d) { return Number(v).toLocaleString('ru-RU', { minimumFractionDigits: d, maximumFractionDigits: d }); }
  _px(v) { const r = Math.round(v / 0.25) * 0.25; return this._num(r, r % 1 === 0 ? 0 : 2); }
  _pct(v) { return this._num(v, v >= 10 || v === 0 ? 0 : 1) + '%'; }
  _pine(j, above) { return (above ? '' : '−') + this._num(j * 0.5, 1); }
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
  // ---------- one session at an observed minute (the rules of lab/live.py; DR, confirmation, break from closed M5) ----------
  _sess(k, obs, live) {
    const D = this._D(), S = D.SESS[k], key = D.day + '|' + k + '|' + obs + '|' + (live ? 1 : 0);
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
    res.close = winAll[winAll.length - 1].c; res.boxUp = res.close >= res.open; res.width = res.idrH - res.idrL;
    const lim = Math.min(obs, S.end), w = res.width;
    const inSess = known.filter(b => b.t >= S.formed && b.t < lim), last = inSess[inSess.length - 1] || winAll[winAll.length - 1];
    res.priceNow = last.c; res.lastT = last.t;
    let conf = null;
    for (const b of closed) {
      if (b.t < S.formed || b.t + 5 > lim) continue;
      if (b.c > res.drH) { conf = { t: b.t + 5, side: 1 }; break; }
      if (b.c < res.drL) { conf = { t: b.t + 5, side: -1 }; break; }
    }
    if (!conf) {
      res.status = obs >= S.end ? 'noconf' : 'waiting';
      if (res.status === 'waiting') res.ov = this._ovWait(k, obs, res);
      return (this.__S[key] = res);
    }
    const side = conf.side;
    Object.assign(res, { conf: conf.t, side, dir: side === 1 ? 'long' : 'short', edge: side === 1 ? res.idrH : res.idrL, opp: side === 1 ? res.drL : res.drH });
    res.coord = v => side * (v - res.edge) / w;
    res.price = c => res.edge + side * c * w;
    for (const b of closed) if (b.t + 5 > conf.t && b.t + 5 <= lim && side * (b.c - res.opp) < 0) { res.failed = b.t + 5; break; }
    res.nowCoord = res.coord(res.priceNow);
    let rs = Infinity, rst = null;
    for (const b of inSess) {
      if (b.t + 5 <= conf.t || (res.failed && b.t + 5 > res.failed)) continue;
      const lo = res.coord(side === 1 ? b.l : b.h);
      if (lo < rs) { rs = lo; rst = b.t + 5; }
    }
    if (rst != null) Object.assign(res, { retrSoFar: rs, retrT: rst, retrP: res.price(rs) });
    // steps of the ladder already taken (Pine STD of the side that is being played)
    const taken = (sd, edge, from, to) => {
      const out = [];
      for (let j = 1; j <= 6; j++) {
        const L = edge + sd * j * w / 2, b = inSess.find(q => q.t + 5 > from && q.t + 5 <= to && (sd === 1 ? q.h >= L : q.l <= L));
        if (!b) break;
        out.push({ j, t: b.t + 5, name: this._pine(j, sd === 1) });
      }
      return out;
    };
    res.taken = taken(side, res.edge, conf.t, res.failed || lim);
    if (res.failed) {
      res.nside = -side; res.nedge = side === 1 ? res.idrL : res.idrH;
      res.ncoord = v => res.nside * (v - res.nedge) / w;
      res.nprice = c => res.nedge + res.nside * c * w;
      res.nowN = res.ncoord(res.priceNow);
      res.takenN = taken(res.nside, res.nedge, res.failed - 5, lim);
    }
    res.status = obs >= S.end ? 'done' : res.failed ? 'broken' : 'confirmed';
    if (res.status === 'confirmed') res.ov = this._ovConf(k, obs, res);
    if (res.status === 'broken') res.ov = this._ovBrk(k, obs, res);
    return (this.__S[key] = res);
  }
  // relation of a session to the previous box: the day models as plain facts (break = an M5 close beyond the level)
  _models(k, obs) {
    const D = this._D(), S = D.SESS[k], i = D.ORDER.indexOf(k);
    const prevK = i > 0 ? D.ORDER[i - 1] : 'PREV', prev = i > 0 ? this._sess(prevK, D.NOW, true) : D.PREV;
    if (prev.drH == null) return null;
    const lim = Math.min(obs, S.end), bars = D.bars.filter(b => b.t >= S.start && b.t + 5 <= lim);
    if (!bars.length) return null;
    const res = { prev: i > 0 ? prevK : 'RDR 23.09', up: 'цел', dn: 'цел' };
    if (bars[0].o < prev.drL) res.up = 'исключён';
    if (bars[0].o > prev.drH) res.dn = 'исключён';
    for (const b of bars) {
      if (res.up === 'цел' && b.c < prev.drL) res.up = 'сломан ' + this._clk(b.t + 5);
      if (res.dn === 'цел' && b.c > prev.drH) res.dn = 'сломан ' + this._clk(b.t + 5);
    }
    return res;
  }
  // ---------- similar sessions: a simulated stand-in for the history cohort, deterministic per day, session and minute ----------
  _walk(r, g, x0, obs, end, o) {
    let x = x0, mn = Infinity, tmn = obs + 1, mx = -Infinity, tmx = obs + 1, cross = 0;
    for (let m = obs + 1; m <= end; m++) {
      const mu = o.mu + (cross ? cross * (o.trend || 0) : 0);
      x += mu - o.pull * Math.exp(-(m - obs) / o.tau) + o.sig * g();
      const lo = x - Math.abs(g()) * o.sig * 0.9, hi = x + Math.abs(g()) * o.sig * 0.9;
      if (lo < mn) { mn = lo; tmn = m; }
      if (hi > mx) { mx = hi; tmx = m; }
      if (o.hiC != null && !cross && m % 5 === 0) { if (x > o.hiC) cross = 1; else if (x < o.loC) cross = -1; }
    }
    return { mn, tmn, mx, tmx, cross };
  }
  // one kind of extreme (pullback / continuation, or upper / lower before a confirmation), in prices: cells of
  // 0.1 IDR x 5 minutes (one glyph each), their probability steps, clusters, price bins and 15-minute time bins
  _kind(meta, vals, u2p, obs, N) {
    const binLo = (v, st) => Math.round(Math.floor(v / st + 1e-9) * st * 10) / 10, binT = (t, st) => Math.floor((t - 1) / st) * st;
    const P = (a, b) => { const x = u2p(a), y = u2p(b); return [Math.min(x, y), Math.max(x, y)]; };
    const cm = new Map(), pm = new Map(), tm = new Map();
    for (const [u, t] of vals) {
      const c = binLo(u, 0.1), ct = binT(t, 5), tt = binT(t, 15), k1 = c.toFixed(1) + '|' + ct, k3 = c.toFixed(1);
      if (!cm.has(k1)) cm.set(k1, { u: c, t: ct, n: 0 }); cm.get(k1).n++;
      if (!pm.has(k3)) pm.set(k3, { u: c, n: 0 }); pm.get(k3).n++;
      if (!tm.has(tt)) tm.set(tt, { t: tt, n: 0 }); tm.get(tt).n++;
    }
    const cells = [...cm.values()].map(c => { const [pLo, pHi] = P(c.u, c.u + 0.1); return { u: c.u, t: c.t, tHi: c.t + 5, pLo, pHi, n: c.n, pct: 100 * c.n / N, cls: 4, cl: 0 }; });
    this._steps(cells, N);
    const clusters = this._clusters(cells, N);
    const pbins = [...pm.values()].map(b => { const [pLo, pHi] = P(b.u, b.u + 0.1); return { pLo, pHi, n: b.n, pct: 100 * b.n / N }; });
    const tbins = [...tm.values()].sort((a, b) => a.t - b.t).map(b => ({ t: b.t, tHi: b.t + 15, n: b.n, pct: 100 * b.n / N }));
    return Object.assign({}, meta, { cells, clusters, pbins, tbins, N, u2p });
  }
  // probability steps by the number of sessions in a cell against the densest cell of the kind, on a square-root scale
  // (one sharp peak must not flatten the rest): step 1 >= 36 % of it, step 2 >= 14 %, step 3 >= 5 % and at least two
  // sessions, step 4 the rest (single sessions: a faint dot)
  _steps(cells, N) {
    const mx = Math.max(1, ...cells.map(c => c.n));
    for (const c of cells) { const f = c.n / mx; c.cls = f >= 0.36 ? 1 : f >= 0.14 ? 2 : f >= 0.05 && c.n >= 2 ? 3 : 4; }
    return cells;
  }
  // clusters: connected groups of step-1 cells (touching by a side or a corner); share = their sessions / N
  _clusters(cells, N) {
    const key = (a, b) => a + ',' + b, map = new Map();
    for (const c of cells) if (c.cls === 1) map.set(key(Math.round(c.u * 10), c.t / 5), c);
    const seen = new Set(), out = [];
    for (const [k0, c0] of map) {
      if (seen.has(k0)) continue;
      const mem = [], stack = [c0]; seen.add(k0);
      while (stack.length) {
        const c = stack.pop(); mem.push(c);
        const a = Math.round(c.u * 10), b = c.t / 5;
        for (let da = -1; da <= 1; da++) for (let db = -1; db <= 1; db++) { const k = key(a + da, b + db); if (!seen.has(k) && map.has(k)) { seen.add(k); stack.push(map.get(k)); } }
      }
      const n = mem.reduce((s, c) => s + c.n, 0), pk = mem.reduce((m, c) => (c.n > m.n ? c : m), mem[0]);
      out.push({ mem, n, pct: 100 * n / N, t0: Math.min(...mem.map(c => c.t)), t1: Math.max(...mem.map(c => c.tHi)), pLo: Math.min(...mem.map(c => c.pLo)), pHi: Math.max(...mem.map(c => c.pHi)), tp: pk.t + 2.5, pp: (pk.pLo + pk.pHi) / 2 });
    }
    const list = out.filter(q => q.pct >= 3).sort((a, b) => b.n - a.n).slice(0, 3);
    list.forEach((q, i) => { q.rank = i + 1; for (const c of q.mem) c.cl = i + 1; });
    return list;
  }
  _cohort(key, n, x0, obs, end, o) {
    const r = this._rng(this._hash(key)), g = () => this._gauss(r), out = [];
    for (let i = 0; i < n; i++) {
      const oo = Object.assign({}, o, { mu: o.mu + (o.muJ || 0) * g(), pull: o.pull * (0.5 + r()), tau: o.tau * (0.6 + 0.8 * r()), sig: o.sig * (0.75 + 0.5 * r()) });
      if (o.rev && r() < o.rev) oo.mu = -Math.abs(oo.mu) * 3;
      out.push(this._walk(r, g, x0 + 0.1 * g(), obs, end, oo));
    }
    return out;
  }
  _ovConf(k, obs, s) {
    const key = this._D().day + '|conf|' + k + '|' + obs; this.__O = this.__O || {};
    if (this.__O[key]) return this.__O[key];
    const r = this._rng(this._hash('n' + key)), N = 380 + Math.floor(r() * 140), pool = N + 260 + Math.floor(r() * 200);
    const C = this._cohort(key, N, s.nowCoord, obs, s.end, { mu: 0.0017, muJ: 0.0022, pull: 0.007, tau: 30, sig: 0.044, rev: 0.1 });
    const pt = s.side === 1 ? 'down' : 'up', u2p = u => s.price(u);
    const res = {
      N, pool, obs, end: s.end, W: s.width, edgeP: s.edge, mode: 'conf',
      cond: k + ' · ' + (s.side === 1 ? 'лонг' : 'шорт') + ' · подтверждение ' + this._clk(s.conf) + ' ±15 мин · DR цел · цена ±0,25 IDR',
      kinds: [
        this._kind({ id: 'pull', role: 'Откат', hue: this._C().pull, shape: 'tri', point: pt, layer: 'pull' }, C.map(p => [p.mn, p.tmn]), u2p, obs, N),
        this._kind({ id: 'cont', role: 'Продолжение', hue: this._C().cont, shape: 'terr', layer: 'cont' }, C.map(p => [p.mx, p.tmx]), u2p, obs, N)
      ]
    };
    return (this.__O[key] = res);
  }
  _ovBrk(k, obs, s) {
    const key = this._D().day + '|brk|' + k + '|' + obs; this.__O = this.__O || {};
    if (this.__O[key]) return this.__O[key];
    const r = this._rng(this._hash('n' + key)), N = 160 + Math.floor(r() * 80), pool = N + 90 + Math.floor(r() * 80);
    const C = this._cohort(key, N, s.nowN, obs, s.end, { mu: 0.0016, muJ: 0.0022, pull: 0.012, tau: 18, sig: 0.042, rev: 0.1 });
    const pt = s.nside === 1 ? 'down' : 'up', u2p = u => s.nprice(u), arrow = s.nside === 1 ? '↑' : '↓';
    const res = {
      N, pool, obs, end: s.end, W: s.width, edgeP: s.nedge, mode: 'brk', arrow,
      cond: k + ' · ' + (s.side === 1 ? 'лонг' : 'шорт') + ' · слом DR ' + arrow + ' ±15 мин от ' + this._clk(s.failed) + ' · цена ±0,25 IDR',
      kinds: [
        this._kind({ id: 'pull', role: 'Откат', hue: this._C().pull, shape: 'tri', point: pt, layer: 'pull' }, C.map(p => [p.mn, p.tmn]), u2p, obs, N),
        this._kind({ id: 'cont', role: 'Продолжение', hue: this._C().cont, shape: 'terr', layer: 'cont' }, C.map(p => [p.mx, p.tmx]), u2p, obs, N)
      ]
    };
    return (this.__O[key] = res);
  }
  // before the confirmation: the upper and the lower extreme of the rest of the session, among sessions not confirmed yet;
  // the direction shares are the first later confirmation; sessions that never confirm stay in the denominator
  _ovWait(k, obs, s) {
    const key = this._D().day + '|wait|' + k + '|' + obs; this.__O = this.__O || {};
    if (this.__O[key]) return this.__O[key];
    const r = this._rng(this._hash('n' + key)), N = 480 + Math.floor(r() * 160), pool = N + 300 + Math.floor(r() * 200);
    const w = s.width, u = p => (p - s.idrL) / w, u2p = v => s.idrL + v * w;
    const C = this._cohort(key, N, u(s.priceNow), obs, s.end, { mu: s.boxUp ? 0.0004 : -0.0004, muJ: 0.0006, pull: 0, tau: 1, sig: 0.04, hiC: u(s.drH), loC: u(s.drL), trend: 0.0022 });
    const up = C.filter(p => p.cross === 1).length, dn = C.filter(p => p.cross === -1).length;
    const res = {
      N, pool, obs, end: s.end, W: w, edgeP: s.idrL, mode: 'wait',
      dir: { up: 100 * up / N, dn: 100 * dn / N, none: 100 * (N - up - dn) / N, nUp: up, nDn: dn, nNone: N - up - dn },
      cond: k + ' · подтверждения нет к ' + this._clk(obs) + ' · цена ±0,25 IDR',
      kinds: [
        this._kind({ id: 'up', role: 'Верх', hue: this._C().neu, shape: 'terr', layer: 'cont' }, C.map(p => [p.mx, p.tmx]), u2p, obs, N),
        this._kind({ id: 'dn', role: 'Низ', hue: this._C().neu, shape: 'terr', layer: 'pull' }, C.map(p => [p.mn, p.tmn]), u2p, obs, N)
      ]
    };
    return (this.__O[key] = res);
  }
  // ---------- the glyphs: one per cell (a triangle for the pullback, a dot for the others), sized and lit by its step ----------
  // zoomed out, when 5-minute cells get narrower than 9 px, they merge into 15- or 30-minute cells (steps recomputed)
  _glyphCells(kd, ppm) {
    const f = 5 * ppm >= 9 ? 1 : 15 * ppm >= 9 ? 3 : 6;
    if (f === 1) return kd.cells;
    const ck = '__g' + f; if (kd[ck]) return kd[ck];
    const m = new Map(), st = 5 * f;
    for (const c of kd.cells) {
      const t = Math.floor(c.t / st) * st, k = c.u.toFixed(1) + '|' + t;
      if (!m.has(k)) m.set(k, { u: c.u, t, tHi: t + st, pLo: c.pLo, pHi: c.pHi, n: 0, cls: 4 });
      m.get(k).n += c.n;
    }
    return (kd[ck] = this._steps([...m.values()], kd.N));
  }
  // how the density is drawn (each artboard of the density row overrides it):
  // steps — one glyph per 5-minute cell, four steps of size and brightness against the densest cell;
  // solid — one glyph per cell, size by its share, fill by the number of sessions behind it (solid >= 8, half 4-7,
  //         outline 2-3, a dot for one);
  // units — blocks of 15 min x 0.2 IDR, each small glyph = 1 % of the similar sessions (count them = the share);
  // mosaic — the cells themselves as tiles: step 1 solid, step 2 translucent, step 3 outlined, single sessions a dot
  _dmode() { return 'steps'; }
  _glyph(kd, x, y, s, f) {
    const h = s * 0.86;
    if (kd.shape === 'tri') return kd.point === 'down'
      ? 'M' + f(x - s / 2) + ',' + f(y - h / 2) + 'L' + f(x + s / 2) + ',' + f(y - h / 2) + 'L' + f(x) + ',' + f(y + h / 2) + 'Z'
      : 'M' + f(x) + ',' + f(y - h / 2) + 'L' + f(x + s / 2) + ',' + f(y + h / 2) + 'L' + f(x - s / 2) + ',' + f(y + h / 2) + 'Z';
    const r = s * 0.42;
    return 'M' + f(x - r) + ',' + f(y) + 'a' + f(r) + ',' + f(r) + ' 0 1,0 ' + f(2 * r) + ',0a' + f(r) + ',' + f(r) + ' 0 1,0 ' + f(-2 * r) + ',0Z';
  }
  _glyphs(sc, kd) {
    const X = sc.X, Y = sc.Y, ppm = sc.PW / (sc.v1 - sc.v0), out = [[], [], [], []], st = [], f = v => v.toFixed(1), mode = this._dmode();
    if (mode === 'units') return this._units(sc, kd);
    const SZ = [0.9, 0.62, 0.4, 0.18], xo = X(sc.obs), cells = this._glyphCells(kd, ppm), mx = Math.max(1, ...cells.map(c => c.n));
    for (const c of cells) {
      const xa = X(c.t), xb = X(c.tHi); if (xb <= xo || xa >= sc.PW) continue;
      const y0 = Y(c.pHi), y1 = Y(c.pLo); if (y1 < 0 || y0 > sc.PH) continue;
      const base = Math.min(xb - xa, y1 - y0);
      if (mode === 'mosaic') {
        const a = Math.max(xa, xo) + 1.5, b = xb - 1.5, t = y0 + 1.5, u = y1 - 1.5;
        if (b - a < 1 || u - t < 1) continue;
        if (c.cls === 4) { out[3].push(this._glyph({ shape: 'dot' }, (a + b) / 2, (t + u) / 2, Math.max(2, base * 0.16), f)); continue; }
        const r = 'M' + f(a) + ',' + f(t) + 'H' + f(b) + 'V' + f(u) + 'H' + f(a) + 'Z';
        if (c.cls === 3) st.push(r); else out[c.cls - 1].push(r);
        continue;
      }
      let s, lv;
      if (mode === 'solid') { s = c.n === 1 ? base * 0.16 : base * (0.3 + 0.62 * Math.sqrt(c.n / mx)); lv = c.n >= 8 ? 0 : c.n >= 4 ? 1 : c.n >= 2 ? -1 : 3; }
      else { s = base * SZ[c.cls - 1]; lv = c.cls - 1; }
      s = Math.max(2, Math.min(17, s));
      const x = Math.max((xa + xb) / 2, xo + s / 2 + 1), y = (y0 + y1) / 2, p = this._glyph(kd, x, y, s, f);
      if (lv < 0) st.push(p); else out[lv].push(p);
    }
    return { p: out.map(a => a.join('') || 'M0,0'), sp: st.join('') || 'M0,0' };
  }
  // units: blocks of 15 min x 0.2 IDR; inside a block as many small glyphs as whole percents of the similar sessions
  // whose extreme fell there (rounded); under half a percent but at least one session: a faint dot
  _units(sc, kd) {
    const X = sc.X, Y = sc.Y, f = v => v.toFixed(1), xo = X(sc.obs), out = [[], [], [], []], m = new Map(), t0 = Math.floor(sc.obs / 5) * 5;
    for (const c of kd.cells) {                        // 15-minute blocks counted from the current moment
      const bu = Math.round(Math.floor(c.u / 0.2 + 1e-9) * 2) / 10, t = t0 + Math.floor((c.t - t0) / 15) * 15, k = bu.toFixed(1) + '|' + t;
      if (!m.has(k)) m.set(k, { bu, t, n: 0 });
      m.get(k).n += c.n;
    }
    const g = 12, s = 9;
    for (const b of m.values()) {
      const pa = kd.u2p(b.bu), pb = kd.u2p(b.bu + 0.2), xa = Math.max(X(b.t), xo), xb = X(b.t + 15), y0 = Y(Math.max(pa, pb)), y1 = Y(Math.min(pa, pb));
      if (xb <= xo || xa >= sc.PW || y1 < 0 || y0 > sc.PH) continue;
      const units = Math.round(100 * b.n / kd.N);
      if (!units) { out[3].push(this._glyph({ shape: 'dot' }, (xa + xb) / 2, (y0 + y1) / 2, 3, f)); continue; }
      const cols = Math.max(1, Math.floor((xb - xa - 2) / g)), rows = Math.max(1, Math.floor((y1 - y0 - 2) / g)), k = Math.min(units, cols * rows);
      const used = Math.min(k, cols), nr = Math.ceil(k / cols), gx = (xa + xb) / 2 - (used - 1) * g / 2, gy = (y0 + y1) / 2 - (nr - 1) * g / 2;
      for (let i = 0; i < k; i++) out[units >= 5 ? 0 : 1].push(this._glyph(kd, gx + (i % cols) * g, gy + Math.floor(i / cols) * g, s, f));
    }
    return { p: out.map(a => a.join('') || 'M0,0'), sp: 'M0,0' };
  }
  // the drawn glyph layers of the moment (cached per view: hover and crosshair do not recompute them)
  _layers(sc, st) {
    const ov = sc.ov, res = { A: null, B: null };
    if (!ov) return res;
    const vk = [sc.act, sc.obs, sc.live, sc.v0, sc.v1, sc.lo, sc.hi, sc.PW, sc.PH, st.layers.pull, st.layers.cont, this._D().day, this._dmode()].map(String).join('|');
    if (this.__LK === vk) return this.__LV;
    const slots = ov.kinds.filter(kd => st.layers[kd.layer]).map(kd => { const g = this._glyphs(sc, kd); return { c: kd.hue, p: g.p, sp: g.sp }; });
    res.A = slots[0] || null; res.B = slots[1] || null;
    this.__LK = vk; this.__LV = res;
    return res;
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
  _setScene(s) {
    const up = { scene: s, session: 'RDR', rp: s === 'wait' ? { sess: 'RDR', at: 640 } : null, pick: null, hover: null, scrub: null, yz: 1, v0: 545, v1: 970 };
    this.__LK = null; this.setState(up);
  }
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
  // the object under the pointer (or pinned): a cell, a zone, a price bin or a time bin of one kind, or a whole time column
  _target(sc) {
    const ov = sc.ov, hp = sc.hp; if (!ov || !hp.length) return null;
    const kd = id => ov.kinds.find(q => q.id === id);
    if (hp[0] === 'cell') { const K = kd(hp[1]); const c = K && K.cells.find(q => q.t === +hp[2] && Math.abs(q.pLo - +hp[3]) < 1e-6); if (c) return { what: 'cell', K, t0: Math.max(c.t, sc.obs), t1: c.tHi, pLo: c.pLo, pHi: c.pHi, n: c.n, pct: c.pct, cls: c.cls, blob: c.cl ? K.clusters[c.cl - 1] : null }; }
    if (hp[0] === 'blob') { const K = kd(hp[1]); const b = K && K.clusters.find(q => q.rank === +hp[2]); if (b) return { what: 'blob', K, t0: Math.max(b.t0, sc.obs), t1: b.t1, pLo: b.pLo, pHi: b.pHi, n: b.n, pct: b.pct, rank: b.rank, blob: b }; }
    if (hp[0] === 'pbin') { const K = kd(hp[1]); const b = K && K.pbins.find(q => Math.abs(q.pLo - +hp[2]) < 1e-6); if (b) return { what: 'pbin', K, t0: sc.obs, t1: ov.end, pLo: b.pLo, pHi: b.pHi, n: b.n, pct: b.pct }; }
    if (hp[0] === 'tbin') { const K = kd(hp[1]); const b = K && K.tbins.find(q => q.t === +hp[2]); if (b) return { what: 'tbin', K, t0: Math.max(b.t, sc.obs), t1: b.tHi, n: b.n, pct: b.pct, noPrice: true }; }
    if (hp[0] === 'col') { const t = +hp[1]; return { what: 'col', t0: Math.max(t, sc.obs), t1: t + 15, noPrice: true, parts: ov.kinds.map(K => { const b = K.tbins.find(q => q.t === t); return { K, n: b ? b.n : 0, pct: b ? b.pct : 0 }; }) }; }
    return null;
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
    // --- price range: visible bars, the active DR, the densest zones in view (they may widen the scale by a third at most)
    let lo = Infinity, hi = -Infinity, olo = Infinity, ohi = -Infinity;
    for (const b of vis) { if (b.l < lo) lo = b.l; if (b.h > hi) hi = b.h; }
    if (A.drH != null && A.end > v0 && A.start < v1) { lo = Math.min(lo, A.drL); hi = Math.max(hi, A.drH); }
    if (ov) for (const kd of ov.kinds) if (L[kd.layer]) for (const b of kd.clusters) if (b.t1 > v0 && b.t0 < v1) { olo = Math.min(olo, b.pLo); ohi = Math.max(ohi, b.pHi); }
    if (isFinite(lo) && isFinite(olo)) { const bs = Math.max(hi - lo, 20); lo = Math.min(lo, Math.max(olo, lo - 0.33 * bs)); hi = Math.max(hi, Math.min(ohi, hi + 0.33 * bs)); }
    if (!isFinite(lo)) { lo = 24400; hi = 24800; }
    if (hi - lo < 20) { const m = (hi + lo) / 2; lo = m - 10; hi = m + 10; }
    const pad = (hi - lo) * 0.07; lo -= pad; hi += pad;
    if (st.yz !== 1) { const m = (lo + hi) / 2, half = (hi - lo) / 2 / st.yz; lo = m - half; hi = m + half; }
    const Y = p => (hi - p) / (hi - lo) * PH;
    const inY = yy => yy > -1 && yy < PH + 1;
    const out = { S, A, ov, act, obs, live, X, Y, lo, hi, sp, bw, hk, hp, K, PW, PH, v0, v1 };
    const after = t => !live && t > obs;
    // which STD side is in play: the confirmation side, after a break the side of the break, before a confirmation none
    const playSide = A.status === 'broken' ? A.nside : A.side || 0;
    out.playSide = playSide;
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
          const wI = s.idrH - s.idrL, fromLow = s.side === -1;
          for (let j = 1; j <= 9; j++) {
            const v = fromLow ? s.idrL + j * wI / 10 : s.idrH - j * wI / 10, yy = Math.round(Y(v));
            out.grid.push({ x: Math.round(xa), y: yy, w: Math.max(1, Math.round(xb - xa)), h: 1, bg: 'rgba(203,213,225,0.30)' });
            if (j !== 5 && xa > 22 && xb - xa >= 90) out.gridT.push({ x: Math.round(xa) - 5, y: yy - 7, t: this._num(j / 10, 1) });
          }
        }
      }
      const lx = Math.max(X(s.start), 0);
      if (X(s.end) > 8 && lx < PW - 40) {
        const hv = this._hv('sess|' + k);
        const sub = s.status === 'confirmed' ? (live ? 'идёт' : '') : s.status === 'broken' ? 'слом DR' : s.status === 'done' ? (s.failed ? 'DR сломан' : 'DR удержался') : s.status === 'waiting' ? 'ждёт подтверждения' : s.status === 'forming' ? 'формируется' : '';
        out.slabels.push({ x: Math.round(lx) + 6, t: k, c: active ? K.text : K.text3, fw: active ? 700 : 600, sub, dot: k === act && live && (s.status === 'confirmed' || s.status === 'broken') ? 'inline-block' : 'none',
          click: () => { if (this._suppressed()) return; if (k !== this._st().session || this._st().rp) this._selSession(k); }, enter: hv.enter, leave: hv.leave, bg: sessHl ? K.hover : 'transparent' });
      }
    }
    // --- levels: the active session as the Pine DR/IDR V1.5 lines, the STD of the side in play brighter;
    //     the earlier boxes of the day and yesterday's RDR as quiet structure running to the right
    out.lines = []; out.lhits = []; out.tags = [];
    const hlLevel = hp[0] === 'lvl' ? hp[1] + '|' + hp[2] : null;
    const pushLine = (k, l, xa, xb, op, th, bg, tag) => {
      const yy = Y(l.p); if (!inY(yy) || xb - xa < 2) return;
      const on = hlLevel === k + '|' + l.id;
      if (on) { th += 1; op = 1; } else if (hlLevel && hlLevel.startsWith(k + '|')) op *= 0.5;
      out.lines.push({ x: Math.round(xa), y: Math.round(yy) - Math.floor(th / 2), w: Math.round(xb - xa), h: th, bg, op: Math.round(op * 100) / 100, sh: on ? '0 0 8px ' + this._a('#FFFFFF', 0.55) : 'none' });
      const lk = 'lvl|' + k + '|' + l.id, hv = this._hv(lk);
      out.lhits.push({ x: Math.round(xa), y: Math.round(yy) - 4, w: Math.round(xb - xa), h: 9, enter: hv.enter, leave: hv.leave, click: hv.click });
      if (tag) out.tags.push(Object.assign({ y: yy, h: 20, price: this._px(l.p), on, key: lk, pri: 0 }, tag));
    };
    if (L.struct) {
      const early = D.ORDER.filter(k => k !== act && S[k].drH != null && D.SESS[k].start < D.SESS[act].start);
      const src = [{ k: 'PREV', s: D.PREV, xa: 0, name: 'RDR 23.09' }].concat(early.map(k => ({ k, s: S[k], xa: Math.max(0, X(S[k].start)), name: k })));
      for (const q of src) {
        const s = q.s, xb = PW, op0 = q.k === 'PREV' ? 0.26 : 0.32;
        const Ls = [{ id: 'drH', p: s.drH, kind: 'dr' }, { id: 'drL', p: s.drL, kind: 'dr' }, { id: 'idrH', p: s.idrH, kind: 'idr' }, { id: 'idrL', p: s.idrL, kind: 'idr' }, { id: 'mid', p: (s.idrH + s.idrL) / 2, kind: 'mid' }];
        for (const l of Ls) {
          const bg = l.kind === 'dr' ? '#CBD5E1' : l.kind === 'idr' ? this._dashH('#CBD5E1', 9, 4) : this._dashDotH('#CBD5E1');
          const tag = l.kind === 'dr' || (l.kind === 'mid' && q.k === 'ADR') ? { kind: 'lvl2', name: q.name + (l.kind === 'mid' ? ' mid' : '') } : null;
          pushLine(q.k, l, q.xa, xb, op0, 1, bg, tag);
        }
      }
    }
    for (const k of D.ORDER) {
      const s = S[k]; if (s.drH == null) continue;
      const active = k === act;
      if (!active && D.SESS[k].start < D.SESS[act].start && L.struct) continue;   // drawn above as structure
      const xa = Math.max(0, X(s.start)), xb = Math.min(PW, X(s.status === 'forming' ? s.winEnd : s.end));
      if (xb - xa < 2) continue;
      const Ls = [{ id: 'drH', p: s.drH, kind: 'dr', name: 'DR' }, { id: 'drL', p: s.drL, kind: 'dr', name: 'DR' }, { id: 'idrH', p: s.idrH, kind: 'idr', name: 'IDR' }, { id: 'idrL', p: s.idrL, kind: 'idr', name: 'IDR' }];
      if (s.complete) {
        Ls.push({ id: 'mid', p: (s.idrH + s.idrL) / 2, kind: 'mid', name: 'mid' }, { id: 'open', p: s.open, kind: 'open', name: 'open' });
        const step = (s.idrH - s.idrL) / 2;
        for (let j = 1; j <= 10; j++) {
          Ls.push({ id: 'u' + j, p: s.idrH + j * step, kind: 'std', name: this._pine(j, true), sd: 1, j });
          Ls.push({ id: 'd' + j, p: s.idrL - j * step, kind: 'std', name: this._pine(j, false), sd: -1, j });
        }
      }
      for (const l of Ls) {
        let th = 1, bg, op = 1;
        if (l.kind === 'dr') { th = 2; bg = K.white; op = 0.92; }
        else if (l.kind === 'idr') { th = 2; bg = this._dashH('#F1F5F9', 9, 4); op = 0.86; }
        else if (l.kind === 'open') { bg = K.up; op = 0.8; }
        else if (l.kind === 'mid') { bg = this._dashDotH('#E2E8F0'); op = 0.75; }
        else { bg = this._dashDotH('#E2E8F0'); const play = active ? playSide : s.side || 0; op = !play ? 0.5 : l.sd === play ? 0.85 : 0.2; if (l.sd === play) th = 1; }
        if (!active) op *= 0.36;
        if (active && after(s.start)) op *= 0.4;
        let tag = null;
        if (active) {
          const play = playSide, show = l.kind !== 'std' || (!play ? l.j <= 2 : l.sd === play);
          if (show) tag = { kind: l.kind, name: l.name, c: l.kind === 'std' ? l.sd * l.j : null, pri: l.kind === 'dr' || l.kind === 'idr' ? 1 : 0, sess: k };
        }
        pushLine(k, l, xa, xb, op, th, bg, tag);
      }
    }
    // --- current / replay price
    const lastBar = D.bars[D.bars.length - 1];
    out.priceLine = null;
    if (live) {
      const upb = lastBar.c >= lastBar.o, yy = Y(lastBar.c);
      if (inY(yy)) out.tags.push({ y: yy, h: 34, kind: 'price', name: '', price: this._px(lastBar.c), sub: '01:52', col: upb ? K.up : K.dn, on: hk === 'price', key: 'price', pri: 2 });
      const xl = X(lastBar.t + 2.5) + bw / 2 + 3;
      if (inY(yy) && xl < PW) out.priceLine = { x: Math.round(Math.max(0, xl)), y: Math.round(yy), w: Math.max(0, Math.round(PW - Math.max(0, xl))), h: 1, bg: this._dashH(upb ? K.up : K.dn, 3, 3), op: 0.55 };
    } else if (A.priceNow != null) {
      const yy = Y(A.priceNow);
      if (inY(yy)) out.tags.push({ y: yy, h: 20, kind: 'rprice', name: '', price: this._px(A.priceNow), col: K.replay, on: hk === 'price', key: 'price', pri: 2 });
    }
    // --- overlay: hit cells, zone rectangles in pixels, the highlighted object
    out.cells = []; out.blobs = []; out.hl = []; out.guide = null; out.hlp = null;
    const rect = (t0, t1, pLo, pHi) => ({ x0: X(Math.max(t0, obs)), x1: X(t1), y0: Y(pHi), y1: Y(pLo) });
    const T = this._target(out);
    out.target = T;
    if (ov) {
      for (const kd of ov.kinds) {
        if (!L[kd.layer]) continue;
        for (const c of kd.cells) {
          const R = rect(c.t, c.tHi, c.pLo, c.pHi);
          if (R.x1 <= 0 || R.x0 >= PW || R.x1 - R.x0 < 1 || R.y1 < 0 || R.y0 > PH) continue;
          const key = 'cell|' + kd.id + '|' + c.t + '|' + c.pLo, hv = this._hv(key);
          out.cells.push({ x: Math.round(R.x0), y: Math.round(R.y0), w: Math.max(1, Math.round(R.x1 - R.x0)), h: Math.max(1, Math.round(R.y1 - R.y0)), key, kid: kd.id, enter: hv.enter, leave: hv.leave, click: hv.click });
        }
        for (const b of kd.clusters) {
          const R = rect(b.t0, b.t1, b.pLo, b.pHi);
          if (R.x1 <= 0 || R.x0 >= PW || R.y1 < 0 || R.y0 > PH) continue;
          const key = 'blob|' + kd.id + '|' + b.rank, hv = this._hv(key);
          out.blobs.push({ R, b, kd, key, hue: kd.hue, on: hk === key, px: X(Math.max(b.tp, obs)), py: Y(b.pp), enter: hv.enter, leave: hv.leave, click: hv.click });
        }
      }
      if (T) {
        const box = (R, hue, strong) => out.hl.push({ x: Math.round(R.x0), y: Math.round(R.y0), w: Math.max(2, Math.round(R.x1 - R.x0)), h: Math.max(2, Math.round(R.y1 - R.y0)), bd: (strong ? 1.5 : 1) + 'px solid ' + (strong ? '#FFFFFF' : this._a(hue, 0.9)), bg: this._a(hue, strong ? 0.16 : 0.08) });
        // the cells of a cluster: a quiet wash under its glyphs (no outline, the gaps between glyphs stay readable)
        if (T.blob) for (const c of T.blob.mem) { const R = rect(c.t, c.tHi, c.pLo, c.pHi); out.hl.push({ x: Math.round(R.x0), y: Math.round(R.y0), w: Math.max(2, Math.round(R.x1 - R.x0)), h: Math.max(2, Math.round(R.y1 - R.y0)), bd: 'none', bg: this._a(T.K.hue, T.what === 'blob' ? 0.2 : 0.09) }); }
        if (T.what === 'col') {
          for (const kd of ov.kinds) if (L[kd.layer]) for (const c of kd.cells) if (c.t >= +hp[1] && c.t < +hp[1] + 15) box(rect(c.t, c.tHi, c.pLo, c.pHi), kd.hue, false);
        } else if (T.what === 'tbin') {
          for (const c of T.K.cells) if (c.t >= +hp[2] && c.t < +hp[2] + 15) box(rect(c.t, c.tHi, c.pLo, c.pHi), T.K.hue, false);
        } else if (T.what === 'pbin') {
          for (const c of T.K.cells) if (Math.abs(c.pLo - T.pLo) < 1e-6) box(rect(c.t, c.tHi, c.pLo, c.pHi), T.K.hue, false);
        } else if (T.what === 'cell') box(rect(T.t0, T.t1, T.pLo, T.pHi), T.K.hue, true);
        const hue = T.K ? T.K.hue : '#D1D4DC', R = T.noPrice ? { x0: X(T.t0), x1: X(T.t1), y0: PH, y1: PH } : rect(T.t0, T.t1, T.pLo, T.pHi);
        out.guide = { R, hue, t0: T.t0, t1: T.t1, pLo: T.pLo, pHi: T.pHi, noPrice: !!T.noPrice, noTime: T.what === 'pbin' };
      }
    }
    // guides from the highlighted object to the axes, with its boundary times and prices
    out.glines = []; out.ttags = [];
    if (out.guide) {
      const G = out.guide, R = G.R, col = this._a(G.hue, 0.75), gx = cfg.PW + (cfg.projW || 0);
      const xa = Math.max(0, R.x0), xb = Math.min(PW, R.x1);
      if (!G.noTime) {
        out.glines.push({ x: Math.round(xa), y: Math.round(R.y1), w: 1, h: Math.max(0, PH - Math.round(R.y1)), bg: this._dashV(col, 3, 3) });
        out.glines.push({ x: Math.round(xb), y: Math.round(R.y1), w: 1, h: Math.max(0, PH - Math.round(R.y1)), bg: this._dashV(col, 3, 3) });
        out.ttags.push({ x: xa, t: this._clk(G.t0), col: G.hue, fg: '#0B0D10', pri: 3 }, { x: xb, t: this._clk(G.t1), col: G.hue, fg: '#0B0D10', pri: 3 });
      }
      if (!G.noPrice) {
        const x1 = G.noTime ? 0 : Math.round(xb);
        out.glines.push({ x: x1, y: Math.round(R.y0), w: Math.max(0, gx - x1), h: 1, bg: this._dashH(col, 3, 3) });
        out.glines.push({ x: x1, y: Math.round(R.y1), w: Math.max(0, gx - x1), h: 1, bg: this._dashH(col, 3, 3) });
        out.tags.push({ y: R.y0, h: 20, kind: 'guide', name: '', price: this._px(G.pHi), col: G.hue, on: true, pri: 3, guide: true });
        out.tags.push({ y: R.y1, h: 20, kind: 'guide', name: '', price: this._px(G.pLo), col: G.hue, on: true, pri: 3, guide: true });
      }
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
    // confirmation and DR-break marks at their candles
    out.pills = [];
    for (const k of D.ORDER) {
      const s = S[k]; if (!s.conf) continue;
      const mk = (minute, bg, below, key, text, wid) => {
        const b = D.bars.find(q => q.t + 5 === minute); if (!b || b.t + 5 <= v0 || b.t >= v1 || (!live && k === act && minute > obs)) return;
        const xc = X(b.t + 2.5), yy = below ? Y(b.l) + 6 : Y(b.h) - 24, hv = this._hv(key), on = hk === key;
        out.pills.push({ x: Math.round(xc - wid / 2), y: Math.round(yy), w: wid, t: text, bg, op: k === act ? 1 : 0.6, bd: on ? '1px solid #FFFFFF' : '1px solid ' + this._a('#FFFFFF', 0.18), enter: hv.enter, leave: hv.leave, click: hv.click });
      };
      mk(s.conf, s.side === 1 ? K.up : K.dn, s.side === -1, 'conf|' + k, (s.side === 1 ? '↑ ' : '↓ ') + this._clk(s.conf), 52);
      if (s.failed) mk(s.failed, K.brk, s.side === 1, 'fail|' + k, 'Слом DR ' + (s.side === 1 ? '↓ ' : '↑ ') + this._clk(s.failed), 108);
    }
    // current minute and the replay moment
    out.vlines = [];
    const xn = X(D.NOW);
    if (xn > 0 && xn < PW) { out.vlines.push({ x: Math.round(xn), y: 0, w: 1, h: PH, bg: this._dashV(this._a('#D1D4DC', 0.34), 6, 4), op: 1 }); out.ttags.push({ x: xn, t: this._clk(D.NOW), col: '#2A2E39', fg: '#FFFFFF', pri: 1 }); }
    if (!live) { const xm = X(obs); if (xm > 0 && xm < PW) { out.vlines.push({ x: Math.round(xm), y: 0, w: 1, h: PH, bg: K.replay, op: 0.9 }); out.ttags.push({ x: xm, t: 'момент ' + this._clk(obs), col: K.replay, fg: '#0B0D10', pri: 2 }); } }
    // crosshair
    out.xh = []; out.hoverBar = null;
    if (st.mx != null && !st.drag && st.mx >= 0 && st.mx < PW && st.my >= 0 && st.my < PH) {
      const tm = v0 + st.mx / PW * span, tb = Math.floor(tm / 5) * 5, xc = Math.round(X(tb + 2.5));
      out.xh.push({ x: xc, y: 0, w: 1, h: PH, bg: this._dashV(this._a('#9598A1', 0.6), 5, 4) }, { x: 0, y: Math.round(st.my), w: PW + (cfg.projW || 0), h: 1, bg: this._dashH(this._a('#9598A1', 0.6), 5, 4) });
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
      out.tlabels.push({ x: Math.round(xx), t: ((t % 1440) + 1440) % 1440 === 0 ? (t < 720 ? D.mid[0] : D.mid[1]) : this._clk(t) });
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
  _tagBoxes(sc, xs) {
    const K = this._C();
    return sc.tags.map(t => {
      let bg = '#1B1F27', fg = K.text, bd = '1px solid #3A404C', fw = 500, fs = '12.5px';
      if (t.kind === 'dr') { bg = K.white; fg = '#0B0D10'; bd = '1px solid ' + K.white; fw = 600; }
      else if (t.kind === 'idr') { bg = '#0B0D10'; fg = '#F1F5F9'; bd = '1px solid #F1F5F9'; }
      else if (t.kind === 'open') { bg = '#0B0D10'; fg = K.up; bd = '1px solid ' + K.up; }
      else if (t.kind === 'lvl2') { bg = '#0E1115'; fg = '#9AA1AD'; bd = '1px solid #2B313C'; fs = '11.5px'; }
      else if (t.kind === 'price') { bg = t.col; fg = '#FFFFFF'; bd = '1px solid ' + t.col; fw = 600; }
      else if (t.kind === 'rprice') { bg = '#0B0D10'; fg = K.replay; bd = '1px solid ' + K.replay; fw = 600; }
      else if (t.kind === 'guide' || t.kind === 'cross') { bg = t.col; fg = t.kind === 'cross' ? '#FFFFFF' : '#0B0D10'; bd = '1px solid ' + t.col; fw = 600; }
      if (t.on && (t.kind === 'std' || t.kind === 'mid' || t.kind === 'lvl2')) { bg = '#E2E8F0'; fg = '#0B0D10'; bd = '1px solid #E2E8F0'; }
      if (t.on && t.kind === 'idr') { bg = '#F1F5F9'; fg = '#0B0D10'; }
      const hv = t.key ? this._hv(t.key) : {};
      return {
        x: xs + 1, y: Math.round(t.ty - t.h / 2), h: t.h, bg, fg, bd, fw, fs, name: t.name, nd: t.name ? 'inline' : 'none', price: t.price,
        sub: t.sub || '', sd: t.sub ? 'block' : 'none', enter: hv.enter, leave: hv.leave, click: hv.click
      };
    });
  }
