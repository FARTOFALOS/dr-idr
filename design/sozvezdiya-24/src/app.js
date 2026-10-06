// ================= DR Lab · design 24 «Границы хода» =================
// Design 22's working screen (candles of the day, the three sessions' DR / IDR, replay, the right panel, hover / pin,
// layers, settings) with its statistical layer replaced by the semantic specification DR-LAB-SEM-1.0
// (meaning/lens/2026-10-01-specifikaciya-v1.md). Every number of this screen belongs to one of these objects:
// - the family F, fixed at today's confirmation (after today's DR break: the break family F_break, the original kept
//   behind an explicit switch); one N per family, every share is of N, unknown mass kept apart;
// - «Границы хода» (main mode): R = the deepest point against the confirmation and X = the farthest point along it,
//   each session from its own confirmation to the end of its block, one point per session; R and X are on screen
//   together (operator 2026-10-01, variant «Окна времени»): their zones drawn as constellations («дымка и нити»), the
//   price histograms of both right of the price scale (two columns, each its own 100 %), the time band under the chart
//   (X up, R down, one scale, every zone a hill of its own sessions' times); hovering a zone or a price band links its
//   densest spot to its peak 15 minutes; what is under the cursor is read in the inspector at the bottom right; the six
//   windows of the family slide up from the bottom edge;
// - «Путь семьи»: where the family's M5 closed on each common clock M5 (each column is its own 100 %);
// - an area is only what the operator selects (a price band, or a band x time window); no automatic clusters, places
//   or targets; «на уровне или дальше» lives in a level's details, «заходили в полосу» in an area's details;
// - DR outcome of the family: held / broken / unknown / no period, 100 % of N.
// Data: lab/scene24.py (/api/d24/*), computed in integer ticks; the page recomputes the distributions from the members
// and checks them against the server's counts. A trading date of 2006-2025 opens as if it were today («История»): its
// families use only earlier sessions and the day is walked by replay (prefix honesty: bars after the slice are shown,
// never used).
(function () {
  'use strict';
  let NOW = 788;                   // the live minute (day minutes, ET); a history day: 17:00, the whole day closed
  const SESS = {
    ADR: { k: 'ADR', start: -270, formed: -210, end: 120 },
    ODR: { k: 'ODR', start: 180, formed: 240, end: 510 },
    RDR: { k: 'RDR', start: 570, formed: 630, end: 960 }
  };
  const ORDER = ['ADR', 'ODR', 'RDR'];
  let PREV = null;
  const A = { inst: 'NQ', src: 'live', date: null, day: null, D: null, fams: new Map(), pending: new Set(), auto: true, timer: 0, busy: false, error: null, dates: null, jump: false };
  const C = {
    bg: '#08090C', grid: '#1C2027', text: '#D1D4DC', text2: '#A3A8B3', text3: '#6F7582', axis: '#0B0C10',
    up: '#089981', dn: '#F23645', dr: '#EEF1F5', idr: '#AEBACB', mid: '#8B95A5', open: '#6B7380', std: '#5F6877', stdOn: '#A7B2C3',
    ADR: '#8E7CF0', ODR: '#E27AB8', PREV: '#8FA0B8', vib: '#F29A38', replay: '#F7C948', hist: '#8FB4FF', brk: '#F23645'
  };
  // everything a viewer can tune in «Настройки»; kept in this browser (localStorage), «Сбросить» restores these
  const DEF = {
    R: '#EBA06C', X: '#72A9EC', path: '#9FB3D1',
    ptA: 80, ptSize: 100, pastA: 35, cloudA: 100, threadA: 100, projA: 90, stripA: 80, heatA: 200,
    dr: '#EEF1F5', drA: 92, drW: 1.6, idr: '#AEBACB', idrA: 85, idrW: 1.2, idrDash: 'dash',
    mid: '#8B95A5', midA: 80, midDash: 'dots', std: '#A7B2C3', stdA: 75, stdOffA: 40,
    boxFill: 'grad', boxA: 45, prevA: 46,
    bandH: 13, bandRise: 30, capA: 100, capTxt: 100, colSize: 100, passedA: 30, zoneLbl: 100, lineLbl: 11, prevLbl: 9,
    fracLbl: 8.5, fracLine: 16, prevDayA: 45, midnightA: 55, pathA: 100, sideA: 70, domK: 200, domLine: 100, spentA: 100, viC: '#F29A38', vibA: 20, vibNQ: 0, vibES: 0, vibYM: 0, upC: '#089981', dnC: '#F23645', bg: '#08090C'
  };
  const BOXFILL = { grad: 'Градиент', solid: 'Сплошная', none: 'Без цвета' };
  const DASH = { solid: [], dash: [7, 4], dots: [1.5, 3.5], dashdot: [9, 3, 2, 3] };
  const CFG_KEY = 'drlab.d24.cfg';
  const cfg = Object.assign({}, DEF);
  try { Object.assign(cfg, JSON.parse(localStorage.getItem(CFG_KEY) || '{}')); } catch (e) { /* no storage: defaults */ }
  // the event colours chosen by the operator on 2026-10-01 (amber R, sky X) replace the earlier defaults kept in a browser
  if (cfg.R === '#DE8580') cfg.R = DEF.R;
  if (cfg.X === '#63C3A5') cfg.X = DEF.X;
  // operator 2026-10-06: every VI is drawn (the author: any gap between bodies); the old thresholds kept in a browser go once
  if (!cfg.vi0) { cfg.vibNQ = 0; cfg.vibES = 0; cfg.vibYM = 0; cfg.vi0 = 1; }
  const saveCfg = () => { try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch (e) { /* not kept */ } };
  const SCHEMA = [
    ['События семьи', [['R', 'Откат R · цвет', 'color'], ['X', 'Продолжение X · цвет', 'color'], ['ptA', 'Точки · яркость', 'range', 10, 100],
      ['ptSize', 'Точки · размер', 'range', 50, 200], ['pastA', 'Прошедшие по часам · яркость', 'range', 5, 100],
      ['cloudA', 'Созвездия · дымка', 'range', 20, 200], ['threadA', 'Созвездия · нити', 'range', 0, 300],
      ['spentA', 'Отработанные созвездия · яркость, %', 'range', 20, 200, 10]]],
    ['Гистограммы', [['projA', 'Цена справа · яркость', 'range', 10, 100], ['stripA', 'Лента времени · яркость', 'range', 10, 100]]],
    ['Путь семьи', [['path', 'Клетки · цвет', 'color'], ['heatA', 'Клетки · яркость (одна для всех колонок)', 'range', 20, 400, 10]]],
    ['Линии сессии', [['dr', 'DR · цвет', 'color'], ['drA', 'DR · яркость', 'range', 10, 100], ['drW', 'DR · толщина', 'range', 0.5, 3, 0.1],
      ['idr', 'IDR · цвет', 'color'], ['idrA', 'IDR · яркость', 'range', 10, 100], ['idrW', 'IDR · толщина', 'range', 0.5, 3, 0.1], ['idrDash', 'IDR · вид', 'dash'],
      ['mid', 'mid · цвет', 'color'], ['midA', 'mid · яркость', 'range', 10, 100], ['midDash', 'mid · вид', 'dash'],
      ['sideA', 'DR / IDR · цвет стороны активации, %', 'range', 0, 100, 5],
      ['std', 'STD · цвет', 'color'], ['stdA', 'STD стороны в игре · яркость', 'range', 5, 100], ['stdOffA', 'STD другой стороны · яркость', 'range', 0, 100]]],
    ['Коробки сессий', [['boxFill', 'Заливка DR / IDR', 'boxfill'], ['boxA', 'Заливка · яркость', 'range', 0, 100]]],
    ['Прошлые сессии и VI', [['prevA', 'DR / IDR прошлых сессий · яркость', 'range', 5, 100], ['viC', 'VI · цвет', 'color'], ['vibA', 'VI · яркость', 'range', 5, 60], ['vibNQ', 'VI NQ · разрыв тел от, пунктов', 'range', 0, 6, 0.25], ['vibES', 'VI ES · разрыв тел от, пунктов', 'range', 0, 3, 0.25], ['vibYM', 'VI YM · разрыв тел от, пунктов', 'range', 0, 20, 1]]],
    ['Лента времени и капсулы', [['bandH', 'Лента · высота, % экрана', 'range', 8, 30], ['bandRise', 'Лента · подъём в пустое место, % графика', 'range', 0, 50],
      ['domK', 'Лента · контраст перевеса X/R, %', 'range', 0, 400, 10], ['domLine', 'Лента · контур перевеса, %', 'range', 0, 200, 10], ['capA', 'Капсулы зон · заливка', 'range', 20, 300, 10], ['capTxt', 'Капсулы зон · текст', 'range', 40, 150, 5]]],
    ['Подписи', [['colSize', 'Колонка у цены · размер цифр, %', 'range', 60, 160, 5], ['passedA', 'Колонка · прошедшее и невозможное · яркость', 'range', 5, 80],
      ['zoneLbl', 'Созвездия · размер подписи, %', 'range', 60, 160, 5], ['lineLbl', 'DR / IDR · размер названия, px', 'range', 8, 16, 0.5],
      ['prevLbl', 'Прошлые уровни · размер названия, px', 'range', 6, 14, 0.5], ['fracLbl', 'Доли IDR в коробке · размер, px', 'range', 6, 14, 0.5],
      ['fracLine', 'Доли IDR в коробке · линии', 'range', 0, 60]]],
    ['День', [['prevDayA', 'Свечи вчера · яркость', 'range', 10, 100], ['midnightA', 'Полночь · линия', 'range', 0, 100], ['pathA', 'Путь сессии при наведении · яркость, %', 'range', 0, 300, 10]]],
    ['График', [['upC', 'Свеча вверх', 'color'], ['dnC', 'Свеча вниз', 'color'], ['bg', 'Фон', 'color']]]
  ];
  const DASH_NAMES = { solid: 'сплошная', dash: 'штрих', dots: 'точки', dashdot: 'штрихпунктир' };
  const FONT = '-apple-system,BlinkMacSystemFont,"Trebuchet MS",Roboto,Ubuntu,sans-serif';
  const LAYERS = [
    ['pts', 'Точки: одна сессия — одно событие', '#EBA06C'], ['zones', 'Созвездия: зоны R / X (карта зон)', '#72A9EC'],
    ['proj', 'Гистограммы цены справа', '#EBA06C'], ['strip', 'Лента времени снизу', '#72A9EC'], ['std', 'STD', C.stdOn],
    ['prev', 'DR и IDR прошлых сессий', C.dr], ['vib', 'VI (volume imbalance)', C.vib], ['det', 'Шесть окон семьи (снизу)', C.text2]
  ];

  // ---------- small helpers ----------
  const clk = m => { const x = ((Math.round(m) % 1440) + 1440) % 1440; return String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); };
  const num = (v, d) => Number(v).toLocaleString('ru-RU', { minimumFractionDigits: d, maximumFractionDigits: d });
  const px = v => { const r = Math.round(v / 0.25) * 0.25; return num(r, r % 1 === 0 ? 0 : 2); };
  // spec §6: shares computed before rounding, shown with one decimal and no trailing zero; details may show two
  const pct = v => { const r = Math.round(v * 10) / 10; return num(r, Number.isInteger(r) ? 0 : 1) + '%'; };
  const pct2 = v => { const r = Math.round(v * 100) / 100; return num(r, Number.isInteger(r) ? 0 : (Math.round(r * 10) === r * 10 ? 1 : 2)) + '%'; };
  const sgn = v => (v >= 0 ? '+' : '−') + num(Math.abs(v), 2);
  const sd = v => (Math.abs(v) < 1e-9 ? '0' : (v > 0 ? '+' : '−') + num(Math.abs(v), Math.abs(v * 10 - Math.round(v * 10)) < 1e-9 ? 1 : 2));
  const band = (k0, k1) => sd(k0 / 10) + '…' + sd(k1 / 10);
  const rgb = hex => { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  const mixW = (hex, f) => { const c = rgb(hex).map(v => Math.round(v + (255 - v) * f)); return '#' + c.map(v => v.toString(16).padStart(2, '0')).join(''); };
  const mixHex = (a, b, f) => { const x = rgb(a), y = rgb(b); return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * f).toString(16).padStart(2, '0')).join(''); };
  // THE COLOUR CATALOGUE BY STATE (operator 2026-10-06; meaning/13 entry 26): one rule for every element.
  //   active (a zone still possible, a band still ahead, the next level) — the event's own colour (R amber, X sky);
  //   HOLDS (today's extreme lies in the zone) — the same colour, lighter;
  //   spent (an IMPOSSIBLE zone, a band passed or impossible today, a reached level) — a slate shade of its colour, quiet;
  //   red — only the time pointer «уже прошло» (ring and window of a past peak); nowhere else
  const SPENT = '#59606C';
  const stateCol = (col, state) => state === 'IMPOSSIBLE' || state === 'spent' ? mixHex(col, SPENT, 0.55) : state === 'HOLDS' ? mixW(col, 0.25) : col;
  const rgba = (hex, a) => { const c = rgb(hex); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  // a percentage on the canvas: the number in its font, the «%» after it small and dim (operator 2026-10-06)
  const pctW = (c, t, wt, fs) => { c.font = wt + fs.toFixed(1) + 'px ' + FONT; const a = c.measureText(t.replace('%', '')).width; c.font = '600 ' + (fs * 0.58).toFixed(1) + 'px ' + FONT; return a + 1 + c.measureText('%').width; };
  function pctDraw(c, t, x, y, wt, fs, col) {
    const num = t.replace('%', '');
    c.font = wt + fs.toFixed(1) + 'px ' + FONT; c.fillStyle = col; c.fillText(num, x, y);
    const wn = c.measureText(num).width;
    c.save(); c.globalAlpha *= 0.55; c.font = '600 ' + (fs * 0.58).toFixed(1) + 'px ' + FONT; c.fillText('%', x + wn + 1, y); c.restore();
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const stepName = (j, above) => (above ? '+' : '−') + num(j * 0.5, 1);
  // exact floor division of integers (b > 0): the price cell of a directed value is floor(10 v / w)
  const fdiv = (a, b) => { let q = Math.floor(a / b); if (q * b > a) q--; else if ((q + 1) * b <= a) q++; return q; };

  // ---------- the day: bars and volume imbalances ----------
  // volume imbalance (VI, ICT; operator 2026-09-29): two neighbouring M5 candles whose BODIES do not overlap while their
  // WICKS do; the zone is the space between the two bodies. Bodies apart and wicks apart = a gap, not a VI.
  function vibsOf(bars) {
    const vibs = [];
    for (let i = 1; i < bars.length; i++) {
      const a = bars[i - 1], b = bars[i];
      if (b.t - a.t !== 5) continue;
      const aT = Math.max(a.o, a.c), aB = Math.min(a.o, a.c), bT = Math.max(b.o, b.c), bB = Math.min(b.o, b.c);
      let lo, hi, dir;
      if (bB > aT + 1e-9 && b.l <= a.h + 1e-9) { lo = aT; hi = bB; dir = 1; }
      else if (bT < aB - 1e-9 && b.h >= a.l - 1e-9) { lo = bT; hi = aB; dir = -1; }
      else continue;
      let fill = null;   // rebalanced: a later bar enters the zone, even with a wick
      for (let j = i + 1; j < bars.length; j++) { const q = bars[j]; if (q.l < hi && q.h > lo) { fill = q.t; break; } }
      vibs.push({ t: b.t, lo, hi, dir, fill });
    }
    return vibs;
  }
  const MON = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'], WD = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
  function day() {
    const x = A.day;
    if (!x || x.status !== 'ok') return A.D = { d: 'none', bars: [], vibs: [], date: '', dm: '', S: {}, hist: A.src === 'hist' };
    const key = A.inst + '|' + (x.source === 'history' ? 'h' + x.date : x.fetched_at);
    if (A.D && A.D.d === key) return A.D;
    const [yy, mm, dd] = x.date.split('-').map(Number);
    const bars = x.bars.map(b => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4] }));
    return (A.D = { d: key, bars, vibs: vibsOf(bars), date: WD[x.weekday] + ', ' + dd + ' ' + MON[mm - 1] + (x.source === 'history' ? ' ' + yy : ''),
      dm: dd + ' ' + MON[mm - 1], S: {}, hist: x.source === 'history', iso: x.date });
  }
  // ---------- one session at an observed minute (the rules of lab/live.py; DR, confirmation, break from closed M5) ----------
  function sess(D, k, obs, live) {
    const S = SESS[k], key = k + '|' + obs + '|' + (live ? 1 : 0);
    if (D.S[key]) return D.S[key];
    const closedBy = live ? NOW : obs;
    const closed = D.bars.filter(b => b.t + 5 <= closedBy), known = live ? D.bars : closed;
    const res = { k, start: S.start, formed: S.formed, end: S.end, obs, live };
    const win = known.filter(b => b.t >= S.start && b.t < S.formed);
    if (!win.length || obs < S.start) { res.status = 'before'; return (D.S[key] = res); }
    res.open = win[0].o;
    res.drH = Math.max(...win.map(b => b.h)); res.drL = Math.min(...win.map(b => b.l));
    res.idrH = Math.max(...win.map(b => Math.max(b.o, b.c))); res.idrL = Math.min(...win.map(b => Math.min(b.o, b.c)));
    res.mid = (res.idrH + res.idrL) / 2;
    res.complete = closed.filter(b => b.t >= S.start && b.t < S.formed).length === (S.formed - S.start) / 5;
    if (!res.complete) { res.status = 'forming'; return (D.S[key] = res); }
    res.close = win[win.length - 1].c; res.boxUp = res.close >= res.open; res.width = res.idrH - res.idrL;
    const lim = Math.min(obs, S.end), w = res.width;
    const inSess = known.filter(b => b.t >= S.formed && b.t < lim), last = inSess[inSess.length - 1] || win[win.length - 1];
    res.priceNow = last.c; res.lastT = last.t;
    let conf = null;
    for (const b of closed) {
      if (b.t < S.formed || b.t + 5 > lim) continue;
      if (b.c > res.drH) { conf = { t: b.t + 5, side: 1 }; break; }
      if (b.c < res.drL) { conf = { t: b.t + 5, side: -1 }; break; }
    }
    if (!conf) { res.status = obs >= S.end ? 'noconf' : 'waiting'; return (D.S[key] = res); }
    const side = conf.side;
    Object.assign(res, { conf: conf.t, side, edge: side === 1 ? res.idrH : res.idrL, opp: side === 1 ? res.drL : res.drH });
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
    let far = -Infinity, fart = null;
    for (const b of inSess) {
      if (b.t + 5 <= conf.t || (res.failed && b.t + 5 > res.failed)) continue;
      const hi = res.coord(side === 1 ? b.h : b.l);
      if (hi > far) { far = hi; fart = b.t + 5; }
    }
    if (fart != null) Object.assign(res, { farSoFar: far, farT: fart, farP: res.price(far) });
    const taken = (sd_, edge, from, to) => {
      const out = [];
      for (let j = 1; j <= 6; j++) {
        const L = edge + sd_ * j * w / 2, b = inSess.find(q => q.t + 5 > from && q.t + 5 <= to && (sd_ === 1 ? q.h >= L : q.l <= L));
        if (!b) { out.push({ j, t: null, name: stepName(j, sd_ === 1) }); break; }
        out.push({ j, t: b.t + 5, name: stepName(j, sd_ === 1) });
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
    return (D.S[key] = res);
  }
  // the named lines of a session, as Pine DR/IDR V1.5 draws them (STD = steps of 0.5 IDR from the IDR edges)
  function levels(s) {
    if (s.drH == null) return [];
    const w = s.idrH - s.idrL, L = [
      { id: 'drH', name: 'DR', full: 'DR high', p: s.drH, type: 'dr' }, { id: 'drL', name: 'DR', full: 'DR low', p: s.drL, type: 'dr' },
      { id: 'idrH', name: 'IDR', full: 'IDR high', p: s.idrH, type: 'idr' }, { id: 'idrL', name: 'IDR', full: 'IDR low', p: s.idrL, type: 'idr' },
      { id: 'mid', name: 'mid', full: 'середина IDR', p: s.mid, type: 'mid' }, { id: 'open', name: 'open', full: 'открытие сессии', p: s.open, type: 'open' }
    ];
    for (let j = 1; j <= 6; j++) {
      L.push({ id: 'u' + j, name: stepName(j, true), full: 'STD ' + stepName(j, true), p: s.idrH + j * w / 2, type: 'std', dir: 1, j });
      L.push({ id: 'd' + j, name: stepName(j, false), full: 'STD ' + stepName(j, false), p: s.idrL - j * w / 2, type: 'std', dir: -1, j });
    }
    return L;
  }
  // the side in play: the confirmation's, after a break the break's, none before the confirmation
  const playSide = s => (s.status === 'broken' || (s.status === 'done' && s.failed) ? s.nside : s.side) || 0;
  // operator 2026-10-06: an STD level is shown only while it is valid, on the side in play (both sides before the
  // confirmation); the levels against it (−0,5, −1 … for a long) are not drawn, named or hoverable
  // operator 2026-10-06: today's DR / IDR take the colour of the side in play (green for a long, red for a short, the
  // break's side after a break), so the lines, their names and their price tags show where the session goes; before the
  // confirmation they keep their own colour (settings). setting «sideA» = how strongly (0 = never)
  const sideCol = (s, base) => { const p = playSide(s); return !p || !cfg.sideA ? base : mixHex(base, p > 0 ? C.up : C.dn, cfg.sideA / 100); };
  // operator 2026-10-06: an STD level on the side in play is drawn by what it means NOW: 'taken' — reached today after
  // the confirmation (or the break), no longer a question: quiet round dots (not dashes, which are IDR's); 'next' — the
  // first one not reached yet, the trader's question «will it get there?»: the strongest; 'far' — the ones beyond it
  function stdState(s, l) {
    const p = playSide(s);
    if (l.type !== 'std' || !p || l.dir !== p) return 'plain';
    const e = ((s.failed ? s.takenN : s.taken) || []).find(z => z.j === l.j);
    return e && e.t ? 'taken' : e ? 'next' : 'far';
  }
  const stdShown = (s, l) => l.type !== 'std' || (st.L.std && (!playSide(s) || l.dir === playSide(s)));
  function where(s, p) {
    const L = levels(s).filter(l => l.type !== 'open').sort((a, b) => a.p - b.p), w = s.idrH - s.idrL;
    let best = null;
    for (const l of L) if (!best || Math.abs(l.p - p) < Math.abs(best.p - p)) best = l;
    if (best && Math.abs(best.p - p) < 0.12 * w) return 'у ' + (best.type === 'std' ? best.name : best.full);
    let a = null, b = null;
    for (const l of L) { if (l.p <= p) a = l; if (l.p > p && !b) b = l; }
    const nm = l => (l.type === 'std' ? l.name : l.full);
    if (a && b) return 'между ' + nm(a) + ' и ' + nm(b);
    return a ? 'выше ' + nm(a) : b ? 'ниже ' + nm(b) : '';
  }

  // ---------- the family snapshot (spec §3, §5, §9, §13) ----------
  // The server (lab/scene24.py) selects the family and measures every member in integer ticks: R, X (value v, first
  // open t, ties), DR outcome, order, the path per common clock M5 (directed low, high, close). The page maps a member's
  // u = v / w to today's price through today's IDR (spec §9.1: a coordinate transfer, not a forecast of prices).
  const wantView = s => s.failed && st.view !== 'conf' ? 'brk' : 'conf';
  const famKey = (D, s, view) => D.d + '|' + s.k + '|' + s.conf + '|' + s.side + '|' + view + '|' + (view === 'brk' ? s.failed : '') + '|' + st.scope;
  const sliceOf = ctx => ctx.live ? Math.floor(NOW / 5) * 5 : ctx.obs;      // the last closed M5 (AGENTS.md rule 6)
  function requestFamily(fk, s, view) {
    if (A.pending.has(fk)) return;
    A.pending.add(fk);
    const at = s.live ? Math.floor(NOW / 5) * 5 : s.obs;
    fetch('/api/d24/family?instrument=' + A.inst + '&session=' + s.k + '&at=' + at + (A.src === 'hist' ? '&date=' + A.date : '') + '&view=' + view + (st.scope === 'all' ? ':all' : ''))
      .then(r => r.json()).then(r => { A.fams.set(fk, r); if (A.fams.size > 40) A.fams.delete(A.fams.keys().next().value); })
      .catch(() => A.fams.set(fk, { status: 'error', message: 'Локальный сервер не ответил' }))
      .finally(() => { A.pending.delete(fk); redraw(true); });
  }
  function snapOf(D, s) {
    if (!s.conf || !['confirmed', 'broken', 'done'].includes(s.status) || D.d === 'none') return null;
    const view = wantView(s), fk = famKey(D, s, view), r = A.fams.get(fk);
    if (!r) { requestFamily(fk, s, view); return null; }
    if (r.status !== 'ok' || r.view !== view || (r.key.scope || 'weekday') !== st.scope || !r.today || r.today.c0 !== s.conf || r.today.side !== s.side) return null;
    if (!r._F) r._F = buildSnap(r, s, view);
    return r._F;
  }
  function buildSnap(r, s, view) {
    const side = s.side, brk = view === 'brk', w0 = s.idrH - s.idrL, tick = (A.day && A.day.tick) || 0.25;
    const d0 = brk ? -side : side, e0 = brk ? (side === 1 ? s.idrL : s.idrH) : (side === 1 ? s.idrH : s.idrL);
    const F = {
      r, view, brk, N: r.N, f: r.schedule.formed, end: r.schedule.end, grid: r.grid, M: r.members, cond: r.cond,
      d0, e0, w0, tick, e0t: Math.round(e0 / tick), w0t: Math.round(w0 / tick), act0: brk ? s.failed : s.conf, side,
      names: brk ? { R: 'Откат против слома', X: 'Продолжение слома' } : { R: 'Откат', X: 'Продолжение' },   // operator 2026-10-06; X = the author's max extension
      what: brk ? { R: 'самая глубокая точка против слома', X: 'самая дальняя точка по слому' } : { R: 'самая глубокая точка против подтверждения', X: 'самая дальняя точка по подтверждению' },
      from: brk ? 'от своего слома' : 'от своего подтверждения', nb: (r.schedule.end - r.schedule.formed) / 15
    };
    F.u2p = u => F.e0 + F.d0 * u * F.w0;
    F.p2u = p => F.d0 * (p - F.e0) / F.w0;
    F.cellOfP = p => Math.floor(10 * F.p2u(p) + 1e-9);
    F.ev = { R: evDist(F, 'R'), X: evDist(F, 'X') };
    if (!brk) { F.out = { held: 0, broken: 0, unknown: 0, none: 0 }; for (const m of F.M) F.out[m.outcome]++; }
    // the zone maps of R and X (zone-map-3, meaning/12): found once by the server on the snapshot; the page recounts
    // every zone from the member points and compares (the zone is its exact region of cells, never its envelope)
    F.zones = r.zones || {};
    F.zcell = {};
    for (const ev of ['R', 'X']) {
      F.zcell[ev] = new Map();
      const Zm = F.zones[ev];
      if (Zm) Zm.zones.forEach((z, i) => { for (const [k, b] of z.cell_mask) F.zcell[ev].set(k + '|' + b, i); });
    }
    // the same definitions computed twice: the page's counts must equal the server's (checked by tests/ui_check24.js)
    F.mismatch = [];
    for (const ev of ['R', 'X']) {
      const a = r.counts[ev], b = F.ev[ev];
      const sa = a.cells.map(c => c.join(',')).sort().join(';'), sb = [...b.cells.values()].map(c => [c.k, c.b, c.list.length].join(',')).sort().join(';');
      if (sa !== sb || a.unknown !== b.unknown || a.none !== b.none) F.mismatch.push(ev);
      const Zm = F.zones[ev];
      if (Zm) {
        const n = Zm.zones.map(() => 0);
        for (const q of b.pts) { const i = F.zcell[ev].get(q.k + '|' + q.b); if (i != null) n[i]++; }
        if (Zm.zones.some((z, i) => z.n_zone !== n[i]) || n.reduce((t, x) => t + x, 0) + Zm.n_residual_total + Zm.unknown_count + Zm.no_event_count !== F.N) F.mismatch.push('zones ' + ev);
      }
    }
    if (F.out && JSON.stringify(F.out) !== JSON.stringify(r.counts.outcome)) F.mismatch.push('outcome');
    if (F.mismatch.length) console.error('design 24: the page and the server disagree on', F.mismatch);
    return F;
  }
  // one event of the family: its points, its joint table price cell x time cell, and the unknown / no-period mass
  function evDist(F, ev) {
    const cells = new Map(), P = new Map(), T = new Map(), pts = [];
    let unknown = 0, none = 0;
    F.M.forEach((m, i) => {
      const e = m[ev];
      if (e.s === 'known') {
        const k = fdiv(10 * e.v, m.w), b = Math.floor((e.t - F.f) / 15), key = k + '|' + b;
        if (!cells.has(key)) cells.set(key, { k, b, list: [] });
        cells.get(key).list.push(i);
        P.set(k, (P.get(k) || 0) + 1); T.set(b, (T.get(b) || 0) + 1);
        const u = e.v / m.w;
        pts.push({ i, ev, k, b, t: e.t, u, p: F.u2p(u), m });
      } else if (e.s === 'unknown') unknown++; else none++;
    });
    return { cells, P, T, pts, unknown, none, known: pts.length };
  }
  // a level u = a / b (b > 0) in the snapshot's directed scale; up: an M5 high at or beyond it, down: an M5 low
  function reachOne(F, m, L, up, from) {
    let gap = false;
    for (let j = 0; j < F.grid.length; j++) {
      if (F.grid[j] <= from) continue;
      const q = m.path[j];
      if (!q) { gap = true; continue; }
      if (up ? q[1] * L.b >= L.a * m.w : q[0] * L.b <= L.a * m.w) return 'yes';
    }
    return gap ? 'unknown' : 'no';
  }
  // a band [k0/10, k1/10): an M5 range visits it when low < k1/10 and high >= k0/10 (spec §5.4)
  function visitOne(F, m, k0, k1, from) {
    let gap = false;
    for (let j = 0; j < F.grid.length; j++) {
      if (F.grid[j] <= from) continue;
      const q = m.path[j];
      if (!q) { gap = true; continue; }
      if (10 * q[0] < k1 * m.w && 10 * q[1] >= k0 * m.w) return 'yes';
    }
    return gap ? 'unknown' : 'no';
  }
  // the literal crossing of a level by a candle (spec §5.4): low <= L <= high on one M5 — another event than «на уровне
  // или дальше» (a gap past the level is «дальше» without a crossing); details only
  function crossOne(F, m, L, from) {
    let gap = false;
    for (let j = 0; j < F.grid.length; j++) {
      if (F.grid[j] <= from) continue;
      const q = m.path[j];
      if (!q) { gap = true; continue; }
      if (q[0] * L.b <= L.a * m.w && L.a * m.w <= q[1] * L.b) return 'yes';
    }
    return gap ? 'unknown' : 'no';
  }
  const crossCount = (F, L, from) => tally(F, m => crossOne(F, m, L, from == null ? m.act : from));
  // the range field V(K, j) of one M5 (spec §5.3): the sessions whose M5 range touched the cell; not C, not normalised
  function rangeField(F, j, k) {
    let n = 0, unknown = 0;
    for (const m of F.M) { const q = m.path[j]; if (!q) { unknown++; continue; } if (10 * q[0] < (k + 1) * m.w && 10 * q[1] >= k * m.w) n++; }
    return { n, unknown };
  }
  function tally(F, fn) { const c = { yes: 0, no: 0, unknown: 0, list: [] }; F.M.forEach((m, i) => { const v = fn(m); c[v]++; if (v === 'yes') c.list.push(i); }); return c; }
  // from = null: each session from its own activation (its whole horizon); a minute: the common remaining hours (t, E]
  const reachCount = (F, L, up, from) => tally(F, m => reachOne(F, m, L, up, from == null ? m.act : from));
  const visitCount = (F, k0, k1, from) => tally(F, m => visitOne(F, m, k0, k1, from == null ? m.act : from));
  // the events of an area: a price band [k0, k1) of cells, optionally a time window [b0, b1) of 15-minute cells
  function areaCount(F, ev, a) {
    let n = 0;
    for (const q of F.ev[ev].pts) if (q.k >= a.k0 && q.k < a.k1 && (a.b0 == null || (q.b >= a.b0 && q.b < a.b1))) n++;
    return n;
  }
  // «Путь семьи»: the family's M5 closes on one common clock M5 (spec §5.3); one vote per session, a missing M5 = unknown
  function filmOf(F) {
    if (F.film) return F.film;
    F.film = F.grid.map((T, j) => {
      const cells = new Map();
      let unknown = 0, pre = 0;
      F.M.forEach((m, i) => {
        const q = m.path[j];
        if (!q) { unknown++; return; }
        const k = fdiv(10 * q[2], m.w);
        if (!cells.has(k)) cells.set(k, []);
        cells.get(k).push(i);
        if (T < m.act) pre++;
      });
      return { j, T, cells, unknown, pre };
    });
    return F.film;
  }
  // a price level of today's chart as an exact rational u = a / b of the snapshot's scale (half ticks allowed)
  function levelRat(F, p) {
    const p2 = Math.round(2 * p / F.tick);
    return { a: F.d0 * (p2 - 2 * F.e0t), b: 2 * F.w0t };
  }
  const tk = p => Math.round(p / ((A.day && A.day.tick) || 0.25));
  // today's closed M5 after today's activation up to the slice (spec §8 «Сегодняшние факты»), directed ticks
  function todayRows(F, ctx) {
    const sl = sliceOf(ctx), out = [];
    for (const b of ctx.D.bars) {
      const T = b.t + 5;
      if (T <= F.act0 || T > sl) continue;
      const lo = F.d0 === 1 ? b.l : b.h, hi = F.d0 === 1 ? b.h : b.l;
      out.push({ T, lo: F.d0 * (tk(lo) - F.e0t), hi: F.d0 * (tk(hi) - F.e0t), cl: F.d0 * (tk(b.c) - F.e0t) });
    }
    return out;
  }
  function actClose(F, ctx) { const b = ctx.D.bars.find(q => q.t + 5 === F.act0); return b ? F.d0 * (tk(b.c) - F.e0t) : null; }
  function todayReach(F, ctx, L, up) {
    const w = F.w0t, r = todayRows(F, ctx).find(q => up ? q.hi * L.b >= L.a * w : q.lo * L.b <= L.a * w), c = actClose(F, ctx);
    return { t: r ? r.T - 5 : null, atAct: c == null ? null : up ? c * L.b >= L.a * w : c * L.b <= L.a * w };
  }
  function todayVisit(F, ctx, k0, k1) {
    const w = F.w0t, r = todayRows(F, ctx).find(q => 10 * q.lo < k1 * w && 10 * q.hi >= k0 * w), c = actClose(F, ctx);
    return { t: r ? r.T - 5 : null, atAct: c == null ? null : 10 * c >= k0 * w && 10 * c < k1 * w };
  }
  // the side of a level's question (spec §5.4): a level beyond the edge of play (u > 0) asks «по направлению» (an M5 high
  // at or beyond it; its full-horizon share is the tail of X), a level at or behind the edge (u <= 0) asks «против»
  // (an M5 low at or beyond it; the cumulative share of R). Named in every passport.
  // eslint-disable-next-line no-unused-vars
  function levelUp(F, ctx, L) { return L.a > 0; }
  const gcd = (a, b) => { a = Math.abs(a); b = Math.abs(b); while (b) [a, b] = [b, a % b]; return a || 1; };
  const ratTxt = L => { const g = gcd(L.a, L.b), a = L.a / g, b = L.b / g; return b === 1 ? String(a) : a + '/' + b; };
  const dirName = (F, up) => F.brk ? (up ? 'по слому' : 'против слома') : (up ? 'по подтверждению' : 'против подтверждения');

  // ---------- passports (spec §13.3): every number shown is made here, with its object, region, horizon and counts ----------
  const P24 = { links: [], list: [], seq: 0 };
  function pp(F, o) {
    const p = Object.assign({ id: ++P24.seq, family_id: F.r.family_id, snapshot_id: F.r.snapshot_id, N: F.N, unknown_count: 0, no_event_count: 0 }, o);
    p.pct = F.N ? 100 * p.yes_count / F.N : null;
    p.pctHi = F.N && p.unknown_count ? 100 * (p.yes_count + p.unknown_count) / F.N : null;
    P24.list.push(p);
    if (P24.list.length > 600) P24.list.splice(0, 300);
    return p;
  }
  const ppTxt = (p, range) => p.pct == null ? '—' : range && p.pctHi != null ? pct(p.pct) + '–' + pct(p.pctHi) : pct(p.pct);
  // the reading of a number in one sentence (spec §14): such a share of this family had THIS event, IN THIS area, OVER
  // THIS horizon (and ON THIS M5)
  function sentence(p) { return '<b>' + ppTxt(p, p.binary) + '</b> семьи — ' + p.phrase + ' · <span class="k">' + p.horizon + '</span>'; }
  function evPass(F, ev, region, bounds, time, yes) {
    const D = F.ev[ev];
    return pp(F, { event_id: ev, region_kind: region, exact_price_bounds: bounds, time_bounds: time, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: yes, unknown_count: D.unknown, no_event_count: D.none, display_scope: region,
      phrase: F.names[ev].toLowerCase() + ' ' + ev + ' (' + F.what[ev] + ')' + (bounds ? ' в полосе ' + band(bounds[0], bounds[1]) + ' SD' : '') + (time ? ' в ' + clk(time[0]) + '–' + clk(time[1]) : ''),
      horizon: F.from + ' до ' + clk(F.end) });
  }

  // ---------- view state ----------
  const st = {
    session: 'RDR', rp: null, v0: 545, v1: 1005, p0: null, p1: null, auto: true,
    L: { pts: true, zones: true, proj: true, strip: true, std: true, prev: true, vib: true, det: true },
    ev: 'R', mode: 'bounds', view: 'auto', scope: 'weekday', area: null, tool: false, col: null,
    hover: null, pin: null, mx: -1, my: -1, drag: null, stripH: 46, stripPin: false, menu: false,
    detH: 22, detPin: false, detOver: false, navHover: false
  };
  const root = document.getElementById('dr21-root');
  const dom = id => id === 'dr21-root' ? root : root.querySelector('#' + id);
  const cv = dom('cv'), g2 = cv.getContext('2d'), tip = dom('tip'), panel = dom('panel'), nav = dom('nav'), det = dom('det');
  let V = null;   // this frame's geometry and context

  function cur() {
    const D = day(), obs = st.rp != null ? st.rp : NOW, live = st.rp == null;
    const s = sess(D, st.session, obs, live), F = snapOf(D, s);
    return { D, obs, live, s, F };
  }
  // the right edge of the time axis is anchored at the session end + 45 minutes (design 22's wheel; operator 2026-10-06:
  // for every gesture): only the left edge moves, from the «↺» view (box start .. session end) to the previous day's RDR (LEFT_MOST)
  const rightEdge = () => SESS[st.session].end + 45;
  // operator 2026-10-06: the left edge goes back no further than the previous trading day's RDR (its box at 09:30
  // yesterday, minute −870, plus a quarter of an hour): further left there is nothing to read, only black
  const LEFT_MOST = -885;
  function anchorRight(v0) {
    const lim = rightEdge(), maxSpan = lim - LEFT_MOST, minSpan = Math.min(lim - (SESS[st.session].start - 25), maxSpan);
    st.v1 = lim; st.v0 = lim - clamp(lim - v0, minSpan, maxSpan);
  }
  function fitSession(k) { const S = SESS[k]; st.v0 = S.start - 25; st.v1 = S.end + 45; st.auto = true; st.p0 = st.p1 = null; }
  function selSession(k) {
    st.session = k; st.pin = null; st.hover = null; st.area = null; st.col = null; st.view = 'auto';
    if (A.src === 'hist') { const s = sess(day(), k, NOW, false); st.rp = s.conf || null; }
    else if (NOW >= SESS[k].start) {
      if (NOW >= SESS[k].end) { const s = sess(day(), k, SESS[k].end, false); st.rp = s.conf ? Math.min(SESS[k].end, s.conf + 30) : null; }
      else st.rp = null;
    } else st.rp = null;
    fitSession(k);
    render(true);
  }
  function sessOf(t) { return ORDER.find(k => t > SESS[k].start && t <= SESS[k].end) || null; }
  function replayAt(t) {
    const k = sessOf(t);
    if (!k) return;
    if (st.rp === t) { st.rp = null; if (A.src === 'live') st.session = sessionNow(); st.pin = null; render(true); return; }
    st.rp = t >= NOW ? null : t;
    if (k !== st.session) { st.session = k; st.area = null; st.col = null; st.view = 'auto'; }
    st.pin = null;
    render(true);
  }
  function backLive() { st.rp = null; if (A.src === 'live') st.session = sessionNow(); st.pin = null; render(true); }
  function sessionNow() {
    for (const k of ORDER) if (NOW >= SESS[k].start && NOW < SESS[k].end) return k;
    let best = 'RDR';
    for (const k of ORDER) if (NOW >= SESS[k].start) best = k;
    return best;
  }

  // ---------- geometry ----------
  function geom(ctx) {
    const W = cv.clientWidth, H = cv.clientHeight, handleH = st.L.det ? 22 : 0, axisW = 66, timeH = 28;
    const bounds = !!(ctx.F && ctx.F.N) && st.mode === 'bounds';
    // the price column holds R and X in one column in «Границы хода» (each its own 100 %; operator 2026-10-06: one
    // column, not two), one M5 column in «Путь семьи»
    const projW = st.L.proj && ctx.F && ctx.F.N ? (bounds ? 116 : 96) : 0;
    // the time band under the chart (variant «Окна времени»): capsules, hills, columns; operator 2026-10-06: the candles
    // take the height, the band about an eighth of it (84-118 px)
    const bandH = bounds && st.L.strip ? Math.round(clamp((H - handleH - timeH) * cfg.bandH / 100, 60, (H - handleH - timeH) * 0.4)) : 0;
    const plot = { x: 0, y: 0, w: W - axisW - projW, h: H - handleH - timeH - bandH };
    const G = { W, H, handleH, axisW, timeH, plot, projW, ctx, bandH, taxisY: plot.h + bandH };
    G.proj = { x: plot.w + axisW, y: 0, w: projW, h: plot.h };
    G.X = t => plot.x + (t - st.v0) / (st.v1 - st.v0) * plot.w;
    G.T = x => st.v0 + (x - plot.x) / plot.w * (st.v1 - st.v0);
    let p0 = st.p0, p1 = st.p1;
    if (st.auto || p0 == null) { const r = autoRange(ctx); p0 = r[0]; p1 = r[1]; }
    G.p0 = p0; G.p1 = p1;
    G.Y = p => plot.y + (p1 - p) / (p1 - p0) * plot.h;
    G.P = y => p1 - (y - plot.y) / plot.h * (p1 - p0);
    G.bs = plot.w * 5 / (st.v1 - st.v0);
    G.stripOn = bandH > 0;
    G.band = { x: plot.x, y: plot.h, w: plot.w, h: bandH };
    G.strip = G.band;
    return G;
  }
  // the price range: the day's candles in view and the box; with a family also the middle 90 % of R and of X (both, so the
  // switch R / X does not jump); everything outside stays in the distribution and is named at the column's edge
  function autoRange(ctx) {
    let lo = Infinity, hi = -Infinity;
    const inV = t => t + 5 >= st.v0 && t <= st.v1;
    for (const b of ctx.D.bars) if (inV(b.t)) { lo = Math.min(lo, b.l); hi = Math.max(hi, b.h); }
    const s = ctx.s;
    if (s.drH != null) { lo = Math.min(lo, s.drL); hi = Math.max(hi, s.drH); }
    // operator 2026-10-06: the «↺» view fits the candles, the box and the zones still ahead (status HOLDS or POSSIBLE,
    // R and X: the constellations the trader looks at next); scattered points and impossible zones do not widen it,
    // the points beyond the frame are named by ▲ / ▼ in the price column
    if (ctx.F && isFinite(lo)) for (const ev of ['R', 'X']) {
      const Zm = ctx.F.zones[ev], S = Zm ? zoneStatus(ctx.F, ctx, ev) : [];
      if (Zm) Zm.zones.forEach((z, i) => {
        if (S[i] === 'IMPOSSIBLE') return;
        const ks = z.cell_mask.map(q => q[0]), a = ctx.F.u2p(Math.min(...ks) / 10), b = ctx.F.u2p((Math.max(...ks) + 1) / 10);
        lo = Math.min(lo, a, b); hi = Math.max(hi, a, b);
      });
    }
    // operator 2026-10-06: the next STD not reached yet on the side in play is the trader's question («will it get
    // there?»), so it is always in the frame
    if (isFinite(lo) && s.drH != null && st.L.std) { const nx = levels(s).find(l => stdState(s, l) === 'next'); if (nx) { lo = Math.min(lo, nx.p); hi = Math.max(hi, nx.p); } }
    if (!isFinite(lo)) { lo = 24400; hi = 24800; }
    // room under the lowest content for the time band's columns and hills to rise into (bandOverlay): they never cover
    // candles, the box or a live zone, so they need free space below them (operator 2026-10-06)
    if (ctx.F && st.mode === 'bounds' && st.L.strip) lo -= (hi - lo) * 0.16;
    const pad = (hi - lo) * 0.05;
    return [lo - pad, hi + pad + (hi - lo) * 0.02];
  }
  const bodyW = S => { if (S >= 2.5 && S <= 4) return 3; const c = 1 - 0.2 * Math.atan(Math.max(4, S) - 4) / (Math.PI * 0.5); let w = Math.max(1, Math.min(Math.floor(S * c), Math.floor(S))); if (w >= 2 && w % 2 === 0) w -= 1; return w; };

  // ---------- drawing ----------
  function render(full) {
    const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const ctx = cur();
    if (st.pinLvl && ctx.s.drH != null) { const l = levels(ctx.s).find(z => z.id === st.pinLvl); if (l) st.pin = { k: 'lvl', id: l.id, l }; st.pinLvl = null; }
    if (st.pinZone && ctx.F) { st.pin = { k: 'zone', ev: st.ev, i: st.pinZone - 1 }; st.pinZone = null; }
    V = geom(ctx);
    V.win = null;
    const c = g2;
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    Object.assign(C, { dr: cfg.dr, idr: cfg.idr, mid: cfg.mid, std: cfg.std, stdOn: cfg.std, vib: cfg.viC, up: cfg.upC, dn: cfg.dnC, bg: cfg.bg });
    c.fillStyle = C.bg; c.fillRect(0, 0, W, H);
    c.save(); c.beginPath(); c.rect(V.plot.x, V.plot.y, V.plot.w, V.plot.h); c.clip();
    const F = ctx.F;
    drawBoxes(c, ctx);
    drawMidnight(c, 0, V.plot.h);
    if (st.L.prev) drawPrev(c, ctx);
    if (st.L.vib) drawVib(c, ctx);
    if (F && st.mode === 'path') drawFilm(c, ctx);
    if (F) { drawHighlight(c, ctx); linkOf(ctx); }
    drawLevels(c, ctx);
    drawReference(c, ctx);
    if (F && st.mode === 'bounds') { if (st.L.zones) drawClouds(c, ctx); drawMemberPath(c, ctx); }
    drawCandles(c, ctx);
    drawPills(c, ctx);
    drawNow(c, ctx);
    if (F && st.mode === 'bounds') drawLink(c, ctx);
    if (F && st.mode === 'bounds' && st.L.pts) drawPoints(c, ctx);
    if (F && st.mode === 'bounds') drawPair(c, ctx);
    if (F) drawZones(c, ctx);
    if (F) drawArea(c, ctx);
    if (F && st.mini) drawMini(c, ctx);
    drawTags(c, ctx);
    drawCross(c);
    c.restore();
    if (F && V.stripOn) drawBand(c, ctx);
    drawPriceAxis(c, ctx);
    if (F && V.projW) drawProj(c, ctx);
    drawTimeAxis(c, ctx);
    drawLegend(c, ctx);
    if (full) { toolbar(ctx); panelHtml(ctx); }
    else panelMarks();
    showTip(st.hover);
    details(ctx);
    if (st.geo) geoDump(ctx);
    placeNav();
  }
  const hv = () => st.hover || st.pin;

  function drawBoxes(c, ctx) {
    for (const k of ORDER) {
      const s = sess(ctx.D, k, ctx.obs, ctx.live);
      if (s.drH == null || s.status === 'forming' && k !== ctx.s.k) continue;
      const x0 = V.X(s.start), x1 = V.X(s.formed), y0 = V.Y(s.drH), y1 = V.Y(s.drL);
      // box colour (operator 2026-09-29): green / red by the box's close against its open, grey while it forms or is flat;
      // gradient = strongest over the IDR body, fading to the DR wick edges
      const col = s.status === 'forming' || s.close == null || s.close === s.open ? '#8B93A1' : s.close > s.open ? C.up : C.dn;
      const a = cfg.boxA / 100 * (k === ctx.s.k ? 1 : 0.6);
      if (cfg.boxFill === 'none') { c.fillStyle = k === ctx.s.k ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.025)'; }
      else if (cfg.boxFill === 'solid') { c.fillStyle = rgba(col, 0.3 * a); }
      else {
        const g = c.createLinearGradient(0, y0, 0, y1), f = p => Math.min(1, Math.max(0, (V.Y(p) - y0) / Math.max(1, y1 - y0)));
        const ih = f(s.idrH), il = f(s.idrL);
        g.addColorStop(0, rgba(col, 0.06 * a)); g.addColorStop(ih, rgba(col, 0.42 * a)); g.addColorStop((ih + il) / 2, rgba(col, 0.5 * a));
        g.addColorStop(Math.max(ih, il), rgba(col, 0.42 * a)); g.addColorStop(1, rgba(col, 0.06 * a));
        c.fillStyle = g;
      }
      c.fillRect(x0, y0, x1 - x0, y1 - y0);
      c.fillStyle = k === ctx.s.k ? C.text2 : C.text3; c.font = '600 11px ' + FONT; c.textBaseline = 'bottom';
      c.fillText(k, x0 + 2, y0 - 3);
    }
    // the previous trading day's RDR box (09:30-10:30 yesterday), quiet, when its candles are on the screen
    if (PREV && ctx.D.bars.some(b => b.t >= PREV.start && b.t < PREV.formed)) {
      const x0 = V.X(PREV.start), x1 = V.X(PREV.formed), y0 = V.Y(PREV.drH), y1 = V.Y(PREV.drL);
      if (x1 > 0) {
        const col = PREV.close == null || PREV.close === PREV.open ? '#8B93A1' : PREV.close > PREV.open ? C.up : C.dn;
        c.fillStyle = rgba(col, 0.13 * cfg.boxA / 100); c.fillRect(x0, y0, x1 - x0, y1 - y0);
        c.fillStyle = C.text3; c.font = '600 11px ' + FONT; c.textBaseline = 'bottom'; c.fillText(PREV.name, x0 + 2, y0 - 3);
      }
    }
  }
  // operator 2026-10-06: New York midnight as an orange dashed line over the whole height (chart and time band), so the
  // dimmer candles of the previous trading day are clearly set apart; drawn under the candles
  function drawMidnight(c, y0, y1) {
    const x = Math.round(V.X(0)) + 0.5;
    if (x < 0 || x > V.plot.w) return;
    c.save(); c.strokeStyle = rgba('#F29A38', cfg.midnightA / 100); c.lineWidth = 1; c.setLineDash([6, 3, 1, 3]);
    c.beginPath(); c.moveTo(x, y0); c.lineTo(x, y1); c.stroke(); c.restore();
  }
  function prevList(ctx) {
    const i = ORDER.indexOf(ctx.s.k), out = PREV ? [{ k: 'PREV', name: PREV.name, col: C.PREV, s: PREV }] : [];
    for (let j = 0; j < i; j++) { const s = sess(ctx.D, ORDER[j], ctx.obs, ctx.live); if (s.drH != null && s.complete) out.push({ k: ORDER[j], name: ORDER[j], col: C[ORDER[j]], s }); }
    return out;
  }
  // DR and IDR of past sessions: the same white lines as today's (DR solid, IDR dashed), a little dimmer, named at the right
  function drawPrev(c, ctx) {
    const h = hv();
    for (const P of prevList(ctx)) {
      const s = P.s, x0 = Math.max(V.plot.x, V.X(P.k === 'PREV' ? Math.max(st.v0, P.s.start) : SESS[P.k].start)), x1 = V.plot.w;
      if (x1 <= x0) continue;
      for (const [p, type] of [[s.drH, 'dr'], [s.drL, 'dr'], [s.idrH, 'idr'], [s.idrL, 'idr']]) {
        const on = h && h.k === 'prev' && h.id === P.k && Math.abs(h.p - p) < 1e-6, y = Math.round(V.Y(p)) + 0.5;
        c.strokeStyle = type === 'dr' ? rgba(C.dr, on ? 1 : cfg.prevA / 100) : rgba(C.idr, on ? 1 : cfg.prevA / 100 * 0.87);
        c.lineWidth = type === 'dr' ? Math.max(0.6, cfg.drW * 0.75) : Math.max(0.6, cfg.idrW * 0.85); c.setLineDash(type === 'dr' ? [] : DASH[cfg.idrDash] || []);
        c.beginPath(); c.moveTo(x0, y); c.lineTo(x1, y); c.stroke(); c.setLineDash([]);
      }
    }
  }
  function vibsKnown(ctx) {
    const by = ctx.live ? NOW : ctx.obs;
    const min = cfg['vib' + A.inst] || 0;
    return ctx.D.vibs.filter(v => v.t + 5 <= by && v.hi - v.lo >= min - 1e-9).map(v => Object.assign({}, v, { fill: v.fill != null && v.fill + 5 <= by ? v.fill : null }));
  }
  function drawVib(c, ctx) {
    const h = hv();
    for (const v of vibsKnown(ctx)) {
      const x0 = V.X(v.t), x1 = v.fill != null ? V.X(v.fill + 5) : V.plot.w, y0 = V.Y(v.hi), y1 = V.Y(v.lo);
      if (x1 < 0 || x0 > V.plot.w) continue;
      const on = h && h.k === 'vib' && h.t === v.t;
      const vf = cfg.vibA / 20;
      c.fillStyle = rgba(C.vib, Math.min(1, on ? 0.34 * vf : v.fill != null ? 0.12 * vf : 0.2 * vf));
      c.fillRect(x0, y0 - 1, x1 - x0, Math.max(2, y1 - y0 + 2));
      c.fillStyle = rgba(C.vib, Math.min(1, on ? 0.9 : (v.fill != null ? 0.25 : 0.5) * vf));
      c.fillRect(x0, y0 - 1, 1.5, Math.max(2, y1 - y0 + 2));
      // its name inside the rectangle at the right end, only when it fits (operator 2026-10-06)
      const hh = y1 - y0 + 2, xr = Math.min(x1, V.plot.w) - 4;
      if (v.fill == null && hh >= 10 && xr - Math.max(x0, 0) > 22) {
        c.font = '600 ' + Math.min(10, hh - 2).toFixed(1) + 'px ' + FONT; c.fillStyle = rgba(C.vib, 0.95); c.textAlign = 'right'; c.textBaseline = 'middle';
        c.fillText('VI', xr, (y0 + y1) / 2 + 0.5); c.textAlign = 'left';
      }
    }
  }
  // the price of a cell edge k / 10 in today's scale; a band [k0, k1) as a top / bottom pair of screen y
  const cellY = (F, k0, k1) => { const a = V.Y(F.u2p(k0 / 10)), b = V.Y(F.u2p(k1 / 10)); return [Math.min(a, b), Math.max(a, b)]; };
  // «Путь семьи»: one column per common clock M5, one cell per 0.1 SD; colour = the share of N on one fixed linear scale
  // 0…100 % for every column (spec §9.2: no normalisation to a column's or a row's own maximum); passed hours dimmer
  function drawFilm(c, ctx) {
    const F = ctx.F, sl = sliceOf(ctx), h = hv(), f = cfg.heatA / 100, col = cfg.path;
    for (const cd of filmOf(F)) {
      const x0 = V.X(cd.T - 5), x1 = V.X(cd.T);
      if (x1 < 0 || x0 > V.plot.w) continue;
      const past = cd.T <= sl;
      for (const [k, list] of cd.cells) {
        const [ya, yb] = cellY(F, k, k + 1), share = list.length / F.N;
        c.fillStyle = rgba(col, Math.min(1, (0.1 + 0.9 * share) * f * (past ? 0.55 : 1)));
        c.fillRect(x0 + 0.5, ya + 0.5, Math.max(1, x1 - x0 - 1), Math.max(1, yb - ya - 1));
      }
      const on = (h && (h.k === 'col' || h.k === 'fcell') && h.j === cd.j) || (!h && st.col === cd.j);
      if (on) { c.strokeStyle = 'rgba(236,240,246,.8)'; c.lineWidth = 1; c.strokeRect(Math.round(x0) + 0.5, 0.5, Math.max(1, Math.round(x1 - x0) - 1), V.plot.h - 1); }
      if (h && h.k === 'fcell' && h.j === cd.j) { const [ya, yb] = cellY(F, h.kk, h.kk + 1); c.strokeStyle = '#FFFFFF'; c.lineWidth = 1.5; c.strokeRect(x0 + 0.5, ya + 0.5, x1 - x0 - 1, yb - ya - 1); }
    }
  }
  // a hovered price cell or band of the histogram runs across the chart; a hovered time cell runs down to the time axis
  function drawHighlight(c, ctx) {
    const F = ctx.F, h = hv();
    if (!h) return;
    const col = cfg[h.ev || st.ev];
    if (h.k === 'pcell') {
      const [ya, yb] = cellY(F, h.k0, h.k1);
      c.fillStyle = rgba(col, 0.09); c.fillRect(0, ya, V.plot.w, Math.max(1, yb - ya));
      c.strokeStyle = rgba(col, 0.5); c.setLineDash([3, 3]); c.lineWidth = 1;
      c.beginPath(); c.moveTo(0, Math.round(ya) + 0.5); c.lineTo(V.plot.w, Math.round(ya) + 0.5); c.moveTo(0, Math.round(yb) + 0.5); c.lineTo(V.plot.w, Math.round(yb) + 0.5); c.stroke(); c.setLineDash([]);
      V.win = { t0: null, t1: null, pA: F.u2p(h.k0 / 10), pB: F.u2p(h.k1 / 10), col };
    }
    if (h.k === 'tcell') {
      const x0 = V.X(F.f + 15 * h.b0), x1 = V.X(F.f + 15 * h.b1);
      c.fillStyle = 'rgba(209,212,220,.05)'; c.fillRect(x0, 0, x1 - x0, V.plot.h);
      V.win = { t0: F.f + 15 * h.b0, t1: F.f + 15 * h.b1, pA: null, pB: null, col: '#C9CDD4' };
    }
  }
  function drawLevels(c, ctx) {
    const s = ctx.s;
    if (s.drH == null) return;
    const x0 = V.X(s.start), x1 = V.plot.w, h = hv();
    if (x1 <= x0) return;
    const play = s.status === 'broken' || (s.status === 'done' && s.failed) ? s.nside : s.side || 0;
    const line = (p, col, a, w, dash) => { const y = Math.round(V.Y(p)) + 0.5; c.strokeStyle = rgba(col, a); c.lineWidth = w; c.setLineDash(dash); c.beginPath(); c.moveTo(Math.max(x0, 0), y); c.lineTo(x1, y); c.stroke(); c.setLineDash([]); };
    for (const l of levels(s)) {
      const on = h && h.k === 'lvl' && h.id === l.id;
      if (l.type === 'std') {
        if (!stdShown(s, l)) continue;
        const inPlay = play === l.dir, ss = stdState(s, l);
        if (ss === 'taken') { c.lineCap = 'round'; line(l.p, C.std, on ? 1 : 0.5 * cfg.stdA / 100, 1.6, [0.1, 4.5]); c.lineCap = 'butt'; }
        else if (ss === 'next') line(l.p, mixW(C.stdOn, 0.35), on ? 1 : Math.min(1, 1.25 * cfg.stdA / 100), 1.6, []);
        else if (ss === 'far') line(l.p, C.std, on ? 1 : 0.6 * cfg.stdA / 100, 1, []);
        else line(l.p, C.std, on ? 1 : (inPlay ? cfg.stdA : cfg.stdOffA) / 100, 1, []);
      } else if (l.type === 'dr') line(l.p, sideCol(s, C.dr), on ? 1 : cfg.drA / 100, +cfg.drW, []);
      else if (l.type === 'idr') line(l.p, sideCol(s, C.idr), on ? 1 : cfg.idrA / 100, +cfg.idrW, DASH[cfg.idrDash] || []);
      else if (l.type === 'mid') line(l.p, C.mid, on ? 1 : cfg.midA / 100, 1.2, DASH[cfg.midDash] || []);
      else if (l.type === 'open') line(l.p, C.open, on ? 0.9 : 0.5, 1, [1, 6]);
    }
    // the IDR fractions inside the box (0,1 ... 0,9 of the IDR), as in the Pine indicator; operator 2026-10-06: a thin line
    // for each over the box only (box start .. box end), the 0,5 (the IDR mid) clearly stronger
    const w = s.idrH - s.idrL, xb = V.X(s.start) - 4, bx0 = V.X(s.start), bx1 = V.X(s.formed), hpx = w * V.plot.h / (V.p1 - V.p0);
    if (hpx > 30 && bx1 > bx0) for (let j = 1; j <= 9; j++) {
      const y = Math.round(V.Y(s.idrL + j * w / 10)) + 0.5;
      c.strokeStyle = j === 5 ? rgba(C.mid, 0.85) : rgba('#D1D4DC', cfg.fracLine / 100); c.lineWidth = j === 5 ? 1.4 : 1;
      c.beginPath(); c.moveTo(Math.max(bx0, 0), y); c.lineTo(bx1, y); c.stroke();
    }
    c.textBaseline = 'middle'; c.textAlign = 'right';
    if (hpx > 90) for (let j = 1; j <= 9; j++) {
      c.font = (j === 5 ? '700 ' + (cfg.fracLbl + 1) + 'px ' : cfg.fracLbl + 'px ') + FONT; c.fillStyle = j === 5 ? C.mid : C.text3;   // small (operator 2026-10-06)
      c.fillText(num(j / 10, 1), xb, V.Y(s.idrL + j * w / 10));
    }
    c.textAlign = 'left';
  }
  function brightLine(c, p, text) {
    const y = Math.round(V.Y(p)) + 0.5;
    c.strokeStyle = 'rgba(246,248,252,.95)'; c.lineWidth = 2; c.setLineDash([]);
    c.beginPath(); c.moveTo(0, y); c.lineTo(V.plot.w, y); c.stroke();
    if (text) {
      c.font = '700 12px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'right';
      const w = c.measureText(text).width + 10, xr = V.plot.w - 8;
      c.fillStyle = '#F4F6FA'; roundRect(c, xr - w, y - 9, w, 18, 3); c.fill();
      c.fillStyle = '#0B0C10'; c.fillText(text, xr - 5, y + 0.5); c.textAlign = 'left';
    }
  }
  // the lit level (hover or pin): a bright line; its numbers are in the tooltip and the panel
  function drawReference(c, ctx) {
    const h = hv();
    if (!h) return;
    if (h.k === 'lvl' && h.l) brightLine(c, h.l.p, null);          // its name and price stand on the price scale
    else if (h.k === 'prev') brightLine(c, h.p, null);
  }
  // the chosen history session: its own path (M5 ranges and closes, in its own IDR units carried to today's scale, at
  // its real clock), its activation and its break; R and X are marked by drawPair. No arrow joins R and X (spec §8).
  function pinnedMember(ctx) { const h = hv(); return h && h.k === 'pt' && ctx.F ? ctx.F.M[h.i] : null; }
  function drawMemberPath(c, ctx) {
    const F = ctx.F, m = pinnedMember(ctx);
    if (!m) return;
    const col = cfg[st.ev];
    c.save();
    let first = true;
    c.beginPath();
    F.grid.forEach((T, j) => {
      const q = m.path[j];
      if (!q) { first = true; return; }
      const x = V.X(T - 2.5), y = V.Y(F.u2p(q[2] / m.w));
      if (first) { c.moveTo(x, y); first = false; } else c.lineTo(x, y);
    });
    c.strokeStyle = rgba('#ECF0F6', Math.min(1, 0.4 * cfg.pathA / 100)); c.lineWidth = 1; c.stroke();
    F.grid.forEach((T, j) => {
      const q = m.path[j];
      if (!q) return;
      const x = Math.round(V.X(T - 2.5)) + 0.5, ya = V.Y(F.u2p(q[0] / m.w)), yb = V.Y(F.u2p(q[1] / m.w));
      // the session's M5 ranges: a quiet trace (operator 2026-10-06: they must not pull the eye off today's candles)
      c.strokeStyle = rgba('#ECF0F6', Math.min(1, (T <= m.act ? 0.06 : 0.14) * cfg.pathA / 100)); c.lineWidth = 1;
      c.beginPath(); c.moveTo(x, Math.min(ya, yb)); c.lineTo(x, Math.max(ya, yb)); c.stroke();
    });
    const tag = (T, text, bg) => { const x = V.X(T - 2.5); c.font = '600 10.5px ' + FONT; const w = c.measureText(text).width + 8; c.fillStyle = bg; roundRect(c, x - w / 2, 70, w, 16, 3); c.fill(); c.fillStyle = '#0B0C10'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, x, 78.5); c.textAlign = 'left'; };
    tag(m.act, (F.brk ? 'слом ' : 'подтв. ') + clk(m.act), 'rgba(236,240,246,.85)');
    if (!F.brk && m.brk != null) tag(m.brk, 'слом DR ' + clk(m.brk), 'rgba(242,54,69,.9)');
    c.restore();
    void col;
  }
  // today's candles; after the slice (replay) shown faint, never used
  function drawCandles(c, ctx) {
    const bw = bodyW(V.bs), used = ctx.live ? NOW : ctx.obs;
    for (const b of ctx.D.bars) {
      const cx = Math.round(V.X(b.t + 2.5));
      if (cx < -bw || cx > V.plot.w + bw) continue;
      const future = !ctx.live && b.t + 5 > used;
      // operator 2026-10-06: the previous trading day's candles (before New York midnight) are context, drawn dimmer
      const col = b.c >= b.o ? C.up : C.dn, a = (future ? 0.22 : 1) * (b.t < 0 ? cfg.prevDayA / 100 : 1);
      c.fillStyle = rgba(col, a);
      const yh = V.Y(b.h), yl = V.Y(b.l), yo = V.Y(b.o), yc = V.Y(b.c);
      c.fillRect(cx, yh, 1, Math.max(1, yl - yh));
      c.fillRect(cx - (bw - 1) / 2, Math.min(yo, yc), bw, Math.max(1, Math.abs(yo - yc)));
    }
  }
  function pill(c, x, y, text, bg, fg, up) {
    c.font = '600 11px ' + FONT;
    const w = c.measureText(text).width + 12, h = 18, yy = up ? y - h - 6 : y + 6;
    c.fillStyle = bg; roundRect(c, x - w / 2, yy, w, h, 4); c.fill();
    c.fillStyle = fg; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, x, yy + h / 2 + 0.5); c.textAlign = 'left';
  }
  function roundRect(c, x, y, w, h, r) { c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath(); }
  function drawPills(c, ctx) {
    for (const k of ORDER) {
      const s = sess(ctx.D, k, ctx.obs, ctx.live);
      if (!s.conf) continue;
      const b = ctx.D.bars.find(q => q.t === s.conf - 5);
      if (b) pill(c, V.X(b.t + 2.5), s.side === 1 ? V.Y(b.h) : V.Y(b.l), (s.side === 1 ? '↑ ' : '↓ ') + clk(s.conf), k === ctx.s.k ? 'rgba(8,153,129,.9)' : 'rgba(80,88,100,.8)', '#fff', s.side === 1);
      if (s.failed) { const q = ctx.D.bars.find(z => z.t === s.failed - 5); if (q) pill(c, V.X(q.t + 2.5), s.side === 1 ? V.Y(q.l) : V.Y(q.h), 'Слом DR ' + (s.side === 1 ? '↓ ' : '↑ ') + clk(s.failed), 'rgba(159,29,36,.95)', '#fff', s.side !== 1); }
    }
  }
  function drawNow(c, ctx) {
    const E = SESS[ctx.s.k].end;
    if (ctx.F) {
      const xe = Math.round(V.X(E)) + 0.5;
      c.strokeStyle = 'rgba(255,255,255,.12)'; c.setLineDash([2, 5]); c.lineWidth = 1;
      c.beginPath(); c.moveTo(xe, 0); c.lineTo(xe, V.plot.h); c.stroke(); c.setLineDash([]);
      // the text «конец <session> HH:MM» removed (operator 2026-10-06): the dotted line says it
    }
    const x = Math.round(V.X(ctx.obs)) + 0.5;
    c.strokeStyle = ctx.live && !ctx.D.hist ? 'rgba(255,255,255,.14)' : rgba(ctx.D.hist ? C.hist : C.replay, 0.55); c.setLineDash([3, 4]); c.lineWidth = 1;
    c.beginPath(); c.moveTo(x, 0); c.lineTo(x, V.plot.h); c.stroke(); c.setLineDash([]);
  }
  // does a point take part in what is hovered / pinned / selected? true = lit, false = dimmed, null = neutral
  function emphOf(q, h, F, ctx) {
    if (h) {
      if (h.k === 'pcell') return (!h.ev || h.ev === q.ev) && q.k >= h.k0 && q.k < h.k1;
      if (h.k === 'tcell') return q.b >= h.b0 && q.b < h.b1;
      if (h.k === 'area') return inArea(q, st.area);
      if (h.k === 'zone') return h.ev === q.ev && F.zcell[h.ev].get(q.k + '|' + q.b) === h.i;
      if (h.k === 'pt') return q.i === h.i;
      if (h.k === 'out') return q.m.outcome === h.cat;
      if (h.k === 'evrow') return true;
      if (h.k === 'hcell') return h.ev === q.ev && q.k === h.kk && q.b === h.b;
      if (h.k === 'order') { const o = q.m.order; return h.key === 'unknown' ? !['X_before_R', 'R_before_X', 'same_M5'].includes(o) : o === h.key; }
      if (h.k === 'lvl' && h.l && ctx) { const L = levelRat(F, h.l.p), up = levelUp(F, ctx, L); return reachOne(F, q.m, L, up, q.m.act) === 'yes'; }
    }
    if (st.area) return inArea(q, st.area) ? true : null;
    return null;
  }
  const inArea = (q, a) => !!a && (!a.ev || a.ev === q.ev) && q.k >= a.k0 && q.k < a.k1 && (a.b0 == null || (q.b >= a.b0 && q.b < a.b1));
  // one point = one session's event (spec §7): no jitter; points on the same spot stay on it (their weight adds up in
  // brightness, the tooltip lists every session). A ring = that session broke its DR (the family is never thinned by it).
  // R and X together; the stars of a zone are brighter and a little larger than the residual ones
  function drawPoints(c, ctx) {
    const F = ctx.F, sl = sliceOf(ctx), h = hv(), R0 = 1.7 * cfg.ptSize / 100;
    for (const ev of ['R', 'X']) {
      const col0 = cfg[ev], look = F.zones[ev] ? zoneLook(F, ctx, ev) : [], spent = stateCol(col0, 'spent');
      for (const q of F.ev[ev].pts) {
        const zi = F.zcell[ev].get(q.k + '|' + q.b), col = zi != null && look[zi] === 'IMPOSSIBLE' ? spent : col0;
        const x = V.X(q.t + 2.5), y = V.Y(q.p);
        if (x < -4 || x > V.plot.w + 4 || y < -4 || y > V.plot.h + 4) continue;
        const past = q.t + 5 <= sl, e = emphOf(q, h, F, ctx), inZone = F.zcell[ev].has(q.k + '|' + q.b);
        let a = (past ? cfg.pastA : cfg.ptA) / 100 * (inZone ? 1.1 : 0.62), r = R0 * (inZone ? 1 : 0.8);
        if (e === true) { a = Math.min(1, Math.max(a, 0.55) + 0.3); r = R0 * 1.3; } else if (e === false) a *= 0.28;
        a = Math.min(1, a);
        if (!F.brk && q.m.outcome === 'broken') { c.strokeStyle = rgba(col, a); c.lineWidth = 1; c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.stroke(); }
        else { c.fillStyle = rgba(col, a); c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.fill(); }
      }
    }
  }
  // the chosen session's paired event: its R and X both marked and named (spec §8 «парная точка»)
  function drawPair(c, ctx) {
    const F = ctx.F, m = pinnedMember(ctx);
    if (!m) return;
    for (const ev of ['R', 'X']) {
      const e = m[ev];
      if (e.s !== 'known') continue;
      const x = V.X(e.t + 2.5), y = V.Y(F.u2p(e.v / m.w)), col = cfg[ev];
      c.strokeStyle = col; c.lineWidth = 1.6; c.beginPath(); c.arc(x, y, 6, 0, 6.2832); c.stroke();
      c.font = '700 11px ' + FONT; c.fillStyle = col; c.textBaseline = 'middle'; c.fillText(ev, x + 9, y + 0.5);
    }
  }
  // ---------- constellations (operator 2026-10-01: «дымка и нити», amber R and sky X) ----------
  // A zone of zone-map-3 is its exact region of cells; its sessions are the points in those cells. The constellation is a
  // drawing of those points only: their density in screen space (a Gaussian of 18 px), filled softly at 0.22 and 0.6 of
  // its own peak (blurred), the thinnest lines of the shortest tree joining its stars, and on hover the 0.35 iso-line
  // and the exact cells. It carries no number of its own: the zone's share is n / N of its cells (zonePass).
  function kde(pts, sig) {
    const step = 4, xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    const x0 = Math.min(...xs) - 3 * sig, y0 = Math.min(...ys) - 3 * sig;
    const nx = Math.ceil((Math.max(...xs) + 3 * sig - x0) / step) + 1, ny = Math.ceil((Math.max(...ys) + 3 * sig - y0) / step) + 1, gv = new Float64Array(nx * ny);
    let mx = 0, mi = 0;
    for (let iy = 0; iy < ny; iy++) for (let ix = 0; ix < nx; ix++) {
      const gx = x0 + ix * step, gy = y0 + iy * step;
      let s = 0;
      for (const p of pts) { const dx = gx - p[0], dy = gy - p[1]; s += Math.exp(-(dx * dx + dy * dy) / (2 * sig * sig)); }
      gv[iy * nx + ix] = s;
      if (s > mx) { mx = s; mi = iy * nx + ix; }
    }
    return { step, x0, y0, nx, ny, gv, mx, spot: { x: x0 + (mi % nx) * step, y: y0 + Math.floor(mi / nx) * step } };
  }
  // the iso-lines of a density at a fraction of its peak: marching squares, chained into closed loops, smoothed twice
  function iso(G, frac) {
    const L = G.mx * frac, nx = G.nx, step = G.step, v = (ix, iy) => G.gv[iy * nx + ix], P = {}, adj = {};
    const link = (a, b) => { (adj[a] = adj[a] || []).push(b); (adj[b] = adj[b] || []).push(a); };
    for (let iy = 0; iy < G.ny - 1; iy++) for (let ix = 0; ix < nx - 1; ix++) {
      const a = v(ix, iy), b = v(ix + 1, iy), c = v(ix + 1, iy + 1), d = v(ix, iy + 1);
      const idx = (a >= L ? 8 : 0) | (b >= L ? 4 : 0) | (c >= L ? 2 : 0) | (d >= L ? 1 : 0);
      if (idx === 0 || idx === 15) continue;
      const X0 = G.x0 + ix * step, Y0 = G.y0 + iy * step, T = 'h' + ix + ',' + iy, B = 'h' + ix + ',' + (iy + 1), Lf = 'v' + ix + ',' + iy, R = 'v' + (ix + 1) + ',' + iy;
      P[T] = [X0 + step * (L - a) / (b - a), Y0]; P[B] = [X0 + step * (L - d) / (c - d), Y0 + step];
      P[Lf] = [X0, Y0 + step * (L - a) / (d - a)]; P[R] = [X0 + step, Y0 + step * (L - b) / (c - b)];
      const E = { 1: [[Lf, B]], 2: [[B, R]], 3: [[Lf, R]], 4: [[T, R]], 5: [[Lf, T], [B, R]], 6: [[T, B]], 7: [[Lf, T]], 8: [[Lf, T]], 9: [[T, B]], 10: [[T, R], [Lf, B]], 11: [[T, R]], 12: [[Lf, R]], 13: [[B, R]], 14: [[Lf, B]] }[idx];
      for (const e of E) link(e[0], e[1]);
    }
    const seen = {}, loops = [];
    for (const k0 in adj) {
      if (seen[k0]) continue;
      const loop = [];
      let prev = null, cur = k0;
      while (cur && !seen[cur]) { seen[cur] = 1; loop.push(P[cur]); const nb = adj[cur].filter(k => k !== prev && !seen[k]); prev = cur; cur = nb[0]; }
      if (loop.length > 6) loops.push(loop);
    }
    return loops.map(lp => {
      let a = lp;
      for (let it = 0; it < 2; it++) { const o = []; for (let i = 0; i < a.length; i++) { const p = a[i], q = a[(i + 1) % a.length]; o.push([0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]], [0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]]); } a = o; }
      return a;
    });
  }
  // the shortest tree joining the stars of a zone (Prim): the «нити»
  function mst(pts) {
    const inT = [0], segs = [];
    while (inT.length < pts.length) {
      let best = null;
      for (const i of inT) for (let j = 0; j < pts.length; j++) { if (inT.includes(j)) continue; const d = Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]); if (!best || d < best[2]) best = [i, j, d]; }
      inT.push(best[1]); segs.push([pts[best[0]][0], pts[best[0]][1], pts[best[1]][0], pts[best[1]][1]]);
    }
    return segs;
  }
  const loopsPath = (c, loops) => { c.beginPath(); for (const L of loops) { c.moveTo(L[0][0], L[0][1]); for (let i = 1; i < L.length; i++) c.lineTo(L[i][0], L[i][1]); c.closePath(); } };
  function inLoops(loops, x, y) {
    let inside = false;
    for (const L of loops) for (let i = 0, j = L.length - 1; i < L.length; j = i++) { const a = L[i], b = L[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside; }
    return inside;
  }
  // the zones' geometry in this frame's screen space (cached until the view moves); per zone: its points, density, fills,
  // iso-lines, threads, its peak 15 minutes (the time cell holding most of its sessions) and its box
  function cloudsOf(F) {
    const key = [V.plot.w, V.plot.h, st.v0, st.v1, V.p0, V.p1].map(v => Math.round(v * 100)).join('|');
    if (F._cl && F._cl.key === key) return F._cl;
    const out = { key, R: [], X: [] };
    for (const ev of ['R', 'X']) {
      const Zm = F.zones[ev];
      if (!Zm) continue;
      Zm.zones.forEach((z, i) => {
        const pts = F.ev[ev].pts.filter(q => F.zcell[ev].get(q.k + '|' + q.b) === i).map(q => [V.X(q.t + 2.5), V.Y(q.p), q.b]);
        if (!pts.length) { out[ev].push(null); return; }
        const kd = kde(pts, 18), pb = new Map();
        for (const p of pts) pb.set(p[2], (pb.get(p[2]) || 0) + 1);
        let peak = null;
        for (const [b, n] of pb) if (peak == null || n > pb.get(peak) || (n === pb.get(peak) && b < peak)) peak = b;
        out[ev].push({ z, i, pts, kd, g1: iso(kd, 0.22), g2: iso(kd, 0.6), hit: iso(kd, 0.2), ln: iso(kd, 0.35), mst: mst(pts), peak, peakN: pb.get(peak),
          bb: [Math.min(...pts.map(p => p[0])), Math.min(...pts.map(p => p[1])), Math.max(...pts.map(p => p[0])), Math.max(...pts.map(p => p[1]))] });
      });
    }
    return (F._cl = out);
  }
  // how strongly a zone is drawn for what is hovered: the hovered zone stronger, the others quieter
  function cloudK(F, ev, i, h, z) {
    if (!h) return 1;
    if (h.k === 'zone') return h.ev === ev && h.i === i ? 1.5 : 0.45;
    if (h.k === 'pt') return 0.6;
    if (h.k === 'pcell') return h.ev === ev && z.cell_mask.some(([k]) => k >= h.k0 && k < h.k1) ? 1.15 : 0.6;
    if (h.k === 'tcell') return z.cell_mask.some(([, b]) => b >= h.b0 && b < h.b1) ? 1.1 : 0.55;
    return 0.8;
  }
  function drawClouds(c, ctx) {
    const F = ctx.F, CL = cloudsOf(F), h = hv(), fa = cfg.cloudA / 100, ta = cfg.threadA / 100;
    for (const ev of ['R', 'X']) {
      const S = zoneLook(F, ctx, ev), col0 = cfg[ev];
      CL[ev].forEach((g, i) => {
        if (!g) return;
        const col = stateCol(col0, S[i]);
        // a spent constellation stays readable as history (operator 2026-10-06: «чуть-чуть ярче»), setting «spentA»
        const k = cloudK(F, ev, i, h, g.z), dim = S[i] === 'IMPOSSIBLE' ? 0.6 * cfg.spentA / 100 : S[i] === 'HOLDS' ? 1.15 : 1;
        c.save();
        c.filter = 'blur(14px)'; c.fillStyle = rgba(col, Math.min(0.5, 0.17 * k * dim * fa)); loopsPath(c, g.g1); c.fill();
        c.filter = 'blur(7px)'; c.fillStyle = rgba(col, Math.min(0.45, 0.13 * k * dim * fa)); loopsPath(c, g.g2); c.fill();
        c.filter = 'none';
        c.strokeStyle = rgba(col, Math.min(0.35, 0.13 * k * dim * ta)); c.lineWidth = 0.5;
        c.beginPath(); for (const s of g.mst) { c.moveTo(s[0], s[1]); c.lineTo(s[2], s[3]); } c.stroke();
        c.restore();
      });
    }
  }
  // the link (operator 2026-10-01): hovering a zone or a price band runs from the densest spot of that cluster straight
  // down to its peak 15 minutes (the time cell holding most of its sessions), lit to the time axis in one move
  // the time the hovered zone or price band points at (operator 2026-10-06; audit 2026-10-06): the peak 15 minutes among
  // the family's events that are still AHEAD by the same rule as the column (their M5 closes after the slice, t + 5 > s)
  // AND sit in a cell today's path still allows (reachOf); if there are none, the past peak, drawn red: that has
  // already happened or can no longer happen today. qs = the family's points {k, b, t, p}; yc = a fixed y (a band)
  function peakAhead(F, ctx, qs, ev, yc) {
    const Rch = reachOf(F, ctx), ahead = qs.filter(q => q.t + 5 > Rch.sl && Rch.okCell(ev, q.k, q.b));
    const past = !ahead.length, use = past ? qs : ahead, cnt = new Map();
    for (const q of use) cnt.set(q.b, (cnt.get(q.b) || 0) + 1);
    let b = null;
    for (const [bb, n] of cnt) if (b == null || n > cnt.get(b) || (n === cnt.get(b) && bb < b)) b = bb;
    if (b == null) return null;
    const ps = use.filter(q => q.b === b);
    return { b, n: cnt.get(b), past, x: ps.reduce((a, q) => a + V.X(q.t + 2.5), 0) / ps.length, y: yc != null ? yc : ps.reduce((a, q) => a + V.Y(q.p), 0) / ps.length };
  }
  function linkOf(ctx) {
    const F = ctx.F, h = hv();
    V.lk = null;
    if (!F || st.mode !== 'bounds' || !h) return;
    if (h.k === 'zone' && h.ev) {
      const pk = peakAhead(F, ctx, F.ev[h.ev].pts.filter(q => F.zcell[h.ev].get(q.k + '|' + q.b) === h.i), h.ev);
      if (pk) V.lk = { ev: h.ev, x: pk.x, y: pk.y, b: pk.b, n: pk.n, past: pk.past };
    } else if (h.k === 'pcell' && h.ev) {
      const yc = (V.Y(F.u2p(h.k0 / 10)) + V.Y(F.u2p(h.k1 / 10))) / 2;
      const pk = peakAhead(F, ctx, F.ev[h.ev].pts.filter(q => q.k >= h.k0 && q.k < h.k1), h.ev, yc);
      if (pk) V.lk = { ev: h.ev, x: pk.x, y: yc, b: pk.b, n: pk.n, past: pk.past };
    }
    if (V.lk) { const t0 = F.f + 15 * V.lk.b; V.win = Object.assign({ pA: null, pB: null }, V.win || {}, { t0, t1: t0 + 15, col: V.lk.past ? '#F23645' : cfg[V.lk.ev] }); }
  }
  // a cell of the six windows under the mouse, framed on the main chart: its price band × its time (operator 2026-10-06)
  function drawMini(c, ctx) {
    const m = st.mini, F = ctx.F, [ya, yb] = cellY(F, m.k0, m.k1), xa = V.X(m.t0), xb = V.X(m.t1);
    c.save(); c.fillStyle = rgba(m.col, 0.16); c.fillRect(xa, ya, xb - xa, yb - ya);
    c.strokeStyle = rgba(m.col, 0.95); c.lineWidth = 1.5; c.strokeRect(Math.round(xa) + 0.5, Math.round(ya) + 0.5, Math.max(2, xb - xa - 1), Math.max(2, yb - ya - 1));
    c.restore();
  }
  function drawLink(c, ctx) {
    const lk = V.lk;
    if (!lk) return;
    const F = ctx.F, col = lk.past ? '#F23645' : cfg[lk.ev], t0 = F.f + 15 * lk.b, xa = V.X(t0), xb = V.X(t0 + 15), yb = V.plot.h;
    const g = c.createLinearGradient(0, lk.y, 0, yb);
    g.addColorStop(0, rgba(col, 0.03)); g.addColorStop(1, rgba(col, 0.15));
    c.fillStyle = g; c.fillRect(xa, lk.y, xb - xa, yb - lk.y);
    c.strokeStyle = rgba(col, 0.45); c.lineWidth = 1; c.setLineDash([3, 3]);
    c.beginPath(); for (const x of [xa, xb]) { c.moveTo(Math.round(x) + 0.5, lk.y); c.lineTo(Math.round(x) + 0.5, yb); } c.stroke(); c.setLineDash([]);
    c.save(); c.shadowColor = rgba(col, 0.7); c.shadowBlur = 8; c.strokeStyle = col; c.lineWidth = 1.6;
    c.beginPath(); c.arc(lk.x, lk.y, 7, 0, 6.2832); c.stroke(); c.restore();
  }
  // the selected area (spec §7.1): the bracket right of the block end spans the WHOLE price band and carries the band's
  // share of the event; a band x time window is a frame carrying its own joint share; a time window is a column
  function drawArea(c, ctx) {
    const F = ctx.F, a = st.area || (st.drag && st.drag.area);
    V.areaHit = null;
    if (!a) return;
    const col = st.mode === 'path' ? '#E6EAF0' : cfg[a.ev || st.ev], live = st.drag && st.drag.area === a;
    const xE = Math.min(V.X(F.end) + 8, V.plot.w - 64);
    const hasBand = isFinite(a.k0);
    const x0 = a.b0 != null ? V.X(F.f + 15 * a.b0) : V.X(F.f), x1 = a.b0 != null ? V.X(F.f + 15 * a.b1) : V.X(F.end);
    let ya = 0, yb = V.plot.h;
    if (hasBand) [ya, yb] = cellY(F, a.k0, a.k1);
    c.save();
    c.fillStyle = rgba(col, 0.06); c.fillRect(x0, ya, x1 - x0, yb - ya);
    c.strokeStyle = rgba(col, 0.9); c.lineWidth = 1; c.setLineDash(live ? [4, 3] : []);
    if (a.b0 != null && hasBand) c.strokeRect(Math.round(x0) + 0.5, Math.round(ya) + 0.5, Math.round(x1 - x0), Math.round(yb - ya));
    else if (hasBand) { c.beginPath(); for (const y of [ya, yb]) { c.moveTo(x0, Math.round(y) + 0.5); c.lineTo(x1, Math.round(y) + 0.5); } c.stroke(); }
    else { c.beginPath(); for (const x of [x0, x1]) { c.moveTo(Math.round(x) + 0.5, 0); c.lineTo(Math.round(x) + 0.5, V.plot.h); } c.stroke(); }
    c.setLineDash([]);
    if (st.mode === 'bounds' && !live) {
      const N = F.N, ev = a.ev || st.ev;
      c.font = '700 13px ' + FONT; c.textBaseline = 'middle';
      if (hasBand) {
        // the bracket of the whole band
        const x = Math.round(xE) + 0.5, top = Math.max(1, ya), bot = Math.min(V.plot.h - 1, yb);
        c.strokeStyle = rgba(col, 0.9); c.lineWidth = 1.2;
        c.beginPath(); c.moveTo(x, top); c.lineTo(x, bot); c.moveTo(x - 4, top); c.lineTo(x, top); c.moveTo(x - 4, bot); c.lineTo(x, bot); c.stroke();
        const nb = areaCount(F, ev, { k0: a.k0, k1: a.k1 }), tb = pct(100 * nb / N), yl = clamp((top + bot) / 2, 10, V.plot.h - 10);
        c.fillStyle = '#FFFFFF'; c.fillText(tb, x + 5, yl);
        V.areaHit = [{ box: [x - 6, top, c.measureText(tb).width + 14, Math.max(12, bot - top)], part: 'band' }];
      }
      if (a.b0 != null) {
        const nr = areaCount(F, ev, a), tr = pct(100 * nr / N), w = c.measureText(tr).width;
        const lx = clamp(x1 - w - 4, x0 + 2, V.plot.w - w - 4), ly = hasBand ? Math.max(10, ya - 9) : 12;
        c.fillStyle = 'rgba(8,9,12,.8)'; c.fillRect(lx - 3, ly - 8, w + 6, 16);
        c.fillStyle = col; c.fillText(tr, lx, ly + 0.5);
        (V.areaHit = V.areaHit || []).push({ box: [lx - 3, ly - 8, w + 6, 16], part: 'window' }, { box: [x0, ya, x1 - x0, yb - ya], part: 'frame' });
      }
    }
    c.restore();
  }
  // the zone map of R and X (zone-map-3) on the chart: each zone's label (its share of the family, in a size that follows
  // the share; a zone that can no longer hold today shows its name only, with a dashed iso-line) and, on hover or pin,
  // its iso-line and its exact cells. The share is the family's (n / N of its cells), never a chance for today.
  function drawZones(c, ctx) {
    const F = ctx.F;
    V.zoneHit = null;
    if (!st.L.zones || st.mode !== 'bounds') return;
    const CL = cloudsOf(F), h = hv(), placed = [], used = ctx.live ? NOW + 5 : ctx.obs;
    const bars = ctx.D.bars.filter(b => b.t + 5 <= used && V.X(b.t + 5) > 0 && V.X(b.t) < V.plot.w).map(b => [V.X(b.t) - 2, V.Y(b.h) - 2, V.X(b.t + 5) + 2, V.Y(b.l) + 2]);
    const over = (a, b) => a[0] < b[2] && a[2] > b[0] && a[1] < b[3] && a[3] > b[1];
    V.zoneHit = [];
    for (const ev of ['X', 'R']) {
      const S = zoneLook(F, ctx, ev), col0 = cfg[ev];
      CL[ev].forEach((g, i) => {
        if (!g) return;
        const col = stateCol(col0, S[i]);
        const z = g.z, s = S[i], imp = s === 'IMPOSSIBLE', on = !!(h && h.k === 'zone' && h.ev === ev && h.i === i);
        if (on || imp) { c.save(); c.strokeStyle = rgba(col, on ? 0.6 : 0.3); c.lineWidth = 1; c.setLineDash(imp ? [4, 3] : []); loopsPath(c, g.ln); c.stroke(); c.restore(); }
        if (on) {
          // the zone itself: its exact region of cells, quietly (the constellation is only its drawing)
          const set = new Set(z.cell_mask.map(([k, b]) => k + '|' + b)), up = F.u2p(0.1) > F.u2p(0);
          c.save(); c.strokeStyle = rgba(col, 0.32); c.lineWidth = 1; c.setLineDash([1.5, 2.5]); c.beginPath();
          for (const [k, b] of z.cell_mask) {
            const x0 = Math.round(V.X(F.f + 15 * b)) + 0.5, x1 = Math.round(V.X(F.f + 15 * b + 15)) + 0.5, [ya0, yb0] = cellY(F, k, k + 1), ya = Math.round(ya0) + 0.5, yb = Math.round(yb0) + 0.5;
            if (!set.has((up ? k + 1 : k - 1) + '|' + b)) { c.moveTo(x0, ya); c.lineTo(x1, ya); }
            if (!set.has((up ? k - 1 : k + 1) + '|' + b)) { c.moveTo(x0, yb); c.lineTo(x1, yb); }
            if (!set.has(k + '|' + (b - 1))) { c.moveTo(x0, ya); c.lineTo(x0, yb); }
            if (!set.has(k + '|' + (b + 1))) { c.moveTo(x1, ya); c.lineTo(x1, yb); }
          }
          c.stroke(); c.restore();
        }
        // Historical mass and today's applicability are separate encodings: status may dim/dash a zone, but never
        // removes or resizes its n/N label. This prevents p_snapshot from looking like today's conditional chance.
        // a spent zone's label (operator 2026-10-06): 20 % smaller, not bold, translucent, its plate almost clear, so what lies
        // under it on the chart (a VI, candles) stays visible
        const share = 100 * z.p_snapshot, fs = Math.round(clamp(12 + 0.45 * share, 15, 21) * cfg.zoneLbl / 100 * (imp ? 0.8 : 1)), sub = s === 'HOLDS' ? 'держится' : '', lw = imp ? '500 ' : '700 ', nfs = imp ? 10 : 12;
        c.font = lw + nfs + 'px ' + FONT;
        const wN = c.measureText(z.label).width;
        c.font = '700 ' + fs + 'px ' + FONT;
        const wS = pctW(c, pct(share), lw, fs), wT = wN + 5 + wS + 10, hT = fs + 8 + (sub ? 13 : 0), bb = g.bb;
        const cands = [[bb[2] - wT + 6, bb[1] - hT - 6], [bb[2] + 10, (bb[1] + bb[3]) / 2 - hT / 2], [bb[2] - wT + 6, bb[3] + 6], [bb[0] - 6, bb[1] - hT - 6], [bb[0] - wT - 10, (bb[1] + bb[3]) / 2 - hT / 2]];
        let best = null;
        for (const q of cands) {
          const r = [q[0], q[1], q[0] + wT, q[1] + hT];
          if (r[1] < 44 || r[3] > V.plot.h - 6 || r[0] < 4 || r[2] > V.plot.w - 112) continue;   // clear of the line names at the right edge
          if (bars.some(b => over(r, b)) || placed.some(b => over(r, b))) continue;
          best = q; break;
        }
        if (!best) best = [clamp(cands[0][0], 4, V.plot.w - wT - 112), clamp(cands[0][1], 44, V.plot.h - hT - 6)];
        const [lx, ly] = best, k = cloudK(F, ev, i, h, z), op = k < 1 ? 0.4 + 0.5 * k : 1;
        placed.push([lx, ly, lx + wT, ly + hT]);
        c.save(); c.globalAlpha = op;
        // no plate under a zone's label (operator 2026-10-06): the text alone, with a faint shadow to stay readable over candles
        c.shadowColor = 'rgba(0,0,0,' + (imp ? 0.35 : 0.75) + ')'; c.shadowBlur = 3;
        c.textBaseline = 'alphabetic';
        c.font = lw + nfs + 'px ' + FONT; c.fillStyle = imp ? rgba(col, 0.55) : col; c.fillText(z.label, lx + 5, ly + 4 + fs * 0.86);
        pctDraw(c, pct(share), lx + 10 + wN, ly + 4 + fs * 0.86, lw, fs, imp ? 'rgba(200,205,214,.38)' : '#EEF1F5');
        if (sub) { c.font = '600 10.5px ' + FONT; c.fillStyle = col; c.fillText(sub, lx + 5, ly + hT - 5); }
        c.restore();
        V.zoneHit.push({ box: [lx, ly, wT, hT], ev, i, loops: g.hit });
      });
    }
  }
  // ---------- the time band (variant «Окна времени», operator 2026-10-01) ----------
  // X above the centre, R below, in three layers:
  // - the capsules (outer lanes): every zone over its whole time window (the 15-minute cells it covers), with its share
  //   of the family and today's status: the zone as a cluster in time;
  // - the hills: the shape of each zone's sessions in time (a Gaussian of 7 minutes); one height scale per event, its
  //   tallest hill filling the half: where in its window the zone is densest, a drawing without a number (X and R hills
  //   are not compared by height; the capsules and the columns carry the numbers);
  // - the columns: R and X of the family by 15 minutes on one square-root scale, each its own 100 % (with «?» at the
  //   right), both shares of the same N, so the taller of the two is the event more of the family set in that window.
  // Passed windows are dimmer.
  function bandHills(F, ctx, ev) {
    const Zm = F.zones[ev];
    if (!Zm) return [];
    return Zm.zones.map((z, i) => {
      const ts = F.ev[ev].pts.filter(q => F.zcell[ev].get(q.k + '|' + q.b) === i).map(q => q.t + 2.5);
      if (!ts.length) return null;
      const sig = 7, t0 = Math.min(...ts) - 3 * sig, t1 = Math.max(...ts) + 3 * sig, pts = [];
      let pk = 0, pkT = t0;
      for (let t = t0; t <= t1 + 0.01; t += 1.5) {
        let d = 0;
        for (const u of ts) d += Math.exp(-((t - u) * (t - u)) / (2 * sig * sig));
        pts.push([t, d]);
        if (d > pk) { pk = d; pkT = t; }
      }
      const bs = z.cell_mask.map(q => q[1]);
      return { z, i, pts, pk, pkT, b0: Math.min(...bs), b1: Math.max(...bs) + 1 };
    });
  }
  // how far the time band may rise above its own strip into the chart: up to just under the lowest thing the trader reads
  // there (the lowest candle in view, today's DR low, the lowest edge of a zone still ahead), at most 30 % of the chart
  function bandOverlay(ctx) {
    const F = ctx.F, s = ctx.s;
    let yLow = 0;
    for (const b of ctx.D.bars) if (b.t + 5 >= st.v0 && b.t <= st.v1) yLow = Math.max(yLow, V.Y(b.l));
    if (s.drL != null) yLow = Math.max(yLow, V.Y(s.drL), V.Y(s.drH));
    for (const ev of ['R', 'X']) {
      const Zm = F.zones[ev], S = Zm ? zoneStatus(F, ctx, ev) : [];
      if (Zm) Zm.zones.forEach((z, i) => {
        if (S[i] === 'IMPOSSIBLE') return;
        const ks = z.cell_mask.map(q => q[0]);
        yLow = Math.max(yLow, V.Y(F.u2p(Math.min(...ks) / 10)), V.Y(F.u2p((Math.max(...ks) + 1) / 10)));
      });
    }
    return Math.round(clamp(V.plot.h - yLow - 10, 0, V.plot.h * cfg.bandRise / 100));
  }
  function drawBand(c, ctx) {
    const F = ctx.F, B0 = V.band, h = hv(), sl = sliceOf(ctx), lk = V.lk, N = F.N, dir = F.d0 > 0 ? { X: -1, R: 1 } : { X: 1, R: -1 };
    // the band's drawing area: its own strip plus the free height above it (operator 2026-10-06: the columns of X and R
    // must be tall enough to compare, without covering the chart)
    const ov = V.bandOv = bandOverlay(ctx), B = { x: B0.x, y: B0.y - ov, w: B0.w, h: B0.h + ov };
    const S = { X: zoneLook(F, ctx, 'X'), R: zoneLook(F, ctx, 'R') }, H = { X: bandHills(F, ctx, 'X'), R: bandHills(F, ctx, 'R') };
    // the capsules' lanes first: a zone takes the first lane where it does not overlap an earlier one (two lanes at most)
    const caps = [], lanesUsed = { X: 0, R: 0 };
    for (const ev of ['X', 'R']) {
      const ends = [];
      H[ev].filter(Boolean).slice().sort((a, b) => a.b0 - b.b0).forEach(o => {
        let ln = 0;
        while (ends[ln] != null && ends[ln] > o.b0) ln++;
        ln = Math.min(ln, 1); ends[ln] = Math.max(ends[ln] || 0, o.b1);
        lanesUsed[ev] = Math.max(lanesUsed[ev], ln + 1);
        caps.push({ ev, o, ln });
      });
    }
    // the band follows the side of today's activation: X on the side of the confirmation (above for a long, below for a
    // short), R on the other (operator 2026-10-06), as on the chart
    const upEv = dir.X < 0 ? 'X' : 'R', dnEv = upEv === 'X' ? 'R' : 'X';
    const LH = 15, top = B.y + 3 + lanesUsed[upEv] * (LH + 2) + 2, bot = B.y + B.h - 3 - lanesUsed[dnEv] * (LH + 2) - 2;
    const cy = Math.round((top + bot) / 2) + 0.5, half = (bot - top) / 2 - 2;
    c.save(); c.beginPath(); c.rect(B.x, B.y, B.w, B.h); c.clip();
    c.fillStyle = '#0A0B0F'; c.fillRect(B0.x, B0.y, B0.w, B0.h);
    if (ov > 0) { const gr = c.createLinearGradient(0, B.y, 0, B0.y); gr.addColorStop(0, 'rgba(10,11,15,0)'); gr.addColorStop(1, 'rgba(10,11,15,.72)'); c.fillStyle = gr; c.fillRect(B.x, B.y, B.w, ov); }
    c.fillStyle = C.grid; c.fillRect(B0.x, B0.y, B0.w, 1);
    drawMidnight(c, B0.y, B0.y + B0.h);
    const T = { R: F.ev.R.T, X: F.ev.X.T }, mx = Math.max(1, ...T.R.values(), ...T.X.values());
    // operator 2026-10-06: the height is LINEAR in the share (the square root hid the difference: 4,8 against 3,2 looked
    // like 1,22 instead of 1,5); the counts are unchanged
    const yOf = (ev, n) => cy + dir[ev] * (1 + half * Math.min(1, Math.max(0, n) / mx));
    // the columns
    V.bandCols = [];
    const labels = [];
    for (let b = 0; b < F.nb; b++) {
      const t0 = F.f + 15 * b, x0 = V.X(t0) + 1, x1 = V.X(t0 + 15) - 1;
      if (x1 < B.x || x0 > B.x + B.w) continue;
      V.bandCols.push({ b, x0, x1 });
      const nX = T.X.get(b) || 0, nR = T.R.get(b) || 0, past = t0 + 15 <= sl;
      const lit = (h && h.k === 'tcell' && b >= h.b0 && b < h.b1) || (lk && lk.b === b), zl = h && h.k === 'zone' && F.zones[h.ev] && F.zones[h.ev].zones[h.i] && F.zones[h.ev].zones[h.i].cell_mask.some(([, bb]) => bb === b);
      for (const ev of ['X', 'R']) {
        const n = ev === 'X' ? nX : nR, o = ev === 'X' ? nR : nX;
        // the balance inside the 15 minutes (operator 2026-10-06): the larger side brighter, the smaller dimmer, the more
        // so the stronger the tilt (setting «контраст перевеса»); a drawing of the same two shares, not a new number
        const dom = n + o > 0 ? (n - o) / (n + o) : 0;
        let a = (0.12 + 0.26 * Math.pow(n / mx, 0.7)) * Math.max(0.15, 1 + cfg.domK / 100 * dom);
        if (past) a *= 0.5;
        if (lit || zl) a = Math.max(a, 0.5);
        c.fillStyle = rgba(cfg[ev], Math.min(1, a * cfg.stripA / 80));
        const y = yOf(ev, n);
        c.fillRect(x0, Math.min(cy + dir[ev], y), x1 - x0, Math.abs(y - cy) - 1);
        // a thin outline on the side that outweighs, even for a small tilt (3,8 against 3,2), stronger with the tilt but
        // always quiet (operator 2026-10-06: an outline takes the eye, so only the winner and only lightly)
        if (n > o && cfg.domLine > 0 && Math.abs(y - cy) > 3) {
          c.strokeStyle = rgba(cfg[ev], Math.min(0.9, (0.12 + 0.18 * Math.min(1, 3 * dom)) * (past ? 0.6 : 1) * cfg.domLine / 100)); c.lineWidth = 1;   // barely visible (operator 2026-10-06)
          c.strokeRect(Math.round(x0) + 0.5, Math.round(Math.min(cy + dir[ev], y)) + 0.5, Math.max(1, Math.round(x1 - x0) - 1), Math.max(1, Math.round(Math.abs(y - cy) - 1) - 1));
        }
        if (lit && n) labels.push({ x: (x0 + x1) / 2, y: dir[ev] < 0 ? y - 7 : y + 8, t: pct(100 * n / N).replace('%', ''), col: cfg[ev] });
      }
    }
    // the hills: one height scale per event, its tallest hill filling its half (a shape, not a number)
    const hmax = { X: Math.max(1e-9, ...H.X.filter(Boolean).map(o => o.pk)), R: Math.max(1e-9, ...H.R.filter(Boolean).map(o => o.pk)) };
    V.hills = [];
    for (const ev of ['X', 'R']) H[ev].forEach(o => {
      if (!o) return;
      const s = S[ev][o.i], imp = s === 'IMPOSSIBLE', on = !!(h && h.k === 'zone' && h.ev === ev && h.i === o.i), other = !!(h && h.k === 'zone' && !on), col = stateCol(cfg[ev], s);
      const scr = o.pts.map(([t, d]) => [V.X(t), cy + dir[ev] * (1 + 0.94 * half * d / hmax[ev])]);
      c.beginPath(); c.moveTo(scr[0][0], cy + dir[ev]);
      for (const p of scr) c.lineTo(p[0], p[1]);
      c.lineTo(scr[scr.length - 1][0], cy + dir[ev]); c.closePath();
      const a = (imp ? 0.05 : s === 'HOLDS' ? 0.5 : 0.38) * (on ? 1.5 : other ? 0.45 : 1);
      c.save(); c.shadowColor = rgba(col, imp ? 0 : 0.6); c.shadowBlur = on ? 18 : 12; c.fillStyle = rgba(col, Math.min(0.8, a)); c.fill(); c.restore();
      c.strokeStyle = rgba(col, imp ? 0.18 : on ? 0.95 : other ? 0.3 : 0.6); c.lineWidth = on ? 1.4 : 1; c.setLineDash(imp ? [3, 4] : []);
      c.beginPath(); scr.forEach((p, j) => j ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.stroke(); c.setLineDash([]);
      V.hills.push({ ev, i: o.i, scr, cy, up: dir[ev] < 0 });
    });
    for (const L of labels) { c.font = '700 10.5px ' + FONT; c.fillStyle = L.col; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(L.t, L.x, L.y); c.textAlign = 'left'; }
    // the capsules: the zone over its whole time window, its share and status inside. Operator 2026-10-06: no outline on a
    // live zone, only a soft fill whose saturation follows the zone's share (one scale for R and X); a hovered or pinned
    // zone gets a hairline; a zone that is already IMPOSSIBLE today is a faint dashed trace with dim text, so the eye
    // goes to the zones still ahead
    V.caps = [];
    const capMax = Math.max(1e-9, ...caps.map(q => q.o.z.p_snapshot));
    for (const { ev, o, ln } of caps) {
      const s = S[ev][o.i], imp = s === 'IMPOSSIBLE', hold = s === 'HOLDS', on = !!(h && h.k === 'zone' && h.ev === ev && h.i === o.i), other = !!(h && h.k === 'zone' && !on), col = stateCol(cfg[ev], s);
      const x0 = V.X(F.f + 15 * o.b0) + 1, x1 = V.X(F.f + 15 * o.b1) - 1, y0 = dir[ev] < 0 ? B.y + 3 + ln * (LH + 2) : B.y + B.h - 3 - (ln + 1) * (LH + 2) + 2, w = x1 - x0;
      const r = Math.pow(o.z.p_snapshot / capMax, 0.7);
      c.save(); c.globalAlpha = other ? 0.5 : 1;
      if (imp && !on) {
        c.strokeStyle = rgba(col, Math.min(1, 0.3 * cfg.capA / 100)); c.lineWidth = 1; c.setLineDash([3, 4]); roundRect(c, x0 + 0.5, y0 + 0.5, w - 1, LH - 1, LH / 2); c.stroke(); c.setLineDash([]);
      } else {
        c.fillStyle = rgba(col, Math.min(1, (on ? 0.34 : 0.12 + 0.22 * r + (hold ? 0.06 : 0)) * cfg.capA / 100)); roundRect(c, x0, y0, w, LH, LH / 2); c.fill();
        if (on) { c.strokeStyle = rgba(col, 0.6); c.lineWidth = 1; roundRect(c, x0 + 0.5, y0 + 0.5, w - 1, LH - 1, LH / 2); c.stroke(); }
      }
      c.beginPath(); c.rect(x0 + 2, y0, w - 4, LH); c.clip();
      c.textBaseline = 'middle';
      let x = x0 + 9;
      c.font = '700 10.5px ' + FONT; c.fillStyle = rgba(col, Math.min(1, (imp ? 0.45 : 0.85 + 0.15 * r) * cfg.capTxt / 100)); c.fillText(o.z.label, x, y0 + LH / 2 + 0.5); x += c.measureText(o.z.label).width + 6;
      const sh = pct(100 * o.z.p_snapshot), sfs = imp ? 10.5 : 10.5 + 1.5 * r;
      pctDraw(c, sh, x, y0 + LH / 2 + 0.5, '700 ', sfs, imp ? rgba('#8C929D', Math.min(1, 0.55 * cfg.capTxt / 100)) : rgba('#EEF1F5', Math.min(1, (0.8 + 0.2 * r) * cfg.capTxt / 100))); x += pctW(c, sh, '700 ', sfs) + 7;
      if (hold) { c.font = '600 9.5px ' + FONT; c.fillStyle = col; c.fillText(ZST[s], x, y0 + LH / 2 + 0.5); }
      c.restore();
      V.caps.push({ ev, i: o.i, box: [x0, y0, w, LH] });
    }
    // the centre line, the slice, the names of the halves, the unknown mass
    const xF = V.X(F.f), xE = V.X(F.end);
    c.fillStyle = 'rgba(209,212,220,.14)'; c.fillRect(Math.max(B.x, xF), cy, Math.min(B.x + B.w, xE) - Math.max(B.x, xF), 1);
    const xs = Math.round(V.X(sl)) + 0.5;
    if (xs > B.x && xs < B.x + B.w) { c.strokeStyle = 'rgba(209,212,220,.35)'; c.setLineDash([3, 4]); c.beginPath(); c.moveTo(xs, B.y + 1); c.lineTo(xs, B.y + B.h); c.stroke(); c.setLineDash([]); }
    c.font = '700 11px ' + FONT; c.textBaseline = 'middle';
    if (xF - 60 > B.x) {
      c.font = '700 10px ' + FONT;
      c.fillStyle = cfg.X; c.fillText('X ' + F.names.X.toLowerCase(), Math.max(B.x + 6, xF - 110), cy + dir.X * 9);
      c.fillStyle = cfg.R; c.fillText('R ' + F.names.R.toLowerCase(), Math.max(B.x + 6, xF - 110), cy + dir.R * 9);
    }
    V.stripUnk = null;
    const uX = F.ev.X.unknown + F.ev.X.none, uR = F.ev.R.unknown + F.ev.R.none;
    if (uX + uR) {
      const x0 = Math.min(xE + 6, B.x + B.w - 40), w = 14;
      c.fillStyle = 'rgba(160,168,180,.45)';
      for (const [ev, u] of [['X', uX], ['R', uR]]) { const y = yOf(ev, u); c.fillRect(x0, Math.min(y, cy + dir[ev]), w, Math.abs(y - cy) - 1); }
      c.fillStyle = C.text2; c.font = '600 10.5px ' + FONT; c.fillText('?', x0 + w + 4, cy);
      V.stripUnk = [x0, top, w + 14, bot - top];
    }
    c.restore();
    V.bandCy = cy;
    // the corner under the price scale and the price columns: what the band holds
    c.fillStyle = C.axis; c.fillRect(V.plot.w, B0.y, V.W - V.plot.w, B0.h);
    c.fillStyle = C.grid; c.fillRect(V.plot.w, B0.y, V.W - V.plot.w, 1); c.fillRect(V.plot.w, B0.y, 1, B0.h);
    // its explanation («▲ X · зоны и когда …») removed by the operator 2026-10-06: the names stand at the band's left
  }
  // names of the lines at their right end, just before the price scale, so nothing has to be scrolled to be read
  function drawTags(c, ctx) {
    const items = [], s = ctx.s, xr = V.plot.w - 6;
    if (s.drH != null) {
      const play = s.status === 'broken' ? s.nside : s.side || 0;
      for (const l of levels(s)) {
        if (l.type === 'std' && !stdShown(s, l)) continue;   // every drawn line is named (operator 2026-10-06)
        // today's DR / IDR named on their own lines, not as wide tags on the price scale (operator 2026-10-06)
        // operator 2026-10-06: the price stays on the price scale; the line ends with its name only
        if (l.type === 'dr' || l.type === 'idr') { items.push({ y: V.Y(l.p), text: l.type === 'dr' ? 'DR' : 'IDR', col: sideCol(s, l.type === 'dr' ? '#E9ECF1' : '#AEB6C4'), pr: 3, big: 1 }); continue; }
        const col = l.type === 'mid' ? C.mid : l.type === 'open' ? C.open : play === l.dir ? C.stdOn : C.std;
        const ss = stdState(s, l);
        items.push({ y: V.Y(l.p), text: (l.type === 'std' ? '' : s.k + ' ') + l.name + (ss === 'taken' ? ' ✓' : ''), col: ss === 'taken' ? C.text3 : ss === 'next' ? '#FFFFFF' : col, pr: ss === 'next' ? 3 : l.type === 'std' ? 1 : 2, big: ss === 'next' ? 1 : 0 });
      }
    }
    if (st.L.prev) for (const P of prevList(ctx)) {
      items.push({ y: V.Y(P.s.drH), text: P.name + ' DR', col: '#BFC6D2', pr: 2 }, { y: V.Y(P.s.drL), text: P.name + ' DR', col: '#BFC6D2', pr: 2 });
      items.push({ y: V.Y(P.s.idrH), text: P.name + ' IDR', col: '#8C95A3', pr: 1 }, { y: V.Y(P.s.idrL), text: P.name + ' IDR', col: '#8C95A3', pr: 1 });
    }
    if (st.L.vib) {
      const open = vibsKnown(ctx).filter(v => v.fill == null), pNow = s.priceNow != null ? s.priceNow : 0;
      const near = side => open.filter(v => side * ((v.lo + v.hi) / 2 - pNow) > 0).sort((a, b) => Math.abs((a.lo + a.hi) / 2 - pNow) - Math.abs((b.lo + b.hi) / 2 - pNow)).slice(0, 2);
      // operator 2026-10-06: the VI name stands inside its own rectangle (drawVib) or nowhere, never shifted off it
      void near;
    }
    const vis = items.filter(q => q.y > 8 && q.y < V.plot.h - 6).sort((a, b) => a.y - b.y);
    const placed = [];
    for (const q of vis.slice().sort((a, b) => b.pr - a.pr)) {
      let y = q.y;
      for (let tries = 0; tries < 6 && placed.some(p => Math.abs(p.y - y) < 12); tries++) {
        const hit_ = placed.find(p => Math.abs(p.y - y) < 12);
        y = q.y >= hit_.y ? hit_.y + 12 : hit_.y - 12;
      }
      if (placed.some(p => Math.abs(p.y - y) < 11)) continue;
      placed.push({ y, q });
    }
    c.textBaseline = 'middle'; c.textAlign = 'right';
    for (const { y, q } of placed) {
      c.font = (q.big ? '600 ' + cfg.lineLbl + 'px ' : cfg.prevLbl + 'px ') + FONT;
      const w = c.measureText(q.text).width + 6;
      c.fillStyle = 'rgba(8,9,12,.82)'; c.fillRect(xr - w, y - 6, w + 2, 12);
      c.fillStyle = q.col; c.fillText(q.text, xr - 2, y + 0.5);
    }
    c.textAlign = 'left';
  }
  function drawCross(c) {
    if (st.mx < 0 || (st.drag && !st.drag.area) || st.mx > V.plot.w || st.my > V.plot.h) return;
    c.strokeStyle = 'rgba(150,160,175,.55)'; c.lineWidth = 1; c.setLineDash([4, 4]);
    const x = Math.round(V.X(snapT(V.T(st.mx)))) + 0.5, y = Math.round(st.my) + 0.5;
    c.beginPath(); c.moveTo(x, 0); c.lineTo(x, V.plot.h); c.moveTo(0, y); c.lineTo(V.plot.w, y); c.stroke(); c.setLineDash([]);
  }
  const snapT = t => Math.floor(t / 5) * 5 + 2.5;
  function niceStep(span, pxs, minPx, list) { for (const s of list) if (s * pxs / span >= minPx) return s; return list[list.length - 1]; }
  function axisTag(c, y, text, bg, fg) {
    const x = V.plot.w + 1, w = V.axisW - 2;
    c.fillStyle = bg; roundRect(c, x, y - 8, w, 16, 3); c.fill();
    c.fillStyle = fg; c.font = '600 10.5px ' + FONT; c.textBaseline = 'middle'; c.fillText(text, x + 4, y + 0.5);
  }
  function drawPriceAxis(c, ctx) {
    const x = V.plot.w, H = V.plot.h;
    c.fillStyle = C.axis; c.fillRect(x, 0, V.axisW, H);
    c.fillStyle = C.grid; c.fillRect(x, 0, 1, H);
    const span = V.p1 - V.p0, step = niceStep(span, H, 46, [0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100, 250, 500]);
    c.font = '10.5px ' + FONT; c.fillStyle = C.text2; c.textBaseline = 'middle';
    for (let p = Math.ceil(V.p0 / step) * step; p <= V.p1; p += step) { const y = V.Y(p); if (y > 8 && y < H - 8) c.fillText(px(p), x + 5, y); }
    // operator 2026-10-06: today's DR / IDR prices on the scale as narrow tags (price only); their names stand at the end
    // of their lines inside the chart (drawTags)
    const s = ctx.s, tags = [];
    if (s.drH != null) {
      const dbg = sideCol(s, '#E9ECF1'), ibg = playSide(s) && cfg.sideA ? mixHex('#39414E', playSide(s) > 0 ? C.up : C.dn, 0.55 * cfg.sideA / 100) : '#39414E';
      tags.push([V.Y(s.drH), px(s.drH), dbg, '#0B0C10'], [V.Y(s.drL), px(s.drL), dbg, '#0B0C10']);
      tags.push([V.Y(s.idrH), px(s.idrH), ibg, '#E6EAF0'], [V.Y(s.idrL), px(s.idrL), ibg, '#E6EAF0']);
    }
    const hh = hv(), wn = V.win;
    if (wn && wn.pA != null) { tags.push([V.Y(wn.pB), px(wn.pB), wn.col, '#0B0C10', 1], [V.Y(wn.pA), px(wn.pA), wn.col, '#0B0C10', 1]); }
    if (hh && hh.k === 'lvl' && hh.l) tags.push([V.Y(hh.l.p), px(hh.l.p), '#C9D1DD', '#0B0C10']);
    if (hh && hh.k === 'prev') tags.push([V.Y(hh.p), px(hh.p), '#8C95A3', '#0B0C10']);
    const lastP = s.priceNow != null ? s.priceNow : null;
    if (lastP != null) { const b = ctx.D.bars.filter(q => q.t + 5 <= (ctx.live ? NOW + 5 : ctx.obs)).pop(); tags.push([V.Y(lastP), px(lastP), b && b.c >= b.o ? C.up : C.dn, '#fff']); }
    const hot = tags.filter(q => q[4]);
    for (const [y, t, bg, fg, hv_] of tags) if (y > 0 && y < H && (hv_ || !hot.some(q => Math.abs(q[0] - y) < 18))) axisTag(c, y, t, bg, fg);
    if (st.mx >= 0 && st.my >= 0 && st.my < H && st.mx < V.plot.w) axisTag(c, st.my, px(V.P(st.my)), '#363A45', '#fff');
    if (!st.auto) { c.fillStyle = '#262B35'; roundRect(c, x + V.axisW - 24, H - 22, 18, 16, 3); c.fill(); c.fillStyle = C.text2; c.font = '600 10px ' + FONT; c.fillText('A', x + V.axisW - 19, H - 13.5); }
  }
  // the column right of the price scale: the chosen event's price histogram P_E(k) by 0.1 SD (bounds), or the family's
  // M5 closes on the chosen M5 (path); the share out of view is named at the column's edges; «?» = unknown mass
  function projData(ctx) {
    const F = ctx.F;
    if (st.mode === 'bounds') {
      const D = F.ev[st.ev];
      return { bars: [...D.P].map(([k, n]) => ({ k, n })), unk: D.unknown, none: D.none, col: cfg[st.ev], head: st.ev + ' · ' + F.names[st.ev].toLowerCase() };
    }
    const cd = colFor(ctx);
    if (!cd) return null;
    return { bars: [...cd.cells].map(([k, list]) => ({ k, n: list.length })), unk: cd.unknown, none: 0, col: cfg.path, head: 'M5 ' + clk(cd.T - 5), cd };
  }
  // the M5 column of «Путь семьи» the panel and the column describe: hovered, else pinned, else the slice's own M5
  function colFor(ctx) {
    const F = ctx.F, h = hv(), film = filmOf(F);
    if (h && (h.k === 'col' || h.k === 'fcell')) return film[h.j];
    if (st.col != null && film[st.col]) return film[st.col];
    const sl = sliceOf(ctx), j = F.grid.indexOf(sl);
    return j >= 0 ? film[j] : film[0];
  }
  // «Границы хода»: R and X in ONE column (operator 2026-10-06), each its own 100 % (their «?» is in the panel). One price
  // row = one horizontal bar from the same edge: R's segment first (amber), X's right after it (sky), so where both have
  // sessions at that price the two shares stand side by side in one bar. R's percentage always left of the bar, X's
  // always right of it. Rows of a zone brighter, each zone's densest row in a larger type; a zone's price extent is a
  // thin tick at the right edge. A segment is the share of the whole band over the whole horizon, never the zone's.
  function drawProjRX(c, ctx) {
    const F = ctx.F, A_ = V.proj, h = hv(), top0 = 40, bot0 = A_.h - 16, x0 = A_.x + 38, blen = A_.w - 38 - 36;
    c.fillStyle = C.axis; c.fillRect(A_.x, 0, A_.w, A_.h);
    c.fillStyle = C.grid; c.fillRect(A_.x, 0, 1, A_.h);
    V.projBars = []; V.projCols = { X: [A_.x, A_.x + A_.w], R: [A_.x, A_.x + A_.w] }; V.projUnk = null; V.projEdge = null;
    c.save(); c.beginPath(); c.rect(A_.x, 0, A_.w, A_.h); c.clip();
    const info = {}, lanes = [], out = { X: [0, 0], R: [0, 0] };
    for (const ev of ['R', 'X']) {
      const D = F.ev[ev], Zm = F.zones[ev], hzi = h && h.k === 'zone' && h.ev === ev ? h.i : null, zr = new Map(), peak = new Set();
      if (Zm) Zm.zones.forEach((z, i) => {
        const ks = z.cell_mask.map(q => q[0]), k0 = Math.min(...ks), k1 = Math.max(...ks) + 1;
        let bk = null;
        for (let k = k0; k < k1; k++) { zr.set(k, i); if (bk == null || (D.P.get(k) || 0) > (D.P.get(bk) || 0)) bk = k; }
        if (bk != null && D.P.get(bk)) peak.add(bk);
        lanes.push({ i, k0, k1, ev, hot: hzi === i });
      });
      info[ev] = { D, zr, peak, hzi };
    }
    const keys = [...new Set([...F.ev.R.P.keys(), ...F.ev.X.P.keys()])];
    const mx = Math.max(1, ...keys.map(k => (F.ev.R.P.get(k) || 0) + (F.ev.X.P.get(k) || 0)));
    const m1 = Math.max(1, ...F.ev.R.P.values(), ...F.ev.X.P.values()), str = n => Math.pow(n / m1, 0.75);   // 0..1, one scale
    // operator 2026-10-06: a band's sessions whose event is already behind today's slice (by the clock) vs still ahead;
    // the segment keeps its whole length (the band's share), the passed part is faded, so «what is still ahead» reads
    const Rch = reachOf(F, ctx), sl = Rch.sl, gone = { R: new Map(), X: new Map() };
    for (const ev of ['R', 'X']) for (const q of F.ev[ev].pts) if (q.t + 5 <= sl) gone[ev].set(q.k, (gone[ev].get(q.k) || 0) + 1);
    // audit 2026-10-06: a band where today's final event can no longer lie (today's R is already deeper, today's X already
    // further) is faded whole and its label grey: this is what «the level has traded today» means
    const labels = [];
    for (const k of keys) {
      const [top, bot] = cellY(F, k, k + 1);
      if (bot < top0 || top > bot0) { for (const ev of ['R', 'X']) out[ev][bot < top0 ? 0 : 1] += info[ev].D.P.get(k) || 0; continue; }
      let x = x0;
      for (const ev of ['R', 'X']) {
        const I = info[ev], n = I.D.P.get(k) || 0;
        if (!n) continue;
        const z = I.zr.get(k), on = !!(h && h.k === 'pcell' && h.ev === ev && k >= h.k0 && k < h.k1);
        const inA = !!(st.area && st.area.ev === ev && isFinite(st.area.k0) && k >= st.area.k0 && k < st.area.k1);
        const r = str(n);
        let a = z != null ? 0.22 + 0.78 * r : 0.1 + 0.32 * r;     // a zone row from faint to full, a residual row stays quiet
        if (I.hzi != null) a = z === I.hzi ? Math.max(a, 0.6) : a * 0.4;
        if (on || inA) a = 1;
        const len = Math.max(2, blen * n / mx), g = Rch.okK(ev, k) ? Math.min(n, gone[ev].get(k) || 0) : n, la = len * (n - g) / n, hh = Math.max(1, bot - top - 1);
        c.fillStyle = rgba(cfg[ev], Math.min(1, a * cfg.projA / 90)); c.fillRect(x, top + 0.5, la, hh);
        if (g) { c.fillStyle = rgba(stateCol(cfg[ev], 'spent'), Math.min(1, Math.min(1, a * cfg.projA / 90) * cfg.passedA / 100 * 1.8)); c.fillRect(x + la, top + 0.5, len - la, hh); }
        V.projBars.push({ ev, k, top, bot, x0: x, x1: x + len });
        const pk = I.peak.has(k);
        if (on || pk || z != null || 100 * n / F.N >= 3) labels.push({ ev, y: (top + bot) / 2, xe: x + len, n, ahead: n - g, pk, on, z, rowH: bot - top });
        x += len;
      }
    }
    // the labels: R left of the bar, X right of it; per side the hovered and the zones' peaks first, never overlapping
    const used = { R: [], X: [] };
    for (const L of labels.sort((a, b) => (b.on - a.on) || (b.pk - a.pk) || (b.n - a.n))) {
      // the label's size and brightness follow the share on the same scale as the bar: the strongest rows read first
      // the strongest row of the column 14 px bold, the weakest zone rows about 9 px (linear in the share)
      // the weight of a label follows what is still AHEAD in its band (the number stays the band's whole share); a band
      // with nothing ahead is grey and small: it has played out today (operator 2026-10-06)
      const dead = !L.on && L.ahead <= 0, r = str(L.ahead), q = L.ahead / m1, fs = (L.on ? 13 : dead ? 8.5 : L.z != null ? 8.5 + 5.5 * q : 8 + 1.2 * q) * cfg.colSize / 100;
      if (used[L.ev].some(u => Math.abs(u[0] - L.y) < (u[1] + fs) / 2 + 1)) continue;
      used[L.ev].push([L.y, fs]);
      const col = cfg[L.ev], wt = L.on || (!dead && q > 0.7) ? '700 ' : L.z != null && !dead ? '600 ' : '';
      c.textBaseline = 'middle';
      const t = pct(100 * L.n / F.N), tw = pctW(c, t, wt, fs);
      pctDraw(c, t, L.ev === 'R' ? Math.max(A_.x + 3, x0 - 3 - tw) : Math.min(L.xe + 3, A_.x + A_.w - tw - 6), L.y + 0.5, wt, fs,
        L.on ? '#FFFFFF' : dead ? 'rgba(140,146,157,.5)' : L.z != null ? rgba(mixW(col, 0.45 * r), 0.5 + 0.5 * r) : C.text3);
    }
    // the zones' price extents: thin ticks at the right edge, one lane per overlap
    const ends = [];
    lanes.sort((a, b) => a.k0 - b.k0).forEach(o => {
      let ln = 0;
      while (ends[ln] != null && ends[ln] > o.k0) ln++;
      ends[ln] = o.k1;
      const [ya, yb] = cellY(F, o.k0, o.k1), y0 = Math.max(top0, ya), y1 = Math.min(bot0, yb);
      if (y1 > y0) { c.fillStyle = rgba(cfg[o.ev], o.hot ? 1 : 0.7); c.fillRect(A_.x + A_.w - 4 - 3 * ln, y0, 2, y1 - y0); }
    });
    // the heads (R on the left, X on the right, as their percentages) and the shares beyond the frame
    c.textBaseline = 'top'; c.font = '700 10.5px ' + FONT;
    c.fillStyle = cfg.R; c.fillText('R откат', A_.x + 5, 3);
    const hx = 'X прод.';
    c.fillStyle = cfg.X; c.fillText(hx, A_.x + A_.w - c.measureText(hx).width - 5, 3);
    const shares = (i, y, base) => {
      c.font = '10px ' + FONT; c.textBaseline = base;
      c.fillStyle = C.text2; c.fillText(i ? '▼' : '▲', A_.x + A_.w / 2 - 4, y);
      if (out.R[i]) { c.fillStyle = cfg.R; c.fillText(pct(100 * out.R[i] / F.N), A_.x + 5, y); }
      if (out.X[i]) { const t = pct(100 * out.X[i] / F.N); c.fillStyle = cfg.X; c.fillText(t, A_.x + A_.w - c.measureText(t).width - 5, y); }
    };
    if (out.X[0] + out.R[0]) shares(0, 18, 'top');
    if (out.X[1] + out.R[1]) shares(1, A_.h - 3, 'bottom');
    c.restore();
  }
  function drawProj(c, ctx) {
    if (st.mode === 'bounds') return drawProjRX(c, ctx);
    const F = ctx.F, A_ = V.proj, W = A_.w - 40, h = hv(), d = projData(ctx);
    c.fillStyle = C.axis; c.fillRect(A_.x, 0, A_.w, A_.h);
    c.fillStyle = C.grid; c.fillRect(A_.x, 0, 1, A_.h);
    V.projBars = [];
    if (!d) return;
    c.save(); c.beginPath(); c.rect(A_.x, 0, A_.w, A_.h); c.clip();
    const mx = Math.max(1, ...d.bars.map(b => b.n)), labels = [];
    let above = 0, below = 0;
    for (const b of d.bars) {
      const [top, bot] = cellY(F, b.k, b.k + 1);
      if (bot < 0) { above += b.n; continue; }
      if (top > A_.h) { below += b.n; continue; }
      const len = Math.max(1, W * b.n / mx);
      const on = h && ((h.k === 'pcell' && b.k >= h.k0 && b.k < h.k1) || (h.k === 'fcell' && b.k === h.kk)) || (st.area && isFinite(st.area.k0) && b.k >= st.area.k0 && b.k < st.area.k1 && st.mode === 'bounds');
      c.fillStyle = rgba(d.col, on ? 1 : Math.min(1, (0.18 + 0.72 * b.n / mx) * cfg.projA / 90));
      c.fillRect(A_.x + 3, top + 0.5, len, Math.max(1, bot - top - 1));
      V.projBars.push({ k: b.k, top, bot });
      labels.push({ y: (top + bot) / 2, x: A_.x + 6 + len, n: b.n, k: b.k });
    }
    // the percentages, largest first, never overlapping
    c.font = '600 10.5px ' + FONT; c.textBaseline = 'middle';
    const used = [];
    for (const L of labels.sort((a, b) => b.n - a.n)) {
      if (L.y < 20 || L.y > A_.h - 16 || used.some(u => Math.abs(u - L.y) < 11)) continue;
      used.push(L.y);
      c.fillStyle = d.col; c.fillText(pct(100 * L.n / F.N), Math.min(L.x, A_.x + A_.w - 34), L.y + 0.5);
    }
    c.font = '600 10px ' + FONT; c.fillStyle = C.text2; c.textBaseline = 'top';
    c.fillText(d.head, A_.x + 4, 3);
    V.projEdge = null;
    if (above) { c.fillStyle = C.text2; c.fillText('▲ ' + pct(100 * above / F.N), A_.x + 4, 16); }
    if (below) { c.textBaseline = 'bottom'; c.fillStyle = C.text2; c.fillText('▼ ' + pct(100 * below / F.N), A_.x + 4, A_.h - 16); }
    V.projEdge = { above, below };
    V.projUnk = null;
    if (d.unk + d.none) {
      c.textBaseline = 'bottom'; c.fillStyle = C.text3;
      c.fillText('? ' + pct(100 * (d.unk + d.none) / F.N), A_.x + 4, A_.h - 3);
      V.projUnk = [A_.x, A_.h - 15, A_.w, 15];
    }
    c.restore();
  }
  function drawTimeAxis(c, ctx) {
    const y = V.taxisY, W = V.plot.w;
    c.fillStyle = C.axis; c.fillRect(0, y, V.W, V.timeH);
    c.fillStyle = C.grid; c.fillRect(0, y, V.W, 1);
    const step = niceStep(st.v1 - st.v0, W, 72, [5, 10, 15, 30, 60, 120, 180, 240, 360, 720]);
    const h = hv(), busy = [ctx.obs], wn = V.win;
    if (wn && wn.t0 != null) busy.push(wn.t0, wn.t1);
    if (st.mx >= 0 && st.mx < W && st.my < V.plot.h) busy.push(snapT(V.T(st.mx)) - 2.5);
    c.font = '11.5px ' + FONT; c.fillStyle = C.text2; c.textBaseline = 'middle'; c.textAlign = 'center';
    for (let t = Math.ceil(st.v0 / step) * step; t <= st.v1; t += step) { const x = V.X(t); if (x > 20 && x < W - 20 && !busy.some(b => Math.abs(V.X(b) - x) < 42)) c.fillText(t % 1440 === 0 ? ctx.D.dm : clk(t), x, y + V.timeH / 2); }
    const tag = (t, bg, fg, txt) => { const x = V.X(t), text = txt || clk(t); c.font = '600 11px ' + FONT; const w = c.measureText(text).width + 12; c.fillStyle = bg; roundRect(c, x - w / 2, y + 4, w, 20, 3); c.fill(); c.fillStyle = fg; c.fillText(text, x, y + 14.5); };
    // operator 2026-10-06: the hovered cluster's time window is what the trader looks for, so it is drawn last, over the
    // slice tag; the cursor's own time tag is left out while a window is shown
    tag(ctx.obs, ctx.live && !ctx.D.hist ? '#2A2F38' : ctx.D.hist ? C.hist : C.replay, ctx.live && !ctx.D.hist ? '#fff' : '#0B0C10');
    if (!(wn && wn.t0 != null) && st.mx >= 0 && st.mx < W && st.my < V.plot.h) tag(snapT(V.T(st.mx)) - 2.5, '#363A45', '#fff');
    if (wn && wn.t0 != null) { if (V.X(wn.t1) - V.X(wn.t0) < 96) tag((wn.t0 + wn.t1) / 2, wn.col, '#0B0C10', clk(wn.t0) + '–' + clk(wn.t1)); else { tag(wn.t0, wn.col, '#0B0C10'); tag(wn.t1, wn.col, '#0B0C10'); } }
    c.textAlign = 'left';
    void h;
  }
  function barAt(ctx, t) { const tt = Math.floor(t / 5) * 5; return ctx.D.bars.find(b => b.t === tt) || null; }
  // the top-left corner (operator 2026-10-06): only the instrument, the timeframe and the session, small; the OHLC
  // numbers and the «↑ 04:10 · взято …» line repeated what the chart, the scale and the panel already show
  function drawLegend(c, ctx) {
    c.textBaseline = 'top'; c.font = '600 11px ' + FONT; c.fillStyle = C.text2;
    c.fillText(A.inst + '1! · 5 · ' + ctx.s.k, 10, 8);
  }

  // ---------- hit test ----------
  function hit(x, y) {
    const ctx = V.ctx, F = ctx.F;
    if (F && V.projW && x >= V.proj.x && y < V.plot.h) {
      if (V.projUnk && y >= V.projUnk[1]) return { k: 'unk', src: 'proj' };
      if (st.mode === 'bounds') {
        // the two columns: R on the left, X on the right; a band of the event under the cursor
        const row = (V.projBars || []).filter(q => y >= q.top - 1 && y <= q.bot + 1), b = row.find(q => x >= q.x0 && x <= q.x1) || (x < V.proj.x + 38 ? row.find(q => q.ev === 'R') : row.find(q => q.ev === 'X')) || row[0], ev = b ? b.ev : st.ev;
        if (b) return { k: 'pcell', ev, k0: b.k, k1: b.k + 1, src: 'proj' };
        const k = F.cellOfP(V.P(y));
        return { k: 'pcell', ev, k0: k, k1: k + 1, src: 'proj', empty: true };
      }
      const b = (V.projBars || []).find(q => y >= q.top - 1 && y <= q.bot + 1);
      const cd = colFor(ctx);
      if (cd) { const k = b ? b.k : F.cellOfP(V.P(y)); return { k: 'fcell', j: cd.j, kk: k, src: 'proj' }; }
      return { k: 'paxis' };
    }
    if (x > V.plot.w) return y < V.plot.h ? { k: 'paxis' } : null;
    if (y > V.taxisY) return { k: 'taxis' };
    if (!F) return y > V.plot.h ? null : lvlHit(ctx, y) || vibHit(ctx, x, y) || prevHit(ctx, y);
    if (y > V.plot.h - (V.stripOn ? V.bandOv || 0 : 0) && x <= V.plot.w) {
      // the time band (with its raised part over the free bottom of the chart): a zone's hill (its label first), else a 15-minute column (both events), «?» at the right
      if (!V.stripOn) return { k: 'taxis' };
      const inBox = a => x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3];
      const cp = (V.caps || []).find(inBox);
      if (cp) return { k: 'zone', ev: cp.ev, i: cp.i, src: 'strip' };
      if (V.stripUnk && x >= V.stripUnk[0] && x <= V.stripUnk[0] + V.stripUnk[2]) return { k: 'unk', src: 'strip' };
      const cy = V.bandCy;
      for (const H of V.hills || []) {
        if (x < H.scr[0][0] || x > H.scr[H.scr.length - 1][0]) continue;
        let j = 1;
        while (j < H.scr.length - 1 && H.scr[j][0] < x) j++;
        const yh = H.scr[j][1];
        if (H.up ? y < cy && y >= yh - 2 : y > cy && y <= yh + 2) return { k: 'zone', ev: H.ev, i: H.i, src: 'strip' };
      }
      const q = (V.bandCols || []).find(z => x >= z.x0 - 1 && x <= z.x1 + 1);
      if (q) return { k: 'tcell', b0: q.b, b1: q.b + 1, src: 'strip' };
      return { k: 'stripBg' };
    }
    if (st.area && V.areaHit) for (const a of V.areaHit) if (a.part !== 'frame' && x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3]) return { k: 'area', part: a.part };
    const inBox = a => x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3];
    const zl = (V.zoneHit || []).find(inBox);
    if (zl) return { k: 'zone', ev: zl.ev, i: zl.i };
    if (st.mode === 'bounds' && st.L.pts) {
      // a star of R or of X: the nearest within 5 px
      let best = null, bd = 5;
      for (const ev of ['R', 'X']) for (const q of F.ev[ev].pts) { const d = Math.hypot(V.X(q.t + 2.5) - x, V.Y(q.p) - y); if (d < bd) { bd = d; best = q; } }
      if (best) {
        const all = F.ev[best.ev].pts.filter(q => Math.hypot(V.X(q.t + 2.5) - V.X(best.t + 2.5), V.Y(q.p) - V.Y(best.p)) < 2.5);
        return { k: 'pt', ev: best.ev, i: best.i, q: best, same: all.map(q => q.i) };
      }
    }
    if (st.mode === 'path') {
      const t = V.T(x), j = F.grid.findIndex(T => t >= T - 5 && t < T);
      if (j >= 0) { const k = F.cellOfP(V.P(y)), cd = filmOf(F)[j]; if (cd.cells.has(k)) return { k: 'fcell', j, kk: k }; const lv = lvlHit(ctx, y); if (lv) return lv; return { k: 'col', j }; }
    }
    if (st.area && V.areaHit) for (const a of V.areaHit) if (a.part === 'frame' && x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3]) { const lv = lvlHit(ctx, y); if (lv) return lv; return { k: 'area', part: 'window' }; }
    // inside a constellation (its 0.2 iso-line): that zone
    for (const z of V.zoneHit || []) if (inLoops(z.loops, x, y)) return lvlHit(ctx, y) || { k: 'zone', ev: z.ev, i: z.i };
    return lvlHit(ctx, y) || vibHit(ctx, x, y) || prevHit(ctx, y);
  }
  function lvlHit(ctx, y) {
    for (const l of levels(ctx.s)) { if (!stdShown(ctx.s, l)) continue; if (Math.abs(V.Y(l.p) - y) <= 3.5) return { k: 'lvl', id: l.id, l }; }
    return null;
  }
  function vibHit(ctx, x, y) {
    if (!st.L.vib) return null;
    for (const v of vibsKnown(ctx)) { const x0 = V.X(v.t), x1 = v.fill != null ? V.X(v.fill + 5) : V.plot.w; if (x >= x0 && x <= x1 && y >= V.Y(v.hi) - 3 && y <= V.Y(v.lo) + 3) return { k: 'vib', t: v.t, v }; }
    return null;
  }
  function prevHit(ctx, y) {
    if (!st.L.prev) return null;
    for (const P of prevList(ctx)) for (const [p, nm] of [[P.s.drH, 'DR high'], [P.s.drL, 'DR low'], [P.s.idrH, 'IDR high'], [P.s.idrL, 'IDR low']]) if (Math.abs(V.Y(p) - y) <= 3.5) return { k: 'prev', id: P.k, P, p, nm };
    return null;
  }
  const memberLine = (F, m) => m.date.split('-').reverse().join('.');
  // one line per history session: what the system may say about the order of its first R and X (spec §8)
  function orderText(F, m) {
    if (m.order === 'unknown') return 'порядок неизвестен: событие не определено';
    if (m.order === 'same_M5') return 'R и X в одной M5: порядок внутри свечи неизвестен';
    const d = m.orderDetail || {};
    if (m.order === 'R_before_X') return d.all_r_before_all_x ? 'первая глубочайшая точка была раньше первого максимума расширения' : 'первая глубочайшая точка была раньше первого максимума; глубочайшая цена повторялась и позже';
    return d.all_x_before_all_r ? 'максимум расширения был раньше глубочайшей точки и после неё не повторялся' : 'первый максимум расширения был раньше глубочайшей точки; он повторялся и позже';
  }
  function tipHtml(h, ctx) {
    const F = ctx.F, s = ctx.s;
    if (!h) return '';
    if (h.k === 'pt' && F) {
      const m = F.M[h.i], ev = h.ev || st.ev, e = m[ev], other = ev === 'R' ? 'X' : 'R', o = m[other];
      const lines = ['<b>Сессия семьи · ' + memberLine(F, m) + '</b>' + (h.same && h.same.length > 1 ? ' <span class="k">и ещё ' + (h.same.length - 1) + ' в этой точке</span>' : '')];
      lines.push('<span style="color:' + cfg[ev] + '">' + F.names[ev] + ' ' + ev + '</span> ' + sd(e.v / m.w) + ' SD · ' + px(F.u2p(e.v / m.w)) + ' · ' + clk(e.t) + '–' + clk(e.t + 5) + (e.ties.length > 1 ? ' <span class="k">(та же цена ещё ' + (e.ties.length - 1) + ' раз)</span>' : ''));
      lines.push('<span style="color:' + cfg[other] + '">' + F.names[other] + ' ' + other + '</span> ' + (o.s === 'known' ? sd(o.v / m.w) + ' SD · ' + px(F.u2p(o.v / m.w)) + ' · ' + clk(o.t) + '–' + clk(o.t + 5) : 'неизвестно'));
      lines.push('<span class="k">' + orderText(F, m) + '</span>');
      if (!F.brk) lines.push((m.outcome === 'broken' ? 'DR сломан ' + (m.brkKnown ? clk(m.brk) : '(время первого слома неизвестно)') : m.outcome === 'held' ? 'DR удержался до ' + clk(F.end) : 'исход DR неизвестен'));
      lines.push('<span class="k">' + (F.brk ? 'слом' : 'подтверждение') + ' ' + clk(m.act) + ' · события ' + F.from + ' до ' + clk(F.end) + '</span>');
      return lines.join('<br>');
    }
    if (h.k === 'pcell' && F) {
      if (st.mode !== 'bounds') return '';
      // a price band: both events in it over the whole horizon, the peak 15 minutes of the hovered one, and the visits
      const ev = h.ev || st.ev, a = { k0: h.k0, k1: h.k1 }, nX = areaCount(F, 'X', a), nR = areaCount(F, 'R', a), lk = V && V.lk, sl = sliceOf(ctx);
      evPass(F, 'X', 'price_cell', [h.k0, h.k1], null, nX); evPass(F, 'R', 'price_cell', [h.k0, h.k1], null, nR);
      const vf = visitCount(F, h.k0, h.k1, null), vr = visitCount(F, h.k0, h.k1, sl), p0 = F.u2p(h.k0 / 10), p1 = F.u2p(h.k1 / 10);
      return '<div class="ih">Полоса ' + band(h.k0, h.k1) + ' SD</div><div class="is">' + px(Math.min(p0, p1)) + '–' + px(Math.max(p0, p1)) + ' · ' + where(s, F.u2p((h.k0 + h.k1) / 20)) + '</div>' +
        '<div class="iq">свой экстремум в этой полосе · ' + F.from + ' до ' + clk(F.end) + '</div>' + twoBars(F, nX, nR, ev) +
        (lk ? '<div class="il" style="color:' + (lk.past ? '#F23645' : cfg[ev]) + '">' + (lk.past ? 'уже прошло · пик ' : 'у семьи впереди · пик ') + ev + ' в полосе: ' + clk(F.f + 15 * lk.b) + '–' + clk(F.f + 15 * lk.b + 15) + ' · ' + pct(100 * lk.n / F.N) + ' семьи</div>' : '') +
        (() => { const Rch = reachOf(F, ctx), gn = e => F.ev[e].pts.filter(q => q.k >= h.k0 && q.k < h.k1 && q.t + 5 <= sl).length, gX = gn('X'), gR = gn('R');
          const off = e => !Rch.okK(e, h.k0), ttl = ' title="История похожих сессий по часам дня, не сегодняшний путь цены"';
          const why = e => e === 'R' ? 'сегодняшний откат уже глубже' : 'сегодняшнее продолжение уже дальше';
          return (off(ev) ? '<div class="il" style="color:#F23645">сегодня ' + ev + ' здесь уже невозможен: ' + why(ev) + '</div>' : '') +
            (sl >= F.end ? '' : '<div class="ir"' + ttl + '>у семьи позже ' + clk(sl) + '<b><span style="color:' + cfg.R + '">R ' + pct(100 * (nR - gR) / F.N) + '</span> · <span style="color:' + cfg.X + '">X ' + pct(100 * (nX - gX) / F.N) + '</span></b></div>' +
            '<div class="ir dim"' + ttl + '>у семьи раньше ' + clk(sl) + '<b>R ' + pct(100 * gR / F.N) + ' · X ' + pct(100 * gX / F.N) + '</b></div>'); })() +
        '<div class="ir">заходили в полосу · вся сессия<b>' + yr(F, vf) + '</b></div><div class="ir">заходили · после ' + clk(sl) + '<b>' + yr(F, vr) + '</b></div>' + ifoot(F);
    }
    if (h.k === 'tcell' && F) {
      // a 15-minute window: R and X of the family set there, which of them is more, and where in price each was densest
      const b = h.b0, t0 = F.f + 15 * b, nX = F.ev.X.T.get(b) || 0, nR = F.ev.R.T.get(b) || 0;
      evPass(F, 'X', 'time_cell', null, [t0, t0 + 15], nX); evPass(F, 'R', 'time_cell', null, [t0, t0 + 15], nR);
      const peakK = ev => {
        let bk = null, bc = 0;
        for (const c of F.ev[ev].cells.values()) if (c.b === b && (c.list.length > bc || (c.list.length === bc && c.k < bk))) { bc = c.list.length; bk = c.k; }
        return bk == null ? '' : '<div class="ir">' + ev + ' чаще всего в ' + band(bk, bk + 1) + ' SD<b>' + px(F.u2p((bk + 0.5) / 10)) + '</b></div>';
      };
      return '<div class="ih">' + clk(t0) + '–' + clk(t0 + 15) + '</div><div class="iq">в эти 15 минут свой экстремум поставили</div>' + twoBars(F, nX, nR, 'X') + peakK('X') + peakK('R') + ifoot(F, ' · время — открытие первой M5, где достигнута цена');
    }
    if (h.k === 'unk' && F) {
      const cd = st.mode === 'path' ? colFor(ctx) : null;
      if (st.mode === 'bounds') return ['X', 'R'].map(ev => { const D = F.ev[ev]; return '<b>' + pct(100 * (D.unknown + D.none) / F.N) + '</b> семьи — ' + F.names[ev].toLowerCase() + ' ' + ev + ' не определено' + (D.unknown ? ': нет свечи M5 на горизонте (' + pct(100 * D.unknown / F.N) + ')' : '') + (D.none ? (D.unknown ? ', ' : ': ') + 'нет периода измерения (' + pct(100 * D.none / F.N) + ')' : ''); }).join('<br>') + '<br><span class="k">не рисуется ни по какой цене и времени</span>';
      if (cd) return '<b>' + pct(100 * cd.unknown / F.N) + '</b> семьи — нет свечи на M5 ' + clk(cd.T - 5) + '–' + clk(cd.T) + ' (неизвестно / рынок закрыт)';
    }
    if (h.k === 'fcell' && F) {
      const cd = filmOf(F)[h.j], list = cd.cells.get(h.kk) || [], rf = rangeField(F, h.j, h.kk);
      const p = pp(F, { event_id: 'close_M5', region_kind: 'M5_cell', exact_price_bounds: [h.kk, h.kk + 1], time_bounds: [cd.T - 5, cd.T], start_rule: 'M5 ' + clk(cd.T - 5), end_rule: clk(cd.T), yes_count: list.length, unknown_count: cd.unknown, display_scope: 'path',
        phrase: 'закрытие M5 в полосе ' + band(h.kk, h.kk + 1) + ' SD', horizon: 'на пятиминутке ' + clk(cd.T - 5) + '–' + clk(cd.T) });
      return sentence(p) + '<br><span class="k">свеча M5 задевала эту полосу у ' + pct(100 * rf.n / F.N) + ' семьи (диапазон, не закрытие)</span>';
    }
    if (h.k === 'col' && F) { const cd = filmOf(F)[h.j]; return '<b>M5 ' + clk(cd.T - 5) + '–' + clk(cd.T) + '</b>' + (cd.unknown ? '<br><span class="k">нет свечи у ' + pct(100 * cd.unknown / F.N) + ' семьи</span>' : ''); }
    if (h.k === 'area' && F && st.area) return areaTip(F, ctx, h.part);
    if (h.k === 'zone' && F) return zoneTip(F, ctx, h);
    if (h.k === 'lvl' && h.l) {
      const l = h.l;
      let out = '<b>' + s.k + ' · ' + l.full + '</b> · ' + px(l.p);
      const tkn = (s.taken || []).concat(s.takenN || []).find(q => q.t && l.type === 'std' && q.name === l.name);
      if (tkn) out += ' · взят в ' + clk(tkn.t);
      if (F) {
        const q = levelQuery(F, ctx, l.p, l.type === 'std' ? l.name : l.full);
        out += '<br>' + sentence(q.full) + '<br>' + sentence(q.rest) + '<br><span class="k">' + q.today + '</span>';
      }
      return out;
    }
    if (h.k === 'vib') { const v = h.v; return '<b>VI ' + (v.dir === 1 ? '↑' : '↓') + '</b> · ' + px(v.lo) + '–' + px(v.hi) + ' · ' + clk(v.t) + '<br><span class="k">' + (v.fill != null ? 'ребалансирован в ' + clk(v.fill) : 'открыт: цена ещё не заходила') + '</span>'; }
    if (h.k === 'prev') {
      const P = h.P, q = P.s;
      const how = q.conf ? (q.side === 1 ? '↑ ' : '↓ ') + clk(q.conf) + (q.failed ? ' · слом DR ' + clk(q.failed) : ' · DR удержался') : P.k === 'PREV' ? 'вчерашняя RDR' : 'подтверждения не было';
      return '<b>' + P.name + ' · ' + h.nm + '</b> · ' + px(h.p) + '<br><span class="k">' + how + ' · цена сейчас ' + (ctx.s.priceNow > h.p ? 'выше' : 'ниже') + '</span>';
    }
    return '';
  }
  // «на уровне или дальше» of a level (spec §5.4): on each session's whole horizon and on the common hours after the slice;
  // the side is the sign of the level's u (levelUp: beyond the edge of play = along), and it is named
  function levelQuery(F, ctx, price, name) {
    const L = levelRat(F, price), up = levelUp(F, ctx, L), sl = sliceOf(ctx), dn = dirName(F, up);
    const ph = 'на ' + name + ' (' + sd(L.a / L.b) + ' SD) или дальше ' + dn + ' (свеча M5 дошла до уровня или дальше)';
    const cf = reachCount(F, L, up, null), cr = reachCount(F, L, up, sl);
    const full = pp(F, { event_id: up ? 'reach_up' : 'reach_down', region_kind: 'level', exact_price_bounds: [ratTxt(L)], level_sd: L.a / L.b, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: cf.yes, unknown_count: cf.unknown, no_event_count: cf.no, display_scope: 'level', binary: true, phrase: 'были ' + ph, horizon: F.from + ' до ' + clk(F.end) });
    const rest = pp(F, { event_id: up ? 'reach_up' : 'reach_down', region_kind: 'level', exact_price_bounds: [ratTxt(L)], level_sd: L.a / L.b, time_bounds: [sl, F.end], start_rule: 'после ' + clk(sl), end_rule: 'до ' + clk(F.end),
      yes_count: cr.yes, unknown_count: cr.unknown, no_event_count: cr.no, display_scope: 'level', binary: true, phrase: 'были ' + ph, horizon: sl >= F.end ? 'остатка блока нет' : 'после ' + clk(sl) + ' до ' + clk(F.end) });
    const t = todayReach(F, ctx, L, up);
    const today = 'сегодня: ' + (t.atAct ? 'уже за уровнем в момент ' + (F.brk ? 'слома' : 'подтверждения') + '; ' : '') + (t.t != null ? 'закрытая M5 ' + clk(t.t) + '–' + clk(t.t + 5) + ' дошла до уровня' : 'закрытые M5 после ' + clk(F.act0) + ' до уровня не доходили');
    const xc = crossCount(F, L, null);
    const cross = pp(F, { event_id: 'cross', region_kind: 'level', exact_price_bounds: [ratTxt(L)], level_sd: L.a / L.b, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: xc.yes, unknown_count: xc.unknown, no_event_count: xc.no, display_scope: 'details', binary: true, phrase: 'пересекали ' + name + ' свечой M5 (минимум ≤ уровня ≤ максимум)', horizon: F.from + ' до ' + clk(F.end) });
    return { L, up, full, rest, today, cf, cr, cross };
  }
  // the selected area (spec §7.1, §5.4, §8): the band's share over the whole session, the window's own share, the band's
  // visits (another event), and what today's closed M5 did there
  function areaInfo(F, ctx) {
    const a = st.area, ev = a.ev || st.ev, sl = sliceOf(ctx), out = { a, ev };
    const hasBand = isFinite(a.k0), hasTime = a.b0 != null;
    const tb = hasTime ? [F.f + 15 * a.b0, F.f + 15 * a.b1] : null;
    if (hasBand) out.band = evPass(F, ev, 'price_band', [a.k0, a.k1], null, areaCount(F, ev, { k0: a.k0, k1: a.k1 }));
    if (hasTime) out.win = evPass(F, ev, hasBand ? 'price_time' : 'time_band', hasBand ? [a.k0, a.k1] : null, tb, areaCount(F, ev, a));
    if (hasBand) {
      const vf = visitCount(F, a.k0, a.k1, null), vr = visitCount(F, a.k0, a.k1, sl);
      const ph = 'заходили в полосу ' + band(a.k0, a.k1) + ' SD (свеча M5 задевала её)';
      out.vfull = pp(F, { event_id: 'visit', region_kind: 'price_band', exact_price_bounds: [a.k0, a.k1], time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end), yes_count: vf.yes, unknown_count: vf.unknown, no_event_count: vf.no, display_scope: 'area', binary: true, phrase: ph, horizon: F.from + ' до ' + clk(F.end) });
      out.vrest = pp(F, { event_id: 'visit', region_kind: 'price_band', exact_price_bounds: [a.k0, a.k1], time_bounds: [sl, F.end], start_rule: 'после ' + clk(sl), end_rule: 'до ' + clk(F.end), yes_count: vr.yes, unknown_count: vr.unknown, no_event_count: vr.no, display_scope: 'area', binary: true, phrase: ph, horizon: sl >= F.end ? 'остатка блока нет' : 'после ' + clk(sl) + ' до ' + clk(F.end) });
      const t = todayVisit(F, ctx, a.k0, a.k1);
      out.today = 'сегодня: ' + (t.atAct ? 'закрытие ' + (F.brk ? 'слома' : 'подтверждения') + ' было в полосе; ' : '') + (t.t != null ? 'закрытая M5 ' + clk(t.t) + '–' + clk(t.t + 5) + ' заходила в полосу' : 'закрытые M5 после ' + clk(F.act0) + ' в полосу не заходили');
      out.prices = [Math.min(F.u2p(a.k0 / 10), F.u2p(a.k1 / 10)), Math.max(F.u2p(a.k0 / 10), F.u2p(a.k1 / 10))];
    }
    out.name = (hasBand ? band(a.k0, a.k1) + ' SD' : '') + (hasBand && hasTime ? ' × ' : '') + (hasTime ? clk(tb[0]) + '–' + clk(tb[1]) : '');
    return out;
  }
  function areaTip(F, ctx, part) {
    const I = areaInfo(F, ctx), lines = ['<b>Выбранная область · ' + I.name + '</b>'];
    if (I.band) lines.push((part === 'band' ? '▸ ' : '') + 'в полосе за всю сессию: ' + sentence(I.band));
    if (I.win) lines.push((part === 'window' ? '▸ ' : '') + 'в выбранном окне: ' + sentence(I.win));
    if (I.today) lines.push('<span class="k">' + I.today + '</span>');
    return lines.join('<br>');
  }

  // ---------- the zone map (zone-map-3, meaning/12): the server's zones, today's status, the passport ----------
  const ZST = { HOLDS: 'держится', POSSIBLE: 'возможна', IMPOSSIBLE: 'невозможна', STATUS_UNKNOWN: 'неизвестно: нет свечи M5' };
  const zonesOf = (F, ev) => F && F.zones ? F.zones[ev || st.ev] || null : null;
  const zoneName = z => band(z.price_low, z.price_high) + ' SD × ' + clk(z.time_start) + '–' + clk(z.time_end);
  function zonePass(F, ev, z) {
    const Zm = F.zones[ev];
    return pp(F, { event_id: ev, region_kind: 'zone_mask', exact_price_bounds: null, time_bounds: null, cell_mask: z.cell_mask.length, zone_id: z.zone_id,
      start_rule: F.from, end_rule: 'до ' + clk(F.end), yes_count: z.n_zone, unknown_count: Zm.unknown_count, no_event_count: Zm.no_event_count, display_scope: 'zone',
      phrase: F.names[ev].toLowerCase() + ' ' + ev + ' в зоне ' + z.label + ' (её точная область в ' + band(z.price_low, z.price_high) + ' SD × ' + clk(z.time_start) + '–' + clk(z.time_end) + ', не весь прямоугольник)', horizon: F.from + ' до ' + clk(F.end) });
  }
  // today's status of the zones of one event (zone-map-3 §24): today's provisional R or X from the closed M5 after the
  // activation and the reachable set of the final event: HOLDS (it lies in the zone), POSSIBLE (a farther price at a
  // later open can still land in the zone), IMPOSSIBLE; STATUS_UNKNOWN when a whole M5 is missing. At the slice of the
  // request the server's statuses are compared with these.
  // what today's path still allows (audit 2026-10-06, the same rule as zone status): the FINAL R can only be as deep as
  // today's deepest point after the confirmation or deeper, the final X only as far as today's furthest or further; a
  // cell must also not be over by the clock. okK: the price band can still hold today's final event; okCell: and its
  // 15 minutes are not over. Unknown today (a missing M5) → everything stays open
  function reachOf(F, ctx) {
    const sl = sliceOf(ctx), rows = todayRows(F, ctx), w = F.w0t, last = F.end - 5, known = rows.length === Math.max(0, (sl - F.act0) / 5);
    const ext = { R: null, X: null };
    if (known && rows.length) { ext.R = 10 * Math.min(...rows.map(r => r.lo)); ext.X = 10 * Math.max(...rows.map(r => r.hi)); }
    const okK = (ev, k) => !known || (sl <= last && (ext[ev] == null || (ev === 'R' ? k * w < ext[ev] : (k + 1) * w > ext[ev])));
    const okCell = (ev, k, b) => okK(ev, k) && (!known || (F.f + 15 * b + 10 >= sl && F.f + 15 * b <= last));
    return { sl, known, ext, okK, okCell };
  }
  // the look of a zone (drawing only; its status is not changed — A5): a POSSIBLE zone none of whose sessions sit in a
  // cell still reachable today is drawn as IMPOSSIBLE (its window is over: 0 of its sessions ahead)
  function zoneLook(F, ctx, ev) {
    const S = zoneStatus(F, ctx, ev), Rch = reachOf(F, ctx);
    return S.map((st_, i) => st_ !== 'POSSIBLE' ? st_ : F.ev[ev].pts.some(q => F.zcell[ev].get(q.k + '|' + q.b) === i && Rch.okCell(ev, q.k, q.b)) ? st_ : 'IMPOSSIBLE');
  }
  function zoneStatus(F, ctx, ev) {
    const Zm = F.zones[ev];
    if (!Zm) return [];
    const sl = sliceOf(ctx), rows = todayRows(F, ctx), w = F.w0t, last = F.end - 5;
    let out;
    if (rows.length !== Math.max(0, (sl - F.act0) / 5)) out = Zm.zones.map(() => 'STATUS_UNKNOWN');
    else {
      let q = null, v10 = null;
      if (rows.length) {
        let j = 0;
        for (let i = 1; i < rows.length; i++) if (ev === 'R' ? rows[i].lo < rows[j].lo : rows[i].hi > rows[j].hi) j = i;
        const v = ev === 'R' ? rows[j].lo : rows[j].hi;
        q = fdiv(10 * v, w) + '|' + Math.floor((rows[j].T - 5 - F.f) / 15); v10 = 10 * v;
      }
      out = Zm.zones.map(z => {
        if (q && z.cell_mask.some(([k, b]) => k + '|' + b === q)) return 'HOLDS';
        if (sl > last) return 'IMPOSSIBLE';
        for (const [k, b] of z.cell_mask) {
          if (q && !(ev === 'R' ? k * w < v10 : (k + 1) * w > v10)) continue;
          if (F.f + 15 * b + 10 >= sl && F.f + 15 * b <= last) return 'POSSIBLE';
        }
        return 'IMPOSSIBLE';
      });
    }
    const srv = F.r.today && F.r.today.zones && F.r.today.zones[ev];
    if (srv && F.r.today.slice === sl && JSON.stringify(srv.status) !== JSON.stringify(out) && !F.mismatch.includes('zone status ' + ev)) {
      F.mismatch.push('zone status ' + ev);
      console.error('design 24: the page and the server disagree on the zone status', ev, srv.status, out);
    }
    return out;
  }
  function zoneTip(F, ctx, h) {
    const Zm = F.zones[h.ev], z = Zm && Zm.zones[h.i];
    if (!z) return '';
    // the zone: its share of the family, its status today, its peak 15 minutes, and in its time window which of R and X
    // more of the family set there (both are shares of the same N)
    const s = zoneStatus(F, ctx, h.ev)[h.i], bs = z.cell_mask.map(q => q[1]), b0 = Math.min(...bs), b1 = Math.max(...bs) + 1, p = zonePass(F, h.ev, z);
    let nX = 0, nR = 0;
    for (let b = b0; b < b1; b++) { nX += F.ev.X.T.get(b) || 0; nR += F.ev.R.T.get(b) || 0; }
    const g = V ? (cloudsOf(F)[h.ev] || [])[h.i] : null, q0 = F.u2p(z.price_low / 10), q1 = F.u2p(z.price_high / 10);
    const lkz = ctx ? peakAhead(F, ctx, F.ev[h.ev].pts.filter(q => F.zcell[h.ev].get(q.k + '|' + q.b) === h.i), h.ev) : null, look = ctx ? zoneLook(F, ctx, h.ev)[h.i] : s;
    return '<div class="ih"><span style="color:' + cfg[h.ev] + '">' + z.label + '</span> · ' + F.names[h.ev].toLowerCase() + ' · ' + clk(z.time_start) + '–' + clk(z.time_end) + '<span class="zs zs-' + s + '">' + ZST[s] + '</span></div>' +
      '<div class="is">' + band(z.price_low, z.price_high) + ' SD · ' + px(Math.min(q0, q1)) + '–' + px(Math.max(q0, q1)) + '</div>' +
      '<div class="ibig" style="color:' + cfg[h.ev] + '">' + ppTxt(p) + '<span>семьи в этой зоне</span></div>' +
      (s === 'POSSIBLE' && look === 'IMPOSSIBLE' ? '<div class="il" style="color:#F23645">окно зоны прошло: впереди 0 сессий зоны</div>' : '') +
      (lkz ? '<div class="il" style="color:' + (lkz.past ? '#F23645' : cfg[h.ev]) + '">' + (lkz.past ? 'уже прошло · пиковые 15 минут ' : 'у семьи впереди · пиковые 15 минут ') + clk(F.f + 15 * lkz.b) + '–' + clk(F.f + 15 * lkz.b + 15) + ' · ' + pct(100 * lkz.n / F.N) + ' семьи</div>' : '') +
      '<div class="iq">в окне ' + clk(F.f + 15 * b0) + '–' + clk(F.f + 15 * b1) + ' свой экстремум поставили</div>' + twoBars(F, nX, nR, h.ev) +
      ifoot(F, ' · не шанс на сегодня');
  }
  // Two independent event-time shares on the same denominator N. They may overlap in the same session, so they are
  // compared only as two measurements; they are never presented as competing parts of one 100 %.
  function twoBars(F, cX, cR, first) {
    const mx = Math.max(cX, cR, 1), row = (ev, c) => '<div class="ib"><i style="color:' + cfg[ev] + '">' + ev + ' · ' + F.names[ev].toLowerCase() + '</i><span><em style="width:' + (100 * c / mx).toFixed(1) + '%;background:' + cfg[ev] + '"></em></span><b>' + pct(100 * c / F.N) + '</b></div>';
    const rows = first === 'R' ? row('R', cR) + row('X', cX) : row('X', cX) + row('R', cR);
    const gap = num(100 * Math.abs(cX - cR) / F.N, 1);
    if (cX > cR * 1.15) return rows + '<div class="im" style="color:' + cfg.X + '">X-время встречалось в этом окне чаще на ' + gap + ' п.п. <span class="k">две отдельные доли N, не части одной сотни</span></div>';
    if (cR > cX * 1.15) return rows + '<div class="im" style="color:' + cfg.R + '">R-время встречалось в этом окне чаще на ' + gap + ' п.п. <span class="k">две отдельные доли N, не части одной сотни</span></div>';
    return rows + '<div class="im">R- и X-время близки <span class="k">две отдельные доли N, не складываются в 100 %</span></div>';
  }
  const yr = (F, c) => c.unknown ? pct(100 * c.yes / F.N) + '–' + pct(100 * (c.yes + c.unknown) / F.N) : pct(100 * c.yes / F.N);
  const ifoot = (F, more) => '<div class="if">доля всей семьи · ' + F.from + ' до ' + clk(F.end) + ' · шаг доли ' + pct(100 / F.N) + (more || '') + '</div>';

  // ---------- toolbar and the day picker ----------
  function toolbar(ctx) {
    const F = ctx.F;
    dom('sess').innerHTML = ORDER.map(k => '<button data-s="' + k + '" class="' + (k === st.session ? 'on' : '') + '">' + k + '</button>').join('');
    dom('inst').innerHTML = ['NQ', 'ES', 'YM'].map(k => '<button data-i="' + k + '" class="' + (k === A.inst ? 'on' : '') + '">' + k + '</button>').join('');
    for (const b of dom('mode').querySelectorAll('button')) b.classList.toggle('on', b.dataset.m === st.mode);
    const nm = F ? F.names : ctx.s.failed ? { R: 'Откат против слома', X: 'Продолжение слома' } : { R: 'Откат', X: 'Продолжение' };
    // A freehand area belongs to the event currently in focus. Make that semantic choice explicit before the drag.
    const ab = dom('areab');
    if (ab) { ab.textContent = '▭ Область · ' + st.ev; ab.title = 'Выбрать область ' + st.ev + ' мышью: цена или цена × время; R/X меняется вместе с текущим фокусом'; }
    // R and X are on the chart together (operator 2026-10-01): the toolbar names them, there is no switch
    dom('ev').innerHTML = ['R', 'X'].map(e => '<span class="evc' + (st.mode === 'path' ? ' off' : '') + '" title="' + (F ? esc(F.what[e]) : '') + '"><i style="background:' + cfg[e] + '"></i>' + e + '<span> ' + nm[e].toLowerCase() + '</span></span>').join('');
    dom('areab').classList.toggle('on', st.tool);
    const x = A.day;
    if (A.src === 'live') {
      const et = x && x.fetched_at ? new Date(x.fetched_at).toLocaleTimeString('ru-RU', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
      dom('apibar').innerHTML = '<span class="feed">' + (A.error ? '<b class="err">' + esc(A.error) + '</b>' : x && x.status === 'ok' ? esc((x.feed || A.inst) + ' · ' + et + ' ET') : x ? esc(x.message || '') : 'загружаю…') + '</span>' +
        '<label class="auto"><input type="checkbox" id="auto21"' + (A.auto ? ' checked' : '') + '> Авто</label><button id="refresh21"' + (A.busy ? ' disabled' : '') + '>⟳ Обновить</button>';
    } else dom('apibar').innerHTML = A.error ? '<b class="err">' + esc(A.error) + '</b>' : x && x.status !== 'ok' ? '<span class="feed">' + esc(x.message || '') + '</span>' : '';
    const hd = A.src === 'hist' && A.date ? A.date.split('-').reverse().join('.') : '';
    dom('dayb').textContent = A.src === 'hist' ? 'История · ' + hd : 'История';
    dom('dayb').classList.toggle('hs', A.src === 'hist');
    dom('date').textContent = ctx.D.date;
    const cmp = dom('cmp22');
    cmp.style.display = A.src === 'live' ? '' : 'none';
    cmp.href = '/22/#inst=' + A.inst + '&session=' + st.session + (st.rp != null ? '&at=' + clk(st.rp) : '');
    dom('clock').innerHTML = A.src === 'hist'
      ? '<div style="display:flex;gap:6px"><div class="pill hs"><span class="dot"></span>' + (st.rp != null ? 'История ' + st.session + ' · ' + clk(ctx.obs) : 'История · день закрыт') + '</div>' + (st.rp != null ? '<button id="back">К концу дня</button>' : '') + '</div>'
      : ctx.live ? '<div class="pill"><span class="dot"></span><span id="live">LIVE ' + clk(NOW) + ' ET</span></div>'
        : '<div style="display:flex;gap:6px"><div class="pill rp"><span class="dot"></span>Повтор ' + ctx.s.k + ' · ' + clk(ctx.obs) + '</div><button id="back">К текущему</button></div>';
    dom('menu').innerHTML = LAYERS.map(([k, n, col]) => '<label><input type="checkbox" data-l="' + k + '"' + (st.L[k] ? ' checked' : '') + '><span class="sw" style="background:' + col + '"></span>' + n + '</label>').join('');
  }
  function dayPicker() {
    const d = A.date || '2025-12-17';
    dom('dayp').innerHTML = '<div class="dr"><button id="dprev" title="Предыдущий торговый день">‹</button><input type="date" id="dinput" min="2006-01-03" max="2025-12-31" value="' + d + '" title="Любой день 2006–2025: его семьи берутся только из сессий раньше него"><button id="dnext" title="Следующий торговый день">›</button></div>' +
      '<div class="dr"><button id="drand">Случайный день</button><div class="sp"></div><button id="dlive"' + (A.src === 'live' ? ' disabled' : '') + '>Сегодня · LIVE</button></div>';
  }
  // the trading dates of the base on which the chosen session has an established confirmation (a family to show)
  async function ensureDates() {
    if (!A.dates || A.dates.inst !== A.inst) {
      try { const r = await (await fetch('/api/d24/dates?instrument=' + A.inst)).json(); if (r.status === 'ok') A.dates = { inst: A.inst, list: r.dates }; } catch (e) { /* the picker still works by date */ }
    }
    const L = st.session[0];
    return A.dates ? A.dates.list.filter(x => x[1].includes(L)).map(x => x[0]) : [];
  }
  // a history day for the chosen session when the live day has no family (the live moment never blocks the review)
  async function histFallback() { const list = await ensureDates(); if (list.length) openHist(list[list.length - 1]); }
  function openHist(date) {
    if (!date) return;
    A.src = 'hist'; A.date = date; A.day = null; A.D = null; A.jump = true; A.fams.clear();
    st.pin = null; st.hover = null; st.area = null; st.col = null; st.view = 'auto';
    try { history.replaceState(null, '', '#date=' + date + '&inst=' + A.inst + '&session=' + st.session); } catch (e) { /* optional */ }
    loadDay(false);
  }
  function openLive() {
    A.src = 'live'; A.date = null; A.day = null; A.D = null; A.fams.clear();
    st.rp = null; st.pin = null; st.hover = null; st.area = null; st.col = null; st.view = 'auto'; st.userSession = false;
    try { history.replaceState(null, '', location.pathname); } catch (e) { /* optional */ }
    loadDay(false);
  }

  /*__PANEL24__*/
  // ---------- &geo=1: the screen's geometry for the annotated specification (spec/ekran-24/, tools/annotate.py) ----------
  // Page pixels of every layer and block in this frame, written into <script id="geo" type="application/json"> so a
  // headless browser can dump them next to its screenshot of the same address. Changes nothing on the screen.
  function geoDump(ctx) {
    const F = ctx.F, r0 = cv.getBoundingClientRect(), ox = r0.left, oy = r0.top, s = ctx.s;
    const P = (x, y) => [Math.round(ox + x), Math.round(oy + y)];
    const rect = el => { if (!el) return null; const r = el.getBoundingClientRect(); return r.width || r.height ? [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] : null; };
    const G = { url: location.hash, W: innerWidth, H: innerHeight, mode: st.mode, view: F ? F.view : null, dom: {}, chart: {}, panel: {}, det: {} };
    for (const id of ['inst', 'sess', 'date', 'mode', 'ev', 'areab', 'apibar', 'dayb', 'step21', 'panel21toggle', 'lay', 'cfgb', 'cmp22', 'clock', 'panel', 'insp', 'det', 'deth', 'nav']) G.dom[id] = rect(dom(id));
    const pl = [...panel.children];
    G.panel.blocks = pl.map(el => ({ cls: el.className, text: el.innerText.split('\n')[0].slice(0, 40), r: rect(el) }));
    G.panel.links = [...panel.querySelectorAll('[data-l21]')].map(el => ({ text: el.innerText.split('\n')[0].slice(0, 40), r: rect(el) }));
    G.panel.now = rect(panel.querySelector('.p24-now'));
    G.panel.bar = rect(panel.querySelector('.p24-bar'));
    G.panel.out = rect(panel.querySelector('.p24-out'));
    G.panel.seg = rect(panel.querySelector('.p24-seg'));
    G.panel.notes = [...panel.querySelectorAll('.p21-note')].map(rect);
    G.det.cards = [...document.querySelectorAll('#detg .dcard')].map(el => ({ title: el.querySelector('.dt') ? el.querySelector('.dt').innerText : '', r: rect(el) }));
    const C2 = G.chart;
    C2.plot = [Math.round(ox), Math.round(oy), Math.round(V.plot.w), Math.round(V.plot.h)];
    C2.axis = [Math.round(ox + V.plot.w), Math.round(oy), V.axisW, Math.round(V.plot.h)];
    if (V.projW) C2.proj = [Math.round(ox + V.proj.x), Math.round(oy), V.projW, Math.round(V.plot.h)];
    if (V.projCols) C2.projCols = { R: [Math.round(ox + V.projCols.R[0]), Math.round(ox + V.projCols.R[1])], X: [Math.round(ox + V.projCols.X[0]), Math.round(ox + V.projCols.X[1])] };
    if (V.projBars) { C2.projRow = {}; for (const ev of ['R', 'X']) { const zs = F && F.zones[ev] ? F.zones[ev].zones : []; if (!zs.length) continue; const ks = zs[0].cell_mask.map(q => q[0]), mid = Math.round((Math.min(...ks) + Math.max(...ks)) / 2), b = V.projBars.find(q => q.ev === ev && q.k === mid) || V.projBars.find(q => q.ev === ev); if (b) C2.projRow[ev] = P(V.projCols[ev][0] + 18, (b.top + b.bot) / 2); } }
    C2.band = V.stripOn ? [Math.round(ox), Math.round(oy + V.band.y), Math.round(V.band.w), Math.round(V.band.h)] : null;
    C2.bandCy = V.bandCy != null ? Math.round(oy + V.bandCy) : null;
    C2.taxis = [Math.round(ox), Math.round(oy + V.taxisY), Math.round(V.plot.w), V.timeH];
    C2.legend = P(12, 14);
    C2.status = P(12, 32);
    if (s.drH != null) {
      C2.box = [...P(V.X(s.start), V.Y(s.drH)), Math.round(V.X(s.formed) - V.X(s.start)), Math.round(V.Y(s.drL) - V.Y(s.drH))];
      C2.drH = P(V.X(s.formed) + 120, V.Y(s.drH)); C2.drL = P(V.X(s.formed) + 120, V.Y(s.drL));
      C2.idrH = P(V.X(s.formed) + 200, V.Y(s.idrH)); C2.idrL = P(V.X(s.formed) + 200, V.Y(s.idrL));
      C2.mid = P(V.X(s.formed) + 260, V.Y(s.mid));
      const w = s.idrH - s.idrL, side = s.side || 1;
      C2.std = P(V.plot.w - 140, V.Y((side === 1 ? s.idrH : s.idrL) + side * w));
      C2.axisDR = P(V.plot.w + 40, V.Y(s.drH)); C2.axisIDR = P(V.plot.w + 40, V.Y(s.idrH));
      C2.fracs = P(V.X(s.start) - 14, V.Y(s.idrL + 0.3 * w));
      if (s.priceNow != null) C2.priceNow = P(V.plot.w + 40, V.Y(s.priceNow));
    }
    if (s.conf) { const b = ctx.D.bars.find(q => q.t === s.conf - 5); if (b) C2.pill = P(V.X(b.t + 2.5), s.side === 1 ? V.Y(b.h) - 15 : V.Y(b.l) + 15); }
    if (s.failed) { const b = ctx.D.bars.find(q => q.t === s.failed - 5); if (b) C2.brkPill = P(V.X(b.t + 2.5), s.side === 1 ? V.Y(b.l) + 15 : V.Y(b.h) - 15); }
    C2.slice = P(V.X(sliceOf(ctx)), V.plot.h * 0.42);
    C2.end = P(V.X(SESS[ctx.s.k].end), 70);
    const lastBar = ctx.D.bars.filter(b => b.t + 5 <= (ctx.live ? NOW : ctx.obs)).pop();
    if (lastBar) C2.candle = P(V.X(lastBar.t + 2.5), V.Y(lastBar.h) - 4);
    if (F && st.mode === 'bounds') {
      const CL = cloudsOf(F);
      C2.zones = (V.zoneHit || []).map(z => { const g = CL[z.ev][z.i]; return { ev: z.ev, i: z.i, label: g.z.label, labelBox: [...P(z.box[0], z.box[1]), Math.round(z.box[2]), Math.round(z.box[3])], spot: P(g.kd.spot.x, g.kd.spot.y), bb: [...P(g.bb[0], g.bb[1]), Math.round(g.bb[2] - g.bb[0]), Math.round(g.bb[3] - g.bb[1])] }; });
      C2.caps = (V.caps || []).map(q => ({ ev: q.ev, i: q.i, box: [...P(q.box[0], q.box[1]), Math.round(q.box[2]), Math.round(q.box[3])] }));
      C2.hills = (V.hills || []).map(q => { const t = q.scr.reduce((a, p) => (q.ev === 'X' ? p[1] < a[1] : p[1] > a[1]) ? p : a, q.scr[0]); return { ev: q.ev, i: q.i, top: P(t[0], t[1] + (q.ev === 'X' ? 6 : -6)) }; });
      if (V.bandCols && V.bandCols.length) { const T = F.ev.X.T, R = F.ev.R.T; let best = null; for (const c of V.bandCols) { const n = (T.get(c.b) || 0) + (R.get(c.b) || 0); if (!best || n > best.n) best = { c, n }; } C2.column = P((best.c.x0 + best.c.x1) / 2, V.bandCy - 10); }
      if (V.stripUnk) C2.unk = P(V.stripUnk[0] + 7, V.stripUnk[1] + V.stripUnk[3] / 2);
      const star = (ev, inZone, broken) => { const q = F.ev[ev].pts.find(p => !!F.zcell[ev].has(p.k + '|' + p.b) === inZone && (broken == null || (p.m.outcome === 'broken') === broken) && V.X(p.t + 2.5) > V.X(sliceOf(ctx)) + 20 && V.X(p.t + 2.5) < V.plot.w - 80 && V.Y(p.p) > 60 && V.Y(p.p) < V.plot.h - 20); return q ? P(V.X(q.t + 2.5), V.Y(q.p)) : null; };
      C2.stars = { Rzone: star('R', true), Xzone: star('X', true), Rres: star('R', false, false), Xres: star('X', false, false), ring: star('R', false, true) || star('X', false, true) };
      if (V.lk) { const t0 = F.f + 15 * V.lk.b; C2.link = { spot: P(V.lk.x, V.lk.y), line: P((V.X(t0) + V.X(t0 + 15)) / 2, (V.lk.y + V.plot.h) / 2), pill: P(V.X(t0), V.taxisY + 14) }; }
      if (V.win && V.win.pA != null) C2.pricePill = P(V.plot.w + 40, V.Y(V.win.pA));
      const h = hv();
      if (h && h.k === 'pt' && F.M[h.i]) { const m = F.M[h.i], at = e => m[e].s === 'known' ? P(V.X(m[e].t + 2.5), V.Y(F.u2p(m[e].v / m.w))) : null; C2.pair = { R: at('R'), X: at('X') }; const j = F.grid.findIndex(T => T > m.act + 60 && m.path[F.grid.indexOf(T)]); if (j >= 0) C2.pair.path = P(V.X(F.grid[j] - 2.5), V.Y(F.u2p(m.path[j][2] / m.w))); }
      if (st.area && V.areaHit) C2.area = V.areaHit.map(a => ({ part: a.part, box: [...P(a.box[0], a.box[1]), Math.round(a.box[2]), Math.round(a.box[3])] }));
      if (h && h.k === 'lvl' && h.l) C2.level = P(V.plot.w - 300, V.Y(h.l.p));
      if (h && h.k === 'pcell') { const b = (V.projBars || []).find(q => q.ev === h.ev && q.k === h.k0); if (b) C2.hovRow = P(V.projCols[h.ev][0] + 14, (b.top + b.bot) / 2); C2.hovBand = P(V.plot.w * 0.55, (cellY(F, h.k0, h.k1)[0] + cellY(F, h.k0, h.k1)[1]) / 2); }
      if (h && h.k === 'tcell') { const c = (V.bandCols || []).find(q => q.b === h.b0); if (c) { C2.hovCol = P((c.x0 + c.x1) / 2, V.bandCy - 6); C2.hovColChart = P((c.x0 + c.x1) / 2, V.plot.h * 0.3); } }
      if (h && h.k === 'zone') { const g = CL[h.ev][h.i]; C2.zoneCells = P(V.X(F.f + 15 * g.z.cell_mask[0][1] + 7.5), V.Y(F.u2p((g.z.cell_mask[0][0] + 0.5) / 10))); }
    }
    if (F && st.mode === 'path') {
      const film = filmOf(F), j = Math.floor(film.length * 0.6), cd = film[j], k = [...cd.cells.keys()][0];
      if (cd && k != null) C2.filmCell = P(V.X(cd.T - 2.5), (cellY(F, k, k + 1)[0] + cellY(F, k, k + 1)[1]) / 2);
      if (V.projBars && V.projBars.length) { const b = V.projBars[Math.floor(V.projBars.length / 2)]; C2.filmCol = P(V.proj.x + 20, (b.top + b.bot) / 2); }
    }
    let el = document.getElementById('geo');
    if (!el) { el = document.createElement('script'); el.type = 'application/json'; el.id = 'geo'; document.body.appendChild(el); }
    el.textContent = JSON.stringify(G);
  }
  function placeNav() {
    if (!V) return;
    nav.style.left = (V.plot.w / 2 - 50) + 'px';
    nav.style.top = (V.plot.h - 44) + 'px';
    nav.classList.toggle('show', st.navHover || (st.mx >= 0 && st.mx < V.plot.w && st.my < V.plot.h && st.my > V.plot.h * 0.5));
  }
  // the inspector (operator 2026-10-01): what is under the cursor is read in one fixed place at the bottom right, never
  // over the candles; with nothing under the cursor it shows the pinned object, else the family's snapshot in one line
  function showTip(h) {
    const el = dom('insp');
    if (!el || !V) return;
    const ctx = V.ctx, use = h && h.k !== 'stripBg' ? h : st.pin;
    let html = use ? tipHtml(use, ctx) : '';
    if (!html && ctx.F && ctx.F.N) html = '<div class="ih">Слепок семьи</div><div class="is">' + esc(ctx.F.cond) + '</div>' + ifoot(ctx.F, ' · зафиксирован при ' + (ctx.F.brk ? 'сломе ' : 'подтверждении ') + clk(ctx.F.act0));
    if (el._h !== html) { el.innerHTML = html; el._h = html; }
  }

  // ---------- interaction (TradingView-like; an area is drawn with «▭ Область» or Shift) ----------
  let raf = 0, fullNext = false;
  const redraw = full => { fullNext = fullNext || !!full; if (!raf) raf = requestAnimationFrame(() => { raf = 0; const f = fullNext; fullNext = false; render(f); }); };
  function animStrip() { redraw(); }
  const local = e => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  // an area from a drag on the chart: price cells x 15-minute cells, snapped to the grid of the distributions
  function areaFromDrag(F, x0, y0, x1, y1) {
    const ka = F.cellOfP(V.P(y0)), kb = F.cellOfP(V.P(y1)), clampB = b => clamp(b, 0, F.nb - 1);
    const ba = clampB(Math.floor((V.T(x0) - F.f) / 15)), bb = clampB(Math.floor((V.T(x1) - F.f) / 15));
    return { k0: Math.min(ka, kb), k1: Math.max(ka, kb) + 1, b0: Math.min(ba, bb), b1: Math.max(ba, bb) + 1 };
  }
  cv.addEventListener('mousemove', e => {
    const [x, y] = local(e);
    st.mx = x; st.my = y;
    const d = st.drag;
    if (d) {
      const dx = x - d.x, dy = y - d.y, F = V.ctx.F;
      if (Math.abs(dx) + Math.abs(dy) > 3) d.moved = true;
      if (d.zone === 'draw' && F && d.moved) d.area = Object.assign(areaFromDrag(F, d.x, d.y, x, y), { ev: st.ev });
      else if (d.zone === 'proj' && F && d.moved && st.mode === 'bounds') { const ka = F.cellOfP(V.P(d.y)), kb = F.cellOfP(V.P(y)); d.area = { k0: Math.min(ka, kb), k1: Math.max(ka, kb) + 1, ev: ((V.projBars || []).find(q => d.y >= q.top - 1 && d.y <= q.bot + 1 && d.x >= q.x0 && d.x <= q.x1) || (V.projBars || []).find(q => d.y >= q.top - 1 && d.y <= q.bot + 1) || { ev: st.ev }).ev }; }
      else if (d.zone === 'strip' && F && d.moved) {
        const b0 = clamp(Math.floor((V.T(d.x) - F.f) / 15), 0, F.nb - 1), b1 = clamp(Math.floor((V.T(x) - F.f) / 15), 0, F.nb - 1);
        const a = st.area && isFinite(st.area.k0) ? st.area : { k0: -Infinity, k1: Infinity };
        d.area = { k0: a.k0, k1: a.k1, b0: Math.min(b0, b1), b1: Math.max(b0, b1) + 1, ev: (st.area && st.area.ev) || st.ev };
      }
      else if (d.zone === 'plot') {
        // operator 2026-10-06: the right edge never leaves the session end; a horizontal drag only adds or removes history
        anchorRight(d.v0 - dx * (d.v1 - d.v0) / V.plot.w);
        if (Math.abs(y - d.y) > 2 || !st.auto) { const ps = d.p1 - d.p0; st.auto = false; st.p0 = d.p0 + dy * ps / V.plot.h; st.p1 = d.p1 + dy * ps / V.plot.h; }
      } else if (d.zone === 'paxis') {
        const f = Math.exp(dy * 0.006), m = (d.p0 + d.p1) / 2, half = (d.p1 - d.p0) / 2 * f;
        st.auto = false; st.p0 = m - half; st.p1 = m + half;
      } else if (d.zone === 'taxis') {
        anchorRight(rightEdge() - (d.v1 - d.v0) * Math.exp(-dx * 0.005));
      }
      cv.style.cursor = d.zone === 'plot' ? 'grabbing' : d.zone === 'paxis' ? 'ns-resize' : d.zone === 'taxis' ? 'ew-resize' : 'crosshair';
      tip.hidden = true;
      redraw();
      return;
    }
    const h = hit(x, y), key = o => JSON.stringify(o && Object.assign({}, o, { q: undefined, l: undefined, v: undefined, P: undefined, same: undefined }));
    const was = key(st.hover);
    st.hover = h && !['paxis', 'taxis', 'stripBg'].includes(h.k) ? h : (h && h.k === 'stripBg' ? h : null);
    if (st.hover && st.hover.ev) st.ev = st.hover.ev;      // the event in focus: what the panel and the area speak of
    cv.style.cursor = st.tool ? 'crosshair' : !h ? 'crosshair' : h.k === 'paxis' ? 'ns-resize' : h.k === 'taxis' ? 'ew-resize' : ['pcell', 'tcell', 'pt', 'area', 'col', 'fcell', 'unk'].includes(h.k) ? 'pointer' : 'crosshair';
    showTip(st.hover);
    if (key(st.hover) !== was) { animStrip(); redraw(true); } else redraw();
  });
  cv.addEventListener('mouseleave', () => { st.mx = -1; st.my = -1; if (!st.drag) { st.hover = null; tip.hidden = true; animStrip(); } redraw(true); });
  cv.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    const [x, y] = local(e), F = V.ctx.F;
    let zone = x > V.plot.w && x < V.plot.w + V.axisW && y < V.plot.h ? 'paxis' : V.projW && x >= V.proj.x && y < V.plot.h ? 'proj' : y > V.taxisY ? 'taxis' : y > V.plot.h - (V.stripOn ? V.bandOv || 0 : 0) ? (V.stripOn && x <= V.plot.w ? 'strip' : 'none') : 'plot';
    if (zone === 'plot' && F && (st.tool || e.shiftKey)) zone = 'draw';
    st.drag = { x, y, zone, v0: st.v0, v1: st.v1, p0: V.p0, p1: V.p1, moved: false, h: st.hover };
    e.preventDefault();
  });
  window.addEventListener('mouseup', e => {
    const d = st.drag;
    if (!d) return;
    st.drag = null; cv.style.cursor = 'crosshair';
    if (d.moved && d.area) { st.area = d.area; st.hover = null; render(true); return; }
    if (d.moved) { redraw(); return; }
    const [x, y] = local(e);
    click(x, y, d);
  });
  function click(x, y, d) {
    const h = hit(x, y), F = V.ctx.F;
    if (h && h.k === 'pcell' && F && st.mode === 'bounds') {        // a click on the price histogram selects its band
      const same = st.area && st.area.k0 === h.k0 && st.area.k1 === h.k1 && st.area.b0 == null && st.area.ev === h.ev;
      st.area = same ? null : { k0: h.k0, k1: h.k1, ev: h.ev || st.ev }; render(true); return;
    }
    if (h && h.k === 'fcell' && d.zone === 'proj') { st.col = h.j; render(true); return; }
    if (h && h.k === 'tcell' && F) {                                  // a click on the time histogram: a window (for the band)
      const a = st.area && isFinite(st.area.k0) ? st.area : null, same = st.area && st.area.b0 === h.b0 && st.area.b1 === h.b1;
      st.area = same ? (a ? { k0: a.k0, k1: a.k1, ev: a.ev } : null) : { k0: a ? a.k0 : -Infinity, k1: a ? a.k1 : Infinity, b0: h.b0, b1: h.b1, ev: a ? a.ev : st.ev };
      render(true); return;
    }
    if (h && h.k === 'zone' && d.zone === 'strip') { pin(h); return; }
    if (d.zone !== 'plot' && d.zone !== 'draw') return;
    if (h && h.k === 'pt') { pin(h); return; }
    if (h && (h.k === 'col' || h.k === 'fcell')) { st.col = st.col === h.j ? null : h.j; render(true); return; }
    if (h && h.k === 'area') { pin({ k: 'area', part: h.part }); return; }
    if (h && h.k === 'zone') { pin(h); return; }
    if (d.zone === 'strip') return;
    const b = barAt(V.ctx, V.T(x));
    if (b && y >= V.Y(b.h) - 6 && y <= V.Y(b.l) + 6 && b.t + 5 <= NOW) { replayAt(b.t + 5); return; }
    if (h && ['lvl', 'prev', 'vib'].includes(h.k)) { pin(h); return; }
    if (st.pin) { st.pin = null; st.hover = null; render(true); }
  }
  // R and X are on screen together: the event is part of the key (zone R2 is not zone X2), and so are the band, the
  // window and the cell, so the passport of the first bottom window follows what is under the cursor
  const pinKey = h => h ? [h.k, h.ev, h.i, h.id, h.j, h.part, h.cat, h.t, h.p, h.k0, h.b0, h.kk].join('|') : '';
  function pin(h) { st.pin = pinKey(st.pin) === pinKey(h) ? null : h; st.hover = null; tip.hidden = true; render(true); }
  cv.addEventListener('dblclick', e => {
    const [x, y] = local(e);
    if (x > V.plot.w && x < V.plot.w + V.axisW && y < V.plot.h) { st.auto = true; redraw(); }
    else if (y > V.taxisY && y < V.taxisY + V.timeH) { fitSession(st.session); redraw(); }
  });
  cv.addEventListener('wheel', e => {
    const [x] = local(e);
    e.preventDefault();
    if (x > V.plot.w) {
      const f = Math.exp(e.deltaY * 0.0015), m = (V.p0 + V.p1) / 2, half = (V.p1 - V.p0) / 2 * f;
      st.auto = false; st.p0 = m - half; st.p1 = m + half;
    } else if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
      anchorRight(st.v0 + (e.deltaX || e.deltaY) * (st.v1 - st.v0) / V.plot.w * 0.6);
    } else {
      // design 22 (operator 2026-09-29): the right edge stays at the session end + 45 minutes; the wheel only adds or
      // removes history on the left; zooming in stops at the «↺» view (box start .. session end)
      anchorRight(rightEdge() - (rightEdge() - st.v0) * Math.exp(e.deltaY * 0.0012));   // the same left limit as every gesture
    }
    redraw();
  }, { passive: false });
  nav.addEventListener('mouseenter', () => { st.navHover = true; placeNav(); });
  nav.addEventListener('mouseleave', () => { st.navHover = false; placeNav(); });
  nav.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    const z = +b.dataset.z;
    if (z === 0) { fitSession(st.session); if (st.session === 'RDR') { st.v0 = 545; st.v1 = 1005; } }
    else anchorRight(rightEdge() - (st.v1 - st.v0) * (z > 0 ? 1.35 : 1 / 1.35));
    redraw();
  });
  function stepReplay(dt) {
    const t0 = st.rp != null ? st.rp : Math.floor(NOW / 5) * 5, t = t0 + dt;
    if (t >= NOW) backLive();
    else if (sessOf(t)) { st.rp = t; if (sessOf(t) !== st.session) { st.session = sessOf(t); st.area = null; st.col = null; st.view = 'auto'; } st.pin = null; render(true); }
  }
  window.addEventListener('keydown', e => {
    if (e.target && /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
    if (e.key === 'Escape') { if (st.drag) st.drag = null; else if (st.pin) st.pin = null; else if (st.area) st.area = null; else if (st.tool) st.tool = false; else if (st.stripPin) st.stripPin = false; else if (st.rp != null && A.src === 'live') backLive(); animStrip(); render(true); }
    else if (e.altKey && (e.key === 'r' || e.key === 'R' || e.key === 'к' || e.key === 'К')) { e.preventDefault(); fitSession(st.session); if (st.session === 'RDR') { st.v0 = 545; st.v1 = 1005; } redraw(); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); stepReplay(e.key === 'ArrowLeft' ? -5 : 5); }
  });
  root.addEventListener('click', e => {
    const t = e.target;
    if (t.closest('#sess button')) { st.userSession = true; selSession(t.closest('button').dataset.s); }
    else if (t.closest('#inst button')) {
      A.inst = t.closest('button').dataset.i; A.day = null; A.D = null; A.fams.clear(); st.area = null; st.pin = null; st.view = 'auto';
      if (A.src === 'hist') { A.jump = true; try { history.replaceState(null, '', '#date=' + A.date + '&inst=' + A.inst + '&session=' + st.session); } catch (e) { /* optional */ } }
      loadDay(false);
    }
    else if (t.closest('#mode button')) { st.mode = t.closest('button').dataset.m; st.hover = null; st.pin = null; render(true); }
    else if (t.closest('#ev button')) { if (st.mode === 'bounds') { st.ev = t.closest('button').dataset.e; st.hover = null; if (st.pin && st.pin.k === 'pt') st.pin = null; render(true); } }
    else if (t.id === 'areab') { st.tool = !st.tool; render(true); }
    else if (t.id === 'refresh21') loadDay(true);
    else if (t.id === 'back') backLive();
    else if (t.id === 'lay') { st.menu = !st.menu; dom('menu').hidden = !st.menu; t.classList.toggle('on', st.menu); dom('cfgp').hidden = true; dom('cfgb').classList.remove('on'); dom('dayp').hidden = true; }
    else if (t.id === 'cfgb') { const o = dom('cfgp').hidden; dom('cfgp').hidden = !o; t.classList.toggle('on', o); st.menu = false; dom('menu').hidden = true; dom('lay').classList.remove('on'); dom('dayp').hidden = true; }
    else if (t.id === 'dayb') { const o = dom('dayp').hidden; if (o) dayPicker(); dom('dayp').hidden = !o; t.classList.toggle('on', o); st.menu = false; dom('menu').hidden = true; dom('cfgp').hidden = true; ensureDates(); }
    else if (t.id === 'dlive') { dom('dayp').hidden = true; openLive(); }
    else if (t.id === 'dprev' || t.id === 'dnext' || t.id === 'drand') {
      ensureDates().then(list => {
        if (!list.length) return;
        const cur_ = dom('dinput').value || A.date || list[list.length - 1];
        let d;
        if (t.id === 'drand') d = list[Math.floor(Math.random() * list.length)];
        else { const i = list.findIndex(x => x >= cur_); d = t.id === 'dprev' ? list[Math.max(0, (i < 0 ? list.length : i) - 1)] : list[Math.min(list.length - 1, i < 0 ? list.length - 1 : list[i] === cur_ ? i + 1 : i)]; }
        dom('dinput').value = d; openHist(d);
      });
    }
    else {
      if (!t.closest('#menu') && st.menu) { st.menu = false; dom('menu').hidden = true; dom('lay').classList.remove('on'); }
      if (!t.closest('#cfgp') && !dom('cfgp').hidden) { dom('cfgp').hidden = true; dom('cfgb').classList.remove('on'); }
      if (!t.closest('#dayp') && !dom('dayp').hidden) { dom('dayp').hidden = true; dom('dayb').classList.remove('on'); }
    }
  });
  dom('dayp').addEventListener('change', e => { if (e.target.id === 'dinput' && e.target.value) openHist(e.target.value); });
  dom('apibar').addEventListener('change', e => { if (e.target.id === 'auto21') { A.auto = e.target.checked; try { localStorage.setItem('drlab.auto', A.auto ? '1' : '0'); } catch (x) { /* optional */ } schedule(); } });
  dom('menu').addEventListener('change', e => {
    const k = e.target.dataset.l;
    if (k) { st.L[k] = e.target.checked; if (k === 'det') { st.detPin = false; } render(true); }
  });
  // the settings panel: built from SCHEMA; every change redraws at once and is kept in this browser
  function cfgPanel() {
    const row = ([k, n, type, a, b, step]) => {
      const v = cfg[k];
      if (type === 'color') return '<label class="cr"><span>' + n + '</span><input type="color" data-c="' + k + '" value="' + v + '"></label>';
      if (type === 'boxfill') return '<label class="cr"><span>' + n + '</span><select data-c="' + k + '">' + Object.keys(BOXFILL).map(d => '<option value="' + d + '"' + (d === v ? ' selected' : '') + '>' + BOXFILL[d] + '</option>').join('') + '</select></label>';
      if (type === 'dash') return '<label class="cr"><span>' + n + '</span><select data-c="' + k + '">' + Object.keys(DASH).map(d => '<option value="' + d + '"' + (d === v ? ' selected' : '') + '>' + DASH_NAMES[d] + '</option>').join('') + '</select></label>';
      return '<label class="cr"><span>' + n + '</span><input type="range" data-c="' + k + '" min="' + a + '" max="' + b + '" step="' + (step || 1) + '" value="' + v + '"><em>' + v + '</em></label>';
    };
    dom('cfgp').innerHTML = '<div class="ch"><b>Настройки</b><button id="cfgReset">Сбросить</button></div>' + SCHEMA.map(([t, rows]) => '<div class="cg">' + t + '</div>' + rows.map(row).join('')).join('');
  }
  dom('cfgp').addEventListener('input', e => {
    const k = e.target.dataset.c;
    if (!k) return;
    const d = DEF[k];
    cfg[k] = typeof d === 'number' ? +e.target.value : e.target.value;
    const em = e.target.parentNode.querySelector('em'); if (em) em.textContent = e.target.value;
    saveCfg(); redraw(true);
  });
  dom('cfgp').addEventListener('click', e => { const b = e.target.closest('button'); if (b && b.id === 'cfgReset') { Object.assign(cfg, DEF); saveCfg(); cfgPanel(); redraw(true); } });
  window.addEventListener('resize', () => redraw(true));

  // ---------- data: the live day from the server (refreshed after every M5 close while a session runs), or a history day ----------
  function etMinute() {
    const p = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }).formatToParts(new Date());
    const g = t => +p.find(x => x.type === t).value;
    return (g('hour') % 24) * 60 + g('minute') + g('second') / 60;
  }
  function running() { const k = sessionNow(); return A.src === 'live' && A.day && A.day.status === 'ok' && NOW >= SESS[k].start && NOW < SESS[k].end; }
  function schedule() {
    clearTimeout(A.timer);
    if (!A.auto || !running()) return;
    const step = A.day.switched ? 5 : 1, m = etMinute(), wait = ((Math.floor(m / step) + 1) * step + (step === 1 ? 3 : 20) / 60 - m) * 60000;
    A.timer = setTimeout(() => loadDay(true), Math.max(5000, wait));
  }
  function takeDay(x, first) {
    A.day = x;
    if (x.status !== 'ok') return;
    NOW = A.src === 'hist' ? 1020 : Math.floor(x.now);
    PREV = x.prev ? { k: 'PREV', name: x.prev.name, start: -870, formed: -810, drH: x.prev.drH, drL: x.prev.drL, idrH: x.prev.idrH, idrL: x.prev.idrL, open: x.prev.open, close: x.prev.close } : null;
    if (A.src === 'live') {
      if (!st.userSession && (first || st.rp == null)) st.session = sessionNow();
      if (first) { fitSession(st.session); if (st.session === 'RDR' && st.rp == null) { st.v0 = 545; st.v1 = 1005; } }
    }
  }
  async function loadDay(refresh) {
    A.busy = true; A.error = null; toolbar(cur());
    const first = !A.day;
    try {
      const q = '/api/d24/day?instrument=' + A.inst + (A.src === 'hist' ? '&date=' + A.date : '');
      let x = await (await fetch(q)).json();
      if (A.src === 'live') {
        const stale = x.status !== 'ok' || Date.now() - Date.parse(x.fetched_at) > 180000;
        if (refresh || stale) {
          if (x.status === 'ok' && first) { takeDay(x, true); render(true); }      // the saved day at once, the refresh after
          const y = await (await fetch(q + '&refresh=1')).json();
          if (y.status === 'error') A.error = /CDP|9222|TradingView/.test(y.message || '') ? 'TradingView не отвечает: свечи последнего обновления' : (y.message || '').slice(0, 80); else x = y;
        }
        takeDay(x, first && !A.day);
      } else A.day = x;
      if (A.src === 'hist' && x.status === 'ok') {
        NOW = 1020;
        PREV = x.prev ? { k: 'PREV', name: x.prev.name, start: -870, formed: -810, drH: x.prev.drH, drL: x.prev.drL, idrH: x.prev.idrH, idrL: x.prev.idrL, open: x.prev.open, close: x.prev.close } : null;
        if (A.jump) {
          // a history day opens at the confirmation of the chosen session: the family's snapshot as it was fixed then
          A.jump = false;
          const s = sess(day(), st.session, 1020, false);
          if (st.rpWanted != null) { st.rp = st.rpWanted; st.rpWanted = null; } else st.rp = s.conf || null;
          fitSession(st.session);
          if (st.session === 'RDR') { st.v0 = 545; st.v1 = 1005; }
        }
      }
    } catch (e) { A.error = 'Локальный сервер не ответил'; }
    A.busy = false;
    render(true);
    schedule();
  }
  window.__d24 = { st, A, render, cur, hit: (x, y) => hit(x, y), get V() { return V; }, passports: () => P24.list.slice(), links: () => P24.links.slice(), openHist, openLive, filmOf, levelQuery, areaInfo, areaCount, zonesOf, zoneStatus };
  initPanel24();
  // the address: #date=2025-12-17 (a history day) &inst=NQ &session=RDR &at=11:50 (replay) &ev=X &mode=path
  //              &area=3:6[:b0:b1] (price cells [3, 6) x time cells [b0, b1)) &hist=1 (details open)
  {
    const q = new URLSearchParams(location.hash.slice(1));
    try { A.auto = localStorage.getItem('drlab.auto') !== '0'; } catch (x) { /* optional */ }
    if (['NQ', 'ES', 'YM'].includes(q.get('inst'))) A.inst = q.get('inst');
    if (SESS[q.get('session')]) { st.session = q.get('session'); st.userSession = true; }
    if (q.get('ev') === 'X') st.ev = 'X';
    if (q.get('mode') === 'path') st.mode = 'path';
    if (q.get('view') === 'conf') st.view = 'conf';
    if (q.get('det')) { st.detPin = true; }
    const at = q.get('at') ? (() => { const [hh, mm] = q.get('at').split(':').map(Number); return hh * 60 + mm - (hh >= 18 ? 1440 : 0); })() : null;
    if (q.get('area')) { const a = q.get('area').split(':').map(Number); st.area = a.length >= 4 ? { k0: a[0], k1: a[1], b0: a[2], b1: a[3] } : { k0: a[0], k1: a[1] }; }
    if (q.get('pt') != null && q.get('pt') !== '') st.pin = { k: 'pt', i: +q.get('pt') };      // &pt=5: the 6th session of the family pinned
    if (q.get('lvl')) st.pinLvl = q.get('lvl');                                               // &lvl=u2: a level pinned (drH, idrL, mid, u1 … d6)
    if (q.get('col') != null && q.get('col') !== '') st.col = +q.get('col');                   // &col=12: an M5 column of «Путь семьи» pinned
    if (q.get('scope') === 'all') st.scope = 'all';                                         // &scope=all: the all-weekdays family
    if (q.get('zone')) st.pinZone = +q.get('zone');                                         // &zone=2: the second zone of the chosen event pinned
    if (q.get('geo')) st.geo = true;                                                         // &geo=1: geometry for spec/ekran-24
    if (q.get('hov')) { const a = q.get('hov').split(':'); st.hover = a[0] === 'pcell' ? { k: 'pcell', ev: a[1], k0: +a[2], k1: +a[2] + 1, src: 'proj' } : a[0] === 'tcell' ? { k: 'tcell', b0: +a[1], b1: +a[1] + 1, src: 'strip' } : null; if (st.hover && st.hover.ev) st.ev = st.hover.ev; }   // review snapshots
    cfgPanel();
    if (/^\d{4}-\d\d-\d\d$/.test(q.get('date') || '')) { A.src = 'hist'; A.date = q.get('date'); A.jump = true; st.rpWanted = at; }
    else if (at != null) { st.rp = at; st.session = sessOf(at) || st.session; st.userSession = true; fitSession(st.session); }
    render(true); loadDay(false);
  }
})();
