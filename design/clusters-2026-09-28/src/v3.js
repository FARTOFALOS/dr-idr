  // ================= variant 3 · «Проекции»: the clusters on the chart without numbers; the same extremes laid out as bars
  // along the price scale (where) and along the time axis (when); a card under the pointer =================
  _cfg() { return { W: 1920, H: 910, PW: 1676, PH: 818, projW: 112, scaleW: 132, axisH: 28, bandH: 64 }; }
  // where: one bar per 0.1 IDR of price, per kind; the three largest bars of each kind carry their share
  _proj(sc, st) {
    const cfg = this._cfg(), ov = sc.ov, T = sc.target, hk = sc.hk, bars = [], texts = [];
    if (!ov) return { bars, texts };
    const x0 = cfg.PW + 6, maxLen = 64;
    for (const kd of ov.kinds) {
      if (!st.layers[kd.layer]) continue;
      const mx = Math.max(1, ...kd.pbins.map(b => b.n)), top = kd.pbins.slice().sort((a, b) => b.n - a.n).slice(0, 3);
      for (const b of kd.pbins) {
        const y0 = sc.Y(b.pHi), y1 = sc.Y(b.pLo);
        if (y1 < 0 || y0 > cfg.PH) continue;
        const key = 'pbin|' + kd.id + '|' + b.pLo, hv = this._hv(key), on = hk === key;
        const lit = on || (T && T.K === kd && T.what !== 'pbin' && !T.noPrice && b.pHi > T.pLo + 1e-6 && b.pLo < T.pHi - 1e-6);
        const len = Math.max(2, Math.round(maxLen * b.n / mx)), h = Math.max(2, Math.round(y1 - y0) - 1);
        bars.push({ x: x0, y: Math.round(y0), w: len, h, bg: this._a(kd.hue, on ? 1 : lit ? 0.95 : 0.62), hx: cfg.PW, hw: cfg.projW, enter: hv.enter, leave: hv.leave, click: hv.click });
        if (top.includes(b)) texts.push({ x: x0 + len + 4, y: Math.round((y0 + y1) / 2) - 7, t: this._pct(b.pct), c: on || lit ? '#FFFFFF' : '#9AA1AD' });
      }
    }
    texts.sort((a, b) => a.y - b.y);
    for (let i = 1; i < texts.length; i++) if (texts[i].y - texts[i - 1].y < 14) texts[i].y = texts[i - 1].y + 14;
    return { bars, texts };
  }
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
  _stateLine(sc) {
    const A = sc.A, f = this._facts(sc), get = l => (f.find(r => r[0] === l) || [])[1];
    if (A.status === 'waiting') { const d = this._dir(sc); return 'Подтверждение позже: ' + d.line + ' · до конца ' + get('До конца'); }
    if (A.status === 'broken') return 'После слома взято: ' + get('После слома взято') + ' · до конца ' + get('До конца');
    if (A.status === 'confirmed') return 'Взято: ' + get('Взято') + (get('Откат пока') ? ' · откат ' + get('Откат пока') : '') + ' · до конца ' + get('До конца');
    return '';
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), sc = this._scene(cfg, st), C = this._common(sc, st);
    const band = this._band(sc, st, cfg.bandH, true), pj = this._proj(sc, st), line = this._stateLine(sc);
    return Object.assign(C, {
      card: this._card(sc, st), sb: this._scrub(), band: band.bars, bandT: band.texts, bandMark: band.mark, bandMid: band.mid,
      pbars: pj.bars, ptexts: pj.texts, nav: this._nav(sc, st, 1920), stateLine: line, hasState: !!line
    });
  }
