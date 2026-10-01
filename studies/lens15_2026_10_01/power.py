"""Lens 15, sensitivity of the pipeline (added after the tape run; it says what the run could have found, not what the
tape holds). Synthetic random-walk families on an RDR-like block, N sessions each; a share s of them is given a dip that
puts their R near -0.8 SD around 12:00-12:45 (a planted price x time cluster of R, beyond geometry by construction).
Every other rule is selector.py's, unchanged. No market data.

    python -B studies/lens15_2026_10_01/power.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import selector as SEL  # noqa: E402

LEVELS = (0.0, 0.1, 0.2, 0.3)
SIZES = (60, 150)
REPS = 4


def family(N, share, rng):
    f, E, w, w0 = 630, 960, 100, 1
    recs = []
    for _ in range(N):
        conf = f + 15 * w0 + 5 * int(rng.integers(0, 3)) + 5
        T = np.arange(conf + 5, E + 1, 5)
        n = len(T)
        inc = rng.normal(0, 18, n)
        if rng.random() < share:
            j = int(np.searchsorted(T, 725 + 5 * int(rng.integers(0, 7))))   # the dip's bottom closes 12:05-12:35
            inc[:j] += (-80 - 30) / max(j, 1) - inc[:j].mean()
            inc[j:] += 150 / max(n - j, 1)
        cl = np.round(30 + np.cumsum(inc)).astype(np.int64)
        prev = np.concatenate(([30], cl[:-1]))
        hi = np.maximum(cl, prev) + np.round(np.abs(rng.normal(0, 6, n))).astype(np.int64)
        lo = np.minimum(cl, prev) - np.round(np.abs(rng.normal(0, 6, n))).astype(np.int64)
        opens = T - 5
        jr, jx = int(lo.argmin()), int(hi.argmax())
        recs.append(dict(key=(0, 1, w0), first=bool(rng.random() < 0.5), w=w, known=True, R=(int(lo[jr]), int(opens[jr])),
                         X=(int(hi[jx]), int(opens[jx])), c0=30, lo=lo, hi=hi, cl=cl, opens=opens))
    return recs, f, E


def main():
    rng = np.random.default_rng(SEL.SEED + 15)
    out = {}
    for N in SIZES:
        for s in LEVELS:
            hits = {k: 0 for k in SEL.SELECTORS}
            planted_hit = {k: 0 for k in SEL.SELECTORS}
            regions = {k: [] for k in SEL.SELECTORS}
            for _ in range(REPS):
                recs, f, E = family(N, s, rng)
                F = SEL.Family((0, 1, 1), recs, f, E, None, rng)
                for sel in SEL.SELECTORS:
                    x = F.evaluate(sel, "real", "R", rng)
                    hits[sel] += x["confirmed"]
                    m = x["main"]
                    if x["confirmed"] and m: regions[sel].append(f"{m['price'][0]:+.1f}..{m['price'][1]:+.1f} x {m['time'][0]}-{m['time'][1]} {m['share']}%")
                    # the planted place: R near -0.8 SD (cells -12..-5) between 11:45 and 13:00
                    if x["confirmed"] and m and m["price"][1] <= -0.3 and m["price"][0] >= -1.4:
                        planted_hit[sel] += 1
            out[f"N{N}/share{s}"] = dict(confirmed=hits, confirmed_at_planted_place=planted_hit, confirmed_regions=regions, families=REPS)
            print(f"N {N:3d} planted share {s:.1f}: confirmed {hits}, at the planted place {planted_hit} of {REPS}; {regions}", flush=True)
    (HERE / "power.json").write_text(json.dumps(dict(levels=LEVELS, sizes=SIZES, reps=REPS, results=out), indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
