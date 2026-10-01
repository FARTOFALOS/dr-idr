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
    if (F.out) out.push(outcomeHtml(F));
    if (st.mode === 'bounds') {
      out.push(zonesHtml(F, ctx));
      const tf = todayFacts(F, ctx);
      if (tf) out.push('<div class="p21-note" title="Наблюдённые закрытые свечи сегодняшнего дня после ' + (F.brk ? 'слома' : 'подтверждения') + ' до среза; не окончательные значения">' + tf + '</div>');
    }
    if (st.mode === 'path') out.push(columnHtml(F, ctx));
    if (st.area && st.mode === 'bounds') out.push(areaHtml(F, ctx));
    const h = st.pin;
    if (h && h.k === 'lvl' && h.l) out.push(levelHtml(F, ctx, h.l));
    if (h && h.k === 'pt' && F.M[h.i]) out.push(memberHtml(F, F.M[h.i]));
    panel.innerHTML = out.join('');
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
    if (!rows.length) out.push('<div class="p21-note">зон нет: ни одна область не набрала минимальной поддержки</div>');
    let sep = false;
    for (const r of rows) {
      if (!sep && r.z.time_end > sl) { sep = true; out.push('<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>'); }
      const p = zonePass(F, r.ev, r.z), big = r.s !== 'IMPOSSIBLE' && p.pct >= 15 ? ' big' : '';
      out.push(link({ k: 'zone', ev: r.ev, i: r.i }, '<span class="t"><span><span class="zt">' + clk(r.z.time_start) + '–' + clk(r.z.time_end) + '</span> <i class="zn" style="color:' + cfg[r.ev] + '">' + r.z.label + '</i></span>' +
        '<span class="p21-sub">' + band(r.z.price_low, r.z.price_high) + ' SD · ' + ZST[r.s] + '</span></span><b class="zp' + big + '">' + ppTxt(p) + '</b>', 'mc zst-' + r.s, p, plainTitle(p)));
    }
    if (!sep) out.push('<div class="p24-now"><span></span>' + (sl >= F.end ? 'блок закончен' : 'сейчас ' + clk(sl)) + '<span></span></div>');
    // the rest of each event's 100 %: outside the zones, and not determined (never drawn at any price)
    for (const ev of ['X', 'R']) {
      const Zm = zonesOf(F, ev), D = F.ev[ev];
      if (Zm) {
        const r = pp(F, { event_id: ev, region_kind: 'residual', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end),
          yes_count: Zm.n_residual_total, display_scope: 'zone', phrase: F.names[ev].toLowerCase() + ' ' + ev + ' вне зон (остаток распределения)', horizon: F.from + ' до ' + clk(F.end) });
        out.push(link({ k: 'evrow', ev }, prow('<i style="color:' + cfg[ev] + '">' + ev + '</i> вне зон', pct(r.pct)), 'dim', r, plainTitle(r)));
      }
      if (D.unknown + D.none) {
        const u = pp(F, { event_id: ev, region_kind: 'unknown', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end), yes_count: D.unknown + D.none, display_scope: 'panel',
          phrase: F.names[ev].toLowerCase() + ' ' + ev + ' не определено (нет свечи M5 на горизонте' + (D.none ? ' или нет периода' : '') + '); на графике не рисуется', horizon: F.from + ' до ' + clk(F.end) });
        out.push(link({ k: 'evrow', ev }, prow('<i style="color:' + cfg[ev] + '">' + ev + '</i> не определено · нет свечи M5', pct(u.pct)), 'dim', u, plainTitle(u)));
      }
    }
    return out.join('');
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
    return '<div class="p21-h second">DR до ' + clk(F.end) + '<span>доля всей семьи</span></div>' + bar + '<div class="p24-out big">' + rows + '</div>';
  }
  function areaHtml(F, ctx) {
    const I = areaInfo(F, ctx), out = ['<div class="p21-h second p24-sel">Выбранная область <span><button class="p24-x" data-clear="area" title="Снять выбор (Esc)">✕</button></span></div>'];
    out.push('<div class="p21-note"><b style="color:#D1D4DC;font-weight:600">' + esc(I.name) + '</b>' + (I.prices ? ' · ' + px(I.prices[0]) + ' – ' + px(I.prices[1]) + ' · ' + esc(where(ctx.s, (I.prices[0] + I.prices[1]) / 2)) : '') + '</div>');
    if (I.band) out.push(link({ k: 'area', part: 'band' }, prow('<i style="color:' + cfg[I.ev] + '">' + I.ev + '</i> в полосе за всю сессию', ppTxt(I.band)), '', I.band, plainTitle(I.band)));
    if (I.win) out.push(link({ k: 'area', part: 'window' }, prow('<i style="color:' + cfg[I.ev] + '">' + I.ev + '</i> в выбранном окне', ppTxt(I.win)), '', I.win, plainTitle(I.win)));
    if (I.vfull) {
      out.push(link({ k: 'area', part: 'visit' }, prow('заходили в полосу · вся сессия', ppTxt(I.vfull, true)), 'dim', I.vfull, plainTitle(I.vfull)));
      out.push(link({ k: 'area', part: 'visit' }, prow('заходили в полосу · ' + (ctx && sliceOf(ctx) >= F.end ? 'остатка нет' : 'после ' + clk(sliceOf(ctx))), ppTxt(I.vrest, true)), 'dim', I.vrest, plainTitle(I.vrest)));
    }
    if (I.today) out.push('<div class="p21-note">' + esc(I.today) + '</div>');
    return out.join('');
  }
  function levelHtml(F, ctx, l) {
    const q = levelQuery(F, ctx, l.p, l.type === 'std' ? l.name : l.full), sl = sliceOf(ctx);
    return '<div class="p21-h second p24-sel">Уровень <span>' + esc(l.type === 'std' ? l.name : l.full) + ' · ' + px(l.p) + ' <button class="p24-x" data-clear="pin" title="Снять (Esc)">✕</button></span></div>' +
      link({ k: 'lvl', id: l.id, l }, prow('дальше ' + dirName(F, q.up) + ' · вся сессия', ppTxt(q.full, true)), '', q.full, plainTitle(q.full)) +
      link({ k: 'lvl', id: l.id, l }, prow('дальше ' + dirName(F, q.up) + ' · ' + (sl >= F.end ? 'остатка нет' : 'после ' + clk(sl)), ppTxt(q.rest, true)), '', q.rest, plainTitle(q.rest)) +
      '<div class="p21-note">' + esc(q.today) + '</div>';
  }
  function memberHtml(F, m) {
    const ev = e => m[e].s === 'known' ? sd(m[e].v / m.w) + ' SD · ' + px(F.u2p(m[e].v / m.w)) + ' · ' + clk(m[e].t) : 'неизвестно';
    return '<div class="p21-h second p24-sel">Сессия семьи <span>' + esc(memberLine(F, m)) + ' <button class="p24-x" data-clear="pin" title="Снять (Esc)">✕</button></span></div>' +
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
    const b = p.exact_price_bounds;
    return dRow('событие', esc(p.phrase)) + dRow('горизонт', esc(p.horizon)) +
      (b && b.length === 2 && typeof b[0] === 'number' ? dRow('цена', band(b[0], b[1]) + ' SD <span class="k">[' + b[0] + '/10; ' + b[1] + '/10)</span>') : b && b.length === 1 ? dRow('уровень', sd(p.level_sd) + ' SD <span class="k">точно u = ' + b[0] + ' ширины IDR от края</span>') : '') +
      (p.time_bounds ? dRow('время', clk(p.time_bounds[0]) + '–' + clk(p.time_bounds[1])) : '') +
      dRow('доля', ppTxt(p, p.binary) + (p.pct != null ? ' <span class="k">(' + pct2(p.pct) + ')</span>' : '')) +
      (p.unknown_count ? dRow('неизвестно', pct(100 * p.unknown_count / p.N) + (p.binary ? '' : ' <span class="k">граница: до ' + pct(100 * (p.yes_count + p.unknown_count) / p.N) + '</span>')) : '') +
      dRow('знаменатель', 'вся семья, шаг доли ' + pct(100 / p.N));
  }
  // the passport of a zone (zone-map-3 §40) and its diagnostics: properties of the zone, never a permission to exist;
  // the study figures are research, not a chance for today
  function zoneRows(F, ctx, ev, i) {
    const Zm = zonesOf(F, ev), z = Zm.zones[i], s = zoneStatus(F, ctx, ev)[i], sh = n => pct(100 * n / F.N);
    return dRow('зона', esc(z.label + ' · ' + z.zone_id + ' · ' + z.algorithm_version)) +
      dRow('семья', esc((z.family_scope === 'all' ? 'все дни недели' : 'день недели') + ' · ' + F.cond)) +
      dRow('область', z.cell_mask.length + ' клеток 0,1 SD × 15 мин <span class="k">рамка ' + band(z.price_low, z.price_high) + ' SD × ' + clk(z.time_start) + '–' + clk(z.time_end) + '; членство — сами клетки</span>') +
      dRow('вершина', 'клетка ' + band(z.peak_anchor[0], z.peak_anchor[0] + 1) + ' SD × ' + clk(F.f + 15 * z.peak_anchor[1]) + '–' + clk(F.f + 15 * z.peak_anchor[1] + 15)) +
      dRow('доля семьи', pct(100 * z.p_snapshot) + ' <span class="k">шаг доли ' + pct(100 / F.N) + '; неизвестно у ' + sh(Zm.unknown_count) + ', нет периода у ' + sh(Zm.no_event_count) + '; вне зон ' + sh(Zm.n_residual_total) + '</span>') +
      dRow('сегодня', ZST[s] + ' <span class="k">по сегодняшнему экстремуму после ' + (F.brk ? 'слома' : 'подтверждения') + ' и времени; не вероятность</span>') +
      dRow('слепок', esc(z.snapshot_id + ' · семья ' + z.family_id));
  }
  function zoneDiag(F, ev, z) {
    const g = z.grid_member_jaccard, b = z.bootstrap_recovery, f2 = v => v == null ? '—' : num(v, 2);
    let s = dRow('сдвиг сетки', 'те же сессии на 0,05 SD — ' + f2(g.price_half) + ', на 5 мин — ' + f2(g.time_5) + ', на 10 мин — ' + f2(g.time_10) + ' <span class="k">Жаккар множеств сессий; 1 — та же зона</span>') +
      dRow('пересэмплирование', 'в среднем ' + f2(b.mean) + ', не меньше 0,5 — в ' + (b.share_ge_half == null ? '—' : pct(100 * b.share_ge_half)) + ' из ' + b.of + ' повторов');
    if (z.null_status === 'measured') {
      s += dRow('путь без направления', 'реальные ' + pct(100 * z.p_real_mask) + ', без направления ' + pct(100 * z.p_null_mask) +
        ' · избыток ' + (z.null_excess >= 0 ? '+' : '−') + num(Math.abs(100 * z.null_excess), 1) + ' п.п. <span class="k">различим с ' + num(100 * z.minimum_detectable_excess, 1) + ' п.п.</span>');
    } else s += dRow('путь без направления', '<span class="k">' + esc(z.null_status.replace('not_applicable: ', 'не считается: ')) + '</span>');
    if (z.study_refs) s += dRow('исследование', '<span class="k">' + esc(z.study_refs.text) + '</span>');
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
        dRow('слепок', esc(r.snapshot_id + ' · семья ' + r.family_id + ' · ' + r.semantics)) + dRow('шаг доли', pct(100 / F.N)) };
    }
    if (o.k === 'pt') {
      const m = F.M[o.i];
      return { head: 'Сессия ' + memberLine(F, m), body: dRow(F.names.R.toLowerCase() + ' R', m.R.s === 'known' ? sd(m.R.v / m.w) + ' SD · ' + clk(m.R.t) + (m.R.ties.length > 1 ? ' · та же цена ещё ' + m.R.ties.slice(1).map(clk).join(', ') : '') : 'неизвестно') +
        dRow(F.names.X.toLowerCase() + ' X', m.X.s === 'known' ? sd(m.X.v / m.w) + ' SD · ' + clk(m.X.t) + (m.X.ties.length > 1 ? ' · та же цена ещё ' + m.X.ties.slice(1).map(clk).join(', ') : '') : 'неизвестно') +
        dRow('порядок', esc(orderText(F, m))) + (F.brk ? '' : dRow('DR', m.outcome === 'broken' ? 'сломан ' + (m.brkKnown ? clk(m.brk) : '') : m.outcome === 'held' ? 'удержался до ' + clk(F.end) : 'неизвестно')) +
        dRow(F.brk ? 'слом' : 'подтверждение', clk(m.act)) + (m.missing ? dRow('нет свечей', m.missing + ' M5 на горизонте') : '') };
    }
    if (o.k === 'lvl' && o.l) {
      const q = levelQuery(F, ctx, o.l.p, o.l.type === 'std' ? o.l.name : o.l.full);
      return { head: 'Уровень ' + (o.l.type === 'std' ? o.l.name : o.l.full), body: passportRows(q.full) + dRow('после среза', ppTxt(q.rest, true) + ' <span class="k">' + esc(q.rest.horizon) + '</span>') +
        dRow('пересекали свечой', ppTxt(q.cross, true) + ' <span class="k">другое событие: минимум ≤ уровня ≤ максимум одной M5</span>') + dRow('сегодня', esc(q.today.replace(/^сегодня: /, ''))) };
    }
    if (o.k === 'area' && st.area) {
      const I = areaInfo(F, ctx);
      return { head: 'Область ' + I.name, body: (I.band ? passportRows(I.band) : '') + (I.win ? dRow('в окне', ppTxt(I.win) + ' <span class="k">' + esc(I.win.phrase) + '</span>') : '') +
        (I.vfull ? dRow('заходили', ppTxt(I.vfull, true) + ' вся сессия · ' + ppTxt(I.vrest, true) + ' ' + esc(I.vrest.horizon)) : '') + (I.today ? dRow('сегодня', esc(I.today.replace(/^сегодня: /, ''))) : '') };
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
        const list = cd.cells.get(o.kk) || [], rf = rangeField(F, o.j, o.kk);
        return { head: 'M5 ' + clk(cd.T - 5) + '–' + clk(cd.T), body: passportRows(pp(F, { event_id: 'close_M5', region_kind: 'M5_cell', exact_price_bounds: [o.kk, o.kk + 1], time_bounds: [cd.T - 5, cd.T], start_rule: 'M5 ' + clk(cd.T - 5), end_rule: clk(cd.T),
          yes_count: list.length, unknown_count: cd.unknown, display_scope: 'details', phrase: 'закрытие M5 в полосе ' + band(o.kk, o.kk + 1) + ' SD', horizon: 'на пятиминутке ' + clk(cd.T - 5) + '–' + clk(cd.T) })) +
          dRow('задевали диапазоном', pct(100 * rf.n / F.N) + ' <span class="k">поле диапазонов V: свеча M5 задевала полосу; не закрытие</span>') };
      }
      return { head: 'M5 ' + clk(cd.T - 5) + '–' + clk(cd.T), body: dRow('колонка', 'закрытия семьи на этой M5; своя сотня процентов') + dRow('нет свечи', pct(100 * cd.unknown / F.N)) };
    }
    if (o.k === 'out') {
      const nm = { held: 'удержался', broken: 'сломан', unknown: 'неизвестно', none: 'нет периода' }[o.cat];
      return { head: 'Исход DR', body: dRow('категория', nm) + dRow('доля', pct(100 * F.out[o.cat] / F.N)) + dRow('правило', 'закрытие M5 строго за своим противоположным DR; тень и равенство не ломают; слом не отменяется возвратом') + dRow('горизонт', F.from + ' до ' + clk(F.end)) };
    }
    if (o.k === 'zone' && zonesOf(F, o.ev) && zonesOf(F, o.ev).zones[o.i]) {
      const z = zonesOf(F, o.ev).zones[o.i];
      return { head: 'Зона ' + z.label + ' · ' + zoneName(z), body: zoneRows(F, ctx, o.ev, o.i) + '<div class="p24-sep"></div>' + zoneDiag(F, o.ev, z) };
    }
    if (o.k === 'evrow') {
      const ev = o.ev || st.ev, D = F.ev[ev];
      return { head: F.names[ev] + ' ' + ev, body: dRow('событие', esc(F.what[ev])) + dRow('определено', pct(100 * D.known / F.N)) + dRow('неизвестно', pct(100 * D.unknown / F.N) + ' <span class="k">нет свечи M5 на горизонте</span>') + (D.none ? dRow('нет периода', pct(100 * D.none / F.N)) : '') + dRow('горизонт', F.from + ' до ' + clk(F.end)) };
    }
    return detBody(ctx, null);
  }
  // window 4: what came first in each session, its first R or its first X (spec §8); one 100 %
  function orderHtml(F) {
    const n = { X_before_R: 0, R_before_X: 0, same_M5: 0, unknown: 0 };
    for (const m of F.M) n[n[m.order] != null ? m.order : 'unknown']++;
    const rows = [['X_before_R', 'сначала максимум X, потом глубочайший R', cfg.X], ['R_before_X', 'сначала глубочайший R, потом максимум X', cfg.R], ['same_M5', 'в одной M5: порядок внутри свечи неизвестен', '#8C929D'], ['unknown', 'неизвестно: событие не определено', '#4A505B']];
    const P = rows.map(([k, t]) => pp(F, { event_id: 'order_' + k, region_kind: 'order', exact_price_bounds: null, time_bounds: null, start_rule: F.from, end_rule: 'до ' + clk(F.end), yes_count: n[k], display_scope: 'details', phrase: 'порядок первых R и X: ' + t, horizon: F.from + ' до ' + clk(F.end) }));
    return '<div class="p24-bar wide">' + rows.map(([k, , c]) => n[k] ? '<i style="width:' + (100 * n[k] / F.N).toFixed(2) + '%;background:' + c + '"></i>' : '').join('') + '</div>' +
      rows.map(([k, t, c], j) => '<div class="dq" title="' + esc(plainTitle(P[j])) + '"><i style="background:' + c + '"></i><span>' + t + '</span><b>' + pct(P[j].pct) + '</b></div>').join('');
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
      rows.push('<div class="dl" title="' + esc(plainTitle(q.full)) + '"><span class="n">' + esc(l.type === 'std' ? 'STD ' + l.name : nm) + (tk ? ' <em>✓ ' + clk(tk.t) + '</em>' : '') + '</span><span class="b"><i style="width:' + (q.full.pct || 0).toFixed(1) + '%;background:' + rgba(col, 0.35) + '"></i><i style="width:' + (q.rest.pct || 0).toFixed(1) + '%;background:' + rgba(col, 0.9) + '"></i></span><b>' + ppTxt(q.full, true) + '</b><span class="r" style="color:' + col + '">' + ppTxt(q.rest, true) + '</span></div>');
    }
    return '<div class="dlh"><span></span><span>вся сессия</span><span>после ' + clk(sl) + '</span></div>' + rows.join('');
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
    for (const q of cells) { if (q.k < k0 || q.k >= k1) continue; c.fillStyle = rgba(cfg[ev], 0.18 + 0.82 * Math.pow(q.list.length / mx, 0.7)); c.fillRect(X(q.b) + 0.5, Y(q.k) + 0.25, Math.max(1, cw - 1), Math.max(1, rh - 0.5)); }
    const Zm = F.zones[ev];
    if (Zm) Zm.zones.forEach(z => {
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
    det.addEventListener('mouseleave', () => { st.detOver = false; render(false); });
    dom('deth').addEventListener('click', () => { st.detPin = !st.detPin; render(false); });
    new ResizeObserver(() => redraw(true)).observe(cv);
  }
