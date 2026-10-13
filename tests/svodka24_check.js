// In-page check of the «Сводка» candidate of screen 24 (branch svodka-24, the operator's brief of 13.10.2026). Evaluate in
// the page after it has loaded (tests/svodka24.mjs does it on the declared scenes). It returns the problems the candidate
// must never show; problems: [] = good. What it holds the panel to — the distinctions of the brief, made checkable:
//  C1  the parts stand in their fixed order: Сегодня → По цене → Ориентир (never rearranged by a share or a state);
//  C2  the price ladder is ordered as the chart (higher price on top), every «Сейчас» row stands right under the extreme
//      it starts from, the close of the slice stands between the rows above and below it;
//  C3  the anchors are today's own extremes after the activation (closed M5), the same the server's «Сейчас» starts from;
//  C4  every conditional share carries its own set: «Отсюда» «дошли k из n», «Сейчас» X its support, «Сейчас» R in its title;
//  C5  the R title names the side of the price (a deeper pullback is lower for a long, higher for a short);
//  C6  a place reached today is named by the opening minute of its M5, as every other fact of the summary;
//  C7  «Сегодня» holds facts: its only share is the passport of the operator's rule (the history clock of R);
//  C8  the fixed history stays fixed: the DR outcome and the zone shares are the same one M5 earlier; today's extremes
//      never retreat;
//  C9  the line of the last M5 is true: a new extreme is named iff one happened; «новых фактов нет» iff nothing did;
//  C10 a missing M5 in today's prefix is said at the anchors, the DR and the depth of the rule;
//  C11 the frame says the family does not change (after a break: that it is another family);
//  C12 no forecast grammar anywhere in the summary.
(async () => {
  const problems = [], D = window.__d24, wait = ms => new Promise(r => setTimeout(r, ms));
  if (!D) return { problems: ['the screen did not start'] };
  const panel = document.getElementById('panel');
  for (let i = 0; i < 40; i++) { D.render(true); const c = D.cur(); if (!c.F || (D.nowOf(c) && D.arriveOf(c))) break; await wait(150); }
  D.render(true);
  const c = D.cur(), F = c.F, info = { status: c.s.status, slice: c.obs };
  const txt = panel.innerText;
  if (/дойд[её]т|будет|вероятност|шанс|углубится|пойд[её]т/i.test(txt)) problems.push('C12: forecast grammar in the summary');
  if (!F) return { problems, info, note: 'no family on screen' };
  const num = s => { const m = String(s).replace(/\s/g, '').replace('−', '-').replace(',', '.').match(/-?\d+(\.\d+)?/); return m ? +m[0] : null; };
  const tick = (D.A.day && D.A.day.tick) || 0.25;
  // C1
  const parts = [...panel.querySelectorAll('.p24-L .n')].map(e => e.textContent);
  if (parts.join('|') !== 'Сегодня|По цене|Ориентир') problems.push('C1: the parts are ' + parts.join(' → '));
  // C11
  const frame = (panel.querySelector('.p24-frame') || {}).innerText || '';
  if (!/не меняется/.test(frame) || (F.brk && !/другая семья/.test(frame))) problems.push('C11: the frame does not say what the family is: ' + frame);
  // C2, C3
  const rail = panel.querySelector('.p24-rail'), L = D.links();
  const rows = rail ? [...rail.children].map(e => {
    const a = e.matches('[data-l21]') ? e : e.querySelector('[data-l21]'), h = a ? L[+a.dataset.l21] || {} : {};
    return { el: e, sep: e.classList.contains('p24-railnow'), k: h.k, ev: h.ev, id: h.id, p: e.classList.contains('p24-railnow') ? num(e.innerText) : num((e.querySelector('.rp') || {}).textContent || ''), now: e.classList.contains('p24-nowblk') };
  }) : [];
  let last = Infinity;
  rows.forEach((r, i) => {
    if (r.now) { const prev = rows[i - 1]; if (!prev || prev.k !== 'fact' || prev.ev !== r.ev) problems.push('C2: «Сейчас» ' + r.ev + ' is not right under its anchor'); return; }
    if (r.p == null) return;
    if (r.p > last + 1e-9) problems.push('C2: the ladder is not ordered by price at ' + r.p);
    last = r.p;
  });
  const sep = rows.find(r => r.sep);
  if (sep) rows.forEach((r, i) => { if (r.sep || r.now || r.p == null) return; const above = i < rows.indexOf(sep); if (above ? r.p < sep.p - 1e-9 : r.p >= sep.p + 1e-9) problems.push('C2: the close of the slice is not between the rows (' + r.p + ')'); });
  const tr = D.todayRows(F, c), sl = D.sliceOf(c);
  if (tr.length) {
    const lo = Math.min(...tr.map(q => q.lo)), hi = Math.max(...tr.map(q => q.hi));
    const want = { R: F.u2p(lo / F.w0t), X: F.u2p(hi / F.w0t) };
    for (const ev of ['R', 'X']) {
      const a = rows.find(r => r.k === 'fact' && r.ev === ev);
      if (!a) { problems.push('C3: no anchor of today\'s ' + ev); continue; }
      if (Math.abs(a.p - want[ev]) > tick / 2 + 1e-9) problems.push('C3: the anchor of ' + ev + ' ' + a.p + ' is not today\'s extreme ' + want[ev]);
    }
    const n = D.nowOf(c);
    if (n && n.status === 'OK') for (const ev of ['R', 'X']) {
      const E = n[ev]; if (!E || !E.state) continue;
      const u0 = ev === 'R' ? E.state.r_seen : E.state.x_seen;
      if (Math.abs(F.u2p(u0) - want[ev]) > tick / 2 + 1e-9) problems.push('C3: «Сейчас» ' + ev + ' starts from ' + F.u2p(u0) + ', the page\'s extreme is ' + want[ev]);
    }
    // C10
    const seen = new Set(tr.map(q => q.T)); let gap = null;
    for (let T = F.act0 + 5; T <= sl; T += 5) if (!seen.has(T)) { gap = T; break; }
    const anchorsText = rows.filter(r => r.k === 'fact').map(r => r.el.innerText).join(' ');
    if (gap != null && !/нет M5/.test(anchorsText)) problems.push('C10: a missing M5 ' + gap + ' is not said at the anchors');
    if (gap == null && /нет M5/.test(anchorsText)) problems.push('C10: a missing M5 said where none is');
  }
  // C4, C5, C6
  const r = D.arriveOf(c);
  for (const row of rows) {
    if (row.k === 'arrive' && r && r.status === 'OK') {
      const P = r.places.find(x => x.level === row.id), t = row.el.innerText;
      if (!P) continue;
      if (P.state.status === 'RESOLVED') {
        const [h, m] = P.state.time.split(':').map(Number), x = ((h * 60 + m - 5) % 1440 + 1440) % 1440, o = String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0');
        if (!t.includes('M5 ' + o)) problems.push('C6: the place ' + P.level + ' reached today is not named by its M5 ' + o);
      } else if (P.publication === 'PUBLISHED' && !P.withheld && !t.includes('дошли ' + P.counts.yes + ' из ' + P.counts.n_match)) problems.push('C4: «Отсюда» ' + P.level + ' without its set');
    }
    if (row.k === 'now' && row.ev === 'X' && /\d%/.test(row.el.innerText) && !/опора|похожих/.test(row.el.innerText)) problems.push('C4: «Сейчас» X without its support');
    if (row.k === 'now' && row.ev === 'R' && /\d%/.test(row.el.innerText)) {
      const a = row.el.querySelector('[title]'), title = a ? a.title : '';
      if (!/живых к этому часу \(\d/.test(title)) problems.push('C4: «Сейчас» R without its set in the title');
      const side = F.d0 === 1 ? 'ниже по цене' : 'выше по цене';
      if (!title.includes(side)) problems.push('C5: the R title does not say «' + side + '»');
    }
  }
  // C7
  const today = [], hd = [...panel.querySelectorAll('.p24-L')];
  for (let e = hd[0] && hd[0].nextElementSibling; e && !e.classList.contains('p24-L'); e = e.nextElementSibling) today.push(e);
  for (const e of today) if (/\d\s*%/.test(e.innerText) && !(e.matches('[data-pp]') && (L[+e.dataset.l21] || {}).k === 'phase')) problems.push('C7: a share in «Сегодня» that is not the rule\'s passport: ' + e.innerText.slice(0, 60));
  // C9
  const chg = (panel.querySelector('.p24-chg') || {}).innerText || '', list = D.changeOf(F, c);
  const prev = tr.filter(q => q.T <= sl - 5), lastRow = tr.find(q => q.T === sl);
  const newExt = !!(lastRow && prev.length && (lastRow.lo < Math.min(...prev.map(q => q.lo)) || lastRow.hi > Math.max(...prev.map(q => q.hi))));
  if (newExt !== /теперь/.test(chg) && sl > F.act0) problems.push('C9: the line of the last M5 says «' + chg + '», a new extreme ' + (newExt ? 'happened' : 'did not happen'));
  if ((list.length === 0) !== /новых фактов нет/.test(chg)) problems.push('C9: «новых фактов нет» does not match the changes ' + JSON.stringify(list));
  // C8: one M5 earlier, in the same family
  const base = () => { const z = [...panel.querySelectorAll('.p24-out [data-pp], .p21-link[class*="zst-"] b')].map(e => e.innerText.trim()); return z.join('|'); };
  const b1 = base(), save = D.st.rp;
  if (sl - 5 > F.act0 && save != null) {
    D.st.rp = sl - 5; D.render(true); await wait(50);
    const c0 = D.cur();
    if (c0.F && c0.F.r.snapshot_id === F.r.snapshot_id) {
      const b0 = base(), tr0 = D.todayRows(c0.F, c0);
      if (b0 !== b1) problems.push('C8: the fixed history changed with the slice: ' + b0 + ' → ' + b1);
      if (tr0.length && tr.length && (Math.min(...tr0.map(q => q.lo)) < Math.min(...tr.map(q => q.lo)) || Math.max(...tr0.map(q => q.hi)) > Math.max(...tr.map(q => q.hi)))) problems.push('C8: today\'s extremes retreated');
    }
    D.st.rp = save; D.render(true);
  }
  Object.assign(info, { parts, ladder: rows.map(x => x.sep ? 'NOW@' + x.p : (x.k || '?') + (x.ev ? ':' + x.ev : '') + (x.id ? ':' + x.id : '') + (x.p != null ? '@' + x.p : '')), change: chg });
  return { problems, info };
})()
