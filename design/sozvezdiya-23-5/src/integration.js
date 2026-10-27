  // One publication scene; accepted SC11 remains the registry of BASE/NOW. Review profiles have their own edition.
  const ICFG = window.DR_INTEGRATION || { enabled: false }, REVIEW = ICFG.registry;
  // phase / nowmarks: the operator's decisions of 2026-10-08 (meaning/17 §7) on the page only, over accepted bundles and the
  // candidate labels FF:PHASE-RULE, row_mark / title_mark (integration/candidates/registry/40-claims.yaml); no server call
  // The old broad PB overlay is superseded by the explicitly approved time x SD profile of 23.5.
  // Legacy flags cannot reinstate that overlay; the new profile is the normal bounds view.
  // Operator 2026-10-26: on 23.5 the decisions of 08.10 are on by default (before confirmation, «Сейчас» as a number with
  // marks, the phase rule as two facts); screen 24 keeps them off. «ON_0810» switches them on once over an older saved choice.
  const TRIAL = { pre: !!ICFG.enabled, arrive: false, paths: false, continuations: !!ICFG.enabled, phase: !!ICFG.enabled, nowmarks: !!ICFG.enabled, pullbacks: false };
  // the viewer's own choice of trials is kept in this browser like every other setting (2026-10-19); the address still adds
  const TRIAL_KEY = 'drlab.d235.trials', ON_0810 = 'drlab.d235.trials.on0810';
  if (ICFG.enabled) try {
    const kept = JSON.parse(localStorage.getItem(TRIAL_KEY) || '{}');
    if (localStorage.getItem(ON_0810) == null) { for (const k of ['pre', 'phase', 'nowmarks']) delete kept[k]; localStorage.setItem(ON_0810, '1'); }
    for (const k in TRIAL) if (k !== 'pullbacks' && typeof kept[k] === 'boolean') TRIAL[k] = kept[k];
    if (kept.pullbacks) {
      if (localStorage.getItem(TRIAL_KEY+'.before-withdrawal') == null) localStorage.setItem(TRIAL_KEY+'.before-withdrawal',JSON.stringify(kept));
      localStorage.setItem(TRIAL_KEY,JSON.stringify({...kept,pullbacks:false}));
    }
  } catch (e) { /* defaults */ }
  if (ICFG.enabled) for (const k of (new URLSearchParams(location.hash.slice(1)).get('trial') || '').split(',')) if (k in TRIAL && k !== 'pullbacks') TRIAL[k] = true;
  {
    const q=new URLSearchParams(location.hash.slice(1)),before=q.toString();
    const active=(q.get('trial')||'').split(',').filter(k=>k&&k!=='pullbacks');
    if(active.length)q.set('trial',active.join(','));else q.delete('trial');
    if(q.get('mode')==='pullbacks')q.delete('mode');
    // The locality scale remains an explicit parameter of the new profile.
    if(q.toString()!==before)history.replaceState(null,'',location.pathname+location.search+(q.toString()?'#'+q:''));
  }
  if (ICFG.enabled) window.addEventListener('hashchange',()=>location.reload());
  const IS = { key: null, packet: null, pending: new Set(), cache: new Map(), error: null, discarded: 0, committed: 0, selection: null, epoch: 0 };
  function sceneRequest() {
    const D = day(), obs = st.rp != null ? st.rp : NOW, s = sess(D, st.session, obs, st.rp == null);
    const cut = Math.floor(obs / 5) * 5, trials = ['pre', 'arrive'].filter(k => TRIAL[k]);
    return { D, s, cut, view: wantView(s), trials,
      key: [IS.epoch,A.inst, A.src, A.src === 'hist' ? A.date : D.iso, st.session, cut, wantView(s), st.scope, trials.join(',')].join('|') };
  }
  const intentContext = ctx => [A.inst, ctx.D.iso, ctx.s.k, st.scope, ctx.F && ctx.F.r.family_id].join('|');
  function scenePacket() { const q = sceneRequest(); return IS.key === q.key ? IS.packet : null; }
  function requestScene() {
    if (!ICFG.enabled || !A.day || A.day.status !== 'ok') return;
    const q = sceneRequest();
    if (IS.key === q.key && IS.error) return;
    if (IS.key === q.key && IS.packet || IS.pending.has(q.key)) return;
    if (IS.key !== q.key) { IS.error = null; IS.key = q.key; IS.packet = null; }
    IS.pending.add(q.key);
    const query = new URLSearchParams({ instrument: A.inst, session: q.s.k, at: q.cut, view: q.view, scope: st.scope, trials: q.trials.join(',') });
    if (A.src === 'hist') query.set('date', A.date);
    fetch('/api/integration/scene?' + query).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(r => {
      if (q.key !== sceneRequest().key) { IS.discarded++; return; }
      if (r.status !== 'OK' || !r.context || r.context.instrument !== A.inst || r.context.date !== q.D.iso || r.context.session !== q.s.k || r.context.cut !== q.cut || r.context.scope !== st.scope) throw new Error(r.message || 'Ответ другого состояния');
      if (r.context.registry_hash !== SC11.registry_hash) throw new Error('Реестр сцены отличается от страницы');
      const prefix = q.D.bars.filter(b => b.t + 5 <= q.cut).map(b => [b.t, b.o, b.h, b.l, b.c]);
      const received = r.day.bars.filter(b => b[0] + 5 <= q.cut);
      if (JSON.stringify(prefix) !== JSON.stringify(received)) throw new Error('Свечи сцены отличаются от видимого префикса');
      const fam = r.family, fk = famKey(q.D, q.s, fam.view || q.view);
      if (fam.status === 'ok' && (fam.today.slice !== q.cut || fam.today.c0 !== q.s.conf || fam.today.side !== q.s.side)) throw new Error('Другая активация сцены');
      if(r.now?.cut){const expected=r.now.status==='FROZEN_AT_BREAK'?q.s.failed-5:q.cut;if(r.now.cut.cut!==expected||r.now.cut.family_id!==fam.family_id||r.now.cut.snapshot_id!==fam.snapshot_id)r.now={status:'ERROR',message:'Ответ «Сейчас» относится к другой семье или срезу'};}
      for(const [name,child] of Object.entries(r.candidates)){
        const valid=name==='arrive'?child.status!=='OK'||child.cut?.cut===q.cut&&child.family_id===fam.family_id&&child.snapshot_id===fam.snapshot_id&&child.scope===st.scope:
          child.status!=='ok'||q.s.status==='waiting'&&child.key?.cut===q.cut&&child.key?.scope===st.scope;
        if(!valid)r.candidates[name]={status:'CONTEXT_MISMATCH',message:'Кандидатный ответ относится к другому состоянию'};
      }
      fam._fk = fk; fam._ctx = 'scene|' + r.context.id + '|' + (A.respSeq = (A.respSeq || 0) + 1);
      A.fams.set(fk, fam);
      if (r.now) { r.now._ctx = fam._ctx + '|now'; A.now.set(fk + '|' + q.cut, r.now); }
      for (const k of ['pre', 'arrive']) if (r.candidates[k]) r.candidates[k]._ctx = fam._ctx + '|' + k;
      IS.packet = r; IS.key = q.key; IS.error = null; IS.committed++;
      if (st.pin && st.pin.context && st.pin.context !== intentContext({ D: q.D, s: q.s, F: fam.status === 'ok' ? { r: fam } : null })) { st.pin = null; st.hover = null; }
      if (st.pin && st.pin.k === 'pre' && q.s.status !== 'waiting') { st.pin = null; st.hover = null; }
    }).catch(e => { if (q.key === sceneRequest().key) { IS.packet = null; IS.error = e.message; } })
      .finally(() => { IS.pending.delete(q.key); redraw(true); });
  }
  function candidateOf(name) { if (!ICFG.enabled || !TRIAL[name]) return null; requestScene(); return scenePacket()?.candidates[name] || null; }
  const preOf = ctx => ctx.s.status === 'waiting' ? candidateOf('pre') : null;
  const arriveOf = ctx => ctx.F && ctx.s.conf ? candidateOf('arrive') : null;
  function reviewFault(r) {
    if (!REVIEW || !r || !r.contract) return 'Нет проверенного ответа';
    if (r.review?.decision !== 'CANDIDATE' || r.contract.edition !== REVIEW.edition || r.contract.registry_hash !== REVIEW.registry_hash) return 'Другая редакция испытания';
    if (r.contract.status !== 'CONFORMANT') return 'Число не опубликовано: ' + r.contract.status;
    return null;
  }
  function preBundle(r, est, side) {
    if (reviewFault(r)) return null;
    const f = REVIEW.forms[est], b = r.contract.bundles.find(x => x.estimand === est && (side == null || parOf(x).side === side));
    if (!b || !f || b.claim_form !== f.id || b.claim.claim_class !== f.claim_class || !b.admissible_claims.includes(f.claim_class)) return null;
    if (est === 'EST:P-DIR' && b.estimates[0].denominator !== r.N) return null;
    return b;
  }
  function arriveBundle(r, level, P) {
    if (reviewFault(r) || !P?.counts) return null;
    const f = REVIEW.forms['EST:K-ARRIVE'], b = r.contract.bundles.find(x => x.estimand === 'EST:K-ARRIVE' && parOf(x).level === level);
    if (!b || b.claim_form !== f.id || b.claim.claim_class !== f.claim_class || !b.admissible_claims.includes(f.claim_class)) return null;
    const k = P.counts, pt = b.estimates.find(x => x.value_kind === 'POINT'), bd = b.estimates.find(x => x.value_kind === 'BOUNDS');
    const sp = b.supports[0] || {}, cm = (sp.components || [])[0] || {};
    if ((pt ? pt.numerator !== k.yes || pt.denominator !== k.n_known : k.n_known) || !bd || bd.denominator !== k.n_match ||
      sp.n_eligible !== k.N_eligible || sp.n_base !== r.N_parent || cm.yes !== k.yes || cm.no !== k.no || cm.unknown !== k.unknown ||
      b.claim.selected_case_set !== (r.scope === 'all' ? 'CS:K-ARRIVE-ALL-1' : 'CS:K-ARRIVE-1')) return null;
    if(Math.abs(bd.lower-k.yes/k.n_match)>1e-12||Math.abs(bd.upper-(k.yes+k.unknown)/k.n_match)>1e-12||pt&&Math.abs(pt.value-k.yes/k.n_known)>1e-12)return null;
    return b;
  }
  // the standing of a candidate where it is shown (FF:CANDIDATE-STATUS, operator 2026-10-19): a candidate block or a trial
  // form is never read as an accepted function of the screen; panel only, nothing over the chart
  function candTag() { return ' <i class="p24-cand" title="' + esc(lbl('FF:CANDIDATE-STATUS', 'title')) + '">' + lbl('FF:CANDIDATE-STATUS', 'tag') + '</i>'; }
  const arrPlace = (r, level) => r?.places?.find(p => p.level === level) || null;
  const placeName = level => lbl('EST:K-ARRIVE', level === '0' ? 'p0' : level === '-1/2' ? 'p12' : 'p710');
  function arrivalValue(r, P) {
    if (!P || P.state.status !== 'OPEN' || P.publication !== 'PUBLISHED' || !arriveBundle(r, P.level, P)) return '—';
    const k = P.counts; return k.unknown ? pct(100 * k.yes / k.n_match) + '–' + pct(100 * (k.yes + k.unknown) / k.n_match) : pct(100 * k.yes / k.n_match);
  }
  function arrivalFact(level) { return scenePacket()?.target_facts?.[level] || null; }
  function factText(f) { return f?.reached === 'YES' ? (f.time_known ? lbl('FF:K-TARGET', 'RESOLVED', { time: clk(f.bar_close) }) : lbl('FF:K-TARGET','RESOLVED_TIME_UNKNOWN')) : ''; }
  function candidatePanel(ctx) {
    if (!ICFG.enabled) return '';
    return pbEntry() + candidateRows(ctx);
  }
  function candidateRows(ctx) {
    if (TRIAL.pre && ctx.s.status === 'waiting') {
      const r = preOf(ctx), b = r && preBundle(r, 'EST:P-DIR');
      let out = '<div class="p24-pre"><div class="p21-h second"><span class="p24-ht">' + lbl('EST:P-DIR', 'head') + candTag() + '</span>' + scopeSwitch() + '</div>';
      if (!b) return out + '<div class="p21-note">' + esc(IS.error || r?.message || 'Подбираю похожие сессии…') + '</div></div>';
      if (!r.N) return out + '<div class="p21-note">' + lbl('EST:P-DIR','zero') + '</div></div>';
      if (r.few) out += '<div class="p21-note">мало сессий</div>';
      for (const x of b.estimates[0].categories) out += link({ k: 'pre', id: x.category }, prow(lbl('EST:P-DIR', x.category), pct(100 * x.count / r.N)), 'in', null, lbl('EST:P-DIR', 'title', { cut: clk(ctx.obs), n: r.N })).replace('data-l21=','data-bundle="'+b.id+'" data-edition="'+REVIEW.edition+'" data-l21=');
      return out + '</div>';
    }
    if (!TRIAL.arrive || !ctx.F) return '';
    const r = arriveOf(ctx), out = ['<div class="p24-arrblk"><div class="p21-h second" title="' + esc(lbl('EST:K-ARRIVE', 'head_title')) + '"><span class="p24-ht">' + (ctx.s.failed?lbl('FF:K-TARGET','ORIGINAL_PLACES'):lbl('EST:K-ARRIVE', 'head')) + candTag() + '</span></div>'];
    if (!r) return out.join('') + '<div class="p21-note">' + esc(IS.error || 'Сопоставляю историю…') + '</div></div>';
    if (r.status !== 'OK') out.push('<div class="p21-note">' + esc(REVIEW.facts['FF:K-TARGET'].labels[r.status] ? lbl('FF:K-TARGET', r.status, { time: r.time || (ctx.s.failed ? clk(ctx.s.failed) : '') }) : r.message || r.status) + '</div>');
    for (const level of ['0', '-1/2', '-7/10']) {
      const P = arrPlace(r, level), f = arrivalFact(level);
      if (!P && !factText(f)) continue;
      const title = factText(f) || (P?.publication === 'WITHHELD_FEW_SESSIONS' ? 'мало сессий' : P?.publication === 'NO_KNOWN_OUTCOME' ? lbl('FF:K-TARGET', 'none_known') : P?.publication==='PUBLISHED'&&!arriveBundle(r,P.level,P)?lbl('FF:K-TARGET','withheld'):'');
      let row=link({ k: 'arrive', id: level, ev: 'R', context: intentContext(ctx) }, '<span class="t">' + placeName(level) + (title ? '<span class="p21-sub">' + esc(title) + '</span>' : '') + '</span><b>' + (factText(f) ? '✓' : arrivalValue(r, P)) + '</b>', 'in', null, lbl('EST:K-ARRIVE', 'head_title'));
      const bound=P?.publication==='PUBLISHED'&&arriveBundle(r,level,P);
      if(bound)row=row.replace('data-l21=','data-bundle="'+bound.id+'" data-edition="'+REVIEW.edition+'" data-l21=');
      out.push(row);
    }
    return out.join('') + '</div>';
  }
  function candidateTip(h, ctx) {
    if (h.k === 'pre') {
      const r = preOf(ctx), b = r && preBundle(r, 'EST:P-DIR');
      if (!b) return esc(IS.error || 'Ответ не опубликован');
      if (!r.N || !b.estimates[0].categories) return lbl('EST:P-DIR','zero');
      const x = b.estimates[0].categories.find(x => x.category === h.id);
      let html = '<div class="ih">' + lbl('EST:P-DIR', h.id) + '</div><div class="is">' + lbl('EST:P-DIR', 'title', { cut: clk(ctx.obs), n: r.N }) + '</div><b>' + pct(100 * x.count / r.N) + '</b>';
      if (h.id==='LONG'||h.id==='SHORT') {
        const when=preBundle(r,'EST:P-WHEN',h.id),dr=preBundle(r,'EST:P-DR',h.id);
        if(when){const e=when.estimates[0],top=e.categories.reduce((a,b)=>a.count>=b.count?a:b);html+='<div class="is" title="'+esc(when.claim.statement_ru)+'">'+lbl('EST:P-WHEN','when',{window:top.category,k:top.count,n:e.denominator})+'</div>';}
        if(dr){const e=dr.estimates[0],held=e.categories.find(x=>x.category==='HELD');html+='<div class="is" title="'+esc(dr.claim.statement_ru)+'">'+lbl('EST:P-DR','dr',{held:held?.count||0,n:e.denominator})+'</div>';}
        for(const ev of ['R','X']){const b=preBundle(r,'EST:P-'+ev,h.id),q=b?.estimates[0]?.quantiles?.find(x=>x.quantile===.5);if(q)html+='<div class="is" title="'+esc(b.claim.statement_ru)+'">'+lbl('EST:P-'+ev,ev==='R'?'r':'x',{q50:sd(q.value)})+'</div>';}
      }
      return html+'<div class="is">' + (r.few ? 'мало сессий · ' : '') + 'кандидат · приёмка не проведена</div>';
    }
    const r = arriveOf(ctx), P = arrPlace(r, h.id), k = P?.counts, f = arrivalFact(h.id), name = placeName(h.id);
    if (!r) return esc(IS.error || 'Сопоставляю историю…');
    let out = '<div class="ih">' + lbl('EST:K-ARRIVE', 'win_head', { place: name, price: px(ctx.s.price((h.id === '0' ? 0 : h.id === '-1/2' ? -.5 : -.7))) }) + '</div>';
    if (factText(f)) out += '<div class="is">' + esc(factText(f)) + (f.time_known ? ' · M5 ' + clk(f.bar_open) + '–' + clk(f.bar_close) : '') + '</div>';
    if (!k) return out + '<div class="is">' + esc(r.status === 'OK' ? 'Вопрос решён фактом' : r.message || r.status) + '</div>';
    out += '<div class="is">' + lbl('EST:K-ARRIVE', 'win_q_v', { cut: r.cut.cut_clock_et, end: r.cut.horizon_end }) + '</div>';
    out += '<div class="is">' + lbl('EST:K-ARRIVE', 'win_chain_v', { eligible: k.N_eligible, notyet: k.N_not_yet, n: k.n_match }) + '</div>';
    out += '<div class="is">' + lbl('EST:K-ARRIVE', 'win_out_v', k) + '</div><b>' + arrivalValue(r, P) + '</b>';
    if (P.publication === 'PUBLISHED' && !arriveBundle(r,P.level,P)) out += '<div class="is">' + lbl('FF:K-TARGET','withheld') + '</div>';
    else if (P.publication !== 'PUBLISHED') out += '<div class="is">' + (P.publication === 'WITHHELD_FEW_SESSIONS' ? 'мало сессий: n=' + k.n_match : lbl('FF:K-TARGET', 'none_known')) + '</div>';
    out += '<div class="is">' + lbl('EST:K-ARRIVE', 'win_ad_' + (r.evidence.ad_target_domain && r.cut.on_ad_15min_grid ? 'in' : 'out')) + '</div>';
    return out + '<div class="is">кандидат · ' + lbl('EST:K-ARRIVE', r.scope) + ' · приёмка не проведена</div>';
  }
  function candidateSelection(ctx, h) {
    if (!h || h.k !== 'arrive' || !ctx.F || h.context !== intentContext(ctx)) return null;
    const r = arriveOf(ctx), P = arrPlace(r, h.id), ready = !!(P && P.state.status === 'OPEN' && P.publication === 'PUBLISHED' && arriveBundle(r, h.id, P));
    return { r, P, ready, members: ready ? P.members : [], ids: ready ? new Set(P.members.map(x => x[0])) : new Set() };
  }
  function candidateEmphasis(q, h, F, ctx) {
    const a = candidateSelection(ctx, h); return a ? a.ready ? q.ev === 'R' && a.ids.has(q.m.id) : null : null;
  }
  function candidateHighlight(c, ctx, h) {
    const a = candidateSelection(ctx, h); IS.selection = null;
    if (!a?.ready) return;
    const p = ctx.s.price(a.P.a / a.P.b), y = V.Y(p);
    c.strokeStyle = rgba(cfg.R, .9); c.lineWidth = 1; c.setLineDash([5, 4]); c.beginPath(); c.moveTo(0, y); c.lineTo(V.plot.w, y); c.stroke(); c.setLineDash([]);
    V.win = { pA: p, pB: p, t0: null, t1: null, col: cfg.R };
    IS.selection = { context: scenePacket().context.id, level: h.id, price: p, ids: [...a.ids], bundle: arriveBundle(a.r, h.id, a.P).id };
  }
  function candidateDetails(ctx, o) { return o?.k === 'arrive' ? { head: lbl('EST:K-ARRIVE', 'head'), body: candidateTip(o, ctx) } : null; }
  // ---------- the operator's decisions of 2026-10-08 (meaning/17 §7), on screen as trials since 2026-10-19 ----------
  // They existed only as candidate definitions (integration/pr-dispositions.json U03, U04). Page only: accepted bundles
  // and passports, candidate words; nothing is computed on the server for them.
  // The named phase rule (FF:PHASE-RULE): «откат сделан» when today's deepest point after the activation reached the
  // retirement zone (−0.7) AND at least half of the family's sessions had their final R earlier than the cut by the common
  // clock (known, of N: EST:B-CLOCK-R over the whole price range, part EARLIER, a passport the server verifies). A rule
  // of the operator, not a statement about the market; only for the confirmation family (a break is another frame)
  // Operator 2026-10-26: the screen shows what was, it does not switch sides by a rule. On 23.5 the rule is its two facts
  // with today's values; no «откат сделан» verdict and no quieter side (phaseK = 1).
  function phaseOf(F, ctx) {
    if (!TRIAL.phase || !F || F.brk || !F.N) return null;
    const rows = todayRows(F, ctx);
    if (!rows.length) return null;
    let lo = rows[0];
    for (const q of rows) if (q.lo < lo.lo) lo = q;
    const cut = sliceOf(ctx), n = F.ev.R.pts.filter(q => q.t + 5 <= cut).length;
    const pass = clockPass(F, 'R', { k0: -100000, k1: 100000 }, 'EARLIER', cut, n);
    const deep = 10 * lo.lo <= -7 * F.w0t, half = 2 * n >= F.N;
    return { r: lo.lo / F.w0t, deep, half, done: deep && half, pass, cut };
  }
  // the zones of the side the rule points at stay as they are; the other side's haze and stars a little quieter
  // (operator 2026-10-06 «пока откат не сделан, зоны R чуть ярче, после — зоны X»; 2026-10-08 the rule); never a size
  const phaseK = () => 1;
  // its one place in the panel: the state and both criteria with today's values
  function phasePanel(F, ctx) {
    const ph = phaseOf(F, ctx), P = 'FF:PHASE-RULE';
    if (!ph) return '';
    const ok = b => b ? '✓ ' : '', share = ppTxt(ph.pass, true);
    return '<div class="p24-phase" title="' + esc(lbl(P, 'title')) + '"><div class="p21-h second"><span>' + lbl(P, 'head') + candTag() + '</span></div>' +
      '<div class="p21-note">' + ok(ph.deep) + lbl(P, 'depth', { r: sd(ph.r) }) + '</div>' +
      link({ k: 'phase' }, '<span class="t"><span>' + ok(ph.half) + lbl(P, 'clock', { cut: clk(ph.cut), share }) + '</span></span>', 'mc', ph.pass, lbl('EST:B-CLOCK-R', 'title')) + '</div>';
  }
  // the candidate edition's own words for the accepted «Сейчас» forms (row_mark / title_mark, operator 08.10), read only
  // here and only for the trial «nowmarks»: the general lbl() keeps refusing them (tests/integration_faults.mjs)
  function reviewLbl(id, key, vars) {
    const box = REVIEW && REVIEW.forms[id], set = box && box.labels[key], t = set && set.ANY;
    if (t == null) { kViolate('a candidate label outside its registry: ' + id + ' · ' + key); return ''; }
    const out = vars ? t.replace(/\{([A-Za-z0-9_]+)\}/g, (m, k) => vars[k] != null ? String(vars[k]) : m) : t;
    if (/\{[A-Za-z0-9_]+\}/.test(out)) kViolate('a candidate label without its value: ' + id + ' · ' + key);
    return out;
  }
  // «Сейчас», the pullback line as only its number (trial «nowmarks»): its levels are the marks at the price scale, the
  // historical words, levels, time and support are in its title
  function nowMarkRow(F, n, E, o) {
    const { val, bN, bI, bT, q, tm, sp, u0, sgn, lv } = o, NE = 'EST:N-NEW-R';
    const P = v => Math.round(F.u2p(u0 + sgn * v)), cnt = sp.N_match_unknown ? sp.N_new_yes + '–' + (sp.N_new_yes + sp.N_match_unknown) : String(sp.N_new_yes);
    const t1 = bN ? reviewLbl(NE, 'title_mark', { ev: 'R', cut: n.cut.cut_clock_et, today: num(P(0), 0), pct: val, yes: cnt, D: sp.N_match_total, n: sp.N_eligible, N: n.base.N_base }) : '';
    const t2 = bI ? reviewLbl('EST:N-IF-NEW-R', 'title_mark', { p50: lv(q.q50), lo: num(Math.min(P(q.q25), P(q.q75)), 0), hi: num(Math.max(P(q.q25), P(q.q75)), 0), time: bT ? reviewLbl('EST:N-TIME-R', 'title_mark', { min: Math.round(tm.q50_min) }) : '' }) : '';
    return link({ k: 'now', ev: 'R' }, '<span class="t"><span>' + reviewLbl(NE, 'row_mark', { ev: '<i style="color:' + cfg.R + '">R</i>' }) + candTag() + (E.note ? ' <span class="p21-sub">' + esc(E.note) + '</span>' : '') + '</span></span><b>' + val + '</b>', 'mc', null, [t1, t2].filter(Boolean).join(' '));
  }
  // its levels at the price scale, always, no text: today's deepest point after the activation (dashed), and for the
  // sessions whose pullback went deeper the middle half of where it ended (a narrow bar) with its median (a tick); a thin
  // line joins them. The same published bundles as the number; the hover picture of the row stays as it was
  function drawNowMarks(c, ctx) {
    if (!TRIAL.nowmarks || st.mode !== 'bounds') return;
    const F = ctx.F, n = nowOf(ctx), E = n && n.R;
    if (!E || (n.status !== 'OK' && n.status !== 'FROZEN_AT_BREAK') || !E.state || !E.continuation || !nowBundle(n, 'EST:N-NEW-R', 'MAIN', E.continuation)) return;
    const q = E.continuation.p_new_extreme && nowBundle(n, 'EST:N-IF-NEW-R', 'MAIN') ? E.continuation.delta_if_new || {} : {};
    const u0 = E.state.r_seen, col = cfg.R, xr = V.plot.w, y0 = Math.round(V.Y(F.u2p(u0))) + 0.5;
    c.save(); c.lineWidth = 1;
    c.strokeStyle = rgba(col, 0.9); c.setLineDash([3, 2]); c.beginPath(); c.moveTo(xr - 24, y0); c.lineTo(xr, y0); c.stroke(); c.setLineDash([]);
    if (q.q25 != null && q.q75 != null && q.q50 != null) {
      const ya = V.Y(F.u2p(u0 - q.q25)), yb = V.Y(F.u2p(u0 - q.q75)), ym = Math.round(V.Y(F.u2p(u0 - q.q50))) + 0.5;
      c.strokeStyle = rgba(col, 0.4); c.beginPath(); c.moveTo(xr - 7.5, y0); c.lineTo(xr - 7.5, ya); c.stroke();
      c.fillStyle = rgba(col, 0.5); c.fillRect(xr - 10, Math.min(ya, yb), 5, Math.max(2, Math.abs(yb - ya)));
      c.strokeStyle = rgba(col, 1); c.lineWidth = 2; c.beginPath(); c.moveTo(xr - 16, ym); c.lineTo(xr, ym); c.stroke();
    }
    c.restore();
  }
  function candidatePaths(ctx) {
    const a = candidateSelection(ctx, hv()), cv = dom('dcF'), geom = cv?._g;
    if (!TRIAL.paths || !a?.ready || !geom) { IS.pathEvidence = null; return; }
    const c = cv.getContext('2d'), F = ctx.F, cut = sliceOf(ctx);
    const X = j => geom.L + (j + .5) * geom.cw, Y = u => geom.T + (geom.k1 - 10 * u) * geom.rh;
    const evidence = [];
    c.save(); c.beginPath(); c.rect(geom.L, geom.T, cv.clientWidth - geom.L - 4, cv.clientHeight - geom.T - 16); c.clip();
    for (const [id, label] of a.members) {
      const m = F.M.find(m => m.id === id); if (!m) continue;
      c.strokeStyle = rgba(label === 'YES' ? cfg.R : label === 'NO' ? cfg.path : '#A6AFBC', label === 'YES' ? .55 : .28);
      c.lineWidth = .7; c.setLineDash(label === 'UNKNOWN' ? [3, 3] : []); let last = null;
      for (let j = 0; j < F.grid.length; j++) {
        const row = m.path[j], T = F.grid[j];
        if (!row || T <= cut || T <= m.act) { last = null; continue; }
        const p = { j, T, u: row[2] / m.w };
        c.beginPath(); c.moveTo(X(j), Y(row[0] / m.w)); c.lineTo(X(j), Y(row[1] / m.w)); c.stroke();
        if (last && T - last.T === 5) { c.beginPath(); c.moveTo(X(last.j), Y(last.u)); c.lineTo(X(j), Y(p.u)); c.stroke(); }
        evidence.push([id, j, p.u]); last = p;
      }
    }
    c.restore(); IS.pathEvidence = { context: scenePacket().context.id, ids: [...a.ids], points: evidence };
  }
  function integrationSettings() {
    if (!ICFG.enabled) return '';
    return '<details class="cgd"><summary class="cg">Испытание кандидатов</summary>' +
      [['pre', 'История до подтверждения'], ['arrive', 'Отсюда до места · Q1'], ['paths', 'Связанные пути в нижнем окне'], ['continuations', 'Продолжения · закреплённое окно'],
        ['phase', 'Фаза по вашему правилу · 08.10'], ['nowmarks', '«Сейчас»: откат числом и отметками у шкалы · 08.10']].map(([k,t]) => '<label class="cr"><span>' + t + '</span><input type="checkbox" data-trial="' + k + '"' + (TRIAL[k] ? ' checked' : '') + '></label>').join('') +
      '<button type="button" id="auditScene">Проверить происхождение и опору</button><div id="auditResult" class="p21-note"></div></details>';
  }
  async function auditScene() {
    const q=sceneRequest(), packet=scenePacket(), el=dom('auditResult');
    if(!packet){el.textContent='Сцена ещё рассчитывается';return;}
    el.textContent='Проверяю…';
    const args=new URLSearchParams({instrument:A.inst,session:q.s.k,at:q.cut,scope:st.scope,view:q.view,trials:q.trials.join(','),context:packet.context.id});
    if(A.src==='hist')args.set('date',A.date);
    try{const report=await(await fetch('/api/integration/audit?'+args)).json();
      if(scenePacket()?.context.id!==report.context){el.textContent='Срез изменился: проверка относится к прежней сцене';return;}
      IS.audit=report; el.textContent=report.status==='PASS_SCOPED'?'Заявленные проверки сцены прошли. Полная карта и человеческая приёмка отдельно.':report.status==='NO_ADDITIONAL_COVERAGE'?'Для этой сцены проверен шлюз SC; дополнительных пересчётов Trace нет.':'Проверка обнаружила несоответствие';
    }catch(e){el.textContent='Проверка не завершилась: '+e.message;}
  }
  function setTrial(k, on) {
    if(k==='pullbacks')return false; // rejected bounds mapping; not a dormant checkbox that can undo the repair
    TRIAL[k] = !!on; IS.key = null; IS.packet = null; IS.error = null;
    try { localStorage.setItem(TRIAL_KEY, JSON.stringify(TRIAL)); } catch (e) { /* not kept */ }
    if(k==='continuations'&&!on){CS.seq++;CS.packet=null;CS.drawing=null;if(st.mode==='continuations')st.mode='bounds';}
    if(k==='pullbacks'){PB.seq++;PB.key=PB.packet=PB.error=PB.pending=PB.cl=PB.model=null;st.pin=st.hover=null;}
    if (!TRIAL.arrive && st.pin?.k === 'arrive') st.pin = st.hover = null;
    dom('detg')._k = ''; render(true);
  }
  root.addEventListener('click', e => { if(e.target.closest('#auditScene'))auditScene(); });
