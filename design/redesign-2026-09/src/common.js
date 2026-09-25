  // ================= shared view pieces (toolbar, side facts) =================
  _toolbar(sc, st) {
    const K = this._C(), D = this._D();
    const inst = ['NQ', 'ES', 'YM'].map(t => ({ t, bg: t === 'NQ' ? '#2A2E39' : 'transparent', c: t === 'NQ' ? '#FFFFFF' : K.text2 }));
    const sess = D.ORDER.map(k => {
      const s = sc.S[k], on = k === sc.act, hv = this._hv('sess|' + k);
      const running = k === 'RDR' && s.status === 'confirmed' && sc.live;
      return {
        t: k, bg: on ? '#2A2E39' : 'transparent', c: on ? '#FFFFFF' : K.text2,
        dot: running ? K.up : s.status === 'done' ? (s.failed ? K.dn : '#6B7280') : 'transparent',
        tip: k === 'ADR' ? 'ADR · окно 19:30–20:30 · до 02:00' : k === 'ODR' ? 'ODR · окно 03:00–04:00 · до 08:30' : 'RDR · окно 09:30–10:30 · до 16:00',
        click: () => this._selSession(k), enter: hv.enter, leave: hv.leave
      };
    });
    const L = st.layers;
    const layers = [
      { k: 'rclust', t: 'Откат', sw: K.retr }, { k: 'eclust', t: 'Экстремум', sw: K.ext },
      { k: 'fan', t: 'Веер', sw: '#C9CED6' }, { k: 'ladder', t: 'Лесенка', sw: 'linear-gradient(180deg,' + K.ext + ' 0px 5px,' + K.retr + ' 5px 10px)' }
    ].map(l => ({ t: l.t, sw: l.sw, bg: L[l.k] ? '#1F242D' : 'transparent', c: L[l.k] ? K.text : '#8F939E', bd: L[l.k] ? '1px solid #3A404C' : '1px solid #252A33', swop: L[l.k] ? 1 : 0.35, click: () => this._toggleLayer(l.k) }));
    return {
      inst, sess, layers, live: sc.live, replay: !sc.live,
      clock: this._clk(D.NOW) + ' ET', rpText: sc.act + ' · ' + this._clk(sc.obs),
      toLive: () => this._live(), refresh: () => {}
    };
  }
  // the facts of the active session in words and numbers (shared by the side views)
  _facts(sc) {
    const A = sc.A, ov = sc.ov, K = this._C();
    const f = { status: A.status, sess: sc.act, live: sc.live, obs: sc.obs, n: '', ntip: '', bigLabel: '', big: '', bigCol: '#D1D4DC' };
    f.arrow = A.side === 1 ? '↑' : A.side === -1 ? '↓' : '';
    if (A.drH != null) { f.dr = this._px(A.drL) + ' – ' + this._px(A.drH); f.idr = this._px(A.idrL) + ' – ' + this._px(A.idrH); }
    if (A.status === 'confirmed' && ov) {
      f.bigLabel = 'DR удержится до ' + this._clk(A.end); f.big = this._num(ov.drTrue, 1) + '%';
      f.bigCol = ov.drTrue >= 80 ? '#FFFFFF' : ov.drTrue >= 60 ? K.retr : K.dn;
      f.conf = f.arrow + ' ' + this._clk(A.conf);
      f.price = this._sg(A.nowCoord, 2) + ' IDR · ' + this._px(A.priceNow);
      f.priceLabel = sc.live ? 'Цена сейчас' : 'Цена на ' + this._clk(sc.obs);
      f.n = ov.n + ' похожих сессий';
      f.ntip = ov.n + ' из ' + ov.pool + ' сессий 2006–2025: подтверждение ' + f.arrow + ' ±15 мин от ' + this._clk(A.conf) + ', DR цел на ' + this._clk(sc.obs) + ', цена ±' + this._num(ov.band, 2) + ' IDR от сегодняшней. В макете числа синтетические.';
    } else if (A.status === 'done') {
      f.bigLabel = 'Сессия завершена'; f.big = A.failed ? 'DR сломан ' + this._clk(A.failed) : 'DR удержался'; f.bigCol = A.failed ? K.dn : '#FFFFFF';
      f.conf = f.arrow + ' ' + this._clk(A.conf);
      f.retr = this._sg(A.retrSoFar, 2) + ' IDR · ' + this._clk(A.retrT); f.ext = this._sg(A.extSoFar, 2) + ' IDR · ' + this._clk(A.extT);
    } else if (A.status === 'waiting') {
      f.bigLabel = 'DR сформирован'; f.big = 'Подтверждения нет'; f.bigCol = '#E6E8EE';
      f.pending = [['Позже вверх', '46% · 10:55'], ['Позже вниз', '38% · 11:05'], ['Без подтверждения', '16%']];
    } else if (A.status === 'forming') {
      f.bigLabel = 'Окно ' + this._clk(A.start) + '–' + this._clk(A.formed); f.big = 'DR формируется'; f.bigCol = '#E6E8EE';
    } else { f.bigLabel = ''; f.big = 'Сессия не началась'; f.bigCol = K.text2; }
    return f;
  }
  // the day's three sessions as clickable rows (select a session; hover lights its window on the chart)
  _days(sc) {
    const K = this._C(), D = this._D();
    return D.ORDER.map(k => {
      const s = sc.S[k], hv = this._hv('sess|' + k), on = k === sc.act, running = s.status === 'confirmed' && (k !== sc.act || sc.live);
      const conf = s.conf ? (s.side === 1 ? '↑ ' : '↓ ') + this._clk(s.conf) : '—';
      const stt = s.status === 'done' ? (s.failed ? 'DR сломан ' + this._clk(s.failed) : 'DR удержался') : running ? 'идёт' : s.status === 'waiting' ? 'ждёт подтверждения' : s.status === 'forming' ? 'DR формируется' : s.status === 'confirmed' ? 'повтор' : '';
      return {
        k, conf, st: stt, bg: on ? '#1B2029' : sc.hk === 'sess|' + k ? '#161A21' : 'transparent', c: on ? '#FFFFFF' : K.text2,
        ac: s.side === 1 ? K.up : s.side === -1 ? K.dn : K.text3, dot: running && sc.live ? K.up : 'transparent',
        click: () => { if (k !== this._st().session || this._st().rp) this._selSession(k); }, enter: hv.enter, leave: hv.leave
      };
    });
  }
