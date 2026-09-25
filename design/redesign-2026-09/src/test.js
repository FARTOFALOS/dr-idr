// Offline check of an artboard: runs its Component.renderVals() under many states with a stub DCLogic,
// and checks that every {{hole}} of the markup resolves (inside <sc-for> against the first item).
const fs = require('fs');
const file = process.argv[2];
const src = fs.readFileSync(file, 'utf8');
const script = src.split('data-dc-script')[1].split('>').slice(1).join('>').split('</script>')[0];
const markup = src.split('<x-dc>')[1].split('</x-dc>')[0];
global.requestAnimationFrame = f => { f(); return 0; };
class DCLogic { constructor() { this.props = {}; this.state = undefined; } setState(p) { this.state = Object.assign({}, this.state || {}, typeof p === 'function' ? p(this.state) : p); } forceUpdate() {} }
const Component = new Function('DCLogic', script + '\nreturn Component;')(DCLogic);
const c = new Component();
let problems = [];
const walk = (v, path, seen) => {
  if (v == null) return;
  if (typeof v === 'number') { if (!Number.isFinite(v)) problems.push(path + ' = ' + v); return; }
  if (typeof v === 'string') { if (/NaN|undefined|Infinity/.test(v)) problems.push(path + ' = ' + v.slice(0, 80)); return; }
  if (typeof v === 'function' || typeof v === 'boolean') return;
  if (seen.has(v)) return; seen.add(v);
  if (Array.isArray(v)) { v.forEach((x, i) => walk(x, path + '[' + i + ']', seen)); return; }
  for (const k of Object.keys(v)) { if (k === 'R' || k === 'c' || k === 'z' || k === 'hit') { if (k === 'hit') walk(v[k], path + '.hit', seen); continue; } walk(v[k], path + '.' + k, seen); }
};
// resolve holes
const holes = (vals, label) => {
  const re = /<sc-for\s+list="\{\{\s*([\w.]+)\s*\}\}"\s+as="(\w+)"|<\/sc-for>|\{\{\s*([\w.$]+)\s*\}\}/g;
  const scope = [];
  let m;
  const get = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
  const resolve = p => {
    if (p === 'true' || p === 'false' || /^\d/.test(p)) return true;
    const head = p.split('.')[0];
    for (let i = scope.length - 1; i >= 0; i--) if (scope[i].alias === head) {
      if (scope[i].item === undefined) return 'EMPTY';
      const rest = p.split('.').slice(1).join('.');
      return rest ? get(scope[i].item, rest) : scope[i].item;
    }
    return get(vals, p);
  };
  const miss = new Set();
  while ((m = re.exec(markup))) {
    if (m[1]) { const list = resolve(m[1]); if (list === 'EMPTY') { scope.push({ alias: m[2], item: undefined }); continue; } if (!Array.isArray(list)) miss.add('LIST ' + m[1]); scope.push({ alias: m[2], item: Array.isArray(list) ? list[0] : undefined }); }
    else if (m[0] === '</sc-for>') scope.pop();
    else { const r = resolve(m[3]); if (r === undefined) { const head = m[3].split('.')[0]; const inEmpty = scope.some(s => s.alias === head && s.item === undefined); if (!inEmpty) miss.add(m[3]); } }
  }
  if (miss.size) problems.push(label + ' unresolved: ' + [...miss].join(', '));
};
const run = (label, st) => {
  c.state = Object.assign({}, st);
  const t0 = Date.now();
  let v;
  try { v = c.renderVals(); } catch (e) { problems.push(label + ' THROW ' + e.stack.split('\n').slice(0, 3).join(' | ')); return null; }
  const ms = Date.now() - t0;
  const before = problems.length;
  walk(v, label, new WeakSet());
  holes(v, label);
  const cnt = k => (Array.isArray(v[k]) ? v[k].length : '-');
  console.log(label.padEnd(26), (ms + 'ms').padStart(6), 'bars', cnt('bodies'), 'cells', cnt('cells'), 'zones', cnt('zones'), 'tags', cnt('tags'), 'lines', cnt('lines'), problems.length > before ? 'PROBLEMS ' + (problems.length - before) : '');
  return v;
};
const base = {};
const v = run('live default', base);
run('replay RDR 11:30', { rp: { sess: 'RDR', at: 690 } });
run('replay RDR 10:05 forming', { rp: { sess: 'RDR', at: 605 }, session: 'RDR' });
run('replay RDR 10:45 waiting', { rp: { sess: 'RDR', at: 645 }, session: 'RDR' });
run('replay ODR 05:00', { rp: { sess: 'ODR', at: 300 }, session: 'ODR', v0: 155, v1: 520 });
run('replay ADR 21:30', { rp: { sess: 'ADR', at: -150 }, session: 'ADR', v0: -295, v1: 130 });
run('ADR done', { session: 'ADR', v0: -295, v1: 130 });
run('whole day', { v0: -390, v1: 1050 });
run('zoomed 12:00-13:30', { v0: 720, v1: 810 });
run('future only', { v0: 800, v1: 960 });
run('eclust on', { layers: { rclust: true, eclust: true, fan: true, ladder: true } });
run('layers off', { layers: { rclust: false, eclust: false, fan: false, ladder: false } });
run('yz 2', { yz: 2 });
run('crosshair', { mx: 500, my: 300 });
if (v) {
  const z = (v.zones || [])[0], cell = (v.cells || [])[0];
  if (z) run('hover zone', { hover: z.key });
  if (z) run('pick zone', { pick: z.key });
  if (cell) run('hover cell', { hover: cell.key });
  if (cell) run('pick cell + hover other', { pick: cell.key, hover: (v.cells[1] || cell).key });
  run('hover lvl dr', { hover: 'lvl|RDR|dr' });
  run('hover lvl u2', { hover: 'lvl|RDR|u2' });
  run('hover touch 1', { hover: 'touch|1' });
  run('hover price', { hover: 'price' });
  run('hover conf', { hover: 'conf|RDR' });
  run('hover sess ODR', { hover: 'sess|ODR' });
  run('bin retr', { hover: 'bin|retr|0.3' });
  run('bin rtime', { hover: 'bin|rtime|795' });
  run('bin ext', { hover: 'bin|ext|1.2' });
  run('hcell', { hover: 'hcell|0.3|795' });
  // handlers
  c.state = {};
  const h = c.renderVals();
  try {
    if (h.chits && h.chits[10]) h.chits[10].click();
    console.log('after candle click rp =', JSON.stringify(c.state.rp));
    const h2 = c.renderVals();
    if (h2.tb && h2.tb.toLive) { h2.tb.toLive(); console.log('toLive rp =', c.state.rp); }
    const h3 = c.renderVals();
    if (h3.tb) { h3.tb.sess[1].click(); console.log('session ODR ->', c.state.session, c.state.v0, c.state.v1); }
    c._zoomAt(-300, 600); console.log('zoom in ->', c.state.v0.toFixed(1), c.state.v1.toFixed(1));
    c._panBy(200); console.log('pan ->', c.state.v0.toFixed(1), c.state.v1.toFixed(1));
    const h4 = c.renderVals(); if (h4.tb) h4.tb.layers[1].click(); console.log('layers ->', JSON.stringify(c.state.layers));
  } catch (e) { problems.push('handlers THROW ' + e.stack.split('\n').slice(0, 3).join(' | ')); }
}
console.log(problems.length ? '\nPROBLEMS:\n' + problems.slice(0, 40).join('\n') : '\nno problems');
