"""Checks of the 23.5 local layer «Съёмы лоу» (SW-0.1) on the reference lab/sweeps235_ref.py.

The operator's two scenes of 26.10 and the edges of the definition, as synthetic paths in directed ticks (w = 10 ticks
= 1 SD, so 1 tick = 0.1 SD). Optional: the real families of a running integration server (argument: its address) for
the invariants that must hold on every family. The page itself is compared with the reference by sweeps235_page.mjs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab"))
import sweeps235_ref as R

ok = 0


def check(cond, name):
    global ok
    if not cond:
        raise SystemExit("FAIL " + name)
    ok += 1
    print("PASS " + name)


def run(bars, act=0):
    """bars: [(lo, hi)] per M5 after the activation, directed ticks; None = a missing M5."""
    grid = [5 * (i + 1) for i in range(len(bars))]
    m = dict(id="s", act=act, w=10, path=[None if b is None else [b[0], b[1], b[0]] for b in bars])
    return R.session(grid, m)


# 1. Retirement entry, long (operator 26.10): a low at -7 holds, price goes a little lower to -8, takes it, then a new
#    high of the session at +10.
st, ev = run([(0, 5), (-3, 3), (-7, -2), (-6, -1), (-5, 0), (-8, -4), (-6, 0), (-2, 4), (2, 10)])
check(st == "KNOWN" and len(ev) == 1 and ev[0]["swing"][0] == -7 and ev[0]["bottom"][0] == -8 and ev[0]["cont"] is not None,
      "retirement entry: the held low -0.7 is taken to -0.8, then a new high: one sweep with continuation")
# 2. Expanding triangle (operator 26.10): +0.5, back to the middle, +0.6, below the middle, then +1.0
st, ev = run([(1, 5), (-5, 0), (-4, 2), (0, 6), (-6, 1), (-5, 3), (2, 10)])
check(st == "KNOWN" and len(ev) == 1 and ev[0]["swing"][0] == -5 and ev[0]["bottom"][0] == -6 and ev[0]["cont"] == 30,
      "expanding triangle: the middle low is taken, the new high of +1.0 follows at the next M5")
# 3. The low holds and is never taken: no event
st, ev = run([(0, 5), (-4, 1), (-3, 3), (-1, 6), (0, 9)])
check(st == "KNOWN" and ev == [], "a low that is never taken is not a sweep")
# 4. Taken, and no new high until the block ends
st, ev = run([(0, 5), (-4, 1), (-3, 3), (-6, 0), (-5, 2)])
check(st == "KNOWN" and len(ev) == 1 and ev[0]["cont"] is None, "taken without a new high: an event without continuation")
# 5. A straight fall: every M5 a new low, none held — nothing to take
st, ev = run([(0, 5), (-2, 0), (-4, -1), (-6, -3), (-8, -5), (0, 12)])
check(st == "KNOWN" and ev == [], "a low that never held is not a stop to take")
# 6. Equal lows: the second touch does not take the first (one tick beyond is needed)
st, ev = run([(0, 5), (-4, 1), (-4, 2), (-2, 3), (-4, 0), (1, 9)])
check(st == "KNOWN" and ev == [], "an equal low is a retest, not a sweep")
# 7. One tick beyond is enough (wick)
st, ev = run([(0, 5), (-4, 1), (-3, 2), (-5, 0), (1, 9)])
check(len(ev) == 1 and ev[0]["bottom"][0] == -5 and ev[0]["cont"] is not None, "one tick beyond the held low is a sweep")
# 8. A missing M5: unknown, as for R and X
st, ev = run([(0, 5), (-4, 1), None, (1, 9)])
check(st == "UNKNOWN", "a missing M5 after the activation makes the session unknown")
# 9. One M5 makes the new low and the new high: the order inside it is unknown (no M1) and it is not a continuation
st, ev = run([(0, 5), (-4, 1), (-3, 2), (-6, 7)])
check(st == "UNKNOWN", "a new low and a new high in one M5 cannot be ordered")
# 10. Two sweeps in one leg: the thread goes to the last held low taken, the bottom is the deepest point
st, ev = run([(0, 6), (-3, 2), (-2, 3), (-5, 0), (-4, 1), (-7, -3), (-5, 2), (0, 9)])
check(len(ev) == 1 and ev[0]["swing"][0] == -5 and ev[0]["bottom"][0] == -7, "a chain of taken lows: one bottom, its thread to the last held low taken")
# 11. The activating M5 is not part of the session's path after the activation
st, ev = run([(-9, 9), (0, 5), (-4, 1), (-3, 2), (-5, 0), (1, 9)], act=5)
check(len(ev) == 1 and ev[0]["swing"][0] == -4, "the activating M5 is excluded, as for R and X")

# 12. Regions: one vote per session, half height of its own peak
cells = {"a": {(0, 0)}, "b": {(0, 0), (0, 1)}, "c": {(1, 0)}, "d": {(9, 5)}}
regs = R.regions(cells, 0, 6)
check(any((0, 0) in r for r in regs) and all(len(set(r)) == len(r) for r in regs), "regions: a dense corner is found once")

if len(sys.argv) > 1:
    base = sys.argv[1]
    for inst, sess, at, date in [("NQ", "RDR", 670, "2025-12-17"), ("ES", "RDR", 660, "2025-11-12"), ("YM", "ODR", 270, "2025-10-20"),
                                 ("NQ", "ODR", 270, "2025-12-16"), ("YM", "RDR", 660, "2025-12-18")]:
        fam = R.fetch(base, instrument=inst, session=sess, at=at, date=date)
        out = R.model(fam)
        check(sum(out["cats"].values()) == out["N"] and all(z["n"] >= out["need"] and len(set(z["members"])) == z["n"] for z in out["zones"]),
              f"{inst} {sess} {date}: the categories split N and every constellation has its own support")
print(f"ALL GOOD · {ok} checks")
