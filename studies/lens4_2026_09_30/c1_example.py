"""Check 1 of lens 4, one example: on one historical M5 bar, the four things the lens asks to tell apart — the place's
near edge, the true first entry (M1), the bar's high and the star the screen draws. Prints normalized values only
(IDR units, minutes after the bar's open, no date, no price); the full record goes to lab/.runtime (local).
python -B c1_example.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from lenscommon import RT, Screen, dense, edges_conf, slot

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
from build_market import load_minutes  # noqa: E402
from c5_minute_alignment import conf_coords, minute_arrays  # noqa: E402

d = dense("NQ", "RDR")
S = Screen(d)
t = 660
s = slot(d, t)
rng = np.random.default_rng(1)
cand = [i for i in np.flatnonzero((d["year"] == 2020) & d["complete"] & (d["conf"] >= 0) & (d["conf"] <= t) & ~((d["fail"] >= 0) & (d["fail"] <= t)))]
df = load_minutes("NQ")
Hm, Lm, Cm = minute_arrays(df, d)
upm, dnm, _ = conf_coords(d, Hm, Lm, Cm)
for i in cand:
    sel, band, u0 = S.cohort(i, t, d["year"] < 2020)
    if band != 0.25 or not (0.25 <= u0 < 0.5): continue
    role, lo, hi = edges_conf(u0)[0]
    for j in sel:
        a = S.up[j, s + 1:]
        hit = np.flatnonzero(np.nan_to_num(a, nan=-np.inf) >= lo)
        if not len(hit): continue
        k = s + 1 + hit[0]
        depth = min(a[hit[0]], hi) - lo
        if depth < 0.15: continue
        bar_open = d["start"] + 5 * k                       # the bar opens here and closes 5 minutes later
        c0 = bar_open - d["start"]
        mins = upm[j, c0:c0 + 5]
        first_min = int(np.flatnonzero(mins >= lo)[0])
        lines = [f"place {lo:+.2f}..{hi:+.2f} IDR (price now {u0:+.2f})",
                 f"near edge: {lo:+.2f}",
                 f"true first entry: minute +{first_min} after the bar's open, at the edge {lo:+.2f} (the M1 high that minute {mins[first_min]:+.2f})",
                 f"the M5 bar: high {a[hit[0]]:+.2f}, opened {bar_open - t} min after the moment",
                 f"the star the screen draws: at the bar's open, at {min(a[hit[0]], hi):+.2f} (= {depth:.2f} IDR above the edge)"]
        print("\n".join(lines))
        (RT / "lens4_example.txt").write_text(f"session {d['date'][i]} analog {d['date'][j]}\n" + "\n".join(lines), encoding="utf-8")
        raise SystemExit
