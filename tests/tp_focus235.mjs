// Run against an integration server. Pass --ym-case while the 27 November YM replay is in its live cache.
import assert from 'node:assert/strict';
import { startChrome, evaluate } from './trace_page.mjs';

const base = (process.argv[2] || 'http://127.0.0.1:8735').replace(/\/$/, '');
const ym = process.argv.includes('--ym-case');
const scene = ym ? 'inst=YM&session=ODR&at=04:45' : 'date=2025-12-17&inst=NQ&session=RDR&at=11:40';
const browser = await startChrome(), cdp = browser.cdp;
const query = () => evaluate(cdp, () => {
  const d = window.__d24, F = d?.V?.ctx?.F;
  if (!F?._tp) return null;
  const view = d.V, q = view.tpFocus, sl = d.reachOf(F,view.ctx).sl, W = F._tp.clock.windows[F._tp.w];
  const cells = new Map();
  for (const pt of F.ev.R.pts) {
    if (pt.b < W[0] || pt.b >= W[1]) continue;
    const key = pt.k + '|' + pt.b;
    cells.set(key,(cells.get(key) || 0) + 1);
  }
  return { q, label: view.tpFocusLabel, sl, cells: [...cells], N: F.N, w: F._tp.w, issues: d.contract().violations,
    known: d.reachOf(F,view.ctx).known, failed: view.ctx.s.failed, rbx: F.rbx };
});
try {
  await cdp.send('Page.navigate', { url: `${base}/23-5/#${scene}` });
  let r;
  for (let i=0; i<80; i++) {
    r = await query();
    if (r?.q?.shown) break;
    await new Promise(resolve => setTimeout(resolve,250));
  }
  assert.ok(r?.q?.shown, JSON.stringify(r));
  const { q } = r;
  assert.equal(q.pass.estimand, 'EST:B-RX-REGION-R');
  assert.equal(q.pass.case_set, 'CS:TP-WINDOW-1');
  assert.equal(q.pass.N,r.N);
  assert.equal(q.pass.yes_count,new Map(r.cells).get(q.k + '|' + q.b));
  assert.equal(q.t1-q.t0,15);
  assert.deepEqual(r.issues,[]);
  if (ym) {
    assert.deepEqual([r.w,r.N,q.k,q.n,q.t0,q.t1,q.active],['W2',22,-8,3,285,300,true]);
    assert.ok(r.label, 'the verified joint share is drawn beside its price row');
  }
  console.log(`verified focus ${r.w}, ${q.n}/${r.N}, SD ${q.k/10} to ${(q.k+1)/10}, ET minute ${q.t0}–${q.t1}`);
  const mode = await evaluate(cdp, () => { window.__d24.st.mode='path';window.__d24.render(true);return window.__d24.V.tpFocus; });
  assert.equal(mode,null);
} finally { await browser.close(); }
