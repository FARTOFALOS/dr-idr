// M21: executable geometry and interaction checks of the operator's 13.10 plan. Run in an isolated test browser.
// Fixtures discriminate zero/missing closes, own widths, own activation and a non-consecutive clock. Real scenes
// compare the selected case identities and their coordinates to the published inputs; no human acceptance is inferred.
(async () => {
  const D = window.__d24, problems = [], info = {}, wait = ms => new Promise(r => setTimeout(r, ms));
  const check = (ok, what) => { if (!ok) problems.push(what); };
  const saved = { mode: D.st.mode, hover: D.st.hover, pin: D.st.pin, pathFreq: D.st.pathFreq, rp: D.st.rp };
  const close = (a, b) => Math.abs(a - b) < 1e-8;
  const query = (kind, key) => D.links().find(h => h.context && h.k === kind && (kind === 'now' ? h.ev === key : kind === 'arrive' ? h.id === key : true));
  const focus = h => { D.st.hover = h; D.render(true); return D.graphEvidence; };
  const settle = async () => {
    for (let i = 0; i < 100; i++) {
      D.render(true); const c = D.cur();
      if (c.F && D.nowOf(c) && D.arriveOf(c) && !D.A.nowPending.size && !D.A.arrPending.size) break;
      if (!c.F && !['confirmed', 'broken', 'done'].includes(c.s.status)) break;
      await wait(100);
    }
  };
  try {
    const fx = { r: { snapshot_id: 'fixture-M21' }, grid: [600, 605, 610, 615, 620, 630], u2p: u => 100 + 20 * u };
    const m = { w: 40, act: 605, path: [[-4, 8, 0], [-4, 12, 10], null, [-10, 2, -5], [-12, 1, -10], [-16, 0, -15]] };
    const ss = D.familyCloseSegments(fx, m);
    check(ss.length === 3 && ss.map(s => s.length).join() === '2,2,1', 'M5 gap and non-consecutive clock must break the path');
    check(ss[0][0].p === 100 && ss[0][1].p === 105 && ss[1][0].p === 97.5, 'zero is an observed close; use the historical own width, never today’s width');
    check(ss[0].every(p => p.pre) && ss[1].every(p => !p.pre), 'the session keeps its own activation on the common clock');
    const scaled = D.familyCloseSegments(fx, { ...m, w: 80, path: m.path.map(x => x && x.map(v => v * 2)) });
    check(JSON.stringify(ss) === JSON.stringify(scaled), 'scaling one historical IDR and all its ticks must not change displayed coordinates');

    await settle(); D.st.mode = 'path'; D.st.hover = D.st.pin = null; D.render(true);
    const c = D.cur(), F = c.F;
    info.status = c.s.status; info.cut = D.sliceOf(c); info.N = F && F.N;
    const b = c.D.bars.find(x => x.t + 5 === D.sliceOf(c));
    check(b ? D.V.currentClose && D.V.currentClose.t === b.t + 5 && close(D.V.currentClose.p, b.c) : !D.V.currentClose, 'current marker must be the last CLOSED M5, absent on a missing cut candle');
    if (!F) { check(!D.graphEvidence && !D.pathEvidence, 'before confirmation: no inherited family or conditional geometry'); return { problems, info }; }
    const ev0 = D.pathEvidence;
    check(ev0 && JSON.stringify(ev0.ids) === JSON.stringify(F.M.map(m => m.id)), 'the base path layer must retain every parent case identity');
    let points = 0, pre = 0;
    for (const path of ev0.segments) {
      const member = F.M.find(m => m.id === path.id);
      for (const segment of path.points) for (let i = 0; i < segment.length; i++) {
        const [j, t, u, p] = segment[i], raw = member.path[j]; points++; if (t <= member.act) pre++;
        check(t === F.grid[j] && close(u, raw[2] / member.w) && close(p, F.u2p(u)), 'a real close must retain its own coordinate and clock');
        if (i) check(t - segment[i - 1][1] === 5, 'no line over a missing M5');
      }
    }
    info.points = points; info.pre = pre;
    check(points > 0, 'real historical closes must be present');
    const filmSig = () => JSON.stringify(D.filmOf(F).map(cd => [cd.T, cd.unknown, [...cd.cells].map(([k, ids]) => [k, ids.length])]));
    const before = filmSig(); document.getElementById('pathfreq21').click(); D.render(true);
    check(D.st.pathFreq && D.pathEvidence.frequencies && before === filmSig(), '«Частоты» must toggle drawing only, without changing any frequency');
    document.getElementById('pathfreq21').click();

    const r = D.arriveOf(c);
    if (r && r.status === 'OK') for (const P of r.places) {
      const h = query('arrive', P.level); check(!!h, 'all three fixed places must have shared controls'); if (!h) continue;
      D.st.mode = 'path'; const e = focus(h), q = D.graphQuestion(D.cur(), h);
      const published = P.state.status === 'OPEN' && P.publication === 'PUBLISHED' && !P.withheld;
      check(e && e.ready === published, 'unpublished, resolved, few or withdrawn answers must not draw conditional paths');
      check(JSON.stringify(e.members) === JSON.stringify(published ? P.members : []), 'the highlighted path set must be EXACTLY the published prefix-matched cases');
      if (published) {
        const text = document.getElementById('insp').innerText;
        check(text.includes(P.counts.yes + ' из ' + P.counts.n_match), 'numerator and denominator must be available together in the inspector');
        D.st.pin = h; D.st.hover = null; document.querySelector('#mode [data-m="bounds"]').click();
        const bc = D.cur(), be = D.graphEvidence, ids = new Set(P.members.map(([id]) => id));
        const lit = bc.F.ev.R.pts.filter(pt => D.emphOf(pt, D.st.pin, bc.F, bc) === true);
        const known = bc.F.M.filter(m => ids.has(m.id) && m.R.s === 'known').length;
        check(D.st.pin && be && JSON.stringify(be.members) === JSON.stringify(P.members) && lit.length === known && lit.every(pt => ids.has(pt.m.id)), 'mode switch must keep the question and exactly the same cases, using FINAL R times');
        document.querySelector('#mode [data-m="path"]').click();
        check(D.st.pin && D.graphEvidence && JSON.stringify(D.graphEvidence.members) === JSON.stringify(P.members), 'returning to paths must retain the pin');
        focus(query('past')); D.st.hover = null; D.render(true);
        check(D.graphEvidence && D.graphEvidence.kind === 'arrive' && D.graphEvidence.id === P.level, 'leaving another hover must restore the pinned answer');
      }
      if (P.state.status === 'RESOLVED' && !P.withheld) {
        const [hr, min] = P.state.time.split(':').map(Number), t = hr * 60 + min;
        check(e.observedM5 && e.observedM5[0] === t - 5 && e.observedM5[1] === t && !e.members.length, 'today’s arrival must show its observed M5 interval, never an exact intrabar time or historical final R');
        const text = document.getElementById('insp').innerText;
        check(text.startsWith('Сегодня дошли') && !text.includes('дошли ли после') && text.includes('M5'), 'a resolved question must become today’s observed fact in its words too');
      }
      if (!published) check(!q.members.length, 'small/absent support may not leak a highlighted conditional subset');
    }
    D.st.pin = null;
    for (const ev of ['R', 'X']) {
      const h = query('now', ev); if (!h) continue;
      const e = focus(h), q = D.graphQuestion(D.cur(), h), E = q.event;
      if (!q.ready) { check(!e.priceRange && !e.firstTimeRange, 'unavailable NOW must withdraw conditional price and time geometry'); continue; }
      const a = E.continuation.delta_if_new, t = E.continuation.time_to_new, u = ev === 'R' ? E.state.r_seen : E.state.x_seen, s = ev === 'R' ? -1 : 1;
      if (q.amount && a.q25 != null) check(e.priceRange && close(e.priceRange[0], F.u2p(u + s * a.q25)) && close(e.priceRange[1], F.u2p(u + s * a.q75)), 'NOW final additional magnitude must be transferred from today’s OWN anchor');
      if (q.time && t.q25_min != null) check(e.firstTimeRange && e.firstTimeRange[0] === Math.min(F.end, q.cut + t.q25_min) && e.firstTimeRange[1] === Math.min(F.end, q.cut + t.q75_min), 'FIRST update time must have its own time-axis interval');
      check(!e.futurePoint && !e.forecastPath && D.pathEvidence.ids.length === F.N, 'separate marginal summaries must not create a synthetic endpoint or a forecast path');
      if (e.priceRange) check(D.V.win && D.V.win.pA === e.priceRange[0] && D.V.win.pB === e.priceRange[1], 'price answers must be presented at the price axis');
    }
    D.st.hover = D.st.pin = null; D.render(true);
    const hs = [...document.querySelectorAll('.p24-queries [data-l21]')];
    const pane = document.getElementById('panel').getBoundingClientRect();
    check(hs.length === 7 && hs.every(el => { const x = el.getBoundingClientRect(); return x.top >= pane.top && x.bottom <= pane.bottom; }), 'all primary questions and three places must be visible without scrolling');
    info.questions = hs.length;
    check(!D.contract().violations.length, 'the graph must not introduce a contract violation');
  } finally { Object.assign(D.st, saved); D.render(true); }
  return { problems, info };
})()
