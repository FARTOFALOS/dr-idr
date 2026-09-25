  // ================= variant A · Терминал =================
  _cfg() { return { W: 1568, H: 788, PW: 1372, PH: 760, ladderW: 88, scaleW: 108, axisH: 28 }; }
  _panelA(sc) {
    const K = this._C(), A = sc.A, ov = sc.ov, hk = sc.hk, f = this._facts(sc), G = sc.guide;
    const row = (key, label, value) => { const hv = key ? this._hv(key) : {}; return { label, value, bg: key && hk === key ? K.hover : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click, cur: key ? 'pointer' : 'default' }; };
    const P = { f, rows: [], zmin: [], zmax: [], lv: [], showZ: false, showN: 'none', days: this._days(sc) };
    if (f.status === 'confirmed') {
      P.rows.push(row('conf|' + sc.act, 'Подтверждение', f.conf), row('price', f.priceLabel, f.price));
      const zr = (kind, z) => {
        const key = 'zone|' + kind + '|' + z.rank, hv = this._hv(key), hue = kind === 'min' ? K.retr : K.ext;
        const soft = G && G.kind === kind && G.zone && G.zone.rank === z.rank && hk !== key;
        const a = A.price(z.lo), b = A.price(z.hi);
        return {
          rank: String(z.rank), hue, time: this._clk(Math.max(z.t, sc.obs)) + '–' + this._clk(z.t_hi), price: this._px(Math.min(a, b)) + '–' + this._px(Math.max(a, b)), pct: this._pct(z.pct),
          bg: hk === key ? this._a(hue, 0.16) : soft ? this._a(hue, 0.08) : 'transparent', bd: hk === key ? '1px solid ' + this._a(hue, 0.7) : '1px solid transparent',
          enter: hv.enter, leave: hv.leave, click: hv.click
        };
      };
      P.zmin = ov.zonesMin.map(z => zr('min', z)); P.zmax = ov.zonesMax.map(z => zr('max', z)); P.showZ = true; P.showN = 'flex';
    } else if (f.status === 'done') {
      P.rows.push(row('conf|' + sc.act, 'Подтверждение', f.conf), row(null, 'Откат', f.retr), row(null, 'Расширение', f.ext));
    } else if (f.status === 'waiting') {
      for (const [a, b] of f.pending) P.rows.push(row(null, a, b));
    }
    if (f.dr) {
      const lr = (id, label, value) => { const key = 'lvl|' + sc.act + '|' + id, hv = this._hv(key), on = hk === key || (hk && hk.startsWith('lvl|' + sc.act + '|' + id)); return { label, value, bg: on ? K.hover : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click }; };
      P.lv.push(lr('dr', 'DR', f.dr), lr('idr', 'IDR', f.idr));
    }
    return P;
  }
  _cardA(sc, st) {
    const K = this._C(), ov = sc.ov, cfg = this._cfg();
    const none = { show: false, x: 0, y: 0, hue: K.retr, what: '', pct: '', time: '', price: '', scale: '', count: '', rank: '', rd: 'none', close: () => {} };
    if (!ov || !st.pick) return none;
    const it = sc.cells.find(c => c.key === st.pick) || sc.zones.find(z => z.key === st.pick);
    if (!it) return none;
    const kind = it.kind, hue = kind === 'min' ? K.retr : K.ext, R = it.R, A = sc.A;
    const d = it.z && st.pick.startsWith('zone') ? it.z : it.c;
    const lo = d.lo, hi = d.hi != null ? d.hi : d.lo + 0.1, t0 = Math.max(d.t, sc.obs), t1 = d.t_hi != null ? d.t_hi : d.t + 15;
    const a = A.price(lo), b = A.price(hi);
    const W = 236, Hc = 166;
    let x = R.x0 - 14 - W; if (x < 8) x = R.x1 + 14; x = Math.min(x, cfg.PW - W - 6);
    const y = Math.min(Math.max(R.y0 - 12, 8), cfg.PH - Hc - 8);
    return {
      show: true, x: Math.round(x), y: Math.round(y), hue, what: kind === 'min' ? 'Откат закончится' : 'Экстремум',
      pct: this._pct(d.pct != null ? d.pct : 100 * d.n / ov.n), time: this._clk(t0) + '–' + this._clk(t1),
      price: this._px(Math.min(a, b)) + ' – ' + this._px(Math.max(a, b)), scale: this._sg(lo, 1) + '…' + this._sg(hi, 1) + ' IDR',
      count: d.n + ' из ' + ov.n, rank: d.rank ? String(d.rank) : '', rd: d.rank ? 'flex' : 'none',
      close: e => { if (e && e.stopPropagation) e.stopPropagation(); this.setState({ pick: null }); }
    };
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), K = this._C();
    const sc = this._scene(cfg, st), m = this._mouse(), xs = cfg.PW + cfg.ladderW;
    const tb = this._toolbar(sc, st), P = this._panelA(sc), card = this._cardA(sc, st), bot = this._bottom(sc, 1920, 168);
    const anchors = sc.tags.filter(t => Math.abs(t.ty - t.y) > 1.5).map(t => ({ x: xs, y: Math.round(t.y), bg: t.kind === 'dr' ? K.white : '#9BA1AC' }));
    const conf = sc.A.conf ? (sc.A.side === 1 ? '↑ ' : '↓ ') + this._clk(sc.A.conf) : '';
    return {
      tb, P, card, bot, m, chartRef: this._refCb(), cursor: st.drag ? 'grabbing' : 'crosshair',
      boxes: sc.boxes, grid: sc.grid, gridT: sc.gridT, lines: sc.lines, lhits: sc.lhits, cells: sc.cells, zones: sc.zones, badges: sc.badges,
      picks: sc.picks, wicks: sc.wicks, bodies: sc.bodies, chits: sc.chits, pills: sc.pills, vlines: sc.vlines, glines: sc.glines, xh: sc.xh,
      ladder: sc.ladder, ladderT: sc.ladderT, ladderOn: st.layers.ladder && !!sc.ov, ticks: sc.ticks, tags: this._tagBoxes(sc, xs, false), anchors,
      tlabels: sc.tlabels, ttags: sc.ttags, slabels: sc.slabels, lg: sc.legend, act: sc.act, conf, confBg: sc.A.side === 1 ? K.up : K.dn, confShow: conf ? 'inline-flex' : 'none',
      hasFan: !!sc.fan, fanArea: sc.fan ? sc.fan.area : 'M0,0', fanMid: sc.fan ? sc.fan.mid : 'M0,0',
      priceLine: sc.priceLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent', op: 0 }, touchLine: sc.touchLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent' },
      zoomIn: () => this._zoomBtn(-1), zoomOut: () => this._zoomBtn(1), reset: () => this._reset(),
      replay: !sc.live, live: sc.live
    };
  }
