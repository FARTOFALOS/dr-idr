"""Acceptance tests of the layer «Сейчас» (DR-LAB-NOW-1.0 §23, T1-T13 and T15; T14 on the page: tests/ui_check24.js).

    python -B tests/now24.py

Synthetic sessions in integer ticks (width w, directed low / high / close per common clock M5) exercise lab/now24.py;
T1 reads the session base (lab/.runtime/boxes_*) through lab/scene24.py. Exit code 0 = all good.
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import now24 as N  # noqa: E402
import zonemap24  # noqa: E402

failures = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond: failures.append(msg)


def P(rows, L=12):
    """rows: {grid index: (low, high, close)} -> (L, 3) float with nan elsewhere."""
    a = np.full((L, 3), np.nan)
    for j, v in rows.items(): a[j] = v
    return a


def full(L=12, base=0, lo=-2, hi=2):
    return {j: (base + lo, base + hi, base) for j in range(L)}


# ---------- T2: the common clock ----------
A = full(); A[3] = (-6, 1, 0)
B = full(); B[3] = (-6, 1, 0)
sa, sb = N.series(P(A), 2), N.series(P(B), 3)        # A activated at index 2, B at index 3 (same window)
check(sa["valid"][6] and sb["valid"][6] and sa["r"][6] == -6 and sb["r"][6] == -2,
      "T2 common clock: at the same cut A counts its M5 3..6, B only 4..6 (its own activation M5 excluded, no shift)")
check(sa["valid"][3] and not sb["valid"][3], "T2 a session without a post-activation M5 at the cut is not eligible yet")

# ---------- T6: a tie is not a new extreme ----------
t = full(); t[4] = (-5, 1, 0); t[8] = (-5, 1, 0)
st = N.series(P(t), 1)
check(st["newR"][5] == 0 and st["dR"][5] == 0, "T6 a later repeat of the same low is not a new R (new = 0, d = 0)")
t2 = copy.deepcopy(t); t2[8] = (-6, 1, 0)
st2 = N.series(P(t2), 1)
check(st2["newR"][5] == 1 and st2["dR"][5] == 1 and st2["tauR"][5] == 3, "T6 one tick deeper is new: d = 1 tick, tau = 3 M5")

# ---------- T7: a hole in the prefix ----------
h = full(); del h[4]
sh = N.series(P(h), 1)
check(sh["valid"][3] and not sh["valid"][4] and not sh["valid"][9], "T7 a missing M5 in the prefix makes every later cut ineligible")

# ---------- T8: the unknown future ----------
u = full(); del u[9]
su = N.series(P(u), 1)
check(su["newR"][6] == -1 and su["dR"][6] == -1, "T8 a missing M5 after the cut with no deeper low seen: new unknown, d unknown")
u2 = copy.deepcopy(u); u2[7] = (-9, 1, 0)
su2 = N.series(P(u2), 1)
check(su2["newR"][6] == 1 and su2["dR"][6] == -1, "T8 a deeper low seen before the hole: new = 1 (evidence), the final d still unknown")
S = N.stack([N.series(P(full()), 1), su, su2])
f = N.forecast(S, np.array([10, 10, 10]), np.array([True, True, True]), 6, "R")
check(f["support"]["N_match_unknown"] == 1 and f["p_new_bounds"] == [round(1 / 3, 4), round(2 / 3, 4)] and f["p_new_extreme"] == 0.5,
      "T8 the unknown is never «no»: bounds 1/3 … 2/3, the point only over the known (1 of 2)")

# ---------- T5: the exact threshold, T3/T4: no leakage, the future changes the outcome only ----------
w = 40
today = full(base=0); today[3] = (-10, 2, 0)                       # r_today = -10 / 40 = -0.25
T = N.series(P(today), 1)
m_in = full(); m_in[3] = (-20, 2, 0)                              # -20 / 40 = -0.50: |diff| = 0.25 exactly
m_out = full(); m_out[3] = (-21, 2, 0)                            # 0.275
S = N.stack([N.series(P(m_in), 1), N.series(P(m_out), 1)])
Mk = N.masks(S, np.array([w, w]), np.array([1, 1]), T, w, 1, [5])
check(bool(Mk["M1R"][0, 0]) and not bool(Mk["M1R"][1, 0]), "T5 a distance of exactly 0.25 belongs to M1; 0.275 does not")
fut = copy.deepcopy(m_in); fut[8] = (-99, 50, 30); fut[10] = (-120, 60, 40)
S2 = N.stack([N.series(P(fut), 1), N.series(P(m_out), 1)])
Mk2 = N.masks(S2, np.array([w, w]), np.array([1, 1]), T, w, 1, [5])
check(all(np.array_equal(Mk[k], Mk2[k]) for k in Mk), "T3 changing the member's candles after the cut changes no membership")
check(S["newR"][0, 5] == 0 and S2["newR"][0, 5] == 1 and S2["dR"][0, 5] == 100 and S2["tauR"][0, 5] == 3,
      "T4 the same change moves only the outcome (new, d, tau)")

# ---------- M3: the recent path ----------
tp = {j: (-2, 2, j) for j in range(12)}
mp = {j: (-2, 2, j + 3) for j in range(12)}                       # closes 3 ticks away on w = 40: 0.075 each
mfar = {j: (-2, 2, j + (15 if j == 5 else 0)) for j in range(12)}  # one close 0.375 away
S3 = N.stack([N.series(P(mp), 1), N.series(P(mfar), 1)])
Mk3 = N.masks(S3, np.array([40, 40]), np.array([1, 1]), N.series(P(tp), 1), 40, 1, [7])
check(bool(Mk3["M3"][0, 0]) and not bool(Mk3["M3"][1, 0]), "M3 the last six closes: MAE 0.075 passes, one close 0.375 away (max > 0.35) fails")
Mk4 = N.masks(S3, np.array([40, 40]), np.array([1, 1]), N.series(P(tp), 1), 40, 1, [3])
check(not Mk4["M3"].any(), "M3 needs at least 3 closes after today's activation")

# ---------- T12: R / X symmetry ----------
rng = np.random.default_rng(7)
for _ in range(20):
    c = np.cumsum(rng.integers(-3, 4, 12))
    lo, hi = c - rng.integers(0, 4, 12), c + rng.integers(0, 4, 12)
    p = np.stack([lo, hi, c], 1).astype(float)
    q = np.stack([-hi, -lo, -c], 1).astype(float)
    s1, s2 = N.series(p, 2), N.series(q, 2)
    if not (np.array_equal(s1["newR"], s2["newX"]) and np.array_equal(s1["dR"], s2["dX"]) and np.array_equal(s1["tauR"], s2["tauX"])
            and np.array_equal(s1["r"], -s2["x"])): break
else:
    s1 = None
check(s1 is None, "T12 a mirrored path gives the mirrored R / X: new, d, tau and the state")

# ---------- the live payload on a synthetic family: T9, T10, T11, T13 ----------
FORMED, END = 630, 690
GRID = list(range(FORMED + 5, END + 1, 5))        # 12 M5


def member(i, deep):
    path = [[-2, 2, 0] for _ in GRID]
    path[3] = [-4, 2, 0]
    path[8] = [deep, 2, 0]
    return dict(id=f"S{i}", date=f"2020-01-{i + 1:02d}", w=40, act=GRID[1], conf=GRID[1], path=path, oppv=-200,
                R=dict(s="known", v=min(-4, deep), t=0), X=dict(s="known", v=2, t=0))


def fam(n, brk=None, slice_=GRID[5], far=0):
    """n sessions; the first `far` of them reached -1.0 by the cut (not similar to today's -0.1 under M1)."""
    mem = [member(i, -30 if i % 2 else -3) for i in range(n)]
    for m in mem[:far]: m["path"][3] = [-40, 2, 0]
    return dict(status="ok", view="conf", grid=GRID, schedule=dict(start=570, formed=FORMED, end=END), N=n,
                key=dict(instrument="NQ", session="RDR", scope="weekday"), family_id=f"f{n}", snapshot_id=f"s{n}-{brk}-{far}",
                members=mem, today=dict(side=1, c0=GRID[1], brk=brk, idrH=110.0, idrL=100.0, slice=slice_))


TICK = 0.25
BARS = [[T - 5, 110.0, 110.0 + 0.5, 110.0 - 1.0, 110.0] for T in GRID]     # today: low -4 ticks, w = 40 ticks
real_decision = N.decision
N.decision = lambda view, ev, inst, session, scope: dict(status="VALIDATED", matcher="M1", magnitude="PATH", time="PATH")
p19, p20 = N.payload(fam(25, far=6), BARS, TICK), N.payload(fam(25, far=5), BARS, TICK)
check(p19["R"]["mode"] == "TIME_BASELINE" and "мало" in (p19["R"]["note"] or "") and p20["R"]["mode"] == "PATH_CONDITIONED",
      "T9 of 25 eligible, N_match = 19 shows the time baseline (with the note), 20 the validated matcher")
N.decision = lambda view, ev, inst, session, scope: dict(status="UNSTABLE", matcher="M1", magnitude="B0", time="B0")
pu = N.payload(fam(30), BARS, TICK)
check(pu["R"]["mode"] == "TIME_BASELINE" and pu["R"]["research"] and pu["R"]["research"]["M1"]["support"]["N_match_total"] == 30,
      "T10 a matcher that is not VALIDATED: the time baseline is the main NOW, the path result only in research")
N.decision = real_decision
pb = N.payload(fam(25, brk=GRID[6], slice_=GRID[9]), BARS, TICK)
check(pb["status"] == "FROZEN_AT_BREAK" and pb["cut"]["cut"] == GRID[6] - 5, "T11 after today's break the original NOW freezes on the last cut before it")
dead = fam(25)
dead["snapshot_id"] = "dead"                                       # another snapshot: no cached series
for m in dead["members"][:5]: m["path"][2] = [-300, 2, -300]          # closed beyond its own opposite DR before the cut
check(N.payload(dead, BARS, TICK)["R"]["baseline"]["support"]["N_match_total"] == 20, "T11 a member already broken by the cut is in another phase: not eligible")
small = N.payload(fam(12), BARS, TICK)
check(small["R"]["mode"] == "INSUFFICIENT_SUPPORT" and small["R"]["continuation"] is None and "n=12" in small["R"]["note"],
      "decision 12: fewer than 20 eligible sessions — no number even for the time baseline")
check(json.dumps(N.payload(fam(25), BARS, TICK), sort_keys=True) == json.dumps(N.payload(fam(25), BARS, TICK), sort_keys=True),
      "T13 the same input gives the same payload, byte for byte")
late = copy.deepcopy(BARS); late[9] = [GRID[9] - 5, 50.0, 51.0, 10.0, 50.0]
check(json.dumps(N.payload(fam(25), BARS, TICK), sort_keys=True) == json.dumps(N.payload(fam(25), late, TICK), sort_keys=True),
      "T3 today's candles after the slice (a replayed history day has them) never enter NOW")

# ---------- T15: reachability and the history clock are two axes ----------
cells = [[-3, 2], [-2, 2], [-3, 3]]                                # a zone over the time cells 2..3 (11:00-11:30 on an RDR grid)
times_past = [FORMED + 30, FORMED + 35]                            # both events closed before the slice
sl = FORMED + 40
st_ = zonemap24.status(cells, "R", (0, 1), 0, 40, sl, FORMED, END - 5)
cl_ = zonemap24.history_clock(cells, times_past, sl, FORMED, END - 5)
check(st_ == "POSSIBLE" and cl_ == "FUTURE_EMPTY", "T15 a zone can be POSSIBLE today while its family history ahead is empty (FUTURE_EMPTY)")
check(zonemap24.history_clock(cells, times_past + [FORMED + 50], sl, FORMED, END - 5) == "FUTURE_PRESENT", "T15 one event closing after the slice: FUTURE_PRESENT")
check(zonemap24.history_clock(cells, times_past, FORMED + 70, FORMED, END - 5) == "PAST_ONLY", "T15 no event ahead and the window over: PAST_ONLY")

# ---------- T1: the base map does not move with the cut ----------
try:
    import scene24
    a = scene24.family("NQ", "RDR", 660, "2025-12-09", "conf")
    b = scene24.family("NQ", "RDR", 780, "2025-12-09", "conf")
    same = all(a[k] == b[k] for k in ("family_id", "snapshot_id", "N", "counts")) and a["zones"] == b["zones"]
    check(same, "T1 moving the cut 11:00 -> 13:00 changes no family id, snapshot, N, distribution or zone")
    n1, n2 = N.live("NQ", "RDR", 660, "2025-12-09", "conf"), N.live("NQ", "RDR", 780, "2025-12-09", "conf")
    check(n1["base"]["N_base"] == n2["base"]["N_base"] == a["N"], "T1 NOW reports the same N_base at every cut")
except Exception as exc:                                            # the base is local market data; absent on a fresh clone
    print("  skip T1 (no session base): " + str(exc)[:80])

print()
print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
