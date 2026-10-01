// Built from design/sozvezdiya-24/src (app.js + panel.js) by its build.py: edit there.
// ================= DR Lab · design 24 «Границы хода» =================
// Design 22's working screen (candles of the day, the three sessions' DR / IDR, replay, the right panel, hover / pin,
// layers, settings) with its statistical layer replaced by the semantic specification DR-LAB-SEM-1.0
// (meaning/lens/2026-10-01-specifikaciya-v1.md). Every number of this screen belongs to one of these objects:
// - the family F, fixed at today's confirmation (after today's DR break: the break family F_break, the original kept
//   behind an explicit switch); one N per family, every share is of N, unknown mass kept apart;
// - «Границы хода» (main mode): R = the deepest point against the confirmation and X = the farthest point along it,
//   each session from its own confirmation to the end of its block, one point per session; the price histogram right
//   of the price scale and the time histogram at the bottom are the same event; one switch R / X changes all three;
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
    R: '#DE8580', X: '#63C3A5', path: '#9FB3D1',
    ptA: 80, ptSize: 100, pastA: 35, glowA: 25, projA: 90, stripA: 80, heatA: 200,
    dr: '#EEF1F5', drA: 92, drW: 1.6, idr: '#AEBACB', idrA: 85, idrW: 1.2, idrDash: 'dash',
    mid: '#8B95A5', midA: 80, midDash: 'dots', std: '#A7B2C3', stdA: 75, stdOffA: 40,
    boxFill: 'grad', boxA: 45, prevA: 46, viC: '#F29A38', vibA: 20, vibNQ: 2, vibES: 0.5, vibYM: 5, upC: '#089981', dnC: '#F23645', bg: '#08090C'
  };
  const BOXFILL = { grad: 'Градиент', solid: 'Сплошная', none: 'Без цвета' };
  const DASH = { solid: [], dash: [7, 4], dots: [1.5, 3.5], dashdot: [9, 3, 2, 3] };
  const CFG_KEY = 'drlab.d24.cfg';
  const cfg = Object.assign({}, DEF);
  try { Object.assign(cfg, JSON.parse(localStorage.getItem(CFG_KEY) || '{}')); } catch (e) { /* no storage: defaults */ }
  const saveCfg = () => { try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch (e) { /* not kept */ } };
  const SCHEMA = [
    ['События семьи', [['R', 'Откат R · цвет', 'color'], ['X', 'Расширение X · цвет', 'color'], ['ptA', 'Точки · яркость', 'range', 10, 100],
      ['ptSize', 'Точки · размер', 'range', 50, 200], ['pastA', 'Прошедшие по часам · яркость', 'range', 5, 100], ['glowA', 'Свечение точек', 'range', 0, 60]]],
    ['Гистограммы', [['projA', 'Цена справа · яркость', 'range', 10, 100], ['stripA', 'Время снизу · яркость', 'range', 10, 100]]],
    ['Путь семьи', [['path', 'Клетки · цвет', 'color'], ['heatA', 'Клетки · яркость (одна для всех колонок)', 'range', 20, 400, 10]]],
    ['Линии сессии', [['dr', 'DR · цвет', 'color'], ['drA', 'DR · яркость', 'range', 10, 100], ['drW', 'DR · толщина', 'range', 0.5, 3, 0.1],
      ['idr', 'IDR · цвет', 'color'], ['idrA', 'IDR · яркость', 'range', 10, 100], ['idrW', 'IDR · толщина', 'range', 0.5, 3, 0.1], ['idrDash', 'IDR · вид', 'dash'],
      ['mid', 'mid · цвет', 'color'], ['midA', 'mid · яркость', 'range', 10, 100], ['midDash', 'mid · вид', 'dash'],
      ['std', 'STD · цвет', 'color'], ['stdA', 'STD стороны в игре · яркость', 'range', 5, 100], ['stdOffA', 'STD другой стороны · яркость', 'range', 0, 100]]],
    ['Коробки сессий', [['boxFill', 'Заливка DR / IDR', 'boxfill'], ['boxA', 'Заливка · яркость', 'range', 0, 100]]],
    ['Прошлые сессии и VI', [['prevA', 'DR / IDR прошлых сессий · яркость', 'range', 5, 100], ['viC', 'VI · цвет', 'color'], ['vibA', 'VI · яркость', 'range', 5, 60], ['vibNQ', 'VI NQ · разрыв тел от, пунктов', 'range', 0, 6, 0.25], ['vibES', 'VI ES · разрыв тел от, пунктов', 'range', 0, 3, 0.25], ['vibYM', 'VI YM · разрыв тел от, пунктов', 'range', 0, 20, 1]]],
    ['График', [['upC', 'Свеча вверх', 'color'], ['dnC', 'Свеча вниз', 'color'], ['bg', 'Фон', 'color']]]
  ];
  const DASH_NAMES = { solid: 'сплошная', dash: 'штрих', dots: 'точки', dashdot: 'штрихпунктир' };
  const FONT = '-apple-system,BlinkMacSystemFont,"Trebuchet MS",Roboto,Ubuntu,sans-serif';
  const LAYERS = [
    ['pts', 'Точки: одна сессия — одно событие', '#DE8580'], ['glow', 'Свечение точек (рисунок, без чисел)', '#9FB3D1'],
    ['proj', 'Гистограмма цены справа', '#DE8580'], ['strip', 'Гистограмма времени снизу', '#63C3A5'], ['std', 'STD', C.stdOn],
    ['prev', 'DR и IDR прошлых сессий', C.dr], ['vib', 'VI (volume imbalance)', C.vib], ['det', 'Детали (снизу)', C.text2]
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
  const rgba = (hex, a) => { const c = rgb(hex); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
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
  const famKey = (D, s, view) => D.d + '|' + s.k + '|' + s.conf + '|' + s.side + '|' + view + '|' + (view === 'brk' ? s.failed : '');
  const sliceOf = ctx => ctx.live ? Math.floor(NOW / 5) * 5 : ctx.obs;      // the last closed M5 (AGENTS.md rule 6)
  function requestFamily(fk, s, view) {
    if (A.pending.has(fk)) return;
    A.pending.add(fk);
    const at = s.live ? Math.floor(NOW / 5) * 5 : s.obs;
    fetch('/api/d24/family?instrument=' + A.inst + '&session=' + s.k + '&at=' + at + (A.src === 'hist' ? '&date=' + A.date : '') + '&view=' + view)
      .then(r => r.json()).then(r => { A.fams.set(fk, r); if (A.fams.size > 40) A.fams.delete(A.fams.keys().next().value); })
      .catch(() => A.fams.set(fk, { status: 'error', message: 'Локальный сервер не ответил' }))
      .finally(() => { A.pending.delete(fk); redraw(true); });
  }
  function snapOf(D, s) {
    if (!s.conf || !['confirmed', 'broken', 'done'].includes(s.status) || D.d === 'none') return null;
    const view = wantView(s), fk = famKey(D, s, view), r = A.fams.get(fk);
    if (!r) { requestFamily(fk, s, view); return null; }
    if (r.status !== 'ok' || r.view !== view || !r.today || r.today.c0 !== s.conf || r.today.side !== s.side) return null;
    if (!r._F) r._F = buildSnap(r, s, view);
    return r._F;
  }
  function buildSnap(r, s, view) {
    const side = s.side, brk = view === 'brk', w0 = s.idrH - s.idrL, tick = (A.day && A.day.tick) || 0.25;
    const d0 = brk ? -side : side, e0 = brk ? (side === 1 ? s.idrL : s.idrH) : (side === 1 ? s.idrH : s.idrL);
    const F = {
      r, view, brk, N: r.N, f: r.schedule.formed, end: r.schedule.end, grid: r.grid, M: r.members, cond: r.cond,
      d0, e0, w0, tick, e0t: Math.round(e0 / tick), w0t: Math.round(w0 / tick), act0: brk ? s.failed : s.conf, side,
      names: brk ? { R: 'Против слома', X: 'По слому' } : { R: 'Откат', X: 'Расширение' },
      what: brk ? { R: 'самая глубокая точка против слома', X: 'самая дальняя точка по слому' } : { R: 'самая глубокая точка против подтверждения', X: 'самая дальняя точка по подтверждению' },
      from: brk ? 'от своего слома' : 'от своего подтверждения', nb: (r.schedule.end - r.schedule.formed) / 15
    };
    F.u2p = u => F.e0 + F.d0 * u * F.w0;
    F.p2u = p => F.d0 * (p - F.e0) / F.w0;
    F.cellOfP = p => Math.floor(10 * F.p2u(p) + 1e-9);
    F.ev = { R: evDist(F, 'R'), X: evDist(F, 'X') };
    if (!brk) { F.out = { held: 0, broken: 0, unknown: 0, none: 0 }; for (const m of F.M) F.out[m.outcome]++; }
    // the same definitions computed twice: the page's counts must equal the server's (checked by tests/ui_check24.js)
    F.mismatch = [];
    for (const ev of ['R', 'X']) {
      const a = r.counts[ev], b = F.ev[ev];
      const sa = a.cells.map(c => c.join(',')).sort().join(';'), sb = [...b.cells.values()].map(c => [c.k, c.b, c.list.length].join(',')).sort().join(';');
      if (sa !== sb || a.unknown !== b.unknown || a.none !== b.none) F.mismatch.push(ev);
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
    L: { pts: true, glow: false, proj: true, strip: true, std: true, prev: true, vib: true, det: true },
    ev: 'R', mode: 'bounds', view: 'auto', area: null, tool: false, col: null,
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
    const W = cv.clientWidth, H = cv.clientHeight, handleH = st.L.det ? 22 : 0, axisW = 88, timeH = 28;
    const projW = st.L.proj && ctx.F && ctx.F.N ? 96 : 0;
    const plot = { x: 0, y: 0, w: W - axisW - projW, h: H - handleH - timeH };
    const G = { W, H, handleH, axisW, timeH, plot, projW, ctx };
    G.proj = { x: plot.w + axisW, y: 0, w: projW, h: plot.h };
    G.X = t => plot.x + (t - st.v0) / (st.v1 - st.v0) * plot.w;
    G.T = x => st.v0 + (x - plot.x) / plot.w * (st.v1 - st.v0);
    let p0 = st.p0, p1 = st.p1;
    if (st.auto || p0 == null) { const r = autoRange(ctx); p0 = r[0]; p1 = r[1]; }
    G.p0 = p0; G.p1 = p1;
    G.Y = p => plot.y + (p1 - p) / (p1 - p0) * plot.h;
    G.P = y => p1 - (y - plot.y) / plot.h * (p1 - p0);
    G.bs = plot.w * 5 / (st.v1 - st.v0);
    const F = ctx.F;
    G.stripOn = st.L.strip && !!F && !!F.N && st.mode === 'bounds';
    const sx0 = F ? Math.max(plot.x, G.X(F.f)) : 0;
    G.strip = { x: sx0, y: plot.h - st.stripH, w: F ? Math.max(0, Math.min(plot.w, G.X(F.end + 15)) - sx0) : 0, h: st.stripH };
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
    if (ctx.F) for (const ev of ['R', 'X']) {
      const ps = ctx.F.ev[ev].pts.map(q => q.p).sort((a, b) => a - b);
      if (ps.length >= 3) { lo = Math.min(lo, ps[Math.floor(0.05 * (ps.length - 1))]); hi = Math.max(hi, ps[Math.ceil(0.95 * (ps.length - 1))]); }
    }
    if (!isFinite(lo)) { lo = 24400; hi = 24800; }
    const pad = (hi - lo) * 0.07;
    return [lo - pad, hi + pad + (hi - lo) * 0.03];
  }
  const bodyW = S => { if (S >= 2.5 && S <= 4) return 3; const c = 1 - 0.2 * Math.atan(Math.max(4, S) - 4) / (Math.PI * 0.5); let w = Math.max(1, Math.min(Math.floor(S * c), Math.floor(S))); if (w >= 2 && w % 2 === 0) w -= 1; return w; };

  // ---------- drawing ----------
  function render(full) {
    const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const ctx = cur();
    if (st.pinLvl && ctx.s.drH != null) { const l = levels(ctx.s).find(z => z.id === st.pinLvl); if (l) st.pin = { k: 'lvl', id: l.id, l }; st.pinLvl = null; }
    V = geom(ctx);
    V.win = null;
    const c = g2;
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    Object.assign(C, { dr: cfg.dr, idr: cfg.idr, mid: cfg.mid, std: cfg.std, stdOn: cfg.std, vib: cfg.viC, up: cfg.upC, dn: cfg.dnC, bg: cfg.bg });
    c.fillStyle = C.bg; c.fillRect(0, 0, W, H);
    c.save(); c.beginPath(); c.rect(V.plot.x, V.plot.y, V.plot.w, V.plot.h); c.clip();
    const F = ctx.F;
    drawBoxes(c, ctx);
    if (st.L.prev) drawPrev(c, ctx);
    if (st.L.vib) drawVib(c, ctx);
    if (F && st.mode === 'path') drawFilm(c, ctx);
    if (F) drawHighlight(c, ctx);
    drawLevels(c, ctx);
    drawReference(c, ctx);
    if (F && st.mode === 'bounds') { if (st.L.glow) drawGlow(c, ctx); drawMemberPath(c, ctx); }
    drawCandles(c, ctx);
    drawPills(c, ctx);
    drawNow(c, ctx);
    if (F && st.mode === 'bounds' && st.L.pts) drawPoints(c, ctx);
    if (F && st.mode === 'bounds') drawPair(c, ctx);
    if (F) drawArea(c, ctx);
    if (F && V.stripOn) drawStrip(c, ctx);
    drawTags(c, ctx);
    drawCross(c);
    c.restore();
    drawPriceAxis(c, ctx);
    if (F && V.projW) drawProj(c, ctx);
    drawTimeAxis(c, ctx);
    drawLegend(c, ctx);
    if (full) { toolbar(ctx); panelHtml(ctx); }
    else panelMarks();
    details(ctx);
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
      const s = P.s, x0 = Math.max(V.plot.x, V.X(P.k === 'PREV' ? st.v0 : SESS[P.k].start)), x1 = V.plot.w;
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
      c.fillStyle = rgba(C.vib, Math.min(1, on ? 0.34 * vf : v.fill != null ? 0.09 * vf : 0.2 * vf));
      c.fillRect(x0, y0 - 1, x1 - x0, Math.max(2, y1 - y0 + 2));
      c.fillStyle = rgba(C.vib, Math.min(1, on ? 0.9 : (v.fill != null ? 0.25 : 0.5) * vf));
      c.fillRect(x0, y0 - 1, 1.5, Math.max(2, y1 - y0 + 2));
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
    if (h.k === 'pcell') {
      const [ya, yb] = cellY(F, h.k0, h.k1);
      c.fillStyle = rgba(cfg[st.ev], 0.09); c.fillRect(0, ya, V.plot.w, Math.max(1, yb - ya));
      V.win = { t0: null, t1: null, pA: F.u2p(h.k0 / 10), pB: F.u2p(h.k1 / 10), col: cfg[st.ev] };
    }
    if (h.k === 'tcell') {
      const x0 = V.X(F.f + 15 * h.b0), x1 = V.X(F.f + 15 * h.b1);
      c.fillStyle = rgba(cfg[st.ev], 0.07); c.fillRect(x0, 0, x1 - x0, V.plot.h);
      V.win = { t0: F.f + 15 * h.b0, t1: F.f + 15 * h.b1, pA: null, pB: null, col: cfg[st.ev] };
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
        if (!st.L.std) continue;
        const inPlay = play === l.dir;
        line(l.p, C.std, on ? 1 : (inPlay ? cfg.stdA : cfg.stdOffA) / 100, 1, []);
      } else if (l.type === 'dr') line(l.p, C.dr, on ? 1 : cfg.drA / 100, +cfg.drW, []);
      else if (l.type === 'idr') line(l.p, C.idr, on ? 1 : cfg.idrA / 100, +cfg.idrW, DASH[cfg.idrDash] || []);
      else if (l.type === 'mid') line(l.p, C.mid, on ? 1 : cfg.midA / 100, 1.2, DASH[cfg.midDash] || []);
      else if (l.type === 'open') line(l.p, C.open, on ? 0.9 : 0.5, 1, [1, 6]);
    }
    // the IDR fractions inside the box (0,1 ... 0,9 of the IDR), as in the Pine indicator
    c.fillStyle = C.text3; c.font = '10px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'right';
    const w = s.idrH - s.idrL, xb = V.X(s.start) - 4;
    if (w * V.plot.h / (V.p1 - V.p0) > 90) for (let j = 1; j <= 9; j++) if (j !== 5) c.fillText(num(j / 10, 1), xb, V.Y(s.idrL + j * w / 10));
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
    c.strokeStyle = 'rgba(236,240,246,.55)'; c.lineWidth = 1.2; c.stroke();
    F.grid.forEach((T, j) => {
      const q = m.path[j];
      if (!q) return;
      const x = Math.round(V.X(T - 2.5)) + 0.5, ya = V.Y(F.u2p(q[0] / m.w)), yb = V.Y(F.u2p(q[1] / m.w));
      c.strokeStyle = T <= m.act ? 'rgba(236,240,246,.18)' : 'rgba(236,240,246,.42)'; c.lineWidth = 1;
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
      const col = b.c >= b.o ? C.up : C.dn, a = future ? 0.22 : 1;
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
      c.fillStyle = C.text3; c.font = '11px ' + FONT; c.textBaseline = 'top'; c.textAlign = 'right'; c.fillText('конец ' + ctx.s.k + ' ' + clk(E), xe - 5, 64); c.textAlign = 'left';
    }
    const x = Math.round(V.X(ctx.obs)) + 0.5;
    c.strokeStyle = ctx.live && !ctx.D.hist ? 'rgba(255,255,255,.14)' : rgba(ctx.D.hist ? C.hist : C.replay, 0.55); c.setLineDash([3, 4]); c.lineWidth = 1;
    c.beginPath(); c.moveTo(x, 0); c.lineTo(x, V.plot.h); c.stroke(); c.setLineDash([]);
  }
  // does a point take part in what is hovered / pinned / selected? true = lit, false = dimmed, null = neutral
  function emphOf(q, h, F, ctx) {
    if (h) {
      if (h.k === 'pcell') return q.k >= h.k0 && q.k < h.k1;
      if (h.k === 'tcell') return q.b >= h.b0 && q.b < h.b1;
      if (h.k === 'area') return inArea(q, st.area);
      if (h.k === 'pt') return q.i === h.i;
      if (h.k === 'out') return q.m.outcome === h.cat;
      if (h.k === 'evrow') return true;
      if (h.k === 'lvl' && h.l && ctx) { const L = levelRat(F, h.l.p), up = levelUp(F, ctx, L); return reachOne(F, q.m, L, up, q.m.act) === 'yes'; }
    }
    if (st.area) return inArea(q, st.area) ? true : null;
    return null;
  }
  const inArea = (q, a) => !!a && q.k >= a.k0 && q.k < a.k1 && (a.b0 == null || (q.b >= a.b0 && q.b < a.b1));
  // one point = one session's event (spec §7): no jitter; points on the same spot stay on it (their weight adds up in
  // brightness, the tooltip lists every session). A ring = that session broke its DR (the family is never thinned by it).
  function drawPoints(c, ctx) {
    const F = ctx.F, D = F.ev[st.ev], col = cfg[st.ev], sl = sliceOf(ctx), h = hv(), R0 = 2.4 * cfg.ptSize / 100;
    for (const q of D.pts) {
      const x = V.X(q.t + 2.5), y = V.Y(q.p);
      if (x < -4 || x > V.plot.w + 4 || y < -4 || y > V.plot.h + 4) continue;
      const past = q.t + 5 <= sl, e = emphOf(q, h, F, ctx);
      let a = (past ? cfg.pastA : cfg.ptA) / 100, r = R0;
      if (e === true) { a = Math.min(1, Math.max(a, 0.55) + 0.3); r *= 1.3; } else if (e === false) a *= 0.28;
      if (!F.brk && q.m.outcome === 'broken') { c.strokeStyle = rgba(col, a); c.lineWidth = 1.3; c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.stroke(); }
      else { c.fillStyle = rgba(col, a); c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.fill(); }
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
  // decoration only (spec §7.1): a soft halo per point, the same for every point, so it never makes a number or a contour
  function drawGlow(c, ctx) {
    const F = ctx.F, col = cfg[st.ev], a = cfg.glowA / 100, r0 = 16;
    c.save(); c.globalCompositeOperation = 'lighter';
    for (const q of F.ev[st.ev].pts) {
      const x = V.X(q.t + 2.5), y = V.Y(q.p);
      if (x < -r0 || x > V.plot.w + r0 || y < -r0 || y > V.plot.h + r0) continue;
      const g = c.createRadialGradient(x, y, 0, x, y, r0);
      g.addColorStop(0, rgba(col, 0.35 * a)); g.addColorStop(1, rgba(col, 0));
      c.fillStyle = g; c.fillRect(x - r0, y - r0, 2 * r0, 2 * r0);
    }
    c.restore();
  }
  // the selected area (spec §7.1): the bracket right of the block end spans the WHOLE price band and carries the band's
  // share of the event; a band x time window is a frame carrying its own joint share; a time window is a column
  function drawArea(c, ctx) {
    const F = ctx.F, a = st.area || (st.drag && st.drag.area);
    V.areaHit = null;
    if (!a) return;
    const col = st.mode === 'path' ? '#E6EAF0' : cfg[st.ev], live = st.drag && st.drag.area === a;
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
      const N = F.N, ev = st.ev;
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
  // the time histogram T_E(b) of the chosen event: 15-minute cells from the box end to the block end; passed cells
  // dimmer (they stay in the distribution); the unknown mass is a separate cell «?» after the block end
  function stripData(F) {
    const D = F.ev[st.ev], cols = [];
    for (let b = 0; b < F.nb; b++) cols.push({ b, t: F.f + 15 * b, t1: F.f + 15 * (b + 1), n: D.T.get(b) || 0 });
    return { cols, mx: Math.max(1, ...cols.map(q => q.n)), unk: D.unknown + D.none };
  }
  function drawStrip(c, ctx) {
    const F = ctx.F, S = V.strip;
    if (S.w < 20) return;
    const open = S.h > 60, h = hv(), { cols, mx, unk } = stripData(F), col = cfg[st.ev], sl = sliceOf(ctx), base = S.y + S.h - (open ? 16 : 3), hmax = S.h - (open ? 34 : 8);
    c.fillStyle = open ? 'rgba(10,11,15,.94)' : 'rgba(8,9,12,.72)'; c.fillRect(S.x, S.y, S.w, S.h);
    c.fillStyle = C.grid; c.fillRect(S.x, S.y, S.w, 1);
    V.stripCols = [];
    for (const q of cols) {
      const x0 = Math.max(S.x, V.X(q.t)) + 1, x1 = Math.min(S.x + S.w, V.X(q.t1)) - 1;
      if (x1 - x0 < 1) continue;
      V.stripCols.push({ q, x0, x1 });
      const past = q.t1 <= sl, on = h && ((h.k === 'tcell' && q.b >= h.b0 && q.b < h.b1) || (h.k === 'area' && st.area && st.area.b0 != null && q.b >= st.area.b0 && q.b < st.area.b1));
      const len = hmax * q.n / mx;
      c.fillStyle = rgba(col, Math.min(1, (on ? 0.95 : past ? 0.28 : 0.2 + 0.6 * Math.pow(q.n / mx, 0.8)) * cfg.stripA / 80));
      c.fillRect(x0, base - len, x1 - x0, len);
      if (open && q.n && x1 - x0 >= 18) {
        c.font = '600 10.5px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'bottom';
        c.fillStyle = rgba(col, past ? 0.6 : 0.95); c.fillText(pct(100 * q.n / F.N).replace('%', ''), (x0 + x1) / 2, base - len - 2);
        c.textAlign = 'left';
      }
    }
    if (open) {
      c.font = '10.5px ' + FONT; c.fillStyle = C.text3; c.textBaseline = 'top';
      c.fillText(F.names[st.ev] + ' ' + st.ev + ' · когда · % семьи', S.x + 4, S.y + 4);
    }
    // the unknown / no-period mass: a separate cell, never drawn at a time it did not have
    V.stripUnk = null;
    if (unk) {
      const x0 = Math.min(S.x + S.w + 4, V.plot.w - 26), w = 22, len = hmax * unk / mx;
      c.fillStyle = 'rgba(160,168,180,.45)'; c.fillRect(x0, base - len, w, len);
      c.font = '600 10.5px ' + FONT; c.fillStyle = C.text2; c.textBaseline = 'bottom'; c.textAlign = 'center'; c.fillText('?', x0 + w / 2, base - len - 2); c.textAlign = 'left';
      V.stripUnk = [x0, S.y, w, S.h];
    }
  }
  // names of the lines at their right end, just before the price scale, so nothing has to be scrolled to be read
  function drawTags(c, ctx) {
    const items = [], s = ctx.s, xr = V.plot.w - 6;
    if (s.drH != null) {
      const play = s.status === 'broken' ? s.nside : s.side || 0;
      for (const l of levels(s)) {
        if (l.type === 'std' && (!st.L.std || l.j > 4)) continue;
        if (l.type === 'dr' || l.type === 'idr') continue;   // today's DR / IDR are already named on the price scale (operator 2026-09-29)
        const col = l.type === 'mid' ? C.mid : l.type === 'open' ? C.open : play === l.dir ? C.stdOn : C.std;
        items.push({ y: V.Y(l.p), text: (l.type === 'std' ? '' : s.k + ' ') + l.name, col, pr: l.type === 'std' ? 1 : 2 });
      }
    }
    if (st.L.prev) for (const P of prevList(ctx)) {
      items.push({ y: V.Y(P.s.drH), text: P.name + ' DR', col: '#BFC6D2', pr: 2 }, { y: V.Y(P.s.drL), text: P.name + ' DR', col: '#BFC6D2', pr: 2 });
      items.push({ y: V.Y(P.s.idrH), text: P.name + ' IDR', col: '#8C95A3', pr: 1 }, { y: V.Y(P.s.idrL), text: P.name + ' IDR', col: '#8C95A3', pr: 1 });
    }
    if (st.L.vib) {
      const open = vibsKnown(ctx).filter(v => v.fill == null), pNow = s.priceNow != null ? s.priceNow : 0;
      const near = side => open.filter(v => side * ((v.lo + v.hi) / 2 - pNow) > 0).sort((a, b) => Math.abs((a.lo + a.hi) / 2 - pNow) - Math.abs((b.lo + b.hi) / 2 - pNow)).slice(0, 2);
      for (const v of near(1).concat(near(-1))) items.push({ y: V.Y((v.lo + v.hi) / 2), text: 'VI', col: C.vib, pr: 0 });
    }
    const vis = items.filter(q => q.y > 8 && q.y < V.plot.h - (V.stripOn ? V.strip.h : 0) - 6).sort((a, b) => a.y - b.y);
    const placed = [];
    for (const q of vis.slice().sort((a, b) => b.pr - a.pr)) {
      let y = q.y;
      for (let tries = 0; tries < 6 && placed.some(p => Math.abs(p.y - y) < 7); tries++) {
        const hit_ = placed.find(p => Math.abs(p.y - y) < 7);
        y = q.y >= hit_.y ? hit_.y + 7 : hit_.y - 7;
      }
      if (placed.some(p => Math.abs(p.y - y) < 6)) continue;
      placed.push({ y, q });
    }
    c.font = '5px ' + FONT; c.textBaseline = 'middle'; c.textAlign = 'right';
    for (const { y, q } of placed) {
      const w = c.measureText(q.text).width + 4;
      c.fillStyle = 'rgba(8,9,12,.8)'; c.fillRect(xr - w, y - 3.5, w + 2, 7);
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
    c.fillStyle = bg; roundRect(c, x, y - 9, w, 18, 3); c.fill();
    c.fillStyle = fg; c.font = '600 11px ' + FONT; c.textBaseline = 'middle'; c.fillText(text, x + 6, y + 0.5);
  }
  function drawPriceAxis(c, ctx) {
    const x = V.plot.w, H = V.plot.h;
    c.fillStyle = C.axis; c.fillRect(x, 0, V.axisW, H);
    c.fillStyle = C.grid; c.fillRect(x, 0, 1, H);
    const span = V.p1 - V.p0, step = niceStep(span, H, 46, [0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100, 250, 500]);
    c.font = '11px ' + FONT; c.fillStyle = C.text2; c.textBaseline = 'middle';
    for (let p = Math.ceil(V.p0 / step) * step; p <= V.p1; p += step) { const y = V.Y(p); if (y > 8 && y < H - 8) c.fillText(px(p), x + 8, y); }
    const s = ctx.s, tags = [];
    if (s.drH != null) {
      tags.push([V.Y(s.drH), 'DR ' + px(s.drH), '#E9ECF1', '#0B0C10'], [V.Y(s.drL), 'DR ' + px(s.drL), '#E9ECF1', '#0B0C10']);
      tags.push([V.Y(s.idrH), 'IDR ' + px(s.idrH), '#39414E', '#E6EAF0'], [V.Y(s.idrL), 'IDR ' + px(s.idrL), '#39414E', '#E6EAF0']);
    }
    const hh = hv(), wn = V.win;
    if (wn && wn.pA != null) { tags.push([V.Y(wn.pB), px(wn.pB), wn.col, '#0B0C10'], [V.Y(wn.pA), px(wn.pA), wn.col, '#0B0C10']); }
    if (hh && hh.k === 'lvl' && hh.l) tags.push([V.Y(hh.l.p), hh.l.name + ' ' + px(hh.l.p), '#C9D1DD', '#0B0C10']);
    if (hh && hh.k === 'prev') tags.push([V.Y(hh.p), px(hh.p), '#8C95A3', '#0B0C10']);
    const lastP = s.priceNow != null ? s.priceNow : null;
    if (lastP != null) { const b = ctx.D.bars.filter(q => q.t + 5 <= (ctx.live ? NOW + 5 : ctx.obs)).pop(); tags.push([V.Y(lastP), px(lastP), b && b.c >= b.o ? C.up : C.dn, '#fff']); }
    for (const [y, t, bg, fg] of tags) if (y > 0 && y < H) axisTag(c, y, t, bg, fg);
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
  function drawProj(c, ctx) {
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
    const y = V.plot.h, W = V.plot.w;
    c.fillStyle = C.axis; c.fillRect(0, y, V.W, V.timeH);
    c.fillStyle = C.grid; c.fillRect(0, y, V.W, 1);
    const step = niceStep(st.v1 - st.v0, W, 72, [5, 10, 15, 30, 60, 120, 180, 240, 360, 720]);
    const h = hv(), busy = [ctx.obs], wn = V.win;
    if (wn && wn.t0 != null) busy.push(wn.t0, wn.t1);
    if (st.mx >= 0 && st.mx < W && st.my < V.plot.h) busy.push(snapT(V.T(st.mx)) - 2.5);
    c.font = '11.5px ' + FONT; c.fillStyle = C.text2; c.textBaseline = 'middle'; c.textAlign = 'center';
    for (let t = Math.ceil(st.v0 / step) * step; t <= st.v1; t += step) { const x = V.X(t); if (x > 20 && x < W - 20 && !busy.some(b => Math.abs(V.X(b) - x) < 42)) c.fillText(t % 1440 === 0 ? ctx.D.dm : clk(t), x, y + V.timeH / 2); }
    const tag = (t, bg, fg, txt) => { const x = V.X(t), text = txt || clk(t); c.font = '600 11px ' + FONT; const w = c.measureText(text).width + 12; c.fillStyle = bg; roundRect(c, x - w / 2, y + 4, w, 20, 3); c.fill(); c.fillStyle = fg; c.fillText(text, x, y + 14.5); };
    if (wn && wn.t0 != null) { if (V.X(wn.t1) - V.X(wn.t0) < 96) tag((wn.t0 + wn.t1) / 2, wn.col, '#0B0C10', clk(wn.t0) + '–' + clk(wn.t1)); else { tag(wn.t0, wn.col, '#0B0C10'); tag(wn.t1, wn.col, '#0B0C10'); } }
    tag(ctx.obs, ctx.live && !ctx.D.hist ? '#2A2F38' : ctx.D.hist ? C.hist : C.replay, ctx.live && !ctx.D.hist ? '#fff' : '#0B0C10');
    if (st.mx >= 0 && st.mx < W && st.my < V.plot.h) tag(snapT(V.T(st.mx)) - 2.5, '#363A45', '#fff');
    c.textAlign = 'left';
    void h;
  }
  function barAt(ctx, t) { const tt = Math.floor(t / 5) * 5; return ctx.D.bars.find(b => b.t === tt) || null; }
  function drawLegend(c, ctx) {
    const s = ctx.s, used = ctx.live ? NOW + 5 : ctx.obs;
    let b = st.mx >= 0 && st.mx < V.plot.w && st.my < V.plot.h ? barAt(ctx, V.T(st.mx)) : null;
    if (!b) b = ctx.D.bars.filter(q => q.t + 5 <= used).pop();
    c.textBaseline = 'top';
    let x = 10;
    const put = (t, col, bold) => { c.font = (bold ? '600 ' : '') + '12.5px ' + FONT; c.fillStyle = col; c.fillText(t, x, 8); x += c.measureText(t).width + 6; };
    put(A.inst + '1! · 5 · ' + s.k, C.text, true);
    if (b) { const col = b.c >= b.o ? C.up : C.dn; put('O', C.text3); put(px(b.o), col); put('H', C.text3); put(px(b.h), col); put('L', C.text3); put(px(b.l), col); put('C', C.text3); put(px(b.c), col); put(sgn(b.c - b.o), col); put(clk(b.t), C.text3); }
    c.font = '12px ' + FONT; c.fillStyle = C.text2;
    let line = '';
    if (s.status === 'confirmed' || s.status === 'broken' || s.status === 'done') {
      if (s.conf) line = (s.side === 1 ? '↑ ' : '↓ ') + clk(s.conf) + ' · взято ' + (s.taken.filter(q => q.t).map(q => q.name + ' в ' + clk(q.t)).join(' · ') || 'ничего');
      if (s.failed) line = 'Слом DR ' + (s.side === 1 ? '↓ ' : '↑ ') + clk(s.failed) + ' · сторона анализа ' + (s.nside === 1 ? 'вверх' : 'вниз') + (s.takenN && s.takenN.some(q => q.t) ? ' · взято ' + s.takenN.filter(q => q.t).map(q => q.name + ' в ' + clk(q.t)).join(' · ') : '');
    } else if (s.status === 'waiting') line = 'подтверждения нет · ' + (ctx.obs - s.formed) + ' мин после коробки';
    else if (s.status === 'forming') line = 'коробка формируется';
    else if (s.status === 'noconf') line = 'сессия закончилась без подтверждения';
    if (line) c.fillText(line, 10, 28);
  }

  // ---------- hit test ----------
  function hit(x, y) {
    const ctx = V.ctx, F = ctx.F;
    if (F && V.projW && x >= V.proj.x && y < V.plot.h) {
      if (V.projUnk && y >= V.projUnk[1]) return { k: 'unk', src: 'proj' };
      const b = (V.projBars || []).find(q => y >= q.top - 1 && y <= q.bot + 1);
      if (st.mode === 'bounds') {
        if (b) return { k: 'pcell', k0: b.k, k1: b.k + 1, src: 'proj' };
        const k = F.cellOfP(V.P(y));
        return { k: 'pcell', k0: k, k1: k + 1, src: 'proj', empty: true };
      }
      const cd = colFor(ctx);
      if (cd) { const k = b ? b.k : F.cellOfP(V.P(y)); return { k: 'fcell', j: cd.j, kk: k, src: 'proj' }; }
      return { k: 'paxis' };
    }
    if (x > V.plot.w) return y < V.plot.h ? { k: 'paxis' } : null;
    if (y > V.plot.h) return { k: 'taxis' };
    if (!F) return lvlHit(ctx, y) || vibHit(ctx, x, y) || prevHit(ctx, y);
    if (V.stripOn && x >= V.strip.x && y >= V.strip.y) {
      if (V.stripUnk && x >= V.stripUnk[0] && x <= V.stripUnk[0] + V.stripUnk[2]) return { k: 'unk', src: 'strip' };
      const q = (V.stripCols || []).find(z => x >= z.x0 - 1 && x <= z.x1 + 1);
      if (q) return { k: 'tcell', b0: q.q.b, b1: q.q.b + 1, src: 'strip' };
      if (x <= V.strip.x + V.strip.w) return { k: 'stripBg' };
    }
    if (st.area && V.areaHit) for (const a of V.areaHit) if (a.part !== 'frame' && x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3]) return { k: 'area', part: a.part };
    if (st.mode === 'bounds' && st.L.pts) {
      let best = null, bd = 5;
      for (const q of F.ev[st.ev].pts) { const d = Math.hypot(V.X(q.t + 2.5) - x, V.Y(q.p) - y); if (d < bd) { bd = d; best = q; } }
      if (best) {
        const all = F.ev[st.ev].pts.filter(q => Math.hypot(V.X(q.t + 2.5) - V.X(best.t + 2.5), V.Y(q.p) - V.Y(best.p)) < 2.5);
        return { k: 'pt', i: best.i, q: best, same: all.map(q => q.i) };
      }
    }
    if (st.mode === 'path') {
      const t = V.T(x), j = F.grid.findIndex(T => t >= T - 5 && t < T);
      if (j >= 0) { const k = F.cellOfP(V.P(y)), cd = filmOf(F)[j]; if (cd.cells.has(k)) return { k: 'fcell', j, kk: k }; const lv = lvlHit(ctx, y); if (lv) return lv; return { k: 'col', j }; }
    }
    if (st.area && V.areaHit) for (const a of V.areaHit) if (a.part === 'frame' && x >= a.box[0] && x <= a.box[0] + a.box[2] && y >= a.box[1] && y <= a.box[1] + a.box[3]) { const lv = lvlHit(ctx, y); if (lv) return lv; return { k: 'area', part: 'window' }; }
    return lvlHit(ctx, y) || vibHit(ctx, x, y) || prevHit(ctx, y);
  }
  function lvlHit(ctx, y) {
    for (const l of levels(ctx.s)) { if (l.type === 'std' && !st.L.std) continue; if (Math.abs(V.Y(l.p) - y) <= 3.5) return { k: 'lvl', id: l.id, l }; }
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
      const m = F.M[h.i], ev = st.ev, e = m[ev], other = ev === 'R' ? 'X' : 'R', o = m[other];
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
      const n = areaCount(F, st.ev, { k0: h.k0, k1: h.k1 }), p = evPass(F, st.ev, 'price_cell', [h.k0, h.k1], null, n);
      return sentence(p) + '<br><span class="k">' + px(Math.min(F.u2p(h.k0 / 10), F.u2p(h.k1 / 10))) + '–' + px(Math.max(F.u2p(h.k0 / 10), F.u2p(h.k1 / 10))) + ' · ' + where(s, F.u2p((h.k0 + h.k1) / 20)) + '</span>' +
        (F.ev[st.ev].unknown ? '<br><span class="k">ещё неизвестно у ' + pct(100 * F.ev[st.ev].unknown / F.N) + ' семьи</span>' : '');
    }
    if (h.k === 'tcell' && F) {
      const n = F.ev[st.ev].T.get(h.b0) || 0, t0 = F.f + 15 * h.b0, p = evPass(F, st.ev, 'time_cell', null, [t0, t0 + 15], n);
      return sentence(p);
    }
    if (h.k === 'unk' && F) {
      const D = st.mode === 'bounds' ? F.ev[st.ev] : null, cd = st.mode === 'path' ? colFor(ctx) : null;
      if (D) return '<b>' + pct(100 * (D.unknown + D.none) / F.N) + '</b> семьи — ' + F.names[st.ev].toLowerCase() + ' ' + st.ev + ' не определено: ' + (D.unknown ? 'нет свечи M5 на горизонте (' + pct(100 * D.unknown / F.N) + ')' : '') + (D.none ? (D.unknown ? ', ' : '') + 'нет периода измерения (' + pct(100 * D.none / F.N) + ')' : '') + '<br><span class="k">не рисуется ни по какой цене и времени</span>';
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
  // the side is toward the level from today's close at the slice, and it is named
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
    const a = st.area, ev = st.ev, sl = sliceOf(ctx), out = { a };
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

  // ---------- toolbar and the day picker ----------
  function toolbar(ctx) {
    const F = ctx.F;
    dom('sess').innerHTML = ORDER.map(k => '<button data-s="' + k + '" class="' + (k === st.session ? 'on' : '') + '">' + k + '</button>').join('');
    dom('inst').innerHTML = ['NQ', 'ES', 'YM'].map(k => '<button data-i="' + k + '" class="' + (k === A.inst ? 'on' : '') + '">' + k + '</button>').join('');
    for (const b of dom('mode').querySelectorAll('button')) b.classList.toggle('on', b.dataset.m === st.mode);
    const nm = F ? F.names : ctx.s.failed ? { R: 'Против слома', X: 'По слому' } : { R: 'Откат', X: 'Расширение' };
    dom('ev').innerHTML = ['R', 'X'].map(e => '<button data-e="' + e + '" class="' + (e === st.ev ? 'on' : '') + (st.mode === 'path' ? ' off' : '') + '" title="' + (F ? esc(F.what[e]) : '') + '">' + nm[e] + ' <i style="color:' + cfg[e] + '">' + e + '</i></button>').join('');
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
    cmp.href = '/#inst=' + A.inst + '&session=' + st.session + (st.rp != null ? '&at=' + clk(st.rp) : '');
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

  // ---------- the right panel: design 22's place and manner (percentages only, every line a link to the chart) ----------
  // What it holds (spec §10.3): the family and its slice; the chosen event and its unknown mass; the DR outcome of the
  // family (one 100 %); the selected area; the pinned level; the pinned history session. In «Путь семьи»: the family's
  // closes on one M5. No list of «best» places, no targets, no session counts.
  function link(h, html, cls, p, title) {
    const i = P24.links.push(h) - 1;
    return '<div class="p21-link' + (cls ? ' ' + cls : '') + '" data-l21="' + i + '"' + (p ? ' data-pp="' + p.id + '"' : '') + (title ? ' title="' + esc(title) + '"' : '') + '>' + html + '</div>';
  }
  const prow = (text, val) => '<span class="t">' + text + '</span><b>' + val + '</b>';
  const plainTitle = p => (p.phrase + ' · ' + p.horizon + (p.unknown_count ? ' · неизвестно у ' + pct(100 * p.unknown_count / p.N) + ' семьи' : '')).replace(/<[^>]+>/g, '');
  function statusMsg(ctx) {
    const s = ctx.s, x = A.day;
    if (!x || x.status !== 'ok') return (x && x.message) || (A.src === 'hist' ? 'Загружаю день истории…' : 'Загружаю свечи…');
    if (s.status === 'before') return 'Сессия ещё не началась';
    if (s.status === 'forming') return 'Коробка формируется: семьи ещё нет';
    if (s.status === 'waiting') return 'Подтверждения нет: семьи ещё нет';
    if (s.status === 'noconf') return 'Сессия закончилась без подтверждения';
    const r = A.fams.get(famKey(ctx.D, s, wantView(s)));
    if (!r) return 'Собираю семью…';
    if (r.status === 'ok' && !r.N) return 'В семье нет сессий: процентов нет';
    return 'Семья не собрана' + (r.message ? ': ' + r.message : '');
  }
  // after today's DR break: the break family, or the original confirmation snapshot kept as it was (spec §9.3)
  const viewSwitch = s => '<div class="p24-seg"><button data-view="auto" class="' + (wantView(s) === 'brk' ? 'on' : '') + '">Семья слома · ' + clk(s.failed) + '</button><button data-view="conf" class="' + (wantView(s) === 'brk' ? '' : 'on') + '">Исходная · ' + clk(s.conf) + '</button></div>';
  function panelHtml(ctx) {
    const s = ctx.s, F = ctx.F;
    P24.links = [];
    if (!F || !F.N) {
      // no family at this moment: one click opens a history day on which this session had one (spec: the live moment
      // must never block the review)
      const noFam = !F && ['before', 'forming', 'waiting', 'noconf'].includes(s.status) && A.day && A.day.status === 'ok';
      panel.innerHTML = '<div class="p21-empty">' + esc(F && !F.N ? 'В семье нет сессий: процентов нет' : statusMsg(ctx)) + '</div>' +
        (F && !F.N ? '<div class="p21-note">' + esc(F.cond) + '</div>' : '') + (s.failed && s.conf ? viewSwitch(s) : '') +
        (noFam ? '<button class="p24-btn" data-hist="1">' + (A.src === 'live' ? 'Открыть ' + st.session + ' на истории' : 'Ближайший день с подтверждением ' + st.session) + '</button>' : '');
      return;
    }
    const out = [], sl = sliceOf(ctx), step = 100 / F.N, src = F.r.source || {};
    const ttl = 'Слепок зафиксирован при ' + (F.brk ? 'сломе DR ' : 'подтверждении ') + clk(F.act0) + ' и за день не меняется. Все проценты — доли всей семьи, шаг доли ' + pct(step) +
      '. История ' + (src.history || '2006–2025') + ', только дни раньше ' + F.r.key.cutoff + '. Слепок ' + F.r.snapshot_id + ' · семья ' + F.r.family_id + ' · ' + F.r.semantics + '.';
    out.push('<div class="p21-h"><span title="' + esc(ttl) + '">' + (F.brk ? 'Семья слома' : 'Семья') + ' · ' + esc(F.cond) + '</span><span>' + (sl >= F.end ? 'блок закончен' : 'после ' + clk(sl)) + '</span></div>');
    if (s.failed) out.push(viewSwitch(s));
    if (st.mode === 'bounds') {
      const D = F.ev[st.ev], known = pp(F, { event_id: st.ev, region_kind: 'known', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
        yes_count: D.known, unknown_count: D.unknown, no_event_count: D.none, display_scope: 'panel', phrase: F.names[st.ev].toLowerCase() + ' ' + st.ev + ' определено', horizon: F.from + ' до ' + clk(F.end) });
      out.push(link({ k: 'evrow' }, '<span class="t"><span><i style="color:' + cfg[st.ev] + '">●</i> ' + F.names[st.ev] + ' ' + st.ev + '</span><span class="p21-sub">' + esc(F.what[st.ev]) + ' · ' + F.from + ' до ' + clk(F.end) + '</span></span>', 'ev', known,
        'одна сессия — одна точка; определено у ' + pct(known.pct) + ' семьи'));
      if (D.unknown + D.none) {
        const u = pp(F, { event_id: st.ev, region_kind: 'unknown', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end), yes_count: D.unknown + D.none, display_scope: 'panel',
          phrase: F.names[st.ev].toLowerCase() + ' ' + st.ev + ' не определено (нет свечи M5 на горизонте' + (D.none ? ' или нет периода' : '') + '); на графике не рисуется', horizon: F.from + ' до ' + clk(F.end) });
        out.push(link({ k: 'evrow' }, prow('не определено · нет свечи M5', pct(u.pct)), 'dim', u, plainTitle(u)));
      }
      const tf = todayFacts(F, ctx);
      if (tf) out.push('<div class="p21-note" title="Наблюдённые закрытые свечи сегодняшнего дня после ' + (F.brk ? 'слома' : 'подтверждения') + ' до среза; не окончательные значения">' + tf + '</div>');
    }
    if (F.out) out.push(outcomeHtml(F));
    if (st.mode === 'path') out.push(columnHtml(F, ctx));
    if (st.area && st.mode === 'bounds') out.push(areaHtml(F, ctx));
    const h = st.pin;
    if (h && h.k === 'lvl' && h.l) out.push(levelHtml(F, ctx, h.l));
    if (h && h.k === 'pt' && F.M[h.i]) out.push(memberHtml(F, F.M[h.i]));
    panel.innerHTML = out.join('');
    panelMarks();
  }
  // today's own path after the activation (facts, not shares): the deepest and the farthest closed-M5 point so far
  function todayFacts(F, ctx) {
    const rows = todayRows(F, ctx);
    if (!rows.length) return '';
    let lo = rows[0], hi = rows[0];
    for (const q of rows) { if (q.lo < lo.lo) lo = q; if (q.hi > hi.hi) hi = q; }
    return 'сегодня пока: ' + (F.brk ? 'против слома ' : 'глубже всего ') + sd(lo.lo / F.w0t) + ' SD в ' + clk(lo.T - 5) + ' · ' + (F.brk ? 'по слому ' : 'дальше всего ') + sd(hi.hi / F.w0t) + ' SD в ' + clk(hi.T - 5);
  }
  // the DR outcome of the family (spec §5.2): four categories that add up to 100 % of N; one compact bar
  function outcomeHtml(F) {
    const cats = [['held', 'удержался', '#6FB59A', 'ни одно закрытие M5 не ушло за свой противоположный DR до ' + clk(F.end)], ['broken', 'сломан', '#E5877F', 'закрытие M5 за своим противоположным DR (тень не считается; возврат не отменяет)'],
      ['unknown', 'неизвестно', '#8C95A3', 'нет свечи M5 на горизонте и слома до неё не видно'], ['none', 'нет периода', '#5F6877', 'после подтверждения до конца блока не было ни одной M5']];
    const P = {};
    for (const [k, nm, , what] of cats) P[k] = pp(F, { event_id: 'dr_' + k, region_kind: 'outcome', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: F.out[k], display_scope: 'panel', phrase: 'DR ' + nm + ' (' + what + ')', horizon: F.from + ' до ' + clk(F.end) });
    const bar = '<div class="p24-bar">' + cats.filter(([k]) => F.out[k]).map(([k, , col]) => '<i style="width:' + (100 * F.out[k] / F.N).toFixed(2) + '%;background:' + col + '"></i>').join('') + '</div>';
    const rows = cats.filter(([k]) => F.out[k] || k === 'held' || k === 'broken').map(([k, nm, col]) => link({ k: 'out', cat: k }, '<span class="t"><i style="color:' + col + '">■</i> ' + nm + '</span><b>' + pct(P[k].pct) + '</b>', 'in', P[k], plainTitle(P[k]))).join('');
    return '<div class="p21-h second">DR до ' + clk(F.end) + '<span>доля всей семьи</span></div>' + bar + '<div class="p24-out">' + rows + '</div>';
  }
  function areaHtml(F, ctx) {
    const I = areaInfo(F, ctx), out = ['<div class="p21-h second">Выбранная область <span><button class="p24-x" data-clear="area" title="Снять выбор (Esc)">✕</button></span></div>'];
    out.push('<div class="p21-note"><b style="color:#D1D4DC;font-weight:600">' + esc(I.name) + '</b>' + (I.prices ? ' · ' + px(I.prices[0]) + ' – ' + px(I.prices[1]) + ' · ' + esc(where(ctx.s, (I.prices[0] + I.prices[1]) / 2)) : '') + '</div>');
    if (I.band) out.push(link({ k: 'area', part: 'band' }, prow('<i style="color:' + cfg[st.ev] + '">' + st.ev + '</i> в полосе за всю сессию', ppTxt(I.band)), '', I.band, plainTitle(I.band)));
    if (I.win) out.push(link({ k: 'area', part: 'window' }, prow('<i style="color:' + cfg[st.ev] + '">' + st.ev + '</i> в выбранном окне', ppTxt(I.win)), '', I.win, plainTitle(I.win)));
    if (I.vfull) {
      out.push(link({ k: 'area', part: 'visit' }, prow('заходили в полосу · вся сессия', ppTxt(I.vfull, true)), 'dim', I.vfull, plainTitle(I.vfull)));
      out.push(link({ k: 'area', part: 'visit' }, prow('заходили в полосу · ' + (ctx && sliceOf(ctx) >= F.end ? 'остатка нет' : 'после ' + clk(sliceOf(ctx))), ppTxt(I.vrest, true)), 'dim', I.vrest, plainTitle(I.vrest)));
    }
    if (I.today) out.push('<div class="p21-note">' + esc(I.today) + '</div>');
    return out.join('');
  }
  function levelHtml(F, ctx, l) {
    const q = levelQuery(F, ctx, l.p, l.type === 'std' ? l.name : l.full), sl = sliceOf(ctx);
    return '<div class="p21-h second">Уровень <span>' + esc(l.type === 'std' ? l.name : l.full) + ' · ' + px(l.p) + ' <button class="p24-x" data-clear="pin" title="Снять (Esc)">✕</button></span></div>' +
      link({ k: 'lvl', id: l.id, l }, prow('дальше ' + dirName(F, q.up) + ' · вся сессия', ppTxt(q.full, true)), '', q.full, plainTitle(q.full)) +
      link({ k: 'lvl', id: l.id, l }, prow('дальше ' + dirName(F, q.up) + ' · ' + (sl >= F.end ? 'остатка нет' : 'после ' + clk(sl)), ppTxt(q.rest, true)), '', q.rest, plainTitle(q.rest)) +
      '<div class="p21-note">' + esc(q.today) + '</div>';
  }
  function memberHtml(F, m) {
    const ev = e => m[e].s === 'known' ? sd(m[e].v / m.w) + ' SD · ' + px(F.u2p(m[e].v / m.w)) + ' · ' + clk(m[e].t) : 'неизвестно';
    return '<div class="p21-h second">Сессия семьи <span>' + esc(memberLine(F, m)) + ' <button class="p24-x" data-clear="pin" title="Снять (Esc)">✕</button></span></div>' +
      '<div class="p24-mem"><div><i style="color:' + cfg.R + '">R</i> ' + F.names.R.toLowerCase() + ': ' + ev('R') + '</div><div><i style="color:' + cfg.X + '">X</i> ' + F.names.X.toLowerCase() + ': ' + ev('X') + '</div>' +
      '<div class="p21-sub">' + esc(orderText(F, m)) + '</div>' +
      (F.brk ? '' : '<div class="p21-sub">' + (m.outcome === 'broken' ? 'DR сломан ' + (m.brkKnown ? clk(m.brk) : '') : m.outcome === 'held' ? 'DR удержался до ' + clk(F.end) : 'исход DR неизвестен') + '</div>') +
      '<div class="p21-sub">' + (F.brk ? 'слом ' : 'подтверждение ') + clk(m.act) + '</div></div>';
  }
  // «Путь семьи» (spec §5.3, §10.2): the closes of the family on ONE M5, a column of its own 100 % (the missing M5 in it).
  // The distribution itself stands right of the price scale, aligned with the prices; the panel names the M5, the cell
  // under the cursor, the missing mass and what today's candle did on the same M5 (no second copy of the column).
  function columnHtml(F, ctx) {
    const cd = colFor(ctx), out = [], h = hv();
    const pinned = st.col === cd.j, hovered = h && (h.k === 'col' || h.k === 'fcell');
    out.push('<div class="p21-h second">Путь семьи · M5 ' + clk(cd.T - 5) + '–' + clk(cd.T) + '<span>' + (hovered ? 'под курсором' : pinned ? 'выбрана' : cd.T === sliceOf(ctx) ? 'на срезе' : '') + '</span></div>');
    if (h && h.k === 'fcell' && h.j === cd.j) {
      const list = cd.cells.get(h.kk) || [];
      const p = pp(F, { event_id: 'close_M5', region_kind: 'M5_cell', exact_price_bounds: [h.kk, h.kk + 1], time_bounds: [cd.T - 5, cd.T], start_rule: 'M5 ' + clk(cd.T - 5), end_rule: clk(cd.T),
        yes_count: list.length, unknown_count: cd.unknown, display_scope: 'panel', phrase: 'закрытие M5 в полосе ' + band(h.kk, h.kk + 1) + ' SD', horizon: 'на пятиминутке ' + clk(cd.T - 5) + '–' + clk(cd.T) });
      out.push(link({ k: 'fcell', j: cd.j, kk: h.kk }, prow('закрылись в ' + band(h.kk, h.kk + 1) + ' SD <span class="p21-sub">' + px(Math.min(F.u2p(h.kk / 10), F.u2p((h.kk + 1) / 10))) + '</span>', pct(p.pct)), '', p, plainTitle(p)));
    }
    if (cd.unknown) {
      const p = pp(F, { event_id: 'close_M5', region_kind: 'M5_unknown', exact_price_bounds: null, time_bounds: [cd.T - 5, cd.T], start_rule: 'M5 ' + clk(cd.T - 5), end_rule: clk(cd.T), yes_count: cd.unknown, display_scope: 'panel', phrase: 'нет свечи на этой M5 (неизвестно / рынок закрыт)', horizon: 'на пятиминутке ' + clk(cd.T - 5) + '–' + clk(cd.T) });
      out.push('<div class="p21-link fc dim" data-pp="' + p.id + '" title="' + esc(plainTitle(p)) + '"><span class="t">нет свечи · неизвестно</span><b>' + pct(p.pct) + '</b></div>');
    }
    if (cd.pre) out.push('<div class="p21-note">из них ещё до своего ' + (F.brk ? 'слома' : 'подтверждения') + ': ' + pct(100 * cd.pre / F.N) + '</div>');
    const tb = ctx.D.bars.find(b => b.t + 5 === cd.T);
    if (tb && cd.T <= sliceOf(ctx)) out.push('<div class="p21-note">сегодня на этой M5: закрытие ' + sd(F.d0 * (tk(tb.c) - F.e0t) / F.w0t) + ' SD · ' + px(tb.c) + '</div>');
    return out.join('');
  }
  function panelMarks() {
    const h = hv();
    for (const el of panel.querySelectorAll('[data-l21]')) {
      const L = P24.links[+el.dataset.l21];
      const on = !!(h && L && pinKey(L) === pinKey(h)) || !!(h && L && h.k === 'fcell' && L.k === 'fcell' && L.kk === h.kk && L.j === h.j);
      el.classList.toggle('on', on);
      el.classList.toggle('pinned', !!(st.pin && L && pinKey(L) === pinKey(st.pin)));
    }
  }

  // ---------- the details area (bottom): the whole passport of what is chosen, and one small chart for it ----------
  // Spec §10.4: one area that opens, not a row of charts. A history session: its whole path; a level or a band: how the
  // share of «на уровне или дальше» / «заходили» changes when the remaining hours start later (the snapshot does not).
  function detailObj(ctx) {
    const h = hv();
    if (h && ['pt', 'lvl', 'pcell', 'tcell', 'fcell', 'col', 'area', 'out', 'evrow'].includes(h.k)) return h;
    if (st.area) return { k: 'area', part: 'band' };
    return null;
  }
  const dRow = (k, v) => '<div class="p24-dr"><span>' + k + '</span><b>' + v + '</b></div>';
  function passportRows(p) {
    const b = p.exact_price_bounds;
    return dRow('событие', esc(p.phrase)) + dRow('горизонт', esc(p.horizon)) +
      (b && b.length === 2 && typeof b[0] === 'number' ? dRow('цена', band(b[0], b[1]) + ' SD <span class="k">[' + b[0] + '/10; ' + b[1] + '/10)</span>') : b && b.length === 1 ? dRow('уровень', sd(p.level_sd) + ' SD <span class="k">точно u = ' + b[0] + ' ширины IDR от края</span>') : '') +
      (p.time_bounds ? dRow('время', clk(p.time_bounds[0]) + '–' + clk(p.time_bounds[1])) : '') +
      dRow('доля', ppTxt(p, p.binary) + (p.pct != null ? ' <span class="k">(' + pct2(p.pct) + ')</span>' : '')) +
      (p.unknown_count ? dRow('неизвестно', pct(100 * p.unknown_count / p.N) + (p.binary ? '' : ' <span class="k">граница: до ' + pct(100 * (p.yes_count + p.unknown_count) / p.N) + '</span>')) : '') +
      dRow('знаменатель', 'вся семья, шаг доли ' + pct(100 / p.N));
  }
  function details(ctx) {
    const on = st.L.det;
    det.style.display = on ? '' : 'none';
    if (!on) return;
    const open = st.detPin || st.detOver, F = ctx.F, o = F ? detailObj(ctx) : null;
    det.classList.toggle('open', open);
    let head = 'Детали', body = '', chart = null;
    if (!F) head += ' · ' + statusMsg(ctx);
    else if (!o) {
      head += ' · слепок семьи';
      const r = F.r, src = r.source || {};
      body = dRow('семья', esc(F.cond)) + dRow('ключ', esc(r.key.instrument + ' × ' + r.key.session + ' × ' + WD[r.key.weekday] + ' × ' + (r.key.direction === 'long' ? 'лонг' : 'шорт') + ' × ' + (r.key.event === 'confirmation' ? 'окно подтверждения ' : 'окно слома ') + clk(r.key.window[0]) + '–' + clk(r.key.window[1]))) +
        dRow('история', esc((src.history || '') + ', только дни раньше ' + r.key.cutoff)) + dRow('шкала', esc('u = d·(цена − край)/ширина IDR; край: ' + r.scale.edge + '; ячейки 0,1 SD × 15 мин от ' + clk(r.scale.f))) +
        dRow('начало', esc(r.rules.start)) + dRow('конец', esc(r.rules.end)) + dRow('время события', esc(r.rules.time)) + dRow('атом', esc(r.rules.atom)) +
        dRow('слепок', esc(r.snapshot_id + ' · семья ' + r.family_id + ' · ' + r.semantics)) + dRow('шаг доли', pct(100 / F.N));
    } else if (o.k === 'pt') {
      const m = F.M[o.i];
      head += ' · сессия ' + memberLine(F, m);
      body = dRow(F.names.R.toLowerCase() + ' R', m.R.s === 'known' ? sd(m.R.v / m.w) + ' SD · ' + clk(m.R.t) + (m.R.ties.length > 1 ? ' · та же цена ещё ' + m.R.ties.slice(1).map(clk).join(', ') : '') : 'неизвестно') +
        dRow(F.names.X.toLowerCase() + ' X', m.X.s === 'known' ? sd(m.X.v / m.w) + ' SD · ' + clk(m.X.t) + (m.X.ties.length > 1 ? ' · та же цена ещё ' + m.X.ties.slice(1).map(clk).join(', ') : '') : 'неизвестно') +
        dRow('порядок', esc(orderText(F, m))) + (F.brk ? '' : dRow('DR', m.outcome === 'broken' ? 'сломан ' + (m.brkKnown ? clk(m.brk) : '') : m.outcome === 'held' ? 'удержался до ' + clk(F.end) : 'неизвестно')) +
        dRow(F.brk ? 'слом' : 'подтверждение', clk(m.act)) + (m.missing ? dRow('нет свечей', m.missing + ' M5 на горизонте') : '');
      chart = { kind: 'member', m };
    } else if (o.k === 'lvl' && o.l) {
      const q = levelQuery(F, ctx, o.l.p, o.l.type === 'std' ? o.l.name : o.l.full);
      head += ' · уровень ' + (o.l.type === 'std' ? o.l.name : o.l.full);
      body = passportRows(q.full) + dRow('после среза', ppTxt(q.rest, true) + ' <span class="k">' + esc(q.rest.horizon) + '</span>') +
        dRow('пересекали свечой', ppTxt(q.cross, true) + ' <span class="k">другое событие: минимум ≤ уровня ≤ максимум одной M5</span>') + dRow('сегодня', esc(q.today.replace(/^сегодня: /, '')));
      chart = { kind: 'reach', L: q.L, up: q.up, name: o.l.type === 'std' ? o.l.name : o.l.full };
    } else if (o.k === 'area' && st.area) {
      const I = areaInfo(F, ctx);
      head += ' · область ' + I.name;
      body = (I.band ? passportRows(I.band) : '') + (I.win ? dRow('в окне', ppTxt(I.win) + ' <span class="k">' + esc(I.win.phrase) + '</span>') : '') +
        (I.vfull ? dRow('заходили', ppTxt(I.vfull, true) + ' вся сессия · ' + ppTxt(I.vrest, true) + ' ' + esc(I.vrest.horizon)) : '') + (I.today ? dRow('сегодня', esc(I.today.replace(/^сегодня: /, ''))) : '');
      if (I.band) chart = { kind: 'visit', a: st.area };
    } else if (o.k === 'pcell' && st.mode === 'bounds') {
      head += ' · полоса ' + band(o.k0, o.k1) + ' SD';
      body = passportRows(evPass(F, st.ev, 'price_cell', [o.k0, o.k1], null, areaCount(F, st.ev, { k0: o.k0, k1: o.k1 })));
      chart = { kind: 'visit', a: { k0: o.k0, k1: o.k1 } };
    } else if (o.k === 'tcell') {
      const t0 = F.f + 15 * o.b0;
      head += ' · ' + clk(t0) + '–' + clk(t0 + 15);
      body = passportRows(evPass(F, st.ev, 'time_cell', null, [t0, t0 + 15], F.ev[st.ev].T.get(o.b0) || 0));
    } else if (o.k === 'fcell' || o.k === 'col') {
      const cd = filmOf(F)[o.j];
      head += ' · M5 ' + clk(cd.T - 5) + '–' + clk(cd.T);
      if (o.k === 'fcell') {
        const list = cd.cells.get(o.kk) || [];
        const rf = rangeField(F, o.j, o.kk);
        body = passportRows(pp(F, { event_id: 'close_M5', region_kind: 'M5_cell', exact_price_bounds: [o.kk, o.kk + 1], time_bounds: [cd.T - 5, cd.T], start_rule: 'M5 ' + clk(cd.T - 5), end_rule: clk(cd.T),
          yes_count: list.length, unknown_count: cd.unknown, display_scope: 'details', phrase: 'закрытие M5 в полосе ' + band(o.kk, o.kk + 1) + ' SD', horizon: 'на пятиминутке ' + clk(cd.T - 5) + '–' + clk(cd.T) })) +
          dRow('задевали диапазоном', pct(100 * rf.n / F.N) + ' <span class="k">поле диапазонов V: свеча M5 задевала полосу; не закрытие, колонка не нормирована</span>');
      } else body = dRow('колонка', 'закрытия семьи на этой M5; своя сотня процентов') + dRow('нет свечи', pct(100 * cd.unknown / F.N));
    } else if (o.k === 'out') {
      head += ' · исход DR';
      const nm = { held: 'удержался', broken: 'сломан', unknown: 'неизвестно', none: 'нет периода' }[o.cat];
      body = dRow('категория', nm) + dRow('доля', pct(100 * F.out[o.cat] / F.N)) + dRow('правило', 'закрытие M5 строго за своим противоположным DR; тень и равенство не ломают; слом не отменяется возвратом') + dRow('горизонт', F.from + ' до ' + clk(F.end));
    } else if (o.k === 'evrow') {
      const D = F.ev[st.ev];
      head += ' · ' + F.names[st.ev] + ' ' + st.ev;
      body = dRow('событие', esc(F.what[st.ev])) + dRow('определено', pct(100 * D.known / F.N)) + dRow('неизвестно', pct(100 * D.unknown / F.N) + ' <span class="k">нет свечи M5 на горизонте</span>') + (D.none ? dRow('нет периода', pct(100 * D.none / F.N)) : '') + dRow('горизонт', F.from + ' до ' + clk(F.end));
    }
    dom('deth').innerHTML = '<span>' + (open ? '▾ ' : '▴ ') + esc(head) + '</span>' + (st.detPin ? '<span class="k">закреплено</span>' : '');
    if (!open) { dom('dett').innerHTML = ''; return; }
    dom('dett').innerHTML = body;
    drawDetChart(chart, F, ctx);
  }
  function drawDetChart(ch, F, ctx) {
    const cvd = dom('detc'), r = cvd.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    cvd.style.display = ch ? '' : 'none';
    if (!ch) return;
    if (cvd.width !== Math.round(r.width * dpr) || cvd.height !== Math.round(r.height * dpr)) { cvd.width = Math.round(r.width * dpr); cvd.height = Math.round(r.height * dpr); }
    const c = cvd.getContext('2d'), W = r.width, H = r.height, L = 34, T = 16, B = 18, R = 10;
    c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, W, H);
    const X = t => L + (t - F.f) / (F.end - F.f) * (W - L - R), sl = sliceOf(ctx);
    c.font = '10.5px ' + FONT; c.fillStyle = C.text3; c.textBaseline = 'top';
    c.fillText(clk(F.f), L, H - B + 4); c.textAlign = 'right'; c.fillText(clk(F.end), W - R, H - B + 4); c.textAlign = 'left';
    if (ch.kind === 'member') {
      const m = ch.m, vals = [];
      m.path.forEach(q => { if (q) vals.push(q[0] / m.w, q[1] / m.w); });
      vals.push(0, -1);
      const lo = Math.min(...vals) - 0.1, hi = Math.max(...vals) + 0.1, Y = u => T + (hi - u) / (hi - lo) * (H - T - B);
      const hl = (u, col, dash, txt) => { c.strokeStyle = col; c.setLineDash(dash); c.beginPath(); c.moveTo(L, Y(u)); c.lineTo(W - R, Y(u)); c.stroke(); c.setLineDash([]); c.fillStyle = col; c.textBaseline = 'middle'; c.fillText(txt, 2, Y(u)); };
      hl(0, 'rgba(174,186,203,.6)', [5, 3], '0'); hl(-1, 'rgba(174,186,203,.6)', [5, 3], '−1');
      if (m.oppv != null) hl(m.oppv / m.w, 'rgba(238,241,245,.5)', [], 'DR');
      F.grid.forEach((Tm, j) => {
        const q = m.path[j]; if (!q) return;
        const x = X(Tm - 2.5), up = q[2] >= (m.path[j - 1] ? m.path[j - 1][2] : q[2]);
        c.strokeStyle = Tm <= m.act ? 'rgba(160,168,180,.35)' : up ? rgba(C.up, 0.8) : rgba(C.dn, 0.8);
        c.beginPath(); c.moveTo(x, Y(q[1] / m.w)); c.lineTo(x, Y(q[0] / m.w)); c.stroke();
      });
      const xa = X(m.act); c.strokeStyle = 'rgba(236,240,246,.4)'; c.setLineDash([3, 3]); c.beginPath(); c.moveTo(xa, T); c.lineTo(xa, H - B); c.stroke(); c.setLineDash([]);
      for (const e of ['R', 'X']) if (m[e].s === 'known') { const x = X(m[e].t + 2.5), y = Y(m[e].v / m.w); c.strokeStyle = cfg[e]; c.lineWidth = 1.5; c.beginPath(); c.arc(x, y, 4, 0, 6.2832); c.stroke(); c.lineWidth = 1; c.fillStyle = cfg[e]; c.textBaseline = 'middle'; c.fillText(e, x + 6, y); }
      c.fillStyle = C.text3; c.textBaseline = 'top'; c.fillText('путь сессии в ширинах своего IDR · ' + (F.brk ? 'слом ' : 'подтверждение ') + clk(m.act), L, 1);
      return;
    }
    // reach / visit share as the remaining hours start later: each point = its own question «после t до конца блока»
    const pts = [];
    for (let t = F.f; t <= F.end; t += 5) {
      const cnt = ch.kind === 'reach' ? reachCount(F, ch.L, ch.up, t) : visitCount(F, ch.a.k0, ch.a.k1, t);
      pts.push([t, 100 * cnt.yes / F.N, 100 * (cnt.yes + cnt.unknown) / F.N]);
    }
    const full = ch.kind === 'reach' ? reachCount(F, ch.L, ch.up, null) : visitCount(F, ch.a.k0, ch.a.k1, null);
    const Y = v => T + (100 - v) / 100 * (H - T - B);
    c.strokeStyle = C.grid; for (const v of [0, 50, 100]) { c.beginPath(); c.moveTo(L, Y(v)); c.lineTo(W - R, Y(v)); c.stroke(); c.fillStyle = C.text3; c.textBaseline = 'middle'; c.fillText(v + '%', 2, Y(v)); }
    c.strokeStyle = 'rgba(236,240,246,.35)'; c.setLineDash([4, 4]); c.beginPath(); c.moveTo(L, Y(100 * full.yes / F.N)); c.lineTo(W - R, Y(100 * full.yes / F.N)); c.stroke(); c.setLineDash([]);
    c.strokeStyle = st.mode === 'path' ? cfg.path : cfg[st.ev]; c.lineWidth = 1.6; c.beginPath();
    pts.forEach(([t, v], i) => { const x = X(t), y = Y(v); if (i) c.lineTo(x, y); else c.moveTo(x, y); }); c.stroke(); c.lineWidth = 1;
    if (sl >= F.f && sl <= F.end) { const x = X(sl); c.strokeStyle = rgba(ctx.D.hist ? C.hist : C.replay, 0.8); c.setLineDash([3, 3]); c.beginPath(); c.moveTo(x, T); c.lineTo(x, H - B); c.stroke(); c.setLineDash([]); }
    c.fillStyle = C.text3; c.textBaseline = 'top';
    c.fillText((ch.kind === 'reach' ? 'на ' + ch.name + ' или дальше ' + dirName(F, ch.up) : 'заходили в полосу ' + band(ch.a.k0, ch.a.k1) + ' SD') + ' · после t до ' + clk(F.end) + ' · пунктир — вся сессия от своего ' + (F.brk ? 'слома' : 'подтверждения'), L, 1);
  }
  function initPanel24() {
    panel.addEventListener('mouseover', e => { const el = e.target.closest('[data-l21]'); if (!el) return; st.hover = P24.links[+el.dataset.l21]; animStrip(); redraw(); });
    panel.addEventListener('mouseout', e => { const el = e.target.closest('[data-l21]'); if (!el || el.contains(e.relatedTarget)) return; st.hover = null; animStrip(); redraw(); });
    panel.addEventListener('click', e => {
      if (e.target.closest('[data-hist]')) {
        if (A.src === 'live') histFallback();
        else ensureDates().then(list => { const i = list.findIndex(x => x >= A.date), d = list[Math.max(0, (i < 0 ? list.length : i) - 1)]; if (d) openHist(d); });
        return;
      }
      const v = e.target.closest('[data-view]');
      if (v) { st.view = v.dataset.view; st.area = null; st.pin = null; st.hover = null; st.col = null; render(true); return; }
      const x = e.target.closest('[data-clear]');
      if (x) { if (x.dataset.clear === 'area') st.area = null; else st.pin = null; st.hover = null; render(true); return; }
      const el = e.target.closest('[data-l21]');
      if (!el) return;
      const L = P24.links[+el.dataset.l21];
      if (L.k === 'fcell') { st.col = L.j; render(true); return; }
      if (L.k === 'area') { pin({ k: 'area', part: L.part }); return; }
      pin(L);
    });
    dom('step21').addEventListener('click', e => { const b = e.target.closest('button'); if (b) stepReplay(Number(b.dataset.step)); });
    dom('panel21toggle').addEventListener('click', () => { const closed = dom('dr21-root').classList.toggle('panel21closed'); dom('panel21toggle').setAttribute('aria-pressed', String(!closed)); render(true); });
    det.addEventListener('mouseenter', () => { st.detOver = true; render(false); });
    det.addEventListener('mouseleave', () => { st.detOver = false; render(false); });
    dom('deth').addEventListener('click', () => { st.detPin = !st.detPin; render(false); });
    new ResizeObserver(() => redraw(true)).observe(cv);
  }
  function placeNav() {
    if (!V) return;
    nav.style.left = (V.plot.w / 2 - 50) + 'px';
    nav.style.top = (V.plot.h - (V.stripOn ? V.strip.h : 0) - 44) + 'px';
    nav.classList.toggle('show', st.navHover || (st.mx >= 0 && st.mx < V.plot.w && st.my < V.plot.h && st.my > V.plot.h * 0.5));
  }
  function showTip(h, x, y) {
    const html = tipHtml(h, V.ctx);
    if (!html) { tip.hidden = true; return; }
    tip.innerHTML = html; tip.hidden = false;
    const r = cv.getBoundingClientRect(), w = tip.offsetWidth, hh = tip.offsetHeight;
    let tx = x + 16, ty = y + 16;
    if (tx + w > r.width - 4) tx = x - w - 14;
    if (ty + hh > r.height - 4) ty = y - hh - 12;
    tip.style.left = Math.max(4, tx) + 'px'; tip.style.top = Math.max(4, ty) + 'px';
  }

  // ---------- interaction (TradingView-like; an area is drawn with «▭ Область» or Shift) ----------
  let raf = 0, fullNext = false;
  const redraw = full => { fullNext = fullNext || !!full; if (!raf) raf = requestAnimationFrame(() => { raf = 0; const f = fullNext; fullNext = false; render(f); }); };
  function stripTarget() { return V && V.stripOn && (st.stripPin || (st.hover && (st.hover.src === 'strip' || st.hover.k === 'stripBg'))) ? 150 : 46; }
  function animStrip() {
    const ts = stripTarget(), done = Math.abs(st.stripH - ts) < 1;
    if (done) { st.stripH = ts; redraw(); return; }
    st.stripH += (ts - st.stripH) * 0.35;
    redraw();
    requestAnimationFrame(animStrip);
  }
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
      if (d.zone === 'draw' && F && d.moved) d.area = areaFromDrag(F, d.x, d.y, x, y);
      else if (d.zone === 'proj' && F && d.moved && st.mode === 'bounds') { const ka = F.cellOfP(V.P(d.y)), kb = F.cellOfP(V.P(y)); d.area = { k0: Math.min(ka, kb), k1: Math.max(ka, kb) + 1 }; }
      else if (d.zone === 'strip' && F && d.moved) {
        const b0 = clamp(Math.floor((V.T(d.x) - F.f) / 15), 0, F.nb - 1), b1 = clamp(Math.floor((V.T(x) - F.f) / 15), 0, F.nb - 1);
        const a = st.area && isFinite(st.area.k0) ? st.area : { k0: -Infinity, k1: Infinity };
        d.area = { k0: a.k0, k1: a.k1, b0: Math.min(b0, b1), b1: Math.max(b0, b1) + 1 };
      }
      else if (d.zone === 'plot') {
        const span = d.v1 - d.v0; st.v0 = d.v0 - dx * span / V.plot.w; st.v1 = d.v1 - dx * span / V.plot.w;
        if (Math.abs(y - d.y) > 2 || !st.auto) { const ps = d.p1 - d.p0; st.auto = false; st.p0 = d.p0 + dy * ps / V.plot.h; st.p1 = d.p1 + dy * ps / V.plot.h; }
      } else if (d.zone === 'paxis') {
        const f = Math.exp(dy * 0.006), m = (d.p0 + d.p1) / 2, half = (d.p1 - d.p0) / 2 * f;
        st.auto = false; st.p0 = m - half; st.p1 = m + half;
      } else if (d.zone === 'taxis') {
        const f = Math.exp(-dx * 0.005), span = clamp((d.v1 - d.v0) * f, 30, 1500);
        st.v0 = d.v1 - span; st.v1 = d.v1;
      }
      cv.style.cursor = d.zone === 'plot' ? 'grabbing' : d.zone === 'paxis' ? 'ns-resize' : d.zone === 'taxis' ? 'ew-resize' : 'crosshair';
      tip.hidden = true;
      redraw();
      return;
    }
    const h = hit(x, y), key = o => JSON.stringify(o && Object.assign({}, o, { q: undefined, l: undefined, v: undefined, P: undefined, same: undefined }));
    const was = key(st.hover);
    st.hover = h && !['paxis', 'taxis', 'stripBg'].includes(h.k) ? h : (h && h.k === 'stripBg' ? h : null);
    cv.style.cursor = st.tool ? 'crosshair' : !h ? 'crosshair' : h.k === 'paxis' ? 'ns-resize' : h.k === 'taxis' ? 'ew-resize' : ['pcell', 'tcell', 'pt', 'area', 'col', 'fcell', 'unk'].includes(h.k) ? 'pointer' : 'crosshair';
    showTip(st.hover && st.hover.k !== 'stripBg' ? st.hover : null, x, y);
    if (key(st.hover) !== was) { animStrip(); redraw(true); } else redraw();
  });
  cv.addEventListener('mouseleave', () => { st.mx = -1; st.my = -1; if (!st.drag) { st.hover = null; tip.hidden = true; animStrip(); } redraw(true); });
  cv.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    const [x, y] = local(e), F = V.ctx.F;
    let zone = x > V.plot.w && x < V.plot.w + V.axisW && y < V.plot.h ? 'paxis' : V.projW && x >= V.proj.x && y < V.plot.h ? 'proj' : y > V.plot.h ? 'taxis' : 'plot';
    if (zone === 'plot' && F && V.stripOn && y >= V.strip.y && x >= V.strip.x && x <= V.strip.x + V.strip.w) zone = 'strip';
    else if (zone === 'plot' && F && (st.tool || e.shiftKey)) zone = 'draw';
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
      const same = st.area && st.area.k0 === h.k0 && st.area.k1 === h.k1 && st.area.b0 == null;
      st.area = same ? null : { k0: h.k0, k1: h.k1 }; render(true); return;
    }
    if (h && h.k === 'fcell' && d.zone === 'proj') { st.col = h.j; render(true); return; }
    if (h && h.k === 'tcell' && F) {                                  // a click on the time histogram: a window (for the band)
      const a = st.area && isFinite(st.area.k0) ? st.area : null, same = st.area && st.area.b0 === h.b0 && st.area.b1 === h.b1;
      st.area = same ? (a ? { k0: a.k0, k1: a.k1 } : null) : { k0: a ? a.k0 : -Infinity, k1: a ? a.k1 : Infinity, b0: h.b0, b1: h.b1 };
      render(true); return;
    }
    if (h && (h.k === 'stripBg' || h.src === 'strip')) { st.stripPin = !st.stripPin; animStrip(); return; }
    if (d.zone !== 'plot' && d.zone !== 'draw') return;
    if (h && h.k === 'pt') { pin(h); return; }
    if (h && (h.k === 'col' || h.k === 'fcell')) { st.col = st.col === h.j ? null : h.j; render(true); return; }
    if (h && h.k === 'area') { pin({ k: 'area', part: h.part }); return; }
    const b = barAt(V.ctx, V.T(x));
    if (b && y >= V.Y(b.h) - 6 && y <= V.Y(b.l) + 6 && b.t + 5 <= NOW) { replayAt(b.t + 5); return; }
    if (h && ['lvl', 'prev', 'vib'].includes(h.k)) { pin(h); return; }
    if (st.pin) { st.pin = null; st.hover = null; render(true); }
  }
  const pinKey = h => h ? [h.k, h.i, h.id, h.j, h.part, h.cat, h.t, h.p].join('|') : '';
  function pin(h) { st.pin = pinKey(st.pin) === pinKey(h) ? null : h; st.hover = null; tip.hidden = true; render(true); }
  cv.addEventListener('dblclick', e => {
    const [x, y] = local(e);
    if (x > V.plot.w && x < V.plot.w + V.axisW && y < V.plot.h) { st.auto = true; redraw(); }
    else if (y > V.plot.h && y < V.plot.h + V.timeH) { fitSession(st.session); redraw(); }
  });
  cv.addEventListener('wheel', e => {
    const [x] = local(e);
    e.preventDefault();
    if (x > V.plot.w) {
      const f = Math.exp(e.deltaY * 0.0015), m = (V.p0 + V.p1) / 2, half = (V.p1 - V.p0) / 2 * f;
      st.auto = false; st.p0 = m - half; st.p1 = m + half;
    } else if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
      const dt = (e.deltaX || e.deltaY) * (st.v1 - st.v0) / V.plot.w * 0.6; st.v0 += dt; st.v1 += dt;
    } else {
      // design 22 (operator 2026-09-29): the right edge stays at the session end + 45 minutes; the wheel only adds or
      // removes history on the left; zooming in stops at the «↺» view (box start .. session end)
      const lim = SESS[st.session].end + 45, minSpan = lim - (SESS[st.session].start - 25);
      const span = clamp((lim - st.v0) * Math.exp(e.deltaY * 0.0012), Math.min(minSpan, 1500), 1500);
      st.v1 = lim; st.v0 = lim - span;
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
    else { const f = z > 0 ? 1.35 : 1 / 1.35, span = clamp((st.v1 - st.v0) * f, 30, 1500); st.v0 = st.v1 - span; }
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
    PREV = x.prev ? { k: 'PREV', name: x.prev.name, start: -360, drH: x.prev.drH, drL: x.prev.drL, idrH: x.prev.idrH, idrL: x.prev.idrL } : null;
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
        PREV = x.prev ? { k: 'PREV', name: x.prev.name, start: -360, drH: x.prev.drH, drL: x.prev.drL, idrH: x.prev.idrH, idrL: x.prev.idrL } : null;
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
  window.__d24 = { st, A, render, cur, hit: (x, y) => hit(x, y), get V() { return V; }, passports: () => P24.list.slice(), links: () => P24.links.slice(), openHist, openLive, filmOf, levelQuery, areaInfo };
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
    cfgPanel();
    if (/^\d{4}-\d\d-\d\d$/.test(q.get('date') || '')) { A.src = 'hist'; A.date = q.get('date'); A.jump = true; st.rpWanted = at; }
    else if (at != null) { st.rp = at; st.session = sessOf(at) || st.session; st.userSession = true; fitSession(st.session); }
    render(true); loadDay(false);
  }
})();
