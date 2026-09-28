// Offline check of an artboard: runs Component.renderVals() under many states with a stub DCLogic, checks that every
// {{hole}} of the markup resolves (inside <sc-for> against the first item) and that no value is NaN/undefined.
// usage: node test.js ../built/project/Main.dc.html
const fs = require('fs');
const file = process.argv[2];
const src = fs.readFileSync(file, 'utf8');
const script = src.split('data-dc-script')[1].split('>').slice(1).join('>').split('</script>')[0];
const markup = src.split('<x-dc>')[1].split('</x-dc>')[0];
global.requestAnimationFrame = f => { f(); return 0; };
class DCLogic { constructor() { this.props = {}; this.state = undefined; } setState(p) { this.state = Object.assign({}, this.state || {}, typeof p === 'function' ? p(this.state) : p); } forceUpdate() {} }
const Component = new Function('DCLogic', script + '\nreturn Component;')(DCLogic);
const c = new Component();
const problems = [];
const walk = (v, path, seen) => {
  if (v == null) return;
  if (typeof v === 'number') { if (!Number.isFinite(v)) problems.push(path + ' = ' + v); return; }
  if (typeof v === 'string') { if (/NaN|undefined|Infinity/.test(v)) problems.push(path + ' = ' + v.slice(0, 80)); return; }
  if (typeof v === 'function' || typeof v === 'boolean') return;
  if (seen.has(v)) return; seen.add(v);
  if (Array.isArray(v)) { v.forEach((x, i) => walk(x, path + '[' + i + ']', seen)); return; }
  for (const k of Object.keys(v)) { if (k === 'R' || k === 'z' || k === 'kd') continue; walk(v[k], path + '.' + k, seen); }
};
const holes = (vals, label) => {
  const re = /<sc-for\s+list="\{\{\s*([\w.]+)\s*\}\}"\s+as="(\w+)"|<\/sc-for>|\{\{\s*([\w.$]+)\s*\}\}/g;
  const scope = [], get = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
  const resolve = p => {
    if (p === 'true' || p === 'false' || /^\d/.test(p)) return true;
    const head = p.split('.')[0];
    for (let i = scope.length - 1; i >= 0; i--) if (scope[i].alias === head) { if (scope[i].item === undefined) return 'EMPTY'; const rest = p.split('.').slice(1).join('.'); return rest ? get(scope[i].item, rest) : scope[i].item; }
    return get(vals, p);
  };
  const miss = new Set(); let m;
  while ((m = re.exec(markup))) {
    if (m[1]) { const list = resolve(m[1]); if (list === 'EMPTY') { scope.push({ alias: m[2], item: undefined }); continue; } if (!Array.isArray(list)) miss.add('LIST ' + m[1]); scope.push({ alias: m[2], item: Array.isArray(list) ? list[0] : undefined }); }
    else if (m[0] === '</sc-for>') scope.pop();
    else { const r = resolve(m[3]); if (r === undefined && !scope.some(s => s.alias === m[3].split('.')[0] && s.item === undefined)) miss.add(m[3]); }
  }
  if (miss.size) problems.push(label + ' unresolved: ' + [...miss].join(', '));
};
const run = (label, st) => {
  c.state = Object.assign({}, st);
  const t0 = Date.now(); let v;
  try { v = c.renderVals(); } catch (e) { problems.push(label + ' THROW ' + e.stack.split('\n').slice(0, 3).join(' | ')); return null; }
  const ms = Date.now() - t0, before = problems.length;
  walk(v, label, new WeakSet()); holes(v, label);
  const n = k => (Array.isArray(v[k]) ? v[k].length : '-'), len = s => (s || '').length;
  console.log(label.padEnd(28), (ms + 'ms').padStart(6), 'bars', n('bodies'), 'cells', n('cells'), 'hl', n('hl'), 'tags', n('tags'), 'A1', len(v.ds && v.ds.A.p0), 'B1', len(v.ds && v.ds.B.p0), 'clu', v.zlab ? v.zlab.length : '-', problems.length > before ? 'PROBLEMS ' + (problems.length - before) : '');
  return v;
};
const scenes = [['conf', {}], ['wait', { scene: 'wait', rp: { sess: 'RDR', at: 640 } }], ['brk', { scene: 'brk' }]];
for (const [name, base] of scenes) {
  const v = run(name, base);
  run(name + ' crosshair', Object.assign({ mx: 900, my: 300 }, base));
  run(name + ' whole day', Object.assign({ v0: -390, v1: 1050 }, base));
  run(name + ' zoom future', Object.assign({ v0: 780, v1: 965 }, base));
  run(name + ' layers off', Object.assign({ layers: { pull: false, cont: false, struct: false } }, base));
  run(name + ' yz 2', Object.assign({ yz: 2 }, base));
  if (!v) continue;
  const cell = (v.cells || [])[3];
  if (cell) { run(name + ' hover cell', Object.assign({ hover: cell.key }, base)); run(name + ' pick cell', Object.assign({ pick: cell.key, hover: cell.key }, base)); }
  const kid = name === 'wait' ? 'up' : 'pull';
  run(name + ' hover blob', Object.assign({ hover: 'blob|' + kid + '|1' }, base));
  run(name + ' pick blob', Object.assign({ pick: 'blob|' + (name === 'wait' ? 'dn' : 'cont') + '|1', hover: 'blob|' + (name === 'wait' ? 'dn' : 'cont') + '|1' }, base));
  run(name + ' col', Object.assign({ hover: 'col|870' }, base));
  if (v.pbars && v.pbars[2]) { c.state = Object.assign({}, base); c.renderVals(); const k = Object.keys(c.__hv).find(q => q.startsWith('pbin|')); if (k) run(name + ' pbin', Object.assign({ hover: k }, base)); }
  run(name + ' lvl', Object.assign({ hover: 'lvl|RDR|u2' }, base));
  run(name + ' replay 11:30', Object.assign({ rp: { sess: 'RDR', at: 690 } }, base));
  run(name + ' ODR', Object.assign({ session: 'ODR', v0: 155, v1: 520 }, base));
  run(name + ' scrub past', Object.assign({ scrub: { sess: 'RDR', at: 700 } }, base));
}
c.state = {};
try {
  const h = c.renderVals();
  h.tb.scenes[2].click(); console.log('scene ->', c.state.scene, JSON.stringify(c.state.rp));
  const h2 = c.renderVals(); h2.tb.scenes[1].click(); console.log('scene ->', c.state.scene, JSON.stringify(c.state.rp));
  const h3 = c.renderVals(); if (h3.chits[20]) h3.chits[20].click(); console.log('candle ->', JSON.stringify(c.state.rp));
  const h4 = c.renderVals(); h4.tb.toLive(); console.log('live ->', c.state.rp);
  c._zoomAt(-300, 600); c._panBy(200); console.log('zoom/pan ->', c.state.v0.toFixed(1), c.state.v1.toFixed(1));
  const h5 = c.renderVals(); h5.tb.layers[0].click(); console.log('layers ->', JSON.stringify(c.state.layers));
} catch (e) { problems.push('handlers THROW ' + e.stack.split('\n').slice(0, 3).join(' | ')); }
console.log(problems.length ? '\nPROBLEMS:\n' + problems.slice(0, 40).join('\n') : '\nno problems');
