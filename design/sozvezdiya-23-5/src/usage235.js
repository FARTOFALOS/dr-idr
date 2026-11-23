  // ---------- the usage journal of 23.5 (spec/DR-LAB-23-5-USAGE-TRACKER.md, lab/usage235.py; operator 23.11.2026) ----------
  // What the operator's hand does with this screen, read from the screen's own state, never from the market: an action is
  // a change of the view state (st, A, TP, ANT) that follows his input, named by what changed; a click that changed
  // nothing is «клик без отклика»; a view is an object the interface itself recognised under the mouse (st.hover) shown
  // for at least 800 ms; an open detail is a pinned or open thing and how long it stayed on screen; the trace of the
  // mouse is kept in the screen's semantic coordinates: the region, the window fraction, the minute from the box start,
  // the position against the IDR (0 low, 1 high, an STD step 0.5), the family's SD from the edge in play and the named
  // line within 6 px (operator 23.11: «куда я вожу мышкой» — e.g. along the 70 % level to the left where no line is drawn).
  // No prices, no candles, no page text, no pixels of the chart. The chart never waits for the journal: events are
  // queued in this browser and posted in packets; a failure only delays them.
  const USG = {
    on: !/(?:^|[#&])usage=0(?:&|$)/.test(location.hash), visit: null, seq: 0, q: [], dropped: 0, rejected: 0, fail: 0, busy: false, saved: 0,
    lastInput: 0, idle: false, ptr: { in: false, x: -1, y: -1, el: null }, hov: null, hovGrace: 0, opens: new Map(),
    pending: null, base: null, baseHover: null, gest: null, wheel: null, stroke: null, avail: new Set(), ctxKey: '', inactive: 'hidden', started: false
  };
  const BUILD235 = '/*__BUILD235__*/';
  const UQ = 'drlab.usage235.q', UOFF = 'drlab.usage235.off', HOVER_MS = 800, IDLE_MS = 30000, TICK = 150, QMAX = 4000;
  try { if (localStorage.getItem(UOFF) === '1') USG.on = false; } catch (e) { /* optional */ }
  const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); }));
  const uid = v => v == null ? undefined : String(v).replace(/[^A-Za-z0-9_.:+\-|%/<>=]/g, '_').slice(0, 64) || undefined;
  const r2 = (v, q) => v == null || !isFinite(v) ? null : Math.round(v / q) * q;
  const rnd = (v, d) => v == null || !isFinite(v) ? null : +v.toFixed(d);
  function etDate() {
    const p = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    return p;
  }
  function uMode() { return A.src === 'hist' ? 'history' : st.rp != null ? 'replay' : 'live'; }
  function uLayers() {
    const on = Object.keys(st.L).filter(k => st.L[k]);
    if (typeof ANT !== 'undefined' && ANT.on) on.push('ant');
    if (typeof TRIAL !== 'undefined') for (const k of Object.keys(TRIAL)) if (TRIAL[k]) on.push('t.' + k);
    return on.join(',').slice(0, 160);
  }
  function uCtx() {
    const s = V && V.ctx && V.ctx.s, F = V && V.ctx && V.ctx.F;
    return {
      instrument: A.inst, trading_date: A.src === 'hist' ? A.date : etDate(), session: st.session, mode: uMode(),
      at: Math.round(st.rp != null ? st.rp : NOW), status: (s && s.status) || null,
      window: (typeof TP !== 'undefined' && (TP.pin || TP.last)) || null, event: st.ev, view: st.mode,
      layers: uLayers(), map: F ? (F._tp ? 'tp' : F.brk ? 'break' : 'table') : null
    };
  }
  // the object the interface recognised, named by its own identifiers (a window W1, a place R2, a level u2, a cell band)
  function uObj(h) {
    if (!h) return undefined;
    switch (h.k) {
      case 'tpwin': return uid(h.id);
      case 'tpzone': return uid(h.id + '.' + (h.ev || 'R') + (h.i + 1));
      case 'tpline': return uid((h.id || '') + '.' + (h.ev || ''));
      case 'zone': return uid((h.ev || '') + (h.i + 1));
      case 'lvl': return uid(h.id);
      case 'prev': return uid(h.id + '.' + (h.nm || ''));
      case 'pcell': case 'pbpcell': return uid((h.ev || '') + ':k' + h.k0 + '-' + h.k1);
      case 'tcell': case 'pbtcell': return uid((h.ev || '') + ':b' + h.b0 + '-' + h.b1);
      case 'hcell': return uid((h.ev || '') + ':k' + h.kk + 'b' + h.b);
      case 'fcell': case 'col': return uid('j' + h.j);
      case 'order': return uid(h.key);
      default: return uid([h.ev, h.id, h.i, h.j, h.part, h.cat].filter(v => v != null && v !== '').join('.')) || undefined;
    }
  }
  function uEmit(kind, f) {
    if (!USG.on || !USG.visit) return;
    const e = Object.assign({ schema_version: 1, event_id: uuid(), visit_id: USG.visit, seq: USG.seq++, started_at_utc: new Date().toISOString(), kind, build: BUILD235 }, f);
    if (e.feature) e.feature = uid(e.feature);   // an identifier the server accepts (review 23.11: one event refused by its name)
    for (const k of Object.keys(e)) if (e[k] === undefined || e[k] === null) delete e[k];
    if (!e.context) e.context = uCtx();
    USG.q.push(e);
    if (USG.q.length > QMAX) { const n = USG.q.length - QMAX; USG.q.splice(0, n); USG.dropped += n; }
    if (USG.q.length >= 60) uFlush(false);
  }
  function uSave(force) {
    const t = performance.now();
    if (!force && t - USG.saved < 3000) return;
    USG.saved = t;
    try { localStorage.setItem(UQ, JSON.stringify(USG.q)); } catch (e) {
      // the browser's store is full: keep the newer half, say so in the journal
      const n = Math.ceil(USG.q.length / 2); USG.q.splice(0, n); USG.dropped += n;
      try { localStorage.setItem(UQ, JSON.stringify(USG.q)); } catch (x) { /* optional */ }
    }
  }
  function uGapNote() {
    if (USG.dropped || USG.rejected) {
      const d = USG.dropped, r = USG.rejected; USG.dropped = 0; USG.rejected = 0;
      uEmit('gap', { feature: d ? 'queue.overflow' : 'events.rejected', data: { dropped: d, rejected: r } });
    }
  }
  async function uFlush(beacon) {
    if (!USG.q.length) return;
    uGapNote();
    const batch = USG.q.slice(0, 250), body = JSON.stringify({ schema_version: 1, events: batch }), url = '/api/usage/23-5/events';
    if (beacon) {
      // leaving or hiding the page: no answer is awaited; the events stay queued and the next opening resends them (the
      // server ignores an event_id it already has)
      try { navigator.sendBeacon(url, new Blob([body], { type: 'text/plain' })); } catch (e) { /* optional */ }
      uSave(true);
      return;
    }
    if (USG.busy) return;
    USG.busy = true;
    try {
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
      const j = await r.json().catch(() => ({}));
      if (r.ok && j.status === 'ok') {
        const done = new Set(j.accepted || []);
        for (const x of j.rejected || []) if (x.event_id) done.add(x.event_id);
        USG.rejected += (j.rejected || []).length;
        USG.q = USG.q.filter(e => !done.has(e.event_id)); USG.fail = 0; uSave(true);
      } else if (r.status === 400) { USG.q.splice(0, batch.length); USG.rejected += batch.length; USG.fail++; uSave(true); }
      else USG.fail++;
    } catch (e) { USG.fail++; }
    USG.busy = false;
  }

  // ---------- activity: the page visible, focused, the pointer inside it, an input within 30 s ----------
  const uVisible = () => document.visibilityState === 'visible';
  function uActive() {
    if (!uVisible()) return 'hidden';
    if (!document.hasFocus()) return 'blur';
    if (USG.idle) return 'idle';
    return null;
  }
  function uInput(e) {
    USG.lastInput = performance.now();
    if (USG.idle) { USG.idle = false; }
    if (!USG.visit) uBegin();
  }

  // ---------- the state the operator changes: one snapshot, diffed after each of his inputs ----------
  const U_FIELDS = ['inst', 'date', 'src', 'session', 'mode', 'ev', 'scope', 'view', 'tpPin', 'pin', 'area', 'col', 'rp', 'tool', 'ant', 'layers', 'trials', 'detPin', 'stripPin', 'panel', 'menu', 'cfg', 'day', 'auto'];
  const U_NAME = {
    inst: 'instrument', date: 'history.day', src: 'history.source', session: 'session', mode: 'map.mode', ev: 'event.focus', scope: 'family.scope',
    view: 'family.view', tpPin: 'tp.window_pin', pin: 'detail.pin', area: 'area.select', col: 'column.select', rp: 'replay.slice', tool: 'area.tool',
    ant: 'layer.ant', layers: 'layers', trials: 'trials', detPin: 'lower_window.pin', stripPin: 'strip.pin', panel: 'summary.panel',
    menu: 'menu.layers', cfg: 'menu.settings', day: 'menu.history', auto: 'price.autoscale'
  };
  function uSnap() {
    const a = st.area;
    return {
      inst: A.inst, date: A.date || '', src: A.src, session: st.session, mode: st.mode, ev: st.ev, scope: st.scope, view: st.view,
      tpPin: (typeof TP !== 'undefined' && TP.pin) || '', pin: st.pin ? st.pin.k + ':' + (uObj(st.pin) || '') : '',
      area: a ? [isFinite(a.k0) ? a.k0 : '', isFinite(a.k1) ? a.k1 : '', a.b0 ?? '', a.b1 ?? '', a.ev || ''].join('/') : '',
      col: st.col ?? '', rp: st.rp ?? '', tool: !!st.tool, ant: typeof ANT !== 'undefined' && !!ANT.on, layers: Object.keys(st.L).filter(k => st.L[k]).join(','),
      trials: typeof TRIAL !== 'undefined' ? Object.keys(TRIAL).filter(k => TRIAL[k]).join(',') : '', detPin: !!st.detPin, stripPin: !!st.stripPin,
      panel: !root.classList.contains('panel21closed'), menu: !!st.menu, cfg: !dom('cfgp').hidden, day: !dom('dayp').hidden, auto: !!st.auto
    };
  }
  function uValue(k, s, o) {
    if (k === 'layers' || k === 'trials') {
      const a = new Set(String(o[k]).split(',').filter(Boolean)), b = new Set(String(s[k]).split(',').filter(Boolean));
      const on = [...b].filter(x => !a.has(x)), off = [...a].filter(x => !b.has(x));
      return (on.length ? '+' + on.join('+') : '') + (off.length ? '-' + off.join('-') : '');
    }
    if (k === 'pin') return s.pin || 'none';
    if (k === 'rp') return s.rp === '' ? 'live' : 'm' + s.rp;
    const v = s[k];
    return v === true ? 'on' : v === false ? 'off' : v === '' ? 'none' : String(v);
  }
  // the control the operator pressed, named by its identifiers (never its text)
  function uControl(t) {
    if (!t || !t.closest) return null;
    const el = t.closest('button, input, select, summary, a, label, [data-l21], [data-scope], [data-view], [data-clear]');
    if (!el || !root.contains(el)) return null;
    const box = el.closest('#inst, #sess, #mode, #ev, #step21, #nav, #menu, #cfgp, #dayp, #panel, #det, #apibar, #insp');
    const d = el.dataset || {};
    if (box) {
      const b = box.id;
      if (b === 'inst') return ['top.instrument', d.i];
      if (b === 'sess') return ['top.session', d.s];
      if (b === 'mode') return ['top.mode', d.m];
      if (b === 'ev') return ['top.event', d.e];
      if (b === 'step21') return ['top.replay_step', d.step];
      if (b === 'nav') return ['chart.nav', d.z];
      if (b === 'menu') return ['layers.' + (d.l || el.id || 'item')];
      if (b === 'cfgp') return [d.trial ? 'trial.' + d.trial : d.c ? 'settings.' + d.c : d.g ? 'settings.group' : 'settings.' + (el.id || (el.closest('details') || {}).dataset?.g || 'item')];
      if (b === 'dayp') return ['history.' + (el.id || 'item')];
      if (b === 'panel' || b === 'det') {
        if (d.scope) return [b + '.scope', d.scope];
        if (d.view) return [b + '.view', d.view];
        if (d.clear) return [b + '.clear', d.clear];
        if (d.l21 != null && typeof P24 !== 'undefined') { const L = P24.links[+d.l21]; return [b + '.' + (L ? L.k : 'link'), uObj(L)]; }
        return [b + '.' + (el.id || el.tagName.toLowerCase())];
      }
      if (b === 'apibar') return ['top.' + (el.id || 'api')];
    }
    if (el.id) return ['top.' + el.id];
    return null;
  }
  // after an input: what changed is the action; the pending check is re-read once more for a change that lands later
  function uAfter(via, target, region, x, y, delay) {
    clearTimeout(USG.pendingT);
    const ctl = uControl(target);
    USG.pending = { via, ctl, region, x, y, t: performance.now(), tries: 0, hov: USG.baseHover, base: USG.base || uSnap() };
    USG.pendingT = setTimeout(uResolve, delay || 90);
  }
  function uResolve() {
    const p = USG.pending; if (!p) return;
    const s = uSnap(), o = p.base;
    const changed = U_FIELDS.filter(k => String(s[k]) !== String(o[k]));
    if (!changed.length && p.tries === 0 && p.ctl) { p.tries = 1; USG.pendingT = setTimeout(uResolve, 700); return; }
    USG.pending = null; USG.base = null;
    const from = p.ctl ? p.ctl[0] : p.region;
    if (changed.length) {
      // the primary function: the first by intent that took a value (clearing a pin after a switch is its consequence)
      const pos = changed.find(k => s[k] !== '' && s[k] !== false && s[k] !== 'none') || changed[0];
      const data = { from, changed: changed.filter(k => k !== pos).map(k => k + '=' + uValue(k, s, o)).slice(0, 8) };
      if (p.region === 'chart' && p.x >= 0) Object.assign(data, uPoint(p.x, p.y, true));
      if (!data.changed.length) delete data.changed;
      uEmit('action', { feature: U_NAME[pos] || pos, object: uid(uValue(pos, s, o)), via: p.via, data });
      uAvailability();
      return;
    }
    if (p.ctl) { uEmit('action', { feature: p.ctl[0], object: uid(p.ctl[1]), via: p.via }); return; }
    if (p.region && p.via === 'mouse') {
      // a click that changed nothing on screen: the place where he expected an answer
      const h = p.hov;
      uEmit('dead_click', { feature: 'click.' + p.region, object: h ? uid(h.k + (uObj(h) ? '.' + uObj(h) : '')) : 'empty', via: 'mouse', data: p.x >= 0 ? uPoint(p.x, p.y, true) : undefined });
    }
  }

  // ---------- gestures on the chart: a pan, a zoom of time or price, a reset; one record per finished gesture ----------
  const uView = () => ({ v0: st.v0, v1: st.v1, p0: V ? V.p0 : st.p0, p1: V ? V.p1 : st.p1, auto: !!st.auto });
  function uIdrW() { const s = V && V.ctx && V.ctx.s; return s && s.idrH != null && s.idrH > s.idrL ? s.idrH - s.idrL : null; }
  function uGesture(kind, via, g0, from) {
    const g1 = uView(), w = uIdrW();
    const dl = g1.v0 - g0.v0, ds = (g1.v1 - g1.v0) / Math.max(1, g0.v1 - g0.v0);
    // with the price scale on auto the screen fits the prices itself: only a manual scale is his gesture
    const manual = !(g0.auto && g1.auto);
    const dp = manual && w && g0.p0 != null && g1.p0 != null ? ((g1.p0 + g1.p1) - (g0.p0 + g0.p1)) / 2 / w : null;
    const ps = manual && g0.p0 != null && g1.p0 != null && g0.p1 !== g0.p0 ? (g1.p1 - g1.p0) / (g0.p1 - g0.p0) : null;
    if (Math.abs(dl) < 0.5 && Math.abs(ds - 1) < 0.01 && !(dp && Math.abs(dp) > 0.01) && !(ps && Math.abs(ps - 1) > 0.01) && g0.auto === g1.auto) return false;
    // 23.5 keeps the right edge at the session end: a horizontal drag or the wheel only adds or removes the past on the
    // left (operator 06.10), so the time gesture is named by that: more of the past, less of it
    const time = Math.abs(dl) >= 0.5 || Math.abs(ds - 1) >= 0.01, price = (dp && Math.abs(dp) > 0.01) || (ps && Math.abs(ps - 1) > 0.01) || g0.auto !== g1.auto;
    const f = kind || (time ? 'view.time' : 'view.price');
    const obj = kind ? undefined : time ? (dl < 0 ? 'more_past' : 'less_past') : g1.auto && !g0.auto ? 'auto' : ps && Math.abs(ps - 1) > 0.01 ? (ps > 1 ? 'wider' : 'narrower') : dp > 0 ? 'up' : 'down';
    uEmit('action', { feature: f, object: obj, via,
      data: { from, left_min: rnd(dl, 1), span_x: rnd(ds, 3), price_idr: rnd(dp, 3), price_span_x: rnd(ps, 3), span_min: Math.round(g1.v1 - g1.v0), also_price: time && price ? true : undefined } });
    return true;
  }

  // ---------- where the pointer is: a region of the screen and, over the chart, the method's coordinates ----------
  const U_REG = ['chart', 'price_axis', 'price_column', 'time_axis', 'strip', 'panel', 'lower_window', 'inspector', 'top', 'menu', 'other'];
  function uRegion(el, x, y) {
    if (!el || !el.closest) return 'other';
    if (el === cv && V) {
      if (x > V.plot.w && x < V.plot.w + V.axisW && y < V.plot.h) return 'price_axis';
      if (V.projW && x >= V.proj.x && y < V.plot.h) return 'price_column';
      if (y > V.taxisY) return 'time_axis';
      if (y > V.plot.h - (V.stripOn ? V.bandOv || 0 : 0)) return 'strip';
      return 'chart';
    }
    if (el.closest('#det')) return 'lower_window';
    if (el.closest('#panel')) return 'panel';
    if (el.closest('#insp')) return 'inspector';
    if (el.closest('#menu, #cfgp, #dayp')) return 'menu';
    if (el.closest('#tb')) return 'top';
    return 'other';
  }
  function uPoint(x, y, full) {
    // x, y: canvas pixels; returned: minute from the box start, position against the IDR, SD of the family from its
    // edge in play, the named line within 6 px
    if (!V || !V.ctx) return {};
    const s = V.ctx.s, F = V.ctx.F, p = V.P(y), out = {};
    const m = V.T(x) - SESS[st.session].start;
    out.min = r2(m, 1);
    if (s && s.idrH != null && s.idrH > s.idrL) out.idr = rnd((p - s.idrL) / (s.idrH - s.idrL), 2);
    if (F && F.u2p && F.w0) { const u = (p - F.e0) / (F.d0 * F.w0); if (isFinite(u)) out.sd = rnd(u, 2); }
    let best = 6.01, near = null;
    try {
      for (const l of levels(s)) { if (!stdShown(s, l)) continue; const d = Math.abs(V.Y(l.p) - y); if (d < best) { best = d; near = l.id; } }
      if (F && F._tp && typeof tpLevels === 'function') for (const L of tpLevels(F)) { const d = Math.abs(V.Y(F.u2p(L.k / 10)) - y); if (d < best) { best = d; near = 'reach' + L.q; } }
    } catch (e) { /* the family is being rebuilt */ }
    if (near) out.near = near;
    return out;
  }
  // a stroke: the pointer's path while the page is active; a point is [ms spent there, region, x/width, y/height,
  // minute from the box start, position to the IDR, family SD, near line]; consecutive equal points add up their time
  function uTrace(t) {
    const a = uActive() || (!USG.ptr.in ? 'pointer_left_page' : null);
    if (a || !USG.visit) { uStrokeEnd(); return; }
    const P = USG.ptr, reg = uRegion(P.el, P.cx, P.cy);
    let pt = [0, U_REG.indexOf(reg), r2(P.x / innerWidth, 0.01), r2(P.y / innerHeight, 0.01), null, null, null, null];
    if (P.el === cv && (reg === 'chart' || reg === 'strip' || reg === 'price_column' || reg === 'price_axis')) {
      const q = uPoint(P.cx, P.cy);
      pt[4] = reg === 'price_column' || reg === 'price_axis' ? null : q.min ?? null; pt[5] = q.idr ?? null; pt[6] = q.sd ?? null; pt[7] = q.near || null;
    }
    pt = pt.map(v => typeof v === 'number' ? +v.toFixed(2) : v);
    if (!USG.stroke) USG.stroke = { t0: new Date().toISOString(), last: t, tStart: t, p: [], ctx: uCtx() };
    const S = USG.stroke, dt = Math.round(t - S.last); S.last = t;
    const prev = S.p[S.p.length - 1];
    if (prev && prev.slice(1).every((v, i) => v === pt[i + 1])) prev[0] += dt;
    else { if (prev) prev[0] += dt; S.p.push(pt); }
    if (S.p.length >= 120 || t - S.tStart > 30000) uStrokeEnd();
  }
  function uStrokeEnd() {
    const S = USG.stroke; USG.stroke = null;
    if (!S || !S.p.length) return;
    while (S.p.length && S.p[S.p.length - 1][0] === 0) S.p.pop();
    if (!S.p.length) return;
    const ms = S.p.reduce((a, q) => a + q[0], 0);
    if (ms < 100) return;
    uEmit('trace', { feature: 'pointer', started_at_utc: S.t0, duration_ms: ms, context: S.ctx, data: { p: S.p.map(q => { const r = q.slice(); while (r.length > 4 && r[r.length - 1] == null) r.pop(); return r; }) } });
  }

  // ---------- views: an object under the mouse at least 800 ms; an open or pinned detail and how long it stayed ----------
  function uHoverNow() {
    const h = st.hover;
    if (!h || h.k === 'stripBg' || h.k === 'paxis' || h.k === 'taxis') return null;
    const reg = uRegion(USG.ptr.el, USG.ptr.cx, USG.ptr.cy);
    const where = reg === 'lower_window' ? 'lower_window' : reg === 'panel' ? 'panel' : 'chart';
    const feature = where + '.' + h.k, object = uObj(h);
    return { key: feature + '|' + (object || ''), feature, object };
  }
  function uOpensNow() {
    const m = new Map(), add = (feature, object) => m.set(feature + '|' + (object || ''), { feature, object });
    if (st.pin) add('open.pin.' + st.pin.k, uObj(st.pin));
    if (typeof TP !== 'undefined' && TP.pin) add('open.tp_window', uid(TP.pin));
    if (st.area) add('open.area', uid(st.area.b0 != null ? (isFinite(st.area.k0) ? 'price_time' : 'time') : 'price'));
    if (st.col != null) add('open.column', uid('j' + st.col));
    if (st.detPin) add('open.lower_window_pin');
    if (st.menu) add('open.menu.layers');
    if (!dom('cfgp').hidden) add('open.menu.settings');
    if (!dom('dayp').hidden) add('open.menu.history');
    if (typeof ANT !== 'undefined' && ANT.on) add('open.layer.ant');
    return m;
  }
  function uEndView(kind, v, reason, t) {
    const ms = Math.round(t - v.t0);
    if (ms >= HOVER_MS) uEmit(kind, { feature: v.feature, object: v.object, duration_ms: ms, end_reason: reason, started_at_utc: v.wall, context: v.ctx });
  }
  function uViews(t) {
    const inact = uActive();
    const out = inact || (!USG.ptr.in ? 'pointer_left_page' : null);
    // hover: needs the pointer inside the page; a flicker under 200 ms between the same object keeps one episode
    const h = out ? null : uHoverNow();
    const cur = USG.hov;
    if (cur && (!h || h.key !== cur.key)) {
      if (!h && !out && !USG.hovGrace) USG.hovGrace = t;
      if (h || out || t - USG.hovGrace > 200) { uEndView('hover_view', cur, out || (h ? 'replaced' : 'pointer_left_object'), USG.hovGrace && !h && !out ? USG.hovGrace : t); USG.hov = null; USG.hovGrace = 0; }
    } else USG.hovGrace = 0;
    if (h && !USG.hov) USG.hov = Object.assign({ t0: t, wall: new Date().toISOString(), ctx: uCtx() }, h);
    // open details: the page visible, focused, not idle and the pointer inside it (review 23.11: with the pointer gone to
    // another screen the detail's time is not counted; it resumes as a new episode when the pointer returns)
    const now = out ? new Map() : uOpensNow();
    for (const [k, v] of USG.opens) if (!now.has(k)) { uEndView('open_view', v, out || 'closed', t); USG.opens.delete(k); }
    for (const [k, v] of now) if (!USG.opens.has(k)) USG.opens.set(k, Object.assign({ t0: t, wall: new Date().toISOString(), ctx: uCtx() }, v));
  }
  function uEndAll(reason) {
    const t = performance.now();
    if (USG.hov) { uEndView('hover_view', USG.hov, reason, t); USG.hov = null; }
    for (const v of USG.opens.values()) uEndView('open_view', v, reason, t);
    USG.opens.clear();
    uStrokeEnd();
    if (reason !== 'idle') uAwayEnd(reason, t);   // looking at another screen is not idleness of this one
  }
  // the pointer outside the page while the page stays visible and focused: a look at another screen (TradingView on
  // the second monitor); at least 800 ms, at most 5 minutes (then he is not at the screens at all)
  const AWAY_MAX = 300000;
  function uAway(t) {
    const here = uVisible() && document.hasFocus();
    if (USG.away) {
      if (USG.ptr.in) uAwayEnd('returned', t);
      else if (!here) uAwayEnd(uActive() || 'blur', t);
      else if (t - USG.away.t0 > AWAY_MAX) uAwayEnd('idle', USG.away.t0 + AWAY_MAX);
    } else if (USG.visit && here && !USG.ptr.in && USG.ptr.x >= 0 && !USG.awayDone) {
      USG.away = { t0: t, wall: new Date().toISOString(), ctx: uCtx() };
    }
    if (USG.ptr.in) USG.awayDone = false;
  }
  function uAwayEnd(reason, t) {
    const a = USG.away; if (!a) return;
    USG.away = null;
    if (reason === 'idle') USG.awayDone = true;   // one record until the pointer comes back
    const ms = Math.round(t - a.t0);
    if (ms >= HOVER_MS) uEmit('away', { feature: 'pointer.away', duration_ms: ms, end_reason: reason, started_at_utc: a.wall, context: a.ctx });
  }

  // ---------- availability: which functions were on screen and usable, once per visit and context ----------
  function uAvailability() {
    if (!USG.visit) return;
    const c = uCtx(), ck = [c.instrument, c.session, c.mode].join('|');
    const seen = (f) => { const k = f + '|' + ck; if (USG.avail.has(k)) return; USG.avail.add(k); uEmit('available', { feature: f, context: c }); };
    const vis = el => el && !el.hidden && el.offsetParent !== null && !el.disabled;
    for (const el of root.querySelectorAll('#inst button, #sess button, #mode button, #ev button, #step21 button, #nav button')) if (vis(el)) { const ctl = uControl(el); if (ctl) seen(ctl[0]); }
    for (const id of ['areab', 'antb', 'dayb', 'panel21toggle', 'lay', 'cfgb', 'cmp22', 'back', 'refresh21', 'deth']) { const el = dom(id); if (vis(el)) seen('top.' + id); }
    if (st.menu) for (const el of root.querySelectorAll('#menu input[data-l]')) if (vis(el)) seen('layers.' + el.dataset.l);
    // what the chart offers under the mouse right now (the interface's own hit kinds)
    if (V) {
      seen('chart.view');   // the chart's own gestures: a drag, the wheel, a double click, Alt+R
      // a window is pinned and an area selected by a click on the chart itself (no button): their availability is
      // what makes them pressable (review 23.11: «доступность не подтверждена» beside their use)
      if ((V.tpCaps || []).length) { seen('chart.tpwin'); seen('tp.window_pin'); }
      if ((V.zoneHit || []).length) seen('chart.zone');
      if ((V.projBars || []).length) seen('chart.pcell');
      if ((V.projBars || []).length || V.stripOn) seen('area.select');
      if (V.ctx && V.ctx.s && V.ctx.s.drH != null) seen('chart.lvl');
    }
    for (const el of root.querySelectorAll('#panel [data-l21]')) { if (!vis(el) || typeof P24 === 'undefined') continue; const L = P24.links[+el.dataset.l21]; if (L) seen('panel.' + L.k); }
  }

  // ---------- the visit: begins when the page is first visible and focused; a reload is a new visit ----------
  function uBegin() {
    if (USG.visit || !USG.on || !uVisible() || !document.hasFocus()) return;
    // the opening is named in the session the screen shows: wait for its data (at most 10 s), not the default context
    // before loading (review 23.11: «before» and RDR at every opening)
    if (!(V && V.ctx && V.ctx.s) && performance.now() < 10000) return;
    USG.visit = uuid(); USG.seq = 0;
    const nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || {};
    uEmit('visit', { feature: 'page.open', via: uid(nav.type || 'navigate'), data: { w: innerWidth, h: innerHeight, dpr: devicePixelRatio || 1, queued: USG.q.length } });
    uAvailability();
  }
  function uStart() {
    if (USG.started) return;
    USG.started = true;
    try { const q = JSON.parse(localStorage.getItem(UQ) || '[]'); if (Array.isArray(q)) USG.q = q.slice(-QMAX); } catch (e) { /* optional */ }
    const cap = { capture: true, passive: true };
    document.addEventListener('pointermove', e => {
      const inside = e.clientX >= 0 && e.clientY >= 0 && e.clientX < innerWidth && e.clientY < innerHeight;
      USG.ptr.in = inside; USG.ptr.x = e.clientX; USG.ptr.y = e.clientY; USG.ptr.el = e.target;
      if (e.target === cv) { const r = cv.getBoundingClientRect(); USG.ptr.cx = e.clientX - r.left; USG.ptr.cy = e.clientY - r.top; }
      if (inside) uInput(e);
    }, cap);
    document.addEventListener('pointerout', e => { if (!e.relatedTarget) { USG.ptr.in = false; } }, cap);
    document.documentElement.addEventListener('pointerleave', () => { USG.ptr.in = false; }, { passive: true });
    document.addEventListener('pointerdown', e => {
      uInput(e);
      if (e.button !== 0) return;
      // the state before the press (this capture listener runs before the page's own handlers)
      USG.base = uSnap(); USG.baseHover = st.hover;
      USG.gest = { t: e.target, x: e.clientX, y: e.clientY, view: uView() };
      // after the chart's own mousedown st.drag tells the zone of the gesture
      setTimeout(() => { if (USG.gest && st.drag) USG.gest.zone = st.drag.zone; }, 0);
    }, true);
    window.addEventListener('pointerup', e => {
      const g = USG.gest; USG.gest = null;
      if (!g || e.button !== 0) return;
      const moved = Math.abs(e.clientX - g.x) + Math.abs(e.clientY - g.y) > 3;
      if (g.t === cv) {
        const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top, region = uRegion(cv, g.x - r.left, g.y - r.top);
        if (g.zone && /^al/.test(g.zone)) { setTimeout(() => uEmit('action', { feature: 'alert.' + g.zone.slice(2).toLowerCase(), via: 'mouse', data: uPoint(x, y) }), 60); return; }
        if (moved && ['plot', 'paxis', 'taxis'].includes(g.zone)) { setTimeout(() => uGesture(null, 'drag', g.view, 'chart.view'), 60); return; }
        uAfter('mouse', null, region, x, y);
        return;
      }
      if (!moved) uAfter('mouse', g.t, uRegion(g.t, -1, -1), -1, -1);
    }, true);
    document.addEventListener('keydown', e => {
      uInput(e);
      if (e.target && /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
      if (e.key === 'Escape' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') { USG.base = uSnap(); USG.baseHover = null; uAfter('key', null, 'keyboard', -1, -1); return; }
      if (e.altKey && /^[rRкК]$/.test(e.key)) { const g = uView(); setTimeout(() => uGesture('view.reset', 'key', g, 'chart.view'), 60); }
    }, true);
    document.addEventListener('change', e => { uInput(e); if (e.target && e.target.closest && e.target.closest('#cfgp, #menu, #dayp, #apibar') && e.target.id !== 'usageOn') { USG.base = USG.base || uSnap(); uAfter('mouse', e.target, 'menu', -1, -1, 40); } }, true);
    document.addEventListener('wheel', e => {
      if (e.target !== cv) return;
      uInput(e);
      if (!USG.wheel) USG.wheel = { view: uView() };
      clearTimeout(USG.wheel.t);
      USG.wheel.t = setTimeout(() => { const w = USG.wheel; USG.wheel = null; uGesture(null, 'wheel', w.view, 'chart.view'); }, 300);
    }, { capture: true, passive: true });   // before the chart's own handler: the view before the first notch
    cv.addEventListener('dblclick', () => { const g = uView(); setTimeout(() => uGesture('view.reset', 'mouse', g, 'chart.view'), 60); }, { passive: true });
    nav.addEventListener('click', () => { /* the nav buttons change the view: recorded as a gesture of the control */ const g = uView(); setTimeout(() => uGesture(null, 'button', g, 'chart.nav'), 60); }, true);
    document.addEventListener('visibilitychange', () => { if (!uVisible()) { uEndAll('hidden'); uFlush(true); } else uBegin(); });
    window.addEventListener('blur', () => { uEndAll('blur'); });
    window.addEventListener('focus', () => uBegin());
    window.addEventListener('pagehide', () => { uEndAll('pagehide'); uFlush(true); });
    setInterval(() => {
      const t = performance.now();
      if (!USG.on) return;
      if (!USG.visit) { uBegin(); return; }
      if (!USG.idle && t - USG.lastInput > IDLE_MS) { uEndAll('idle'); USG.idle = true; }
      // a view, an open detail and a stroke belong to one context: a switch of the instrument, session, mode or day
      // ends them, and they begin again under the new one (review 23.11: a window pinned on NQ was counted 35 s on NQ
      // across switches to ES and YM)
      const vk = [A.inst, st.session, uMode(), A.src === 'hist' ? A.date : ''].join('|');
      if (USG.viewKey && vk !== USG.viewKey) uEndAll('context');
      USG.viewKey = vk;
      uViews(t);
      uAway(t);
      uTrace(t);
      const ck = [A.inst, st.session, uMode(), st.mode].join('|');
      // and again every 5 s: the chart's objects (windows, zones, cells) appear only after the family has loaded, after
      // the switch itself (the check repeats nothing already noted for this context)
      if (ck !== USG.ctxKey || t - (USG.availT || 0) > 5000) { USG.ctxKey = ck; USG.availT = t; uAvailability(); }
    }, TICK);
    // the server unreachable: retry every 15 s, after 20 failures every 2 minutes; the queue waits in this browser
    let skip = 0;
    setInterval(() => { if (USG.on) { uSave(false); if (USG.q.length && (USG.fail < 20 || ++skip % 8 === 0)) uFlush(false); } }, 15000);
    setTimeout(() => { if (USG.q.length) uFlush(false); }, 4000);
    uBegin();
  }
  // the switch outside the chart (⚙ Настройки): stops the journal in this browser; the report opens beside the screen
  function usageSettings() {
    return '<details class="cgd" data-g="usage"><summary class="cg">Запись использования</summary>' +
      '<label class="cr"><span>Записывать, как я пользуюсь экраном</span><input type="checkbox" id="usageOn"' + (USG.on ? ' checked' : '') + '></label>' +
      '<div class="p21-note">Только действия на этом экране, без цен. Журнал: lab/.runtime/usage-23-5.sqlite3' + (USG.q.length ? ' · в очереди ' + USG.q.length : '') + '</div>' +
      '<a href="/23-5/usage/" target="_blank" rel="noopener">Отчёт использования ↗</a></details>';
  }
  function usageToggle(on) {
    if (!on && USG.on) { uEndAll('closed'); uEmit('tracker', { feature: 'tracker.off', via: 'mouse' }); uFlush(false); }
    USG.on = on;
    try { localStorage.setItem(UOFF, on ? '0' : '1'); } catch (e) { /* optional */ }
    if (on) { USG.visit = null; uBegin(); uEmit('tracker', { feature: 'tracker.on', via: 'mouse' }); }
  }
  window.__usage235 = { state: () => USG, flush: () => uFlush(false), snap: () => uSnap() };   // for tests/usage235_page checks
  setTimeout(uStart, 0);
