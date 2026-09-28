"""Builds design 20 «Созвездия» into one self-contained page: ../built/index.html.

python build.py
The two days are the synthetic days of design/clusters-2026-09-28 (gen_days.py; NOT market data). Those bars open
exactly at the previous close, so there is no body gap anywhere; a few volume imbalances (VIB: a gap between one
bar's close and the next bar's open) are added here, deterministically, on strong moves outside the box windows, so
the VIB layer has something to show. DR, IDR, confirmations and breaks do not change (they use closes and the box
bars only).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
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


days = {}
for d in 'AB':
    bars = json.load(open(os.path.join(HERE, 'bars_%s.min.json' % d.lower())))
    v = add_vibs(bars)
    print(d, 'bars', len(bars), 'VIB at', [bars[i][0] for i in v])
    days[d] = bars

page = open(os.path.join(HERE, 'page.html'), encoding='utf-8').read()
app = open(os.path.join(HERE, 'app.js'), encoding='utf-8').read()
out = page.replace('/*__DAYS__*/', 'window.__DAYS__=' + json.dumps(days, separators=(',', ':')) + ';').replace('/*__APP__*/', app)
os.makedirs(os.path.join(HERE, '..', 'built'), exist_ok=True)
open(os.path.join(HERE, '..', 'built', 'index.html'), 'w', encoding='utf-8').write(out)
print('built/index.html', round(len(out) / 1e3), 'kB')
