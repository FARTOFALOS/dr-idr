  // ---------- the right panel: design 22's place and manner (percentages only, every line a link to the chart) ----------
  // What it holds (spec §10.3): the family and its slice; the chosen event and its unknown mass; the DR outcome of the
  // family (one 100 %); the selected area; the pinned level; the pinned history session. In «Путь семьи»: the family's
  // closes on one M5. No list of «best» places, no targets, no session counts.
  function link(h, html, cls, p, title) {
    const i = P24.links.push(h) - 1;
    return '<div class="p21-link' + (cls ? ' ' + cls : '') + '" data-l21="' + i + '"' + (p ? ' data-pp="' + p.id + '"' : '') + (title ? ' title="' + esc(title) + '"' : '') + '>' + html + '</div>';
  }
  const prow = (text, val) => '<span class="t">' + text + '</span><b>' + val + '</b>';
  const plainTitle = p => (p.phrase + ' · ' + p.horizon + (p.unknown_count ? lbl('FF:PASSPORT-VIEW', 'title_unknown', { pct: pct(100 * p.unknown_count / p.N) }) : '')).replace(/<[^>]+>/g, '');
  // DR-LAB-SC-1.1: a violation of the contract of this scene stands at the top of the panel (all of them in its title);
  // one found on another day, family or cut does not (DR-LAB-SWPC-1.1 M16)
  const scNotice = ctx => { const v = kNow(ctx); return !v.length ? '' : '<div class="p24-sc" title="' + esc(v.join('\n')) + '">Контракт SC-1.1: ' + esc(v[v.length - 1]) + (v.length > 1 ? ' · ещё ' + (v.length - 1) : '') + '</div>'; };
  function statusMsg(ctx) {
    const s = ctx.s, x = A.day;
    if (!x || x.status !== 'ok') return (x && x.message) || (A.src === 'hist' ? 'Загружаю день истории…' : 'Загружаю свечи…');
    if (s.status === 'before') return 'Сессия ещё не началась';
    if (s.status === 'forming') return 'Коробка формируется: семьи ещё нет';
    if (s.status === 'waiting') return 'Подтверждения нет: семьи ещё нет';
    if (s.status === 'noconf') return 'Сессия закончилась без подтверждения';
    const r = A.fams.get(famKey(ctx.D, s, wantView(s)));
    if (!r) return 'Собираю семью…';
    if (r.status === 'ok' && r._refused) return 'Числа не публикуются: ' + r._refused;
    if (r.status === 'ok' && !r.N) return 'В семье нет сессий: процентов нет';
    if (/^contract_/.test(r.status || '')) return r.message || 'нарушение контракта SC-1.1: числа не публикуются';
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
      // before the confirmation: the block of the profile PRE-24 under the status line (operator 2026-10-08)
      const pre = !F && s.status === 'waiting' && A.day && A.day.status === 'ok' ? preHtml(ctx) : '';
      panel.innerHTML = scNotice(ctx) + '<div class="p21-empty">' + esc(F && !F.N ? 'В семье нет сессий: процентов нет' : statusMsg(ctx)) + '</div>' + pre +
        (F && !F.N ? '<div class="p21-note">' + esc(F.cond) + '</div>' : '') + (s.failed && s.conf ? viewSwitch(s) : '') +
        (noFam ? '<button class="p24-btn" data-hist="1">' + (A.src === 'live' ? 'Открыть ' + st.session + ' на истории' : 'Ближайший день с подтверждением ' + st.session) + '</button>' : '');
      return;
    }
    const out = [], sl = sliceOf(ctx), step = 100 / F.N, src = F.r.source || {};
    const ttl = lbl('FF:SHARE-STEP', 'head_title', { event: lbl('FF:PASSPORT-VIEW', 'at_act_dr', null, VW(F)), t: clk(F.act0), step: pct(step), history: src.history || '2006–2025',
      cutoff: F.r.key.cutoff, snapshot: F.r.snapshot_id, family: F.r.family_id, semantics: F.r.semantics });
    out.push('<div class="p21-h"><span title="' + esc(ttl) + '">' + (F.brk ? 'Семья слома' : 'Семья') + ' · ' + esc(F.cond) + '</span><span>' + (sl >= F.end ? 'блок закончен' : 'после ' + clk(sl)) + '</span></div>');
    if (s.failed) out.push(viewSwitch(s));
    // a small break family is shown as it is, marked (operator 2026-10-08: «честно писать «мало»», FF:FEW-SESSIONS)
    if (F.brk && F.N < FEW) out.push('<div class="p21-note" title="' + esc(lbl('FF:FEW-SESSIONS', 'title', { step: pct(step) })) + '"><b>' + lbl('FF:FEW-SESSIONS', 'few', { n: F.N }) + '</b></div>');
    if (F.out) out.push(outcomeHtml(F));
    out.push(phaseHtml(F, ctx));
    out.push(nowHtml(F, ctx));
    if (st.mode === 'bounds') {
      out.push(zonesHtml(F, ctx));
      const tf = todayFacts(F, ctx);
      if (tf) out.push('<div class="p21-note" title="' + esc(lbl('FF:TODAY-PREFIX', 'title', { act: lbl('FF:PASSPORT-VIEW', 'act_gen', null, VW(F)) })) + '">' + tf + '</div>');
    }
    if (st.mode === 'path') out.push(columnHtml(F, ctx));
    if (st.area && st.mode === 'bounds') out.push(areaHtml(F, ctx));
    const h = st.pin;
    if (h && h.k === 'lvl' && h.l) out.push(levelHtml(F, ctx, h.l));
    if (h && h.k === 'pt' && F.M[h.i]) out.push(memberHtml(F, F.M[h.i]));
    panel.innerHTML = scNotice(ctx) + out.join('');
    // a new selection (area, level, history session) stands at the end of the panel, under the inspector's edge: scroll
    // the panel to it once, when it appears (the layout stays; the panel keeps its own scroll otherwise)
    const sk = (st.area ? [st.area.k0, st.area.k1, st.area.b0, st.area.b1, st.area.ev].join(',') : '') + '|' + pinKey(st.pin);
    if (sk !== P24.selKey) { P24.selKey = sk; const el = panel.querySelector('.p24-sel'); if (el) panel.scrollTop = Math.min(panel.scrollHeight - panel.clientHeight, el.offsetTop - 8); }
    panelMarks();
  }
  // the zone map of the chosen event (zone-map-3): the family scope (weekday by default, all weekdays only by an explicit
  // click), every zone in the order of time with its share of the family and today's status, then the residual. No
  // counts of sessions; a share is never a chance for today.
  const scopeSwitch = () => '<span class="p24-seg sm"><button data-scope="weekday" class="' + (st.scope === 'weekday' ? 'on' : '') + '">день недели</button><button data-scope="all" class="' + (st.scope === 'all' ? 'on' : '') + '">все дни</button></span>';
  function zonesHtml(F, ctx) {
    const sl = sliceOf(ctx), rows = [];
    for (const ev of ['R', 'X']) {
      const Zm = zonesOf(F, ev);
      if (!Zm) continue;
      const S = zoneStatus(F, ctx, ev);
      Zm.zones.forEach((z, i) => rows.push({ ev, z, i, s: S[i] }));
    }
    if (!rows.length && !zonesOf(F, 'R') && !zonesOf(F, 'X')) return '';
    rows.sort((a, b) => a.z.time_start - b.z.time_start || b.z.p_snapshot - a.z.p_snapshot);
    const out = ['<div class="p21-h second">Зоны по времени' + scopeSwitch() + '</div>'];
    if (!rows.length) out.push('<div class="p21-note">' + lbl('EST:B-ZONE-R', 'none') + '</div>');
    let sep = false;
    for (const r of rows) {
      if (!sep && r.z.time_end > sl) { sep = true; out.push('<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>'); }
      // Historical mass controls its typography; today's status is encoded separately by zst-* opacity/style.
      const p = zonePass(F, r.ev, r.z), big = p.pct >= 15 ? ' big' : '';
      out.push(link({ k: 'zone', ev: r.ev, i: r.i }, '<span class="t"><span><span class="zt">' + clk(r.z.time_start) + '–' + clk(r.z.time_end) + '</span> <i class="zn" style="color:' + cfg[r.ev] + '">' + r.z.label + '</i></span>' +
        '<span class="p21-sub">' + lbl('EST:B-ZONE-' + r.ev, 'sub', { band: band(r.z.price_low, r.z.price_high), status: zst(r.s) }) + '</span></span><b class="zp' + big + '">' + ppTxt(p) + '</b>', 'mc zst-' + r.s, p, plainTitle(p)));
    }
    if (!sep) out.push('<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>');
    // the rest of each event's 100 %: outside the zones, and not determined (never drawn at any price)
    for (const ev of ['X', 'R']) {
      const Zm = zonesOf(F, ev), D = F.ev[ev];
      const tag = '<i style="color:' + cfg[ev] + '">' + ev + '</i>';
      if (Zm) { const r = resPass(F, ev); out.push(link({ k: 'evrow', ev }, prow(lbl('EST:B-ZONE-RESIDUAL-' + ev, 'row', { ev: tag }), ppTxt(r)), 'dim', r, plainTitle(r))); }
      if (D.unknown + D.none) { const u = undPass(F, ev, 'BOTH'); out.push(link({ k: 'evrow', ev }, prow(lbl('EST:B-RX-UNDETERMINED-' + ev, 'row', { ev: tag }), ppTxt(u)), 'dim', u, plainTitle(u))); }
    }
    return out.join('');
  }
  // today's own path after the activation (facts, not shares): the deepest and the farthest closed-M5 point so far
  function todayFacts(F, ctx) {
    const rows = todayRows(F, ctx);
    if (!rows.length) return '';
    let lo = rows[0], hi = rows[0];
    for (const q of rows) { if (q.lo < lo.lo) lo = q; if (q.hi > hi.hi) hi = q; }
    return lbl('FF:TODAY-PREFIX', 'line', { r: sd(lo.lo / F.w0t), rt: clk(lo.T - 5), x: sd(hi.hi / F.w0t), xt: clk(hi.T - 5) }, VW(F));
  }
  // DR-LAB-NOW-1.0 §21: the quiet block «Сейчас» — after the path lived today, how much movement usually remained ahead
  // for comparable states of this family (the time baseline unless a path matcher passed the walk-forward gates). Its
  // support is always shown; it never rewrites the base map; it is not a trade.
  const NOWST = { VALIDATED: 'путь проверен на истории', TIME_BASELINE: 'путь не добавил к базе по времени', NOT_VALIDATED: 'проверка на истории не прогнана',
    NOT_TESTABLE: 'семьи слома малы для проверки пути', UNSTABLE: 'путь неустойчив к порогу', CELL_FALLBACK: 'в этой связке путь хуже базы',
    NOT_VALIDATED_SCOPE: 'путь проверен только для дня недели', STALE: 'паспорт проверки устарел' };
  function nowHtml(F, ctx) {
    const n = nowOf(ctx), head = right => '<div class="p21-h second"><span title="DR-LAB-NOW-1.0: доли считаются заново на каждой закрытой M5 по уже прожитому сегодня пути; базовая карта и её проценты не меняются">Сейчас</span><span>' + right + '</span></div>';
    if (!n) return '<div class="p24-nowblk">' + head('считаю…') + '</div>';
    if (n.status !== 'OK' && n.status !== 'FROZEN_AT_BREAK') return '<div class="p24-nowblk">' + head('') + '<div class="p21-note">' + esc(n.note || n.message || 'нет данных') + '</div></div>';
    const what = F.brk ? 'после слома' : 'после подтверждения', out = [];
    const modes = ['R', 'X'].map(ev => n[ev] && n[ev].mode), path = modes.includes('PATH_CONDITIONED');
    out.push(head('<span title="' + (path ? 'похожий уже прожитый путь' : 'только время ' + what + ': все сессии семьи к этому же часу') + '">' + (path ? 'похожий путь' : 'по времени') + '</span>' + (n.status === 'FROZEN_AT_BREAK' ? ' · на ' : ' · ') + n.cut.cut_clock_et));
    if (n.status === 'FROZEN_AT_BREAK') out.push('<div class="p21-note">исходная семья: заморожено на последней M5 до слома DR</div>');
    for (const ev of ['R', 'X']) {
      const E = n[ev];
      if (E && !E.continuation && E.note) { out.push('<div class="p21-note"><i style="color:' + cfg[ev] + '">' + ev + '</i> ' + esc(E.note) + '</div>'); continue; }
      if (!E || !E.continuation) continue;
      // DR-LAB-SC-1.1 K33: a C1 share of the history, in historical grammar (CF:N-NEW, CF:N-IF-NEW, CF:N-TIME), shown only
      // with its bundle published by the server on this cut
      const C = E.continuation, p = C.p_new_extreme, b = C.p_new_bounds || [], sp = C.support, NE = 'EST:N-NEW-' + ev, bN = nowBundle(n, NE, 'MAIN', C);
      const val = !bN ? '—' : C.support.N_match_unknown ? pct(100 * b[0]) + '–' + pct(100 * b[1]) : p == null ? '—' : pct(100 * p);
      const name = lbl(NE, 'row', { ev: '<i style="color:' + cfg[ev] + '">' + ev + '</i>' }, VW(F));
      const sgn = ev === 'R' ? -1 : 1, u0 = ev === 'R' ? E.state.r_seen : E.state.x_seen, q = C.delta_if_new || {}, tm = C.time_to_new || {};
      const lv = v => num(Math.round(F.u2p(u0 + sgn * v)), 0);   // whole points: a level to watch, not a quote
      const bI = bN && q.q50 != null && p ? nowBundle(n, 'EST:N-IF-NEW-' + ev, 'MAIN') : null, bT = bI && tm.q50_min != null ? nowBundle(n, 'EST:N-TIME-' + ev, 'MAIN') : null;
      const sub = bI ? lbl('EST:N-IF-NEW-' + ev, 'sub', { p50: lv(q.q50), p25: lv(q.q25), p75: lv(q.q75) }) + (bT ? lbl('EST:N-TIME-' + ev, 'sub', { min: Math.round(tm.q50_min) }) : '') : '';
      const support = E.mode === 'PATH_CONDITIONED' ? lbl(NE, 'support_path', { m: sp.N_match_total, n: sp.N_eligible, matcher: E.matcher }) : lbl(NE, 'support_b0', { n: sp.N_eligible, N: n.base.N_base });
      // the pullback line (operator 2026-10-08, meaning/17 §7): only the number; its levels are the marks at the price
      // scale (drawNowMarks); the historical words, the conditional levels, the time and the support are in its title
      if (ev === 'R') {
        const P = v => Math.round(F.u2p(u0 + sgn * v)), cnt = sp.N_match_unknown ? sp.N_new_yes + '–' + (sp.N_new_yes + sp.N_match_unknown) : String(sp.N_new_yes);
        const t1 = bN ? lbl(NE, 'title_mark', { ev: 'R', cut: n.cut.cut_clock_et, today: num(P(0), 0), pct: val, yes: cnt, D: sp.N_match_total, n: sp.N_eligible, N: n.base.N_base }) : '';
        const t2 = bI ? lbl('EST:N-IF-NEW-R', 'title_mark', { p50: lv(q.q50), lo: num(Math.min(P(q.q25), P(q.q75)), 0), hi: num(Math.max(P(q.q25), P(q.q75)), 0), time: bT ? lbl('EST:N-TIME-R', 'title_mark', { min: Math.round(tm.q50_min) }) : '' }) : '';
        out.push(link({ k: 'now', ev }, '<span class="t"><span>' + lbl(NE, 'row_mark', { ev: '<i style="color:' + cfg[ev] + '">' + ev + '</i>' }) + (E.note ? ' <span class="p21-sub">' + esc(E.note) + '</span>' : '') + '</span></span><b>' + val + '</b>', 'mc', null, [t1, t2].filter(Boolean).join(' ')));
        continue;
      }
      out.push(link({ k: 'now', ev }, '<span class="t"><span>' + name + '</span>' + (sub ? '<span class="p21-sub">' + sub + '</span>' : '') +
        '<span class="p21-sub">' + support + (E.note ? ' · ' + esc(E.note) : '') + '</span></span><b>' + val + '</b>', 'mc', null, lbl(NE, 'title', { cut: n.cut.cut_clock_et })));
    }
    const v = (n.R && n.R.validation) || {};
    out.push('<div class="if" title="правила ' + esc(n.rules_id || '') + (v.tested_through ? ' · проверено на истории до ' + v.tested_through : '') + '">' + esc(NOWST[v.status] || v.status || '') + ' · не сделка</div>');
    // the spec (§9.3, §21.2) requires the support next to every NOW number: the only place of the panel with session counts
    return '<div class="p24-nowblk">' + out.join('') + '</div>';
  }
  // the operator's named phase rule in one place (2026-10-08, FF:PHASE-RULE): its state and both criteria with today's
  // values; the share is the passport of EST:B-CLOCK-R over the whole price range (part EARLIER, of N)
  function phaseHtml(F, ctx) {
    const ph = phaseOf(F, ctx), P = 'FF:PHASE-RULE';
    if (!ph) return '';
    const ok = b => b ? '✓ ' : '', share = ppTxt(ph.pass, true);
    return '<div class="p24-phase" title="' + esc(lbl(P, 'title')) + '"><div class="p21-h second"><span>' + lbl(P, 'head') + '</span><span><b>' + lbl(P, ph.done ? 'done' : 'open') + '</b></span></div>' +
      '<div class="p21-note">' + ok(ph.deep) + lbl(P, 'depth', { r: sd(ph.r) }) + '</div>' +
      link({ k: 'phase' }, '<span class="t"><span>' + ok(ph.half) + lbl(P, 'clock', { cut: clk(ph.cut), share }) + '</span></span>', 'mc', ph.pass, lbl('EST:B-CLOCK-R', 'title')) + '</div>';
  }
  // PROFILE:PRE-24 (operator 2026-10-08, SC-1.1 §12.5): before the confirmation, the similar sessions of history at the
  // cut — box colour, models of the day, price position — and, from their verified bundles only: in which direction they
  // then confirmed (a 100 % of N), in which 15 minutes, and what came after on each side. Words: CF:P-*, FF:PRE-STATE,
  // FF:FEW-SESSIONS. Nothing is drawn on the chart
  const FEW = 20;
  function preHtml(ctx) {
    const r = preOf(ctx), D = 'EST:P-DIR', S = 'FF:PRE-STATE';
    if (!r) return '<div class="p21-note">Подбираю похожие сессии…</div>';
    if (r.status !== 'ok') return '<div class="p21-note">' + esc(r.message || r.note || 'Похожие сессии не подобраны') + '</div>';
    const b = preBundle(r, D);
    if (!b) return '<div class="p21-note">Числа не публикуются: нарушение контракта SC-1.1</div>';
    const t = r.today, N = r.N, cut = clk(r.key.cut), out = [];
    out.push('<div class="p24-pre"><div class="p21-h second"><span title="' + esc(lbl(D, 'title', { cut, n: N })) + '">' + lbl(D, 'head') + '</span>' + scopeSwitch() + '</div>');
    out.push('<div class="p21-note" title="' + esc(lbl(S, 'title', { cut })) + '">' + lbl(S, 'line', { colour: lbl(S, t.box), up: lbl(S, t.models.up ? 'alive' : 'broken'), down: lbl(S, t.models.down ? 'alive' : 'broken'), u: (t.pos.a < 0 ? '−' : '') + num(Math.abs(t.pos.a / t.pos.w), 2) }) + '</div>');
    out.push('<div class="p21-note">' + lbl(D, 'at', { cut }) + ' · ' + (r.few ? '<b title="' + esc(lbl('FF:FEW-SESSIONS', 'title', { step: N ? pct(100 / N) : '—' })) + '">' + lbl('FF:FEW-SESSIONS', 'few', { n: N }) + '</b>' : lbl(D, 'n', { n: N })) + '</div>');
    if (!N) return out.join('') + '<div class="p21-note">' + lbl(D, 'zero') + '</div></div>';
    const cnt = {}, cols = { LONG: C.up, SHORT: C.dn, NONE: '#8C95A3', UNKNOWN: '#5F6877' };
    for (const x of b.estimates[0].categories) cnt[x.category] = x.count;
    out.push('<div class="p24-bar">' + ['LONG', 'SHORT', 'NONE', 'UNKNOWN'].filter(k => cnt[k]).map(k => '<i style="width:' + (100 * cnt[k] / N).toFixed(2) + '%;background:' + cols[k] + '"></i>').join('') + '</div>');
    for (const side of ['LONG', 'SHORT', 'NONE', 'UNKNOWN']) {
      if (side === 'UNKNOWN' && !cnt[side]) continue;
      const head = '<span class="t"><span><i style="color:' + cols[side] + '">■</i> ' + lbl(D, side);
      if (!(side === 'LONG' || side === 'SHORT') || !cnt[side]) { out.push('<div class="p21-link mc">' + head + '</span></span><b>' + pct(100 * (cnt[side] || 0) / N) + '</b></div>'); continue; }
      const W = preBundle(r, 'EST:P-WHEN', side), Rb = preBundle(r, 'EST:P-DR', side), BR = preBundle(r, 'EST:P-R', side), BX = preBundle(r, 'EST:P-X', side);
      if (!W || !Rb || !BR || !BX) { out.push('<div class="p21-link mc">' + head + '</span></span><b>—</b></div>'); continue; }
      const n = W.estimates[0].denominator, wins = W.estimates[0].categories;
      const top = wins.reduce((a, x) => x.count > a.count ? x : a, wins[0]);
      const dr = {}; for (const x of Rb.estimates[0].categories) dr[x.category] = x.count;
      const q = B => { const e = B.estimates[0]; return e.value_kind === 'QUANTILES' ? e.quantiles.map(x => sd(x.value)) : null; };
      const qr = q(BR), qx = q(BX);
      // two short lines: when and the DR outcome; the pullback and the extension (their quartiles in the title)
      const sub = [lbl('EST:P-WHEN', 'when', { window: top.category, k: top.count, n }) + ' · ' + lbl('EST:P-DR', 'dr', { held: dr.HELD || 0, n }),
        [qr ? lbl('EST:P-R', 'r', { q50: qr[1] }) : '', qx ? lbl('EST:P-X', 'x', { q50: qx[1] }) : ''].filter(Boolean).join(' · ')].filter(Boolean);
      const title = [lbl('EST:P-WHEN', 'title', { window: top.category, k: top.count, n }), lbl('EST:P-DR', 'title', { held: dr.HELD || 0, broken: dr.BROKEN || 0, n })]
        .concat(qr ? [lbl('EST:P-R', 'title', { q50: qr[1], q25: qr[0], q75: qr[2] })] : []).concat(qx ? [lbl('EST:P-X', 'title', { q50: qx[1], q25: qx[0], q75: qx[2] })] : []).join('; ');
      out.push('<div class="p21-link mc" title="' + esc(title) + '">' + head + '</span>' + sub.map(x => '<span class="p21-sub">' + x + '</span>').join('') + '</span><b>' + pct(100 * cnt[side] / N) + '</b></div>');
    }
    return out.join('') + '</div>';
  }
  // the DR outcome of the family (spec §5.2): four categories that add up to 100 % of N; one compact bar
  function outcomeHtml(F) {
    const D = 'EST:B-DR', cats = [['held', '#6FB59A'], ['broken', '#E5877F'], ['unknown', '#8C95A3'], ['none', '#5F6877']], P = {};
    for (const [k] of cats) P[k] = drPass(F, k);
    // a withheld category (its passport «—», DR-LAB-SWPC-1.1 M14) leaves its part of the bar empty
    const bar = '<div class="p24-bar">' + cats.filter(([k]) => F.out[k]).map(([k, col]) => '<i style="width:' + (100 * F.out[k] / F.N).toFixed(2) + '%;background:' + (P[k].pct == null ? 'transparent' : col) + '"></i>').join('') + '</div>';
    const rows = cats.filter(([k]) => F.out[k] || k === 'held' || k === 'broken').map(([k, col]) => link({ k: 'out', cat: k }, '<span class="t"><i style="color:' + col + '">■</i> ' + lbl(D, k) + '</span><b>' + ppTxt(P[k]) + '</b>', 'in', P[k], plainTitle(P[k]))).join('');
    return '<div class="p21-h second">' + lbl(D, 'head', { end: clk(F.end) }) + '<span>' + lbl(D, 'head_r') + '</span></div>' + bar + '<div class="p24-out big">' + rows + '</div>';
  }
  function areaHtml(F, ctx) {
    const I = areaInfo(F, ctx), out = ['<div class="p21-h second p24-sel">Выбранная область <span><button class="p24-x" data-clear="area" title="Снять выбор (Esc)">✕</button></span></div>'];
    out.push('<div class="p21-note"><b style="color:#D1D4DC;font-weight:600">' + esc(I.name) + '</b>' + (I.prices ? ' · ' + px(I.prices[0]) + ' – ' + px(I.prices[1]) + ' · ' + esc(where(ctx.s, (I.prices[0] + I.prices[1]) / 2)) : '') + '</div>');
    const tag = '<i style="color:' + cfg[I.ev] + '">' + I.ev + '</i>';
    if (I.band) out.push(link({ k: 'area', part: 'band' }, prow(lbl(I.band.estimand, 'area_row', { ev: tag }), ppTxt(I.band)), '', I.band, plainTitle(I.band)));
    if (I.win) out.push(link({ k: 'area', part: 'window' }, prow(lbl(I.win.estimand, 'area_row', { ev: tag }), ppTxt(I.win)), '', I.win, plainTitle(I.win)));
    if (I.vfull) {
      out.push(link({ k: 'area', part: 'visit' }, prow(lbl('EST:B-VISIT-FULL', 'row'), ppTxt(I.vfull, true)), 'dim', I.vfull, plainTitle(I.vfull)));
      out.push(link({ k: 'area', part: 'visit' }, prow(ctx && sliceOf(ctx) >= F.end ? lbl('EST:B-VISIT-REST', 'row_none') : lbl('EST:B-VISIT-REST', 'row', { t: clk(sliceOf(ctx)) }), ppTxt(I.vrest, true)), 'dim', I.vrest, plainTitle(I.vrest)));
    }
    if (I.today) out.push('<div class="p21-note">' + esc(I.today) + '</div>');
    return out.join('');
  }
  function levelHtml(F, ctx, l) {
    const q = levelQuery(F, ctx, l.p, l.type === 'std' ? l.name : l.full), sl = sliceOf(ctx);
    return '<div class="p21-h second p24-sel">Уровень <span>' + esc(l.type === 'std' ? l.name : l.full) + ' · ' + px(l.p) + ' <button class="p24-x" data-clear="pin" title="Снять (Esc)">✕</button></span></div>' +
      link({ k: 'lvl', id: l.id, l }, prow(lbl('EST:B-LEVEL-FULL', 'row', { dir: dirName(F, q.up) }), ppTxt(q.full, true)), '', q.full, plainTitle(q.full)) +
      link({ k: 'lvl', id: l.id, l }, prow(sl >= F.end ? lbl('EST:B-LEVEL-REST', 'row_none', { dir: dirName(F, q.up) }) : lbl('EST:B-LEVEL-REST', 'row', { dir: dirName(F, q.up), t: clk(sl) }), ppTxt(q.rest, true)), '', q.rest, plainTitle(q.rest)) +
      '<div class="p21-note">' + esc(q.today) + '</div>';
  }
  function memberHtml(F, m) {
    const M_ = 'FF:MEMBER', ev = e => m[e].s === 'known' ? sd(m[e].v / m.w) + ' SD · ' + px(F.u2p(m[e].v / m.w)) + ' · ' + clk(m[e].t) : lbl(M_, 'unknown');
    return '<div class="p21-h second p24-sel">' + lbl(M_, 'panel_head') + ' <span>' + esc(memberLine(F, m)) + ' <button class="p24-x" data-clear="pin" title="Снять (Esc)">✕</button></span></div>' +
      '<div class="p24-mem"><div><i style="color:' + cfg.R + '">R</i> ' + F.names.R.toLowerCase() + ': ' + ev('R') + '</div><div><i style="color:' + cfg.X + '">X</i> ' + F.names.X.toLowerCase() + ': ' + ev('X') + '</div>' +
      '<div class="p21-sub">' + esc(orderText(F, m)) + '</div>' +
      (F.brk ? '' : '<div class="p21-sub">' + (m.outcome === 'broken' ? lbl(M_, 'panel_dr_broken', { t: m.brkKnown ? clk(m.brk) : '' }) : m.outcome === 'held' ? lbl(M_, 'dr_held', { end: clk(F.end) }) : lbl(M_, 'dr_unknown')) + '</div>') +
      '<div class="p21-sub">' + lbl(M_, 'panel_act', { act: lbl('FF:PASSPORT-VIEW', 'act', null, VW(F)), t: clk(m.act) }) + '</div></div>';
  }
  // «Путь семьи» (spec §5.3, §10.2): the closes of the family on ONE M5, a column of its own 100 % (the missing M5 in it).
  // The distribution itself stands right of the price scale, aligned with the prices; the panel names the M5, the cell
  // under the cursor, the missing mass and what today's candle did on the same M5 (no second copy of the column).
  function columnHtml(F, ctx) {
    const cd = colFor(ctx), out = [], h = hv();
    const pinned = st.col === cd.j, hovered = h && (h.k === 'col' || h.k === 'fcell');
    out.push('<div class="p21-h second">Путь семьи · M5 ' + clk(cd.T - 5) + '–' + clk(cd.T) + '<span>' + (hovered ? 'под курсором' : pinned ? 'выбрана' : cd.T === sliceOf(ctx) ? 'на срезе' : '') + '</span></div>');
    if (h && h.k === 'fcell' && h.j === cd.j) {
      const list = cd.cells.get(h.kk) || [], p = closePass(F, cd.j, h.kk, h.kk + 1, list.length);
      out.push(link({ k: 'fcell', j: cd.j, kk: h.kk }, prow(lbl('EST:B-CLOSE', 'row', { band: band(h.kk, h.kk + 1) }) + ' <span class="p21-sub">' + px(Math.min(F.u2p(h.kk / 10), F.u2p((h.kk + 1) / 10))) + '</span>', ppTxt(p)), '', p, plainTitle(p)));
    }
    if (cd.unknown) {
      const p = missPass(F, cd);
      out.push('<div class="p21-link fc dim" data-pp="' + p.id + '" title="' + esc(plainTitle(p)) + '"><span class="t">' + lbl('EST:B-CLOSE-MISSING', 'row') + '</span><b>' + ppTxt(p) + '</b></div>');
    }
    if (cd.pre) {
      const p = pp(F, { estimand: 'EST:B-CLOSE-PREACT', params: { j: cd.j }, event_id: 'close_M5', region_kind: 'M5_phase', start_rule: 'M5 ' + clk(cd.T - 5), end_rule: clk(cd.T), yes_count: cd.pre, display_scope: 'panel' });
      out.push('<div class="p21-note">' + lbl('EST:B-CLOSE-PREACT', 'note', { act: lbl('FF:PASSPORT-VIEW', 'act_gen', null, VW(F)), pct: ppTxt(p) }) + '</div>');
    }
    const tb = ctx.D.bars.find(b => b.t + 5 === cd.T);
    if (tb && cd.T <= sliceOf(ctx)) out.push('<div class="p21-note">' + lbl('FF:TODAY-LEVEL', 'column', { sd: sd(F.d0 * (tk(tb.c) - F.e0t) / F.w0t), price: px(tb.c) }) + '</div>');
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

  // ---------- the six windows of the family (bottom; operator 2026-10-01, variant «Окна времени») ----------
  // They slide up when the mouse reaches the bottom edge of the chart and a click on their head pins them. Each window is
  // its own object with its own 100 % or its own nested question, never a repeat of the chart:
  // 1 the passport of what is under the cursor or pinned, else the family's snapshot; 2-3 R and X as price x time cells
  // with the exact cells of their zones; 4 what came first in each session, R or X (its own 100 %); 5 «на уровне или
  // дальше» on today's levels, whole horizon and after the slice (nested, never a 100 %); 6 «Путь семьи», the family's M5
  // closes per common clock M5 (each column its own 100 %), with today's closes on it.
  function detailObj(ctx) {
    const h = hv();
    if (h && ['pt', 'lvl', 'pcell', 'tcell', 'fcell', 'col', 'area', 'out', 'evrow', 'zone'].includes(h.k)) return h;
    if (st.area) return { k: 'area', part: 'band' };
    return null;
  }
  const dRow = (k, v) => '<div class="p24-dr"><span>' + k + '</span><b>' + v + '</b></div>';
  function passportRows(p) {
    const b = p.exact_price_bounds, V_ = 'FF:PASSPORT-VIEW';
    return dRow(lbl(V_, 'win_event'), esc(p.phrase)) + dRow(lbl(V_, 'win_horizon'), esc(p.horizon)) +
      (b && b.length === 2 && typeof b[0] === 'number' ? dRow(lbl(V_, 'win_price'), band(b[0], b[1]) + ' SD <span class="k">[' + b[0] + '/10; ' + b[1] + '/10)</span>') : b && b.length === 1 ? dRow(lbl(V_, 'win_level'), sd(p.level_sd) + ' SD <span class="k">' + lbl(V_, 'win_level_k', { u: b[0] }) + '</span>') : '') +
      (p.time_bounds ? dRow(lbl(V_, 'win_time'), clk(p.time_bounds[0]) + '–' + clk(p.time_bounds[1])) : '') +
      dRow(lbl(V_, 'win_share'), ppTxt(p, p.binary) + (p.pct != null ? ' <span class="k">(' + pct2(p.pct) + ')</span>' : '')) +
      (p.unknown_count ? dRow(lbl(V_, 'win_unknown'), pct(100 * p.unknown_count / p.N) + (p.binary ? '' : ' <span class="k">' + lbl(V_, 'win_bound', { pct: pct(100 * (p.yes_count + p.unknown_count) / p.N) }) + '</span>')) : '') +
      dRow(lbl('FF:SHARE-STEP', 'denominator'), lbl('FF:SHARE-STEP', 'denominator_v', { step: pct(100 / p.N) }));
  }
  // the passport of a zone (zone-map-3 §40) and its diagnostics: properties of the zone, never a permission to exist;
  // the study figures are research, not a chance for today
  function zoneRows(F, ctx, ev, i) {
    const Zm = zonesOf(F, ev), z = Zm.zones[i], s = zoneStatus(F, ctx, ev)[i], E = 'EST:B-ZONE-' + ev;
    return dRow(lbl(E, 'zone'), esc(z.label + ' · ' + z.zone_id + ' · ' + z.algorithm_version)) +
      dRow('семья', esc((z.family_scope === 'all' ? 'все дни недели' : 'день недели') + ' · ' + F.cond)) +
      dRow(lbl(E, 'area'), lbl(E, 'area_v', { n: z.cell_mask.length }) + ' <span class="k">' + lbl(E, 'area_k', { band: band(z.price_low, z.price_high), window: clk(z.time_start) + '–' + clk(z.time_end) }) + '</span>') +
      dRow(lbl(E, 'apex'), lbl(E, 'apex_v', { band: band(z.peak_anchor[0], z.peak_anchor[0] + 1), window: clk(F.f + 15 * z.peak_anchor[1]) + '–' + clk(F.f + 15 * z.peak_anchor[1] + 15) })) +
      dRow(lbl(E, 'row'), ppTxt(zonePass(F, ev, z)) + ' <span class="k">' + lbl(E, 'k', { step: pct(100 / F.N), unknown: ppTxt(undPass(F, ev, 'UNKNOWN')), none: ppTxt(undPass(F, ev, 'NO_PERIOD')), residual: ppTxt(resPass(F, ev)) }) + '</span>') +
      dRow(lbl('FF:TODAY-Z', 'row'), zst(s) + ' <span class="k">' + lbl('FF:TODAY-Z', 'k', { act: lbl('FF:PASSPORT-VIEW', 'act_gen', null, VW(F)) }) + '</span>') +
      dRow('слепок', esc(z.snapshot_id + ' · семья ' + z.family_id));
  }
  // the zone's diagnostics and study figures: properties of the zone, each shown only with its published bundle
  function zoneDiag(F, ev, z) {
    const g = z.grid_member_jaccard, b = z.bootstrap_recovery, f2 = v => v == null ? '—' : num(v, 2), zid = x => x.zone_id === z.zone_id;
    const G = 'EST:ZD-GRID-' + ev, Bt = 'EST:ZD-BOOT-' + ev, Nl = 'EST:ZD-NULL-' + ev;
    let s = (hasBundle(F, G, zid) ? dRow(lbl(G, 'row'), lbl(G, 'text', { g1: f2(g.price_half), g2: f2(g.time_5), g3: f2(g.time_10) }) + ' <span class="k">' + lbl(G, 'k') + '</span>') : '') +
      (b.mean == null || hasBundle(F, Bt, zid) ? dRow(lbl(Bt, 'row'), lbl(Bt, 'text', { mean: f2(b.mean), share: b.share_ge_half == null ? '—' : pct(100 * b.share_ge_half), of: b.of })) : '');
    if (z.null_status === 'measured') {
      if (hasBundle(F, Nl, zid)) s += dRow(lbl(Nl, 'row'), lbl(Nl, 'text', { p_real: pct(100 * z.p_real_mask), p_null: pct(100 * z.p_null_mask), excess: (z.null_excess >= 0 ? '+' : '−') + num(Math.abs(100 * z.null_excess), 1) }) +
        ' <span class="k">' + lbl(Nl, 'k', { mde: num(100 * z.minimum_detectable_excess, 1) }) + '</span>');
    } else { const m = /^not_applicable: (.*)$/.exec(z.null_status || ''); s += dRow(lbl(Nl, 'row'), '<span class="k">' + (m ? lbl(Nl, 'na', { reason: esc(m[1]) }) : esc(z.null_status)) + '</span>'); }
    if (z.study_refs && hasBundle(F, 'EST:ZM3-STUDY', x => x.event === ev)) s += dRow(lbl('EST:ZM3-STUDY', 'row'), '<span class="k">' + esc(z.study_refs.text) + '</span>');
    return s;
  }
  // window 1: the passport of the object (as the details area of design 24 had it), or the family's snapshot
  function detBody(ctx, o) {
    const F = ctx.F;
    if (!o) {
      const r = F.r, src = r.source || {};
      return { head: 'Слепок семьи', body: dRow('семья', esc(F.cond)) + dRow('ключ', esc(r.key.instrument + ' × ' + r.key.session + ' × ' + WD[r.key.weekday] + ' × ' + (r.key.direction === 'long' ? 'лонг' : 'шорт') + ' × ' + (r.key.event === 'confirmation' ? 'окно подтверждения ' : 'окно слома ') + clk(r.key.window[0]) + '–' + clk(r.key.window[1]))) +
        dRow('история', esc((src.history || '') + ', только дни раньше ' + r.key.cutoff)) + dRow('шкала', esc('u = d·(цена − край)/ширина IDR; край: ' + r.scale.edge + '; ячейки 0,1 SD × 15 мин от ' + clk(r.scale.f))) +
        dRow('начало', esc(r.rules.start)) + dRow('конец', esc(r.rules.end)) + dRow('время события', esc(r.rules.time)) + dRow('атом', esc(r.rules.atom)) +
        dRow('слепок', esc(r.snapshot_id + ' · семья ' + r.family_id + ' · ' + r.semantics)) + dRow(lbl('FF:SHARE-STEP', 'step'), pct(100 / F.N)) };
    }
    if (o.k === 'pt') {
      const m = F.M[o.i], M_ = 'FF:MEMBER';
      const one = e => m[e].s === 'known' ? sd(m[e].v / m.w) + ' SD · ' + clk(m[e].t) + (m[e].ties.length > 1 ? lbl(M_, 'win_same_price', { times: m[e].ties.slice(1).map(clk).join(', ') }) : '') : lbl(M_, 'unknown');
      return { head: 'Сессия ' + memberLine(F, m), body: dRow(F.names.R.toLowerCase() + ' R', one('R')) + dRow(F.names.X.toLowerCase() + ' X', one('X')) +
        dRow(lbl(M_, 'win_order'), esc(orderText(F, m))) + (F.brk ? '' : dRow('DR', m.outcome === 'broken' ? lbl(M_, 'win_broken', { t: m.brkKnown ? clk(m.brk) : '' }) : m.outcome === 'held' ? lbl(M_, 'win_held', { end: clk(F.end) }) : lbl(M_, 'win_dr_unknown'))) +
        dRow(lbl('FF:PASSPORT-VIEW', 'act', null, VW(F)), clk(m.act)) + (m.missing ? dRow(lbl(M_, 'win_missing'), lbl(M_, 'win_missing_v', { n: m.missing })) : '') };
    }
    if (o.k === 'lvl' && o.l) {
      const q = levelQuery(F, ctx, o.l.p, o.l.type === 'std' ? o.l.name : o.l.full);
      return { head: 'Уровень ' + (o.l.type === 'std' ? o.l.name : o.l.full), body: passportRows(q.full) + dRow(lbl('EST:B-LEVEL-REST', 'win_row'), ppTxt(q.rest, true) + ' <span class="k">' + esc(q.rest.horizon) + '</span>') +
        dRow(lbl('EST:B-CROSS-FULL', 'win_row'), ppTxt(q.cross, true) + ' <span class="k">' + lbl('EST:B-CROSS-FULL', 'win_k') + '</span>') + dRow(lbl('FF:TODAY-Z', 'row'), esc(q.today.replace(/^сегодня: /, ''))) };
    }
    if (o.k === 'area' && st.area) {
      const I = areaInfo(F, ctx);
      return { head: 'Область ' + I.name, body: (I.band ? passportRows(I.band) : '') + (I.win ? dRow(lbl(I.win.estimand, 'win_row'), ppTxt(I.win) + ' <span class="k">' + esc(I.win.phrase) + '</span>') : '') +
        (I.vfull ? dRow(lbl('EST:B-VISIT-FULL', 'win_row'), ppTxt(I.vfull, true) + ' ' + lbl('EST:B-VISIT-FULL', 'win_full') + ' · ' + ppTxt(I.vrest, true) + ' ' + esc(I.vrest.horizon)) : '') + (I.today ? dRow(lbl('FF:TODAY-Z', 'row'), esc(I.today.replace(/^сегодня: /, ''))) : '') };
    }
    if (o.k === 'pcell') {
      const ev = o.ev || st.ev;
      return { head: 'Полоса ' + band(o.k0, o.k1) + ' SD', body: passportRows(evPass(F, ev, 'price_cell', [o.k0, o.k1], null, areaCount(F, ev, { k0: o.k0, k1: o.k1 }))) };
    }
    if (o.k === 'tcell') {
      const t0 = F.f + 15 * o.b0;
      return { head: clk(t0) + '–' + clk(t0 + 15), body: ['X', 'R'].map(ev => passportRows(evPass(F, ev, 'time_cell', null, [t0, t0 + 15], F.ev[ev].T.get(o.b0) || 0))).join('<div class="p24-sep"></div>') };
    }
    if (o.k === 'fcell' || o.k === 'col') {
      const cd = filmOf(F)[o.j];
      if (o.k === 'fcell') {
        const list = cd.cells.get(o.kk) || [];
        return { head: 'M5 ' + clk(cd.T - 5) + '–' + clk(cd.T), body: passportRows(closePass(F, o.j, o.kk, o.kk + 1, list.length)) +
          dRow(lbl('EST:B-RANGE', 'win_row'), ppTxt(rangePass(F, o.j, o.kk)) + ' <span class="k">' + lbl('EST:B-RANGE', 'win_k') + '</span>') };
      }
      return { head: 'M5 ' + clk(cd.T - 5) + '–' + clk(cd.T), body: dRow(lbl('EST:B-CLOSE', 'col'), lbl('EST:B-CLOSE', 'col_v')) + dRow(lbl('EST:B-CLOSE-MISSING', 'win_row'), ppTxt(missPass(F, cd))) };
    }
    if (o.k === 'out') {
      const D_ = 'EST:B-DR';
      return { head: lbl(D_, 'win_head'), body: dRow(lbl(D_, 'win_cat'), lbl(D_, o.cat)) + dRow(lbl(D_, 'win_share'), ppTxt(drPass(F, o.cat))) + dRow(lbl(D_, 'win_rule'), lbl(D_, 'win_rule_v')) +
        dRow(lbl(D_, 'win_horizon'), lbl('FF:PASSPORT-VIEW', 'horizon', { from: F.from, end: clk(F.end) })) };
    }
    if (o.k === 'zone' && zonesOf(F, o.ev) && zonesOf(F, o.ev).zones[o.i]) {
      const z = zonesOf(F, o.ev).zones[o.i];
      return { head: 'Зона ' + z.label + ' · ' + zoneName(z), body: zoneRows(F, ctx, o.ev, o.i) + '<div class="p24-sep"></div>' + zoneDiag(F, o.ev, z) };
    }
    if (o.k === 'evrow') {
      const ev = o.ev || st.ev, D = F.ev[ev], U = 'EST:B-RX-UNDETERMINED-' + ev, KN = 'EST:B-RX-KNOWN-' + ev, PV = 'FF:PASSPORT-VIEW';
      const kn = pp(F, { estimand: KN, params: {}, event_id: ev, region_kind: 'known', start_rule: F.from, end_rule: 'до ' + clk(F.end), yes_count: D.known, unknown_count: D.unknown, no_event_count: D.none, display_scope: 'details' });
      return { head: F.names[ev] + ' ' + ev, body: dRow(lbl(PV, 'win_event'), esc(F.what[ev])) + dRow(lbl(KN, 'row'), ppTxt(kn)) + dRow(lbl(U, 'win_unknown'), ppTxt(undPass(F, ev, 'UNKNOWN')) + ' <span class="k">' + lbl(U, 'win_unknown_k') + '</span>') +
        (D.none ? dRow(lbl(U, 'win_none'), ppTxt(undPass(F, ev, 'NO_PERIOD'))) : '') + dRow(lbl(PV, 'win_horizon'), lbl(PV, 'horizon', { from: F.from, end: clk(F.end) })) };
    }
    return detBody(ctx, null);
  }
  // window 4: what came first in each session, its first R or its first X (spec §8); one 100 %
  function orderHtml(F) {
    const n = orderCounts(F), O = 'EST:B-ORDER';
    const rows = [['X_before_R', cfg.X], ['R_before_X', cfg.R], ['same_M5', '#8C929D'], ['unknown', '#4A505B'], ['no_period', '#353A44']].filter(([k]) => k !== 'no_period' || n[k]);
    const P = rows.map(([k]) => pp(F, { estimand: O, params: { category: k }, event_id: 'order_' + k, region_kind: 'order', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
      yes_count: n[k], display_scope: 'details', phrase: lbl(O, 'phrase', { t: lbl(O, k) }), horizon: hzOf(F) }));
    return '<div class="p24-bar wide">' + rows.map(([k, c], j) => n[k] ? '<i style="width:' + (100 * n[k] / F.N).toFixed(2) + '%;background:' + (P[j].pct == null ? 'transparent' : c) + '"></i>' : '').join('') + '</div>' +
      rows.map(([k, c], j) => '<div class="dq" data-ord="' + k + '" title="' + esc(plainTitle(P[j])) + '"><i style="background:' + c + '"></i><span>' + lbl(O, k) + '</span><b>' + ppTxt(P[j]) + '</b></div>').join('');
  }
  // window 5: «на уровне или дальше» on today's levels (spec §5.4): nested shares, the whole horizon (pale) and after the
  // slice (bright); a level today already reached is marked with its time
  function ladderHtml(F, ctx) {
    const s = ctx.s, play = F.brk ? -s.side : s.side, L = levels(s), sl = sliceOf(ctx), rows = [];
    const along = L.filter(l => l.type === 'std' && l.dir === play && l.j <= 4).sort((a, b) => b.j - a.j);
    const opp = play === 1 ? ['mid', 'idrL', 'drL', 'd1', 'd2'] : ['mid', 'idrH', 'drH', 'u1', 'u2'];
    const list = along.concat(opp.map(id => L.find(l => l.id === id)).filter(Boolean));
    const taken = (s.taken || []).concat(s.takenN || []);
    for (const l of list) {
      const nm = l.type === 'std' ? l.name : l.full, q = levelQuery(F, ctx, l.p, nm), up = q.up, col = up ? cfg.X : cfg.R;
      const tk = l.type === 'std' ? taken.find(z => z.t && z.name === l.name) : null;
      rows.push('<div class="dl" data-lvl="' + l.id + '" title="' + esc(plainTitle(q.full)) + '"><span class="n">' + esc(l.type === 'std' ? 'STD ' + l.name : nm) + (tk ? ' <em>✓ ' + clk(tk.t) + '</em>' : '') + '</span><span class="b"><i style="width:' + (q.full.pct || 0).toFixed(1) + '%;background:' + rgba(col, 0.35) + '"></i><i style="width:' + (q.rest.pct || 0).toFixed(1) + '%;background:' + rgba(col, 0.9) + '"></i></span><b>' + ppTxt(q.full, true) + '</b><span class="r" style="color:' + col + '">' + ppTxt(q.rest, true) + '</span></div>');
    }
    return '<div class="dlh"><span></span><span>' + lbl('EST:B-LEVEL-FULL', 'ladder_head') + '</span><span>' + lbl('EST:B-LEVEL-REST', 'ladder_head', { t: clk(sl) }) + '</span></div>' + rows.join('');
  }
  // windows 2, 3 and 6 are small canvases
  function cardCanvas(id) {
    const cvs = dom(id);
    if (!cvs) return null;
    const r = cvs.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    cvs.width = Math.round(r.width * dpr); cvs.height = Math.round(r.height * dpr);
    const c = cvs.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { c, W: r.width, H: r.height };
  }
  function drawHeat(id, F, ctx, ev) {
    const K = cardCanvas(id);
    if (!K) return;
    const { c, W, H } = K, cells = [...F.ev[ev].cells.values()], L = 30, T = 4, B = 16, Rm = 4;
    if (!cells.length) return;
    const ks = []; for (const q of cells) for (let i = 0; i < q.list.length; i++) ks.push(q.k);
    ks.sort((a, b) => a - b);
    const k0 = ks[Math.floor(0.03 * (ks.length - 1))], k1 = ks[Math.ceil(0.97 * (ks.length - 1))] + 1, mx = Math.max(...cells.map(q => q.list.length));
    const cw = (W - L - Rm) / F.nb, rh = (H - T - B) / (k1 - k0), X = b => L + b * cw, Y = k => T + (k1 - 1 - k) * rh;
    dom(id)._g = { L, T, cw, rh, k0, k1, n: F.nb, ev };
    for (const q of cells) { if (q.k < k0 || q.k >= k1) continue; c.fillStyle = rgba(cfg[ev], 0.18 + 0.82 * Math.pow(q.list.length / mx, 0.7)); c.fillRect(X(q.b) + 0.5, Y(q.k) + 0.25, Math.max(1, cw - 1), Math.max(1, rh - 0.5)); }
    const Zm = F.zones[ev];
    if (Zm) Zm.zones.forEach((z, i) => {
      if (zoneHeld(F, ev, i)) return;                    // a withheld zone: no outline (DR-LAB-SWPC-1.1 M14)
      const set = new Set(z.cell_mask.map(([k, b]) => k + '|' + b));
      c.strokeStyle = rgba(cfg[ev], 0.95); c.lineWidth = 1; c.beginPath();
      for (const [k, b] of z.cell_mask) {
        if (k < k0 || k >= k1) continue;
        const x0 = X(b), x1 = X(b + 1), y0 = Y(k), y1 = Y(k) + rh;
        if (!set.has((k + 1) + '|' + b)) { c.moveTo(x0, y0); c.lineTo(x1, y0); }
        if (!set.has((k - 1) + '|' + b)) { c.moveTo(x0, y1); c.lineTo(x1, y1); }
        if (!set.has(k + '|' + (b - 1))) { c.moveTo(x0, y0); c.lineTo(x0, y1); }
        if (!set.has(k + '|' + (b + 1))) { c.moveTo(x1, y0); c.lineTo(x1, y1); }
      }
      c.stroke();
      const kk = Math.max(...z.cell_mask.map(q => q[0])), bb = Math.min(...z.cell_mask.filter(q => q[0] === kk).map(q => q[1]));
      c.font = '700 10px ' + FONT; c.fillStyle = cfg[ev]; c.textBaseline = 'bottom'; c.fillText(z.label, X(bb), Math.max(9, Y(kk) - 1));
    });
    const sl = sliceOf(ctx), xs = X((sl - F.f) / 15);
    if (xs > L && xs < W - Rm) { c.strokeStyle = 'rgba(209,212,220,.5)'; c.setLineDash([3, 3]); c.beginPath(); c.moveTo(xs, T); c.lineTo(xs, H - B); c.stroke(); c.setLineDash([]); }
    c.font = '10px ' + FONT; c.fillStyle = C.text3; c.textBaseline = 'middle'; c.textAlign = 'right';
    c.fillText(sd(k1 / 10), L - 4, T + 4); c.fillText(sd(k0 / 10), L - 4, H - B - 4);
    c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText(clk(F.f), L, H - B + 3); c.textAlign = 'right'; c.fillText(clk(F.end), W - Rm, H - B + 3); c.textAlign = 'left';
  }
  function drawFilmMini(id, F, ctx) {
    const K = cardCanvas(id);
    if (!K) return;
    const { c, W, H } = K, film = filmOf(F), L = 30, T = 4, B = 16, Rm = 4, all = [];
    for (const cd of film) for (const [k, l] of cd.cells) for (let i = 0; i < l.length; i++) all.push(k);
    if (!all.length) return;
    all.sort((a, b) => a - b);
    const k0 = all[Math.floor(0.03 * (all.length - 1))], k1 = all[Math.ceil(0.97 * (all.length - 1))] + 1;
    const cw = (W - L - Rm) / film.length, rh = (H - T - B) / (k1 - k0), X = j => L + j * cw, Y = k => T + (k1 - 1 - k) * rh;
    dom(id)._g = { L, T, cw, rh, k0, k1, n: film.length, film: true };
    film.forEach((cd, j) => { for (const [k, l] of cd.cells) { if (k < k0 || k >= k1) continue; c.fillStyle = rgba(cfg.path, Math.min(1, (0.1 + 0.9 * l.length / F.N) * cfg.heatA / 100)); c.fillRect(X(j), Y(k), cw + 0.3, rh + 0.3); } });
    c.fillStyle = '#FFFFFF';
    for (const q of todayRows(F, ctx)) { const j = F.grid.indexOf(q.T), k = 10 * q.cl / F.w0t; if (j < 0 || k < k0 || k >= k1) continue; c.beginPath(); c.arc(X(j) + cw / 2, Y(Math.floor(k)) + rh / 2, 2, 0, 6.2832); c.fill(); }
    const sl = sliceOf(ctx), js = F.grid.indexOf(sl);
    if (js >= 0) { const xs = X(js + 1); c.strokeStyle = 'rgba(209,212,220,.5)'; c.setLineDash([3, 3]); c.beginPath(); c.moveTo(xs, T); c.lineTo(xs, H - B); c.stroke(); c.setLineDash([]); }
    c.font = '10px ' + FONT; c.fillStyle = C.text3; c.textBaseline = 'middle'; c.textAlign = 'right';
    c.fillText(sd(k1 / 10), L - 4, T + 4); c.fillText(sd(k0 / 10), L - 4, H - B - 4);
    c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText(clk(F.grid[0] - 5), L, H - B + 3); c.textAlign = 'right'; c.fillText(clk(F.end), W - Rm, H - B + 3); c.textAlign = 'left';
  }
  function details(ctx) {
    const on = st.L.det;
    det.style.display = on ? '' : 'none';
    if (!on) return;
    const open = st.detPin || st.detOver, F = ctx.F, ok = !!(F && F.N);
    det.classList.toggle('open', open);
    const head = '<span>' + (open ? '▾ ' : '▴ ') + 'Окна семьи' + (ok ? ' · ' + esc(F.cond) + ' · после ' + clk(Math.min(sliceOf(ctx), F.end)) : ' · ' + esc(statusMsg(ctx))) + '</span>' + (st.detPin ? '<span class="k">закреплено</span>' : '');
    const dh = dom('deth');
    if (dh._h !== head) { dh.innerHTML = head; dh._h = head; }
    const g = dom('detg');
    if (!open || !ok) { if (g._k) { g.innerHTML = ''; g._k = ''; } return; }
    const o = detailObj(ctx), key = [F.r.snapshot_id, F.view, sliceOf(ctx), o ? pinKey(o) + '|' + (o.ev || '') : '', det.clientWidth, cfg.R, cfg.X, cfg.path, cfg.heatA].join('|');
    if (g._k === key) return;
    g._k = key;
    const B = detBody(ctx, o);
    g.innerHTML =
      '<div class="dcard"><div class="dt">' + esc(B.head) + '</div><div class="dbody">' + B.body + '</div></div>' +
      '<div class="dcard"><div class="dt" style="color:' + cfg.R + '">' + F.names.R + ' R · цена × время</div><canvas id="dcR"></canvas></div>' +
      '<div class="dcard"><div class="dt" style="color:' + cfg.X + '">' + F.names.X + ' X · цена × время</div><canvas id="dcX"></canvas></div>' +
      '<div class="dcard"><div class="dt">Что было раньше: R или X</div>' + orderHtml(F) + '</div>' +
      '<div class="dcard"><div class="dt">На уровне или дальше</div>' + ladderHtml(F, ctx) + '</div>' +
      '<div class="dcard"><div class="dt" style="color:' + cfg.path + '">Путь семьи · закрытия M5</div><canvas id="dcF"></canvas></div>';
    drawHeat('dcR', F, ctx, 'R'); drawHeat('dcX', F, ctx, 'X'); drawFilmMini('dcF', F, ctx);
  }
  function initPanel24() {
    panel.addEventListener('mouseover', e => { const el = e.target.closest('[data-l21]'); if (!el) return; st.hover = P24.links[+el.dataset.l21]; if (st.hover && st.hover.ev) st.ev = st.hover.ev; showTip(st.hover); redraw(); });
    panel.addEventListener('mouseout', e => { const el = e.target.closest('[data-l21]'); if (!el || el.contains(e.relatedTarget)) return; st.hover = null; animStrip(); redraw(); });
    panel.addEventListener('click', e => {
      if (e.target.closest('[data-hist]')) {
        if (A.src === 'live') histFallback();
        else ensureDates().then(list => { const i = list.findIndex(x => x >= A.date), d = list[Math.max(0, (i < 0 ? list.length : i) - 1)]; if (d) openHist(d); });
        return;
      }
      const sc = e.target.closest('[data-scope]');                // the explicit family scope (zone-map-3 §2.2)
      if (sc) { st.scope = sc.dataset.scope; st.area = null; st.pin = null; st.hover = null; st.col = null; render(true); return; }
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
    det.addEventListener('mouseleave', () => { st.detOver = false; if (st.fromDet) { st.hover = null; st.mini = null; st.fromDet = false; } render(false); });
    // operator 2026-10-06: what is under the mouse in a window is lit on the main chart, like a hovered zone: a cell of
    // R / X «цена × время» → that band × 15 minutes framed (its whole constellation if the cell is in a zone); a row of
    // «что было раньше» → the stars of those sessions; a level of «на уровне или дальше» → that level (and the sessions
    // that reached it); a cell of «Путь семьи» → that band on that M5 framed
    det.addEventListener('mousemove', e => {
      const ctx = V && V.ctx, F = ctx && ctx.F;
      if (!F) return;
      let h = null, mini = null;
      const cvs = e.target.closest('canvas'), row = e.target.closest('[data-ord],[data-lvl]');
      if (cvs && cvs._g) {
        const g = cvs._g, r = cvs.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
        const j = Math.floor((x - g.L) / g.cw), k = g.k1 - 1 - Math.floor((y - g.T) / g.rh);
        if (j >= 0 && j < g.n && k >= g.k0 && k < g.k1) {
          if (g.film) { const cd = filmOf(F)[j]; h = { k: 'fcell', j, kk: k }; mini = { k0: k, k1: k + 1, t0: cd.T - 5, t1: cd.T, col: cfg.path }; }
          else {
            const zi = F.zcell[g.ev].get(k + '|' + j);
            h = zi != null ? { k: 'zone', ev: g.ev, i: zi } : { k: 'hcell', ev: g.ev, kk: k, b: j };
            mini = { k0: k, k1: k + 1, t0: F.f + 15 * j, t1: F.f + 15 * j + 15, col: cfg[g.ev] };
          }
        }
      } else if (row && row.dataset.ord) h = { k: 'order', key: row.dataset.ord };
      else if (row && row.dataset.lvl) { const l = levels(ctx.s).find(z => z.id === row.dataset.lvl); if (l) h = { k: 'lvl', id: l.id, l }; }
      const key = JSON.stringify([h, mini]);
      if (key === st.detKey) return;
      st.detKey = key; st.hover = h; st.mini = mini; st.fromDet = !!h;
      if (h && h.ev) st.ev = h.ev;
      redraw();
    });
    dom('deth').addEventListener('click', () => { st.detPin = !st.detPin; render(false); });
    new ResizeObserver(() => redraw(true)).observe(cv);
  }
