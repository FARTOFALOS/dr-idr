// DR Lab 23.5 · «Слой от Anthropic» — the candidate DR-LAB-ANT-0.1 on the page (design/sozvezdiya-23-5/src/ant235.js,
// operator 22.11.2026: a button left of «▭ Область · R»; off — the original 23.5, on — Claude's proposal over it).
//
//     node tests/ant235_page.mjs http://127.0.0.1:<port>          (a server of this working copy with --integration)
//     ANT_SHOTS=<folder> … also saves the screen of every scene with the layer off and on
//
// For a few history scenes: the button is there and off at the start, 23.5 shows TP-2.0 as before (no layer words in the
// panel); a click puts the layer on: its block stands first in the panel, every number of it is a passport the server's
// candidate gate re-derived (no violation, none unchecked); the ladder does not grow with the level, a line q is the
// farthest level that at least q % of the sessions like today reached, drawn only with as many as a place needs; a
// second click gives back the original. Exit code 0 = every check passed.
import fs from 'node:fs';
import path from 'node:path';
import { startChrome, evaluate } from './trace_page.mjs';

const base = (process.argv[2] || 'http://127.0.0.1:8735').replace(/\/$/, '');
const SHOTS = process.env.ANT_SHOTS || null;
const SCENES = (process.env.ANT_SCENES ? process.env.ANT_SCENES.split(';').map(s => s.split(',')) : null) ||
  [['NQ', 'RDR', '2025-12-17', '11:40'], ['NQ', 'RDR', '2025-12-17', '10:50'], ['ES', 'RDR', '2025-12-18', '12:30'], ['NQ', 'ODR', '2025-12-19', '06:00'], ['YM', 'ADR', '2025-12-16', '00:30']];
const sleep = ms => new Promise(r => setTimeout(r, ms));
let bad = 0;
const ck = (ok, what) => { if (!ok) bad++; console.log((ok ? '  ok   ' : '  FAIL ') + what); };

async function settle(cdp) {
  for (let i = 0; i < 160; i++) {
    const s = await evaluate(cdp, function () {
      const d = window.__d24;
      if (!d || !d.V || !d.V.ctx || !d.A.day || d.A.day.status !== 'ok') return 'page';
      const t = d.tp(), c = d.contract(), s = d.V.ctx.s;
      if (['before', 'forming', 'waiting', 'noconf'].includes(s.status)) return 'noconf';
      if (!s.conf) return 'page';
      if (t.on && !t.w) return 'tp';
      if (!d.passports().length) return 'passports';
      d.verify();
      return c.unchecked ? 'unchecked' : 'ok';
    });
    if (s === 'ok' || s === 'noconf') return s;
    await sleep(250);
  }
  return 'timeout';
}
const click = async (cdp, x, y) => { await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 }); await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }); };
const button = cdp => evaluate(cdp, function () { const b = document.getElementById('antb'), r = b.getBoundingClientRect(), a = document.getElementById('areab').getBoundingClientRect(); return { hidden: b.hidden, on: b.classList.contains('on'), text: b.textContent, x: r.left + r.width / 2, y: r.top + r.height / 2, leftOfArea: r.right <= a.left + 1 && Math.abs(r.top - a.top) < 4 }; });
const shot = async (cdp, name) => {
  if (!SHOTS) return;
  const r = await cdp.send('Page.captureScreenshot', { format: 'png' });
  fs.mkdirSync(SHOTS, { recursive: true });
  fs.writeFileSync(path.join(SHOTS, name + '.png'), Buffer.from(r.data, 'base64'));
};

const B = await startChrome();
try {
  for (const [inst, sess, date, at] of SCENES) {
    console.log(`${inst} ${sess} ${date} ${at}`);
    await B.cdp.send('Page.navigate', { url: `${base}/23-5/#date=${date}&inst=${inst}&session=${sess}&at=${at}` });
    await sleep(900);
    let st = await settle(B.cdp);
    if (st === 'noconf') { console.log('  (no confirmation in this scene: skipped)'); continue; }
    ck(st === 'ok', 'the scene settles with every passport checked (' + st + ')');
    let b = await button(B.cdp);
    ck(!b.hidden && !b.on && b.text === 'Слой отAnthropic' && b.leftOfArea, 'the button «Слой от Anthropic» stands left of «▭ Область», off at the start');
    const off = await evaluate(B.cdp, function () { const d = window.__d24; return { a: d.ant(), panel: document.getElementById('panel').innerText, n: d.passports().filter(p => /^EST:ANT-/.test(p.estimand)).length }; });
    ck(!off.a.on && !/Слой от Anthropic/.test(off.panel) && /Время отката/.test(off.panel), 'off: the original 23.5 (TP-2.0 panel, no layer words)');
    await shot(B.cdp, `${inst}-${sess}-${date}-off`);
    await click(B.cdp, b.x, b.y); await sleep(400);
    st = await settle(B.cdp);
    ck(st === 'ok', 'on: the scene settles with every passport checked (' + st + ')');
    const r = await evaluate(B.cdp, function () {
      const d = window.__d24, c = d.contract(), ps = d.passports().filter(p => /^EST:ANT-/.test(p.estimand));
      return { a: d.ant(), c, ps: ps.map(p => ({ e: p.estimand, checked: !!p.checked, v: p.violation || null, k: p.params.k, cs: p.case_set, form: p.claim_form })),
        panel: document.getElementById('panel').innerText };
    });
    const a = r.a;
    const at0 = r.panel.search(/Слой от Anthropic · после \d\d:\d\d/), at1 = r.panel.indexOf('Время отката');
    ck(a.on && at0 >= 0 && (at1 < 0 || at0 < at1), 'on: the layer\'s block stands above the TP-2.0 panel');
    ck(!r.c.all.length && !r.c.unchecked, 'no contract violation, nothing unchecked (' + (r.c.all[0] || r.c.unchecked || '') + ')');
    if (a.why) { ck(['wait', 'broken', 'nowin', 'ended'].includes(a.why), 'the layer says why it has no numbers here: ' + a.why); }
    else if (!a.n) { ck(/как сегодня не было ни одной сессии семьи/.test(r.panel) && !r.ps.length, 'no session was like today: the layer says so and shows no number'); }
    else {
      ck(r.ps.length > 0 && r.ps.every(p => p.checked && !p.v && p.cs === 'CS:ANT-LIKE-NOW-1' && /^CF:ANT-/.test(p.form)), 'every number of the layer is a C1 passport on CS:ANT-LIKE-NOW-1, re-derived by the candidate gate (' + r.ps.length + ')');
      const lad = a.ladder;
      ck(lad.every((x, i) => i === 0 || x.yes <= lad[i - 1].yes) && lad.every(x => x.yes + x.unknown + x.no === a.n) && (!lad.length || lad[0].k === a.kt + 1),
        'the ladder starts above today\'s top, does not grow with the level and keeps every session (n ' + a.n + ', ' + lad.length + ' rows)');
      const far = L => { const nx = lad.find(x => x.k === L.k + 1); return L.yes * 100 >= L.q * a.n && (!nx || nx.yes * 100 < L.q * a.n); };
      ck(a.lines.every(far) && (a.n >= a.need || !a.lines.length), 'a line q is the farthest level at least q % reached, drawn only with as many as a place needs (' + a.lines.map(L => L.q + '%:' + L.k).join(' ') + '; n ' + a.n + ', need ' + a.need + ')');
      ck(/из похожих/.test(r.panel) && /Проверка на истории/.test(r.panel) && (!a.cond || /так закончились/.test(r.panel)), 'the panel shows the ladder, the condition of the window\'s levels and the check on history');
      console.log('       n=' + a.n + ' need=' + a.need + ' kt=' + a.kt + ' L70=' + a.L70 + ' L50=' + a.L50 + ' cond=' + JSON.stringify(a.cond));
    }
    await shot(B.cdp, `${inst}-${sess}-${date}-on`);
    b = await button(B.cdp);
    ck(b.on, 'the button shows the layer is on');
    await click(B.cdp, b.x, b.y); await sleep(400); await settle(B.cdp);
    const back = await evaluate(B.cdp, function () { const d = window.__d24; return { a: d.ant(), panel: document.getElementById('panel').innerText, c: d.contract() }; });
    ck(!back.a.on && !/Слой от Anthropic/.test(back.panel) && !back.c.all.length, 'a second click gives back the original 23.5');
  }
} finally { await B.close(); }
console.log(bad ? bad + ' check(s) failed' : 'all checks passed');
process.exit(bad ? 1 : 0);
