  // ================= variant 1 · «Кластеры на графике»: the chart takes the whole width; each dense zone carries its
  // share and time next to it; details in a small card under the pointer (click pins it) =================
  _cfg() { return { W: 1920, H: 910, PW: 1788, PH: 852, scaleW: 132, axisH: 28, bandH: 30 }; }
  _zoneLabels(sc) {
    const cfg = this._cfg(), T = sc.target, out = [];
    for (const z of sc.blobs) {
      const on = z.on || (T && T.K === z.kd && T.blob && T.blob.rank === z.b.rank);
      const wEst = 134, R = z.R;
      let x = Math.round(R.x1) + 6, y = Math.round(z.py) - 9;
      if (x + wEst > cfg.PW - 4) { x = Math.round(Math.max(R.x0, R.x1 - wEst)); y = Math.round(R.y0) - 20; if (y < 4) y = Math.round(R.y1) + 4; }
      x = Math.min(Math.max(4, x), cfg.PW - wEst - 4); y = Math.min(Math.max(4, y), cfg.PH - 22);
      out.push({ x, y, pct: this._pct(z.b.pct), when: this._clk(Math.max(z.b.t0, sc.obs)) + '–' + this._clk(z.b.t1),
        pc: on ? '#FFFFFF' : '#D1D4DC', wc: on ? '#E6E8EE' : '#8F939E', fw: z.b.rank === 1 ? 700 : 600, hue: z.hue,
        clip: z.kd.shape === 'tri' ? (z.kd.point === 'down' ? 'polygon(0% 0%, 100% 0%, 50% 100%)' : 'polygon(50% 0%, 100% 100%, 0% 100%)') : 'none', rad: z.kd.shape === 'tri' ? '0px' : '2px',
        ic: z.kd.id === 'up' || z.kd.id === 'dn' ? 'none' : 'inline-block', ar: z.kd.id === 'up' ? '↑' : z.kd.id === 'dn' ? '↓' : '', ard: z.kd.id === 'up' || z.kd.id === 'dn' ? 'inline' : 'none',
        enter: z.enter, leave: z.leave, click: z.click });
    }
    out.sort((a, b) => a.y - b.y);
    for (let i = 1; i < out.length; i++) for (let j = 0; j < i; j++) if (Math.abs(out[i].x - out[j].x) < 130 && Math.abs(out[i].y - out[j].y) < 19) out[i].y = out[j].y + 19;
    return out;
  }
  // the detail card beside the object (never on top of it)
  _card(sc, st) {
    const cfg = this._cfg(), d = this._detail(sc), G = sc.guide;
    const none = { show: false, x: 0, y: 0, title: '', hue: '#D1D4DC', big: '', bigShow: 'none', sub: '', rows: [], cond: '', pin: 'none', pe: 'none', close: () => {} };
    if (!d || !G) return none;
    const w = 262, h = 92 + d.rows.length * 22;
    let x = G.noTime ? cfg.PW - w - 14 : G.R.x0 - w - 14;
    if (x < 8) x = G.R.x1 + 14;
    x = Math.min(Math.max(8, x), cfg.PW - w - 8);
    let y = G.noPrice ? 48 : G.R.y0 - 10; y = Math.min(Math.max(48, y), cfg.PH - h - 8);
    const pinned = !!st.pick && st.pick === sc.hk;
    return { show: true, x: Math.round(x), y: Math.round(y), title: d.title, hue: d.hue, big: d.big, bigShow: d.big ? 'block' : 'none', sub: d.sub, rows: d.rows.map(r => ({ l: r[0], v: r[1] })), cond: d.cond,
      pin: pinned ? 'flex' : 'none', pe: pinned ? 'auto' : 'none', close: () => this.setState({ pick: null, hover: null }) };
  }
  // one quiet line of facts under the legend
  _stateLine(sc) {
    const A = sc.A, f = this._facts(sc), get = l => (f.find(r => r[0] === l) || [])[1];
    if (A.status === 'waiting') { const d = this._dir(sc); return 'Подтверждение позже: ' + d.line + ' · до конца ' + get('До конца'); }
    if (A.status === 'broken') return 'После слома взято: ' + get('После слома взято') + ' · до конца ' + get('До конца');
    if (A.status === 'confirmed') return 'Взято: ' + get('Взято') + (get('Откат пока') ? ' · откат ' + get('Откат пока') : '') + ' · до конца ' + get('До конца');
    return '';
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), sc = this._scene(cfg, st), C = this._common(sc, st);
    const band = this._band(sc, st, cfg.bandH, false), line = this._stateLine(sc);
    return Object.assign(C, {
      zlab: this._zoneLabels(sc), card: this._card(sc, st), sb: this._scrub(), band: band.bars, bandMark: band.mark,
      nav: this._nav(sc, st, 1920), stateLine: line, hasState: !!line, dkey: this._dkey()
    });
  }
