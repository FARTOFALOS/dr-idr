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
