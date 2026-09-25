// Static snapshot of an artboard for visual review: expands <sc-for>/<sc-if> and {{holes}} with renderVals() of a state.
const fs = require('fs');
const [file, stateJson, outFile] = process.argv.slice(2);
const src = fs.readFileSync(file, 'utf8');
const script = src.split('data-dc-script')[1].split('>').slice(1).join('>').split('</script>')[0];
const xdc = src.split('<x-dc>')[1].split('</x-dc>')[0];
const helmet = (xdc.match(/<helmet>([\s\S]*?)<\/helmet>/) || ['', ''])[1];
let markup = xdc.replace(/<helmet>[\s\S]*?<\/helmet>/, '');
global.requestAnimationFrame = f => { f(); return 0; };
class DCLogic { constructor() { this.props = {}; } setState(p) { this.state = Object.assign({}, this.state || {}, p); } }
const Component = new Function('DCLogic', script + '\nreturn Component;')(DCLogic);
const c = new Component(); c.state = JSON.parse(stateJson || '{}');
const vals = c.renderVals();
const get = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
const res = (scope, p) => { p = p.trim(); if (p === 'true') return true; if (p === 'false') return false; const head = p.split('.')[0]; for (let i = scope.length - 1; i >= 0; i--) if (head in scope[i]) return get(scope[i], p); return get(vals, p); };
markup = markup.replace(/\s(on[A-Z]\w*|ref)="\{\{[^}]*\}\}"/g, '');
function findClose(s, from, tag) {
  const re = new RegExp('<' + tag + '[\s>]|</' + tag + '>', 'g'); re.lastIndex = from; let depth = 1, m;
  while ((m = re.exec(s))) { if (m[0].startsWith('</')) { if (--depth === 0) return m.index; } else depth++; }
  throw new Error('unclosed ' + tag);
}
function expand(s, scope) {
  let out = '', i = 0;
  const re = /<sc-(for|if)\b([^>]*)>/g; let m;
  while ((m = re.exec(s))) {
    out += interp(s.slice(i, m.index), scope);
    const tag = 'sc-' + m[1], close = findClose(s, re.lastIndex, tag), inner = s.slice(re.lastIndex, close);
    const attr = n => (m[2].match(new RegExp(n + '="\{\{([^}]*)\}\}"')) || [])[1];
    if (m[1] === 'for') { const list = res(scope, attr('list')) || [], as = (m[2].match(/as="(\w+)"/) || [])[1]; for (const it of list) out += expand(inner, scope.concat([{ [as]: it }])); }
    else if (res(scope, attr('value'))) out += expand(inner, scope);
    i = close + ('</' + tag + '>').length; re.lastIndex = i;
  }
  return out + interp(s.slice(i), scope);
}
function interp(s, scope) { return s.replace(/\{\{([^}]*)\}\}/g, (_, p) => { const v = res(scope, p); return v == null || typeof v === 'function' ? '' : String(v); }); }
const html = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>' + helmet.replace(/<\/?style>/g, '') + ' html,body{margin:0}</style></head><body>' + expand(markup, []) + '</body></html>';
fs.writeFileSync(outFile, html);
console.log('wrote', outFile, html.length);
