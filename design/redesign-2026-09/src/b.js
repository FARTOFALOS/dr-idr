  // ================= variant B · Сценарий =================
  _cfg() { return { W: 1548, H: 742, PW: 1416, PH: 714, ladderW: 0, scaleW: 132, axisH: 28 }; }
  // smoothed density of where/when the extreme landed, and its iso-lines (marching squares), in (minute, IDR) units
  _kde(ov, kind) {
    const key = '__kde_' + kind;
    if (ov[key]) return ov[key];
    const pts = kind === 'min' ? ov.ptsMin : ov.ptsMax, obs = ov.t0, t0 = pts.reduce((m, p) => Math.min(m, p[0]), Infinity);
    const cs = pts.map(p => p[1]).sort((a, b) => a - b), cLo = this._q(cs, 0.04) - 0.3, cHi = this._q(cs, 0.96) + 0.3;
    const ts = [], cc = [];
    for (let t = Math.min(obs, t0); t <= ov.end + 0.001; t += 5) ts.push(t);
    for (let c = cLo; c <= cHi + 1e-9; c += 0.05) cc.push(c);
    const sT = 12, sC = 0.085, G = ts.map(() => new Array(cc.length).fill(0));
    let mx = 0;
    for (let i = 0; i < ts.length; i++) for (let j = 0; j < cc.length; j++) {
      let v = 0;
      for (const p of pts) { const dt = (ts[i] - p[0]) / sT, dc = (cc[j] - p[1]) / sC; if (dt * dt + dc * dc < 16) v += Math.exp(-0.5 * (dt * dt + dc * dc)); }
      G[i][j] = v; if (v > mx) mx = v;
    }
    const segs = [0.3, 0.55, 0.8].map(lv => {
      const L = lv * mx, out = [];
      for (let i = 0; i < ts.length - 1; i++) for (let j = 0; j < cc.length - 1; j++) {
        const a = G[i][j], b = G[i + 1][j], c = G[i + 1][j + 1], d = G[i][j + 1];
        const idx = (a > L ? 8 : 0) | (b > L ? 4 : 0) | (c > L ? 2 : 0) | (d > L ? 1 : 0);
        if (idx === 0 || idx === 15) continue;
        const lerp = (v1, v2) => (L - v1) / (v2 - v1);
        const T = [ts[i], ts[i + 1]], C = [cc[j], cc[j + 1]];
        const e = {
          b: [T[0] + (T[1] - T[0]) * lerp(a, b), C[0]], r: [T[1], C[0] + (C[1] - C[0]) * lerp(b, c)],
          t: [T[0] + (T[1] - T[0]) * lerp(d, c), C[1]], l: [T[0], C[0] + (C[1] - C[0]) * lerp(a, d)]
        };
        const map = { 1: ['l', 't'], 2: ['t', 'r'], 3: ['l', 'r'], 4: ['b', 'r'], 5: ['l', 'b', 't', 'r'], 6: ['b', 't'], 7: ['l', 'b'], 8: ['l', 'b'], 9: ['b', 't'], 10: ['l', 't', 'b', 'r'], 11: ['b', 'r'], 12: ['l', 'r'], 13: ['t', 'r'], 14: ['l', 't'] }[idx];
        for (let k = 0; k < map.length; k += 2) out.push([e[map[k]], e[map[k + 1]]]);
      }
      return out;
    });
    return (ov[key] = { segs });
  }
  _contours(sc, kind) {
    const ov = sc.ov, A = sc.A; if (!ov) return ['', '', ''];
    const K = this._kde(ov, kind), X = sc.X, Y = sc.Y;
    return K.segs.map(list => list.map(s => 'M' + X(s[0][0]).toFixed(1) + ',' + Y(A.price(s[0][1])).toFixed(1) + 'L' + X(s[1][0]).toFixed(1) + ',' + Y(A.price(s[1][1])).toFixed(1)).join(''));
  }
  _panelB(sc) {
    const K = this._C(), A = sc.A, ov = sc.ov, hk = sc.hk, hp = sc.hp, f = this._facts(sc), G = sc.guide;
    const P = { f, conf: f.status === 'confirmed', zmin: [], zmax: [], touch: [], ins: null, risk: { pct: '', col: '#FFFFFF', w: 0, label: '', stop: '', stopLabel: '', bg: 'transparent', n: '', ntip: '' } };
    // inspector: what is under the pointer, else "now"
    const ins = { mode: 'now', title: sc.act + (sc.live ? ' · сейчас' : ' · на ' + this._clk(sc.obs)), hue: '#D1D4DC', rank: '', rd: 'none', big: '', rows: [] };
    if (G && G.kind && !G.pick) {
      const a = A.price(G.lo), b = A.price(G.hi);
      Object.assign(ins, { mode: 'obj', title: G.what || (G.kind === 'min' ? 'Откат закончится' : 'Экстремум'), hue: G.kind === 'min' ? K.retr : K.ext, rank: G.rank ? String(G.rank) : '', rd: G.rank ? 'flex' : 'none', big: this._pct(G.pct),
        rows: [['Время', this._clk(G.t0) + '–' + this._clk(G.t1)], ['Цена', this._px(Math.min(a, b)) + ' – ' + this._px(Math.max(a, b))], ['Шкала', this._sg(G.lo, 1) + '…' + this._sg(G.hi, 1) + ' IDR'], ['Сессий', G.n + ' из ' + ov.n]] });
    } else if (G && G.pick) {
      const a = A.price(G.lo), b = A.price(G.hi);
      Object.assign(ins, { mode: 'obj', title: G.kind === 'min' ? 'Выбор · откат' : 'Выбор · экстремум', hue: G.kind === 'min' ? K.retr : K.ext, big: this._clk(G.t0) + '–' + this._clk(G.t1), rows: [['Цена', this._px(Math.min(a, b)) + ' – ' + this._px(Math.max(a, b))], ['Шкала', this._sg(G.lo, 1) + '…' + this._sg(G.hi, 1) + ' IDR']] });
    } else if (hp[0] === 'lvl' || hp[0] === 'touch') {
      const tg = sc.tags.find(t => t.on && (t.key === hk || t.kind === 'guide'));
      const tc = ov && hp[0] === 'touch' ? ov.touch.find(q => Math.abs(q.L - +hp[1]) < 1e-6) : null;
      const lvlTag = hp[0] === 'lvl' ? sc.tags.find(t => t.key === hk || (t.key && t.key.startsWith(hk) && t.on)) : null;
      const tcl = lvlTag && ov && lvlTag.c != null ? ov.touch.find(q => Math.abs(q.L - lvlTag.c) < 1e-6) : null;
      Object.assign(ins, { mode: 'lvl', title: 'Уровень', hue: '#E2E8F0', big: hp[0] === 'touch' ? this._sg(+hp[1], 2) + ' IDR' : (lvlTag ? lvlTag.name : ''),
        rows: [['Цена', hp[0] === 'touch' ? this._px(A.price(+hp[1])) : lvlTag ? lvlTag.price : ''], ['Касание до ' + this._clk(A.end), tc ? this._pct(tc.pct) : tcl ? this._pct(tcl.pct) : '—']] });
      if (!tg && !lvlTag && !tc) ins.rows = [];
    } else if (f.status === 'confirmed') {
      ins.rows = [['Подтверждение', f.conf], [f.priceLabel, f.price], ['Похожих сессий', String(ov.n)]];
    } else if (f.status === 'done') {
      ins.big = f.big; ins.rows = [['Подтверждение', f.conf], ['Откат', f.retr], ['Расширение', f.ext]];
    } else if (f.pending) { ins.big = f.big; ins.rows = f.pending.slice(); }
    else { ins.big = f.big; if (f.dr) ins.rows = [[f.bigLabel, ''], ['DR', f.dr], ['IDR', f.idr]]; }
    ins.rowsV = ins.rows.map(r => ({ l: r[0], v: r[1] }));
    ins.bigShow = ins.big ? 'block' : 'none';
    P.ins = ins;
    if (P.conf) {
      const drl = 'lvl|' + sc.act + '|' + (A.side === 1 ? 'drL' : 'drH'), hv = this._hv(drl);
      P.risk = { pct: f.big, col: f.bigCol, w: Math.round(ov.drTrue * 3.36) / 1, label: f.bigLabel, stop: this._px(A.opp), stopLabel: A.side === 1 ? 'Слом DR: закрытие M5 ниже' : 'Слом DR: закрытие M5 выше', bg: hk === drl ? K.hover : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click, n: f.n, ntip: f.ntip };
      const zr = (kind, z) => {
        const key = 'zone|' + kind + '|' + z.rank, hv = this._hv(key), hue = kind === 'min' ? K.retr : K.ext;
        const soft = G && G.kind === kind && G.zone && G.zone.rank === z.rank && hk !== key, a = A.price(z.lo), b = A.price(z.hi);
        return { rank: String(z.rank), hue, time: this._clk(Math.max(z.t, sc.obs)) + '–' + this._clk(z.t_hi), price: this._px(Math.min(a, b)) + '–' + this._px(Math.max(a, b)), pct: this._pct(z.pct), bw: Math.max(2, Math.round(z.pct * 2.4)),
          bg: hk === key ? this._a(hue, 0.16) : soft ? this._a(hue, 0.08) : 'transparent', bd: hk === key ? '1px solid ' + this._a(hue, 0.7) : '1px solid transparent', enter: hv.enter, leave: hv.leave, click: hv.click };
      };
      P.zmin = ov.zonesMin.map(z => zr('min', z)); P.zmax = ov.zonesMax.map(z => zr('max', z));
      const lv = [2, 1.5, 1, 0.5, 0, -0.5, -1];
      let divDone = false;
      for (const L of lv) {
        const tc = ov.touch.find(q => Math.abs(q.L - L) < 1e-6); if (!tc) continue;
        if (!divDone && L < ov.x0) { P.touch.push({ div: 'flex', row: 'none', label: '', price: '', pct: '', w: 0, hue: 'transparent', now: 'цена ' + this._px(A.priceNow) + ' · ' + this._sg(ov.x0, 2), bg: 'transparent' }); divDone = true; }
        const key = 'touch|' + L, hv = this._hv(key), hue = L >= ov.x0 ? K.ext : K.retr;
        P.touch.push({ div: 'none', row: 'flex', label: this._sg(L, 1), price: this._px(A.price(L)), pct: this._pct(tc.pct), w: Math.max(2, Math.round(tc.pct * 1.1)), hue, now: '', bg: hk === key ? K.hover : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click });
      }
    }
    return P;
  }
  _nav(sc, st) {
    const K = this._C(), D = this._D(), W = 1548, x0 = 12, x1 = W - 12;
    const nx = t => x0 + (t - D.DAY0) / (D.DAY1 - D.DAY0) * (x1 - x0);
    const closes = D.bars.map(b => b.c), lo = Math.min(...closes), hi = Math.max(...closes);
    const ny = v => 19 + (hi - v) / (hi - lo) * 22;
    const spark = D.bars.map((b, i) => (i ? 'L' : 'M') + nx(b.t + 2.5).toFixed(1) + ',' + ny(b.c).toFixed(1)).join('');
    const segs = D.ORDER.map(k => {
      const s = sc.S[k], on = k === sc.act, hv = this._hv('sess|' + k), hl = sc.hk === 'sess|' + k;
      const status = s.status === 'done' ? (s.failed ? '✕' : '✓') : '';
      return { x: Math.round(nx(s.start)), w: Math.round(nx(s.end) - nx(s.start)), wx: Math.round(nx(s.start)), ww: Math.max(2, Math.round(nx(s.formed) - nx(s.start))),
        bg: on ? 'rgba(209,212,220,0.09)' : hl ? 'rgba(209,212,220,0.07)' : 'rgba(209,212,220,0.035)', bd: on ? '1px solid rgba(209,212,220,0.35)' : '1px solid transparent',
        t: k, sub: (s.conf ? (s.side === 1 ? '↑ ' : '↓ ') + this._clk(s.conf) : '') + (status ? ' · ' + (s.failed ? 'DR сломан' : 'DR удержался') : s.status === 'confirmed' && sc.live ? ' · идёт' : ''), c: on ? '#FFFFFF' : K.text2,
        click: e => { if (e && e.stopPropagation) e.stopPropagation(); if (k !== this._st().session || this._st().rp) this._selSession(k); }, enter: hv.enter, leave: hv.leave };
    });
    const center = e => {
      const rc = e.currentTarget.getBoundingClientRect(), sc2 = rc.width / W, px = (e.clientX - rc.left) / sc2;
      const t = D.DAY0 + (px - x0) / (x1 - x0) * (D.DAY1 - D.DAY0), s2 = this._st(), span = s2.v1 - s2.v0;
      let v0 = t - span / 2; v0 = Math.min(Math.max(v0, D.DAY0 - 30), D.DAY1 + 30 - span);
      this.setState({ v0, v1: v0 + span });
    };
    return { spark, segs, fx: Math.round(nx(Math.max(st.v0, D.DAY0 - 30))), fw: Math.max(6, Math.round(nx(Math.min(st.v1, D.DAY1 + 30)) - nx(Math.max(st.v0, D.DAY0 - 30)))), nowx: Math.round(nx(D.NOW)), mx: sc.live ? -10 : Math.round(nx(sc.obs)), click: center,
      labels: [-360, -120, 0, 240, 480, 720, 960].map(t => ({ x: Math.round(nx(t)), t: t === 0 ? '24 сен' : this._clk(t) })) };
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), K = this._C();
    const sc = this._scene(cfg, st), m = this._mouse(), xs = cfg.PW;
    const tb = this._toolbar(sc, st), P = this._panelB(sc), bot = this._bottom(sc, 1920, 168), nav = this._nav(sc, st);
    const anchors = sc.tags.filter(t => Math.abs(t.ty - t.y) > 1.5).map(t => ({ x: xs, y: Math.round(t.y), bg: t.kind === 'dr' ? K.white : '#9BA1AC' }));
    const conf = sc.A.conf ? (sc.A.side === 1 ? '↑ ' : '↓ ') + this._clk(sc.A.conf) : '';
    // clouds: blurred density cells (never before the observed minute), iso-lines on top, invisible cells for hover
    const xNow = Math.max(0, Math.round(sc.X(sc.obs)));
    const cloud = sc.cells.map(c => ({ x: c.x - xNow - 1, y: c.y - 1, w: c.w + 2, h: c.h + 2, bg: this._a(c.kind === 'min' ? K.retr : K.ext, Math.round((0.3 + 0.5 * c.f) * 100) / 100) }));
    const hits = sc.cells.map(c => ({ x: c.x, y: c.y, w: c.w, h: c.h, bd: c.bd === 'none' ? '1px solid transparent' : '1.5px solid #FFFFFF', enter: c.enter, leave: c.leave, click: c.click }));
    const cr = st.layers.rclust && sc.ov ? this._contours(sc, 'min') : ['', '', ''], ce = st.layers.eclust && sc.ov ? this._contours(sc, 'max') : ['', '', ''];
    const zl = sc.zones.map(z => ({ x: Math.round(z.R.x0 + (z.R.x1 - z.R.x0) / 2), y: Math.round(z.R.y0 + (z.R.y1 - z.R.y0) / 2) - 10, t: String(z.z.rank), pct: this._pct(z.z.pct), bg: z.hue, bd: sc.hk === z.key ? '1px solid #FFFFFF' : '1px solid ' + z.hue, box: sc.hk === z.key ? 'block' : 'none', bx: z.x, by: z.y, bw: z.w, bh: z.h, bb: '1.5px solid ' + z.hue, enter: z.enter, leave: z.leave, click: z.click }));
    // zone labels must not sit on each other
    zl.sort((a, b) => a.y - b.y);
    for (let i = 1; i < zl.length; i++) for (let j = 0; j < i; j++) if (Math.abs(zl[i].x - zl[j].x) < 64 && Math.abs(zl[i].y - zl[j].y) < 22) zl[i].y = zl[j].y + 22;
    return {
      tb, P, bot, nav, m, chartRef: this._refCb(), cursor: st.drag ? 'grabbing' : 'crosshair',
      boxes: sc.boxes, grid: sc.grid, gridT: sc.gridT, lines: sc.lines, lhits: sc.lhits, zlab: zl, xNow, cloudW: Math.max(0, cfg.PW - xNow), cloud, hits,
      cr0: cr[0], cr1: cr[1], cr2: cr[2], ce0: ce[0], ce1: ce[1], ce2: ce[2],
      picks: sc.picks, wicks: sc.wicks, bodies: sc.bodies, chits: sc.chits, pills: sc.pills, vlines: sc.vlines, glines: sc.glines, xh: sc.xh,
      ticks: sc.ticks, tags: this._tagBoxes(sc, xs, true), anchors,
      tlabels: sc.tlabels, ttags: sc.ttags, slabels: sc.slabels, lg: sc.legend, act: sc.act, conf, confBg: sc.A.side === 1 ? K.up : K.dn, confShow: conf ? 'inline-flex' : 'none',
      hasFan: !!sc.fan, fanArea: sc.fan ? sc.fan.area : 'M0,0', fanMid: sc.fan ? sc.fan.mid : 'M0,0',
      priceLine: sc.priceLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent', op: 0 }, touchLine: sc.touchLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent' },
      zoomIn: () => this._zoomBtn(-1), zoomOut: () => this._zoomBtn(1), reset: () => this._reset(), replay: !sc.live, live: sc.live
    };
  }
