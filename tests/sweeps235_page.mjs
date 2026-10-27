// 23.5 after the operator's decisions of 26.10: the main map is the final R / X of screen 24, the decisions of 08.10
// are on, and the local layer «Съёмы лоу» is an overlay that the page computes exactly as lab/sweeps235_ref.py does.
// node tests/sweeps235_page.mjs [http://127.0.0.1:8735]   (a running 23.5 server with --integration)
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { startChrome, evaluate } from './trace_page.mjs';
const base = process.argv[2] || 'http://127.0.0.1:8735', b = await startChrome(), errors = [], out = 'lab/.runtime/sweeps235-page';
const PY = process.env.LOCALAPPDATA + '\\Python\\bin\\python.exe';
fs.mkdirSync(out, { recursive: true });
let n = 0;
const pause = ms => new Promise(r => setTimeout(r, ms));
const ck = (ok, name) => { if (!ok) throw Error(name); n++; console.log('PASS ' + name); };
b.cdp.on('Runtime.exceptionThrown', e => errors.push(e.exceptionDetails.exception?.description || e.exceptionDetails.text));
const scenes = [['NQ', 'RDR', '2025-12-17', '11:10'], ['ES', 'RDR', '2025-11-12', '11:00'], ['YM', 'ODR', '2025-10-20', '04:30'], ['YM', 'RDR', '2025-12-18', '11:00']];
const minutes = s => +s.slice(0, 2) * 60 + +s.slice(3);
async function ready() {
  for (let i = 0; i < 400; i++) {
    const s = await evaluate(b.cdp, () => { const d = window.__d24, c = d?.cur(); return { ready: !!(c?.F?.N && c.F.zones && d.V?.plot && !d.contract().unchecked) }; });
    if (s.ready) return;
    await pause(150);
  }
  throw Error('23.5 did not settle');
}
try {
  for (const [width, height] of [[1600, 900], [1920, 1000]]) {
    await b.cdp.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
    for (const [inst, sess, date, at] of scenes) {
      const tag = `${width} ${inst} ${sess} ${date} ${at}`;
      await b.cdp.send('Page.navigate', { url: 'about:blank' });
      await b.cdp.send('Page.navigate', { url: `${base}/23-5/#date=${date}&inst=${inst}&session=${sess}&at=${at}` });
      await ready();
      const s = await evaluate(b.cdp, async () => {
        const d = window.__d24, c = d.cur(), F = c.F;
        const q = new URLSearchParams({ instrument: d.A.inst, session: c.s.k, at: Math.floor((d.st.rp) / 5) * 5, view: 'conf', scope: d.st.scope, trials: '', date: d.A.date });
        const api = (await (await fetch('/api/integration/scene?' + q)).json()).family;
        const same = ['R', 'X'].every(ev => JSON.stringify(F.zones[ev].zones.map(z => [z.zone_id, z.n_zone])) === JSON.stringify(api.zones[ev].zones.map(z => [z.zone_id, z.n_zone])));
        const timeSd = performance.getEntriesByType('resource').some(e => e.name.includes('/api/integration/time-sd'));
        const off = d.st.L.sweep === false && !d.V.sw;
        d.st.L.sweep = true; d.render(true);
        const M = window.__sw235(), sw = d.V.sw, panel = document.getElementById('panel').innerText;
        const geo = sw ? sw.geo.length : -1, zoneStars = M.zones.reduce((a, z) => a + z.stars.length, 0);
        let tip = '';
        if (sw && sw.geo.length) { d.st.hover = d.hit(sw.geo[0].x, sw.geo[0].y); d.render(true); tip = document.getElementById('insp').innerText; }
        d.st.hover = null; d.st.L.sweep = false; d.render(true);
        return { same, timeSd, off, view: F.view, side: F.d0, at: c.s.k, model: { N: M.N, need: M.need, cats: M.cats, stars: M.stars.length,
          zones: M.zones.map(z => ({ label: z.label, n: z.n, k0: z.k0, k1: z.k1, t0: z.t0, t1: z.t1, stars: z.stars.length, depth: +z.depth.toFixed(6) })) },
          geo, zoneStars, tip, panel, verdict: /смотрим X|откат сделан/.test(panel), rows: [...document.querySelectorAll('#panel .p24-visit')].length };
      });
      ck(s.same && !s.timeSd, tag + ': the main map is the zone map of screen 24 (same zones and shares), no time x SD request');
      ck(s.off, tag + ': the local layer is off by default');
      ck(!s.verdict, tag + ': the phase rule shows its facts without a verdict');
      ck(s.view === 'conf', tag + ': the confirmation family (the reference reads the same)');
      const ref = JSON.parse(execFileSync(PY, ['-B', 'lab/sweeps235_ref.py', base, inst, sess, String(minutes(at)), date], { encoding: 'utf8', env: { ...process.env, PYTHONUTF8: '1' } }));
      const refZones = ref.zones.map(z => ({ label: z.label, n: z.n, k0: z.k0, k1: z.k1, t0: z.t0, t1: z.t1, stars: z.stars, depth: +z.depth.toFixed(6) }));
      ck(JSON.stringify(s.model.cats) === JSON.stringify(ref.cats) && s.model.stars === ref.stars && s.model.N === ref.N,
        tag + `: the page's categories of N and stars equal the reference (${JSON.stringify(ref.cats)})`);
      ck(JSON.stringify(s.model.zones) === JSON.stringify(refZones), tag + `: the page's constellations equal the reference (${refZones.map(z => z.label + ' ' + z.n).join(', ') || 'none'})`);
      ck(s.geo === s.zoneStars, tag + ': only the stars of a constellation are drawn');
      ck(!s.geo || (/держался/.test(s.tip) && /Сняли до/.test(s.tip)), tag + ': a star tells its own session: the held low, how far it was taken, the new extreme');
      const words = s.side > 0 ? ['Съёмы лоу', 'новый хай'] : ['Съёмы хай', 'новый лой'];
      ck(words.every(w => s.panel.includes(w) || !s.geo), tag + ': the words follow the side (' + words.join(', ') + ')');
    }
  }
  const shot = await b.cdp.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out + '/last.png', Buffer.from(shot.data, 'base64'));
  ck(!errors.length, 'no page exceptions');
  console.log('ALL GOOD · ' + n + ' checks');
} catch (e) {
  console.log('FAIL ' + e.message); if (errors.length) console.log(errors.join('\n')); process.exitCode = 1;
} finally { await b.close?.(); }
