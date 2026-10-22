  // ================= «Откаты до обновления» · the candidate DR-LAB-PB-0.1 (operator 2026-10-21) =================
  // meaning/lens/2026-10-21-otkaty-do-obnovleniya/: the construction, its review, the definition and the answer. A view of
  // the existing bounds layout; PB-L occupies its amber R display slot. Accepted BASE/NOW stay separate.
  // One source-bound publication (GET /api/integration/pullbacks, lab/pullbacks24.py) for the family on screen (the same
  // F, N, frame): every member's episodes H -> L -> B with its witness bars, the merged bottoms, the constellations of
  // every scale and today's facts. Before anything is drawn the page checks the release hash, the scene and family, every
  // witness against the accepted family path, every star against its own bars (its vertex, the first update, nothing
  // deeper between, after the activation) and every constellation's members and share against its bundle; a failed check
  // withdraws the number and the drawing together. Stepping by M5 changes only today's facts: the map is the family's
  // history, fixed at its activation, and a pinned historical session stays pinned.
  const PBC = cfg.R, PB_SCALES = [1, 2, 3, 6], PB_KEY = 'drlab.d235.pbscale';
  const PB = { key: null, packet: null, pending: null, error: null, seq: 0, scale: 1, cl: null, verified: 0 };
  try { const k = +localStorage.getItem(PB_KEY); if (PB_SCALES.includes(k)) PB.scale = k; } catch (e) { /* 1 */ }
  {
    const q = new URLSearchParams(location.hash.slice(1)), k = +q.get('pbscale');
    if (PB_SCALES.includes(k)) PB.scale = k;
    if (ICFG.enabled && q.get('mode') === 'pullbacks') { TRIAL.pullbacks = true; st.mode = 'bounds'; }
  }
  const pullbackMode = () => ICFG.enabled && TRIAL.pullbacks && st.mode === 'bounds';
  // Keep the original star layer on. Compact cell representatives below prevent a catalogue of overlapping episodes.
  function pbRequest(ctx) {
    if (!ctx.F || !ctx.F.N || !ctx.s.conf) return null;
    const cut = sliceOf(ctx), view = st.view === 'conf' ? 'conf' : 'auto', a = st.area, region = a && a.ev !== 'X' ? [a.k0,a.k1,a.b0,a.b1].map(v=>Number.isFinite(v)?v:null) : null;
    return { cut, view, region, key: [JSON.stringify(region),IS.epoch, A.inst, ctx.D.iso, ctx.s.k, cut, view, st.scope, ctx.F.r.snapshot_id].join('|') };
  }
  function pbPacket(ctx) { const q = pbRequest(ctx); return q && PB.key === q.key ? PB.packet : null; }
  function requestPullbacks(ctx) {
    if (!pullbackMode()) return;
    const q = pbRequest(ctx);
    if (!q || (q.key === PB.key && (PB.packet || PB.error)) || PB.pending === q.key) return;
    const token = ++PB.seq, F = ctx.F;
    PB.key = q.key; PB.packet = null; PB.error = null; PB.pending = q.key; PB.cl = null;
    const args = new URLSearchParams({ instrument: A.inst, session: ctx.s.k, at: q.cut, view: q.view, scope: st.scope });
    if (A.src === 'hist') args.set('date', A.date);
    if (q.region) args.set('region', JSON.stringify(q.region));
    fetch('/api/integration/pullbacks?' + args).then(async res => {
      const r = await res.json();
      if (!res.ok) throw Error(r.message || r.error || 'Сервер не ответил');
      if (token !== PB.seq) return;
      if (r.status !== 'OK') throw Error(r.message || r.status);
      await pbVerify(r, q, ctx, F);
      if (token !== PB.seq) return;
      PB.packet = r; PB.verified++;
    }).catch(e => { if (token === PB.seq) { PB.error = e.message; PB.packet = null; } })
      .finally(() => { if (token === PB.seq) PB.pending = null; redraw(true); });
  }
  function pbBundle(r, est, pred) {
    const f = REVIEW && REVIEW.forms[est], b = (r.contract.bundles || []).find(x => x.estimand === est && pred(parOf(x)));
    if (!b || !f || b.claim_form !== f.id || b.claim.claim_class !== f.claim_class || !(b.admissible_claims || []).includes(f.claim_class)) return null;
    return b;
  }
  // a star and its own bars: the vertex (equal highs, kt neighbours on each side strictly lower), no update before B, the
  // update at B, nothing deeper between H and B, the bottom after the activation
  function pbWitness(pt, w, E) {
    const bars = w.bars, bl = bars[pt.i];
    if (!bl || bl[2] !== pt.v || pt.i <= w.act_i) return 'дно не на своей M5';
    for (const id of pt.episodes) {
      const e = E.get(id);
      if (!e || e.case !== pt.case || e.status !== 'KNOWN' || e.jl !== pt.i || e.L !== pt.v) return 'эпизод точки';
      for (let j = e.a; j <= e.b; j++) if (!bars[j] || bars[j][1] !== e.h) return 'вершина';
      for (let k = 1; k <= e.kt; k++) { const l = bars[e.a - k], r = bars[e.b + k]; if (!l || !r || l[1] >= e.h || r[1] >= e.h) return 'соседи вершины'; }
      for (let j = e.b + 1; j < e.jb; j++) if (!bars[j] || bars[j][1] > e.h) return 'обновление раньше B';
      if (!bars[e.jb] || bars[e.jb][1] <= e.h) return 'нет обновления на B';
      for (let j = e.a + 1; j < e.jb; j++) if (bars[j][2] < pt.v) return 'дно глубже';
      if (pt.i < e.a || pt.i > e.jb) return 'дно вне отрезка H–B';
    }
    return null;
  }
  function pbZoneCheck(r, s) {
    const p = r.proof, zm = p.maps[String(s)], N = p.context.N, pts = p.points.filter(q => q.kt >= s);
    for (const z of zm.zones) {
      const cells = new Set(z.cell_mask.map(c => c[0] + '|' + c[1]));
      const mem = [...new Set(pts.filter(q => cells.has(q.k + '|' + q.b)).map(q => q.case))].sort();
      if (JSON.stringify(mem) !== JSON.stringify(z.members) || z.n_known !== mem.length) return 'состав ' + z.label;
      const b = pbBundle(r, 'EST:PB-ZONE', x => x.zone_id === z.zone_id && x.scale === s);
      const pt = b && b.estimates.find(e => e.value_kind === 'POINT'), bd = b && b.estimates.find(e => e.value_kind === 'BOUNDS');
      if (!pt || pt.numerator !== z.n_known || pt.denominator !== N || (z.n_possible ? !bd || Math.abs(bd.upper - (z.n_known + z.n_possible) / N) > 1e-12 : !!bd)) return 'доля ' + z.label;
    }
    const sb = pbBundle(r, 'EST:PB-SESSIONS', x => x.scale === s), cats = sb && sb.estimates[0].categories;
    if (!cats || cats.reduce((t, c) => t + c.count, 0) !== N || cats.some(c => c.count !== zm.sessions[c.category])) return 'категории сессий';
    return null;
  }
  async function pbVerify(r, q, ctx, F) {
    const p = r.proof, c = p.context;
    if (!r.contract || r.contract.status !== 'CONFORMANT' || reviewFault(r)) throw Error(r.message || 'Нет проверенного выпуска');
    if (c.instrument !== A.inst || c.date !== ctx.D.iso || c.session !== ctx.s.k || c.cut !== q.cut || c.scope !== st.scope) throw Error('Ответ другого среза');
    if (!F || c.family_id !== F.r.family_id || c.snapshot_id !== F.r.snapshot_id || c.view !== F.view || c.N !== F.N) throw Error('Ответ другой семьи или рамки');
    if (c.base_registry_hash !== SC11.registry_hash || c.registry_hash !== REVIEW.registry_hash) throw Error('Другой реестр контракта');
    if (p.definition.version !== 'DR-LAB-PB-0.1' || JSON.stringify(p.definition.scales) !== JSON.stringify(PB_SCALES)) throw Error('Другая версия определения');
    if (await cHash(p) !== r.release_id) throw Error('Данные выпуска подменены');
    if (p.sessions.length !== F.M.length) throw Error('Свидетели — не члены семьи');
    p.sessions.forEach((w, i) => {
      const m = F.M[i];
      if (w.id !== m.id || w.w !== m.w || w.act !== m.act || p.grid[w.act_i] !== m.act) throw Error('Свидетель не совпадает с семьёй: ' + w.id);
      for (let j = 0; j < F.grid.length; j++) {
        const b = w.bars[p.first_i + j], f = m.path[j];
        if ((b == null) !== (f == null) || (b && (b[2] !== f[0] || b[1] !== f[1] || b[3] !== f[2]))) throw Error('Путь свидетеля не совпадает с путём семьи: ' + w.id);
      }
    });
    const W = new Map(p.sessions.map(w => [w.id, w])), E = new Map(p.episodes.map(e => [e.id, e]));
    for (const pt of p.points) { const bad = pbWitness(pt, W.get(pt.case), E); if (bad) throw Error('Точка не подтверждается своими свечами (' + bad + '): ' + pt.case); }
    for (const s of PB_SCALES) { const bad = pbZoneCheck(r, s); if (bad) throw Error('Созвездие не совпадает с публикацией: ' + bad + ' · масштаб ' + s); }
    if(q.region && PB_SCALES.some(s=>!p.marginals[String(s)].some(v=>['k0','k1','b0','b1'].every((k,i)=>v[k]===q.region[i]))))throw Error('Ответ не содержит выбранную область');
    for (const s of PB_SCALES) for (const v of p.marginals[String(s)]) {
      const pts=p.points.filter(pt=>pt.kt>=s&&(v.k0==null||pt.k>=v.k0)&&(v.k1==null||pt.k<v.k1)&&(v.b0==null||pt.b>=v.b0)&&(v.b1==null||pt.b<v.b1));
      const members=[...new Set(pts.map(pt=>pt.case))].sort(), later=new Set(pts.filter(pt=>pt.open+5>q.cut).map(pt=>pt.case)).size;
      const b=pbBundle(r,'EST:PB-REGION',x=>x.scale===s&&['k0','k1','b0','b1'].every(k=>x[k]===v[k])),pt=b?.estimates.find(e=>e.value_kind==='POINT'),bd=b?.estimates.find(e=>e.value_kind==='BOUNDS');
      if(JSON.stringify(members)!==JSON.stringify(v.members)||v.n_known!==members.length||v.earlier+v.later!==members.length||v.later!==later||!pt||pt.numerator!==members.length||pt.denominator!==F.N||(v.n_possible&&(!bd||Math.abs(bd.upper-(members.length+v.n_possible)/F.N)>1e-12))) throw Error('Кластер цены/времени не совпадает с составом сессий');
    }
    // today: the published bars are the visible prefix of this page; every completed episode stands on them
    const T = p.today;
    if (JSON.stringify(todayDirected(ctx, p, T)) !== JSON.stringify(T.bars)) throw Error('Сегодняшние свечи ответа не совпадают с экраном');
    const tw = { bars: T.bars, act_i: p.grid.indexOf(T.act) };
    for (const e of T.episodes) if (e.status === 'KNOWN') {
      const bad = pbWitness({ i: e.jl, v: e.L, case: 'today', episodes: ['t'] }, tw, new Map([['t', Object.assign({}, e, { id: 't', case: 'today' })]]));
      if (bad) throw Error('Сегодняшний эпизод не стоит на свечах: ' + bad);
    }
    return r;
  }
  // today's closed M5 of the block up to the slice, in the frame of the answer (directed ticks)
  function todayDirected(ctx, p, T) {
    const tick = A.day.tick || 0.25, by = new Map(ctx.D.bars.map(b => [b.t + 5, b])), t = v => Math.round(v / tick), d = T.direction, e = T.edge_ticks, out = [];
    for (const Tm of p.grid) {
      if (Tm > T.cut) break;
      const b = by.get(Tm);
      out.push(!b ? null : d === 1 ? [t(b.o) - e, t(b.h) - e, t(b.l) - e, t(b.c) - e] : [e - t(b.o), e - t(b.l), e - t(b.h), e - t(b.c)]);
    }
    return out;
  }
  function pbMst(pts) {
    const n = pts.length, inT = new Uint8Array(n), best = new Float64Array(n).fill(Infinity), from = new Int32Array(n).fill(-1), segs = [];
    if (!n) return segs;
    best[0] = 0;
    for (let it = 0; it < n; it++) {
      let u = -1;
      for (let i = 0; i < n; i++) if (!inT[i] && (u < 0 || best[i] < best[u])) u = i;
      inT[u] = 1;
      if (from[u] >= 0) segs.push([pts[from[u]][0], pts[from[u]][1], pts[u][0], pts[u][1]]);
      for (let i = 0; i < n; i++) if (!inT[i]) { const d = Math.hypot(pts[u][0] - pts[i][0], pts[u][1] - pts[i][1]); if (d < best[i]) { best[i] = d; from[i] = u; } }
    }
    return segs;
  }
  function pbGeom(ctx, r) {
    const p = r.proof, s = PB.scale, F = ctx.F;
    const key = [V.plot.w, V.plot.h, st.v0, st.v1, V.p0, V.p1].map(v => Math.round(v * 100)).join('|') + '|' + s + '|' + r.release_id;
    if (PB.cl && PB.cl.key === key) return PB.cl;
    const W = new Map(p.sessions.map(w => [w.id, w])), E = new Map(p.episodes.map(e => [e.id, e])), P = new Map(p.points.map(q => [q.id, q]));
    const zones = p.maps[String(s)].zones.map((z, i) => {
      const cells = new Set(z.cell_mask.map(c => c[0] + '|' + c[1]));
      const pts = p.points.filter(q => q.kt >= s && cells.has(q.k + '|' + q.b)).map(q => ({ q, x: V.X(q.open + 2.5), y: V.Y(F.u2p(q.v / W.get(q.case).w)) }));
      const xy = pts.map(o => [o.x, o.y]), kd = xy.length ? kde(xy, 18) : null;
      return { z, i, pts, kd, g1: kd ? iso(kd, 0.22) : [], g2: kd ? iso(kd, 0.6) : [], hit: kd ? iso(kd, 0.2) : [], ln: kd ? iso(kd, 0.35) : [], mst: pbMst(xy) };
    });
    return (PB.cl = { key, zones, W, E, P });
  }
  const pbShare = (z, N) => z.n_possible ? pct(100 * z.n_known / N) + '–' + pct(100 * (z.n_known + z.n_possible) / N) : pct(100 * z.n_known / N);
  const pbRel = (r, i) => r.proof.today.zones[String(PB.scale)][i];
  // A bottom can link to several vertices; only vertices established at this view's scale explain its star.
  const pbLinks = (pt, episodes) => pt.episodes.map(id => episodes.get(id)).filter(e => e && e.kt >= PB.scale);
  function pbHit(x, y) {
    if (!pullbackMode()) return null;
    const ctx = V.ctx, r = pbPacket(ctx);
    if (!r || !ctx.F) return null;
    const G = pbGeom(ctx, r);
    let best = null, bd = 5;
    for (const g of G.zones) for (const o of g.pts) { const d = Math.hypot(o.x - x, o.y - y); if (d < bd) { bd = d; best = o; } }
    if (best) {
      const same = new Set(G.zones.flatMap(g => g.pts).filter(o => Math.hypot(o.x - best.x, o.y - best.y) < 2.5).map(o => o.q.case));
      return { k: 'pbpt', id: best.q.id, same: same.size };
    }
    for (const L of V.pbLbl || []) if (x >= L.box[0] && x <= L.box[0] + L.box[2] && y >= L.box[1] && y <= L.box[1] + L.box[3]) return { k: 'pbzone', i: L.i };
    for (const g of G.zones) if (g.hit.length && inLoops(g.hit, x, y)) return { k: 'pbzone', i: g.i };
    return null;
  }
  // ---------- words: only the registered labels of the candidate edition (integration/candidates/registry/90-pullbacks.yaml) ----------
  const PZ = 'EST:PB-ZONE', PS = 'EST:PB-SESSIONS', PT = 'FF:PB-TODAY', PE = 'FF:PB-EPISODE';
  const pbStatus = ctx => !ctx.F || !ctx.F.N ? statusMsg(ctx) : PB.error || 'Собираю эпизоды семьи…';
  // the frame's own words: in a short (and in a break frame of a long) the vertex is a low and the pullback ends at a high
  const pbW = F => { const d = F && F.d0 === -1 ? 'down' : 'up'; return { top: lbl(PE, 'top_' + d), topg: lbl(PE, 'topg_' + d), topgp: lbl(PE, 'topgp_' + d), bot: lbl(PE, 'bot_' + d) }; };
  function pbRelWords(rel, F) {
    const v = rel.visit, cp = rel.completion, w = pbW(F);
    return { clock: lbl(PT, rel.clock), visit: v.state === 'VISITED' ? lbl(PT, 'VISITED', { t: clk(v.close) }) : lbl(PT, v.state === 'UNKNOWN' ? 'VISIT_UNKNOWN' : 'NOT_YET'),
      completion: cp.state === 'COMPLETED' ? lbl(PT, 'COMPLETED', { top: w.top, h: clk(cp.h_open), t: clk(cp.b_close) }) : cp.state === 'IN_ZONE_NOT_UPDATED' ? lbl(PT, 'IN_ZONE_NOT_UPDATED', { top: w.top, h: clk(cp.h_open) }) : lbl(PT, 'NONE') };
  }
  const pbDisplayLabel=z=>z.label.replace(/^L/,'R');
  const pbWin = z => clk(z.time_start) + '–' + clk(z.time_end);
  const pbDate = id => id.slice(3, 7) + '-' + id.slice(7, 9) + '-' + id.slice(9, 11);
  const pbScaleSwitch = () => '<span class="p24-seg sm pbseg" title="' + esc(lbl(PZ, 'scale_title', { k: PB.scale })) + '"><span class="pbsl">' + lbl(PZ, 'scale') + '</span>' +
    PB_SCALES.map(k => '<button data-pbscale="' + k + '" class="' + (PB.scale === k ? 'on' : '') + '">' + k + '</button>').join('') + '</span>';
  function compare24Href(ctx) {
    const q = new URLSearchParams({ inst: A.inst, session: st.session, at: clk(sliceOf(ctx)), scope: st.scope });
    if (A.src === 'hist' && A.date) q.set('date', A.date);
    if (st.view === 'conf') q.set('view', 'conf');
    return 'http://127.0.0.1:8767/24/#' + q;
  }
  function pbPanel(ctx) {
    requestPullbacks(ctx);
    const F = ctx.F, r = pbPacket(ctx), out = [];
    out.push('<div class="p21-h"><span title="' + esc(lbl(PZ, 'head_title')) + '">' + lbl(PZ, 'head') + '</span><span>' + (F ? lbl(PZ, 'frame', null, VW(F)) : '') + '</span></div>');
    if (F) out.push('<div class="p21-note">' + esc(F.cond) + '</div>');
    if (A.src === 'hist') out.push('<div class="p21-note"><a class="pbcompare" data-compare24="1" href="' + esc(compare24Href(ctx)) + '" target="_blank" rel="noopener">Сравнить этот срез с №24 ↗</a></div>');
    out.push('<div class="p21-h second pbctl">' + pbScaleSwitch() + scopeSwitch() + '</div>');
    if (!r) return out.join('') + '<div class="p21-note">' + esc(pbStatus(ctx)) + '</div>';
    const p = r.proof, zm = p.maps[String(PB.scale)], N = p.context.N, sl = sliceOf(ctx), now = () => '<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>';
    if (!zm.zones.length) out.push('<div class="p21-note">' + lbl(PZ, 'none', { need: zm.need }) + '</div>');
    let sep = false;
    zm.zones.forEach((z, i) => {
      if (!sep && z.time_end > sl) { sep = true; out.push(now()); }
      const wd = pbRelWords(pbRel(r, i), F), b = pbBundle(r, PZ, x => x.zone_id === z.zone_id && x.scale === PB.scale);
      const row = '<span class="t"><span><span class="zt">' + pbWin(z) + '</span> <i class="zn" style="color:' + PBC + '">' + z.label + '</i></span>' +
        '<span class="p21-sub">' + lbl(PZ, 'sub', { band: band(z.price_low, z.price_high), clock: wd.clock }) + '</span>' +
        '<span class="p21-sub">' + lbl(PT, 'row') + ': ' + esc(wd.visit) + ' · ' + esc(wd.completion) + '</span></span><b class="zp">' + (b ? pbShare(z, N) : '—') + '</b>';
      let html = link({ k: 'pbzone', i }, row, 'mc' + (pbRel(r, i).clock === 'PAST' ? ' zst-IMPOSSIBLE' : ''), null, b ? b.claim.statement_ru : '');
      if (b) html = html.replace('data-l21=', 'data-bundle="' + b.id + '" data-edition="' + REVIEW.edition + '" data-l21=');
      out.push(html);
    });
    if (!sep && zm.zones.length) out.push(now());
    const sb = pbBundle(r, PS, x => x.scale === PB.scale);
    if (sb) for (const cat of sb.estimates[0].categories) out.push('<div class="p21-link dim" data-bundle="' + sb.id + '" data-edition="' + REVIEW.edition + '" title="' + esc(sb.claim.statement_ru) + '">' + prow(lbl(PS, cat.category), pct(100 * cat.count / N)) + '</div>');
    out.push('<div class="p21-note">' + lbl(PZ, 'note') + '</div>');
    out.push(pbTodayHtml(r, F));
    return out.join('');
  }
  function pbTodayHtml(r, F) {
    const T = r.proof.today, s = PB.scale, u = v => sd(v / T.w), w = pbW(F);
    const done = T.episodes.filter(e => e.status === 'KNOWN' && e.kt >= s), wait = T.episodes.filter(e => e.status === 'NOT_YET' && e.kt >= s && e.L != null);
    const e1 = done.length ? done.reduce((a, b) => b.b_close > a.b_close ? b : a) : null, e2 = wait.length ? wait.reduce((a, b) => b.h_open > a.h_open ? b : a) : null;
    const s1 = e1 ? lbl(PT, 'today_done', { n: done.length, bot: w.bot, top: w.top, l: u(e1.L), lt: clk(e1.l_open), h: u(e1.h), bt: clk(e1.b_close) }) : lbl(PT, 'today_none');
    const s2 = e2 ? lbl(PT, 'today_wait', { top: w.top, bot: w.bot, h: u(e2.h), ht: clk(e2.h_open), l: u(e2.L), lt: clk(e2.l_open) }) : '';
    return '<div class="p21-h second"><span title="' + esc(lbl(PT, 'k', { act: clk(T.act) })) + '">' + lbl(PT, 'today_head', { scale: s }) + '</span></div><div class="p21-note">' + esc(s1) + '</div>' + (s2 ? '<div class="p21-note">' + esc(s2) + '</div>' : '');
  }
  function pbInspector(ctx, h) {
    const r = pbPacket(ctx);
    if (!r) return '<div class="ih">' + lbl(PZ, 'head') + '</div><div class="is">' + esc(pbStatus(ctx)) + '</div>';
    const p = r.proof, N = p.context.N, G = pbGeom(ctx, r), F = ctx.F;
    if(h?.k==='pbunk')return pbUnknownHtml(ctx);
    if (h && (h.k === 'pbpcell' || h.k === 'pbtcell' || h.k === 'pbarea')) return pbRegionInspector(ctx, h);
    if (h && h.k === 'pbzone') {
      const z = p.maps[String(PB.scale)].zones[h.i];
      if (!z) return '';
      const wd = pbRelWords(pbRel(r, h.i), F), ww = pbW(F);
      return '<div class="ih">' + lbl(PZ, 'zone_head', { label: pbDisplayLabel(z), window: pbWin(z), band: band(z.price_low, z.price_high) }) + '</div>' +
        '<div class="is"><b class="big">' + pbShare(z, N) + '</b> ' + lbl(PZ, 'zone_share', { yes: z.n_known, N, topg: ww.topg }) + '</div>' +
        (z.n_possible ? '<div class="is">' + lbl(PZ, 'zone_unknown', { unknown: z.n_possible }) + '</div>' : '') +
        '<div class="is">' + lbl(PZ, 'zone_more', { episodes: z.n_episodes, points: z.n_points, scale: PB.scale }) + '</div>' +
        '<div class="is">' + lbl(PT, 'row') + ': ' + esc(wd.clock) + ' · ' + esc(wd.visit) + ' · ' + esc(wd.completion) + '</div>' +
        '<div class="is k">' + lbl(PZ, 'zone_click') + '</div>';
    }
    if (h && h.k === 'pbpt') {
      const pt = G.P.get(h.id);
      if (!pt) return '';
      const w = G.W.get(pt.case), u = v => sd(v / w.w), episodes = pbLinks(pt, G.E), ww = pbW(F);
      const lines = ['<b>' + lbl(PE, 'head', { date: w.date.split('-').reverse().join('.') }) + '</b>' + (h.same > 1 ? ' <span class="k">' + lbl(PE, 'same', { n: h.same - 1 }) + '</span>' : '')];
      lines.push(lbl(PE, 'L', { bot: ww.bot, sd: u(pt.v), t: clk(pt.open) + '–' + clk(pt.open + 5) }));
      for (const e of episodes) {
        lines.push('<span class="k" data-pb-episode="' + esc(e.id) + '">' + lbl(PE, 'H', { top: ww.top, sd: u(e.h), t: clk(e.h_open) + '–' + clk(e.h_open + 5) }) + '</span>');
        lines.push(lbl(PE, 'B', { topg: ww.topg, t: clk(e.b_close - 5) + '–' + clk(e.b_close), c: clk(e.b_close) }) + ' · <span class="k">' + lbl(PE, 'gap', { m: e.b_close - pt.open - 5 }) + '</span>');
        lines.push('<span data-pb-dr-for="' + esc(e.id) + '">' + lbl(PE, 'dr_' + e.dr, { t: w.brk != null ? clk(w.brk) : '' }) + '</span>');
      }
      if (episodes.length > 1) lines.push('<span class="k">' + lbl(PE, 'links', { n: episodes.length, topgp: ww.topgp }) + '</span>');
      lines.push('<span class="k">' + lbl(PE, 'scale', { top: ww.top, k: pt.kt }) + '</span>');
      lines.push('<span class="k">' + lbl(PE, 'now', { t: clk(sliceOf(ctx)) }) + '</span>');
      return lines.join('<br>');
    }
    return '<div class="ih">' + lbl(PZ, 'head') + ' · ' + lbl(PZ, 'scale') + ' ' + PB.scale + '</div><div class="is">' + esc(F ? F.cond : '') + '</div><div class="is k">' + lbl(PZ, 'note') + '</div>';
  }
  // window 1: a constellation's sessions (each with its bottom and its update), or every episode of one session
  function pbDetail(ctx, o) {
    const r = pbPacket(ctx);
    if (!r) return { head: lbl(PZ, 'head'), body: '<div class="p21-note">' + esc(pbStatus(ctx)) + '</div>' };
    const p = r.proof, N = p.context.N, G = pbGeom(ctx, r);
    if(o?.k==='pbunk')return {head:'Не распределено по координатам',body:pbUnknownHtml(ctx)};
    if (o && ['pbpcell','pbtcell','pbarea'].includes(o.k)) return {head:'L · откаты до обновления',body:pbRegionInspector(ctx,o)};
    if (o && o.k === 'pbzone' && p.maps[String(PB.scale)].zones[o.i]) {
      const z = p.maps[String(PB.scale)].zones[o.i], cells = new Set(z.cell_mask.map(c => c[0] + '|' + c[1])), first = new Map();
      for (const q of p.points) if (q.kt >= PB.scale && cells.has(q.k + '|' + q.b) && !first.has(q.case)) first.set(q.case, q);
      const rows = z.members.map(id => { const q = first.get(id), e = pbLinks(q, G.E)[0]; return '<div class="pbep pbrow" data-pbpt="' + esc(q.id) + '"><span>' + esc(pbDate(id)) + '</span><b>L ' + clk(q.open) + ' · B ' + clk(e.b_close) + '</b></div>'; }).join('');
      return { head: lbl(PZ, 'win_head', { label: pbDisplayLabel(z) }), body: dRow(lbl(PZ, 'win_share'), pbShare(z, N)) + dRow(lbl(PZ, 'win_window'), pbWin(z) + ' · ' + band(z.price_low, z.price_high) + ' SD') +
        '<div class="p21-note">' + lbl(PZ, 'win_cells', { n: z.cell_mask.length }) + ' · ' + lbl(PZ, 'win_apex', { d: z.apex_D }) + '</div>' +
        '<div class="pblist"><div class="pbep k"><span>' + lbl(PZ, 'win_members') + '</span></div>' + rows +
        (z.possible.length ? '<div class="pbep k"><span>' + lbl(PZ, 'win_possible') + '</span></div><div class="p21-note">' + z.possible.map(id => esc(pbDate(id))).join(', ') + '</div>' : '') + '</div>' };
    }
    if (o && o.k === 'pbpt' && G.P.get(o.id)) {
      const pt = G.P.get(o.id), w = G.W.get(pt.case), u = v => sd(v / w.w), mine = new Set(pbLinks(pt, G.E).map(e => e.id));
      const dr = w.oppv == null ? lbl(PE, 'dr_NA') : w.brk != null ? lbl(PE, 'dr_broken', { t: clk(w.brk) }) : w.brk_known ? lbl(PE, 'dr_held', { end: clk(p.context.end) }) : lbl(PE, 'dr_unknown');
      const rows = p.episodes.filter(e => e.case === pt.case && e.kt >= PB.scale).map(e => '<div class="pbep' + (mine.has(e.id) ? ' on' : '') + '" title="' + esc('H ' + u(e.h) + (e.status === 'KNOWN' ? ' · L ' + u(e.L) : '') + ' SD') + '"><span>' +
        clk(e.h_open) + (e.status === 'KNOWN' ? ' → ' + clk(e.l_open) : '') + (e.b_close != null ? ' → ' + clk(e.b_close) : '') + '</span><b>' + lbl(PE, e.status) + ' · ' + lbl(PE, 'win_scale', { k: e.kt }) + '</b></div>').join('');
      return { head: lbl(PE, 'win_head', { date: w.date.split('-').reverse().join('.') }), body: '<div class="p21-note">' + lbl(PE, 'win_act', { t: clk(w.act), dr }) + '</div><div class="pblist"><div class="pbep k"><span>' + lbl(PE, 'win_cols') + '</span></div>' + rows + '</div>' };
    }
    return { head: lbl(PZ, 'head'), body: '<div class="p21-note">' + esc(lbl(PZ, 'head_title')) + '</div><div class="p21-note">' + esc(lbl(PZ, 'scale_title', { k: PB.scale })) + '</div>' + dRow('выпуск', r.release_id.slice(0, 12)) };
  }
  // window 2: the same episodes at every scale (the review: compare scales, the episodes keep their identity)
  function pbScalesHtml(r) {
    const p = r.proof, N = p.context.N;
    return '<div class="pblist">' + PB_SCALES.map(k => {
      const zm = p.maps[String(k)], top = zm.zones.reduce((a, z) => !a || z.n_known > a.n_known ? z : a, null), c = zm.sessions;
      return '<div class="pbsc' + (k === PB.scale ? ' on' : '') + '" data-pbscale="' + k + '">' + dRow(lbl(PS, 'scale_row', { k }), top ? top.label + ' ' + pbShare(top, N) : '—') +
        '<div class="p21-note">' + lbl(PS, 'scale_note', { n: zm.zones.length, in: pct(100 * c.IN_ZONES / N), unk: pct(100 * c.UNKNOWN / N), e: zm.episodes }) + '</div></div>';
    }).join('') + '</div>';
  }
  // window 3: the bottoms of this scale by cell (0,1 SD × 15 min, sessions per cell), the constellations outlined
  function pbHeat(id, ctx, r) {
    const K = cardCanvas(id);
    if (!K) return;
    const { c, W, H } = K, p = r.proof, F = ctx.F, s = PB.scale, L = 30, T = 4, B = 16, Rm = 4, cnt = new Map();
    for (const q of p.points) if (q.kt >= s) { const key = q.k + '|' + q.b; if (!cnt.has(key)) cnt.set(key, new Set()); cnt.get(key).add(q.case); }
    if (!cnt.size) return;
    const ks = [...cnt.keys()].map(k => +k.split('|')[0]).sort((a, b) => a - b);
    const k0 = ks[Math.floor(0.03 * (ks.length - 1))], k1 = ks[Math.ceil(0.97 * (ks.length - 1))] + 1, mx = Math.max(...[...cnt.values()].map(v => v.size));
    const cw = (W - L - Rm) / F.nb, rh = (H - T - B) / Math.max(1, k1 - k0), X = b => L + b * cw, Y = k => T + (k1 - 1 - k) * rh;
    for (const [key, set] of cnt) { const [k, b] = key.split('|').map(Number); if (k < k0 || k >= k1) continue; c.fillStyle = rgba(PBC, 0.18 + 0.82 * Math.pow(set.size / mx, 0.7)); c.fillRect(X(b) + 0.5, Y(k) + 0.25, Math.max(1, cw - 1), Math.max(1, rh - 0.5)); }
    for (const z of p.maps[String(s)].zones) {
      const set = new Set(z.cell_mask.map(([k, b]) => k + '|' + b));
      c.strokeStyle = rgba(PBC, 0.95); c.lineWidth = 1; c.beginPath();
      for (const [k, b] of z.cell_mask) {
        if (k < k0 || k >= k1) continue;
        const x0 = X(b), x1 = X(b + 1), y0 = Y(k), y1 = Y(k) + rh;
        if (!set.has((k + 1) + '|' + b)) { c.moveTo(x0, y0); c.lineTo(x1, y0); }
        if (!set.has((k - 1) + '|' + b)) { c.moveTo(x0, y1); c.lineTo(x1, y1); }
        if (!set.has(k + '|' + (b - 1))) { c.moveTo(x0, y0); c.lineTo(x0, y1); }
        if (!set.has(k + '|' + (b + 1))) { c.moveTo(x1, y0); c.lineTo(x1, y1); }
      }
      c.stroke();
    }
    const xs = X((sliceOf(ctx) - F.f) / 15);
    if (xs > L && xs < W - Rm) { c.strokeStyle = 'rgba(209,212,220,.5)'; c.setLineDash([3, 3]); c.beginPath(); c.moveTo(xs, T); c.lineTo(xs, H - B); c.stroke(); c.setLineDash([]); }
    c.font = '10px ' + FONT; c.fillStyle = C.text3; c.textBaseline = 'middle'; c.textAlign = 'right';
    c.fillText(sd(k1 / 10), L - 4, T + 4); c.fillText(sd(k0 / 10), L - 4, H - B - 4);
    c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText(clk(F.f), L, H - B + 3); c.textAlign = 'right'; c.fillText(clk(F.end), W - Rm, H - B + 3); c.textAlign = 'left';
  }
  // the «↺» frame: the candles, the box and the constellations whose window has not passed (as the accepted view does)
  function pbRange(ctx, lo, hi) {
    const r = pbPacket(ctx), F = ctx.F;
    if (!r || !F) return [lo, hi];
    r.proof.maps[String(PB.scale)].zones.forEach((z, i) => {
      if (pbRel(r, i).clock === 'PAST') return;
      const a = F.u2p(z.price_low / 10), b = F.u2p(z.price_high / 10); lo = Math.min(lo, a, b); hi = Math.max(hi, a, b);
    });
    return [lo, hi];
  }
  // the toolbar keeps its accepted width (SWPC-1.1 W01: the cut is never hidden): the view's own button stands only while the
  // view is open (the area button gives way to it); it is entered from its row in the panel or by switching the trial on
  function pbToolbar(F) {
    const b=dom('mode').querySelector('[data-m="pullbacks"]');if(b)b.hidden=true;
    dom('areab').hidden=false;
    if(pullbackMode()){const role=dom('ev').querySelector('.evc');if(role)role.title=lbl(PZ,'head_title');}
  }
  root.addEventListener('click', e => {
    const b = e.target.closest('[data-pbscale]');
    if (!b || !pullbackMode()) return;
    PB.scale = +b.dataset.pbscale; PB.cl = null; st.pin = st.hover = null;
    try { localStorage.setItem(PB_KEY, String(PB.scale)); } catch (x) { /* not kept */ }
    dom('detg')._k = ''; render(true);
  });
  det.addEventListener('mouseover', e => { const el = e.target.closest('[data-pbpt]'); if (!el || !pullbackMode()) return; st.hover = { k: 'pbpt', id: el.dataset.pbpt, same: 1 }; st.fromDet = true; redraw(); });
  // windows 2 and 3 of the six (panel.js::details): the scales and the bottoms by cell; false = not this view
  function pbCards(g, ctx) {
    const pr = pullbackMode() && pbPacket(ctx);
    if (!pr) return false;
    const cards = g.querySelectorAll('.dcard');
    cards[1].innerHTML = '<div class="dt" style="color:'+cfg.R+'">'+ctx.F.names.R+' R · цена × время</div><canvas id="dcL"></canvas>';
    pbHeat('dcL', ctx, pr);
    drawHeat('dcX',ctx.F,ctx,'X');
    return true;
  }
  // the entry from the accepted view: one row of the candidates' place in the panel (integration.js::candidatePanel)
  function pbEntry() { return ''; }

  // A typed drawing adapter, never a replacement of the accepted family. R is only the existing amber layout slot.
  // Its data/passports are PB-L; X stays FINAL-X. BASE/NOW, order and level questions retain the original F.
  function pbMapContext(ctx) {
    if (!pullbackMode() || !ctx.F) return ctx;
    requestPullbacks(ctx);
    const r=pbPacket(ctx), F=ctx.F, key=r && r.release_id+'|'+PB.scale;
    if (PB.model?.key===key && PB.model.base===F) return {...ctx,F:PB.model.F};
    const W=new Map((r?.proof.sessions||[]).map(w=>[w.id,w])), mi=new Map(F.M.map((m,i)=>[m.id,i]));
    const pts=(r?.proof.points||[]).filter(q=>q.kt>=PB.scale).map(q=>({ev:'R',i:mi.get(q.case),m:F.M[mi.get(q.case)],pbid:q.id,t:q.open,k:q.k,b:q.b,p:F.u2p(q.v/W.get(q.case).w)}));
    const count=axis=>{const m=new Map();for(const q of pts){if(!m.has(q[axis]))m.set(q[axis],new Set());m.get(q[axis]).add(q.m.id);}return new Map([...m].map(([k,v])=>[k,v.size]));};
    const zm=r?.proof.maps[String(PB.scale)], zones=(zm?.zones||[]).map(z=>({...z,label:z.label.replace(/^L/,'R'),event_id:'R',n_zone:z.n_known,p_snapshot:z.n_known/F.N}));
    const zcell=new Map();zones.forEach((z,i)=>z.cell_mask.forEach(([k,b])=>zcell.set(k+'|'+b,i)));
    const cells=new Map();for(const q of pts){const key=q.k+'|'+q.b;if(!cells.has(key))cells.set(key,{k:q.k,b:q.b,list:[]});const ids=cells.get(key).list;if(!ids.includes(q.i))ids.push(q.i);}
    const D={event_id:'PB_L',pts,cells,P:count('k'),T:count('b'),known:new Set(pts.map(q=>q.m.id)).size,unknown:zm?.sessions.UNKNOWN||0,none:zm?.sessions.NONE||0};
    const view={...F,_pb:r||{loading:true},_cl:null,ev:{...F.ev,R:D},zones:{...F.zones,R:{zones,unknown_count:0,no_event_count:0}},zcell:{...F.zcell,R:zcell},names:{...F.names},what:{...F.what,R:'Дна локальных откатов до обновления'}};
    PB.model={key,base:F,F:view};
    return {...ctx,F:view};
  }
  // Draw the WHOLE published zone, not just the anchor's 3x3 neighbourhood. The anchor names the zone; it is not its mask.
  // One actual witness per occupied M5 x 0.1-IDR cell removes coincident stars without deleting a zone's other lobes.
  // The representative is an observed bottom nearest the cell's mean, never an invented price/time coordinate.
  function pbCloudContext(ctx) {
    const F=ctx.F;
    if(!F?._pb?.proof)return ctx;
    if(PB.model.cloud)return {...ctx,F:PB.model.cloud};
    const points=[];
    F.zones.R.zones.forEach(z=>{
      const cells=new Set(z.cell_mask.map(c=>c.join('|'))),groups=new Map();
      for(const q of F.ev.R.pts){
        if(!cells.has(q.k+'|'+q.b))continue;
        const key=q.k+'|'+q.t;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(q);
      }
      for(const qs of groups.values()){
        const mean=qs.reduce((n,q)=>n+q.p,0)/qs.length;
        const q=qs.slice().sort((a,b)=>Math.abs(a.p-mean)-Math.abs(b.p-mean)||a.pbid.localeCompare(b.pbid))[0];
        points.push(q);
      }
    });
    PB.model.cloud={...F,_cl:null,ev:{...F.ev,R:{...F.ev.R,pts:points}}};
    return {...ctx,F:PB.model.cloud};
  }
  function pbProjectionContext(ctx) {
    const F=ctx.F;
    if(!F?._pb?.proof)return ctx;
    const last=new Map();
    for(const q of F.ev.R.pts){const k=q.m.id+'|'+q.k,old=last.get(k);if(!old||q.t>old.t)last.set(k,q);}
    // A case is earlier only when ALL its established bottoms in this price band are past the cut.
    return {...ctx,F:{...F,ev:{...F.ev,R:{...F.ev.R,pts:[...last.values()]}}}};
  }
  // The time hill describes all of a zone's history, not the compact on-chart glyphs.
  // One case contributes at most one Gaussian vote at any clock time, however many local cycles it has there.
  function pbBandHills(F) {
    if(PB.model?.F===F && PB.model.hills)return PB.model.hills;
    const hills=F.zones.R.zones.map((z,i)=>{
      const cells=new Set(z.cell_mask.map(([k,b])=>k+'|'+b)),byCase=new Map();
      for(const q of F.ev.R.pts)if(cells.has(q.k+'|'+q.b)){
        if(!byCase.has(q.m.id))byCase.set(q.m.id,new Set());byCase.get(q.m.id).add(q.t+2.5);
      }
      const all=[...byCase.values()].flatMap(s=>[...s]);if(!all.length)return null;
      const sig=7,t0=Math.min(...all)-3*sig,t1=Math.max(...all)+3*sig,pts=[];
      let pk=0,pkT=t0;
      for(let t=t0;t<=t1+0.01;t+=1.5){
        let d=0;for(const times of byCase.values()){let best=0;for(const u of times)best=Math.max(best,Math.exp(-((t-u)*(t-u))/(2*sig*sig)));d+=best;}
        pts.push([t,d]);if(d>pk){pk=d;pkT=t;}
      }
      const bs=z.cell_mask.map(c=>c[1]);
      return {z,i,pts,pk,pkT,b0:Math.min(...bs),b1:Math.max(...bs)+1,cases:byCase.size};
    });
    if(PB.model?.F===F)PB.model.hills=hills;
    return hills;
  }
  function pbVisualHover(h) {
    if (!h) return h;
    if (h.k==='pbzone') return {...h,k:'zone',ev:'R'};
    if (h.k==='pbpcell') return {...h,k:'pcell',ev:'R'};
    if (h.k==='pbtcell') return {...h,k:'tcell'};
    if (h.k==='pbarea') return {...h,k:'area'};
    if (h.k==='pbpt') {const q=PB.model?.F.ev.R.pts.find(q=>q.pbid===h.id);return q?{...h,k:'pt',ev:'R',i:q.i,q}:h;}
    return h;
  }
  function pbSemanticHit(h) {
    if (!pullbackMode() || !h) return h;
    if (h.k==='zone'&&h.ev==='R') return {...h,k:'pbzone'};
    if (h.k==='pcell'&&h.ev==='R') return {...h,k:'pbpcell'};
    if (h.k==='tcell') return {...h,k:'pbtcell'};
    if (h.k==='unk') return {...h,k:'pbunk'};
    if (h.k==='area'&&st.area?.ev!=='X') return {...h,k:'pbarea'};
    if (h.k==='pt'&&h.q?.pbid) return {k:'pbpt',id:h.q.pbid,same:new Set(h.same).size,ev:'R'};
    return h;
  }
  function pbRegion(r, bounds, time) {
    if(!r?.proof)return null;
    const f=r.proof.context.formed,b0=time?(time[0]-f)/15:null,b1=time?(time[1]-f)/15:null;
    const k0=Number.isFinite(bounds?.[0])?bounds[0]:null,k1=Number.isFinite(bounds?.[1])?bounds[1]:null;
    return r.proof.marginals[String(PB.scale)].find(v=>v.k0===k0&&v.k1===k1&&v.b0===b0&&v.b1===b1)||null;
  }
  function pbPassport(r, est, values, pred) {
    const b=r?.proof&&pbBundle(r,est,pred), v=b?.estimates.find(e=>e.value_kind==='POINT'), bd=b?.estimates.find(e=>e.value_kind==='BOUNDS');
    return {candidate:true,estimand:est,event_id:'PB_L',pct:v?100*v.value:null,pctHi:bd?100*bd.upper:null,
      yes_count:v?.numerator||0,unknown_count:values?.n_possible||0,N:r?.proof?.context.N||0,phrase:b?.claim.statement_ru||'Число ещё не опубликовано',horizon:'после собственной активации до конца блока',bundle:b};
  }
  function pbRegionPass(F,bounds,time,outframe) {
    const r=F._pb;
    let v=pbRegion(r,bounds,time);
    // The off-frame mass is a UNION of sessions, never a sum of overlapping price bins.
    if(!v&&outframe&&r?.proof){
      const ks=r.proof.points.filter(p=>p.kt>=PB.scale).map(p=>p.k);
      if(bounds[0]<=Math.min(...ks))v=pbRegion(r,[null,bounds[1]],null);
      else if(bounds[1]>Math.max(...ks))v=pbRegion(r,[bounds[0],null],null);
    }
    return pbPassport(r,'EST:PB-REGION',v,p=>p.scale===PB.scale&&v&&['k0','k1','b0','b1'].every(k=>p[k]===v[k]));
  }
  function pbZonePass(F,z) {return pbPassport(F._pb,PZ,z,p=>p.scale===PB.scale&&p.zone_id===z.zone_id);}
  function pbUnknownHtml(ctx) {
    const r=pbPacket(ctx),F=ctx.F;if(!r||!F)return '<div class="is">'+esc(pbStatus(ctx))+'</div>';
    const b=pbBundle(r,PS,p=>p.scale===PB.scale);
    let out='<div class="ih">Не распределено по координатам</div>';
    if(b)for(const c of b.estimates[0].categories.filter(c=>c.category==='UNKNOWN'||c.category==='NONE'))out+='<div class="is" data-pb-category="'+c.category+'">R · '+lbl(PS,c.category)+' · '+pct(100*c.count/F.N)+'</div>';
    const x=undPass(F,'X','BOTH');
    return out+'<div class="is">X · не определено / нет периода · '+ppTxt(x)+'</div>';
  }
  function pbRegionInspector(ctx,h) {
    const r=pbPacket(ctx),F=pbMapContext(ctx).F,a=h.k==='pbarea'?st.area:h;
    const bounds=a?.k0!=null?[a.k0,a.k1]:null,time=a?.b0!=null?[F.f+15*a.b0,F.f+15*a.b1]:null,v=pbRegion(r,bounds,time),p=pbRegionPass(F,bounds,time);
    const title=(bounds?band(...bounds)+' SD':'')+(bounds&&time?' · ':'')+(time?clk(time[0])+'–'+clk(time[1]):'');
    const clock=v?'<div class="is">'+v.earlier+' сессий: все установленные дна здесь уже позади по часам; '+v.later+' — есть дно позже среза</div>':'';
    let html='<div class="ih">R · откаты до обновления · '+title+'</div><div class="is"><b class="big">'+ppTxt(p)+'</b></div><div class="is">'+esc(p.phrase)+'</div>'+clock;
    if(h.k==='pbtcell'||h.k==='pbpcell'||h.k==='pcell'){
      const n=areaCount(ctx.F,'X',{k0:bounds?.[0]??-Infinity,k1:bounds?.[1]??Infinity,b0:h.b0,b1:h.b1}),x=evPass(ctx.F,'X','price_time',bounds,time,n);
      html+='<div class="is" style="color:'+cfg.X+'">X · конечное продолжение · '+ppTxt(x)+'</div>';
    }
    return html+'<div class="is k">R — любой завершённый локальный откат, X — единственный конечный экстремум. Одна сессия может дать R в нескольких окнах; это не доли двух противоположных исходов.</div>';
  }
  function pbJointXTip(ctx,h) {
    const F=ctx.F,z=F.zones.X?.zones[h.i];
    if(!z)return '';
    const p=zonePass(F,'X',z),s=zoneStatus(F,ctx,'X')[h.i],time=[z.time_start,z.time_end],mc=pbMapContext(ctx).F,l=pbRegionPass(mc,null,time);
    return '<div class="ih" style="color:'+cfg.X+'">'+z.label+' · конечное продолжение X · '+pbWin(z)+'</div><div class="is">'+band(z.price_low,z.price_high)+' SD</div><div class="ibig">'+ppTxt(p)+'</div><div class="is">'+esc(p.phrase)+'</div>'+winLine(F,ctx,'X',s,...time,zoneClock(F,ctx,'X')[h.i])+'<div class="is" style="color:'+cfg.R+'">R · хотя бы один откат в этом окне времени: '+ppTxt(l)+'</div>';
  }
  function pbAreaHtml(ctx) {
    const F=pbMapContext(ctx).F,a=st.area,bb=isFinite(a.k0)?[a.k0,a.k1]:null,tt=a.b0!=null?[F.f+15*a.b0,F.f+15*a.b1]:null,p=pbRegionPass(F,bb,tt);
    const name=(bb?band(...bb)+' SD':'')+(bb&&tt?' · ':'')+(tt?clk(tt[0])+'–'+clk(tt[1]):'');
    let row=link({k:'pbarea',part:'band'},prow('<i style="color:'+cfg.R+'">R</i> откаты в области',ppTxt(p)), '',null,p.phrase);
    if(p.bundle)row=row.replace('data-l21=','data-bundle="'+p.bundle.id+'" data-edition="'+REVIEW.edition+'" data-l21=');
    return '<div class="p21-h second p24-sel">Выбранная область <span><button class="p24-x" data-clear="area" title="Снять выбор (Esc)">✕</button></span></div><div class="p21-note"><b style="color:#D1D4DC;font-weight:600">'+esc(name)+'</b></div>'+row;
  }
  function pbCombinedZones(ctx) {
    requestPullbacks(ctx);
    const F=ctx.F,r=pbPacket(ctx),out=['<div class="p21-h second"><span>Зоны по времени</span>'+scopeSwitch()+'</div>'];
    out.push('<a data-compare24="1" href="'+esc(compare24Href(ctx))+'" target="_blank" rel="noopener" hidden>№24 ↗</a>');
    if(!r)out.push('<div class="p21-note">R · '+esc(pbStatus(ctx))+'</div>');
    const rows=(r?r.proof.maps[String(PB.scale)].zones.map((z,i)=>({ev:'L',z,i})):[]).concat((F.zones.X?.zones||[]).map((z,i)=>({ev:'X',z,i})));
    rows.sort((a,b)=>a.z.time_start-b.z.time_start||b.z.p_snapshot-a.z.p_snapshot);
    let sep=false;const sl=sliceOf(ctx);
    for(const {ev,z,i} of rows){
      if(!sep&&z.time_end>sl){sep=true;out.push('<div class="p24-now"><span></span>сейчас '+clk(sl)+'<span></span></div>');}
      if(ev==='L'){
        const b=pbBundle(r,PZ,p=>p.scale===PB.scale&&p.zone_id===z.zone_id),wd=pbRelWords(pbRel(r,i),F);
        let row=link({k:'pbzone',i,ev:'R'},'<span class="t"><span><span class="zt">'+pbWin(z)+'</span> <i class="zn" style="color:'+cfg.R+'">'+pbDisplayLabel(z)+'</i></span><span class="p21-sub">'+band(z.price_low,z.price_high)+' SD · '+esc(wd.clock)+'</span></span><b class="zp">'+(b?pbShare(z,F.N):'—')+'</b>','mc',null,b?.claim.statement_ru||'');
        if(b)row=row.replace('data-l21=','data-bundle="'+b.id+'" data-edition="'+REVIEW.edition+'" data-l21=');out.push(row);
      }else{
        const p=zonePass(F,'X',z),status=zoneStatus(F,ctx,'X')[i],paint=zonePaint(F,ctx,'X',z,status);
        out.push(link({k:'zone',ev:'X',i},'<span class="t"><span><span class="zt">'+pbWin(z)+'</span> <i class="zn" style="color:'+cfg.X+'">'+pbDisplayLabel(z)+'</i></span><span class="p21-sub">'+lbl('EST:B-ZONE-X','sub',{band:band(z.price_low,z.price_high),status:zstOf(F,ctx,z,status)})+'</span></span><b class="zp" style="color:'+paint.text+'">'+ppTxt(p)+'</b>','mc zst-'+status,p,plainTitle(p)));
      }
    }
    if(r){
      const sb=pbBundle(r,PS,p=>p.scale===PB.scale);
      if(sb)for(const c of sb.estimates[0].categories)out.push('<div class="p21-link dim" data-bundle="'+sb.id+'" data-edition="'+REVIEW.edition+'">'+prow('<i style="color:'+cfg.R+'">R</i> '+lbl(PS,c.category),pct(100*c.count/F.N))+'</div>');
      out.push('<div class="p21-note">R · '+lbl(PZ,'note')+'</div>');
    }
    if(F.zones.X){const p=resPass(F,'X');out.push(link({k:'evrow',ev:'X'},prow(lbl('EST:B-ZONE-RESIDUAL-X','row',{ev:'<i style="color:'+cfg.X+'">X</i>'}),ppTxt(p)),'dim',p,plainTitle(p)));}
    if(F.ev.X.unknown+F.ev.X.none){const p=undPass(F,'X','BOTH');out.push(link({k:'evrow',ev:'X'},prow(lbl(p.estimand,'row',{ev:'X'}),ppTxt(p)),'dim',p,plainTitle(p)));}
    return out.join('');
  }
