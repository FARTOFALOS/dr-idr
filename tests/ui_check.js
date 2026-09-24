// UI check for agents with a browser tool: evaluate this in the page at http://127.0.0.1:8767 (focus mode, live panel
// loaded). It returns problems the operator must never see. An empty "problems" list = good.
(() => {
  const problems = [];
  const svg = document.querySelector('#live-chart svg');
  if (!svg) problems.push('live chart not drawn');
  // 1) no visible text of the session chart overlaps another
  const t = [...document.querySelectorAll('#live-chart svg text')].filter(e => e.style.visibility !== 'hidden').map(e => ({s: e.textContent, b: e.getBoundingClientRect()}));
  for (let i = 0; i < t.length; i++) for (let j = i + 1; j < t.length; j++) {
    const a = t[i].b, b = t[j].b;
    if (a.width && b.width && a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1) problems.push(`text overlap: "${t[i].s}" x "${t[j].s}"`);
  }
  // 2) right-side level labels never sit on the probability ladder
  const bars = [...document.querySelectorAll('#live-chart rect[height="6"]')].map(r => r.getBoundingClientRect());
  for (const l of [...document.querySelectorAll('#live-chart text.lv-label')].map(e => e.getBoundingClientRect()))
    if (bars.some(r => l.left < r.right && r.left < l.right && l.top < r.bottom && r.top < l.bottom)) problems.push('level label on the ladder');
  // 3) one line per zone row, side column without overflow
  document.querySelectorAll('.zone-row').forEach(r => { if (r.getBoundingClientRect().height > 30) problems.push('zone row wraps: ' + r.innerText); });
  // 4) the page fits one screen in focus mode (desktop)
  if (innerWidth > 1000 && document.documentElement.scrollHeight > innerHeight + 2) problems.push('page scrolls vertically');
  return {problems, texts: t.length, status: (document.getElementById('live-status') || {}).innerText};
})()
