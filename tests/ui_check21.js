// UI check of the working screen «Созвездия» for agents with a browser tool: evaluate this in the page at
// http://127.0.0.1:8767 (wait ~6 s after load). It returns problems the operator must never see; [] = good.
// It also replays one minute of the traded session, so the numbers of the panel are checked on real data.
(async () => {
  const problems = [], D = window.__dr;
  if (!D) return { problems: ['the screen did not start (window.__dr missing)'] };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const panel = document.getElementById('panel'), bar = document.getElementById('apibar');
  if (!document.querySelector('#dr21-root.api')) problems.push('not in working-screen mode (no data from the server)');
  if (/не ответил|ошибка|error/i.test(bar.innerText)) problems.push('feed: ' + bar.innerText);
  // 1) one screen, no page scroll, no horizontal overflow of the panel
  if (innerWidth > 1000 && document.documentElement.scrollHeight > innerHeight + 2) problems.push('page scrolls vertically');
  if (panel.scrollWidth > panel.clientWidth + 1) problems.push('panel overflows horizontally');
  // 2) replay a minute an hour after the box of the session in view, wait for the similar sessions
  const c0 = D.cur(), S = { ADR: -210, ODR: 240, RDR: 630 }[D.st.session];
  const at = Math.min(S + 60, Math.floor(c0.obs / 5) * 5 - 5);
  if (c0.D.bars.length && at > S) {
    D.st.rp = at; D.render(true);
    for (let i = 0; i < 20 && !D.cur().ov; i++) { await wait(300); D.render(true); }
    const c = D.cur();
    if (['confirmed', 'broken', 'waiting'].includes(c.s.status)) {
      if (!c.ov) problems.push('no similar sessions at ' + at);
      else {
        const txt = panel.innerText;
        if (/\d+\s*(из|сесси)/i.test(txt)) problems.push('panel shows session counts');
        if (/NaN|undefined|Infinity/.test(txt)) problems.push('panel shows NaN / undefined');
        const links = panel.querySelectorAll('[data-l21]');
        if (links.length < 5) problems.push('panel has too few linked lines: ' + links.length);
        // every line lights something on the chart
        for (const el of [...links].slice(0, 12)) {
          el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true })); D.render(false);
          if (!D.st.hover) problems.push('hover does nothing: ' + el.innerText.split('\n')[0]);
          el.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, relatedTarget: document.body }));
        }
      }
    }
    D.st.rp = null; D.st.hover = null; D.render(true);
  }
  return { problems, feed: bar.innerText.split('\n')[0], session: D.st.session, replayed: at };
})()
