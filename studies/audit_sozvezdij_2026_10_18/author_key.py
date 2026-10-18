"""Audit 2026-10-18 (meaning/lens/2026-10-18-audit-sozvezdij/), aggregates only: the author's published key
NQ · Friday · RDR · short · confirmation 10:30-11:00 (docs/STRATEGY.md §6.3: DR true 85 %, retracement zones
+0.09…-0.3 and -0.51…-0.7, target 1.0-1.09) against screen 24's constellations for the same key (our 15-minute windows
10:30-10:45 and 10:45-11:00, all sessions of 2006-2025, zone-map-3), and the author's own reading on our tape: DR-true
sessions only, max retracements before 12:00 (his entry window 10:45-12:00), 70th percentile of depth. The same key
was first recomputed by lens 6 (studies/lens6_2026_09_30/).

    python -B studies/audit_sozvezdij_2026_10_18/author_key.py > studies/audit_sozvezdij_2026_10_18/author_key.txt
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab"))
import scene21  # noqa: E402
import scene24  # noqa: E402
import zonemap24  # noqa: E402

inst, session, wd, side = "NQ", "RDR", 4, -1
start, formed, end = scene21.SESS[session]
B = scene24._base(inst)
clk = lambda t: "%02d:%02d" % ((t % 1440) // 60, t % 60)
pooled = []
for win in (0, 1):
    snap = scene24._snapshot(inst, B, session, wd, side, "conf", win, "2026-01-01", "weekday")
    mem = snap["members"]; ids = [m["id"] for m in mem]; N = len(mem)
    pooled += mem
    held = sum(1 for m in mem if m["outcome"] == "held")
    print(f"window {clk(formed + 15 * win)}-{clk(formed + 15 * win + 15)}: N {N}, DR held {held / N:.1%}")
    for ev in ("R", "X"):
        zm = zonemap24.map_of(mem, ev, formed, end, win, ids)
        for i, z in enumerate(zm["zones"]):
            k0, k1 = z["price"]; b0, b1 = z["time"]
            ms = [m for m in mem if m["id"] in set(z["members"])]
            rx = sum(1 for m in ms if m["order"] == "R_before_X") / len(ms)
            print(f"  {ev}{i + 1}: {z['n']}/{N} = {z['n'] / N:.1%}  u {k0 / 10:+.1f}…{k1 / 10:+.1f}  {clk(formed + 15 * b0)}-{clk(formed + 15 * b1)}  R before X {rx:.0%}")
        print(f"  {ev} outside zones {len(zm['residual']) / N:.1%}")
# the author's procedure on our tape for the pooled 30-minute key
true = [m for m in pooled if m["outcome"] == "held" and m["R"]["s"] == "known"]
early = sorted(m["R"]["v"] / m["w"] for m in true if m["R"]["t"] < 720)       # max retracement before 12:00
q = lambda v, p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]
print(f"\nauthor's way, pooled 10:30-11:00: N {len(pooled)}, DR true {len(true)}, of them R before 12:00: {len(early)}")
print(f"  R depth among those: median {q(early, 0.5):+.2f}, 70 % not deeper than {q(early, 0.3):+.2f}")
xs = sorted(m["X"]["v"] / m["w"] for m in true)
print(f"  X (DR true): reached by 70 % of sessions {q(xs, 0.3):+.2f}, median {q(xs, 0.5):+.2f}")
allx = sorted(m["X"]["v"] / m["w"] for m in pooled if m["X"]["s"] == "known")
print(f"  X (all sessions, our family): reached by 70 % {q(allx, 0.3):+.2f}, median {q(allx, 0.5):+.2f}")
