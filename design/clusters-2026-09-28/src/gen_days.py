"""Two synthetic trading days for the DR Lab cluster mockups (NOT market data).

Day A = the published redesign day (seed 41, same anchors): RDR confirms long at 10:55 and holds.
Day B = the same evening and night, a different RDR: confirms long, then an M5 closes below DR low (a DR break).
Minutes are day coordinates of the trading day (ET): the evening before is negative (18:00 = -360).
Usage: python gen_days.py A|B  -> writes bars_a.min.json / bars_b.min.json and prints each session's facts.
"""
import json
import math
import random
import sys

DAY = sys.argv[1] if len(sys.argv) > 1 else "A"
SEED = 41
rng = random.Random(SEED)
TICK = 0.25
NOW = 788            # 13:08 ET: data up to this minute; the 13:05 bar is forming

anchors = [
    (-360, 24468), (-330, 24474), (-300, 24466), (-270, 24470),            # evening, ADR window opens 19:30
    (-262, 24455), (-250, 24478), (-238, 24466), (-224, 24488), (-214, 24493), (-210, 24484),
    (-200, 24489), (-190, 24506), (-175, 24518), (-150, 24529), (-120, 24533),
    (-95, 24517), (-80, 24508), (-50, 24514), (-20, 24527), (0, 24538), (40, 24546),
    (80, 24541), (105, 24556), (120, 24550),                               # ADR ends 02:00
    (150, 24546), (178, 24551),
    (182, 24556), (190, 24586), (198, 24574), (206, 24552), (214, 24524), (222, 24541),
    (230, 24556), (236, 24541), (240, 24537),                              # ODR window 03:00-04:00
    (250, 24527), (258, 24519), (264, 24503), (280, 24492), (300, 24480), (330, 24469),
    (350, 24486), (372, 24502), (395, 24490), (420, 24478), (460, 24456), (480, 24466),
    (510, 24488),                                                          # ODR ends 08:30
    (522, 24497), (528, 24511), (540, 24506), (556, 24516), (569, 24519),
    (572, 24530), (578, 24512), (584, 24498), (592, 24531), (600, 24556), (606, 24549),
    (612, 24588), (618, 24604), (622, 24626), (626, 24618), (629, 24612),  # RDR window 09:30-10:30
    (636, 24603), (642, 24596), (648, 24617), (654, 24641), (658, 24650),
    (668, 24681), (678, 24694), (686, 24708), (694, 24688), (704, 24671), (714, 24652),
    (720, 24641), (728, 24655), (738, 24676), (750, 24707), (760, 24731), (770, 24742),
    (778, 24726), (784, 24716), (788, 24723),
]

if DAY == "B":
    anchors = [a for a in anchors if a[0] <= 569] + [
        (572, 24530), (578, 24514), (586, 24522), (594, 24548), (602, 24566), (610, 24552), (618, 24575), (624, 24590), (629, 24584),
        (636, 24594), (642, 24612), (650, 24626), (658, 24642), (664, 24630), (672, 24598), (680, 24562), (688, 24532), (694, 24510),
        (700, 24488), (708, 24474), (716, 24462), (726, 24448), (736, 24434), (744, 24424), (752, 24438), (760, 24458), (770, 24470),
        (778, 24456), (784, 24450), (788, 24452),
    ]



def sigma(t):
    if t < -270: return 1.5
    if t < 120: return 2.3
    if t < 180: return 1.7
    if t < 510: return 4.0
    if t < 570: return 3.6
    return 7.8


# minute boundary values p(t), t = -360..NOW
p = {}
for (ta, pa), (tb, pb) in zip(anchors, anchors[1:]):
    w = [0.0]
    for t in range(ta + 1, tb + 1):
        w.append(w[-1] + rng.gauss(0, sigma(t)))
    for k, t in enumerate(range(ta, tb + 1)):
        frac = k / (tb - ta)
        p[t] = pa + (pb - pa) * frac + w[k] - frac * w[-1]

r = lambda v: round(v / TICK) * TICK
m1 = []
for t in range(-360, NOW):
    o, c = p[t], p[t + 1]
    s = sigma(t)
    h = max(o, c) + abs(rng.gauss(0, s * 0.95))
    l = min(o, c) - abs(rng.gauss(0, s * 0.95))
    m1.append((t, o, h, l, c))

m5 = {}
for t, o, h, l, c in m1:
    k = math.floor(t / 5) * 5
    if k not in m5: m5[k] = [k, o, h, l, c]
    else:
        b = m5[k]; b[2] = max(b[2], h); b[3] = min(b[3], l); b[4] = c
bars = [[b[0], r(b[1]), r(b[2]), r(b[3]), r(b[4])] for b in (m5[k] for k in sorted(m5))]
for b in bars:                      # keep OHLC consistent after rounding
    b[2] = max(b[2], b[1], b[4]); b[3] = min(b[3], b[1], b[4])
# open of a bar = close of the previous one (continuous tape)
for a, b in zip(bars, bars[1:]):
    b[1] = a[4]; b[2] = max(b[2], b[1]); b[3] = min(b[3], b[1])

SESS = {"ADR": (-270, -210, 120), "ODR": (180, 240, 510), "RDR": (570, 630, 960)}
clock = lambda m: f"{(m // 60) % 24:02d}:{m % 60:02d}"
for name, (s, f, e) in SESS.items():
    win = [b for b in bars if s <= b[0] < f]
    dh, dl = max(b[2] for b in win), min(b[3] for b in win)
    ih, il = max(max(b[1], b[4]) for b in win), min(min(b[1], b[4]) for b in win)
    conf = None
    for b in bars:
        if b[0] < f or b[0] + 5 > min(e, NOW): continue
        if b[4] > dh: conf = (b[0] + 5, "long"); break
        if b[4] < dl: conf = (b[0] + 5, "short"); break
    out = f"{name}: DR {dl}-{dh} ({dh-dl}) IDR {il}-{ih} ({ih-il}) open {win[0][1]} conf {conf and (clock(conf[0] % 1440), conf[1])}"
    if conf:
        side = 1 if conf[1] == "long" else -1
        edge, wd = (ih if side == 1 else il), ih - il
        after = [b for b in bars if b[0] + 5 > conf[0] and b[0] + 5 <= min(e, NOW)]
        opp = dl if side == 1 else dh
        fail = next((b[0] + 5 for b in after if side * (b[4] - opp) < 0), None)
        co = lambda v: side * (v - edge) / wd
        lows = [(co(b[3] if side == 1 else b[2]), b[0]) for b in after]
        highs = [(co(b[2] if side == 1 else b[3]), b[0]) for b in after]
        mn, mx = min(lows), max(highs)
        out += f" | retr {mn[0]:+.2f} @{clock(mn[1] % 1440)} ext {mx[0]:+.2f} @{clock(mx[1] % 1440)} fail {fail and clock(fail % 1440)} last {co(after[-1][4]):+.2f}"
    print(out)
print("bars", len(bars), "first", bars[0], "last", bars[-1])
rng_bar = [b[2] - b[3] for b in bars if b[0] >= 570]
print("RDR bar ranges: median", sorted(rng_bar)[len(rng_bar) // 2], "max", max(rng_bar))
json.dump(bars, open('bars_' + DAY.lower() + '.min.json', 'w'), separators=(',', ':'))
