  // ================= shared view pieces (toolbar, day strip, scrub band, the facts in words, the detail card) =================
  _toolbar(sc, st) {
    const K = this._C(), D = this._D();
    const inst = ['NQ', 'ES', 'YM'].map(t => ({ t, bg: t === 'NQ' ? '#2A2E39' : 'transparent', c: t === 'NQ' ? '#FFFFFF' : K.text2 }));
    const sess = D.ORDER.map(k => {
      const s = sc.S[k], on = k === sc.act, hv = this._hv('sess|' + k);
      const running = k === 'RDR' && (s.status === 'confirmed' || s.status === 'broken') && sc.live;
      return {
        t: k, bg: on ? '#2A2E39' : 'transparent', c: on ? '#FFFFFF' : K.text2,
        dot: running ? K.up : s.status === 'done' ? (s.failed ? K.dn : '#6B7280') : 'transparent',
        click: () => this._selSession(k), enter: hv.enter, leave: hv.leave
      };
    });
    const scenes = [['conf', 'Подтверждено'], ['wait', 'До подтверждения'], ['brk', 'Слом DR']].map(([id, t]) => ({ t, bg: st.scene === id ? '#2A2E39' : 'transparent', c: st.scene === id ? '#FFFFFF' : K.text2, click: () => this._setScene(id) }));
    const L = st.layers, wait = sc.ov && sc.ov.mode === 'wait';
    const tri = sc.playSide === -1 ? 'polygon(50% 0%, 100% 100%, 0% 100%)' : 'polygon(0% 0%, 100% 0%, 50% 100%)';
    const defs = wait
      ? [{ k: 'cont', t: 'Верх', sw: K.neu, clip: 'none' }, { k: 'pull', t: 'Низ', sw: K.neu, clip: 'none' }]
      : [{ k: 'pull', t: 'Откат', sw: K.pull, clip: tri }, { k: 'cont', t: 'Продолжение', sw: K.cont, clip: 'none' }];
    defs.push({ k: 'struct', t: 'Структура дня', sw: '#CBD5E1', clip: 'none' });
    const layers = defs.map(l => ({ t: l.t, sw: l.sw, clip: l.clip, bg: L[l.k] ? '#1F242D' : 'transparent', c: L[l.k] ? K.text : '#8F939E', bd: L[l.k] ? '1px solid #3A404C' : '1px solid #252A33', swop: L[l.k] ? 1 : 0.35, click: () => this._toggleLayer(l.k) }));
    return {
      inst, sess, scenes, layers, live: sc.live, replay: !sc.live, date: D.date,
      clock: this._clk(D.NOW) + ' ET', rpText: sc.act + ' · ' + this._clk(sc.obs), toLive: () => this._live()
    };
  }
  // the whole trading day as a strip: session segments, closes, the visible window, now and the replay moment
  _nav(sc, st, W) {
    const K = this._C(), D = this._D(), x0 = 12, x1 = W - 12;
    const nx = t => x0 + (t - D.DAY0) / (D.DAY1 - D.DAY0) * (x1 - x0);
    const closes = D.bars.map(b => b.c), lo = Math.min(...closes), hi = Math.max(...closes);
    const ny = v => 19 + (hi - v) / (hi - lo) * 22;
    const spark = D.bars.map((b, i) => (i ? 'L' : 'M') + nx(b.t + 2.5).toFixed(1) + ',' + ny(b.c).toFixed(1)).join('');
    const segs = D.ORDER.map(k => {
      const s = sc.S[k], on = k === sc.act, hv = this._hv('sess|' + k), hl = sc.hk === 'sess|' + k;
      const sub = (s.conf ? (s.side === 1 ? '↑ ' : '↓ ') + this._clk(s.conf) : '') + (s.failed ? ' · слом ' + this._clk(s.failed) : s.status === 'done' ? ' · DR удержался' : s.status === 'confirmed' && sc.live ? ' · идёт' : '');
      return { x: Math.round(nx(s.start)), w: Math.round(nx(s.end) - nx(s.start)), wx: Math.round(nx(s.start)), ww: Math.max(2, Math.round(nx(s.formed) - nx(s.start))),
        bg: on ? 'rgba(209,212,220,0.09)' : hl ? 'rgba(209,212,220,0.07)' : 'rgba(209,212,220,0.035)', bd: on ? '1px solid rgba(209,212,220,0.35)' : '1px solid transparent',
        t: k, sub, c: on ? '#FFFFFF' : K.text2,
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
  // the band above the time axis: over the past it shows the screen as of that close, over the future it lights that column
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
        if (at <= D.NOW) {
          const k = this._sessIn(at);
          if (k) { if (!s.scrub || s.scrub.at !== at || s.scrub.sess !== k || s.hover) this.setState({ scrub: { sess: k, at }, hover: null }); }
          else if (s.scrub || s.hover) this.setState({ scrub: null, hover: null });
        } else {
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
  // when the extremes happened (15-minute bins): continuation / upper up, pullback / lower down
  _band(sc, st, H, withPct) {
    const K = this._C(), ov = sc.ov, cfg = this._cfg(), T = sc.target, bars = [], texts = [], mid = Math.round(H / 2);
    const mark = { x: -10, bg: 'transparent' };
    if (st.scrub) { mark.x = Math.round(sc.X(st.scrub.at)); mark.bg = K.replay; }
    else if (T && T.what === 'col') { mark.x = Math.round(sc.X(T.t0 + 7.5)); mark.bg = '#D1D4DC'; }
    if (!ov) return { bars, texts, mark, mid };
    const hMax = mid - (withPct ? 16 : 3);
    for (const kd of ov.kinds) {
      if (!st.layers[kd.layer]) continue;
      const upw = kd.id === 'cont' || kd.id === 'up', mx = Math.max(1, ...kd.tbins.map(b => b.n));
      const top = kd.tbins.slice().sort((a, b) => b.n - a.n).slice(0, 2).map(b => b.t);
      for (const b of kd.tbins) {
        const xa = sc.X(Math.max(b.t, sc.obs)), xb = sc.X(b.tHi);
        if (xb <= 0 || xa >= cfg.PW || xb - xa < 1) continue;
        const h = Math.max(2, Math.round(hMax * Math.sqrt(b.n / mx)));
        const lit = T && T.t1 != null && T.what !== 'pbin' && b.t + 15 > T.t0 && b.t < T.t1 && (T.what === 'col' || !T.K || T.K === kd);
        bars.push({ x: Math.round(xa) + 1, w: Math.max(1, Math.round(xb - xa) - 2), y: upw ? mid - h : mid + 1, h, bg: this._a(kd.hue, lit ? 1 : 0.6) });
        if (withPct && top.includes(b.t) && xb - xa > 26) texts.push({ x: Math.round((xa + xb) / 2), y: upw ? mid - h - 15 : mid + h + 2, t: this._pct(b.pct), c: lit ? '#FFFFFF' : '#9AA1AD' });
      }
    }
    return { bars, texts, mark, mid };
  }
  // what the active session has done, in words (facts only; the numbers of the history come separately)
  _facts(sc) {
    const D = this._D(), A = sc.A, rows = [];
    const box = A.complete ? (A.boxUp ? 'зелёная' : 'красная') + ' · DR ' + this._px(A.drL) + '–' + this._px(A.drH) : 'формируется';
    rows.push(['Коробка', box]);
    const left = Math.max(0, A.end - sc.obs);
    const takenTxt = arr => arr && arr.length ? arr.slice(-2).map(q => q.name + ' в ' + this._clk(q.t)).join(' · ') : 'ещё нет';
    if (A.status === 'waiting') {
      rows.push(['Подтверждение', 'нет к ' + this._clk(sc.obs)]);
      rows.push(['Цена', this._px(A.priceNow) + (A.priceNow >= A.close ? ' · выше закрытия коробки' : ' · ниже закрытия коробки')]);
    } else if (A.conf) {
      rows.push(['Подтверждение', (A.side === 1 ? '↑ ' : '↓ ') + this._clk(A.conf)]);
      if (A.failed) {
        rows.push(['DR', 'Слом DR ' + (A.side === 1 ? '↓ ' : '↑ ') + this._clk(A.failed)]);
        rows.push(['После слома взято', takenTxt(A.takenN)]);
      } else {
        rows.push(['Взято', takenTxt(A.taken)]);
        if (A.retrP != null) rows.push(['Откат пока', 'до ' + this._px(A.retrP) + ' в ' + this._clk(A.retrT)]);
        rows.push(['DR', A.status === 'done' ? 'удержался' : 'цел']);
      }
    }
    if (A.status !== 'done' && A.status !== 'noconf') rows.push(['До конца', this._dur(left)]);
    return rows;
  }
  _dayRows(sc) {
    const D = this._D(), K = this._C();
    return D.ORDER.map(k => {
      const s = sc.S[k], hv = this._hv('sess|' + k), on = k === sc.act;
      const conf = s.conf ? (s.side === 1 ? '↑ ' : '↓ ') + this._clk(s.conf) : '—';
      const stt = s.failed && (s.status === 'broken' || s.status === 'done') ? 'слом DR ' + this._clk(s.failed) : s.status === 'done' ? 'DR удержался' : s.status === 'confirmed' ? (on && !sc.live ? 'на ' + this._clk(sc.obs) : 'идёт') : s.status === 'waiting' ? 'ждёт подтверждения' : s.status === 'forming' ? 'формируется' : s.status === 'noconf' ? 'без подтверждения' : '';
      return { k, conf, st: stt, bg: on ? '#1B2029' : sc.hk === 'sess|' + k ? '#161A21' : 'transparent', c: on ? '#FFFFFF' : K.text2, ac: s.side === 1 ? K.up : s.side === -1 ? K.dn : K.text3, stc: s.failed ? '#F0868A' : K.text3,
        click: () => { if (k !== this._st().session || this._st().rp) this._selSession(k); }, enter: hv.enter, leave: hv.leave };
    });
  }
  _widths(sc) {
    const D = this._D();
    const parts = D.ORDER.filter(k => sc.S[k].width).map(k => k + ' ' + this._num(Math.round(sc.S[k].width), 0));
    return parts.length ? parts.join(' → ') + ' пт' : '';
  }
  // the extreme each kind stands for, in one line (what the share counts)
  _meaning(kd, ov) {
    const end = this._clk(ov.end);
    if (kd.id === 'up') return 'максимум цены до ' + end;
    if (kd.id === 'dn') return 'минимум цены до ' + end;
    if (kd.id === 'pull') return 'самая глубокая точка отката до ' + end;
    return 'самая дальняя точка продолжения до ' + end;
  }
  _role(kd, ov) { return kd.role + (ov.mode === 'brk' ? ' после слома' : ''); }
  // the object under the pointer (or pinned), in words and numbers
  _detail(sc) {
    const T = sc.target, ov = sc.ov; if (!T || !ov) return null;
    if (T.what === 'col') return { title: 'Время ' + this._clk(T.t0) + '–' + this._clk(T.t1), hue: '#D1D4DC', big: '', sub: 'экстремумы в этом отрезке времени',
      rows: T.parts.filter(p => this._st().layers[p.K.layer]).map(p => [this._role(p.K, ov), this._pct(p.pct) + ' · ' + p.n + ' из ' + ov.N]), cond: ov.cond, shape: 'none' };
    const kd = T.K, rows = [];
    rows.push(['Время', T.what === 'pbin' ? 'до ' + this._clk(ov.end) : this._clk(T.t0) + '–' + this._clk(T.t1)]);
    if (!T.noPrice) rows.push(['Цена', this._px(T.pLo) + '–' + this._px(T.pHi)]);
    rows.push(['Сессий', T.n + ' из ' + ov.N]);
    if (T.what === 'cell') rows.push(['Ступень', ['1 · самые частые', '2 · частые', '3 · реже', '4 · единичные'][T.cls - 1]]);
    if (T.what === 'cell' && T.blob) rows.push(['Весь кластер ' + T.blob.rank, this._pct(T.blob.pct)]);
    const what = T.what === 'blob' ? ' · кластер ' + T.rank : T.what === 'cell' ? ' · клетка' : T.what === 'pbin' ? ' · эта цена' : T.what === 'tbin' ? ' · это время' : '';
    return { title: this._role(kd, ov) + what, hue: kd.hue, big: this._pct(T.pct), sub: this._meaning(kd, ov), rows, cond: ov.cond, shape: kd.shape };
  }
  // one row per dense zone, grouped by kind (the side column and the projections use it)
  _groups(sc) {
    const ov = sc.ov, hk = sc.hk, T = sc.target, K = this._C(), st = this._st(); if (!ov) return [];
    return ov.kinds.filter(kd => st.layers[kd.layer]).map(kd => ({
      title: this._role(kd, ov).toUpperCase(), hue: kd.hue, sub: this._meaning(kd, ov),
      clip: kd.shape === 'tri' ? (kd.point === 'down' ? 'polygon(0% 0%, 100% 0%, 50% 100%)' : 'polygon(50% 0%, 100% 100%, 0% 100%)') : 'none', rad: kd.shape === 'tri' ? '0px' : '2px',
      rows: kd.clusters.map(z => {
        const key = 'blob|' + kd.id + '|' + z.rank, hv = this._hv(key), soft = T && T.what === 'cell' && T.K === kd && T.blob && T.blob.rank === z.rank;
        return { rank: String(z.rank), time: this._clk(Math.max(z.t0, sc.obs)) + '–' + this._clk(z.t1), price: this._px(z.pLo) + '–' + this._px(z.pHi), pct: this._pct(z.pct), n: z.n + '/' + ov.N,
          bg: hk === key ? this._a(kd.hue, 0.16) : soft ? this._a(kd.hue, 0.08) : 'transparent', enter: hv.enter, leave: hv.leave, click: hv.click };
      })
    }));
  }
  // the glyphs as svg paths, one path per probability step, and their colours (step 1 full, step 4 faint)
  _dsv(sc, st) {
    const Ly = this._layers(sc, st), T = sc.target, none = 'M0,0';
    const dim = hue => (T && T.K && T.K.hue !== hue ? 0.45 : 1);
    const A = { steps: [1, 0.72, 0.45, 0.22, 0], solid: [1, 0.5, 0, 0.25, 0.9], units: [0.95, 0.6, 0, 0.3, 0], mosaic: [0.72, 0.3, 0, 0.28, 0.5] }[this._dmode()];
    const slot = s => s ? { p0: s.p[0], p1: s.p[1], p2: s.p[2], p3: s.p[3], sp: s.sp, c0: this._a(s.c, A[0]), c1: this._a(s.c, A[1]), c2: this._a(s.c, A[2]), c3: this._a(s.c, A[3]), sc: A[4] ? this._a(s.c, A[4]) : 'none', op: dim(s.c) }
      : { p0: none, p1: none, p2: none, p3: none, sp: none, c0: 'none', c1: 'none', c2: 'none', c3: 'none', sc: 'none', op: 1 };
    return { A: slot(Ly.A), B: slot(Ly.B) };
  }
  // one line that says how the density on this artboard is drawn (the density comparison row only)
  _dkey() {
    return {
      steps: 'Ступени: крупный яркий знак — самые частые клетки · точка — единичные сессии',
      solid: 'Сплошной знак — за ним ≥ 8 сессий · полупрозрачный 4–7 · контур 2–3 · точка — одна · размер — доля',
      units: 'Один маленький знак = 1% похожих сессий · сосчитай знаки в блоке — это доля',
      mosaic: 'Плотная плитка — самые частые клетки · светлая — частые · контур — реже · точка — единичные'
    }[this._dmode()];
  }
  // legend chips of the active session
  _chips(sc) {
    const K = this._C(), A = sc.A, out = [];
    if (A.conf) out.push({ t: (A.side === 1 ? '↑ ' : '↓ ') + this._clk(A.conf), bg: A.side === 1 ? K.up : K.dn });
    if (A.failed && (A.status === 'broken' || A.status === 'done')) out.push({ t: 'Слом DR ' + (A.side === 1 ? '↓ ' : '↑ ') + this._clk(A.failed), bg: K.brk });
    if (A.status === 'waiting') out.push({ t: 'ждёт подтверждения', bg: '#2A2E39' });
    if (A.status === 'forming') out.push({ t: 'DR формируется', bg: '#2A2E39' });
    return out;
  }
  // before a confirmation: the first later confirmation among similar sessions not confirmed yet
  _dir(sc) {
    const ov = sc.ov; if (!ov || !ov.dir) return null;
    const d = ov.dir;
    return { up: this._pct(d.up), dn: this._pct(d.dn), none: this._pct(d.none), wu: Math.round(d.up * 3.2), wd: Math.round(d.dn * 3.2), wn: Math.max(0, 320 - Math.round(d.up * 3.2) - Math.round(d.dn * 3.2)),
      line: 'вверх ' + this._pct(d.up) + ' · вниз ' + this._pct(d.dn) + ' · не будет ' + this._pct(d.none), n: d.nUp + ' / ' + d.nDn + ' / ' + d.nNone + ' из ' + ov.N };
  }
  // the common values every variant's chart markup uses
  _common(sc, st) {
    const K = this._C(), cfg = this._cfg(), xs = cfg.PW + (cfg.projW || 0);
    const pl = sc.priceLine || { x: 0, y: 0, w: 0, h: 0, bg: 'transparent', op: 0 };
    return {
      tb: this._toolbar(sc, st), m: this._mouse(), chartRef: this._refCb(), cursor: st.drag ? 'grabbing' : 'crosshair',
      boxes: sc.boxes, grid: sc.grid, gridT: sc.gridT, lines: sc.lines, lhits: sc.lhits, ds: this._dsv(sc, st),
      cells: sc.cells, hl: sc.hl, hlp: sc.hlp || { line: 'M0,0', fill: 'M0,0', lc: 'none', fc: 'none', w: 1 }, wicks: sc.wicks, bodies: sc.bodies, chits: sc.chits, pills: sc.pills, vlines: sc.vlines, glines: sc.glines, xh: sc.xh,
      ticks: sc.ticks, tags: this._tagBoxes(sc, xs), tlabels: sc.tlabels, ttags: sc.ttags, slabels: sc.slabels,
      lg: sc.legend, act: sc.act, chips: this._chips(sc), priceLine: pl,
      zoomIn: () => this._zoomBtn(-1), zoomOut: () => this._zoomBtn(1), reset: () => this._reset(), live: sc.live, replay: !sc.live
    };
  }
