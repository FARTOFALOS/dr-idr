  // ================= variant C · Чистый график =================
  _cfg() { return { W: 1920, H: 952, PW: 1650, PH: 880, ladderW: 124, scaleW: 146, axisH: 28, noLadder: true }; }
  _hud(sc) {
    const K = this._C(), A = sc.A, ov = sc.ov, f = this._facts(sc), hk = sc.hk, chips = [];
    const chip = (key, t, v, col, tip) => { const hv = key ? this._hv(key) : {}; chips.push({ t, v, col: col || '#E6E8EE', tip: tip || '', bg: key && hk === key ? '#232833' : '#161A21', bd: key && hk === key ? '1px solid #3A404C' : '1px solid #20252E', enter: hv.enter, leave: hv.leave, click: hv.click, cur: key ? 'pointer' : 'default' }); };
    if (f.status === 'confirmed') {
      chip('lvl|' + sc.act + '|' + (A.side === 1 ? 'drL' : 'drH'), f.bigLabel, f.big, f.bigCol, 'Слом DR: закрытие M5 ' + (A.side === 1 ? 'ниже ' : 'выше ') + this._px(A.opp));
      chip('conf|' + sc.act, 'Подтверждение', f.conf, A.side === 1 ? K.up : K.dn);
      chip('price', f.priceLabel, this._sg(A.nowCoord, 2) + ' IDR');
      chip(null, 'Похожих', String(ov.n), '#E6E8EE', f.ntip);
    } else if (f.status === 'done') {
      chip('conf|' + sc.act, 'Подтверждение', f.conf, A.side === 1 ? K.up : K.dn);
      chip(null, 'Итог', f.big, f.bigCol);
      chip(null, 'Откат', f.retr); chip(null, 'Расширение', f.ext);
    } else chip(null, f.bigLabel || sc.act, f.big, f.bigCol);
    return chips;
  }
  // distributions glued to the axes: where (price column at the scale) and when (band above the time axis)
  _profiles(sc, st) {
    const K = this._C(), ov = sc.ov, A = sc.A, cfg = this._cfg(), hk = sc.hk, hp = sc.hp, G = sc.guide;
    const res = { pbars: [], tbars: [], pT: [], show: !!ov };
    if (!ov) return res;
    const L = st.layers, x1 = cfg.PW + cfg.ladderW - 4, maxW = cfg.ladderW - 34;
    const on = (chart, lo, stp) => {
      if (hp[0] === 'bin' && hp[1] === chart) return Math.abs(+hp[2] - lo) < 1e-6;
      if (!G) return false;
      const kindOk = (chart === 'retr' || chart === 'rtime') ? G.kind === 'min' : G.kind === 'max';
      if (!kindOk) return false;
      return (chart === 'retr' || chart === 'ext') ? lo + stp > G.lo + 1e-6 && lo < G.hi - 1e-6 : lo + stp > G.t0 && lo < G.t1;
    };
    for (const chart of ['retr', 'ext']) {
      if (chart === 'retr' ? !L.rclust : !L.eclust) continue;
      const H = ov.H[chart], hue = chart === 'retr' ? K.retr : K.ext, mx = Math.max(1, ...H.co);
      let any = false;
      for (let j = 0; j < H.nb; j++) if (H.co[j] && on(chart, Math.round((H.lo + j * H.st) * 10) / 10, H.st)) any = true;
      for (let j = 0; j < H.nb; j++) {
        if (!H.co[j]) continue;
        const lo = Math.round((H.lo + j * H.st) * 10) / 10, ya = sc.Y(A.price(lo)), yb = sc.Y(A.price(lo + H.st));
        const y0 = Math.min(ya, yb), y1 = Math.max(ya, yb);
        if (y1 < 0 || y0 > cfg.PH) continue;
        const w = Math.max(2, Math.round(maxW * H.co[j] / mx)), key = 'bin|' + chart + '|' + lo.toFixed(1), hv = this._hv(key), lit = on(chart, lo, H.st);
        res.pbars.push({ x: x1 - w, lx: x1 - w - cfg.PW, y: Math.round(y0) + 1, w, h: Math.max(1, Math.round(y1 - y0) - 1), bg: this._a(hue, lit ? 1 : any ? 0.3 : 0.62), hx: cfg.PW, hw: cfg.ladderW, enter: hv.enter, leave: hv.leave, click: hv.click });
      }
    }
    // time: extension up from the middle line, retracement down from it
    const mid = cfg.PH + 22;
    for (const chart of ['rtime', 'etime']) {
      if (chart === 'rtime' ? !L.rclust : !L.eclust) continue;
      const H = ov.H[chart], hue = chart === 'rtime' ? K.retr : K.ext, mx = Math.max(1, ...H.co);
      let any = false;
      for (let j = 0; j < H.nb; j++) if (H.co[j] && on(chart, H.lo + j * H.st, H.st)) any = true;
      for (let j = 0; j < H.nb; j++) {
        const t = H.lo + j * H.st, xa = sc.X(Math.max(t, sc.obs)), xb = sc.X(t + H.st);
        if (xb <= 0 || xa >= cfg.PW || xb - xa < 1) continue;
        const hgt = Math.max(H.co[j] ? 2 : 0, Math.round(20 * Math.sqrt(H.co[j] / mx))), key = 'bin|' + chart + '|' + t, hv = this._hv(key), lit = on(chart, t, H.st);
        res.tbars.push({ x: Math.round(xa) + 1, w: Math.max(1, Math.round(xb - xa) - 2), y: chart === 'rtime' ? mid + 1 : mid - hgt, ry: chart === 'rtime' ? 1 : 22 - hgt, h: hgt, bg: this._a(hue, lit ? 1 : any ? 0.3 : 0.7), hy: chart === 'rtime' ? mid : mid - 22, enter: hv.enter, leave: hv.leave, click: hv.click });
      }
    }
    return res;
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), K = this._C();
    const sc = this._scene(cfg, st), m = this._mouse(), xs = cfg.PW + cfg.ladderW;
    const tb = this._toolbar(sc, st), hud = this._hud(sc), pr = this._profiles(sc, st);
    const anchors = sc.tags.filter(t => Math.abs(t.ty - t.y) > 1.5).map(t => ({ x: xs, y: Math.round(t.y), bg: t.kind === 'dr' ? K.white : '#9BA1AC' }));
    const conf = sc.A.conf ? (sc.A.side === 1 ? '↑ ' : '↓ ') + this._clk(sc.A.conf) : '';
    // zones with their labels on the chart: rank, share and time window, readable without a side list
    const zl = sc.zones.map(z => {
      const on = sc.hk === z.key, a = sc.A.price(z.z.lo), b = sc.A.price(z.z.hi);
      return { x: z.x, y: z.y - 22, t: String(z.z.rank), pct: this._pct(z.z.pct), when: this._clk(Math.max(z.z.t, sc.obs)) + '–' + this._clk(z.z.t_hi), px: on ? this._px(Math.min(a, b)) + ' – ' + this._px(Math.max(a, b)) + ' · ' + z.z.n + ' из ' + sc.ov.n : '', pxd: on ? 'inline' : 'none',
        bg: z.hue, pbg: on ? '#1E2430' : 'rgba(11,13,16,0.9)', bd: on ? '1px solid ' + z.hue : '1px solid ' + this._a(z.hue, 0.45),
        bx: z.x, by: z.y, bw: z.w, bh: z.h, bb: z.bd, bf: on ? this._a(z.hue, 0.2) : this._a(z.hue, z.z.rank === 1 ? 0.12 : 0.07), enter: z.enter, leave: z.leave, click: z.click };
    });
    zl.sort((a, b) => a.y - b.y || a.x - b.x);
    for (let i = 1; i < zl.length; i++) for (let j = 0; j < i; j++) if (Math.abs(zl[i].x - zl[j].x) < 150 && Math.abs(zl[i].y - zl[j].y) < 22) zl[i].y = zl[j].y + 22;
    return {
      tb, hud, pr, m, chartRef: this._refCb(), cursor: st.drag ? 'grabbing' : 'crosshair',
      boxes: sc.boxes, grid: sc.grid, gridT: sc.gridT, lines: sc.lines, lhits: sc.lhits, zlab: zl,
      picks: sc.picks, wicks: sc.wicks, bodies: sc.bodies, chits: sc.chits, pills: sc.pills, vlines: sc.vlines, glines: sc.glines, xh: sc.xh,
      ticks: sc.ticks, tags: this._tagBoxes(sc, xs, st.layers.ladder), anchors,
      tlabels: sc.tlabels, ttags: sc.ttags, slabels: sc.slabels, lg: sc.legend, act: sc.act, conf, confBg: sc.A.side === 1 ? K.up : K.dn, confShow: conf ? 'inline-flex' : 'none',
      hasFan: !!sc.fan, fanArea: sc.fan ? sc.fan.area : 'M0,0', fanMid: sc.fan ? sc.fan.mid : 'M0,0',
      priceLine: sc.priceLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent', op: 0 }, touchLine: sc.touchLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent' },
      zoomIn: () => this._zoomBtn(-1), zoomOut: () => this._zoomBtn(1), reset: () => this._reset(), replay: !sc.live, live: sc.live
    };
  }
