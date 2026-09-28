  // ================= variant 2 · «График + сводка»: the same clusters on the chart (only a small rank beside each zone);
  // a column on the right: what the day and the session have done, and the dense zones as rows linked to the chart =================
  _cfg() { return { W: 1540, H: 910, PW: 1408, PH: 852, scaleW: 132, axisH: 28, bandH: 30 }; }
  _ranks(sc) {
    const T = sc.target, out = [];
    for (const z of sc.blobs) {
      const on = z.on || (T && T.K === z.kd && T.blob && T.blob.rank === z.b.rank);
      out.push({ x: Math.round(z.px) + 10, y: Math.round(z.py) - 7, t: String(z.b.rank), c: on ? '#FFFFFF' : '#E6E8EE', op: on ? 1 : 0.85, enter: z.enter, leave: z.leave, click: z.click });
    }
    out.sort((a, b) => a.y - b.y);
    for (let i = 1; i < out.length; i++) for (let j = 0; j < i; j++) if (Math.abs(out[i].x - out[j].x) < 14 && Math.abs(out[i].y - out[j].y) < 15) out[i].y = out[j].y + 15;
    return out;
  }
  _panel(sc, st) {
    const D = this._D(), A = sc.A, ov = sc.ov, d = this._detail(sc), dir = this._dir(sc), md = this._models(sc.act, sc.obs);
    const head = sc.act + (sc.live ? ' · сейчас ' + this._clk(D.NOW) : ' · на ' + this._clk(sc.obs));
    let ins;
    if (d) ins = { title: d.title, hue: d.hue, big: d.big, line: d.rows.map(r => r[0] + ' ' + r[1]).join(' · '), line2: d.sub };
    else {
      const chips = this._chips(sc).map(c => c.t).join(' · ');
      ins = { title: head, hue: '#D1D4DC', big: '', line: chips + (A.priceNow != null ? ' · цена ' + this._px(A.priceNow) : ''), line2: ov ? ov.N + ' похожих сессий' : '' };
    }
    ins.bigShow = ins.big ? 'inline' : 'none';
    return {
      ins, days: this._dayRows(sc), widths: this._widths(sc), md: md || { prev: '—', up: '—', dn: '—' },
      sessHdr: 'СЕССИЯ ' + sc.act, facts: this._facts(sc).map(r => ({ l: r[0], v: r[1] })),
      hasDir: !!dir, dir: dir || { up: '', dn: '', none: '', wu: 0, wd: 0, wn: 0, line: '', n: '' },
      groups: this._groups(sc), foot: ov ? ov.N + ' похожих · ' + ov.cond : ''
    };
  }
  renderVals() {
    const st = this._st(), cfg = this._cfg(), sc = this._scene(cfg, st), C = this._common(sc, st);
    const band = this._band(sc, st, cfg.bandH, false);
    return Object.assign(C, { ranks: this._ranks(sc), P: this._panel(sc, st), sb: this._scrub(), band: band.bars, bandMark: band.mark, nav: this._nav(sc, st, 1540) });
  }
