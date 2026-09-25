  // ================= variant B′ · Сценарий, chosen by the operator on 2026-09-25 =================
  // Continuation (extension, the far extreme) is green and drawn as a soft cloud with iso-lines;
  // the pullback (retracement) is red and drawn as triangles pointing the way of the pullback, so the two never blend.
  // The band above the time axis scrubs time: over the past it shows the forecast as of that minute (hover replay),
  // over the future it lights the clusters of that 15-minute column.
  _cfg() { return { W: 1548, H: 742, PW: 1416, PH: 684, ladderW: 0, scaleW: 132, axisH: 28, bandH: 30 }; }
  _palX() { return { retr: '#FF5A5F', ext: '#34D399' }; }
  // both kinds are visible from the start: green continuation and red pullback are read together (operator, 2026-09-25)
  _st() {
    const s = this.state || {};
    return {
      session: s.session || 'RDR', rp: s.rp || null, scrub: s.scrub || null,
      v0: s.v0 != null ? s.v0 : 545, v1: s.v1 != null ? s.v1 : 970, yz: s.yz || 1,
      hover: s.hover || null, pick: s.pick || null,
      layers: s.layers || { rclust: true, eclust: true, fan: true, ladder: true },
      mx: s.mx != null ? s.mx : null, my: s.my != null ? s.my : null, drag: !!s.drag
    };
  }
  // smoothed density of where/when the extreme landed, and its iso-lines (marching squares), in (minute, IDR) units
  _kde(ov, kind) {
    const key = '__kde_' + kind;
    if (ov[key]) return ov[key];
    const pts = kind === 'min' ? ov.ptsMin : ov.ptsMax, t0 = pts.reduce((m, p) => Math.min(m, p[0]), Infinity);
    const cs = pts.map(p => p[1]).sort((a, b) => a - b), cLo = this._q(cs, 0.04) - 0.3, cHi = this._q(cs, 0.96) + 0.3;
    const ts = [], cc = [];
    for (let t = Math.min(ov.t0, t0); t <= ov.end + 0.001; t += 5) ts.push(t);
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
        const lerp = (v1, v2) => (L - v1) / (v2 - v1), T = [ts[i], ts[i + 1]], C = [cc[j], cc[j + 1]];
        const e = { b: [T[0] + (T[1] - T[0]) * lerp(a, b), C[0]], r: [T[1], C[0] + (C[1] - C[0]) * lerp(b, c)], t: [T[0] + (T[1] - T[0]) * lerp(d, c), C[1]], l: [T[0], C[0] + (C[1] - C[0]) * lerp(a, d)] };
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
  // triangle glyph inside a cell, pointing the way the pullback goes (down for a long, up for a short)
  _tri(R, f, side, on) {
    const w = R.x1 - R.x0, h = R.y1 - R.y0;
    const base = Math.min(w, h * 2.2), tw = Math.max(8, base * (0.3 + 0.36 * f)), th = Math.max(7, tw * 0.8);
    return { x: Math.round(R.x0 + (w - tw) / 2), y: Math.round(R.y0 + (h - th) / 2), w: Math.round(tw), h: Math.round(th),
      clip: side === 1 ? 'polygon(0% 0%, 100% 0%, 50% 100%)' : 'polygon(50% 0%, 100% 100%, 0% 100%)',
      op: on ? 1 : Math.round((0.42 + 0.5 * f) * 100) / 100, glow: on ? 'drop-shadow(0 0 5px rgba(255,90,95,0.9))' : 'none' };
  }
  _scrub() {
    if (this.__sh) return this.__sh;
    const move = e => {
      const p = this._local(e), cfg = this._cfg(), st = this._st();
      this.__sm = st.v0 + p.x / cfg.PW * (st.v1 - st.v0);
      if (this.__sraf) return;
      this.__sraf = requestAnimationFrame(() => {
        this.__sraf = null;
        const t = this.__sm, D = this._D(), s = this.state || {};
        if (t == null) return;
        const at = Math.floor(t / 5) * 5;
        if (at <= D.NOW) {                      // the past: the screen as it was at that candle close
          const k = this._sessIn(at);
          if (k) { if (!s.scrub || s.scrub.at !== at || s.scrub.sess !== k || s.hover) this.setState({ scrub: { sess: k, at }, hover: null }); }
          else if (s.scrub || s.hover) this.setState({ scrub: null, hover: null });
        } else {                                // the future: the clusters of that 15-minute column
          const key = 'col|' + Math.floor(t / 15) * 15;
          if (s.scrub || s.hover !== key) this.setState({ scrub: null, hover: key });
        }
      });
    };
    return (this.__sh = {
      move,
      leave: () => { this.__sm = null; const s = this.state || {}; if (s.scrub || (s.hover && s.hover.startsWith('col|'))) this.setState({ scrub: null, hover: null }); },
      click: e => { if (e && e.stopPropagation) e.stopPropagation(); if (this._suppressed()) return; const s = this.state || {}; if (s.scrub) this.setState({ rp: s.scrub, session: s.scrub.sess, scrub: null }); }
    });
  }
  _band(sc, st) {
    const K = this._C(), ov = sc.ov, cfg = this._cfg(), hk = sc.hk, G = sc.guide, bars = [];
    const mark = { x: -10, bg: 'transparent' };
    if (st.scrub) { mark.x = Math.round(sc.X(st.scrub.at)); mark.bg = K.replay; }
    else if (hk && hk.startsWith('col|')) { mark.x = Math.round(sc.X(+hk.split('|')[1] + 7.5)); mark.bg = '#D1D4DC'; }
    if (!ov) return { bars, mark };
    const L = st.layers;
    for (const chart of ['rtime', 'etime']) {
      if (chart === 'rtime' ? !L.rclust : !L.eclust) continue;
      const H = ov.H[chart], hue = chart === 'rtime' ? K.retr : K.ext, mx = Math.max(1, ...H.co);
      for (let j = 0; j < H.nb; j++) {
        if (!H.co[j]) continue;
        const t = H.lo + j * H.st, xa = sc.X(Math.max(t, sc.obs)), xb = sc.X(t + H.st);
        if (xb <= 0 || xa >= cfg.PW || xb - xa < 1) continue;
        const h = Math.max(2, Math.round(13 * Math.sqrt(H.co[j] / mx))), lit = G && (G.col || G.kind === (chart === 'rtime' ? 'min' : 'max')) && t + H.st > G.t0 && t < G.t1;
        bars.push({ x: Math.round(xa) + 1, w: Math.max(1, Math.round(xb - xa) - 2), y: chart === 'rtime' ? 15 : 15 - h, h, bg: this._a(hue, lit ? 1 : 0.55) });
      }
    }
    return { bars, mark };
  }
  _panelB(sc) {
    const K = this._C(), A = sc.A, ov = sc.ov, hk = sc.hk, hp = sc.hp, f = this._facts(sc), G = sc.guide;
    const P = { f, conf: f.status === 'confirmed', zmin: [], zmax: [], touch: [], ins: null, risk: { pct: '', col: '#FFFFFF', w: 0, label: '', stop: '', stopLabel: '', bg: 'transparent', n: '', ntip: '' } };
    const ins = { title: sc.act + (sc.live ? ' · сейчас' : ' · на ' + this._clk(sc.obs)), hue: '#D1D4DC', rank: '', rd: 'none', big: '', line: '' };
    if (G && G.col) {
      Object.assign(ins, { title: this._clk(G.t0) + '–' + this._clk(G.t1), line: 'откат закончится здесь: ' + this._pct(100 * G.nr / ov.n) + ' · экстремум: ' + this._pct(100 * G.ne / ov.n) });
    } else if (G && G.kind && !G.pick) {
      const a = A.price(G.lo), b = A.price(G.hi);
      Object.assign(ins, { title: G.kind === 'min' ? 'Откат закончится' : 'Экстремум', hue: G.kind === 'min' ? K.retr : K.ext, rank: G.rank ? String(G.rank) : '', rd: G.rank ? 'flex' : 'none', big: this._pct(G.pct),
        line: this._clk(G.t0) + '–' + this._clk(G.t1) + ' · ' + this._px(Math.min(a, b)) + '–' + this._px(Math.max(a, b)) + ' · ' + G.n + ' из ' + ov.n });
    } else if (G && G.pick) {
      const a = A.price(G.lo), b = A.price(G.hi);
      Object.assign(ins, { title: G.kind === 'min' ? 'Откат · выбор' : 'Экстремум · выбор', hue: G.kind === 'min' ? K.retr : K.ext, line: this._clk(G.t0) + '–' + this._clk(G.t1) + ' · ' + this._px(Math.min(a, b)) + '–' + this._px(Math.max(a, b)) });
    } else if (hp[0] === 'lvl' || hp[0] === 'touch') {
      const lvlTag = hp[0] === 'lvl' ? sc.tags.find(t => t.key && (t.key === hk || t.key.startsWith(hk)) && t.on) : null;
      const L2 = hp[0] === 'touch' ? +hp[1] : lvlTag && lvlTag.c != null ? lvlTag.c : null;
      const tc = ov && L2 != null ? ov.touch.find(q => Math.abs(q.L - L2) < 1e-6) : null;
      Object.assign(ins, { title: hp[0] === 'touch' ? 'Уровень ' + this._sg(L2, 1) : 'Уровень ' + (lvlTag ? lvlTag.name : ''), big: tc ? this._pct(tc.pct) : '',
        line: (hp[0] === 'touch' ? this._px(A.price(L2)) : lvlTag ? lvlTag.price : '') + (tc ? ' · касание до ' + this._clk(A.end) : '') });
    } else if (f.status === 'confirmed') {
      ins.line = f.conf + ' · ' + this._sg(A.nowCoord, 2) + ' IDR · ' + this._px(A.priceNow) + ' · ' + ov.n + ' похожих';
    } else if (f.status === 'done') {
      ins.big = f.big; ins.line = 'Подтверждение ' + f.conf + ' · откат ' + f.retr + ' · расширение ' + f.ext;
    } else if (f.pending) { ins.big = f.big; ins.line = f.pending.map(r => r[0] + ' ' + r[1]).join(' · '); }
    else { ins.big = f.big; ins.line = f.dr ? 'DR ' + f.dr + ' · IDR ' + f.idr : ''; }
    ins.bigShow = ins.big ? 'inline' : 'none';
    P.ins = ins;
    P.triShape = A.side === -1 ? 'polygon(50% 0%, 100% 100%, 0% 100%)' : 'polygon(0% 0%, 100% 0%, 50% 100%)';
    if (P.conf) {
      const drl = 'lvl|' + sc.act + '|' + (A.side === 1 ? 'drL' : 'drH'), hv = this._hv(drl);
      P.risk = { pct: f.big, col: f.bigCol, w: Math.round(ov.drTrue * 3.36), label: f.bigLabel, stop: this._px(A.opp), stopLabel: A.side === 1 ? 'Слом DR: закрытие M5 ниже' : 'Слом DR: закрытие M5 выше', bg: hk === drl ? K.hover : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click, n: f.n, ntip: f.ntip };
      const zr = (kind, z) => {
        const key = 'zone|' + kind + '|' + z.rank, hv = this._hv(key), hue = kind === 'min' ? K.retr : K.ext;
        const soft = G && G.kind === kind && G.zone && G.zone.rank === z.rank && hk !== key, a = A.price(z.lo), b = A.price(z.hi);
        return { rank: String(z.rank), hue, shape: kind === 'min' ? (A.side === 1 ? 'polygon(0% 0%, 100% 0%, 50% 100%)' : 'polygon(50% 0%, 100% 100%, 0% 100%)') : 'circle(50% at 50% 50%)',
          time: this._clk(Math.max(z.t, sc.obs)) + '–' + this._clk(z.t_hi), price: this._px(Math.min(a, b)) + '–' + this._px(Math.max(a, b)), pct: this._pct(z.pct),
          bg: hk === key ? this._a(hue, 0.14) : soft ? this._a(hue, 0.07) : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click };
      };
      P.zmin = ov.zonesMin.map(z => zr('min', z)); P.zmax = ov.zonesMax.map(z => zr('max', z));
      let divDone = false;
      for (const L of [2, 1.5, 1, 0.5, 0, -0.5, -1]) {
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
      return { x: Math.round(nx(s.start)), w: Math.round(nx(s.end) - nx(s.start)), wx: Math.round(nx(s.start)), ww: Math.max(2, Math.round(nx(s.formed) - nx(s.start))),
        bg: on ? 'rgba(209,212,220,0.09)' : hl ? 'rgba(209,212,220,0.07)' : 'rgba(209,212,220,0.035)', bd: on ? '1px solid rgba(209,212,220,0.35)' : '1px solid transparent',
        t: k, sub: (s.conf ? (s.side === 1 ? '↑ ' : '↓ ') + this._clk(s.conf) : '') + (s.status === 'done' ? ' · ' + (s.failed ? 'DR сломан' : 'DR удержался') : s.status === 'confirmed' && sc.live ? ' · идёт' : ''), c: on ? '#FFFFFF' : K.text2,
        click: e => { if (e && e.stopPropagation) e.stopPropagation(); if (k !== this._st().session || this._st().rp) this._selSession(k); }, enter: hv.enter, leave: hv.leave };
    });
    const center = e => {
      const rc = e.currentTarget.getBoundingClientRect(), sc2 = rc.width / W, px = (e.clientX - rc.left) / sc2;
      const t = D.DAY0 + (px - x0) / (x1 - x0) * (D.DAY1 - D.DAY0), s2 = this._st(), span = s2.v1 - s2.v0;
      let v0 = t - span / 2; v0 = Math.min(Math.max(v0, D.DAY0 - 30), D.DAY1 + 30 - span);
      this.setState({ v0, v1: v0 + span });
    };
    return { spark, segs, fx: Math.round(nx(Math.max(st.v0, D.DAY0 - 30))), fw: Math.max(6, Math.round(nx(Math.min(st.v1, D.DAY1 + 30)) - nx(Math.max(st.v0, D.DAY0 - 30)))), nowx: Math.round(nx(D.NOW)), mx: sc.live ? -10 : Math.round(nx(sc.obs)), click: center };
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), K = this._C();
    const sc = this._scene(cfg, st), m = this._mouse(), xs = cfg.PW;
    const tb = this._toolbar(sc, st), P = this._panelB(sc), bot = this._bottom(sc, 1920, 168), nav = this._nav(sc, st), band = this._band(sc, st);
    const anchors = sc.tags.filter(t => Math.abs(t.ty - t.y) > 1.5).map(t => ({ x: xs, y: Math.round(t.y), bg: t.kind === 'dr' ? K.white : '#9BA1AC' }));
    const conf = sc.A.conf ? (sc.A.side === 1 ? '↑ ' : '↓ ') + this._clk(sc.A.conf) : '';
    const side = sc.A.side || 1, xNow = Math.max(0, Math.round(sc.X(sc.obs)));
    // continuation: soft green cloud (blurred cells) under crisp iso-lines
    const cloud = sc.cells.filter(c => c.kind === 'max').map(c => ({ x: c.x - xNow - 1, y: c.y - 1, w: c.w + 2, h: c.h + 2, bg: this._a(K.ext, Math.round((0.16 + 0.62 * c.f) * 100) / 100) }));
    // pullback: red triangles, one per dense cell
    const tris = sc.cells.filter(c => c.kind === 'min').map(c => this._tri(c.R, c.f, side, c.bd !== 'none'));
    const hits = sc.cells.map(c => ({ x: c.x, y: c.y, w: c.w, h: c.h, bd: c.bd === 'none' || c.kind === 'min' ? '1px solid transparent' : '1.5px solid #FFFFFF', enter: c.enter, leave: c.leave, click: c.click }));
    const pickTri = sc.picks.filter(q => q.kind === 'min').map(q => this._tri({ x0: q.x, x1: q.x + q.w, y0: q.y, y1: q.y + q.h }, q.f, side, true));
    const pickBox = sc.picks.filter(q => q.kind === 'max').map(q => ({ x: q.x, y: q.y, w: q.w, h: q.h, bg: q.bg }));
    const cr = st.layers.rclust && sc.ov ? this._contours(sc, 'min') : ['', '', ''], ce = st.layers.eclust && sc.ov ? this._contours(sc, 'max') : ['', '', ''];
    // zone marks: a small rank and a quiet share; the details only under the pointer
    const zl = sc.zones.map(z => {
      const on = sc.hk === z.key;
      const lx = z.R.x1 + 58 > cfg.PW ? Math.round(z.R.x0) - (on ? 150 : 58) : Math.round(z.R.x1) + 4;
      return { x: lx, y: Math.round(z.R.y0 + (z.R.y1 - z.R.y0) / 2) - 8, t: String(z.z.rank), pct: this._pct(z.z.pct), when: on ? this._clk(Math.max(z.z.t, sc.obs)) + '–' + this._clk(z.z.t_hi) : '', wd: on ? 'inline' : 'none',
        bg: z.hue, pc: on ? '#FFFFFF' : '#8F939E', box: on ? 'block' : 'none', bx: z.x, by: z.y, bw: z.w, bh: z.h, bb: '1.5px solid ' + z.hue, enter: z.enter, leave: z.leave, click: z.click };
    });
    zl.sort((a, b) => a.y - b.y);
    for (let i = 1; i < zl.length; i++) for (let j = 0; j < i; j++) if (Math.abs(zl[i].x - zl[j].x) < 56 && Math.abs(zl[i].y - zl[j].y) < 17) zl[i].y = zl[j].y + 17;
    return {
      tb, P, bot, nav, m, sb: this._scrub(), band: band.bars, bandMark: band.mark, chartRef: this._refCb(), cursor: st.drag ? 'grabbing' : 'crosshair',
      boxes: sc.boxes, grid: sc.grid, gridT: sc.gridT, lines: sc.lines, lhits: sc.lhits, zlab: zl, xNow, cloudW: Math.max(0, cfg.PW - xNow), cloud, tris, hits, pickTri, pickBox,
      cr0: cr[0], ce0: ce[0], ce1: ce[1], ce2: ce[2],
      picks: [], wicks: sc.wicks, bodies: sc.bodies, chits: sc.chits, pills: sc.pills, vlines: sc.vlines, glines: sc.glines, xh: sc.xh,
      ticks: sc.ticks, tags: this._tagBoxes(sc, xs, st.layers.ladder ? 'muted' : false), anchors,
      tlabels: sc.tlabels, ttags: sc.ttags, slabels: sc.slabels, lg: sc.legend, act: sc.act, conf, confBg: sc.A.side === 1 ? K.up : K.dn, confShow: conf ? 'inline-flex' : 'none',
      hasFan: !!sc.fan, fanArea: sc.fan ? sc.fan.area : 'M0,0', fanMid: sc.fan ? sc.fan.mid : 'M0,0',
      priceLine: sc.priceLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent', op: 0 }, touchLine: sc.touchLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent' },
      zoomIn: () => this._zoomBtn(-1), zoomOut: () => this._zoomBtn(1), reset: () => this._reset(), replay: !sc.live, live: sc.live
    };
  }
