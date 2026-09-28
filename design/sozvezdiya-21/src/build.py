"""Builds «Созвездия» (design 21) twice from the same source:

- ../built/index.html — the mockup: one self-contained page on two synthetic days (design/clusters-2026-09-28/gen_days.py,
  NOT market data, plus a few body gaps so the VIB layer has something to show);
- lab/dist/index.html + lab/dist/sozvezdiya.js — the working screen of DR Lab: the same code without the synthetic days
  takes its bars and similar sessions from the local server (lab/scene21.py). The previous screen stays as
  lab/dist/classic.html.

python build.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DIST = os.path.join(REPO, 'lab', 'dist')
BOX = [(-270, -210), (180, 240), (570, 630)]


def add_vibs(bars):
    cand = []
    for i in range(1, len(bars) - 1):
        a, b = bars[i - 1], bars[i]
        if any(s <= b[0] < e or s <= a[0] < e for s, e in BOX):
            continue
        body, rng_ = a[4] - a[1], a[2] - a[3]
        if rng_ <= 0 or abs(body) < 0.6 * rng_ or abs(body) < 6:
            continue
        if (b[4] - b[1]) * body <= 0:
            continue
        cand.append((abs(body), i))
    cand.sort(reverse=True)
    picked = []
    for _, i in cand:
        if all(abs(i - j) >= 8 for j in picked):
            picked.append(i)
        if len(picked) == 10:
            break
    for i in picked:
        a, b = bars[i - 1], bars[i]
        d = 1 if a[4] > a[1] else -1
        g = min(2.0, max(0.5, round(0.1 * abs(a[4] - a[1]) / 0.25) * 0.25))
        b[1] = a[4] + d * g
        b[2] = max(b[2], b[1])
        b[3] = min(b[3], b[1])
    return sorted(picked)


def read(name):
    return open(os.path.join(HERE, name), encoding='utf-8').read()


days = {}
for d in 'AB':
    bars = json.load(open(os.path.join(HERE, 'bars_%s.min.json' % d.lower())))
    add_vibs(bars)
    days[d] = bars

page = read('page.html').replace('/*__PANEL21CSS__*/', read('panel21.css'))
app = read('app.js').replace('/*__PANEL21__*/', read('panel21.js'))

mock = page.replace('/*__DAYS__*/', 'window.__DAYS__=' + json.dumps(days, separators=(',', ':')) + ';').replace('/*__APP__*/', app)
os.makedirs(os.path.join(HERE, '..', 'built'), exist_ok=True)
open(os.path.join(HERE, '..', 'built', 'index.html'), 'w', encoding='utf-8').write(mock)

work = page.replace('<title>DR Lab · 21 · Созвездия — смысловая панель</title>', '<title>DR Lab</title>')
work = work.replace('<script>/*__DAYS__*/</script>\n', '').replace('<script>\n/*__APP__*/\n</script>', '<script src="/sozvezdiya.js"></script>')
assert '/*__APP__*/' not in work and '__DAYS__' not in work, 'page template changed: update build.py'
open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8').write(work)
open(os.path.join(DIST, 'sozvezdiya.js'), 'w', encoding='utf-8').write('// Built from design/sozvezdiya-21/src (app.js + panel21.js) by its build.py: edit there.\n' + app)
print('built/index.html', round(len(mock) / 1e3), 'kB · lab/dist/index.html + sozvezdiya.js', round(len(app) / 1e3), 'kB')
