// UI check of design 24 «Границы хода» (variant «Окна времени» since 2026-10-01) (http://127.0.0.1:8767/24/) for agents with a browser tool: evaluate this in the
// page after it has loaded (wait ~4 s). It returns the problems the operator must never see; problems: [] = good.
// With a family on screen it also checks the semantics of DR-LAB-SEM-1.0 on the live objects of the page:
// the page and the server count the same; every percentage of the panel has a passport that reproduces it; R / X and
// the price and time histograms are one table; each «Путь семьи» column is its own 100 %; an area's window never
// exceeds its band; the tail of X equals «на уровне или дальше» on the same horizon; moving the slice rewrites nothing;
// every zone's share is its sessions in its exact cells, zones never overlap, and the slice does not move them.
(async () => {
  const problems = [], D = window.__d24;
  if (!D) return { problems: ['the screen did not start (window.__d24 missing)'] };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const panel = document.getElementById('panel');
  const settle = async () => { for (let i = 0; i < 25; i++) { D.render(true); const c = D.cur(); if (c.F || !['confirmed', 'broken', 'done'].includes(c.s.status)) break; await wait(200); } D.render(true); return D.cur(); };
  // 1) one screen, no page scroll, no horizontal overflow, the toolbar in one row
  if (innerWidth > 1000 && document.documentElement.scrollHeight > innerHeight + 2) problems.push('page scrolls vertically');
  if (panel.scrollWidth > panel.clientWidth + 1) problems.push('panel overflows horizontally');
  const tb = document.getElementById('tb');
  if (innerWidth > 1000 && tb.scrollWidth > tb.clientWidth + 1) problems.push('toolbar overflows: ' + tb.scrollWidth + ' > ' + tb.clientWidth);
  let c = await settle();
  const info = { day: c.D.iso || c.D.date, session: D.st.session, status: c.s.status, slice: c.obs };
  const txt = () => panel.innerText;
  if (/NaN|undefined|Infinity/.test(txt())) problems.push('panel shows NaN / undefined');
  const areaButton = document.getElementById('areab');
  if (areaButton && !areaButton.innerText.includes('· ' + D.st.ev)) problems.push('area button does not name its current R/X event');
  // session counts stay out of the panel, except the support of «Сейчас», which DR-LAB-NOW-1.0 §9.3 / §21.2 requires
  const noNow = () => { const q = panel.cloneNode(true); q.querySelectorAll('.p24-nowblk').forEach(e => e.remove()); return q.innerText; };
  if (/\d+\s*(из\s+\d|сесси[йи])/i.test(noNow())) problems.push('panel shows session counts');
  if (!c.F) return { problems, info, note: 'no family on screen (status ' + c.s.status + ')' };
  const F = c.F, N = F.N;
  info.family = F.cond; info.snapshot = F.r.snapshot_id;
  if (F.mismatch.length) problems.push('page and server disagree on ' + F.mismatch.join(', '));
  // 2) every percentage of the panel carries a passport that reproduces it (spec §13.3)
  const list = D.passports(), byId = new Map(list.map(p => [p.id, p]));
  const fmt = v => { const r = Math.round(v * 10) / 10; return r.toLocaleString('ru-RU', { minimumFractionDigits: Number.isInteger(r) ? 0 : 1, maximumFractionDigits: 1 }) + '%'; };
  for (const el of panel.querySelectorAll('[data-pp]')) {
    const p = byId.get(+el.dataset.pp), b = el.querySelector('b');
    if (!p) { problems.push('a panel number without a passport: ' + el.innerText.split('\n')[0]); continue; }
    for (const f of ['event_id', 'family_id', 'snapshot_id', 'region_kind', 'start_rule', 'end_rule', 'N', 'yes_count', 'unknown_count', 'no_event_count', 'display_scope']) if (!(f in p)) problems.push('passport without ' + f + ': ' + p.phrase);
    if (p.N !== N || p.snapshot_id !== F.r.snapshot_id) problems.push('passport of another family: ' + p.phrase);
    if (b && p.pct != null && !b.innerText.startsWith(fmt(p.pct))) problems.push('shown ' + b.innerText + ' but the passport gives ' + fmt(p.pct) + ': ' + p.phrase);
  }
  // 3) one table read three ways, for both events; the unknown mass apart; sums to N
  for (const ev of ['R', 'X']) {
    const E = F.ev[ev];
    let cells = 0, P = 0, T = 0;
    for (const q of E.cells.values()) cells += q.list.length;
    for (const v of E.P.values()) P += v;
    for (const v of E.T.values()) T += v;
    if (cells !== P || P !== T || cells + E.unknown + E.none !== N) problems.push(ev + ': cells ' + cells + ', price ' + P + ', time ' + T + ', unknown ' + E.unknown + ', none ' + E.none + ', N ' + N);
    if (new Set(E.pts.map(q => q.i)).size !== E.pts.length) problems.push(ev + ': one session gives more than one point');
  }
  if (F.out && Object.values(F.out).reduce((a, b) => a + b, 0) !== N) problems.push('DR outcomes do not add up to N');
  // 4) the tail of X = «на уровне или дальше» up on the same own horizon (known members), at every 0.1 level from -1 to +3
  for (let k = -10; k <= 30; k++) {
    let tail = 0, yesKnown = 0;
    F.M.forEach(m => {
      if (m.X.s !== 'known') return;
      if (10 * m.X.v >= k * m.w) tail++;
      let hitL = false;
      F.grid.forEach((Tt, j) => { const q = m.path[j]; if (Tt > m.act && q && q[1] * 10 >= k * m.w) hitL = true; });
      if (hitL) yesKnown++;
    });
    if (tail !== yesKnown) { problems.push('X tail differs from reach at ' + k / 10 + ': ' + tail + ' vs ' + yesKnown); break; }
  }
  // 5) «Путь семьи»: each column is its own 100 % (cells + missing = N)
  const film = D.filmOf(F);
  for (const cd of film) { let n = cd.unknown; for (const l of cd.cells.values()) n += l.length; if (n !== N) { problems.push('film column ' + cd.T + ' holds ' + n + ' of ' + N); break; } }
  // 6) R and X are on screen together (operator 2026-10-01, variant «Окна времени»): both events' zones are drawn and
  // listed, both price columns exist, the time band holds both; path mode hides the band
  const save = { ev: D.st.ev, mode: D.st.mode, area: D.st.area, rp: D.st.rp, pin: D.st.pin, hover: D.st.hover };
  D.st.hover = null; D.st.pin = null; D.render(true); const vR = D.V.stripOn;
  const zr = (D.zonesOf(F, 'R') || { zones: [] }).zones.length, zx = (D.zonesOf(F, 'X') || { zones: [] }).zones.length;
  if (D.st.L.zones && (D.V.zoneHit || []).length !== zr + zx) problems.push('drawn constellations ' + (D.V.zoneHit || []).length + ' of ' + (zr + zx) + ' zones of R and X');
  if (D.st.L.strip && (D.V.hills || []).length !== zr + zx) problems.push('time band hills ' + (D.V.hills || []).length + ' of ' + (zr + zx));
  if (D.st.L.strip && (D.V.caps || []).length !== zr + zx) problems.push('time band capsules ' + (D.V.caps || []).length + ' of ' + (zr + zx));
  if (D.V.projW && !(D.V.projCols && D.V.projCols.R && D.V.projCols.X)) problems.push('the price column does not hold R and X side by side');
  for (const [ev, n] of [['R', zr], ['X', zx]]) for (const z of (D.zonesOf(F, ev) || { zones: [] }).zones) if (!panel.innerText.includes(z.label)) problems.push('zone ' + z.label + ' missing from the panel list');
  // the inspector reads what is hovered, in its fixed place (never a tooltip over the chart)
  const insp = document.getElementById('insp');
  if (!insp) problems.push('no inspector');
  else {
    const zz = (D.zonesOf(F, 'R') || D.zonesOf(F, 'X') || { zones: [] }).zones[0], zev = D.zonesOf(F, 'R') && D.zonesOf(F, 'R').zones.length ? 'R' : 'X';
    if (zz) { D.st.hover = { k: 'zone', ev: zev, i: 0 }; D.render(true); if (!insp.innerText.includes(zz.label)) problems.push('the inspector does not read a hovered zone'); if (!D.V.lk) problems.push('a hovered zone has no link to its peak 15 minutes'); }
    D.st.hover = { k: 'tcell', b0: 2, b1: 3, src: 'strip' }; D.render(true);
    if (!/R ·/.test(insp.innerText) || !/X ·/.test(insp.innerText)) problems.push('the inspector of a 15-minute window does not show both R and X');
    if (!document.getElementById('tip').hidden) problems.push('a floating tooltip is shown over the chart');
    D.st.hover = null; D.render(true);
  }
  // the six windows slide up and hold six cards
  D.st.detPin = true; D.render(true);
  const cards = document.querySelectorAll('#detg .dcard').length;
  if (cards !== 6) problems.push('the bottom windows hold ' + cards + ' cards, not 6');
  D.st.detPin = false; D.render(true);
  D.st.mode = 'path'; D.render(true);
  if (D.V.stripOn) problems.push('the time histogram stays in «Путь семьи»');
  if (!/Путь семьи/.test(panel.innerText)) problems.push('the panel does not show the M5 column in «Путь семьи»');
  D.st.mode = 'bounds'; D.render(true);
  if (!vR) problems.push('the time histogram is off in «Границы хода»');
  // 7) an area: the window's share never exceeds its band's (spec §14.1-4)
  const E = F.ev[D.st.ev], top = [...E.P].sort((a, b) => b[1] - a[1])[0];
  if (top) {
    const bb = [...E.T].sort((a, b) => b[1] - a[1])[0][0];
    D.st.area = { k0: top[0] - 1, k1: top[0] + 2, b0: bb, b1: bb + 2, ev: D.st.ev }; D.render(true);
    const I = D.areaInfo(F, D.cur());
    if (I.win.yes_count > I.band.yes_count) problems.push('window share above its band share');
    if (!/Выбранная область/.test(panel.innerText)) problems.push('the selected area is not in the panel');
  }
  // DR-LAB-NOW-1.0 T14 / T15 on the page: the band (and cell) of today's extreme is always reachable; a zone is drawn
  // impossible only when its status is IMPOSSIBLE (the history clock never makes a zone impossible)
  const twoAxes = cc => {
    const Rch = D.reachOf(cc.F, cc);
    for (const ev of ['R', 'X']) {
      const q = Rch.cur && Rch.cur[ev];
      if (Rch.known && q && (!Rch.okK(ev, q.k) || !Rch.okCell(ev, q.k, q.b))) problems.push('T14: the band of today’s ' + ev + ' is not reachable at ' + clkOf(cc.obs));
      const S = D.zoneStatus(cc.F, cc, ev), Lk = D.zoneLook(cc.F, cc, ev);
      Lk.forEach((l, i) => { if (l === 'IMPOSSIBLE' && S[i] !== 'IMPOSSIBLE') problems.push('T15: zone ' + ev + (i + 1) + ' drawn impossible while ' + S[i]); });
    }
  };
  const clkOf = t => String(Math.floor(((t % 1440) + 1440) % 1440 / 60)).padStart(2, '0') + ':' + String(((t % 60) + 60) % 60).padStart(2, '0');
  if (!/Сейчас/.test(txt())) problems.push('the panel has no «Сейчас» block');
  // 8) moving the slice rewrites nothing: the same snapshot, the same distributions
  const sig = f => f ? f.r.snapshot_id + '|' + [...f.ev.R.cells.keys()].sort().join(',') + '|' + [...f.ev.X.cells.keys()].sort().join(',') + '|' + JSON.stringify(f.zones) : null;
  const s0 = sig(F), steps = [];
  for (const dt of [15, 60, 120]) {
    const t = F.act0 + dt;
    if (t >= F.end) break;
    D.st.rp = t; const cc = await settle();
    if (cc.F && cc.F.view === F.view && sig(cc.F) !== s0) problems.push('the snapshot changed when the slice moved to ' + t);
    if (cc.F) twoAxes(cc);
    steps.push(t);
  }
  // T14 at the end of the block too: the band of today's extreme stays reachable after the last M5
  D.st.rp = F.end; { const cc = await settle(); if (cc.F) twoAxes(cc); }
  Object.assign(D.st, save); D.render(true);
  // 9) every panel line lights something
  for (const el of [...panel.querySelectorAll('[data-l21]')].slice(0, 14)) {
    el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true })); D.render(false);
    if (!D.st.hover) problems.push('hover does nothing: ' + el.innerText.split('\n')[0]);
    el.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, relatedTarget: document.body }));
  }
  // 10) the zone map (zone-map-3): each zone's share is its sessions in its exact cells (the page recounts it), zones never
  // share a cell, zones + residual + unknown + none = N, every zone is drawn and listed, and today's status of the page
  // equals the server's at the slice of the request (checked inside zoneStatus, reported as a mismatch)
  for (const ev of ['R', 'X']) {
    const Zm = D.zonesOf(F, ev);
    if (!Zm) { problems.push('no zone map for ' + ev); continue; }
    const seen = new Set();
    for (const z of Zm.zones) {
      const cells = new Set(z.cell_mask.map(([k, b]) => k + '|' + b));
      const n = F.ev[ev].pts.filter(q => cells.has(q.k + '|' + q.b)).length;
      if (n !== z.n_zone) problems.push('zone ' + z.label + ': ' + n + ' points in its cells, the passport says ' + z.n_zone);
      for (const c of cells) { if (seen.has(c)) problems.push('two zones share the cell ' + c); seen.add(c); }
      if (Math.abs(z.p_snapshot - z.n_zone / N) > 1e-12) problems.push('zone ' + z.label + ': its share is not n / N');
    }
    if (Zm.zones.reduce((t, z) => t + z.n_zone, 0) + Zm.n_residual_total + Zm.unknown_count + Zm.no_event_count !== N) problems.push(ev + ': zones + residual + unknown + none != N');
  }
  {
    D.render(true);
    const drawn = (D.V.zoneHit || []).length, all = ['R', 'X'].map(ev => D.zonesOf(F, ev)).filter(Boolean), nz = all.reduce((t, Zm) => t + Zm.zones.length, 0);
    if (all.length && D.st.L.zones && D.st.mode === 'bounds' && nz !== drawn) problems.push('drawn zones ' + drawn + ' of ' + nz);
    if (all.length && D.st.mode === 'bounds' && !/Зоны /.test(panel.innerText)) problems.push('the panel has no zone list');
    info.zones = ['R', 'X'].map(ev => (D.zonesOf(F, ev) || { zones: [] }).zones.map(z => z.label + ' ' + Math.round(1000 * z.p_snapshot) / 10 + '%')).flat();
    info.zoneStatus = { R: D.zoneStatus(F, D.cur(), 'R'), X: D.zoneStatus(F, D.cur(), 'X') };
    if (F.mismatch.length) problems.push('page and server disagree on ' + F.mismatch.join(', '));
  }
  info.checkedSlices = steps;
  return { problems, info };
})()
