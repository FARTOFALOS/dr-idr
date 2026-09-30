"""Lens 6: the author's Time & Price statistics recomputed for one published key on our tape (aggregates only).

Key (jPvvCww8aP8, 2025): NQ, Friday, RDR, short, first confirmation close in 10:30-11:00. The author: 346 sessions in
17 years, DR true 85 %, entry window 10:45 (first mode) - 12:00 (median time of the max retracement), zones
+0.09..-0.3 and -0.51..-0.7, P(back into DR) 86.3 %, P(back into IDR) 70.7 %, target 1.0-1.09 at the 70 % line.

Per-session values as the author defines them (qxh2fHQLHlM, 2026), taken from studies/m7_claims.py `instances`:
retr = the most adverse price after the confirmation until 16:00, ext = the most favourable price from the
confirmation bar until 16:00, both in IDR widths from the confirmation-side IDR edge (QuantX sign: negative = into
the IDR); retr_t = the minute of retr; DR true = no M5 close beyond the opposite DR until 16:00. IDR by bodies.

Buckets follow the author's labels: 0..0.09, 0.1..0.19 on the plus side, -0.01..-0.1, -0.11..-0.2 on the minus side.
"70 %" follows the author: for retr the level 70 % of sessions stay above (quantile 0.3 of the signed value), for ext
the level 70 % of sessions reach (quantile 0.3). Time bins are 15 minutes.

Run from this folder: python -B author_key_nq.py   (builds lab/.runtime/study_m7_nq.pkl on the first run)
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from m7_claims import SESSIONS, load  # noqa: E402

RDR_FORMED = SESSIONS["RDR"][1]


def bucket(x):
    """Author's 0.1 bucket index: 0 = 0..0.09, 1 = 0.1..0.19; -1 = -0.01..-0.1, -2 = -0.11..-0.2."""
    return math.floor(round(x * 10, 6)) if x >= 0 else -math.ceil(round(-x * 10, 6))


def label(k):
    return f"+{k / 10:.1f}..+{k / 10 + 0.09:.2f}" if k >= 0 else f"{(k + 1) / 10 - 0.01:+.2f}..{k / 10:+.1f}"


def clock(m):
    m = int(m) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def pct(x):
    return f"{100 * x:5.1f} %"


def describe(T, name):
    print(f"\n-- {name}: n = {len(T)}")
    tod = (T.retr_t - T.day * 1440 - 1).to_numpy()          # minute of the M1 bar that made the extreme
    bins = np.arange(RDR_FORMED, 16 * 60 + 1, 15)
    h, _ = np.histogram(tod, bins=bins)
    share = h / len(T)
    first_mode = next(i for i in range(len(h)) if (i == 0 or h[i] >= h[i - 1]) and (i == len(h) - 1 or h[i] >= h[i + 1]))
    print("  time of max retracement, 15-min bins: " + " ".join(f"{clock(b)} {100 * s:.1f}" for b, s in zip(bins[:-1], share)))
    print(f"  first mode from the left: {clock(bins[first_mode])}-{clock(bins[first_mode] + 15)}; "
          f"median {clock(np.quantile(tod, 0.5))}; 70 % by {clock(np.quantile(tod, 0.7))}")
    r = T.retr.to_numpy()
    k = np.array([bucket(x) for x in r])
    print(f"  max retracement: median {np.quantile(r, 0.5):+.2f}; 70 % stay above {np.quantile(r, 0.3):+.2f}")
    print("  buckets (share): " + "; ".join(f"{label(b)} {100 * np.mean(k == b):.1f}" for b in range(4, -13, -1)))
    z1 = (r <= 0.09 + 1e-9) & (r >= -0.30 - 1e-9)
    z2 = (r <= -0.51 + 1e-9) & (r >= -0.70 - 1e-9)
    print(f"  zone +0.09..-0.3: {pct(z1.mean())}; zone -0.51..-0.7: {pct(z2.mean())}; "
          f"-0.31..-0.5: {pct(((r < -0.30) & (r > -0.51)).mean())}; above +0.09: {pct((r > 0.09).mean())}; "
          f"deeper than -0.7: {pct((r < -0.70).mean())}")
    print(f"  back into DR {pct(T.into_dr.mean())}; back into IDR {pct(T.into_idr.mean())}")
    e = T.ext.to_numpy()
    ke = np.array([bucket(x) for x in e])
    top = max(range(0, 40), key=lambda b: np.mean(ke == b))
    print(f"  max extension: median {np.quantile(e, 0.5):.2f}; 70 % reach {np.quantile(e, 0.3):.2f}; "
          f"reached 1.0: {pct((e >= 1.0).mean())}; tallest bucket {label(top)} ({100 * np.mean(ke == top):.1f} %)")
    print("  extension buckets (share): " + "; ".join(f"{b / 10:.1f} {100 * np.mean(ke == b):.1f}" for b in range(0, 26)))
    if z1.any():
        e1 = e[z1]
        print(f"  cross-filter, max retracement in +0.09..-0.3 (n = {z1.sum()}): reached 1.0 {pct((e1 >= 1.0).mean())}; "
              f"70 % reach {np.quantile(e1, 0.3):.2f}")
    return tod


def main():
    tape, S = load("NQ")
    # sample sizes of the three NQ Friday RDR keys the author published (session counts in his videos)
    F = S[(S.session == "RDR") & (S.wd == 4) & S.complete & (S.dir != 0)].copy()
    F["rel"] = F.conf - (F.day * 1440 + RDR_FORMED)
    print("NQ Friday RDR keys: ours (complete sessions) against the author's published counts")
    for side, lo, hi, author in ((-1, 0, 30, "346 in 17 years, DR true 85 % (jPvvCww8aP8)"),
                                 (1, 0, 30, "190 in 18 years, DR true 79 % (J054OlJm8jE)"),
                                 (1, 30, 60, "88, DR true 91 % (l5DwIIH0rJ8)")):
        g = F[(F.dir == side) & (F.rel > lo) & (F.rel <= hi)]
        g17 = g[(g.year >= 2008) & (g.year <= 2024)]
        print(f"  {'short' if side < 0 else 'long'} {clock(RDR_FORMED + lo)}-{clock(RDR_FORMED + hi)}: 2006-2025 {len(g)} "
              f"(DR true {pct(g.dr_true.mean())}); 2008-2024 {len(g17)} (DR true {pct(g17.dr_true.mean())}); author: {author}")
    C = S[(S.session == "RDR") & (S.dir == -1) & (S.wd == 4)].copy()
    C["rel"] = C.conf - (C.day * 1440 + RDR_FORMED)
    K = C[(C.rel > 0) & (C.rel <= 30) & C.complete].copy()
    print(f"NQ, Friday, RDR, short, first confirmation close in 10:30-11:00, complete sessions {K.year.min()}-{K.year.max()}")
    for y0, y1 in ((2006, 2025), (2008, 2024)):
        k = K[(K.year >= y0) & (K.year <= y1)]
        print(f"  {y0}-{y1}: sessions {len(k)}; DR true {pct(k.dr_true.mean())}")
    T = K[K.dr_true == 1]
    tod = describe(T, "author's set: DR true only")
    describe(K, "prefix-honest set: all sessions of the key")
    w = T[((T.retr_t - T.day * 1440 - 1) >= 10 * 60 + 45) & ((T.retr_t - T.day * 1440 - 1) < 12 * 60)]
    describe(w, "author's set with the time filter: max retracement in 10:45-12:00")

    # one session, no date: the DR-true session of the key whose max retracement lies in the second zone and whose
    # time is closest to the key's median time
    r2 = T[(T.retr <= -0.51) & (T.retr >= -0.70)].copy()
    med = np.quantile(tod, 0.5)
    r2["dist"] = ((r2.retr_t - r2.day * 1440 - 1) - med).abs()
    s = r2.sort_values("dist").iloc[0]
    t = int(s.retr_t - s.day * 1440 - 1)
    tb = RDR_FORMED + 15 * ((t - RDR_FORMED) // 15)
    below = np.mean(tod <= t)
    print("\n-- one session of the key (date withheld)")
    print(f"  confirmation close {clock(s.conf - s.day * 1440)}; DR true; max retracement {s.retr:+.2f} "
          f"-> bucket {label(bucket(s.retr))}; its time {clock(t)} -> time bin {clock(tb)}-{clock(tb + 15)}, "
          f"{100 * below:.0f}th percentile of the key's times; inside the 10:45-12:00 window: {10 * 60 + 45 <= t < 12 * 60}")
    print(f"  max extension {s.ext:.2f} -> bucket {label(bucket(s.ext))}; into DR {bool(s.into_dr)}, into IDR {bool(s.into_idr)}")
    # a second session of the second zone, the one whose time is latest inside the window (it passes the time filter)
    r2["t"] = r2.retr_t - r2.day * 1440 - 1
    inw = r2[(r2.t >= 10 * 60 + 45) & (r2.t < 12 * 60)].sort_values("t")
    if len(inw):
        s = inw.iloc[-1]
        t = int(s.t)
        tb = RDR_FORMED + 15 * ((t - RDR_FORMED) // 15)
        print(f"  second session: confirmation close {clock(s.conf - s.day * 1440)}; DR true; max retracement {s.retr:+.2f} "
              f"-> bucket {label(bucket(s.retr))}; its time {clock(t)} -> time bin {clock(tb)}-{clock(tb + 15)}, "
              f"{100 * np.mean(tod <= t):.0f}th percentile of the key's times; inside the window: True; "
              f"max extension {s.ext:.2f} -> bucket {label(bucket(s.ext))}")
    print(f"  second-zone sessions of the key: DR true {len(r2)}, of them inside the 10:45-12:00 window {len(inw)}")


if __name__ == "__main__":
    main()
